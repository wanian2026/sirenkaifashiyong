"""
交易所API封装模块
提供统一的交易所接口，支持多个交易所
"""

import ccxt
import asyncio
from typing import Dict, List, Optional, Literal
from decimal import Decimal
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ExchangeAPI:
    """交易所API统一接口"""

    def __init__(
        self,
        exchange_id: str,
        api_key: str,
        api_secret: str,
        passphrase: str = None,
        sandbox: bool = False
    ):
        """
        初始化交易所连接

        Args:
            exchange_id: 交易所ID（如 'binance', 'okx'）
            api_key: API密钥
            api_secret: API密钥
            passphrase: 交易密码（部分交易所需要）
            sandbox: 是否使用测试环境
        """
        self.exchange_id = exchange_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase

        # 初始化交易所实例
        exchange_class = getattr(ccxt, exchange_id)
        config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        }

        if passphrase:
            config['password'] = passphrase

        if sandbox:
            config['sandboxMode'] = True

        self.exchange = exchange_class(config)
        logger.info(f"交易所 {exchange_id} 初始化成功")

    async def place_order(
        self,
        symbol: str,
        side: Literal['buy', 'sell'],
        order_type: Literal['market', 'limit', 'stop', 'stop_limit'],
        amount: float,
        price: float = None,
        stop_price: float = None,
        params: Dict = None
    ) -> Dict:
        """
        下单

        Args:
            symbol: 交易对（如 'BTC/USDT'）
            side: 买卖方向（'buy' 或 'sell'）
            order_type: 订单类型（'market', 'limit', 'stop', 'stop_limit'）
            amount: 数量
            price: 价格（限价单必填）
            stop_price: 止损价格（止损单必填）
            params: 额外参数

        Returns:
            订单信息
        """
        params = params or {}

        try:
            # 限价单
            if order_type == 'limit':
                result = await asyncio.to_thread(
                    self.exchange.create_order,
                    symbol,
                    'limit',
                    side,
                    amount,
                    price,
                    params
                )

            # 市价单
            elif order_type == 'market':
                result = await asyncio.to_thread(
                    self.exchange.create_order,
                    symbol,
                    'market',
                    side,
                    amount,
                    None,
                    params
                )

            # 止损单
            elif order_type == 'stop':
                if not stop_price:
                    raise ValueError("止损单需要 stop_price 参数")
                params['stopPrice'] = stop_price
                result = await asyncio.to_thread(
                    self.exchange.create_order,
                    symbol,
                    'stop',
                    side,
                    amount,
                    price,
                    params
                )

            # 止损限价单
            elif order_type == 'stop_limit':
                if not stop_price or not price:
                    raise ValueError("止损限价单需要 stop_price 和 price 参数")
                params['stopPrice'] = stop_price
                result = await asyncio.to_thread(
                    self.exchange.create_order,
                    symbol,
                    'stop_limit',
                    side,
                    amount,
                    price,
                    params
                )

            else:
                raise ValueError(f"不支持的订单类型: {order_type}")

            logger.info(f"下单成功: {result['id']}, {symbol}, {side}, {order_type}, {amount}")
            return result

        except Exception as e:
            logger.error(f"下单失败: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """
        撤单

        Args:
            order_id: 订单ID
            symbol: 交易对

        Returns:
            撤单结果
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.cancel_order,
                order_id,
                symbol
            )
            logger.info(f"撤单成功: {order_id}")
            return result
        except Exception as e:
            logger.error(f"撤单失败: {e}")
            raise

    async def cancel_all_orders(self, symbol: str) -> List[Dict]:
        """
        撤销所有订单

        Args:
            symbol: 交易对

        Returns:
            撤单结果列表
        """
        try:
            # 获取所有未完成订单
            orders = await self.get_open_orders(symbol)

            results = []
            for order in orders:
                try:
                    result = await self.cancel_order(order['id'], symbol)
                    results.append(result)
                except Exception as e:
                    logger.error(f"撤销订单 {order['id']} 失败: {e}")
                    results.append({'id': order['id'], 'status': 'failed', 'error': str(e)})

            return results
        except Exception as e:
            logger.error(f"撤销所有订单失败: {e}")
            raise

    async def get_order(self, order_id: str, symbol: str) -> Dict:
        """
        查询订单

        Args:
            order_id: 订单ID
            symbol: 交易对

        Returns:
            订单信息
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_order,
                order_id,
                symbol
            )
            return result
        except Exception as e:
            logger.error(f"查询订单失败: {e}")
            raise

    async def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """
        获取未完成订单

        Args:
            symbol: 交易对（可选）

        Returns:
            订单列表
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_open_orders,
                symbol
            )
            return result
        except Exception as e:
            logger.error(f"获取未完成订单失败: {e}")
            raise

    async def get_closed_orders(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """
        获取已完成订单

        Args:
            symbol: 交易对（可选）
            limit: 数量限制

        Returns:
            订单列表
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_closed_orders,
                symbol,
                limit=limit
            )
            return result
        except Exception as e:
            logger.error(f"获取已完成订单失败: {e}")
            raise

    async def get_ticker(self, symbol: str) -> Dict:
        """
        获取行情信息

        Args:
            symbol: 交易对

        Returns:
            行情信息（包含最新价、24h涨跌幅等）
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_ticker,
                symbol
            )
            return result
        except Exception as e:
            logger.error(f"获取行情失败: {e}")
            raise

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100,
        since: int = None
    ) -> List[List]:
        """
        获取K线数据

        Args:
            symbol: 交易对
            timeframe: 时间周期（1m, 5m, 15m, 1h, 4h, 1d等）
            limit: 数量限制
            since: 开始时间戳（毫秒）

        Returns:
            K线数据列表 [[timestamp, open, high, low, close, volume], ...]
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_ohlcv,
                symbol,
                timeframe,
                since=since,
                limit=limit
            )
            return result
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            raise

    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """
        获取深度数据

        Args:
            symbol: 交易对
            limit: 深度数量

        Returns:
            深度数据 {bids: [[price, amount], ...], asks: [[price, amount], ...]}
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_order_book,
                symbol,
                limit
            )
            return result
        except Exception as e:
            logger.error(f"获取深度数据失败: {e}")
            raise

    async def get_balance(self) -> Dict:
        """
        获取账户余额

        Returns:
            余额信息
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_balance
            )
            return result
        except Exception as e:
            logger.error(f"获取账户余额失败: {e}")
            raise

    async def get_trades(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """
        获取成交记录

        Args:
            symbol: 交易对（可选）
            limit: 数量限制

        Returns:
            成交记录列表
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_my_trades,
                symbol,
                limit=limit
            )
            return result
        except Exception as e:
            logger.error(f"获取成交记录失败: {e}")
            raise

    async def get_current_price(self, symbol: str) -> float:
        """
        获取当前价格

        Args:
            symbol: 交易对

        Returns:
            当前价格
        """
        try:
            ticker = await self.get_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"获取当前价格失败: {e}")
            raise

    async def create_oco_order(
        self,
        symbol: str,
        side: Literal['buy', 'sell'],
        amount: float,
        price: float,
        stop_loss_price: float,
        take_profit_price: float,
        params: Dict = None
    ) -> Dict:
        """
        创建OCO订单（止盈止损同时设置）

        Args:
            symbol: 交易对
            side: 买卖方向
            amount: 数量
            price: 价格
            stop_loss_price: 止损价格
            take_profit_price: 止盈价格
            params: 额外参数

        Returns:
            订单信息
        """
        params = params or {}

        try:
            # OCO订单参数
            params.update({
                'stopLoss': {'price': stop_loss_price},
                'takeProfit': {'price': take_profit_price}
            })

            result = await asyncio.to_thread(
                self.exchange.create_order,
                symbol,
                'limit',
                side,
                amount,
                price,
                params
            )

            logger.info(f"OCO下单成功: {result['id']}")
            return result

        except Exception as e:
            logger.error(f"OCO下单失败: {e}")
            raise

    def stop(self):
        """停止交易所连接"""
        try:
            if hasattr(self.exchange, 'close'):
                self.exchange.close()
            logger.info("交易所连接已关闭")
        except Exception as e:
            logger.error(f"关闭交易所连接失败: {e}")

    async def get_order(self, order_id: str, symbol: str) -> Dict:
        """
        查询订单

        Args:
            order_id: 订单ID
            symbol: 交易对

        Returns:
            订单信息
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_order,
                order_id,
                symbol
            )
            return result
        except Exception as e:
            logger.error(f"查询订单失败: {e}")
            raise

    async def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """
        查询所有未完成订单

        Args:
            symbol: 交易对（可选，不指定则查询所有）

        Returns:
            订单列表
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_open_orders,
                symbol
            )
            return result
        except Exception as e:
            logger.error(f"查询未完成订单失败: {e}")
            raise

    async def get_balance(self) -> Dict:
        """
        查询账户余额

        Returns:
            余额信息
        """
        try:
            result = await asyncio.to_thread(self.exchange.fetch_balance)
            return result
        except Exception as e:
            logger.error(f"查询余额失败: {e}")
            raise

    async def get_ticker(self, symbol: str) -> Dict:
        """
        查询行情

        Args:
            symbol: 交易对

        Returns:
            行情信息
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_ticker,
                symbol
            )
            return result
        except Exception as e:
            logger.error(f"查询行情失败: {e}")
            raise

    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """
        查询深度数据

        Args:
            symbol: 交易对
            limit: 深度档位

        Returns:
            深度数据
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_order_book,
                symbol,
                limit
            )
            return result
        except Exception as e:
            logger.error(f"查询深度数据失败: {e}")
            raise

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100,
        since: int = None
    ) -> List[List]:
        """
        查询K线数据

        Args:
            symbol: 交易对
            timeframe: 时间周期（1m, 5m, 15m, 1h, 4h, 1d等）
            limit: 数量限制
            since: 起始时间戳

        Returns:
            K线数据 [[timestamp, open, high, low, close, volume], ...]
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_ohlcv,
                symbol,
                timeframe,
                since,
                limit
            )
            return result
        except Exception as e:
            logger.error(f"查询K线数据失败: {e}")
            raise

    async def get_trades(
        self,
        symbol: str,
        limit: int = 100,
        since: int = None
    ) -> List[Dict]:
        """
        查询交易历史

        Args:
            symbol: 交易对
            limit: 数量限制
            since: 起始时间戳

        Returns:
            交易记录列表
        """
        try:
            result = await asyncio.to_thread(
                self.exchange.fetch_my_trades,
                symbol,
                since,
                limit
            )
            return result
        except Exception as e:
            logger.error(f"查询交易历史失败: {e}")
            raise

    async def test_connection(self) -> bool:
        """
        测试连接

        Returns:
            是否连接成功
        """
        try:
            await asyncio.to_thread(self.exchange.fetch_time)
            logger.info("交易所连接测试成功")
            return True
        except Exception as e:
            logger.error(f"交易所连接测试失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        if hasattr(self.exchange, 'close'):
            self.exchange.close()
        logger.info("交易所连接已关闭")
