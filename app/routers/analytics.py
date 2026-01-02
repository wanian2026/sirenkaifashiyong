"""
数据分析API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.analytics import AnalyticsEngine
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取仪表盘总览数据

    包括:
    - 机器人统计（总数、运行中、已停止）
    - 交易统计（总数、胜率、盈利/亏损）
    - 盈亏统计（总盈亏、今日盈亏、最大盈利/亏损）
    - 性能指标（胜率、投资回报率）
    - 最近交易记录
    """
    try:
        analytics = AnalyticsEngine(db)
        summary = analytics.get_dashboard_summary(current_user.id)
        return summary
    except Exception as e:
        logger.error(f"获取仪表盘数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仪表盘数据失败: {str(e)}"
        )


@router.get("/profit-curve")
async def get_profit_curve(
    bot_id: Optional[int] = Query(None, description="机器人ID，不指定则查询全部"),
    period: str = Query("7d", description="时间周期: 1d, 7d, 30d, 90d, all"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取收益曲线数据

    参数:
    - bot_id: 机器人ID（可选）
    - period: 时间周期 (1d, 7d, 30d, 90d, all)

    返回:
    - dates: 日期列表
    - profit_curve: 累计收益曲线
    - daily_pnls: 每日盈亏
    - max_drawdown: 最大回撤
    - drawdowns: 回撤数据
    """
    try:
        analytics = AnalyticsEngine(db)
        profit_curve = analytics.get_profit_curve(
            user_id=current_user.id,
            bot_id=bot_id,
            period=period
        )
        return profit_curve
    except Exception as e:
        logger.error(f"获取收益曲线失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取收益曲线失败: {str(e)}"
        )


@router.get("/trade-statistics")
async def get_trade_statistics(
    bot_id: Optional[int] = Query(None, description="机器人ID，不指定则查询全部"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取交易统计数据

    返回:
    - total_trades: 总交易次数
    - winning_trades: 盈利交易次数
    - losing_trades: 亏损交易次数
    - win_rate: 胜率 (%)
    - profit_factor: 盈利因子
    - average_win: 平均盈利
    - average_loss: 平均亏损
    - largest_win: 最大盈利
    - largest_loss: 最大亏损
    - average_trade: 平均交易盈亏
    - pair_statistics: 按交易对统计
    """
    try:
        analytics = AnalyticsEngine(db)
        stats = analytics.get_trade_statistics(
            user_id=current_user.id,
            bot_id=bot_id
        )
        return stats
    except Exception as e:
        logger.error(f"获取交易统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取交易统计失败: {str(e)}"
        )


@router.get("/bot/{bot_id}/performance")
async def get_bot_performance(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定机器人的性能数据

    返回:
    - 基本信息（名称、交易对、策略、状态）
    - 交易统计（总交易、总盈利、总亏损、净盈利）
    - 订单统计（总数、待成交、已成交）
    - 性能指标（胜率、盈利因子、平均盈利）
    - 运行时间（运行时长、创建时间）
    - 配置信息
    """
    try:
        analytics = AnalyticsEngine(db)
        performance = analytics.get_bot_performance(
            user_id=current_user.id,
            bot_id=bot_id
        )

        if not performance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="机器人不存在"
            )

        return performance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取机器人性能失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取机器人性能失败: {str(e)}"
        )


@router.get("/hourly-trades")
async def get_hourly_trades(
    bot_id: Optional[int] = Query(None, description="机器人ID，不指定则查询全部"),
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取每小时交易统计（用于热力图）

    返回:
    - period: 统计周期
    - heatmap_data: 热力图数据
      - day: 星期几 (0=周日, 1=周一, ..., 6=周六)
      - hour: 小时 (0-23)
      - trades: 交易次数
      - profit: 总盈利
    """
    try:
        analytics = AnalyticsEngine(db)
        hourly_trades = analytics.get_hourly_trades(
            user_id=current_user.id,
            bot_id=bot_id,
            days=days
        )
        return hourly_trades
    except Exception as e:
        logger.error(f"获取每小时交易统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取每小时交易统计失败: {str(e)}"
        )


@router.get("/overview")
async def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取数据分析总览

    一次性获取多个关键指标，用于仪表盘快速加载
    """
    try:
        analytics = AnalyticsEngine(db)

        # 并行获取多个数据
        dashboard = analytics.get_dashboard_summary(current_user.id)
        profit_curve = analytics.get_profit_curve(
            user_id=current_user.id,
            bot_id=None,
            period="7d"
        )
        trade_stats = analytics.get_trade_statistics(
            user_id=current_user.id,
            bot_id=None
        )

        return {
            "dashboard": dashboard,
            "profit_curve": profit_curve,
            "trade_statistics": trade_stats,
            "timestamp": dashboard.get("timestamp")
        }
    except Exception as e:
        logger.error(f"获取分析总览失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分析总览失败: {str(e)}"
        )
