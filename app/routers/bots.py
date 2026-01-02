from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, TradingBot
from app.auth import get_current_user
from app.schemas import BotCreate, BotResponse, BotStatus, BotUpdate
from app.strategies import HedgeGridStrategy
import json

router = APIRouter()

# 存储运行中的机器人实例
running_bots = {}


@router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建交易机器人"""
    new_bot = TradingBot(
        name=bot_data.name,
        exchange=bot_data.exchange,
        trading_pair=bot_data.trading_pair,
        strategy=bot_data.strategy,
        config=json.dumps(bot_data.config) if bot_data.config else None,
        user_id=current_user.id
    )

    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)

    return new_bot


@router.get("/", response_model=List[BotResponse])
async def get_bots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有机器人"""
    bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
    return bots


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定机器人"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )

    return bot


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: int,
    bot_update: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新机器人配置"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )

    # 如果机器人在运行，不允许修改配置
    if bot.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人运行中，无法修改配置，请先停止机器人"
        )

    # 更新字段
    if bot_update.name is not None:
        bot.name = bot_update.name
    if bot_update.exchange is not None:
        bot.exchange = bot_update.exchange
    if bot_update.trading_pair is not None:
        bot.trading_pair = bot_update.trading_pair
    if bot_update.strategy is not None:
        bot.strategy = bot_update.strategy
    if bot_update.config is not None:
        bot.config = json.dumps(bot_update.config)

    db.commit()
    db.refresh(bot)

    return bot


@router.post("/{bot_id}/start")
async def start_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启动机器人"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )

    if bot_id in running_bots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人已在运行中"
        )

    # 创建策略实例
    config = json.loads(bot.config) if bot.config else {}
    strategy = HedgeGridStrategy(
        trading_pair=bot.trading_pair,
        grid_levels=config.get('grid_levels', 10),
        grid_spacing=config.get('grid_spacing', 0.02),
        investment_amount=config.get('investment_amount', 1000)
    )

    # 初始化网格
    await strategy.initialize_grid()

    # 存储运行中的机器人
    running_bots[bot_id] = strategy

    # 更新数据库状态
    bot.status = "running"
    db.commit()

    return {"message": "机器人已启动", "bot_id": bot_id}


@router.post("/{bot_id}/stop")
async def stop_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """停止机器人"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )

    if bot_id not in running_bots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人未运行"
        )

    # 停止策略
    running_bots[bot_id].stop()
    del running_bots[bot_id]

    # 更新数据库状态
    bot.status = "stopped"
    db.commit()

    return {"message": "机器人已停止", "bot_id": bot_id}


@router.get("/{bot_id}/status", response_model=BotStatus)
async def get_bot_status(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取机器人状态"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )

    if bot_id not in running_bots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人未运行"
        )

    # 获取策略状态
    status = await running_bots[bot_id].get_strategy_status()

    return BotStatus(
        current_price=status['current_price'],
        total_invested=status['total_invested'],
        realized_profit=status['realized_profit'],
        pending_orders=status['pending_orders'],
        filled_orders=status['filled_orders']
    )


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除机器人"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )

    if bot_id in running_bots:
        running_bots[bot_id].stop()
        del running_bots[bot_id]

    db.delete(bot)
    db.commit()

    return {"message": "机器人已删除", "bot_id": bot_id}
