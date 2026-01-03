from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, date
from app.database import get_db
from app.models import User, Trade, TradingBot
from app.auth import get_current_user
from app.schemas import TradeResponse, TradeFilter
from sqlalchemy import func, extract, case
import csv
import io
from decimal import Decimal

router = APIRouter()


@router.get("/", response_model=List[TradeResponse])
async def get_trades(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    bot_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的交易记录"""
    query = db.query(Trade).join(TradingBot).filter(
        TradingBot.user_id == current_user.id
    )

    if bot_id:
        query = query.filter(Trade.bot_id == bot_id)

    trades = query.order_by(Trade.created_at.desc()).offset(offset).limit(limit).all()

    return trades


@router.get("/bot/{bot_id}", response_model=List[TradeResponse])
async def get_bot_trades(
    bot_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定机器人的交易记录"""
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

    trades = db.query(Trade).filter(
        Trade.bot_id == bot_id
    ).order_by(Trade.created_at.desc()).offset(offset).limit(limit).all()

    return trades


@router.get("/recent", response_model=List[TradeResponse])
async def get_recent_trades(
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取最近的交易记录"""
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
    bot_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取交易统计"""
    bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
    bot_ids = [bot.id for bot in bots]

    if not bot_ids:
        return {
            "total_trades": 0,
            "total_profit": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "average_profit": 0,
            "max_profit": 0,
            "max_loss": 0
        }

    # 构建查询条件
    query = db.query(Trade).filter(Trade.bot_id.in_(bot_ids))

    if bot_id:
        query = query.filter(Trade.bot_id == bot_id)

    if start_date:
        query = query.filter(Trade.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query = query.filter(Trade.created_at <= datetime.combine(end_date, datetime.max.time()))

    # 计算基本统计数据
    basic_stats = query.with_entities(
        func.count(Trade.id).label('total_trades'),
        func.sum(Trade.profit).label('total_profit'),
        func.avg(Trade.profit).label('average_profit'),
        func.max(Trade.profit).label('max_profit'),
        func.min(Trade.profit).label('min_profit')
    ).first()

    total_trades = basic_stats.total_trades or 0
    total_profit = basic_stats.total_profit or Decimal('0')
    average_profit = basic_stats.average_profit or Decimal('0')
    max_profit = basic_stats.max_profit or Decimal('0')
    min_profit = basic_stats.min_profit or Decimal('0')

    # 计算胜率
    profitable_trades = db.query(func.count(Trade.id)).filter(
        Trade.bot_id.in_(bot_ids),
        Trade.profit > 0
    ).scalar() or 0

    win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

    # 计算盈利因子（总盈利 / 总亏损）
    gross_profit = db.query(func.sum(Trade.profit)).filter(
        Trade.bot_id.in_(bot_ids),
        Trade.profit > 0
    ).scalar() or Decimal('0')

    gross_loss = abs(db.query(func.sum(Trade.profit)).filter(
        Trade.bot_id.in_(bot_ids),
        Trade.profit < 0
    ).scalar() or Decimal('0'))

    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else Decimal('0')

    return {
        "total_trades": total_trades,
        "total_profit": float(round(total_profit, 2)),
        "average_profit": float(round(average_profit, 2)),
        "win_rate": round(win_rate, 2),
        "profit_factor": float(round(profit_factor, 2)),
        "max_profit": float(round(max_profit, 2)),
        "max_loss": float(round(min_profit, 2)),
        "gross_profit": float(round(gross_profit, 2)),
        "gross_loss": float(round(gross_loss, 2))
    }


@router.get("/stats/daily")
async def get_daily_stats(
    bot_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取每日交易统计"""
    bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
    bot_ids = [bot.id for bot in bots]

    if not bot_ids:
        return {"data": []}

    query = db.query(
        func.date(Trade.created_at).label('date'),
        func.count(Trade.id).label('trades_count'),
        func.sum(Trade.profit).label('total_profit'),
        func.sum(case((Trade.profit > 0, 1), else_=0)).label('winning_trades'),
        func.sum(case((Trade.profit < 0, 1), else_=0)).label('losing_trades')
    ).filter(
        Trade.bot_id.in_(bot_ids),
        Trade.created_at >= datetime.now() - timedelta(days=days)
    )

    if bot_id:
        query = query.filter(Trade.bot_id == bot_id)

    daily_stats = query.group_by(
        func.date(Trade.created_at)
    ).order_by(
        func.date(Trade.created_at).desc()
    ).all()

    result = []
    for stat in daily_stats:
        result.append({
            "date": stat.date.isoformat() if stat.date else None,
            "trades_count": stat.trades_count or 0,
            "total_profit": float(stat.total_profit or 0),
            "winning_trades": stat.winning_trades or 0,
            "losing_trades": stat.losing_trades or 0,
            "win_rate": (stat.winning_trades / stat.trades_count * 100) if stat.trades_count else 0
        })

    return {"data": result}


@router.get("/stats/by-pair")
async def get_stats_by_trading_pair(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """按交易对统计"""
    bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
    bot_ids = [bot.id for bot in bots]

    if not bot_ids:
        return {"data": []}

    stats = db.query(
        Trade.trading_pair,
        func.count(Trade.id).label('trades_count'),
        func.sum(Trade.profit).label('total_profit'),
        func.avg(Trade.profit).label('average_profit')
    ).filter(
        Trade.bot_id.in_(bot_ids)
    ).group_by(
        Trade.trading_pair
    ).order_by(
        func.sum(Trade.profit).desc()
    ).all()

    result = []
    for stat in stats:
        result.append({
            "trading_pair": stat.trading_pair,
            "trades_count": stat.trades_count,
            "total_profit": float(stat.total_profit or 0),
            "average_profit": float(stat.average_profit or 0)
        })

    return {"data": result}


@router.get("/filter", response_model=List[TradeResponse])
async def filter_trades(
    bot_id: Optional[int] = None,
    trading_pair: Optional[str] = None,
    side: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_profit: Optional[float] = None,
    max_profit: Optional[float] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", regex="^(created_at|price|amount|profit)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """高级筛选交易记录"""
    bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
    bot_ids = [bot.id for bot in bots]

    if not bot_ids:
        return []

    query = db.query(Trade).filter(Trade.bot_id.in_(bot_ids))

    if bot_id:
        query = query.filter(Trade.bot_id == bot_id)
    if trading_pair:
        query = query.filter(Trade.trading_pair == trading_pair)
    if side:
        query = query.filter(Trade.side == side)
    if start_date:
        query = query.filter(Trade.created_at >= start_date)
    if end_date:
        query = query.filter(Trade.created_at <= end_date)
    if min_profit is not None:
        query = query.filter(Trade.profit >= min_profit)
    if max_profit is not None:
        query = query.filter(Trade.profit <= max_profit)

    # 排序
    sort_column = getattr(Trade, sort_by)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    trades = query.offset(offset).limit(limit).all()

    return trades


@router.get("/export")
async def export_trades(
    format: str = Query("csv", regex="^(csv|json)$"),
    bot_id: Optional[int] = None,
    trading_pair: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出交易记录"""
    bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
    bot_ids = [bot.id for bot in bots]

    if not bot_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有交易记录"
        )

    query = db.query(Trade).filter(Trade.bot_id.in_(bot_ids))

    if bot_id:
        query = query.filter(Trade.bot_id == bot_id)
    if trading_pair:
        query = query.filter(Trade.trading_pair == trading_pair)
    if start_date:
        query = query.filter(Trade.created_at >= start_date)
    if end_date:
        query = query.filter(Trade.created_at <= end_date)

    trades = query.order_by(Trade.created_at.desc()).all()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入标题
        writer.writerow([
            "ID", "Bot ID", "Trading Pair", "Side", "Price",
            "Amount", "Fee", "Profit", "Order ID", "Created At"
        ])

        # 写入数据
        for trade in trades:
            writer.writerow([
                trade.id,
                trade.bot_id,
                trade.trading_pair,
                trade.side,
                trade.price,
                trade.amount,
                trade.fee,
                trade.profit,
                trade.order_id,
                trade.created_at.isoformat()
            ])

        output.seek(0)

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=trades_{timestamp}.csv"
            }
        )

    elif format.lower() == "json":
        import json
        from pydantic import BaseModel

        class TradeExport(BaseModel):
            id: int
            bot_id: int
            order_id: str
            trading_pair: str
            side: str
            price: float
            amount: float
            fee: float
            profit: float
            created_at: datetime

        trades_data = [
            TradeExport(
                id=trade.id,
                bot_id=trade.bot_id,
                order_id=trade.order_id,
                trading_pair=trade.trading_pair,
                side=trade.side,
                price=trade.price,
                amount=trade.amount,
                fee=trade.fee,
                profit=trade.profit,
                created_at=trade.created_at
            ).model_dump()
            for trade in trades
        ]

        return {
            "export_time": datetime.now().isoformat(),
            "total_records": len(trades_data),
            "data": trades_data
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的导出格式"
        )
