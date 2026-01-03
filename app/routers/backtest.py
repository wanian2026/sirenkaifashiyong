"""
回测API路由
只支持代码A策略回测
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import pandas as pd
import io
import json

from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.backtest import (
    BacktestEngine,
    BacktestConfig,
    generate_sample_data
)
from app.code_a_strategy import CodeABacktestStrategy

router = APIRouter()


@router.post("/run")
async def run_backtest(
    strategy_type: str = Query("code_a", regex="^code_a$"),
    initial_capital: float = Query(10000, ge=100),
    start_date: datetime = Query(default_factory=lambda: datetime.now() - timedelta(days=30)),
    end_date: datetime = Query(default_factory=lambda: datetime.now()),
    strategy_params: Optional[Dict] = None,
    use_sample_data: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    运行策略回测（只支持代码A策略）

    Args:
        strategy_type: 策略类型（仅支持code_a）
        initial_capital: 初始资金
        start_date: 回测开始日期
        end_date: 回测结束日期
        strategy_params: 策略参数
        use_sample_data: 是否使用模拟数据（默认True）
    """
    strategy_params = strategy_params or {}

    # 只支持code_a策略
    if strategy_type != 'code_a':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"只支持代码A策略"
        )

    # 获取或生成历史数据
    if use_sample_data:
        data = generate_sample_data(
            start_date=start_date,
            end_date=end_date,
            initial_price=50000,
            volatility=strategy_params.get('volatility', 0.02)
        )
    else:
        # TODO: 从数据库或交易所API获取真实历史数据
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="真实历史数据获取功能尚未实现，请使用模拟数据（use_sample_data=true）"
        )

    # 创建回测配置
    config = BacktestConfig(
        initial_capital=initial_capital,
        commission_rate=strategy_params.get('commission_rate', 0.001),
        slippage_rate=strategy_params.get('slippage_rate', 0.0005),
        start_date=start_date,
        end_date=end_date
    )

    # 创建回测引擎
    engine = BacktestEngine(config)

    # 执行代码A策略回测
    strategy = CodeABacktestStrategy.execute

    # 运行回测
    try:
        result = engine.run_backtest(
            data=data,
            strategy=strategy,
            strategy_params=strategy_params
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回测执行失败: {str(e)}"
        )

    # 格式化结果
    trades_data = []
    for trade in result.trades:
        trades_data.append({
            'timestamp': trade.timestamp.isoformat(),
            'symbol': trade.symbol,
            'action': trade.action,
            'price': trade.price,
            'amount': trade.amount,
            'value': trade.value,
            'commission': trade.commission,
            'balance': trade.balance,
            'position': trade.position
        })

    equity_curve_data = [
        {
            'timestamp': ts.isoformat(),
            'equity': eq
        }
        for ts, eq in zip(result.timestamps, result.equity_curve)
    ]

    return {
        'success': True,
        'config': {
            'strategy_type': strategy_type,
            'strategy_params': strategy_params,
            'initial_capital': initial_capital,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'commission_rate': config.commission_rate,
            'slippage_rate': config.slippage_rate
        },
        'performance': {
            'total_return': round(result.total_return * 100, 2),
            'annual_return': round(result.annual_return * 100, 2),
            'max_drawdown': round(result.max_drawdown * 100, 2),
            'sharpe_ratio': round(result.sharpe_ratio, 2),
            'sortino_ratio': round(result.sortino_ratio, 2),
            'win_rate': round(result.win_rate * 100, 2),
            'profit_factor': round(result.profit_factor, 2),
            'avg_profit': round(result.avg_profit, 2),
            'avg_loss': round(result.avg_loss, 2),
            'max_profit': round(result.max_profit, 2),
            'max_loss': round(result.max_loss, 2),
            'volatility': round(result.volatility * 100, 2),
            'var_95': round(result.var_95 * 100, 2),
            'cvar_95': round(result.cvar_95 * 100, 2)
        },
        'trades': {
            'total': result.total_trades,
            'profitable': result.profitable_trades,
            'losing': result.losing_trades,
            'data': trades_data
        },
        'equity_curve': equity_curve_data
    }


@router.get("/sample-data")
async def get_sample_data(
    days: int = Query(30, ge=1, le=365),
    initial_price: float = Query(50000, gt=0),
    volatility: float = Query(0.02, ge=0.001, le=0.5)
):
    """
    获取模拟价格数据

    Args:
        days: 数据天数
        initial_price: 初始价格
        volatility: 波动率

    Returns:
        模拟价格数据
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    data = generate_sample_data(
        start_date=start_date,
        end_date=end_date,
        initial_price=initial_price,
        volatility=volatility
    )

    return {
        'success': True,
        'data': data.to_dict('records'),
        'count': len(data)
    }
