"""
机器人性能统计和资源监控模块
提供机器人性能分析、资源监控等功能
"""

import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models import TradingBot, Trade, GridOrder
from collections import defaultdict

logger = logging.getLogger(__name__)


class BotPerformanceTracker:
    """机器人性能跟踪器"""

    def __init__(self, db: Session):
        self.db = db

    def get_bot_performance_stats(
        self,
        bot_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取机器人性能统计

        Args:
            bot_id: 机器人ID
            days: 统计天数

        Returns:
            性能统计数据
        """
        start_date = datetime.now() - timedelta(days=days)

        # 查询交易记录
        trades = self.db.query(Trade).filter(
            Trade.bot_id == bot_id,
            Trade.created_at >= start_date
        ).all()

        # 查询订单记录
        orders = self.db.query(GridOrder).filter(
            GridOrder.bot_id == bot_id,
            GridOrder.created_at >= start_date
        ).all()

        # 计算基本统计
        total_trades = len(trades)
        total_profit = sum(trade.profit for trade in trades)
        total_fees = sum(trade.fee for trade in trades)
        net_profit = total_profit - total_fees

        # 计算盈亏交易数
        profit_trades = len([t for t in trades if t.profit > 0])
        loss_trades = len([t for t in trades if t.profit < 0])
        win_rate = (profit_trades / total_trades * 100) if total_trades > 0 else 0

        # 计算平均盈利/亏损
        avg_profit = sum(t.profit for t in trades if t.profit > 0) / profit_trades if profit_trades > 0 else 0
        avg_loss = sum(t.profit for t in trades if t.profit < 0) / loss_trades if loss_trades > 0 else 0

        # 计算盈亏比
        profit_loss_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0

        # 订单统计
        total_orders = len(orders)
        filled_orders = len([o for o in orders if o.status == "filled"])
        pending_orders = len([o for o in orders if o.status == "pending"])
        fill_rate = (filled_orders / total_orders * 100) if total_orders > 0 else 0

        # 最大盈利/亏损
        max_profit = max((t.profit for t in trades), default=0)
        max_loss = min((t.profit for t in trades), default=0)

        # 连续盈亏统计
        consecutive_stats = self._calculate_consecutive_stats(trades)

        # 时间分布统计
        time_distribution = self._calculate_time_distribution(trades)

        return {
            "summary": {
                "period_days": days,
                "total_trades": total_trades,
                "total_orders": total_orders,
                "filled_orders": filled_orders,
                "pending_orders": pending_orders,
                "fill_rate": round(fill_rate, 2),
                "total_profit": round(total_profit, 2),
                "total_fees": round(total_fees, 2),
                "net_profit": round(net_profit, 2),
                "profit_trades": profit_trades,
                "loss_trades": loss_trades,
                "win_rate": round(win_rate, 2)
            },
            "performance": {
                "avg_profit": round(avg_profit, 2),
                "avg_loss": round(avg_loss, 2),
                "profit_loss_ratio": round(profit_loss_ratio, 2),
                "max_profit": round(max_profit, 2),
                "max_loss": round(max_loss, 2),
                "best_trade": {
                    "profit": round(max_profit, 2),
                    "trade_id": max(trades, key=lambda t: t.profit).id if trades else None
                },
                "worst_trade": {
                    "profit": round(max_loss, 2),
                    "trade_id": min(trades, key=lambda t: t.profit).id if trades else None
                }
            },
            "consecutive": consecutive_stats,
            "time_distribution": time_distribution
        }

    def _calculate_consecutive_stats(self, trades: List[Trade]) -> Dict[str, Any]:
        """计算连续盈亏统计"""
        if not trades:
            return {
                "max_consecutive_wins": 0,
                "max_consecutive_losses": 0
            }

        # 按时间排序
        sorted_trades = sorted(trades, key=lambda t: t.created_at)

        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_consecutive_wins = 0
        current_consecutive_losses = 0

        for trade in sorted_trades:
            if trade.profit > 0:
                current_consecutive_wins += 1
                current_consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_consecutive_wins)
            elif trade.profit < 0:
                current_consecutive_losses += 1
                current_consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)

        return {
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses
        }

    def _calculate_time_distribution(self, trades: List[Trade]) -> Dict[str, Any]:
        """计算时间分布统计"""
        if not trades:
            return {
                "hourly": {},
                "daily": {}
            }

        # 小时分布
        hourly_distribution = defaultdict(int)
        for trade in trades:
            if trade.created_at:
                hour = trade.created_at.hour
                hourly_distribution[hour] += 1

        # 星期分布
        daily_distribution = defaultdict(int)
        for trade in trades:
            if trade.created_at:
                weekday = trade.created_at.weekday()
                daily_distribution[weekday] += 1

        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        daily_distribution_named = {
            weekday_names[day]: count
            for day, count in daily_distribution.items()
        }

        return {
            "hourly": dict(hourly_distribution),
            "daily": daily_distribution_named
        }

    def get_bot_resource_usage(self, bot_id: int) -> Dict[str, Any]:
        """
        获取机器人资源使用情况

        Args:
            bot_id: 机器人ID

        Returns:
            资源使用情况
        """
        # 获取当前进程
        process = psutil.Process()

        # 查询机器人的订单和交易数量
        order_count = self.db.query(GridOrder).filter(
            GridOrder.bot_id == bot_id
        ).count()

        trade_count = self.db.query(Trade).filter(
            Trade.bot_id == bot_id
        ).count()

        # 获取内存使用
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()

        # 获取CPU使用
        cpu_percent = process.cpu_percent(interval=0.1)

        # 获取线程数
        num_threads = process.num_threads()

        # 获取文件句柄数
        num_fds = process.num_fds() if hasattr(process, 'num_fds') else 0

        return {
            "bot_id": bot_id,
            "timestamp": datetime.now().isoformat(),
            "orders": {
                "total": order_count,
                "pending": self.db.query(GridOrder).filter(
                    GridOrder.bot_id == bot_id,
                    GridOrder.status == "pending"
                ).count(),
                "filled": self.db.query(GridOrder).filter(
                    GridOrder.bot_id == bot_id,
                    GridOrder.status == "filled"
                ).count()
            },
            "trades": {
                "total": trade_count,
                "today": self.db.query(Trade).filter(
                    Trade.bot_id == bot_id,
                    Trade.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                ).count()
            },
            "system": {
                "memory_rss": memory_info.rss,
                "memory_vms": memory_info.vms,
                "memory_percent": memory_percent,
                "cpu_percent": cpu_percent,
                "num_threads": num_threads,
                "num_fds": num_fds
            }
        }

    def compare_bots_performance(
        self,
        bot_ids: List[int],
        days: int = 30
    ) -> Dict[str, Any]:
        """
        比较多个机器人的性能

        Args:
            bot_ids: 机器人ID列表
            days: 统计天数

        Returns:
            性能比较结果
        """
        comparisons = []

        for bot_id in bot_ids:
            try:
                stats = self.get_bot_performance_stats(bot_id, days)
                comparisons.append({
                    "bot_id": bot_id,
                    "net_profit": stats["summary"]["net_profit"],
                    "win_rate": stats["summary"]["win_rate"],
                    "total_trades": stats["summary"]["total_trades"],
                    "max_consecutive_wins": stats["consecutive"]["max_consecutive_wins"],
                    "max_consecutive_losses": stats["consecutive"]["max_consecutive_losses"]
                })
            except Exception as e:
                logger.error(f"获取机器人 {bot_id} 性能统计失败: {e}")
                continue

        # 按净利润排序
        comparisons.sort(key=lambda x: x["net_profit"], reverse=True)

        return {
            "period_days": days,
            "comparisons": comparisons,
            "best_bot": comparisons[0] if comparisons else None,
            "worst_bot": comparisons[-1] if comparisons else None
        }


class BotConfigTemplate:
    """机器人配置模板管理"""

    def __init__(self, db: Session):
        self.db = db

    def save_config_template(
        self,
        template_name: str,
        bot_id: int,
        user_id: int,
        description: str = None
    ) -> str:
        """
        保存机器人配置为模板

        Args:
            template_name: 模板名称
            bot_id: 机器人ID
            user_id: 用户ID
            description: 模板描述

        Returns:
            模板ID
        """
        bot = self.db.query(TradingBot).filter(
            TradingBot.id == bot_id,
            TradingBot.user_id == user_id
        ).first()

        if not bot:
            raise ValueError("机器人不存在")

        # 这里可以创建一个BotConfigTemplate模型来存储模板
        # 简化处理：使用JSON文件存储
        import os
        import json

        templates_dir = "bot_templates"
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)

        template_id = f"{user_id}_{template_name}_{int(datetime.now().timestamp())}"
        template_file = os.path.join(templates_dir, f"{template_id}.json")

        template_data = {
            "template_id": template_id,
            "template_name": template_name,
            "description": description,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "bot_config": {
                "exchange": bot.exchange,
                "trading_pair": bot.trading_pair,
                "strategy": bot.strategy,
                "config": json.loads(bot.config) if bot.config else {}
            }
        }

        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)

        logger.info(f"配置模板已保存: {template_id}")

        return template_id

    def load_config_template(
        self,
        template_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        加载配置模板

        Args:
            template_id: 模板ID
            user_id: 用户ID

        Returns:
            模板数据
        """
        import os
        import json

        template_file = os.path.join("bot_templates", f"{template_id}.json")

        if not os.path.exists(template_file):
            raise ValueError("模板不存在")

        with open(template_file, 'r', encoding='utf-8') as f:
            template_data = json.load(f)

        # 验证模板所有权
        if template_data.get("user_id") != user_id:
            raise ValueError("无权访问此模板")

        return template_data

    def list_config_templates(self, user_id: int) -> List[Dict[str, Any]]:
        """
        列出用户的所有配置模板

        Args:
            user_id: 用户ID

        Returns:
            模板列表
        """
        import os
        import json

        templates_dir = "bot_templates"
        if not os.path.exists(templates_dir):
            return []

        templates = []

        for filename in os.listdir(templates_dir):
            if not filename.endswith(".json"):
                continue

            try:
                with open(os.path.join(templates_dir, filename), 'r', encoding='utf-8') as f:
                    template_data = json.load(f)

                # 只返回当前用户的模板
                if template_data.get("user_id") == user_id:
                    templates.append({
                        "template_id": template_data["template_id"],
                        "template_name": template_data["template_name"],
                        "description": template_data.get("description", ""),
                        "created_at": template_data["created_at"],
                        "exchange": template_data["bot_config"]["exchange"],
                        "trading_pair": template_data["bot_config"]["trading_pair"],
                        "strategy": template_data["bot_config"]["strategy"]
                    })
            except Exception as e:
                logger.error(f"读取模板失败: {filename}, 错误: {e}")

        return sorted(templates, key=lambda x: x["created_at"], reverse=True)

    def delete_config_template(self, template_id: str, user_id: int) -> bool:
        """
        删除配置模板

        Args:
            template_id: 模板ID
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        import os

        # 验证模板所有权
        template_data = self.load_config_template(template_id, user_id)

        template_file = os.path.join("bot_templates", f"{template_id}.json")
        os.remove(template_file)

        logger.info(f"配置模板已删除: {template_id}")

        return True
