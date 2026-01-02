import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from app.config import settings
from app.exchange import ExchangeAPI


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
        investment_amount: float = 1000,
        dynamic_grid: bool = False,
        batch_build: bool = False,
        batch_count: int = 3
    ):
        self.exchange_id = exchange_id or settings.EXCHANGE_ID
        self.trading_pair = trading_pair
        self.grid_levels = grid_levels
        self.grid_spacing = grid_spacing
        self.investment_amount = investment_amount
        self.dynamic_grid = dynamic_grid  # 是否启用动态网格
        self.batch_build = batch_build  # 是否分批建仓
        self.batch_count = batch_count  # 分批数量

        # 初始化交易所连接
        if api_key and api_secret:
            self.exchange_api = ExchangeAPI(
                exchange_id=self.exchange_id,
                api_key=api_key,
                api_secret=api_secret
            )
            self.mock_mode = False
        else:
            # 使用模拟模式
            self.exchange_api = None
            self.mock_mode = True

        self.grid_orders: List[Dict] = []
        self.current_price: float = 0
        self.total_invested: float = 0
        self.realized_profit: float = 0
        self.price_history: List[float] = []  # 价格历史，用于动态调整
        self.max_history = 100  # 最大历史记录数

        # 动态网格参数
        self.base_price: float = 0
        self.volatility_threshold: float = 0.05  # 波动率阈值

    async def initialize_grid(self, base_price: float = None) -> Dict:
        """初始化网格"""
        if base_price is None:
            base_price = await self.get_current_price()

        self.base_price = base_price
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

        # 如果启用分批建仓，只创建第一批订单
        if self.batch_build:
            batch_size = len(grid_prices) // self.batch_count
            grid_prices = grid_prices[:batch_size] if batch_size > 0 else grid_prices[:1]

        for i, price in enumerate(grid_prices):
            if price < base_price:
                # 低于当前价格，设置买单
                order = {
                    'level': i,
                    'type': 'buy',
                    'price': price,
                    'amount': amount_per_level / price,
                    'status': 'pending',
                    'batch_index': 1 if self.batch_build else None
                }
            elif price > base_price:
                # 高于当前价格，设置卖单
                order = {
                    'level': i,
                    'type': 'sell',
                    'price': price,
                    'amount': amount_per_level / price,
                    'status': 'pending',
                    'batch_index': 1 if self.batch_build else None
                }
            else:
                continue

            self.grid_orders.append(order)

        return {
            'status': 'initialized',
            'current_price': self.current_price,
            'grid_count': len(self.grid_orders),
            'dynamic_grid': self.dynamic_grid,
            'batch_build': self.batch_build,
            'orders': self.grid_orders
        }

    async def adjust_grid_dynamically(self) -> Dict:
        """动态调整网格"""
        if not self.dynamic_grid:
            return {'status': 'skipped', 'reason': '动态网格未启用'}

        # 计算波动率
        if len(self.price_history) < 10:
            return {'status': 'skipped', 'reason': '价格历史不足'}

        recent_prices = self.price_history[-10:]
        price_std = sum((p - sum(recent_prices) / len(recent_prices)) ** 2 for p in recent_prices) / len(recent_prices)
        volatility = (price_std ** 0.5) / self.current_price

        if volatility < self.volatility_threshold:
            return {'status': 'skipped', 'reason': '波动率低于阈值', 'volatility': volatility}

        # 计算新的基准价格
        new_base_price = sum(recent_prices) / len(recent_prices)

        # 调整网格间距
        new_spacing = self.grid_spacing * (1 + volatility)
        new_spacing = min(new_spacing, 0.1)  # 限制最大间距

        # 重新创建网格
        self.grid_spacing = new_spacing
        self.base_price = new_base_price

        return {
            'status': 'adjusted',
            'old_base_price': self.current_price,
            'new_base_price': new_base_price,
            'old_spacing': self.grid_spacing / (1 + volatility),
            'new_spacing': new_spacing,
            'volatility': volatility
        }

    async def create_next_batch(self) -> Dict:
        """创建下一批订单（分批建仓）"""
        if not self.batch_build:
            return {'status': 'skipped', 'reason': '分批建仓未启用'}

        # 查找当前最大的批次数
        max_batch = max([o.get('batch_index', 1) for o in self.grid_orders])
        if max_batch >= self.batch_count:
            return {'status': 'completed', 'reason': '已达到最大批次数'}

        # 计算新的网格层级
        grid_prices = []
        for i in range(-self.grid_levels // 2, self.grid_levels // 2 + 1):
            price = self.base_price * (1 + i * self.grid_spacing)
            if price > 0:
                grid_prices.append(price)

        batch_size = len(grid_prices) // self.batch_count
        start_index = max_batch * batch_size
        end_index = min(start_index + batch_size, len(grid_prices))
        new_batch_prices = grid_prices[start_index:end_index]

        if not new_batch_prices:
            return {'status': 'completed', 'reason': '没有更多订单需要创建'}

        # 创建新批次的订单
        amount_per_level = self.investment_amount / len(grid_prices)

        for i, price in enumerate(new_batch_prices):
            level = start_index + i
            if price < self.current_price:
                order = {
                    'level': level,
                    'type': 'buy',
                    'price': price,
                    'amount': amount_per_level / price,
                    'status': 'pending',
                    'batch_index': max_batch + 1
                }
            elif price > self.current_price:
                order = {
                    'level': level,
                    'type': 'sell',
                    'price': price,
                    'amount': amount_per_level / price,
                    'status': 'pending',
                    'batch_index': max_batch + 1
                }
            else:
                continue

            self.grid_orders.append(order)

        return {
            'status': 'created',
            'batch_index': max_batch + 1,
            'orders_created': len(new_batch_prices)
        }

    async def get_current_price(self) -> float:
        """获取当前价格"""
        if self.exchange_api:
            try:
                ticker = await self.exchange_api.get_ticker(self.trading_pair)
                new_price = ticker['last']
            except Exception as e:
                print(f"获取价格失败: {e}")
                new_price = self.current_price
        else:
            # 模拟价格波动
            import random
            variation = random.uniform(-0.001, 0.001)
            new_price = self.current_price * (1 + variation) if self.current_price else 50000

        # 更新价格历史
        if new_price != self.current_price:
            self.price_history.append(new_price)
            if len(self.price_history) > self.max_history:
                self.price_history.pop(0)
            self.current_price = new_price

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
                if self.exchange_api:
                    # 实盘交易 - 下买单
                    try:
                        result = await self.exchange_api.place_order(
                            symbol=self.trading_pair,
                            side='buy',
                            order_type='limit',
                            amount=order['amount'],
                            price=order['price']
                        )
                        order['exchange_order_id'] = result['id']
                    except Exception as e:
                        print(f"买单执行失败: {e}")
                        continue

                # 更新订单状态
                order['status'] = 'filled'
                order['filled_at'] = datetime.now().isoformat()
                self.total_invested += order['price'] * order['amount']
                executed_orders.append(order.copy())

                # 创建对应卖单（对冲）
                sell_price = order['price'] * (1 + self.grid_spacing)
                sell_order = {
                    'level': order['level'] + self.grid_levels,
                    'type': 'sell',
                    'price': sell_price,
                    'amount': order['amount'],
                    'status': 'pending',
                    'batch_index': order.get('batch_index')
                }
                self.grid_orders.append(sell_order)

            # 检查卖单是否可以执行
            elif order['type'] == 'sell' and current_price >= order['price']:
                if self.exchange_api:
                    # 实盘交易 - 下卖单
                    try:
                        result = await self.exchange_api.place_order(
                            symbol=self.trading_pair,
                            side='sell',
                            order_type='limit',
                            amount=order['amount'],
                            price=order['price']
                        )
                        order['exchange_order_id'] = result['id']
                    except Exception as e:
                        print(f"卖单执行失败: {e}")
                        continue

                # 计算利润
                profit = (order['price'] - (order['price'] / (1 + self.grid_spacing))) * order['amount']
                self.realized_profit += profit

                # 更新订单状态
                order['status'] = 'filled'
                order['filled_at'] = datetime.now().isoformat()
                executed_orders.append(order.copy())

        return executed_orders

    async def place_grid_orders_to_exchange(self) -> List[Dict]:
        """将网格订单提交到交易所"""
        if not self.exchange_api:
            return []

        results = []
        for order in self.grid_orders:
            if order['status'] != 'pending' or 'exchange_order_id' in order:
                continue

            try:
                result = await self.exchange_api.place_order(
                    symbol=self.trading_pair,
                    side=order['type'],
                    order_type='limit',
                    amount=order['amount'],
                    price=order['price']
                )
                order['exchange_order_id'] = result['id']
                results.append({
                    'level': order['level'],
                    'type': order['type'],
                    'price': order['price'],
                    'exchange_order_id': result['id'],
                    'status': 'submitted'
                })
            except Exception as e:
                print(f"提交订单失败: {order}, 错误: {e}")
                results.append({
                    'level': order['level'],
                    'type': order['type'],
                    'price': order['price'],
                    'status': 'failed',
                    'error': str(e)
                })

        return results

    async def get_strategy_status(self) -> Dict:
        """获取策略状态"""
        pending_orders = [o for o in self.grid_orders if o['status'] == 'pending']
        filled_orders = [o for o in self.grid_orders if o['status'] == 'filled']

        # 计算当前持仓
        buy_orders_filled = [o for o in filled_orders if o['type'] == 'buy']
        sell_orders_filled = [o for o in filled_orders if o['type'] == 'sell']
        current_position = sum(o['amount'] for o in buy_orders_filled) - sum(o['amount'] for o in sell_orders_filled)

        # 计算未实现盈亏
        avg_buy_price = sum(o['price'] * o['amount'] for o in buy_orders_filled) / sum(o['amount'] for o in buy_orders_filled) if buy_orders_filled else 0
        unrealized_pnl = (self.current_price - avg_buy_price) * current_position if current_position > 0 else 0

        return {
            'trading_pair': self.trading_pair,
            'current_price': self.current_price,
            'base_price': self.base_price,
            'total_invested': self.total_invested,
            'realized_profit': self.realized_profit,
            'unrealized_pnl': unrealized_pnl,
            'total_pnl': self.realized_profit + unrealized_pnl,
            'current_position': current_position,
            'avg_buy_price': avg_buy_price,
            'pending_orders': len(pending_orders),
            'filled_orders': len(filled_orders),
            'grid_levels': self.grid_levels,
            'grid_spacing': self.grid_spacing,
            'is_mock_mode': self.exchange is None,
            'dynamic_grid': self.dynamic_grid,
            'batch_build': self.batch_build,
            'volatility': self._calculate_volatility() if len(self.price_history) >= 10 else 0
        }

    def _calculate_volatility(self) -> float:
        """计算波动率"""
        if len(self.price_history) < 2:
            return 0

        returns = []
        for i in range(1, len(self.price_history)):
            ret = (self.price_history[i] - self.price_history[i-1]) / self.price_history[i-1]
            returns.append(ret)

        if not returns:
            return 0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return (variance ** 0.5) * (len(returns) ** 0.5)  # 年化波动率

    async def get_kline_data(
        self,
        timeframe: str = '1h',
        limit: int = 100,
        since: int = None
    ) -> List[List]:
        """获取K线数据"""
        if not self.exchange_api:
            # 模拟数据
            import random
            data = []
            base_time = int((datetime.now() - timedelta(hours=limit)).timestamp() * 1000)
            base_price = self.current_price or 50000

            for i in range(limit):
                timestamp = base_time + i * 3600000  # 1小时间隔
                open_price = base_price * (1 + random.uniform(-0.01, 0.01))
                high_price = open_price * (1 + random.uniform(0, 0.02))
                low_price = open_price * (1 - random.uniform(0, 0.02))
                close_price = open_price * (1 + random.uniform(-0.015, 0.015))
                volume = random.uniform(10, 100)

                data.append([timestamp, open_price, high_price, low_price, close_price, volume])
                base_price = close_price

            return data

        return await self.exchange_api.get_ohlcv(
            symbol=self.trading_pair,
            timeframe=timeframe,
            limit=limit,
            since=since
        )

    async def get_order_book_data(self, limit: int = 20) -> Dict:
        """获取深度数据"""
        if not self.exchange_api:
            # 模拟数据
            import random
            bids = []
            asks = []
            base_price = self.current_price or 50000

            for i in range(limit):
                bid_price = base_price * (1 - (i + 1) * 0.0001)
                bid_amount = random.uniform(0.1, 10)
                bids.append([bid_price, bid_amount])

                ask_price = base_price * (1 + (i + 1) * 0.0001)
                ask_amount = random.uniform(0.1, 10)
                asks.append([ask_price, ask_amount])

            return {
                'bids': bids,
                'asks': asks,
                'timestamp': int(datetime.now().timestamp() * 1000)
            }

        return await self.exchange_api.get_order_book(
            symbol=self.trading_pair,
            limit=limit
        )

    async def cancel_all_pending_orders(self) -> Dict:
        """取消所有待处理订单"""
        if not self.exchange_api:
            # 模拟模式 - 只更新本地状态
            cancelled_count = sum(1 for o in self.grid_orders if o['status'] == 'pending')
            for order in self.grid_orders:
                if order['status'] == 'pending':
                    order['status'] = 'cancelled'
            return {
                'cancelled': cancelled_count,
                'failed': 0,
                'message': '模拟模式：已取消所有本地订单'
            }

        # 实盘模式 - 调用交易所API
        try:
            results = await self.exchange_api.cancel_all_orders(self.trading_pair)
            cancelled_count = sum(1 for r in results if r.get('status') != 'failed')
            failed_count = sum(1 for r in results if r.get('status') == 'failed')

            # 更新本地订单状态
            for order in self.grid_orders:
                if order['status'] == 'pending':
                    order['status'] = 'cancelled'

            return {
                'cancelled': cancelled_count,
                'failed': failed_count,
                'message': f'已取消{cancelled_count}个订单，失败{failed_count}个'
            }
        except Exception as e:
            return {
                'cancelled': 0,
                'failed': 0,
                'message': f'取消订单失败: {str(e)}'
            }

    async def close_position(self) -> Dict:
        """平仓 - 取消所有订单并卖出所有持仓"""
        # 先取消所有订单
        cancel_result = await self.cancel_all_pending_orders()

        # 计算持仓
        buy_orders_filled = [o for o in self.grid_orders if o['type'] == 'buy' and o['status'] == 'filled']
        total_position = sum(o['amount'] for o in buy_orders_filled)

        if total_position <= 0:
            return {
                'message': '没有持仓需要平仓',
                'cancel_result': cancel_result,
                'position_closed': 0
            }

        # 卖出持仓
        try:
            if self.exchange_api:
                result = await self.exchange_api.place_order(
                    symbol=self.trading_pair,
                    side='sell',
                    order_type='market',
                    amount=total_position
                )

                # 更新状态
                self.total_invested = 0
                return {
                    'message': '平仓成功',
                    'cancel_result': cancel_result,
                    'position_closed': total_position,
                    'order_id': result.get('id')
                }
            else:
                # 模拟模式
                current_price = await self.get_current_price()
                total_value = total_position * current_price
                avg_buy_price = sum(o['price'] * o['amount'] for o in buy_orders_filled) / total_position
                profit = (current_price - avg_buy_price) * total_position
                self.realized_profit += profit
                self.total_invested = 0

                return {
                    'message': '模拟平仓成功',
                    'cancel_result': cancel_result,
                    'position_closed': total_position,
                    'price': current_price,
                    'profit': profit
                }
        except Exception as e:
            return {
                'message': f'平仓失败: {str(e)}',
                'cancel_result': cancel_result,
                'position_closed': 0
            }

    async def rebalance_grid(self, new_base_price: float = None) -> Dict:
        """重新平衡网格"""
        if new_base_price is None:
            new_base_price = await self.get_current_price()

        old_base_price = self.base_price
        self.base_price = new_base_price

        # 取消所有未完成订单
        await self.cancel_all_pending_orders()

        # 清空订单列表
        self.grid_orders = []

        # 重新初始化网格
        init_result = await self.initialize_grid(new_base_price)

        return {
            'message': '网格重新平衡完成',
            'old_base_price': old_base_price,
            'new_base_price': new_base_price,
            'grid_orders': len(self.grid_orders)
        }

    def get_trading_summary(self) -> Dict:
        """获取交易汇总"""
        buy_orders = [o for o in self.grid_orders if o['type'] == 'buy']
        sell_orders = [o for o in self.grid_orders if o['type'] == 'sell']

        buy_filled = [o for o in buy_orders if o['status'] == 'filled']
        sell_filled = [o for o in sell_orders if o['status'] == 'filled']

        total_buy_amount = sum(o['amount'] for o in buy_filled)
        total_buy_value = sum(o['price'] * o['amount'] for o in buy_filled)
        total_sell_amount = sum(o['amount'] for o in sell_filled)
        total_sell_value = sum(o['price'] * o['amount'] for o in sell_filled)

        avg_buy_price = total_buy_value / total_buy_amount if total_buy_amount > 0 else 0
        avg_sell_price = total_sell_value / total_sell_amount if total_sell_amount > 0 else 0

        # 计算平均利润率
        if buy_filled and sell_filled:
            min_trades = min(len(buy_filled), len(sell_filled))
            avg_profit_rate = (avg_sell_price - avg_buy_price) / avg_buy_price * 100
        else:
            avg_profit_rate = 0

        return {
            'total_trades': len(buy_filled) + len(sell_filled),
            'buy_trades': len(buy_filled),
            'sell_trades': len(sell_filled),
            'total_buy_amount': total_buy_amount,
            'total_buy_value': total_buy_value,
            'total_sell_amount': total_sell_amount,
            'total_sell_value': total_sell_value,
            'avg_buy_price': avg_buy_price,
            'avg_sell_price': avg_sell_price,
            'avg_profit_rate': avg_profit_rate,
            'realized_profit': self.realized_profit
        }

    def stop(self):
        """停止策略"""
        self.grid_orders = []


class MartingaleStrategy:
    """马丁格尔策略"""

    def __init__(
        self,
        exchange_id: str = None,
        api_key: str = None,
        api_secret: str = None,
        trading_pair: str = "BTC/USDT",
        initial_amount: float = 100,
        multiplier: float = 1.5,
        take_profit_percent: float = 0.05,
        stop_loss_percent: float = 0.10,
        max_consecutive_losses: int = 5,
        max_total_loss: float = 5000
    ):
        self.exchange_id = exchange_id or settings.EXCHANGE_ID
        self.trading_pair = trading_pair
        self.initial_amount = initial_amount
        self.multiplier = multiplier
        self.take_profit_percent = take_profit_percent
        self.stop_loss_percent = stop_loss_percent
        self.max_consecutive_losses = max_consecutive_losses
        self.max_total_loss = max_total_loss

        # 初始化交易所连接
        if api_key and api_secret:
            self.exchange_api = ExchangeAPI(
                exchange_id=self.exchange_id,
                api_key=api_key,
                api_secret=api_secret
            )
            self.mock_mode = False
        else:
            self.exchange_api = None
            self.mock_mode = True

        # 状态变量
        self.current_position = 0.0
        self.entry_price = 0.0
        self.current_price = 0.0
        self.consecutive_losses = 0
        self.last_trade_loss = 0.0
        self.total_loss = 0.0
        self.total_profit = 0.0
        self.total_invested = 0.0
        self.active_order = None

    async def get_current_price(self) -> float:
        """获取当前价格"""
        if self.exchange_api:
            try:
                ticker = await self.exchange_api.get_ticker(self.trading_pair)
                self.current_price = ticker['last']
            except Exception as e:
                print(f"获取价格失败: {e}")
        else:
            import random
            variation = random.uniform(-0.001, 0.001)
            self.current_price = self.current_price * (1 + variation) if self.current_price else 50000

        return self.current_price

    async def check_trading_conditions(self) -> Dict:
        """检查交易条件"""
        current_price = await self.get_current_price()

        if self.current_position == 0:
            # 无持仓，检查是否可以开仓
            if self.consecutive_losses < self.max_consecutive_losses and self.total_loss < self.max_total_loss:
                return {
                    'action': 'buy',
                    'reason': '无持仓，满足开仓条件'
                }
            else:
                return {
                    'action': 'hold',
                    'reason': '达到止损或最大连续亏损次数'
                }

        # 有持仓，检查止盈止损
        if self.entry_price > 0:
            pnl_percent = (current_price - self.entry_price) / self.entry_price

            # 止盈
            if pnl_percent >= self.take_profit_percent:
                return {
                    'action': 'sell',
                    'reason': f'达到止盈: {pnl_percent * 100:.2f}%'
                }

            # 止损
            elif pnl_percent <= -self.stop_loss_percent:
                return {
                    'action': 'sell',
                    'reason': f'触发止损: {pnl_percent * 100:.2f}%'
                }

        return {
            'action': 'hold',
            'reason': '持仓中，未达到止盈止损'
        }

    async def execute_trade(self, action: str) -> Dict:
        """执行交易"""
        current_price = await self.get_current_price()

        if action == 'buy':
            # 计算开仓金额
            if self.consecutive_losses > 0:
                amount_value = self.initial_amount * (self.multiplier ** self.consecutive_losses)
            else:
                amount_value = self.initial_amount

            # 计算数量
            amount = amount_value / current_price

            try:
                if self.exchange_api:
                    result = await self.exchange_api.place_order(
                        symbol=self.trading_pair,
                        side='buy',
                        order_type='market',
                        amount=amount
                    )
                    order_id = result['id']
                else:
                    order_id = f"mock_{datetime.now().timestamp()}"

                # 更新状态
                self.current_position = amount
                self.entry_price = current_price
                self.total_invested += amount_value
                self.active_order = {
                    'order_id': order_id,
                    'side': 'buy',
                    'price': current_price,
                    'amount': amount,
                    'value': amount_value,
                    'timestamp': datetime.now()
                }

                return {
                    'success': True,
                    'action': 'buy',
                    'order_id': order_id,
                    'price': current_price,
                    'amount': amount,
                    'value': amount_value
                }

            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }

        elif action == 'sell':
            if self.current_position <= 0:
                return {
                    'success': False,
                    'error': '没有持仓可卖出'
                }

            try:
                if self.exchange_api:
                    result = await self.exchange_api.place_order(
                        symbol=self.trading_pair,
                        side='sell',
                        order_type='market',
                        amount=self.current_position
                    )
                    order_id = result['id']
                else:
                    order_id = f"mock_{datetime.now().timestamp()}"

                # 计算盈亏
                pnl = (current_price - self.entry_price) * self.current_position

                if pnl >= 0:
                    self.total_profit += pnl
                    self.consecutive_losses = 0
                    self.last_trade_loss = 0
                else:
                    self.total_loss += abs(pnl)
                    self.consecutive_losses += 1
                    self.last_trade_loss = abs(pnl)

                # 记录交易
                sell_value = current_price * self.current_position

                # 重置持仓
                self.current_position = 0
                self.entry_price = 0

                return {
                    'success': True,
                    'action': 'sell',
                    'order_id': order_id,
                    'price': current_price,
                    'amount': sell_value / current_price,
                    'value': sell_value,
                    'pnl': pnl,
                    'consecutive_losses': self.consecutive_losses
                }

            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }

        return {
            'success': False,
            'error': '无效的操作'
        }

    async def run_cycle(self) -> Dict:
        """运行一个交易周期"""
        # 检查交易条件
        conditions = await self.check_trading_conditions()
        action = conditions['action']

        # 执行交易
        if action in ['buy', 'sell']:
            result = await self.execute_trade(action)
        else:
            result = {
                'success': True,
                'action': 'hold',
                'reason': conditions['reason']
            }

        return {
            'conditions': conditions,
            'execution': result,
            'status': self.get_strategy_status()
        }

    def get_strategy_status(self) -> Dict:
        """获取策略状态"""
        if self.current_position > 0 and self.entry_price > 0:
            pnl_percent = (self.current_price - self.entry_price) / self.entry_price
            unrealized_pnl = pnl_percent * self.entry_price * self.current_position
        else:
            pnl_percent = 0
            unrealized_pnl = 0

        return {
            'strategy': 'martingale',
            'trading_pair': self.trading_pair,
            'current_price': self.current_price,
            'current_position': self.current_position,
            'entry_price': self.entry_price,
            'unrealized_pnl': unrealized_pnl,
            'pnl_percent': pnl_percent * 100,
            'consecutive_losses': self.consecutive_losses,
            'total_loss': self.total_loss,
            'total_profit': self.total_profit,
            'total_invested': self.total_invested,
            'total_pnl': self.total_profit - self.total_loss,
            'take_profit_percent': self.take_profit_percent * 100,
            'stop_loss_percent': self.stop_loss_percent * 100,
            'is_mock_mode': self.mock_mode
        }

    def stop(self):
        """停止策略"""
        self.current_position = 0
        self.entry_price = 0
        self.active_order = None


class MeanReversionStrategy:
    """均值回归策略"""

    def __init__(
        self,
        exchange_id: str = None,
        api_key: str = None,
        api_secret: str = None,
        trading_pair: str = "BTC/USDT",
        lookback_period: int = 20,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5,
        position_size: float = 1000,
        max_position: float = 5000,
        use_bollinger: bool = True,
        bollinger_period: int = 20,
        bollinger_std: float = 2.0
    ):
        self.exchange_id = exchange_id or settings.EXCHANGE_ID
        self.trading_pair = trading_pair
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold  # 入场阈值（标准差的倍数）
        self.exit_threshold = exit_threshold  # 出场阈值（标准差的倍数）
        self.position_size = position_size
        self.max_position = max_position
        self.use_bollinger = use_bollinger
        self.bollinger_period = bollinger_period
        self.bollinger_std = bollinger_std

        # 初始化交易所连接
        if api_key and api_secret:
            self.exchange_api = ExchangeAPI(
                exchange_id=self.exchange_id,
                api_key=api_key,
                api_secret=api_secret
            )
            self.mock_mode = False
        else:
            self.exchange_api = None
            self.mock_mode = True

        # 状态变量
        self.current_price = 0.0
        self.current_position = 0.0
        self.entry_price = 0.0
        self.price_history = []
        self.total_profit = 0.0
        self.total_invested = 0.0
        self.total_trades = 0
        self.winning_trades = 0

    async def get_historical_prices(self) -> List[float]:
        """获取历史价格"""
        if self.exchange_api:
            try:
                kline_data = await self.exchange_api.get_ohlcv(
                    symbol=self.trading_pair,
                    timeframe='1h',
                    limit=self.lookback_period
                )
                return [kline[4] for kline in kline_data]  # close prices
            except Exception as e:
                print(f"获取历史价格失败: {e}")

        # 返回当前存储的价格历史
        return self.price_history[-self.lookback_period:] if len(self.price_history) >= self.lookback_period else []

    def calculate_zscore(self, price: float, prices: List[float]) -> float:
        """计算Z分数（价格偏离均值的程度）"""
        if len(prices) < 2:
            return 0.0

        mean_price = sum(prices) / len(prices)
        std_price = (sum((p - mean_price) ** 2 for p in prices) / len(prices)) ** 0.5

        if std_price == 0:
            return 0.0

        return (price - mean_price) / std_price

    def calculate_bollinger_bands(self, prices: List[float]) -> Dict:
        """计算布林带"""
        if len(prices) < self.bollinger_period:
            return None

        recent_prices = prices[-self.bollinger_period:]
        middle_band = sum(recent_prices) / len(recent_prices)
        std = (sum((p - middle_band) ** 2 for p in recent_prices) / len(recent_prices)) ** 0.5

        return {
            'middle': middle_band,
            'upper': middle_band + self.bollinger_std * std,
            'lower': middle_band - self.bollinger_std * std,
            'std': std
        }

    async def get_current_price(self) -> float:
        """获取当前价格"""
        if self.exchange_api:
            try:
                ticker = await self.exchange_api.get_ticker(self.trading_pair)
                self.current_price = ticker['last']
            except Exception as e:
                print(f"获取价格失败: {e}")
        else:
            import random
            variation = random.uniform(-0.001, 0.001)
            self.current_price = self.current_price * (1 + variation) if self.current_price else 50000

        # 更新价格历史
        self.price_history.append(self.current_price)
        if len(self.price_history) > 200:  # 最多保存200个价格点
            self.price_history.pop(0)

        return self.current_price

    async def analyze_market(self) -> Dict:
        """分析市场状况"""
        current_price = await self.get_current_price()
        historical_prices = await self.get_historical_prices()

        if len(historical_prices) < self.lookback_period:
            return {
                'ready': False,
                'reason': '价格历史数据不足'
            }

        if self.use_bollinger:
            bollinger = self.calculate_bollinger_bands(historical_prices)
            if not bollinger:
                return {
                    'ready': False,
                    'reason': '布林带计算失败'
                }

            # 判断价格位置
            if current_price > bollinger['upper']:
                position = 'upper_band'
                signal = 'sell'
                strength = (current_price - bollinger['upper']) / bollinger['std']
            elif current_price < bollinger['lower']:
                position = 'lower_band'
                signal = 'buy'
                strength = (bollinger['lower'] - current_price) / bollinger['std']
            else:
                position = 'middle'
                signal = 'hold'
                strength = 0

            return {
                'ready': True,
                'method': 'bollinger',
                'signal': signal,
                'position': position,
                'strength': strength,
                'current_price': current_price,
                'bollinger': bollinger
            }
        else:
            # 使用Z分数方法
            zscore = self.calculate_zscore(current_price, historical_prices)

            if zscore > self.entry_threshold:
                signal = 'sell'
                strength = zscore - self.entry_threshold
            elif zscore < -self.entry_threshold:
                signal = 'buy'
                strength = abs(zscore) - self.entry_threshold
            else:
                signal = 'hold'
                strength = 0

            return {
                'ready': True,
                'method': 'zscore',
                'signal': signal,
                'zscore': zscore,
                'strength': strength,
                'current_price': current_price
            }

    async def execute_trade(self, action: str, amount: float) -> Dict:
        """执行交易"""
        current_price = await self.get_current_price()

        if action == 'buy':
            try:
                if self.exchange_api:
                    result = await self.exchange_api.place_order(
                        symbol=self.trading_pair,
                        side='buy',
                        order_type='market',
                        amount=amount
                    )
                    order_id = result['id']
                else:
                    order_id = f"mock_{datetime.now().timestamp()}"

                value = current_price * amount
                self.current_position += amount
                self.total_invested += value

                if self.current_position == amount:  # 新建仓
                    self.entry_price = current_price

                return {
                    'success': True,
                    'action': 'buy',
                    'order_id': order_id,
                    'price': current_price,
                    'amount': amount,
                    'value': value
                }

            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }

        elif action == 'sell':
            if self.current_position <= 0:
                return {
                    'success': False,
                    'error': '没有持仓可卖出'
                }

            amount = min(amount, self.current_position)

            try:
                if self.exchange_api:
                    result = await self.exchange_api.place_order(
                        symbol=self.trading_pair,
                        side='sell',
                        order_type='market',
                        amount=amount
                    )
                    order_id = result['id']
                else:
                    order_id = f"mock_{datetime.now().timestamp()}"

                # 计算盈亏
                if self.entry_price > 0:
                    pnl = (current_price - self.entry_price) * amount
                    if pnl >= 0:
                        self.winning_trades += 1
                else:
                    pnl = 0

                self.total_profit += pnl
                sell_value = current_price * amount

                self.current_position -= amount
                self.total_trades += 1

                if self.current_position == 0:
                    self.entry_price = 0

                return {
                    'success': True,
                    'action': 'sell',
                    'order_id': order_id,
                    'price': current_price,
                    'amount': amount,
                    'value': sell_value,
                    'pnl': pnl
                }

            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }

        return {
            'success': False,
            'error': '无效的操作'
        }

    async def run_cycle(self) -> Dict:
        """运行一个交易周期"""
        # 分析市场
        analysis = await self.analyze_market()

        if not analysis.get('ready'):
            return {
                'analysis': analysis,
                'execution': {
                    'success': True,
                    'action': 'hold',
                    'reason': analysis.get('reason', '未准备好')
                },
                'status': self.get_strategy_status()
            }

        signal = analysis['signal']
        current_price = await self.get_current_price()

        # 检查是否需要调整持仓
        if signal == 'buy':
            # 价格低于均值，买入
            if self.current_position * current_price < self.max_position:
                amount = self.position_size / current_price
                result = await self.execute_trade('buy', amount)
            else:
                result = {
                    'success': True,
                    'action': 'hold',
                    'reason': '已达到最大持仓'
                }

        elif signal == 'sell':
            # 价格高于均值，卖出
            if self.current_position > 0:
                # 检查是否达到出场阈值
                historical_prices = await self.get_historical_prices()

                if self.use_bollinger:
                    bollinger = analysis['bollinger']
                    exit_price = bollinger['middle']
                else:
                    mean_price = sum(historical_prices) / len(historical_prices)
                    std = (sum((p - mean_price) ** 2 for p in historical_prices) / len(historical_prices)) ** 0.5
                    exit_price = mean_price - self.exit_threshold * std if self.current_position > 0 else mean_price + self.exit_threshold * std

                if (current_price >= exit_price and self.current_position > 0) or (current_price <= exit_price and self.current_position < 0):
                    amount = self.current_position
                    result = await self.execute_trade('sell', amount)
                else:
                    result = {
                        'success': True,
                        'action': 'hold',
                        'reason': '未达到出场阈值'
                    }
            else:
                result = {
                    'success': True,
                    'action': 'hold',
                    'reason': '没有持仓'
                }

        else:  # hold
            result = {
                'success': True,
                'action': 'hold',
                'reason': '价格在正常区间'
            }

        return {
            'analysis': analysis,
            'execution': result,
            'status': self.get_strategy_status()
        }

    def get_strategy_status(self) -> Dict:
        """获取策略状态"""
        if self.current_position > 0 and self.entry_price > 0:
            pnl_percent = (self.current_price - self.entry_price) / self.entry_price
            unrealized_pnl = pnl_percent * self.entry_price * self.current_position
        else:
            pnl_percent = 0
            unrealized_pnl = 0

        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        return {
            'strategy': 'mean_reversion',
            'trading_pair': self.trading_pair,
            'current_price': self.current_price,
            'current_position': self.current_position,
            'entry_price': self.entry_price,
            'position_value': self.current_position * self.current_price,
            'unrealized_pnl': unrealized_pnl,
            'pnl_percent': pnl_percent * 100,
            'total_profit': self.total_profit,
            'total_invested': self.total_invested,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': win_rate,
            'lookback_period': self.lookback_period,
            'use_bollinger': self.use_bollinger,
            'is_mock_mode': self.mock_mode
        }

    def stop(self):
        """停止策略"""
        self.current_position = 0
        self.entry_price = 0
        self.price_history = []
