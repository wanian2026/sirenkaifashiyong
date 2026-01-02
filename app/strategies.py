import ccxt
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from app.config import settings


class HedgeGridStrategy:
    """对冲网格策略"""

    def __init__(
        self,
        exchange_id: str = None,
        api_key: str = None,
        api_secret: str = None,
        trading_pair: str = "BTC/USDT",
        grid_levels: int = 10,
        grid_spacing: float = 0.02,
        investment_amount: float = 1000
    ):
        self.exchange_id = exchange_id or settings.EXCHANGE_ID
        self.trading_pair = trading_pair
        self.grid_levels = grid_levels
        self.grid_spacing = grid_spacing
        self.investment_amount = investment_amount

        # 初始化交易所连接
        if api_key and api_secret:
            self.exchange = getattr(ccxt, self.exchange_id)({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
            })
        else:
            # 使用模拟模式
            self.exchange = None
            self.mock_mode = True

        self.grid_orders: List[Dict] = []
        self.current_price: float = 0
        self.total_invested: float = 0
        self.realized_profit: float = 0

    async def initialize_grid(self, base_price: float = None) -> Dict:
        """初始化网格"""
        if base_price is None:
            base_price = await self.get_current_price()

        self.current_price = base_price
        self.grid_orders = []

        # 计算网格层级价格
        grid_prices = []
        for i in range(-self.grid_levels // 2, self.grid_levels // 2 + 1):
            price = base_price * (1 + i * self.grid_spacing)
            if price > 0:
                grid_prices.append(price)

        # 为每个层级创建订单
        amount_per_level = self.investment_amount / len(grid_prices)

        for i, price in enumerate(grid_prices):
            if price < base_price:
                # 低于当前价格，设置买单
                order = {
                    'level': i,
                    'type': 'buy',
                    'price': price,
                    'amount': amount_per_level / price,
                    'status': 'pending'
                }
            elif price > base_price:
                # 高于当前价格，设置卖单
                order = {
                    'level': i,
                    'type': 'sell',
                    'price': price,
                    'amount': amount_per_level / price,
                    'status': 'pending'
                }
            else:
                continue

            self.grid_orders.append(order)

        return {
            'status': 'initialized',
            'current_price': self.current_price,
            'grid_count': len(self.grid_orders),
            'orders': self.grid_orders
        }

    async def get_current_price(self) -> float:
        """获取当前价格"""
        if self.exchange:
            try:
                ticker = await asyncio.to_thread(self.exchange.fetch_ticker, self.trading_pair)
                return ticker['last']
            except Exception as e:
                print(f"获取价格失败: {e}")
                return self.current_price
        else:
            # 模拟价格波动
            import random
            variation = random.uniform(-0.001, 0.001)
            self.current_price = self.current_price * (1 + variation) if self.current_price else 50000
            return self.current_price

    async def check_and_execute_orders(self) -> List[Dict]:
        """检查并执行订单"""
        executed_orders = []
        current_price = await self.get_current_price()
        self.current_price = current_price

        for order in self.grid_orders:
            if order['status'] != 'pending':
                continue

            # 检查买单是否可以执行
            if order['type'] == 'buy' and current_price <= order['price']:
                if self.exchange:
                    # 实盘交易
                    try:
                        # 这里应该调用交易所API下单
                        # result = await self.place_buy_order(...)
                        pass
                    except Exception as e:
                        print(f"买单执行失败: {e}")
                        continue

                # 更新订单状态
                order['status'] = 'filled'
                self.total_invested += order['price'] * order['amount']
                executed_orders.append(order.copy())

                # 创建对应卖单（对冲）
                sell_price = order['price'] * (1 + self.grid_spacing)
                sell_order = {
                    'level': order['level'] + self.grid_levels,
                    'type': 'sell',
                    'price': sell_price,
                    'amount': order['amount'],
                    'status': 'pending'
                }
                self.grid_orders.append(sell_order)

            # 检查卖单是否可以执行
            elif order['type'] == 'sell' and current_price >= order['price']:
                if self.exchange:
                    # 实盘交易
                    try:
                        # 这里应该调用交易所API下单
                        # result = await self.place_sell_order(...)
                        pass
                    except Exception as e:
                        print(f"卖单执行失败: {e}")
                        continue

                # 计算利润
                profit = (order['price'] - (order['price'] / (1 + self.grid_spacing))) * order['amount']
                self.realized_profit += profit

                # 更新订单状态
                order['status'] = 'filled'
                executed_orders.append(order.copy())

        return executed_orders

    async def get_strategy_status(self) -> Dict:
        """获取策略状态"""
        pending_orders = [o for o in self.grid_orders if o['status'] == 'pending']
        filled_orders = [o for o in self.grid_orders if o['status'] == 'filled']

        return {
            'trading_pair': self.trading_pair,
            'current_price': self.current_price,
            'total_invested': self.total_invested,
            'realized_profit': self.realized_profit,
            'pending_orders': len(pending_orders),
            'filled_orders': len(filled_orders),
            'grid_levels': self.grid_levels,
            'grid_spacing': self.grid_spacing,
            'is_mock_mode': self.exchange is None
        }

    def stop(self):
        """停止策略"""
        self.grid_orders = []
