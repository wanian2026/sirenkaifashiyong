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
from app.schemas import OrderCreate, OrderResponse, OrderUpdate
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """创建订单（支持限价单、市价单、止损单、止盈单）"""
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

    # 获取交易对
    trading_pair = order_data.trading_pair or bot.trading_pair

    # 创建订单记录
    new_order = GridOrder(
        bot_id=order_data.bot_id,
        level=order_data.level or 0,
        order_type=order_data.order_type,  # buy or sell
        order_category=order_data.order_category,  # limit, market, stop_loss, take_profit
        price=order_data.price or 0,
        amount=order_data.amount,
        side=order_data.order_type,
        trading_pair=trading_pair,
        stop_price=order_data.stop_price,
        stop_loss_price=order_data.stop_loss_price,
        take_profit_price=order_data.take_profit_price,
        max_retry=order_data.max_retry or 3,
        status="pending"
    )

    # 获取API密钥并调用交易所下单
    try:
        if bot.config:
            config = json.loads(bot.config)
            exchange_api = ExchangeAPI(
                exchange_id=bot.exchange,
                api_key=config.get('api_key'),
                api_secret=config.get('api_secret')
            )

            # 根据订单类型调用不同的下单接口
            if order_data.order_category == "market":
                result = await exchange_api.create_market_order(
                    symbol=trading_pair,
                    side=order_data.order_type,
                    amount=order_data.amount
                )
                new_order.order_id = result["id"]
                new_order.exchange_order_id = result["id"]

                # 市价单可能立即成交
                if result["status"] == "closed":
                    new_order.status = "filled"
                    new_order.filled_amount = result.get("filled", 0)
                    new_order.filled_price = result.get("price", 0)
                    new_order.filled_at = datetime.now()

            elif order_data.order_category == "limit":
                result = await exchange_api.create_limit_order(
                    symbol=trading_pair,
                    side=order_data.order_type,
                    amount=order_data.amount,
                    price=order_data.price
                )
                new_order.order_id = result["id"]
                new_order.exchange_order_id = result["id"]

            elif order_data.order_category == "stop_loss":
                result = await exchange_api.create_stop_loss_order(
                    symbol=trading_pair,
                    side=order_data.order_type,
                    amount=order_data.amount,
                    stop_price=order_data.stop_price or order_data.stop_loss_price
                )
                new_order.order_id = result["id"]
                new_order.exchange_order_id = result["id"]

            elif order_data.order_category == "take_profit":
                result = await exchange_api.create_take_profit_order(
                    symbol=trading_pair,
                    side=order_data.order_type,
                    amount=order_data.amount,
                    take_profit_price=order_data.take_profit_price
                )
                new_order.order_id = result["id"]
                new_order.exchange_order_id = result["id"]

            logger.info(f"订单创建成功: {new_order.id}, 交易所订单ID: {new_order.order_id}")

    except Exception as e:
        new_order.status = "failed"
        new_order.error_message = str(e)
        logger.error(f"订单创建失败: {e}")

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    bot_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    order_type: Optional[str] = None,
    order_category: Optional[str] = None,
    trading_pair: Optional[str] = None,
    side: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """获取订单列表（支持多种筛选条件）"""
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

    if order_category:
        query = query.filter(GridOrder.order_category == order_category)

    if trading_pair:
        query = query.filter(GridOrder.trading_pair == trading_pair)

    if side:
        query = query.filter(GridOrder.side == side)

    # 分页
    query = query.order_by(GridOrder.created_at.desc())
    orders = query.offset(offset).limit(limit).all()

    return orders


@router.get("/stats/summary")
async def get_order_stats(
    bot_id: Optional[int] = None,
    current_user: User = Depends(get_optional_current_user),
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
    current_user: User = Depends(get_optional_current_user),
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

    # 检查订单状态
    if order.status in ["filled", "cancelled"]:
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
                    api_key=config.get('api_key'),
                    api_secret=config.get('api_secret')
                )

                # 调用交易所API撤单
                await exchange_api.cancel_order(order.order_id, order.trading_pair)
                logger.info(f"交易所撤单成功: {order.order_id}")

        except Exception as e:
            # 记录错误但继续更新本地状态
            logger.warning(f"交易所撤单失败: {e}")

    # 更新订单状态
    order.status = "cancelled"
    order.updated_at = datetime.now()
    db.commit()

    return {"message": "订单已取消", "order_id": order_id, "status": "cancelled"}


@router.post("/batch/cancel")
async def batch_cancel_orders(
    bot_id: int,
    status_filter: str = "pending",
    current_user: User = Depends(get_optional_current_user),
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
    filled_price: Optional[float] = None,
    error_message: Optional[str] = None,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """更新订单状态（支持部分成交处理）"""
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
    order.updated_at = datetime.now()

    # 如果提供了成交数量，更新成交信息
    if filled_amount is not None:
        order.filled_amount = filled_amount

        # 判断是否完全成交或部分成交
        if filled_amount >= order.amount:
            order.status = "filled"
            order.filled_at = datetime.now()
        elif filled_amount > 0:
            order.status = "partial"

    # 如果提供了成交价格，更新成交价格
    if filled_price is not None:
        order.filled_price = filled_price

    # 如果提供了错误信息，更新错误信息
    if error_message is not None:
        order.error_message = error_message

    db.commit()
    db.refresh(order)

    return {
        "message": "订单状态已更新",
        "order_id": order_id,
        "status": new_status,
        "filled_amount": order.filled_amount
    }


@router.post("/{order_id}/retry")
async def retry_order(
    order_id: int,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """重试失败的订单"""
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

    # 检查订单状态
    if order.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"订单状态为 {order.status}，只有失败的订单可以重试"
        )

    # 检查重试次数
    if order.retry_count >= order.max_retry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"已达到最大重试次数 ({order.max_retry})"
        )

    # 更新重试信息
    order.retry_count += 1
    order.last_retry_at = datetime.now()
    order.status = "pending"
    order.error_message = None
    order.updated_at = datetime.now()

    db.commit()

    # 重新下单
    try:
        # 获取机器人配置
        bot = db.query(TradingBot).filter(TradingBot.id == order.bot_id).first()
        if bot.config:
            config = json.loads(bot.config)
            exchange_api = ExchangeAPI(
                exchange_id=bot.exchange,
                api_key=config.get('api_key'),
                api_secret=config.get('api_secret')
            )

            # 根据订单类型重新下单
            if order.order_category == "market":
                result = await exchange_api.create_market_order(
                    symbol=order.trading_pair,
                    side=order.side,
                    amount=order.amount
                )
            elif order.order_category == "limit":
                result = await exchange_api.create_limit_order(
                    symbol=order.trading_pair,
                    side=order.side,
                    amount=order.amount,
                    price=order.price
                )
            elif order.order_category == "stop_loss":
                result = await exchange_api.create_stop_loss_order(
                    symbol=order.trading_pair,
                    side=order.side,
                    amount=order.amount,
                    stop_price=order.stop_price
                )
            elif order.order_category == "take_profit":
                result = await exchange_api.create_take_profit_order(
                    symbol=order.trading_pair,
                    side=order.side,
                    amount=order.amount,
                    take_profit_price=order.take_profit_price
                )

            # 更新订单信息
            order.order_id = result["id"]
            order.exchange_order_id = result["id"]
            order.error_message = None

            # 市价单可能立即成交
            if result["status"] == "closed":
                order.status = "filled"
                order.filled_amount = result.get("filled", 0)
                order.filled_price = result.get("price", 0)
                order.filled_at = datetime.now()

            db.commit()

            logger.info(f"订单重试成功: {order.id}, 重试次数: {order.retry_count}")

            return {
                "message": "订单重试成功",
                "order_id": order_id,
                "retry_count": order.retry_count,
                "status": order.status
            }

    except Exception as e:
        order.status = "failed"
        order.error_message = str(e)
        db.commit()

        logger.error(f"订单重试失败: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"订单重试失败: {e}"
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_optional_current_user),
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


@router.post("/{order_id}/sync")
async def sync_order(
    order_id: int,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """同步订单状态（从交易所获取最新状态）"""
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

    # 检查是否有交易所订单ID
    if not order.order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单没有交易所订单ID，无法同步"
        )

    # 从交易所获取订单状态
    try:
        # 获取机器人配置
        bot = db.query(TradingBot).filter(TradingBot.id == order.bot_id).first()
        if bot.config:
            config = json.loads(bot.config)
            exchange_api = ExchangeAPI(
                exchange_id=bot.exchange,
                api_key=config.get('api_key'),
                api_secret=config.get('api_secret')
            )

            # 获取交易所订单状态
            exchange_order = await exchange_api.get_order(order.order_id, order.trading_pair)

            # 更新本地订单状态
            order.status = exchange_order["status"]
            order.filled_amount = exchange_order.get("filled", 0)
            order.filled_price = exchange_order.get("price") or order.filled_price

            # 判断订单状态
            if exchange_order["status"] == "closed":
                order.status = "filled"
                order.filled_at = datetime.now()
            elif exchange_order["status"] == "open":
                order.status = "pending"
            elif exchange_order["status"] == "canceled":
                order.status = "cancelled"
            elif exchange_order["status"] == "rejected":
                order.status = "failed"

            # 更新手续费
            if exchange_order.get("fee"):
                fee = exchange_order["fee"]
                order.fee = fee.get("cost", 0) if isinstance(fee, dict) else 0

            order.updated_at = datetime.now()
            db.commit()

            logger.info(f"订单同步成功: {order_id}, 状态: {order.status}")

            return {
                "message": "订单同步成功",
                "order_id": order_id,
                "status": order.status,
                "filled_amount": order.filled_amount,
                "exchange_status": exchange_order["status"]
            }

    except Exception as e:
        logger.error(f"订单同步失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"订单同步失败: {e}"
        )


@router.post("/sync/all")
async def sync_all_orders(
    bot_id: Optional[int] = None,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """批量同步订单状态"""
    # 获取待同步的订单列表
    query = db.query(GridOrder).join(
        TradingBot,
        GridOrder.bot_id == TradingBot.id
    ).filter(
        TradingBot.user_id == current_user.id,
        GridOrder.status.in_(["pending", "partial"]),
        GridOrder.order_id.isnot(None)
    )

    if bot_id is not None:
        query = query.filter(GridOrder.bot_id == bot_id)

    orders = query.all()

    if not orders:
        return {
            "message": "没有需要同步的订单",
            "total": 0,
            "synced": 0,
            "failed": 0
        }

    synced_count = 0
    failed_count = 0
    errors = []

    # 批量同步订单
    for order in orders:
        try:
            # 获取机器人配置
            bot = db.query(TradingBot).filter(TradingBot.id == order.bot_id).first()
            if bot.config:
                config = json.loads(bot.config)
                exchange_api = ExchangeAPI(
                    exchange_id=bot.exchange,
                    api_key=config.get('api_key'),
                    api_secret=config.get('api_secret')
                )

                # 获取交易所订单状态
                exchange_order = await exchange_api.get_order(order.order_id, order.trading_pair)

                # 更新本地订单状态
                order.status = exchange_order["status"]
                order.filled_amount = exchange_order.get("filled", 0)
                order.filled_price = exchange_order.get("price") or order.filled_price

                # 判断订单状态
                if exchange_order["status"] == "closed":
                    order.status = "filled"
                    order.filled_at = datetime.now()
                elif exchange_order["status"] == "open":
                    order.status = "pending"
                elif exchange_order["status"] == "canceled":
                    order.status = "cancelled"
                elif exchange_order["status"] == "rejected":
                    order.status = "failed"

                # 更新手续费
                if exchange_order.get("fee"):
                    fee = exchange_order["fee"]
                    order.fee = fee.get("cost", 0) if isinstance(fee, dict) else 0

                order.updated_at = datetime.now()

                synced_count += 1

        except Exception as e:
            failed_count += 1
            errors.append({"order_id": order.id, "error": str(e)})
            logger.error(f"同步订单 {order.id} 失败: {e}")

    db.commit()

    logger.info(f"批量同步订单完成: 总数={len(orders)}, 成功={synced_count}, 失败={failed_count}")

    return {
        "message": "批量同步完成",
        "total": len(orders),
        "synced": synced_count,
        "failed": failed_count,
        "errors": errors
    }
