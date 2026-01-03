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
    # 代号A策略使用自己的回测实现，不需要BacktestEngine

    # 执行代码A策略回测
    try:
        trades_df = CodeABacktestStrategy.execute(data, strategy_params)
        
        # 计算回测结果
        if len(trades_df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="策略未产生任何交易"
            )
        
        # 计算基本统计
        total_profit = 0
        total_loss = 0
        win_trades = 0
        lose_trades = 0
        
        for _, trade in trades_df.iterrows():
            profit = trade.get('profit', 0)
            if profit > 0:
                total_profit += profit
                win_trades += 1
            elif profit < 0:
                total_loss += abs(profit)
                lose_trades += 1
        
        total_trades = len(trades_df)
        win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 简化的性能指标
        total_return = (total_profit - total_loss) / initial_capital if initial_capital > 0 else 0
        
        # 格式化交易数据
        trades_data = []
        for _, trade in trades_df.iterrows():
            trades_data.append({
                'timestamp': trade.get('timestamp', ''),
                'action': trade.get('action', ''),
                'price': trade.get('price', 0),
                'amount': trade.get('amount', 0),
                'profit': trade.get('profit', 0)
            })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回测执行失败: {str(e)}"
        )

    return {
        'success': True,
        'config': {
            'strategy_type': strategy_type,
            'strategy_params': strategy_params,
            'initial_capital': initial_capital,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'performance': {
            'total_return': round(total_return * 100, 2),
            'total_profit': round(total_profit, 2),
            'total_loss': round(total_loss, 2),
            'net_profit': round(total_profit - total_loss, 2),
            'win_rate': round(win_rate, 2),
            'total_trades': total_trades,
            'win_trades': win_trades,
            'lose_trades': lose_trades
        },
        'trades': {
            'total': total_trades,
            'profitable': win_trades,
            'losing': lose_trades,
            'data': trades_data
        }
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
