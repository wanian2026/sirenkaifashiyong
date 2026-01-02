"""
交易所API管理模块
基于CCXT库提供统一的交易所数据访问接口
支持Redis缓存优化
"""

import ccxt
import asyncio
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
from app.config import settings
from app.cache import get_cache

logger = logging.getLogger(__name__)


class ExchangeManager:
    """交易所连接管理器"""

    _instances: Dict[str, ccxt.Exchange] = {}

    @classmethod
    def get_exchange(cls, exchange_id: str = None, api_key: str = None, api_secret: str = None) -> ccxt.Exchange:
        """
        获取交易所实例（单例模式）

        Args:
            exchange_id: 交易所ID (binance, okx, huobi等)
            api_key: API密钥（可选，用于私有API）
            api_secret: API密钥密钥（可选）

        Returns:
            ccxt.Exchange实例
        """
        exchange_id = exchange_id or settings.EXCHANGE_ID
        api_key = api_key or settings.API_KEY
        api_secret = api_secret or settings.API_SECRET

        # 生成实例键
        instance_key = f"{exchange_id}_{api_key[:8] if api_key else 'public'}"

        # 如果实例已存在，直接返回
        if instance_key in cls._instances:
            return cls._instances[instance_key]

        # 创建新实例
        try:
            # 获取交易所类
            exchange_class = getattr(ccxt, exchange_id)

            # 配置参数
            config = {
                'enableRateLimit': True,  # 启用速率限制
                'timeout': 30000,  # 超时时间30秒
                'options': {}
            }

            # 如果提供了API密钥，则配置
            if api_key and api_secret:
                config['apiKey'] = api_key
                config['secret'] = api_secret

                # 特定交易所的额外配置
                if exchange_id == 'binance':
                    config['options']['defaultType'] = 'spot'  # 现货交易
                elif exchange_id == 'okx':
                    config['options']['defaultType'] = 'swap'  # 合约交易

            # 创建交易所实例
            exchange = exchange_class(config)

            # 加载市场数据
            exchange.load_markets()

            # 缓存实例
            cls._instances[instance_key] = exchange

            logger.info(f"成功创建交易所实例: {exchange_id}")
            return exchange

        except AttributeError:
            logger.error(f"不支持的交易所: {exchange_id}")
            raise ValueError(f"不支持的交易所: {exchange_id}")
        except Exception as e:
            logger.error(f"创建交易所实例失败: {e}")
            raise

    @classmethod
    def close_all(cls):
        """关闭所有交易所连接"""
        for instance in cls._instances.values():
            try:
                instance.close()
            except Exception as e:
                logger.error(f"关闭交易所连接失败: {e}")
        cls._instances.clear()


class ExchangeAPI:
    """交易所数据API封装"""

    def __init__(self, exchange_id: str = None, api_key: str = None, api_secret: str = None):
        """
        初始化交易所API

        Args:
            exchange_id: 交易所ID
            api_key: API密钥
            api_secret: API密钥密钥
        """
        self.exchange = ExchangeManager.get_exchange(exchange_id, api_key, api_secret)
        self.exchange_id = exchange_id or settings.EXCHANGE_ID

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取行情信息（带缓存）

        Args:
            symbol: 交易对 (如 BTC/USDT)

        Returns:
            行情数据字典
        """
        cache = get_cache()
        cache_key = f"ticker:{symbol}"

        # 尝试从缓存获取
        cached_data = await cache.get(cache_key)
        if cached_data:
            logger.debug(f"命中缓存: {cache_key}")
            return cached_data

        try:
            ticker = await asyncio.to_thread(self.exchange.fetch_ticker, symbol)

            result = {
                "symbol": symbol,
                "last": ticker.get('last'),
                "high": ticker.get('high'),
                "low": ticker.get('low'),
                "bid": ticker.get('bid'),
                "ask": ticker.get('ask'),
                "volume": ticker.get('baseVolume'),
                "quoteVolume": ticker.get('quoteVolume'),
                "change": ticker.get('change'),
                "percentage": ticker.get('percentage'),
                "timestamp": ticker.get('timestamp')
            }

            # 存入缓存（5秒）
            await cache.set(cache_key, result, ttl=5)
            logger.debug(f"存入缓存: {cache_key}")

            return result
        except Exception as e:
            logger.error(f"获取行情失败 [{symbol}]: {e}")
            raise

    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        获取订单簿深度数据（带缓存）

        Args:
            symbol: 交易对
            limit: 深度数量

        Returns:
            订单簿数据
        """
        cache = get_cache()
        cache_key = f"orderbook:{symbol}:{limit}"

        # 尝试从缓存获取（缓存时间2秒）
        cached_data = await cache.get(cache_key)
        if cached_data:
            logger.debug(f"命中缓存: {cache_key}")
            return cached_data

        try:
            orderbook = await asyncio.to_thread(self.exchange.fetch_order_book, symbol, limit)

            bids = orderbook.get('bids', [])[:limit]
            asks = orderbook.get('asks', [])[:limit]

            # 计算累计量
            total_bid_volume = sum([bid[1] for bid in bids])
            total_ask_volume = sum([ask[1] for ask in asks])

            result = {
                "symbol": symbol,
                "bids": [
                    {
                        "price": bid[0],
                        "amount": bid[1],
                        "total": sum([b[1] for b in bids[:i+1]]),
                        "total_percent": (sum([b[1] for b in bids[:i+1]]) / total_bid_volume * 100) if total_bid_volume > 0 else 0
                    }
                    for i, bid in enumerate(bids)
                ],
                "asks": [
                    {
                        "price": ask[0],
                        "amount": ask[1],
                        "total": sum([a[1] for a in asks[:i+1]]),
                        "total_percent": (sum([a[1] for a in asks[:i+1]]) / total_ask_volume * 100) if total_ask_volume > 0 else 0
                    }
                    for i, ask in enumerate(asks)
                ],
                "timestamp": orderbook.get('timestamp', int(datetime.now().timestamp() * 1000))
            }

            # 存入缓存（2秒）
            await cache.set(cache_key, result, ttl=2)
            logger.debug(f"存入缓存: {cache_key}")

            return result
        except Exception as e:
            logger.error(f"获取订单簿失败 [{symbol}]: {e}")
            raise

    async def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[List]:
        """
        获取K线数据（带缓存）

        Args:
            symbol: 交易对
            timeframe: 时间周期 (1m, 5m, 15m, 1h, 4h, 1d)
            limit: K线数量

        Returns:
            K线数据列表 [[timestamp, open, high, low, close, volume], ...]
        """
        cache = get_cache()
        cache_key = f"ohlcv:{symbol}:{timeframe}:{limit}"

        # 根据时间周期决定缓存时间
        timeframe_ttl = {
            '1m': 10,
            '5m': 30,
            '15m': 60,
            '1h': 120,
            '4h': 300,
            '1d': 600
        }
        ttl = timeframe_ttl.get(timeframe, 60)

        # 尝试从缓存获取
        cached_data = await cache.get(cache_key)
        if cached_data:
            logger.debug(f"命中缓存: {cache_key}")
            return cached_data

        try:
            ohlcv = await asyncio.to_thread(self.exchange.fetch_ohlcv, symbol, timeframe, limit=limit)

            # 存入缓存
            await cache.set(cache_key, ohlcv, ttl=ttl)
            logger.debug(f"存入缓存: {cache_key}")

            return ohlcv
        except Exception as e:
            logger.error(f"获取K线数据失败 [{symbol}, {timeframe}]: {e}")
            raise

    async def get_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """
        获取成交记录

        Args:
            symbol: 交易对
            limit: 成交记录数量

        Returns:
            成交记录列表
        """
        try:
            trades = await asyncio.to_thread(self.exchange.fetch_trades, symbol, limit=limit)

            formatted_trades = []
            for trade in trades:
                formatted_trades.append({
                    "id": str(trade.get('id')),
                    "timestamp": trade.get('timestamp'),
                    "datetime": trade.get('datetime'),
                    "symbol": symbol,
                    "order": trade.get('order'),
                    "type": trade.get('type'),
                    "side": trade.get('side'),
                    "price": trade.get('price'),
                    "amount": trade.get('amount'),
                    "cost": trade.get('cost'),
                    "fee": trade.get('fee')
                })

            return formatted_trades
        except Exception as e:
            logger.error(f"获取成交记录失败 [{symbol}]: {e}")
            raise

    async def get_pairs(self) -> List[Dict]:
        """
        获取支持的交易对列表（带缓存）

        Returns:
            交易对列表
        """
        cache = get_cache()
        cache_key = f"pairs:{self.exchange_id}"

        # 尝试从缓存获取（缓存10分钟）
        cached_data = await cache.get(cache_key)
        if cached_data:
            logger.debug(f"命中缓存: {cache_key}")
            return cached_data

        try:
            markets = await asyncio.to_thread(lambda: self.exchange.markets)

            # 只返回现货交易对
            pairs = []
            for symbol, market in markets.items():
                if market.get('type') == 'spot' and market.get('active', True):
                    pairs.append({
                        "symbol": symbol,
                        "name": market.get('name'),
                        "base": market.get('base'),
                        "quote": market.get('quote')
                    })

            # 限制返回数量，避免数据过大
            result = pairs[:50]

            # 存入缓存（10分钟）
            await cache.set(cache_key, result, ttl=600)
            logger.debug(f"存入缓存: {cache_key}")

            return result
        except Exception as e:
            logger.error(f"获取交易对列表失败: {e}")
            raise

    async def get_24h_stats(self, symbol: str) -> Dict[str, Any]:
        """
        获取24小时统计数据

        Args:
            symbol: 交易对

        Returns:
            24小时统计数据
        """
        try:
            ticker = await self.get_ticker(symbol)

            return {
                "symbol": symbol,
                "open": ticker.get('last') - ticker.get('change', 0),
                "high": ticker.get('high'),
                "low": ticker.get('low'),
                "close": ticker.get('last'),
                "volume": ticker.get('volume'),
                "quoteVolume": ticker.get('quoteVolume'),
                "change": ticker.get('change'),
                "changePercent": ticker.get('percentage'),
                "timestamp": ticker.get('timestamp')
            }
        except Exception as e:
            logger.error(f"获取24小时统计数据失败 [{symbol}]: {e}")
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """
        测试交易所连接

        Returns:
            连接状态信息
        """
        try:
            # 尝试获取交易对列表
            markets = await asyncio.to_thread(lambda: self.exchange.markets)

            return {
                "success": True,
                "exchange": self.exchange_id,
                "has_markets": len(markets) > 0,
                "market_count": len(markets),
                "message": "连接成功"
            }
        except Exception as e:
            logger.error(f"测试连接失败: {e}")
            return {
                "success": False,
                "exchange": self.exchange_id,
                "error": str(e),
                "message": "连接失败"
            }


# 全局实例
_exchange_api: Optional[ExchangeAPI] = None


def get_exchange_api() -> ExchangeAPI:
    """
    获取全局交易所API实例

    Returns:
        ExchangeAPI实例
    """
    global _exchange_api
    if _exchange_api is None:
        _exchange_api = ExchangeAPI()
    return _exchange_api
