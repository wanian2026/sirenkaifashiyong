"""
回测引擎模块
提供策略回测功能，支持多种交易策略的历史数据测试
"""

from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from decimal import Decimal


@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 10000.0  # 初始资金
    commission_rate: float = 0.001  # 手续费率（0.1%）
    slippage_rate: float = 0.0005  # 滑点率（0.05%）
    max_position: float = 10000.0  # 最大持仓
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class Trade:
    """交易记录"""
    timestamp: datetime
    symbol: str
    action: str  # 'buy' or 'sell'
    price: float
    amount: float
    value: float
    commission: float
    balance: float  # 交易后余额
    position: float  # 持仓数量


@dataclass
class BacktestResult:
    """回测结果"""
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)

    # 性能指标
    total_return: float = 0.0
    annual_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    max_profit: float = 0.0
    max_loss: float = 0.0
    total_trades: int = 0
    profitable_trades: int = 0
    losing_trades: int = 0

    # 风险指标
    volatility: float = 0.0
    var_95: float = 0.0  # 95%置信度的VaR
    cvar_95: float = 0.0  # 95%置信度的CVaR


class BacktestEngine:
    """回测引擎"""

    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.timestamps: List[datetime] = []
        self.balance = self.config.initial_capital
        self.position = 0.0
        self.entry_price = 0.0

    def reset(self):
        """重置回测状态"""
        self.trades = []
        self.equity_curve = []
        self.timestamps = []
        self.balance = self.config.initial_capital
        self.position = 0.0
        self.entry_price = 0.0

    def execute_order(
        self,
        timestamp: datetime,
        symbol: str,
        action: str,
        price: float,
        amount: float
    ):
        """
        执行订单

        Args:
            timestamp: 时间戳
            symbol: 交易对
            action: 'buy' or 'sell'
            price: 价格（考虑滑点）
            amount: 数量
        """
        # 应用滑点
        if action == 'buy':
            actual_price = price * (1 + self.config.slippage_rate)
        else:
            actual_price = price * (1 - self.config.slippage_rate)

        # 计算交易金额
        value = actual_price * amount

        # 计算手续费
        commission = value * self.config.commission_rate

        # 检查资金是否足够
        if action == 'buy':
            required = value + commission
            if required > self.balance:
                # 资金不足，调整数量
                amount = (self.balance - commission) / actual_price
                value = actual_price * amount
                commission = value * self.config.commission_rate

        # 执行交易
        if action == 'buy':
            self.balance -= (value + commission)
            self.position += amount
            if self.position == amount:  # 新建仓
                self.entry_price = actual_price
        else:  # sell
            self.balance += (value - commission)
            self.position -= amount
            if self.position == 0:  # 平仓
                self.entry_price = 0.0

        # 记录交易
        trade = Trade(
            timestamp=timestamp,
            symbol=symbol,
            action=action,
            price=actual_price,
            amount=amount,
            value=value,
            commission=commission,
            balance=self.balance,
            position=self.position
        )
        self.trades.append(trade)

    def get_current_equity(self, current_price: float) -> float:
        """获取当前权益"""
        return self.balance + self.position * current_price

    def calculate_performance_metrics(self) -> BacktestResult:
        """计算性能指标"""
        if not self.trades:
            return BacktestResult()

        result = BacktestResult(
            trades=self.trades,
            equity_curve=self.equity_curve,
            timestamps=self.timestamps
        )

        # 计算总收益率
        final_equity = self.equity_curve[-1] if self.equity_curve else self.config.initial_capital
        result.total_return = (final_equity - self.config.initial_capital) / self.config.initial_capital

        # 计算年化收益率
        if len(self.trades) > 1:
            duration_days = (self.trades[-1].timestamp - self.trades[0].timestamp).days
            if duration_days > 0:
                result.annual_return = (1 + result.total_return) ** (365 / duration_days) - 1

        # 计算最大回撤
        if self.equity_curve:
            peak = max(self.equity_curve)
            if peak > 0:
                result.max_drawdown = (peak - min(self.equity_curve)) / peak

        # 计算夏普比率
        if len(self.equity_curve) > 1:
            returns = pd.Series(self.equity_curve).pct_change().dropna()
            if returns.std() > 0:
                result.sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252))

        # 计算索提诺比率
        if len(self.equity_curve) > 1:
            returns = pd.Series(self.equity_curve).pct_change().dropna()
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0 and downside_returns.std() > 0:
                result.sortino_ratio = (returns.mean() * 252) / (downside_returns.std() * np.sqrt(252))

        # 计算交易统计
        profitable_trades = []
        losing_trades = []

        for i in range(0, len(self.trades) - 1, 2):
            if i + 1 < len(self.trades):
                buy_trade = self.trades[i]
                sell_trade = self.trades[i + 1]

                if buy_trade.action == 'buy' and sell_trade.action == 'sell':
                    profit = (sell_trade.price - buy_trade.price) * buy_trade.amount
                    profit -= (buy_trade.commission + sell_trade.commission)

                    if profit > 0:
                        profitable_trades.append(profit)
                    elif profit < 0:
                        losing_trades.append(abs(profit))

        result.total_trades = len(profitable_trades) + len(losing_trades)
        result.profitable_trades = len(profitable_trades)
        result.losing_trades = len(losing_trades)
        result.win_rate = (result.profitable_trades / result.total_trades * 100) if result.total_trades > 0 else 0

        if profitable_trades:
            result.avg_profit = np.mean(profitable_trades)
            result.max_profit = np.max(profitable_trades)

        if losing_trades:
            result.avg_loss = np.mean(losing_trades)
            result.max_loss = np.max(losing_trades)

        # 计算盈利因子
        gross_profit = sum(profitable_trades) if profitable_trades else 0
        gross_loss = sum(losing_trades) if losing_trades else 0
        result.profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # 计算波动率
        if len(self.equity_curve) > 1:
            returns = pd.Series(self.equity_curve).pct_change().dropna()
            result.volatility = returns.std() * np.sqrt(252)

        # 计算VaR和CVaR（95%置信度）
        if len(self.equity_curve) > 1:
            returns = pd.Series(self.equity_curve).pct_change().dropna()
            result.var_95 = np.percentile(returns, 5)
            result.cvar_95 = returns[returns <= result.var_95].mean()

        return result

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy: Callable,
        strategy_params: Dict = None
    ) -> BacktestResult:
        """
        运行回测

        Args:
            data: 历史数据 DataFrame，包含 columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            strategy: 策略函数，接收当前数据和当前状态，返回交易信号
            strategy_params: 策略参数

        Returns:
            回测结果
        """
        self.reset()

        strategy_params = strategy_params or {}

        for idx, row in data.iterrows():
            timestamp = row['timestamp']
            open_price = row['open']
            high_price = row['high']
            low_price = row['low']
            close_price = row['close']
            volume = row['volume']

            # 获取策略信号
            signals = strategy(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                balance=self.balance,
                position=self.position,
                entry_price=self.entry_price,
                **strategy_params
            )

            # 执行信号
            for signal in signals:
                action = signal.get('action')
                price = signal.get('price', close_price)
                amount = signal.get('amount', 0)

                if action == 'buy' and amount > 0:
                    self.execute_order(timestamp, 'BTC/USDT', 'buy', price, amount)
                elif action == 'sell' and amount > 0:
                    self.execute_order(timestamp, 'BTC/USDT', 'sell', price, amount)

            # 记录权益曲线
            current_equity = self.get_current_equity(close_price)
            self.equity_curve.append(current_equity)
            self.timestamps.append(timestamp)

        # 计算性能指标
        return self.calculate_performance_metrics()


class GridBacktestStrategy:
    """网格策略回测"""

    @staticmethod
    def execute(
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        balance: float,
        position: float,
        entry_price: float,
        grid_levels: int = 10,
        grid_spacing: float = 0.02,
        grid_orders: List[Dict] = None
    ) -> List[Dict]:
        """执行网格策略"""
        signals = []

        if grid_orders is None:
            grid_orders = []

        # 初始化网格订单（第一次调用）
        if not grid_orders:
            amount_per_level = balance / (grid_levels * 2)
            for i in range(-grid_levels // 2, grid_levels // 2 + 1):
                price = close * (1 + i * grid_spacing)
                if price > 0:
                    if i < 0:
                        grid_orders.append({
                            'price': price,
                            'amount': amount_per_level / price,
                            'type': 'buy',
                            'status': 'pending'
                        })
                    elif i > 0:
                        grid_orders.append({
                            'price': price,
                            'amount': amount_per_level / price,
                            'type': 'sell',
                            'status': 'pending'
                        })

        # 检查订单是否可以执行
        for order in grid_orders:
            if order['status'] != 'pending':
                continue

            if order['type'] == 'buy' and low <= order['price']:
                signals.append({
                    'action': 'buy',
                    'price': order['price'],
                    'amount': order['amount']
                })
                order['status'] = 'filled'

                # 创建对应的卖单
                sell_price = order['price'] * (1 + grid_spacing)
                grid_orders.append({
                    'price': sell_price,
                    'amount': order['amount'],
                    'type': 'sell',
                    'status': 'pending'
                })

            elif order['type'] == 'sell' and high >= order['price']:
                signals.append({
                    'action': 'sell',
                    'price': order['price'],
                    'amount': order['amount']
                })
                order['status'] = 'filled'

        return signals


class MartingaleBacktestStrategy:
    """马丁策略回测"""

    @staticmethod
    def execute(
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        balance: float,
        position: float,
        entry_price: float,
        initial_amount: float = 100,
        multiplier: float = 1.5,
        take_profit_percent: float = 0.05,
        stop_loss_percent: float = 0.10,
        consecutive_losses: int = 0,
        last_trade_loss: float = 0
    ) -> List[Dict]:
        """执行马丁策略"""
        signals = []

        # 计算当前盈亏
        if position > 0 and entry_price > 0:
            pnl_percent = (close - entry_price) / entry_price

            # 止盈
            if pnl_percent >= take_profit_percent:
                signals.append({
                    'action': 'sell',
                    'price': close,
                    'amount': position
                })
                consecutive_losses = 0
                last_trade_loss = 0

            # 止损
            elif pnl_percent <= -stop_loss_percent:
                signals.append({
                    'action': 'sell',
                    'price': close,
                    'amount': position
                })
                consecutive_losses += 1
                last_trade_loss = abs((close - entry_price) * position)

        # 无持仓时开仓
        elif position == 0:
            # 计算下一次开仓金额
            if consecutive_losses > 0:
                amount = initial_amount * (multiplier ** consecutive_losses)
            else:
                amount = initial_amount

            if amount <= balance:
                signals.append({
                    'action': 'buy',
                    'price': close,
                    'amount': amount / close
                })

        return signals


def generate_sample_data(
    start_date: datetime,
    end_date: datetime,
    initial_price: float = 50000,
    volatility: float = 0.02
) -> pd.DataFrame:
    """
    生成模拟历史数据

    Args:
        start_date: 开始日期
        end_date: 结束日期
        initial_price: 初始价格
        volatility: 波动率

    Returns:
        DataFrame 包含 ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    """
    np.random.seed(42)

    # 生成日期范围
    dates = pd.date_range(start=start_date, end=end_date, freq='H')
    n = len(dates)

    # 生成价格序列（几何布朗运动）
    dt = 1 / 365 / 24  # 1小时的时间步长
    mu = 0.05  # 年化收益率
    sigma = volatility  # 波动率

    returns = np.random.normal(
        (mu - 0.5 * sigma ** 2) * dt,
        sigma * np.sqrt(dt),
        n
    )
    prices = initial_price * np.exp(np.cumsum(returns))

    # 生成OHLC数据
    df = pd.DataFrame({
        'timestamp': dates,
        'close': prices
    })

    # 生成open, high, low
    df['open'] = df['close'].shift(1).fillna(initial_price)
    df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.01, n))
    df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.01, n))

    # 生成volume
    df['volume'] = np.random.uniform(10, 1000, n)

    # 调整顺序
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    return df
