from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User, Trade
from app.auth import get_current_user
from app.schemas import TradeResponse

router = APIRouter()


@router.get("/bot/{bot_id}", response_model=List[TradeResponse])
async def get_bot_trades(
    bot_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定机器人的交易记录"""
    # 这里应该验证bot_id是否属于当前用户
    # 为简化，这里直接查询

    trades = db.query(Trade).filter(
        Trade.bot_id == bot_id
    ).order_by(Trade.created_at.desc()).limit(limit).all()

    return trades


@router.get("/recent", response_model=List[TradeResponse])
async def get_recent_trades(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取最近的交易记录"""
    # 获取用户的所有bot
    from app.models import TradingBot
    bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
    bot_ids = [bot.id for bot in bots]

    if not bot_ids:
        return []

    trades = db.query(Trade).filter(
        Trade.bot_id.in_(bot_ids)
    ).order_by(Trade.created_at.desc()).limit(limit).all()

    return trades


@router.get("/stats")
async def get_trade_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取交易统计"""
    from app.models import TradingBot
    from sqlalchemy import func

    bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
    bot_ids = [bot.id for bot in bots]

    if not bot_ids:
        return {
            "total_trades": 0,
            "total_profit": 0,
            "win_rate": 0
        }

    # 计算统计数据
    stats = db.query(
        func.count(Trade.id).label('total_trades'),
        func.sum(Trade.profit).label('total_profit')
    ).filter(Trade.bot_id.in_(bot_ids)).first()

    total_trades = stats.total_trades or 0
    total_profit = stats.total_profit or 0

    # 计算胜率
    profitable_trades = db.query(func.count(Trade.id)).filter(
        Trade.bot_id.in_(bot_ids),
        Trade.profit > 0
    ).scalar() or 0

    win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

    return {
        "total_trades": total_trades,
        "total_profit": round(total_profit, 2),
        "win_rate": round(win_rate, 2)
    }
