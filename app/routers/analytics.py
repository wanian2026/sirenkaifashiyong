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
from app.cache import cached, CacheKey, CacheManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 缓存TTL设置（秒）
CACHE_TTL_DASHBOARD = 60  # 仪表盘数据缓存1分钟
CACHE_TTL_PROFIT_CURVE = 30  # 收益曲线缓存30秒
CACHE_TTL_TRADE_STATS = 120  # 交易统计缓存2分钟
CACHE_TTL_BOT_PERFORMANCE = 60  # 机器人性能缓存1分钟
CACHE_TTL_HOURLY_TRADES = 300  # 每小时交易统计缓存5分钟

# 全局缓存管理器
cache_manager = CacheManager()


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
        # 生成缓存键
        cache_key = CacheKey.user(current_user.id) + ":dashboard"

        # 尝试从缓存获取
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            logger.debug(f"仪表盘数据缓存命中: user_id={current_user.id}")
            return cached_data

        # 缓存未命中，查询数据库
        analytics = AnalyticsEngine(db)
        summary = analytics.get_dashboard_summary(current_user.id)

        # 存入缓存
        await cache_manager.set(cache_key, summary, CACHE_TTL_DASHBOARD)
        logger.debug(f"仪表盘数据已缓存: user_id={current_user.id}")

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
        # 生成缓存键
        bot_part = f"bot:{bot_id}" if bot_id else "all"
        cache_key = CacheKey.user(current_user.id) + f":profit_curve:{bot_part}:{period}"

        # 尝试从缓存获取
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            logger.debug(f"收益曲线缓存命中: {cache_key}")
            return cached_data

        # 缓存未命中，查询数据库
        analytics = AnalyticsEngine(db)
        profit_curve = analytics.get_profit_curve(
            user_id=current_user.id,
            bot_id=bot_id,
            period=period
        )

        # 存入缓存
        await cache_manager.set(cache_key, profit_curve, CACHE_TTL_PROFIT_CURVE)
        logger.debug(f"收益曲线已缓存: {cache_key}")

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
        # 生成缓存键
        bot_part = f"bot:{bot_id}" if bot_id else "all"
        cache_key = CacheKey.trade_stats(current_user.id, bot_id if bot_id else 0)

        # 尝试从缓存获取
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            logger.debug(f"交易统计缓存命中: {cache_key}")
            return cached_data

        # 缓存未命中，查询数据库
        analytics = AnalyticsEngine(db)
        stats = analytics.get_trade_statistics(
            user_id=current_user.id,
            bot_id=bot_id
        )

        # 存入缓存
        await cache_manager.set(cache_key, stats, CACHE_TTL_TRADE_STATS)
        logger.debug(f"交易统计已缓存: {cache_key}")

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
        # 生成缓存键
        cache_key = CacheKey.bot_performance(bot_id)

        # 尝试从缓存获取
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            logger.debug(f"机器人性能缓存命中: {cache_key}")
            return cached_data

        # 缓存未命中，查询数据库
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

        # 存入缓存
        await cache_manager.set(cache_key, performance, CACHE_TTL_BOT_PERFORMANCE)
        logger.debug(f"机器人性能已缓存: {cache_key}")

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
        # 生成缓存键
        bot_part = f"bot:{bot_id}" if bot_id else "all"
        cache_key = CacheKey.user(current_user.id) + f":hourly_trades:{bot_part}:{days}days"

        # 尝试从缓存获取
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            logger.debug(f"每小时交易统计缓存命中: {cache_key}")
            return cached_data

        # 缓存未命中，查询数据库
        analytics = AnalyticsEngine(db)
        hourly_trades = analytics.get_hourly_trades(
            user_id=current_user.id,
            bot_id=bot_id,
            days=days
        )

        # 存入缓存
        await cache_manager.set(cache_key, hourly_trades, CACHE_TTL_HOURLY_TRADES)
        logger.debug(f"每小时交易统计已缓存: {cache_key}")

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

# ==================== 新增：时间分析API ====================

@router.get("/time-analysis")
async def get_time_analysis(
    analysis_type: str = Query("daily", description="分析类型: daily, weekly, monthly"),
    bot_id: Optional[int] = Query(None, description="机器人ID，不指定则查询全部"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取基于时间的交易分析（每日/每周/每月）

    参数:
    - analysis_type: 分析类型 (daily=每日, weekly=每周, monthly=每月)
    - bot_id: 机器人ID（可选）

    返回:
    - analysis_type: 分析类型
    - period: 统计周期
    - daily_stats/weekly_stats/monthly_stats: 时间序列统计数据
    - summary: 汇总信息
      - total_days/weeks/months: 总天数/周数/月数
      - winning_days/weeks/months: 盈利天数/周数/月数
      - losing_days/weeks/months: 亏损天数/周数/月数
      - total_pnl: 总盈亏
      - avg_daily/weekly/monthly_pnl: 平均盈亏
      - best_day/week/month: 最佳日期/周/月
      - worst_day/week/month: 最差日期/周/月
    """
    try:
        # 生成缓存键
        cache_key = f"{CacheKey.user(current_user.id)}:time_analysis:{analysis_type}:{bot_id or 0}"

        # 尝试从缓存获取
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            logger.debug(f"时间分析缓存命中: {cache_key}")
            return cached_data

        # 验证分析类型
        if analysis_type not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的analysis_type: {analysis_type}，可选值: daily, weekly, monthly"
            )

        # 缓存未命中，查询数据库
        analytics = AnalyticsEngine(db)
        analysis = analytics.get_time_based_analysis(
            user_id=current_user.id,
            bot_id=bot_id,
            analysis_type=analysis_type
        )

        # 存入缓存（不同的分析类型使用不同的TTL）
        ttl = CACHE_TTL_TRADE_STATS if analysis_type == "daily" else CACHE_TTL_PROFIT_CURVE
        await cache_manager.set(cache_key, analysis, ttl)
        logger.debug(f"时间分析已缓存: {cache_key}")

        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取时间分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取时间分析失败: {str(e)}"
        )


# ==================== 新增：交易对分析API ====================

@router.get("/pair-analysis")
async def get_pair_analysis(
    bot_id: Optional[int] = Query(None, description="机器人ID，不指定则查询全部"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取交易对分析

    返回:
    - analysis_type: 分析类型 (trading_pair)
    - pair_stats: 各交易对统计数据列表
      - trading_pair: 交易对
      - trade_count: 交易次数
      - winning_trades: 盈利交易数
      - losing_trades: 亏损交易数
      - total_profit: 总盈利
      - win_rate: 胜率
      - avg_profit: 平均盈利
      - max_profit: 最大盈利
      - min_profit: 最大亏损
      - profit_factor: 盈利因子
    - summary: 汇总信息
      - total_pairs: 总交易对数
      - total_pnl: 总盈亏
      - best_pair: 最佳交易对
      - worst_pair: 最差交易对
      - most_traded_pair: 交易次数最多的交易对
    """
    try:
        # 生成缓存键
        cache_key = f"{CacheKey.user(current_user.id)}:pair_analysis:{bot_id or 0}"

        # 尝试从缓存获取
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            logger.debug(f"交易对分析缓存命中: {cache_key}")
            return cached_data

        # 缓存未命中，查询数据库
        analytics = AnalyticsEngine(db)
        analysis = analytics.get_pair_analysis(
            user_id=current_user.id,
            bot_id=bot_id
        )

        # 存入缓存
        await cache_manager.set(cache_key, analysis, CACHE_TTL_TRADE_STATS)
        logger.debug(f"交易对分析已缓存: {cache_key}")

        return analysis
    except Exception as e:
        logger.error(f"获取交易对分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取交易对分析失败: {str(e)}"
        )

# ==================== 新增：报表导出API ====================

from fastapi.responses import FileResponse
from app.report_export import ReportExporter


@router.get("/export/trades")
async def export_trades(
    format: str = Query("csv", description="导出格式: csv, excel"),
    bot_id: Optional[int] = Query(None, description="机器人ID，不指定则导出全部"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出交易记录

    支持格式: CSV, Excel

    返回: 文件下载
    """
    try:
        # 验证格式
        if format not in ['csv', 'excel']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的格式: {format}，可选值: csv, excel"
            )

        # 查询交易记录
        query = db.query(Trade).join(TradingBot).filter(
            TradingBot.user_id == current_user.id
        )

        if bot_id:
            query = query.filter(Trade.bot_id == bot_id)

        trades = query.order_by(desc(Trade.created_at)).all()

        # 转换为字典列表
        trades_data = [
            {
                'id': trade.id,
                'bot_id': trade.bot_id,
                'trading_pair': trade.trading_pair,
                'side': trade.side,
                'price': trade.price,
                'amount': trade.amount,
                'fee': trade.fee,
                'profit': trade.profit,
                'created_at': trade.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for trade in trades
        ]

        # 导出
        exporter = ReportExporter()

        if format == 'csv':
            output_file = exporter.export_trades_to_csv(trades_data)
        else:
            output_file = exporter.export_trades_to_excel(trades_data)

        return FileResponse(
            output_file,
            media_type='application/octet-stream',
            filename=output_file
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出交易记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出交易记录失败: {str(e)}"
        )


@router.get("/export/analytics")
async def export_analytics_report(
    format: str = Query("excel", description="导出格式: excel（仅支持Excel）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出分析报表（多Sheet）

    包含:
    - 仪表盘概览
    - 最近交易
    - 收益曲线

    返回: Excel文件下载
    """
    try:
        # 验证格式
        if format != 'excel':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分析报表仅支持Excel格式"
            )

        # 获取分析数据
        analytics = AnalyticsEngine(db)

        analytics_data = {
            'dashboard': analytics.get_dashboard_summary(current_user.id),
            'recent_trades': [],
            'profit_curve': analytics.get_profit_curve(
                user_id=current_user.id,
                bot_id=None,
                period="30d"
            )
        }

        # 获取最近交易
        recent_trades = db.query(Trade).join(TradingBot).filter(
            TradingBot.user_id == current_user.id
        ).order_by(desc(Trade.created_at)).limit(50).all()

        analytics_data['recent_trades'] = [
            {
                'id': trade.id,
                'bot_id': trade.bot_id,
                'trading_pair': trade.trading_pair,
                'side': trade.side,
                'price': trade.price,
                'amount': trade.amount,
                'fee': trade.fee,
                'profit': trade.profit,
                'created_at': trade.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for trade in recent_trades
        ]

        # 导出
        exporter = ReportExporter()
        output_file = exporter.export_analytics_to_excel(analytics_data)

        return FileResponse(
            output_file,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=output_file
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出分析报表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出分析报表失败: {str(e)}"
        )


@router.get("/export/time-analysis")
async def export_time_analysis(
    analysis_type: str = Query("daily", description="分析类型: daily, weekly, monthly"),
    bot_id: Optional[int] = Query(None, description="机器人ID，不指定则导出全部"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出时间分析报表

    支持格式: Excel（仅支持Excel）

    参数:
    - analysis_type: 分析类型 (daily, weekly, monthly)
    - bot_id: 机器人ID（可选）

    返回: Excel文件下载
    """
    try:
        # 验证分析类型
        if analysis_type not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的analysis_type: {analysis_type}，可选值: daily, weekly, monthly"
            )

        # 获取时间分析数据
        analytics = AnalyticsEngine(db)
        analysis_data = analytics.get_time_based_analysis(
            user_id=current_user.id,
            bot_id=bot_id,
            analysis_type=analysis_type
        )

        # 导出
        exporter = ReportExporter()
        output_file = exporter.export_time_analysis_to_excel(analysis_data)

        return FileResponse(
            output_file,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=output_file
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出时间分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出时间分析失败: {str(e)}"
        )


@router.get("/export/pair-analysis")
async def export_pair_analysis(
    bot_id: Optional[int] = Query(None, description="机器人ID，不指定则导出全部"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出交易对分析报表

    支持格式: Excel（仅支持Excel）

    参数:
    - bot_id: 机器人ID（可选）

    返回: Excel文件下载
    """
    try:
        # 获取交易对分析数据
        analytics = AnalyticsEngine(db)
        analysis_data = analytics.get_pair_analysis(
            user_id=current_user.id,
            bot_id=bot_id
        )

        # 导出
        exporter = ReportExporter()
        output_file = exporter.export_pair_analysis_to_excel(analysis_data)

        return FileResponse(
            output_file,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=output_file
        )

    except Exception as e:
        logger.error(f"导出交易对分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出交易对分析失败: {str(e)}"
        )
