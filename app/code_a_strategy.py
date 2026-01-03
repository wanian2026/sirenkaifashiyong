"""
代号A策略（Code A Strategy）
基于对冲马丁格尔的智能交易策略

策略逻辑：
1. 初始同时开一个多单和一个空单
2. 上涨触发：价格 ≥ 多单成本价 × (1 + 上涨阈值) 时，平多开多
3. 下跌触发：价格 ≤ 空单成本价 × (1 - 下跌阈值) 时，平空开空
4. 止损：多单价格 ≤ 成本价 × (1 - 止损比例)，空单价格 ≥ 成本价 × (1 + 止损比例)
5. 亏损仓位：要么止损，要么等反弹
"""

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass, field


@dataclass
class Position:
    """仓位信息"""
    position_id: str
    side: str  # 'long' or 'short'
    entry_price: float
    amount: float
    entry_time: datetime
    status: str = 'open'  # 'open', 'closed'
    close_price: Optional[float] = None
    close_time: Optional[datetime] = None
    profit: float = 0.0


class CodeAStrategy:
    """代号A策略 - 对冲马丁格尔策略"""

    def __init__(
        self,
        trading_pair: str = "BTC/USDT",
        investment_amount: float = 1000,
        up_threshold: float = 0.02,  # 上涨阈值（百分比）
        down_threshold: float = 0.02,  # 下跌阈值（百分比）
        stop_loss: float = 0.10,  # 止损比例（百分比）
    ):
        """
        初始化代号A策略

        Args:
            trading_pair: 交易对
            investment_amount: 单边投资金额
            up_threshold: 上涨阈值（百分比）
            down_threshold: 下跌阈值（百分比）
            stop_loss: 止损比例（百分比）
        """
        self.trading_pair = trading_pair
        self.investment_amount = investment_amount
        self.up_threshold = up_threshold
        self.down_threshold = down_threshold
        self.stop_loss = stop_loss

        # 仓位管理
        self.long_positions: List[Position] = []
        self.short_positions: List[Position] = []
        self.position_counter = 0
        self.is_initialized = False

        # 交易历史
        self.trades: List[Dict] = []

        # 统计信息
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.total_trades = 0
        self.win_trades = 0
        self.lose_trades = 0

    def initialize(self, current_price: float):
        """
        初始化策略，同时开多空两单

        Args:
            current_price: 当前价格
        """
        if self.is_initialized:
            return

        # 计算开仓数量
        amount = self.investment_amount / current_price

        # 开多单
        long_pos = Position(
            position_id=f"long_{self._next_id()}",
            side='long',
            entry_price=current_price,
            amount=amount,
            entry_time=datetime.now()
        )
        self.long_positions.append(long_pos)

        # 开空单
        short_pos = Position(
            position_id=f"short_{self._next_id()}",
            side='short',
            entry_price=current_price,
            amount=amount,
            entry_time=datetime.now()
        )
        self.short_positions.append(short_pos)

        self.is_initialized = True

        # 记录初始化交易
        self.trades.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'open',
            'side': 'both',
            'price': current_price,
            'long_amount': amount,
            'short_amount': amount,
            'reason': 'initial_setup'
        })

    def _next_id(self) -> int:
        """生成下一个仓位ID"""
        self.position_counter += 1
        return self.position_counter

    def update(self, current_price: float) -> Dict:
        """
        更新策略状态并生成交易信号

        Args:
            current_price: 当前价格

        Returns:
            交易信号列表
        """
        if not self.is_initialized:
            self.initialize(current_price)
            return {'signals': [], 'status': 'initialized'}

        signals = []

        # 检查多单
        for pos in self.long_positions:
            if pos.status == 'open':
                # 检查上涨触发
                up_trigger_price = pos.entry_price * (1 + self.up_threshold)
                if current_price >= up_trigger_price:
                    # 触发平多开多
                    signals.append({
                        'action': 'close_long',
                        'position_id': pos.position_id,
                        'price': current_price,
                        'amount': pos.amount,
                        'reason': f'up_threshold: {current_price:.2f} >= {up_trigger_price:.2f}'
                    })
                    signals.append({
                        'action': 'open_long',
                        'price': current_price,
                        'amount': pos.amount,
                        'reason': 'reopen_after_close'
                    })

                # 检查止损
                stop_loss_price = pos.entry_price * (1 - self.stop_loss)
                if current_price <= stop_loss_price:
                    signals.append({
                        'action': 'close_long',
                        'position_id': pos.position_id,
                        'price': current_price,
                        'amount': pos.amount,
                        'reason': f'stop_loss: {current_price:.2f} <= {stop_loss_price:.2f}'
                    })

        # 检查空单
        for pos in self.short_positions:
            if pos.status == 'open':
                # 检查下跌触发
                down_trigger_price = pos.entry_price * (1 - self.down_threshold)
                if current_price <= down_trigger_price:
                    # 触发平空开空
                    signals.append({
                        'action': 'close_short',
                        'position_id': pos.position_id,
                        'price': current_price,
                        'amount': pos.amount,
                        'reason': f'down_threshold: {current_price:.2f} <= {down_trigger_price:.2f}'
                    })
                    signals.append({
                        'action': 'open_short',
                        'price': current_price,
                        'amount': pos.amount,
                        'reason': 'reopen_after_close'
                    })

                # 检查止损
                stop_loss_price = pos.entry_price * (1 + self.stop_loss)
                if current_price >= stop_loss_price:
                    signals.append({
                        'action': 'close_short',
                        'position_id': pos.position_id,
                        'price': current_price,
                        'amount': pos.amount,
                        'reason': f'stop_loss: {current_price:.2f} >= {stop_loss_price:.2f}'
                    })

        return {
            'signals': signals,
            'status': 'updated'
        }

    def execute_signals(self, signals: List[Dict]) -> Dict:
        """
        执行交易信号

        Args:
            signals: 交易信号列表

        Returns:
            执行结果
        """
        executed_trades = []

        for signal in signals:
            if signal['action'] == 'close_long':
                # 平多单
                pos = self._find_position(signal['position_id'], self.long_positions)
                if pos and pos.status == 'open':
                    profit = (signal['price'] - pos.entry_price) * pos.amount
                    pos.status = 'closed'
                    pos.close_price = signal['price']
                    pos.close_time = datetime.now()
                    pos.profit = profit

                    # 更新统计
                    self.total_trades += 1
                    if profit > 0:
                        self.total_profit += profit
                        self.win_trades += 1
                    else:
                        self.total_loss += abs(profit)
                        self.lose_trades += 1

                    executed_trades.append({
                        'timestamp': datetime.now().isoformat(),
                        'action': 'close_long',
                        'position_id': pos.position_id,
                        'price': signal['price'],
                        'amount': pos.amount,
                        'profit': profit
                    })

            elif signal['action'] == 'close_short':
                # 平空单
                pos = self._find_position(signal['position_id'], self.short_positions)
                if pos and pos.status == 'open':
                    profit = (pos.entry_price - signal['price']) * pos.amount
                    pos.status = 'closed'
                    pos.close_price = signal['price']
                    pos.close_time = datetime.now()
                    pos.profit = profit

                    # 更新统计
                    self.total_trades += 1
                    if profit > 0:
                        self.total_profit += profit
                        self.win_trades += 1
                    else:
                        self.total_loss += abs(profit)
                        self.lose_trades += 1

                    executed_trades.append({
                        'timestamp': datetime.now().isoformat(),
                        'action': 'close_short',
                        'position_id': pos.position_id,
                        'price': signal['price'],
                        'amount': pos.amount,
                        'profit': profit
                    })

            elif signal['action'] == 'open_long':
                # 开多单
                new_pos = Position(
                    position_id=f"long_{self._next_id()}",
                    side='long',
                    entry_price=signal['price'],
                    amount=signal['amount'],
                    entry_time=datetime.now()
                )
                self.long_positions.append(new_pos)
                executed_trades.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'open_long',
                    'position_id': new_pos.position_id,
                    'price': signal['price'],
                    'amount': signal['amount']
                })

            elif signal['action'] == 'open_short':
                # 开空单
                new_pos = Position(
                    position_id=f"short_{self._next_id()}",
                    side='short',
                    entry_price=signal['price'],
                    amount=signal['amount'],
                    entry_time=datetime.now()
                )
                self.short_positions.append(new_pos)
                executed_trades.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'open_short',
                    'position_id': new_pos.position_id,
                    'price': signal['price'],
                    'amount': signal['amount']
                })

        # 记录所有交易
        self.trades.extend(executed_trades)

        return {
            'executed_trades': executed_trades,
            'total_trades': self.total_trades
        }

    def _find_position(self, position_id: str, positions: List[Position]) -> Optional[Position]:
        """查找仓位"""
        for pos in positions:
            if pos.position_id == position_id:
                return pos
        return None

    def get_status(self) -> Dict:
        """
        获取策略状态

        Returns:
            策略状态信息
        """
        # 计算未实现盈亏
        long_pnl = sum([(pos.entry_price - pos.entry_price) * pos.amount for pos in self.long_positions if pos.status == 'open'])
        short_pnl = sum([(pos.entry_price - pos.entry_price) * pos.amount for pos in self.short_positions if pos.status == 'open'])

        # 计算已实现盈亏
        realized_pnl = self.total_profit - self.total_loss

        return {
            'strategy': 'CodeA',
            'trading_pair': self.trading_pair,
            'investment_amount': self.investment_amount,
            'is_initialized': self.is_initialized,
            'long_positions': {
                'total': len(self.long_positions),
                'open': len([p for p in self.long_positions if p.status == 'open']),
                'closed': len([p for p in self.long_positions if p.status == 'closed'])
            },
            'short_positions': {
                'total': len(self.short_positions),
                'open': len([p for p in self.short_positions if p.status == 'open']),
                'closed': len([p for p in self.short_positions if p.status == 'closed'])
            },
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'realized_pnl': realized_pnl,
            'total_trades': self.total_trades,
            'win_trades': self.win_trades,
            'lose_trades': self.lose_trades,
            'win_rate': self.win_trades / self.total_trades if self.total_trades > 0 else 0,
            'up_threshold': self.up_threshold,
            'down_threshold': self.down_threshold,
            'stop_loss': self.stop_loss
        }

    def get_open_positions(self) -> Dict:
        """获取当前持仓"""
        return {
            'long': [
                {
                    'position_id': pos.position_id,
                    'entry_price': pos.entry_price,
                    'amount': pos.amount,
                    'entry_time': pos.entry_time.isoformat()
                }
                for pos in self.long_positions if pos.status == 'open'
            ],
            'short': [
                {
                    'position_id': pos.position_id,
                    'entry_price': pos.entry_price,
                    'amount': pos.amount,
                    'entry_time': pos.entry_time.isoformat()
                }
                for pos in self.short_positions if pos.status == 'open'
            ]
        }


class CodeABacktestStrategy:
    """代号A策略回测实现"""

    @staticmethod
    def execute(data: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """
        执行回测

        Args:
            data: 价格数据（必须包含 'price' 或 'close' 列）
            params: 策略参数

        Returns:
            回测交易记录
        """
        # 初始化策略
        strategy = CodeAStrategy(
            trading_pair=params.get('trading_pair', 'BTC/USDT'),
            investment_amount=params.get('investment_amount', 1000),
            up_threshold=params.get('up_threshold', 0.02),
            down_threshold=params.get('down_threshold', 0.02),
            stop_loss=params.get('stop_loss', 0.10)
        )

        # 运行回测
        for _, row in data.iterrows():
            price = row['price'] if 'price' in row else row['close']

            # 更新策略状态
            result = strategy.update(price)

            # 执行交易信号
            if result['signals']:
                strategy.execute_signals(result['signals'])

        # 返回交易记录
        return pd.DataFrame(strategy.trades)
