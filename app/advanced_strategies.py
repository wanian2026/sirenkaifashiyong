"""
高级交易策略模块
提供均值回归、动量等高级交易策略
"""

import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, stdev
import logging

logger = logging.getLogger(__name__)


class MeanReversionStrategy:
    """均值回归策略

    基于价格回归均值的策略，当价格偏离均值时进行反向交易
    """

    def __init__(
        self,
        trading_pair: str = "BTC/USDT",
        lookback_period: int = 20,
        std_multiplier: float = 2.0,
        investment_amount: float = 1000,
        min_position_size: float = 0.001,
        max_position_size: float = 1.0,
        position_limit: float = 5000,
        rebalance_threshold: float = 0.5
    ):
        self.trading_pair = trading_pair
        self.lookback_period = lookback_period  # 回望周期
        self.std_multiplier = std_multiplier  # 标准差倍数
        self.investment_amount = investment_amount
        self.min_position_size = min_position_size
        self.max_position_size = max_position_size
        self.position_limit = position_limit
        self.rebalance_threshold = rebalance_threshold

        # 价格历史
        self.price_history: List[float] = []
        self.max_history = lookback_period * 2

        # 持仓信息
        self.current_position: float = 0
        self.entry_price: float = 0
        self.position_value: float = 0
        self.unrealized_pnl: float = 0
        self.realized_pnl: float = 0

        # 交易历史
        self.trades: List[Dict] = []

        # 状态
        self.is_running = False
        self.last_signal_time: Optional[datetime] = None
        self.current_mean: float = 0
        self.current_std: float = 0
        self.upper_band: float = 0
        self.lower_band: float = 0

    async def update_price(self, price: float) -> None:
        """
        更新价格数据

        Args:
            price: 当前价格
        """
        self.price_history.append(price)

        # 限制历史记录数量
        if len(self.price_history) > self.max_history:
            self.price_history = self.price_history[-self.max_history:]

        # 更新布林带
        if len(self.price_history) >= self.lookback_period:
            prices = self.price_history[-self.lookback_period:]
            self.current_mean = mean(prices)
            self.current_std = stdev(prices) if len(prices) > 1 else 0
            self.upper_band = self.current_mean + self.std_multiplier * self.current_std
            self.lower_band = self.current_mean - self.std_multiplier * self.current_std

        # 计算未实现盈亏
        if self.current_position != 0:
            price_change = (price - self.entry_price) * self.current_position
            self.unrealized_pnl = price_change
        else:
            self.unrealized_pnl = 0

    async def generate_signal(self, price: float) -> Optional[Dict]:
        """
        生成交易信号

        Args:
            price: 当前价格

        Returns:
            交易信号或None
        """
        if len(self.price_history) < self.lookback_period:
            return None

        # 检查是否在布林带范围内
        if price > self.upper_band:
            # 价格超出上轨，考虑做空（或减少多头）
            if self.current_position > 0:
                # 持有多头，平仓
                amount = min(self.current_position, self.max_position_size)
                return {
                    'action': 'sell',
                    'amount': amount,
                    'price': price,
                    'reason': f'价格{price:.2f}超出上轨{self.upper_band:.2f}，平仓',
                    'signal_strength': 'strong'
                }
            elif self.current_position == 0:
                # 无持仓，考虑做空（如果做空功能已启用）
                return {
                    'action': 'sell_short',
                    'amount': self._calculate_position_size(price),
                    'price': price,
                    'reason': f'价格{price:.2f}超出上轨{self.upper_band:.2f}，做空',
                    'signal_strength': 'medium'
                }

        elif price < self.lower_band:
            # 价格低于下轨，考虑做多（或减少空头）
            if self.current_position < 0:
                # 持有空头，平仓
                amount = min(abs(self.current_position), self.max_position_size)
                return {
                    'action': 'buy',
                    'amount': amount,
                    'price': price,
                    'reason': f'价格{price:.2f}低于下轨{self.lower_band:.2f}，平仓',
                    'signal_strength': 'strong'
                }
            elif self.current_position == 0:
                # 无持仓，考虑做多
                return {
                    'action': 'buy',
                    'amount': self._calculate_position_size(price),
                    'price': price,
                    'reason': f'价格{price:.2f}低于下轨{self.lower_band:.2f}，做多',
                    'signal_strength': 'medium'
                }

        elif abs(price - self.current_mean) < self.rebalance_threshold * self.current_std:
            # 价格回归均值，考虑平仓
            if self.current_position != 0:
                amount = abs(self.current_position)
                action = 'sell' if self.current_position > 0 else 'buy'
                return {
                    'action': action,
                    'amount': amount,
                    'price': price,
                    'reason': f'价格{price:.2f}回归均值{self.current_mean:.2f}，平仓',
                    'signal_strength': 'strong'
                }

        return None

    def _calculate_position_size(self, price: float) -> float:
        """计算仓位大小"""
        # 基于投资金额计算
        position_value = min(self.investment_amount, self.position_limit - abs(self.position_value))
        position_size = position_value / price

        # 限制仓位大小
        position_size = max(self.min_position_size, min(position_size, self.max_position_size))

        return position_size

    async def execute_trade(self, trade: Dict) -> None:
        """
        执行交易

        Args:
            trade: 交易信息
        """
        action = trade.get('action')
        amount = trade.get('amount', 0)
        price = trade.get('price', 0)

        if action == 'buy':
            self.current_position += amount
            if self.current_position == amount:
                # 开新多头仓位
                self.entry_price = price
            elif self.current_position > 0:
                # 加仓
                self.entry_price = (self.entry_price * (self.current_position - amount) + price * amount) / self.current_position

        elif action == 'sell':
            if amount >= self.current_position:
                # 平仓所有多头
                profit = (price - self.entry_price) * self.current_position
                self.realized_pnl += profit
                self.current_position = 0
                self.entry_price = 0
            else:
                # 减仓
                profit = (price - self.entry_price) * amount
                self.realized_pnl += profit
                self.current_position -= amount

        elif action == 'sell_short':
            self.current_position -= amount
            self.entry_price = price

        # 更新持仓价值
        self.position_value = abs(self.current_position) * price

        # 记录交易
        self.trades.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'amount': amount,
            'price': price,
            'position': self.current_position,
            'pnl': self.unrealized_pnl + self.realized_pnl
        })

        logger.info(
            f"均值回归策略执行交易: {action} {amount:.6f} @ {price:.2f}, "
            f"持仓: {self.current_position:.6f}, 盈亏: {self.realized_pnl + self.unrealized_pnl:.2f}"
        )

    def get_strategy_status(self) -> Dict:
        """获取策略状态"""
        return {
            'strategy': 'mean_reversion',
            'trading_pair': self.trading_pair,
            'is_running': self.is_running,
            'current_position': self.current_position,
            'entry_price': self.entry_price,
            'position_value': self.position_value,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'total_pnl': self.unrealized_pnl + self.realized_pnl,
            'current_mean': self.current_mean,
            'current_std': self.current_std,
            'upper_band': self.upper_band,
            'lower_band': self.lower_band,
            'total_trades': len(self.trades),
            'config': {
                'lookback_period': self.lookback_period,
                'std_multiplier': self.std_multiplier,
                'investment_amount': self.investment_amount
            }
        }


class MomentumStrategy:
    """动量策略

    基于价格动量的趋势跟踪策略
    """

    def __init__(
        self,
        trading_pair: str = "BTC/USDT",
        short_period: int = 10,
        long_period: int = 30,
        momentum_threshold: float = 0.02,
        investment_amount: float = 1000,
        min_position_size: float = 0.001,
        max_position_size: float = 1.0,
        position_limit: float = 5000,
        stop_loss_percent: float = 0.05,
        take_profit_percent: float = 0.15
    ):
        self.trading_pair = trading_pair
        self.short_period = short_period  # 短期均线周期
        self.long_period = long_period  # 长期均线周期
        self.momentum_threshold = momentum_threshold  # 动量阈值
        self.investment_amount = investment_amount
        self.min_position_size = min_position_size
        self.max_position_size = max_position_size
        self.position_limit = position_limit
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent

        # 价格历史
        self.price_history: List[float] = []
        self.max_history = long_period * 2

        # 持仓信息
        self.current_position: float = 0
        self.entry_price: float = 0
        self.position_value: float = 0
        self.unrealized_pnl: float = 0
        self.realized_pnl: float = 0

        # 交易历史
        self.trades: List[Dict] = []

        # 状态
        self.is_running = False
        self.short_ma: float = 0
        self.long_ma: float = 0
        self.momentum: float = 0
        self.last_signal: Optional[str] = None

    async def update_price(self, price: float) -> None:
        """
        更新价格数据

        Args:
            price: 当前价格
        """
        self.price_history.append(price)

        # 限制历史记录数量
        if len(self.price_history) > self.max_history:
            self.price_history = self.price_history[-self.max_history:]

        # 更新均线和动量
        if len(self.price_history) >= self.long_period:
            self.short_ma = mean(self.price_history[-self.short_period:])
            self.long_ma = mean(self.price_history[-self.long_period:])
            self.momentum = (self.short_ma - self.long_ma) / self.long_ma

        # 计算未实现盈亏
        if self.current_position != 0:
            price_change = (price - self.entry_price) * self.current_position
            self.unrealized_pnl = price_change
        else:
            self.unrealized_pnl = 0

    async def generate_signal(self, price: float) -> Optional[Dict]:
        """
        生成交易信号

        Args:
            price: 当前价格

        Returns:
            交易信号或None
        """
        if len(self.price_history) < self.long_period:
            return None

        # 检查止损
        if self.current_position > 0:
            loss_percent = (self.entry_price - price) / self.entry_price
            if loss_percent >= self.stop_loss_percent:
                return {
                    'action': 'sell',
                    'amount': self.current_position,
                    'price': price,
                    'reason': f'触发止损: 亏损{loss_percent:.2%}',
                    'signal_strength': 'strong'
                }

            # 检查止盈
            profit_percent = (price - self.entry_price) / self.entry_price
            if profit_percent >= self.take_profit_percent:
                return {
                    'action': 'sell',
                    'amount': self.current_position,
                    'price': price,
                    'reason': f'触发止盈: 盈利{profit_percent:.2%}',
                    'signal_strength': 'strong'
                }

        # 检查动量信号
        if self.momentum > self.momentum_threshold and self.current_position <= 0:
            # 强烈多头动量
            if self.current_position < 0:
                # 平空
                return {
                    'action': 'buy',
                    'amount': abs(self.current_position),
                    'price': price,
                    'reason': f'多头动量{self.momentum:.2%}，平空仓',
                    'signal_strength': 'strong'
                }
            elif self.last_signal != 'buy':
                # 开多
                return {
                    'action': 'buy',
                    'amount': self._calculate_position_size(price),
                    'price': price,
                    'reason': f'多头动量{self.momentum:.2%}，开多仓',
                    'signal_strength': 'strong'
                }

        elif self.momentum < -self.momentum_threshold and self.current_position >= 0:
            # 强烈空头动量
            if self.current_position > 0:
                # 平多
                return {
                    'action': 'sell',
                    'amount': self.current_position,
                    'price': price,
                    'reason': f'空头动量{self.momentum:.2%}，平多仓',
                    'signal_strength': 'strong'
                }
            elif self.last_signal != 'sell':
                # 开空
                return {
                    'action': 'sell_short',
                    'amount': self._calculate_position_size(price),
                    'price': price,
                    'reason': f'空头动量{self.momentum:.2%}，开空仓',
                    'signal_strength': 'strong'
                }

        return None

    def _calculate_position_size(self, price: float) -> float:
        """计算仓位大小"""
        # 基于投资金额计算
        position_value = min(self.investment_amount, self.position_limit - abs(self.position_value))
        position_size = position_value / price

        # 限制仓位大小
        position_size = max(self.min_position_size, min(position_size, self.max_position_size))

        return position_size

    async def execute_trade(self, trade: Dict) -> None:
        """
        执行交易

        Args:
            trade: 交易信息
        """
        action = trade.get('action')
        amount = trade.get('amount', 0)
        price = trade.get('price', 0)

        if action == 'buy':
            self.current_position += amount
            if self.current_position == amount:
                # 开新多头仓位
                self.entry_price = price
                self.last_signal = 'buy'
            elif self.current_position > 0:
                # 加仓
                self.entry_price = (self.entry_price * (self.current_position - amount) + price * amount) / self.current_position

        elif action == 'sell':
            if amount >= self.current_position:
                # 平仓所有多头
                profit = (price - self.entry_price) * self.current_position
                self.realized_pnl += profit
                self.current_position = 0
                self.entry_price = 0
                self.last_signal = 'sell'
            else:
                # 减仓
                profit = (price - self.entry_price) * amount
                self.realized_pnl += profit
                self.current_position -= amount

        elif action == 'sell_short':
            self.current_position -= amount
            self.entry_price = price
            self.last_signal = 'sell'

        # 更新持仓价值
        self.position_value = abs(self.current_position) * price

        # 记录交易
        self.trades.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'amount': amount,
            'price': price,
            'position': self.current_position,
            'pnl': self.unrealized_pnl + self.realized_pnl
        })

        logger.info(
            f"动量策略执行交易: {action} {amount:.6f} @ {price:.2f}, "
            f"持仓: {self.current_position:.6f}, 盈亏: {self.realized_pnl + self.unrealized_pnl:.2f}"
        )

    def get_strategy_status(self) -> Dict:
        """获取策略状态"""
        return {
            'strategy': 'momentum',
            'trading_pair': self.trading_pair,
            'is_running': self.is_running,
            'current_position': self.current_position,
            'entry_price': self.entry_price,
            'position_value': self.position_value,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'total_pnl': self.unrealized_pnl + self.realized_pnl,
            'short_ma': self.short_ma,
            'long_ma': self.long_ma,
            'momentum': self.momentum,
            'last_signal': self.last_signal,
            'total_trades': len(self.trades),
            'config': {
                'short_period': self.short_period,
                'long_period': self.long_period,
                'momentum_threshold': self.momentum_threshold,
                'investment_amount': self.investment_amount
            }
        }


# 策略工厂
class StrategyFactory:
    """策略工厂类"""

    @staticmethod
    def create_strategy(strategy_type: str, config: Dict) -> Optional[object]:
        """
        创建策略实例

        Args:
            strategy_type: 策略类型
            config: 策略配置

        Returns:
            策略实例或None
        """
        if strategy_type == 'mean_reversion':
            return MeanReversionStrategy(
                trading_pair=config.get('trading_pair', 'BTC/USDT'),
                lookback_period=config.get('lookback_period', 20),
                std_multiplier=config.get('std_multiplier', 2.0),
                investment_amount=config.get('investment_amount', 1000),
                min_position_size=config.get('min_position_size', 0.001),
                max_position_size=config.get('max_position_size', 1.0),
                position_limit=config.get('position_limit', 5000),
                rebalance_threshold=config.get('rebalance_threshold', 0.5)
            )
        elif strategy_type == 'momentum':
            return MomentumStrategy(
                trading_pair=config.get('trading_pair', 'BTC/USDT'),
                short_period=config.get('short_period', 10),
                long_period=config.get('long_period', 30),
                momentum_threshold=config.get('momentum_threshold', 0.02),
                investment_amount=config.get('investment_amount', 1000),
                min_position_size=config.get('min_position_size', 0.001),
                max_position_size=config.get('max_position_size', 1.0),
                position_limit=config.get('position_limit', 5000),
                stop_loss_percent=config.get('stop_loss_percent', 0.05),
                take_profit_percent=config.get('take_profit_percent', 0.15)
            )

        return None
