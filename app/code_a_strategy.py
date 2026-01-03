"""
代码A策略 - 核心交易策略
基于技术分析的智能交易策略，结合趋势跟踪和均值回归
"""

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np


class CodeAStrategy:
    """代码A策略 - 核心交易策略"""

    def __init__(
        self,
        trading_pair: str = "BTC/USDT",
        investment_amount: float = 10000,
        trend_period: int = 20,  # 趋势判断周期
        reversion_period: int = 10,  # 均值回归周期
        volatility_threshold: float = 0.02,  # 波动率阈值
        position_size: float = 0.1,  # 单笔持仓比例
        take_profit: float = 0.05,  # 止盈百分比
        stop_loss: float = 0.03,  # 止损百分比
        risk_limit: float = 0.02  # 单笔风险限制
    ):
        """
        初始化代码A策略

        Args:
            trading_pair: 交易对
            investment_amount: 投资金额
            trend_period: 趋势判断周期
            reversion_period: 均值回归周期
            volatility_threshold: 波动率阈值
            position_size: 单笔持仓比例
            take_profit: 止盈百分比
            stop_loss: 止损百分比
            risk_limit: 单笔风险限制
        """
        self.trading_pair = trading_pair
        self.investment_amount = investment_amount
        self.trend_period = trend_period
        self.reversion_period = reversion_period
        self.volatility_threshold = volatility_threshold
        self.position_size = position_size
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.risk_limit = risk_limit

        # 状态变量
        self.price_history: List[float] = []
        self.position: float = 0  # 当前持仓
        self.entry_price: float = 0  # 入场价格
        self.total_invested: float = 0
        self.realized_profit: float = 0
        self.trades: List[Dict] = []

    def calculate_indicators(self, prices: List[float]) -> Dict:
        """
        计算技术指标

        Args:
            prices: 价格历史列表

        Returns:
            技术指标字典
        """
        if len(prices) < max(self.trend_period, self.reversion_period):
            return {}

        df = pd.DataFrame({'price': prices})

        # 移动平均线
        df['ma_trend'] = df['price'].rolling(window=self.trend_period).mean()
        df['ma_reversion'] = df['price'].rolling(window=self.reversion_period).mean()

        # 波动率
        df['returns'] = df['price'].pct_change()
        df['volatility'] = df['returns'].rolling(window=self.reversion_period).std()

        # RSI
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.reversion_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.reversion_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]

        return {
            'ma_trend': float(latest['ma_trend']),
            'ma_reversion': float(latest['ma_reversion']),
            'volatility': float(latest['volatility']),
            'rsi': float(latest['rsi']),
            'price': float(latest['price'])
        }

    def analyze_market(self, current_price: float) -> Dict:
        """
        分析市场状态

        Args:
            current_price: 当前价格

        Returns:
            市场分析结果
        """
        # 更新价格历史
        self.price_history.append(current_price)

        # 计算指标
        indicators = self.calculate_indicators(self.price_history)

        if not indicators:
            return {'status': 'insufficient_data'}

        price = indicators['price']
        ma_trend = indicators['ma_trend']
        ma_reversion = indicators['ma_reversion']
        volatility = indicators['volatility']
        rsi = indicators['rsi']

        # 趋势判断
        if price > ma_trend:
            trend = 'up'
        elif price < ma_trend:
            trend = 'down'
        else:
            trend = 'neutral'

        # 均值回归信号
        deviation = (price - ma_reversion) / ma_reversion

        # RSI信号
        if rsi > 70:
            rsi_signal = 'overbought'
        elif rsi < 30:
            rsi_signal = 'oversold'
        else:
            rsi_signal = 'neutral'

        return {
            'status': 'analyzed',
            'trend': trend,
            'deviation': deviation,
            'rsi_signal': rsi_signal,
            'volatility': volatility,
            'indicators': indicators
        }

    def generate_signal(self, current_price: float) -> Optional[Dict]:
        """
        生成交易信号

        Args:
            current_price: 当前价格

        Returns:
            交易信号或None
        """
        analysis = self.analyze_market(current_price)

        if analysis['status'] != 'analyzed':
            return None

        # 检查是否需要止损/止盈
        if self.position > 0:
            profit_pct = (current_price - self.entry_price) / self.entry_price
            if profit_pct >= self.take_profit:
                return {
                    'action': 'sell',
                    'reason': 'take_profit',
                    'price': current_price,
                    'amount': self.position
                }
            elif profit_pct <= -self.stop_loss:
                return {
                    'action': 'sell',
                    'reason': 'stop_loss',
                    'price': current_price,
                    'amount': self.position
                }
        elif self.position < 0:
            profit_pct = (self.entry_price - current_price) / self.entry_price
            if profit_pct >= self.take_profit:
                return {
                    'action': 'buy',
                    'reason': 'take_profit',
                    'price': current_price,
                    'amount': abs(self.position)
                }
            elif profit_pct <= -self.stop_loss:
                return {
                    'action': 'buy',
                    'reason': 'stop_loss',
                    'price': current_price,
                    'amount': abs(self.position)
                }

        # 生成新的交易信号
        signal = None

        # 趋势跟踪 + 均值回归组合策略
        if analysis['trend'] == 'up' and analysis['deviation'] < -self.volatility_threshold:
            # 上升趋势 + 价格低于均值，买入
            signal = {
                'action': 'buy',
                'reason': 'trend_up_reversion',
                'price': current_price,
                'amount': self.investment_amount * self.position_size / current_price
            }
        elif analysis['trend'] == 'down' and analysis['deviation'] > self.volatility_threshold:
            # 下降趋势 + 价格高于均值，卖出
            signal = {
                'action': 'sell',
                'reason': 'trend_down_reversion',
                'price': current_price,
                'amount': self.investment_amount * self.position_size / current_price
            }
        elif analysis['rsi_signal'] == 'oversold' and self.position <= 0:
            # 超卖，买入
            signal = {
                'action': 'buy',
                'reason': 'rsi_oversold',
                'price': current_price,
                'amount': self.investment_amount * self.position_size / current_price
            }
        elif analysis['rsi_signal'] == 'overbought' and self.position >= 0:
            # 超买，卖出
            signal = {
                'action': 'sell',
                'reason': 'rsi_overbought',
                'price': current_price,
                'amount': self.investment_amount * self.position_size / current_price
            }

        return signal

    def execute_trade(self, signal: Dict) -> Dict:
        """
        执行交易

        Args:
            signal: 交易信号

        Returns:
            交易结果
        """
        action = signal['action']
        price = signal['price']
        amount = signal['amount']
        reason = signal['reason']

        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': self.trading_pair,
            'action': action,
            'price': price,
            'amount': amount,
            'reason': reason
        }

        if action == 'buy':
            self.position += amount
            self.entry_price = price if self.position == amount else (self.entry_price * (self.position - amount) + price * amount) / self.position
            self.total_invested += price * amount
        else:  # sell
            profit = (price - self.entry_price) * amount if self.position > 0 else (self.entry_price - price) * amount
            self.realized_profit += profit
            self.position -= amount

        self.trades.append(trade)

        return {
            'status': 'executed',
            'trade': trade,
            'position': self.position,
            'realized_profit': self.realized_profit
        }

    def get_status(self) -> Dict:
        """
        获取策略状态

        Returns:
            策略状态信息
        """
        return {
            'strategy': 'CodeA',
            'trading_pair': self.trading_pair,
            'position': self.position,
            'entry_price': self.entry_price,
            'total_invested': self.total_invested,
            'realized_profit': self.realized_profit,
            'total_trades': len(self.trades)
        }


class CodeABacktestStrategy:
    """代码A策略回测实现"""

    @staticmethod
    def execute(data: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """
        执行回测

        Args:
            data: 价格数据
            params: 策略参数

        Returns:
            回测结果
        """
        # 初始化策略
        strategy = CodeAStrategy(
            trading_pair=params.get('trading_pair', 'BTC/USDT'),
            investment_amount=params.get('investment_amount', 10000),
            trend_period=params.get('trend_period', 20),
            reversion_period=params.get('reversion_period', 10),
            volatility_threshold=params.get('volatility_threshold', 0.02),
            position_size=params.get('position_size', 0.1),
            take_profit=params.get('take_profit', 0.05),
            stop_loss=params.get('stop_loss', 0.03),
            risk_limit=params.get('risk_limit', 0.02)
        )

        # 运行回测
        trades = []
        for _, row in data.iterrows():
            price = row['price'] if 'price' in row else row['close']
            signal = strategy.generate_signal(price)

            if signal:
                result = strategy.execute_trade(signal)
                trades.append(result['trade'])

        return pd.DataFrame(trades)
