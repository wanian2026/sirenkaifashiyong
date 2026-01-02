"""
数据分析模块
提供仪表盘、收益曲线、交易统计等分析功能
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app.models import TradingBot, Trade, GridOrder
import logging

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """数据分析引擎"""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_summary(self, user_id: int) -> Dict:
        """
        获取仪表盘总览数据

        Args:
            user_id: 用户ID

        Returns:
            仪表盘总览数据
        """
        # 统计机器人数量
        total_bots = self.db.query(TradingBot).filter(
            TradingBot.user_id == user_id
        ).count()

        running_bots = self.db.query(TradingBot).filter(
            and_(
                TradingBot.user_id == user_id,
                TradingBot.status == "running"
            )
        ).count()

        # 统计交易记录
        total_trades = self.db.query(Trade).join(TradingBot).filter(
            TradingBot.user_id == user_id
        ).count()

        # 计算总盈亏
        total_pnl = self.db.query(func.sum(Trade.profit)).join(TradingBot).filter(
            TradingBot.user_id == user_id
        ).scalar() or 0

        # 计算今日盈亏
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_pnl = self.db.query(func.sum(Trade.profit)).join(TradingBot).filter(
            and_(
                TradingBot.user_id == user_id,
                Trade.created_at >= today_start
            )
        ).scalar() or 0

        # 计算胜率
        winning_trades = self.db.query(Trade).join(TradingBot).filter(
            and_(
                TradingBot.user_id == user_id,
                Trade.profit > 0
            )
        ).count()

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # 计算平均盈亏
        avg_profit = self.db.query(func.avg(Trade.profit)).join(TradingBot).filter(
            TradingBot.user_id == user_id
        ).scalar() or 0

        # 最大单笔盈利/亏损
        max_profit = self.db.query(func.max(Trade.profit)).join(TradingBot).filter(
            and_(
                TradingBot.user_id == user_id,
                Trade.profit > 0
            )
        ).scalar() or 0

        max_loss = self.db.query(func.min(Trade.profit)).join(TradingBot).filter(
            TradingBot.user_id == user_id
        ).scalar() or 0

        # 最近交易
        recent_trades = self.db.query(Trade).join(TradingBot).filter(
            TradingBot.user_id == user_id
        ).order_by(desc(Trade.created_at)).limit(5).all()

        recent_trades_list = [
            {
                "id": trade.id,
                "bot_id": trade.bot_id,
                "trading_pair": trade.trading_pair,
                "side": trade.side,
                "price": trade.price,
                "amount": trade.amount,
                "profit": trade.profit,
                "created_at": trade.created_at.isoformat()
            }
            for trade in recent_trades
        ]

        # 投资金额统计
        total_investment = self.db.query(func.sum(
            func.cast(func.json_extract(TradingBot.config, '$.investment_amount'), type_=float)
        )).filter(
            TradingBot.user_id == user_id
        ).scalar() or 0

        return {
            "bots": {
                "total": total_bots,
                "running": running_bots,
                "stopped": total_bots - running_bots
            },
            "trades": {
                "total": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": total_trades - winning_trades
            },
            "pnl": {
                "total": total_pnl,
                "today": today_pnl,
                "average": avg_profit,
                "max_profit": max_profit,
                "max_loss": max_loss
            },
            "performance": {
                "win_rate": win_rate,
                "total_investment": total_investment,
                "roi": (total_pnl / total_investment * 100) if total_investment > 0 else 0
            },
            "recent_trades": recent_trades_list,
            "timestamp": datetime.now().isoformat()
        }

    def get_profit_curve(
        self,
        user_id: int,
        bot_id: Optional[int] = None,
        period: str = "7d"
    ) -> Dict:
        """
        获取收益曲线数据

        Args:
            user_id: 用户ID
            bot_id: 机器人ID（可选）
            period: 时间周期 (1d, 7d, 30d, 90d, all)

        Returns:
            收益曲线数据
        """
        # 确定时间范围
        end_date = datetime.now()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = datetime.min

        # 查询交易记录
        query = self.db.query(
            func.date(Trade.created_at).label('date'),
            func.sum(Trade.profit).label('daily_pnl'),
            func.count(Trade.id).label('trade_count')
        ).join(TradingBot).filter(
            and_(
                TradingBot.user_id == user_id,
                Trade.created_at >= start_date
            )
        ).group_by(func.date(Trade.created_at)).order_by(func.date(Trade.created_at))

        if bot_id:
            query = query.filter(Trade.bot_id == bot_id)

        results = query.all()

        # 构建收益曲线
        cumulative_pnl = 0
        profit_curve = []
        dates = []
        daily_pnls = []

        for row in results:
            date_str = row.date.strftime('%Y-%m-%d')
            daily_pnl = row.daily_pnl or 0
            cumulative_pnl += daily_pnl

            profit_curve.append(cumulative_pnl)
            dates.append(date_str)
            daily_pnls.append(daily_pnl)

        # 计算回撤
        drawdowns = self._calculate_drawdowns(profit_curve)

        return {
            "period": period,
            "dates": dates,
            "profit_curve": profit_curve,
            "daily_pnls": daily_pnls,
            "cumulative_pnl": cumulative_pnl,
            "max_drawdown": min(drawdowns) if drawdowns else 0,
            "drawdowns": drawdowns,
            "data_points": len(profit_curve)
        }

    def _calculate_drawdowns(self, profit_curve: List[float]) -> List[float]:
        """计算回撤"""
        if not profit_curve:
            return []

        drawdowns = []
        peak = profit_curve[0]

        for value in profit_curve:
            if value > peak:
                peak = value
            drawdown = (value - peak) / peak * 100 if peak != 0 else 0
            drawdowns.append(drawdown)

        return drawdowns

    def get_trade_statistics(
        self,
        user_id: int,
        bot_id: Optional[int] = None
    ) -> Dict:
        """
        获取交易统计数据

        Args:
            user_id: 用户ID
            bot_id: 机器人ID（可选）

        Returns:
            交易统计数据
        """
        # 基础统计
        query = self.db.query(Trade).join(TradingBot).filter(
            TradingBot.user_id == user_id
        )

        if bot_id:
            query = query.filter(Trade.bot_id == bot_id)

        trades = query.all()

        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "average_win": 0,
                "average_loss": 0,
                "largest_win": 0,
                "largest_loss": 0,
                "average_trade": 0
            }

        total_trades = len(trades)
        winning_trades = [t for t in trades if t.profit > 0]
        losing_trades = [t for t in trades if t.profit < 0]

        # 胜率
        win_rate = len(winning_trades) / total_trades * 100

        # 盈利因子
        total_profit = sum(t.profit for t in winning_trades)
        total_loss = abs(sum(t.profit for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        # 平均盈利/亏损
        avg_win = total_profit / len(winning_trades) if winning_trades else 0
        avg_loss = total_loss / len(losing_trades) if losing_trades else 0

        # 最大盈利/亏损
        largest_win = max(t.profit for t in winning_trades) if winning_trades else 0
        largest_loss = min(t.profit for t in losing_trades) if losing_trades else 0

        # 平均交易盈亏
        avg_trade = sum(t.profit for t in trades) / total_trades

        # 交易对统计
        pair_stats = {}
        for trade in trades:
            pair = trade.trading_pair
            if pair not in pair_stats:
                pair_stats[pair] = {
                    "trades": 0,
                    "profit": 0,
                    "winning": 0
                }
            pair_stats[pair]["trades"] += 1
            pair_stats[pair]["profit"] += trade.profit
            if trade.profit > 0:
                pair_stats[pair]["winning"] += 1

        # 计算每个交易对的胜率
        for pair in pair_stats:
            pair_stats[pair]["win_rate"] = (
                pair_stats[pair]["winning"] / pair_stats[pair]["trades"] * 100
                if pair_stats[pair]["trades"] > 0
                else 0
            )

        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "average_win": avg_win,
            "average_loss": avg_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "average_trade": avg_trade,
            "total_profit": total_profit,
            "total_loss": total_loss,
            "net_profit": total_profit - total_loss,
            "pair_statistics": pair_stats,
            "timestamp": datetime.now().isoformat()
        }

    def get_bot_performance(
        self,
        user_id: int,
        bot_id: int
    ) -> Dict:
        """
        获取机器人性能数据

        Args:
            user_id: 用户ID
            bot_id: 机器人ID

        Returns:
            机器人性能数据
        """
        bot = self.db.query(TradingBot).filter(
            and_(
                TradingBot.id == bot_id,
                TradingBot.user_id == user_id
            )
        ).first()

        if not bot:
            return {}

        # 交易统计
        trades = self.db.query(Trade).filter(Trade.bot_id == bot_id).all()

        total_trades = len(trades)
        total_profit = sum(t.profit for t in trades if t.profit > 0)
        total_loss = abs(sum(t.profit for t in trades if t.profit < 0))
        net_profit = total_profit - total_loss

        # 订单统计
        orders = self.db.query(GridOrder).filter(GridOrder.bot_id == bot_id).all()
        pending_orders = [o for o in orders if o.status == "pending"]
        filled_orders = [o for o in orders if o.status == "filled"]

        # 运行时间
        if bot.created_at:
            running_time = datetime.now() - bot.created_at
            running_hours = running_time.total_seconds() / 3600
        else:
            running_hours = 0

        return {
            "bot_id": bot_id,
            "bot_name": bot.name,
            "trading_pair": bot.trading_pair,
            "strategy": bot.strategy,
            "status": bot.status,
            "trades": {
                "total": total_trades,
                "total_profit": total_profit,
                "total_loss": total_loss,
                "net_profit": net_profit
            },
            "orders": {
                "total": len(orders),
                "pending": len(pending_orders),
                "filled": len(filled_orders)
            },
            "performance": {
                "win_rate": (len([t for t in trades if t.profit > 0]) / total_trades * 100) if total_trades > 0 else 0,
                "profit_factor": (total_profit / total_loss) if total_loss > 0 else 0,
                "avg_profit": (total_profit / len([t for t in trades if t.profit > 0])) if any(t.profit > 0 for t in trades) else 0
            },
            "runtime": {
                "hours": running_hours,
                "created_at": bot.created_at.isoformat() if bot.created_at else None
            },
            "config": bot.config,
            "timestamp": datetime.now().isoformat()
        }

    def get_hourly_trades(
        self,
        user_id: int,
        bot_id: Optional[int] = None,
        days: int = 7
    ) -> Dict:
        """
        获取每小时交易统计（用于热力图）

        Args:
            user_id: 用户ID
            bot_id: 机器人ID（可选）
            days: 统计天数

        Returns:
            每小时交易统计
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query = self.db.query(
            func.extract('dow', Trade.created_at).label('day_of_week'),
            func.extract('hour', Trade.created_at).label('hour'),
            func.count(Trade.id).label('trade_count'),
            func.sum(Trade.profit).label('total_profit')
        ).join(TradingBot).filter(
            and_(
                TradingBot.user_id == user_id,
                Trade.created_at >= start_date
            )
        ).group_by(
            func.extract('dow', Trade.created_at),
            func.extract('hour', Trade.created_at)
        )

        if bot_id:
            query = query.filter(Trade.bot_id == bot_id)

        results = query.all()

        # 构建热力图数据 (7天 x 24小时)
        heatmap_data = []
        for row in results:
            heatmap_data.append({
                "day": int(row.day_of_week),
                "hour": int(row.hour),
                "trades": int(row.trade_count),
                "profit": float(row.total_profit or 0)
            })

        return {
            "period": f"{days}d",
            "heatmap_data": heatmap_data,
            "timestamp": datetime.now().isoformat()
        }
