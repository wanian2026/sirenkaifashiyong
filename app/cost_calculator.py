"""
交易成本计算模块

计算策略运行过程中的各项成本，包括：
1. 交易手续费
2. 滑点成本
3. 资金占用成本
4. 资金使用效率
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@dataclass
class CostConfig:
    """成本配置"""
    # 手续费配置
    commission_rate: float = 0.001  # 手续费率（0.1%）
    commission_taker: float = 0.001  # Taker手续费率
    commission_maker: float = 0.0008  # Maker手续费率

    # 滑点配置
    slippage_rate: float = 0.0005  # 滑点率（0.05%）
    volatility_slippage: bool = True  # 是否考虑波动率对滑点的影响

    # 资金占用成本配置
    enable_funding_cost: bool = False  # 是否计算资金占用成本
    funding_rate: float = 0.0001  # 资金费率（每天）
    margin_cost_rate: float = 0.00005  # 杠杆资金成本

    # 其他成本
    network_fee: float = 0.0  # 提现手续费（固定）
    withdrawal_fee: float = 0.0  # 转账手续费


@dataclass
class TradeCost:
    """单笔交易成本明细"""
    trade_id: str
    timestamp: datetime
    symbol: str
    side: str  # 'long' or 'short'
    action: str  # 'open', 'close', 'add', 'reduce'

    # 价格和数量
    entry_price: float
    exit_price: Optional[float]
    amount: float
    trade_value: float

    # 成本明细
    commission: float = 0.0
    slippage: float = 0.0
    funding_cost: float = 0.0
    other_cost: float = 0.0

    # 统计
    total_cost: float = 0.0
    cost_rate: float = 0.0  # 成本率（成本/交易金额）

    # 盈亏（扣除成本后）
    gross_profit: float = 0.0
    net_profit: float = 0.0


class CostCalculator:
    """成本计算器"""

    def __init__(self, config: CostConfig = None):
        self.config = config or CostConfig()
        self.trade_costs: List[TradeCost] = []
        self.total_commission = 0.0
        self.total_slippage = 0.0
        self.total_funding = 0.0
        self.total_other = 0.0
        self.total_cost = 0.0
        self.total_trade_value = 0.0

    def reset(self):
        """重置成本统计"""
        self.trade_costs = []
        self.total_commission = 0.0
        self.total_slippage = 0.0
        self.total_funding = 0.0
        self.total_other = 0.0
        self.total_cost = 0.0
        self.total_trade_value = 0.0

    def calculate_open_cost(
        self,
        trade_id: str,
        timestamp: datetime,
        symbol: str,
        side: str,
        price: float,
        amount: float
    ) -> TradeCost:
        """
        计算开仓成本

        Args:
            trade_id: 交易ID
            timestamp: 时间戳
            symbol: 交易对
            side: 方向（'long' or 'short'）
            price: 价格
            amount: 数量

        Returns:
            交易成本明细
        """
        trade_value = price * amount

        # 1. 手续费（假设Taker订单）
        commission = trade_value * self.config.commission_taker

        # 2. 滑点（开仓滑点通常较小）
        slippage = trade_value * self.config.slippage_rate

        # 3. 资金费（如果有杠杆）
        funding_cost = 0.0
        if self.config.enable_funding_cost:
            # 开仓时通常不计资金费，持仓期间计算
            pass

        # 4. 其他成本
        other_cost = 0.0

        # 总成本
        total_cost = commission + slippage + funding_cost + other_cost
        cost_rate = total_cost / trade_value if trade_value > 0 else 0

        trade_cost = TradeCost(
            trade_id=trade_id,
            timestamp=timestamp,
            symbol=symbol,
            side=side,
            action='open',
            entry_price=price,
            exit_price=None,
            amount=amount,
            trade_value=trade_value,
            commission=commission,
            slippage=slippage,
            funding_cost=funding_cost,
            other_cost=other_cost,
            total_cost=total_cost,
            cost_rate=cost_rate,
            gross_profit=0.0,
            net_profit=-total_cost
        )

        self.trade_costs.append(trade_cost)
        self.update_totals(trade_cost)

        return trade_cost

    def calculate_close_cost(
        self,
        trade_id: str,
        timestamp: datetime,
        symbol: str,
        side: str,
        entry_price: float,
        close_price: float,
        amount: float,
        holding_time: timedelta = None
    ) -> TradeCost:
        """
        计算平仓成本

        Args:
            trade_id: 交易ID
            timestamp: 时间戳
            symbol: 交易对
            side: 方向（'long' or 'short'）
            entry_price: 开仓价格
            close_price: 平仓价格
            amount: 数量
            holding_time: 持仓时长

        Returns:
            交易成本明细
        """
        trade_value = close_price * amount

        # 1. 手续费
        commission = trade_value * self.config.commission_taker

        # 2. 滑点（平仓时滑点通常更大）
        slippage = trade_value * self.config.slippage_rate * 1.2

        # 3. 资金费（持仓期间的资金成本）
        funding_cost = 0.0
        if self.config.enable_funding_cost and holding_time:
            # 计算持仓天数
            holding_days = holding_time.total_seconds() / 86400
            # 资金费 = 持仓天数 × 资金费率 × 持仓价值
            avg_value = (entry_price + close_price) / 2 * amount
            funding_cost = holding_days * self.config.funding_rate * avg_value

        # 4. 其他成本
        other_cost = 0.0

        # 计算毛利润
        if side == 'long':
            gross_profit = (close_price - entry_price) * amount
        else:  # short
            gross_profit = (entry_price - close_price) * amount

        # 总成本
        total_cost = commission + slippage + funding_cost + other_cost
        cost_rate = total_cost / trade_value if trade_value > 0 else 0

        # 净利润
        net_profit = gross_profit - total_cost

        trade_cost = TradeCost(
            trade_id=trade_id,
            timestamp=timestamp,
            symbol=symbol,
            side=side,
            action='close',
            entry_price=entry_price,
            exit_price=close_price,
            amount=amount,
            trade_value=trade_value,
            commission=commission,
            slippage=slippage,
            funding_cost=funding_cost,
            other_cost=other_cost,
            total_cost=total_cost,
            cost_rate=cost_rate,
            gross_profit=gross_profit,
            net_profit=net_profit
        )

        self.trade_costs.append(trade_cost)
        self.update_totals(trade_cost)

        return trade_cost

    def update_totals(self, trade_cost: TradeCost):
        """更新总计"""
        self.total_commission += trade_cost.commission
        self.total_slippage += trade_cost.slippage
        self.total_funding += trade_cost.funding_cost
        self.total_other += trade_cost.other_cost
        self.total_cost += trade_cost.total_cost
        self.total_trade_value += trade_cost.trade_value

    def get_cost_summary(self) -> Dict:
        """获取成本汇总"""
        if self.total_trade_value == 0:
            return {}

        return {
            'total_trades': len(self.trade_costs),
            'total_trade_value': self.total_trade_value,
            'total_commission': self.total_commission,
            'total_slippage': self.total_slippage,
            'total_funding': self.total_funding,
            'total_other': self.total_other,
            'total_cost': self.total_cost,
            'avg_cost_per_trade': self.total_cost / len(self.trade_costs) if self.trade_costs else 0,
            'cost_rate': self.total_cost / self.total_trade_value,
            'commission_rate': self.total_commission / self.total_trade_value,
            'slippage_rate': self.total_slippage / self.total_trade_value,
            'funding_rate': self.total_funding / self.total_trade_value,
            'cost_breakdown': {
                'commission': self.total_commission / self.total_cost * 100 if self.total_cost > 0 else 0,
                'slippage': self.total_slippage / self.total_cost * 100 if self.total_cost > 0 else 0,
                'funding': self.total_funding / self.total_cost * 100 if self.total_cost > 0 else 0,
                'other': self.total_other / self.total_cost * 100 if self.total_cost > 0 else 0
            }
        }

    def get_profit_after_cost(self, gross_profit: float) -> float:
        """获取扣除成本后的净利润"""
        return gross_profit - self.total_cost


def calculate_capital_efficiency(
    total_profit: float,
    initial_capital: float,
    trading_days: int,
    max_drawdown: float = 0.0
) -> Dict:
    """
    计算资金效率指标

    Args:
        total_profit: 总利润
        initial_capital: 初始资金
        trading_days: 交易天数
        max_drawdown: 最大回撤（绝对值）

    Returns:
        资金效率指标
    """
    if initial_capital <= 0:
        return {}

    return {
        'total_return': total_profit / initial_capital,
        'annual_return': (total_profit / initial_capital) * (365 / trading_days) if trading_days > 0 else 0,
        'daily_return': (total_profit / initial_capital) / trading_days if trading_days > 0 else 0,
        'max_drawdown': max_drawdown,
        'return_drawdown_ratio': (total_profit / initial_capital) / max_drawdown if max_drawdown > 0 else 0,
        'capital_efficiency': (total_profit / initial_capital) / (max_drawdown + 0.01)  # 加小数防止除零
    }


def estimate_break_even_trades(
    avg_profit_per_trade: float,
    avg_cost_per_trade: float
) -> Dict:
    """
    估算盈亏平衡点

    Args:
        avg_profit_per_trade: 平均每笔毛利润
        avg_cost_per_trade: 平均每笔成本

    Returns:
        盈亏平衡分析
    """
    if avg_cost_per_trade <= 0:
        return {'break_even_profit': 0, 'trades_to_break_even': 0}

    # 至少需要多少利润才能覆盖成本
    break_even_profit = avg_cost_per_trade

    # 如果平均利润小于成本，需要多少笔交易才能通过偶然大盈利达到盈亏平衡
    if avg_profit_per_trade < avg_cost_per_trade:
        # 假设每10笔中有1笔大盈利（3倍平均盈利）
        large_trade_profit = avg_profit_per_trade * 3
        loss_per_cycle = (avg_cost_per_trade - avg_profit_per_trade) * 9
        additional_trades_needed = math.ceil(loss_per_cycle / (large_trade_profit - avg_cost_per_trade))
        trades_to_break_even = additional_trades_needed * 10
    else:
        trades_to_break_even = 0  # 已经盈利

    return {
        'break_even_profit': break_even_profit,
        'trades_to_break_even': trades_to_break_even,
        'is_profitable': avg_profit_per_trade > avg_cost_per_trade
    }


import math  # 移到这里，避免循环导入
