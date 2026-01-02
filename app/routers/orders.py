"""
订单管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import User, GridOrder, TradingBot
from app.auth import get_current_user
from app.exchange import ExchangeAPI
from app.schemas import OrderCreate, OrderResponse
from app.config import settings
import json

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建订单"""
    # 验证机器人属于当前用户
    bot = db.query(TradingBot).filter(
        TradingBot.id == order_data.bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
        )

    # 创建订单记录
    new_order = GridOrder(
        bot_id=order_data.bot_id,
        level=order_data.level or 0,
        order_type=order_data.order_type,
        price=order_data.price,
        amount=order_data.amount,
        status="pending"
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    bot_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    order_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取订单列表"""
    # 基础查询
    query = db.query(GridOrder).join(
        TradingBot,
        GridOrder.bot_id == TradingBot.id
    ).filter(TradingBot.user_id == current_user.id)

    # 筛选条件
    if bot_id is not None:
        query = query.filter(GridOrder.bot_id == bot_id)

    if status_filter:
        query = query.filter(GridOrder.status == status_filter)

    if order_type:
        query = query.filter(GridOrder.order_type == order_type)

    # 分页
    query = query.order_by(GridOrder.created_at.desc())
    orders = query.offset(offset).limit(limit).all()

    return orders


@router.get("/stats/summary")
async def get_order_stats(
    bot_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取订单统计信息"""
    query = db.query(GridOrder).join(
        TradingBot,
        GridOrder.bot_id == TradingBot.id
    ).filter(TradingBot.user_id == current_user.id)

    if bot_id is not None:
        query = query.filter(GridOrder.bot_id == bot_id)

    total_orders = query.count()

    # 按状态统计
    pending_count = query.filter(GridOrder.status == "pending").count()
    filled_count = query.filter(GridOrder.status == "filled").count()
    cancelled_count = query.filter(GridOrder.status == "cancelled").count()
    failed_count = query.filter(GridOrder.status == "failed").count()

    # 计算总成交金额
    filled_orders = query.filter(GridOrder.status == "filled").all()
    total_filled_amount = sum(order.price * order.filled_amount for order in filled_orders)

    return {
        "total_orders": total_orders,
        "pending_count": pending_count,
        "filled_count": filled_count,
        "cancelled_count": cancelled_count,
        "failed_count": failed_count,
        "total_filled_amount": total_filled_amount
    }


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消单个订单"""
    # 获取订单并验证权限
    order = db.query(GridOrder).join(
        TradingBot,
        GridOrder.bot_id == TradingBot.id
    ).filter(
        GridOrder.id == order_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在或无权访问"
        )

    if order.status not in ["pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"订单状态为 {order.status}，无法取消"
        )

    # 如果有交易所订单ID，调用交易所API撤单
    if order.order_id:
        try:
            # 获取机器人配置
            bot = db.query(TradingBot).filter(TradingBot.id == order.bot_id).first()
            if bot.config:
                config = json.loads(bot.config)
                exchange_api = ExchangeAPI(
                    exchange_id=bot.exchange,
                    api_key=config.get('api_key', settings.API_KEY),
                    api_secret=config.get('api_secret', settings.API_SECRET)
                )

                # 调用交易所API撤单
                await exchange_api.cancel_order(order.order_id, bot.trading_pair)

        except Exception as e:
            # 记录错误但继续更新本地状态
            print(f"交易所撤单失败: {e}")

    # 更新订单状态
    order.status = "cancelled"
    db.commit()

    return {"message": "订单已取消", "order_id": order_id}


@router.post("/batch/cancel")
async def batch_cancel_orders(
    bot_id: int,
    status_filter: str = "pending",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量取消订单"""
    # 验证机器人权限
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
        )

    # 获取要取消的订单
    orders = db.query(GridOrder).filter(
        GridOrder.bot_id == bot_id,
        GridOrder.status == status_filter
    ).all()

    if not orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到符合条件的订单"
        )

    cancelled_count = 0
    failed_count = 0

    # 初始化交易所API
    exchange_api = None
    if bot.config:
        config = json.loads(bot.config)
        exchange_api = ExchangeAPI(
            exchange_id=bot.exchange,
            api_key=config.get('api_key', settings.API_KEY),
            api_secret=config.get('api_secret', settings.API_SECRET)
        )

    # 批量取消订单
    for order in orders:
        try:
            # 如果有交易所订单ID，调用交易所API撤单
            if order.order_id and exchange_api:
                await exchange_api.cancel_order(order.order_id, bot.trading_pair)

            # 更新订单状态
            order.status = "cancelled"
            cancelled_count += 1

        except Exception as e:
            print(f"取消订单 {order.id} 失败: {e}")
            failed_count += 1

    db.commit()

    return {
        "message": f"批量撤单完成",
        "total": len(orders),
        "cancelled": cancelled_count,
        "failed": failed_count
    }


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    new_status: str,
    filled_amount: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新订单状态"""
    # 验证订单和权限
    order = db.query(GridOrder).join(
        TradingBot,
        GridOrder.bot_id == TradingBot.id
    ).filter(
        GridOrder.id == order_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在或无权访问"
        )

    # 验证新状态
    valid_statuses = ["pending", "filled", "cancelled", "failed", "partial"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的状态值。有效值为: {', '.join(valid_statuses)}"
        )

    # 更新状态
    order.status = new_status

    # 如果提供了成交数量，更新成交信息
    if filled_amount is not None:
        order.filled_amount = filled_amount
        if new_status in ["filled", "partial"]:
            order.filled_at = datetime.now()

    db.commit()
    db.refresh(order)

    return {"message": "订单状态已更新", "order_id": order_id, "status": new_status}


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取订单详情"""
    order = db.query(GridOrder).join(
        TradingBot,
        GridOrder.bot_id == TradingBot.id
    ).filter(
        GridOrder.id == order_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在或无权访问"
        )

    return order
