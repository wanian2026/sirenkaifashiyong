"""
策略管理API路由
只保留代码A策略作为核心策略
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Optional
import logging

from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.code_a_strategy import CodeAStrategy, CodeABacktestStrategy

logger = logging.getLogger(__name__)

router = APIRouter()

# 存储运行中的策略实例
running_strategies: Dict[int, Dict] = {}  # {bot_id: {'strategy': strategy, 'type': type}}


@router.get("/types")
async def list_strategy_types():
    """
    列出可用的策略类型

    Returns:
        策略类型列表及说明
    """
    return {
        "strategies": [
            {
                "type": "code_a",
                "name": "代码A策略",
                "description": "基于技术分析的核心交易策略，结合趋势跟踪和均值回归",
                "params": {
                    "trend_period": "趋势判断周期（默认20）",
                    "reversion_period": "均值回归周期（默认10）",
                    "volatility_threshold": "波动率阈值（默认0.02）",
                    "position_size": "单笔持仓比例（默认0.1）",
                    "take_profit": "止盈百分比（默认0.05）",
                    "stop_loss": "止损百分比（默认0.03）",
                    "risk_limit": "单笔风险限制（默认0.02）",
                    "investment_amount": "投资金额"
                }
            }
        ]
    }


@router.post("/backtest")
async def backtest_strategy(
    strategy_type: str,
    config: Dict,
    price_data: list,
    current_user: User = Depends(get_current_user)
):
    """
    回测策略

    Args:
        strategy_type: 策略类型
        config: 策略配置
        price_data: 价格数据列表 [price1, price2, ...]

    Returns:
        回测结果
    """
    try:
        # 只支持code_a策略
        if strategy_type != 'code_a':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"只支持代码A策略"
            )

        # 创建策略实例
        strategy = CodeABacktestStrategy()

        # 准备数据
        import pandas as pd
        df = pd.DataFrame(price_data)

        # 执行回测
        result = strategy.execute(df, config)

        return {
            "success": True,
            "strategy_type": strategy_type,
            "config": config,
            "trades": result.to_dict('records'),
            "total_trades": len(result)
        }

    except Exception as e:
        logger.error(f"回测失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回测执行失败: {str(e)}"
        )


@router.post("/start")
async def start_strategy(
    bot_id: int,
    strategy_type: str,
    config: Dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    启动策略

    Args:
        bot_id: 机器人ID
        strategy_type: 策略类型
        config: 策略配置

    Returns:
        启动结果
    """
    try:
        # 只支持code_a策略
        if strategy_type != 'code_a':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"只支持代码A策略"
            )

        # 创建策略实例
        strategy = CodeAStrategy(
            trading_pair=config.get('trading_pair', 'BTC/USDT'),
            investment_amount=config.get('investment_amount', 10000),
            trend_period=config.get('trend_period', 20),
            reversion_period=config.get('reversion_period', 10),
            volatility_threshold=config.get('volatility_threshold', 0.02),
            position_size=config.get('position_size', 0.1),
            take_profit=config.get('take_profit', 0.05),
            stop_loss=config.get('stop_loss', 0.03),
            risk_limit=config.get('risk_limit', 0.02)
        )

        # 存储策略实例
        running_strategies[bot_id] = {
            'strategy': strategy,
            'type': strategy_type,
            'config': config
        }

        return {
            "success": True,
            "message": "代码A策略已启动",
            "bot_id": bot_id,
            "strategy_type": strategy_type
        }

    except Exception as e:
        logger.error(f"启动策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动策略失败: {str(e)}"
        )


@router.post("/stop")
async def stop_strategy(
    bot_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    停止策略

    Args:
        bot_id: 机器人ID

    Returns:
        停止结果
    """
    try:
        if bot_id in running_strategies:
            strategy_info = running_strategies[bot_id]
            strategy = strategy_info['strategy']
            status = strategy.get_status()

            del running_strategies[bot_id]

            return {
                "success": True,
                "message": "策略已停止",
                "bot_id": bot_id,
                "final_status": status
            }
        else:
            return {
                "success": False,
                "message": "策略未运行",
                "bot_id": bot_id
            }

    except Exception as e:
        logger.error(f"停止策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止策略失败: {str(e)}"
        )


@router.get("/status/{bot_id}")
async def get_strategy_status(
    bot_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    获取策略状态

    Args:
        bot_id: 机器人ID

    Returns:
        策略状态
    """
    try:
        if bot_id in running_strategies:
            strategy = running_strategies[bot_id]['strategy']
            status = strategy.get_status()
            return {
                "success": True,
                "status": status
            }
        else:
            return {
                "success": False,
                "message": "策略未运行"
            }

    except Exception as e:
        logger.error(f"获取策略状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略状态失败: {str(e)}"
        )


@router.post("/signal")
async def generate_signal(
    bot_id: int,
    current_price: float,
    current_user: User = Depends(get_current_user)
):
    """
    生成交易信号

    Args:
        bot_id: 机器人ID
        current_price: 当前价格

    Returns:
        交易信号
    """
    try:
        if bot_id in running_strategies:
            strategy = running_strategies[bot_id]['strategy']
            signal = strategy.generate_signal(current_price)
            return {
                "success": True,
                "signal": signal
            }
        else:
            return {
                "success": False,
                "message": "策略未运行"
            }

    except Exception as e:
        logger.error(f"生成信号失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成信号失败: {str(e)}"
        )
