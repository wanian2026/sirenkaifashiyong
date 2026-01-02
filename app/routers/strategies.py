"""
高级策略管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Optional
import logging

from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.advanced_strategies import (
    MeanReversionStrategy,
    MomentumStrategy,
    StrategyFactory
)

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
                "type": "hedge_grid",
                "name": "对冲网格",
                "description": "基于网格的做市策略，在价格波动中获利",
                "params": {
                    "grid_levels": "网格层数",
                    "grid_spacing": "网格间距",
                    "investment_amount": "投资金额"
                }
            },
            {
                "type": "mean_reversion",
                "name": "均值回归",
                "description": "基于价格回归均值的策略，当价格偏离均值时进行反向交易",
                "params": {
                    "lookback_period": "回望周期（天数）",
                    "std_multiplier": "标准差倍数",
                    "investment_amount": "投资金额",
                    "position_limit": "持仓限制"
                }
            },
            {
                "type": "momentum",
                "name": "动量策略",
                "description": "基于价格动量的趋势跟踪策略，跟踪价格趋势进行交易",
                "params": {
                    "short_period": "短期均线周期",
                    "long_period": "长期均线周期",
                    "momentum_threshold": "动量阈值",
                    "investment_amount": "投资金额",
                    "stop_loss_percent": "止损百分比",
                    "take_profit_percent": "止盈百分比"
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
        # 创建策略实例
        strategy = StrategyFactory.create_strategy(strategy_type, config)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的策略类型: {strategy_type}"
            )

        # 模拟回测
        trades = []
        for price in price_data:
            await strategy.update_price(price)
            signal = await strategy.generate_signal(price)

            if signal:
                await strategy.execute_trade(signal)
                trades.append({
                    'price': price,
                    'signal': signal
                })

        # 获取最终状态
        final_status = strategy.get_strategy_status()

        return {
            "strategy_type": strategy_type,
            "config": config,
            "data_points": len(price_data),
            "total_trades": len(trades),
            "final_pnl": final_status['total_pnl'],
            "realized_pnl": final_status['realized_pnl'],
            "final_position": final_status['current_position'],
            "final_position_value": final_status['position_value'],
            "trades": trades[-10:],  # 只返回最后10笔交易
            "status": final_status
        }

    except Exception as e:
        logger.error(f"策略回测失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"策略回测失败: {str(e)}"
        )


@router.post("/{strategy_type}/initialize")
async def initialize_strategy(
    strategy_type: str,
    bot_id: int,
    config: Dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    初始化策略

    Args:
        strategy_type: 策略类型
        bot_id: 机器人ID
        config: 策略配置

    Returns:
        初始化结果
    """
    try:
        # 创建策略实例
        strategy = StrategyFactory.create_strategy(strategy_type, config)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的策略类型: {strategy_type}"
            )

        # 存储策略实例
        running_strategies[bot_id] = {
            'strategy': strategy,
            'type': strategy_type,
            'user_id': current_user.id
        }

        logger.info(f"策略初始化成功: {strategy_type}, bot_id: {bot_id}")

        return {
            "message": "策略初始化成功",
            "strategy_type": strategy_type,
            "bot_id": bot_id,
            "config": config
        }

    except Exception as e:
        logger.error(f"策略初始化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"策略初始化失败: {str(e)}"
        )


@router.post("/{bot_id}/update")
async def update_strategy(
    bot_id: int,
    price: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新策略状态

    Args:
        bot_id: 机器人ID
        price: 当前价格

    Returns:
        更新结果
    """
    try:
        # 获取策略实例
        if bot_id not in running_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在，请先初始化"
            )

        strategy_data = running_strategies[bot_id]
        strategy = strategy_data['strategy']

        # 验证权限
        if strategy_data['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此策略"
            )

        # 更新价格
        await strategy.update_price(price)

        # 生成信号
        signal = await strategy.generate_signal(price)

        # 如果有信号，执行交易
        trade_executed = False
        if signal:
            await strategy.execute_trade(signal)
            trade_executed = True

        # 获取状态
        status = strategy.get_strategy_status()

        return {
            "bot_id": bot_id,
            "price": price,
            "signal": signal if signal else None,
            "trade_executed": trade_executed,
            "status": status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"策略更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"策略更新失败: {str(e)}"
        )


@router.get("/{bot_id}/status")
async def get_strategy_status(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取策略状态

    Args:
        bot_id: 机器人ID

    Returns:
        策略状态
    """
    try:
        # 获取策略实例
        if bot_id not in running_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )

        strategy_data = running_strategies[bot_id]

        # 验证权限
        if strategy_data['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此策略"
            )

        # 获取状态
        strategy = strategy_data['strategy']
        status = strategy.get_strategy_status()

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略状态失败: {str(e)}"
        )


@router.post("/{bot_id}/stop")
async def stop_strategy(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    停止策略

    Args:
        bot_id: 机器人ID

    Returns:
        停止结果
    """
    try:
        # 获取策略实例
        if bot_id not in running_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )

        strategy_data = running_strategies[bot_id]

        # 验证权限
        if strategy_data['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此策略"
            )

        # 获取最终状态
        strategy = strategy_data['strategy']
        final_status = strategy.get_strategy_status()

        # 停止策略
        running_strategies.pop(bot_id)

        logger.info(f"策略已停止: bot_id: {bot_id}, 最终盈亏: {final_status['total_pnl']:.2f}")

        return {
            "message": "策略已停止",
            "bot_id": bot_id,
            "final_status": final_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止策略失败: {str(e)}"
        )


@router.get("/{bot_id}/trades")
async def get_strategy_trades(
    bot_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取策略交易历史

    Args:
        bot_id: 机器人ID
        limit: 返回数量限制

    Returns:
        交易历史
    """
    try:
        # 获取策略实例
        if bot_id not in running_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )

        strategy_data = running_strategies[bot_id]

        # 验证权限
        if strategy_data['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此策略"
            )

        # 获取交易历史
        strategy = strategy_data['strategy']
        trades = strategy.trades[-limit:] if len(strategy.trades) > limit else strategy.trades

        return {
            "bot_id": bot_id,
            "total_trades": len(strategy.trades),
            "trades": trades
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略交易历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略交易历史失败: {str(e)}"
        )
