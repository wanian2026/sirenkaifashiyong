"""
回测API路由
提供策略回测功能
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
    GridBacktestStrategy,
    MartingaleBacktestStrategy,
    generate_sample_data
)

router = APIRouter()


@router.post("/run")
async def run_backtest(
    strategy_type: str = Query(..., regex="^(grid|martingale|mean_reversion)$"),
    initial_capital: float = Query(10000, ge=100),
    start_date: datetime = Query(default_factory=lambda: datetime.now() - timedelta(days=30)),
    end_date: datetime = Query(default_factory=lambda: datetime.now()),
    strategy_params: Optional[Dict] = None,
    use_sample_data: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    运行策略回测

    Args:
        strategy_type: 策略类型（grid, martingale, mean_reversion）
        initial_capital: 初始资金
        start_date: 回测开始日期
        end_date: 回测结束日期
        strategy_params: 策略参数
        use_sample_data: 是否使用模拟数据
    """
    strategy_params = strategy_params or {}

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

    # 根据策略类型选择策略函数
    if strategy_type == 'grid':
        strategy = GridBacktestStrategy.execute
        strategy_params.setdefault('grid_levels', 10)
        strategy_params.setdefault('grid_spacing', 0.02)
    elif strategy_type == 'martingale':
        strategy = MartingaleBacktestStrategy.execute
        strategy_params.setdefault('initial_amount', 100)
        strategy_params.setdefault('multiplier', 1.5)
        strategy_params.setdefault('take_profit_percent', 0.05)
        strategy_params.setdefault('stop_loss_percent', 0.10)
    elif strategy_type == 'mean_reversion':
        # TODO: 实现均值回归策略
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="均值回归策略尚未实现"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的策略类型: {strategy_type}"
        )

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
            'sharpe_ratio': round(result.sharpe_ratio, 4),
            'sortino_ratio': round(result.sortino_ratio, 4),
            'win_rate': round(result.win_rate, 2),
            'profit_factor': round(result.profit_factor, 2),
            'avg_profit': round(result.avg_profit, 2),
            'avg_loss': round(result.avg_loss, 2),
            'max_profit': round(result.max_profit, 2),
            'max_loss': round(result.max_loss, 2),
            'volatility': round(result.volatility * 100, 2),
            'var_95': round(result.var_95 * 100, 2),
            'cvar_95': round(result.cvar_95 * 100, 2)
        },
        'statistics': {
            'total_trades': result.total_trades,
            'profitable_trades': result.profitable_trades,
            'losing_trades': result.losing_trades,
            'final_equity': round(result.equity_curve[-1], 2) if result.equity_curve else initial_capital
        },
        'trades': trades_data,
        'equity_curve': equity_curve_data
    }


@router.post("/batch")
async def run_batch_backtest(
    strategy_type: str = Query(..., regex="^(grid|martingale)$"),
    initial_capital: float = Query(10000, ge=100),
    start_date: datetime = Query(default_factory=lambda: datetime.now() - timedelta(days=30)),
    end_date: datetime = Query(default_factory=lambda: datetime.now()),
    param_variations: Dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量回测（参数优化）

    Args:
        strategy_type: 策略类型
        initial_capital: 初始资金
        start_date: 回测开始日期
        end_date: 回测结束日期
        param_variations: 参数变化范围，例如:
            {
                "grid_levels": [5, 10, 15, 20],
                "grid_spacing": [0.01, 0.02, 0.03]
            }
    """
    if not param_variations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供参数变化范围"
        )

    # 生成所有参数组合
    from itertools import product

    keys = list(param_variations.keys())
    values = list(param_variations.values())
    combinations = list(product(*values))

    results = []

    for combo in combinations:
        params = dict(zip(keys, combo))
        params['use_sample_data'] = True

        try:
            result = await run_backtest(
                strategy_type=strategy_type,
                initial_capital=initial_capital,
                start_date=start_date,
                end_date=end_date,
                strategy_params=params,
                use_sample_data=True,
                current_user=current_user,
                db=db
            )

            results.append({
                'params': params,
                'performance': result['performance'],
                'statistics': result['statistics']
            })

        except Exception as e:
            results.append({
                'params': params,
                'error': str(e)
            })

    # 找出最佳结果（根据夏普比率）
    valid_results = [r for r in results if 'performance' in r]
    if valid_results:
        best_result = max(valid_results, key=lambda x: x['performance']['sharpe_ratio'])
    else:
        best_result = None

    return {
        'total_combinations': len(combinations),
        'successful_runs': len(valid_results),
        'best_result': best_result,
        'all_results': results
    }


@router.get("/strategies")
async def list_strategies():
    """列出所有可用的回测策略"""
    return {
        'strategies': [
            {
                'id': 'grid',
                'name': '网格策略',
                'description': '在价格区间内设置多个买卖订单，自动低买高卖',
                'params': {
                    'grid_levels': '网格层数 (int)',
                    'grid_spacing': '网格间距 (float, 0.01-0.05)',
                    'commission_rate': '手续费率 (float, 默认0.001)',
                    'slippage_rate': '滑点率 (float, 默认0.0005)'
                }
            },
            {
                'id': 'martingale',
                'name': '马丁策略',
                'description': '每次亏损后加倍下注，直到盈利为止',
                'params': {
                    'initial_amount': '初始下单金额 (float, 默认100)',
                    'multiplier': '加倍倍数 (float, 默认1.5)',
                    'take_profit_percent': '止盈比例 (float, 默认0.05)',
                    'stop_loss_percent': '止损比例 (float, 默认0.10)',
                    'commission_rate': '手续费率 (float, 默认0.001)',
                    'slippage_rate': '滑点率 (float, 默认0.0005)'
                }
            },
            {
                'id': 'mean_reversion',
                'name': '均值回归策略',
                'description': '价格偏离均值时反向交易，等待回归',
                'status': 'coming_soon',
                'params': {}
            }
        ]
    }


@router.post("/export")
async def export_backtest_results(
    backtest_data: Dict,
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(get_current_user)
):
    """导出回测结果"""
    if format == "json":
        return backtest_data

    elif format == "csv":
        # 导出交易记录为CSV
        trades = backtest_data.get('trades', [])
        if not trades:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有交易记录可导出"
            )

        # 创建CSV
        output = io.StringIO()
        import csv
        writer = csv.writer(output)

        # 写入标题
        writer.writerow([
            'Timestamp', 'Symbol', 'Action', 'Price', 'Amount',
            'Value', 'Commission', 'Balance', 'Position'
        ])

        # 写入数据
        for trade in trades:
            writer.writerow([
                trade['timestamp'],
                trade['symbol'],
                trade['action'],
                trade['price'],
                trade['amount'],
                trade['value'],
                trade['commission'],
                trade['balance'],
                trade['position']
            ])

        output.seek(0)

        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=backtest_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的导出格式"
        )


@router.get("/compare")
async def compare_backtests(
    backtest_ids: List[int] = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """对比多个回测结果"""
    # TODO: 从数据库获取保存的回测结果进行对比
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="回测结果保存和对比功能尚未实现"
    )
