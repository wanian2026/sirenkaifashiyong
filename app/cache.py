"""
缓存管理模块
支持Redis缓存和内存缓存
"""

from typing import Optional, Any, List, Callable
from datetime import timedelta
import json
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class CacheBackend:
    """缓存后端基类"""

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        raise NotImplementedError

    async def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存"""
        raise NotImplementedError

    async def delete(self, key: str):
        """删除缓存"""
        raise NotImplementedError

    async def clear(self):
        """清空缓存"""
        raise NotImplementedError


class MemoryCache(CacheBackend):
    """内存缓存"""

    def __init__(self):
        self.cache: dict = {}

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return self.cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存"""
        self.cache[key] = value

    async def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]

    async def clear(self):
        """清空缓存"""
        self.cache.clear()


class RedisCache(CacheBackend):
    """Redis缓存"""

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: str = None,
        decode_responses: bool = True
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.decode_responses = decode_responses
        self.redis_client = None

    async def _get_client(self):
        """获取Redis客户端"""
        if self.redis_client is None:
            try:
                import redis.asyncio as redis
                self.redis_client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=self.decode_responses
                )
                await self.redis_client.ping()
                logger.info(f"Redis连接成功: {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"Redis连接失败: {e}")
                self.redis_client = None

        return self.redis_client

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            client = await self._get_client()
            if client:
                value = await client.get(key)
                if value:
                    return json.loads(value)
        except Exception as e:
            logger.error(f"Redis获取失败: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存"""
        try:
            client = await self._get_client()
            if client:
                await client.set(key, json.dumps(value), ex=ttl)
        except Exception as e:
            logger.error(f"Redis设置失败: {e}")

    async def delete(self, key: str):
        """删除缓存"""
        try:
            client = await self._get_client()
            if client:
                await client.delete(key)
        except Exception as e:
            logger.error(f"Redis删除失败: {e}")

    async def clear(self):
        """清空缓存"""
        try:
            client = await self._get_client()
            if client:
                await client.flushdb()
        except Exception as e:
            logger.error(f"Redis清空失败: {e}")

    async def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配的键"""
        try:
            client = await self._get_client()
            if client:
                return await client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis获取键失败: {e}")
        return []


class CacheManager:
    """缓存管理器"""

    def __init__(self, backend: CacheBackend = None):
        self.backend = backend or MemoryCache()
        self.prefix = "crypto_bot:"

    def _make_key(self, key: str) -> str:
        """生成缓存键"""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        full_key = self._make_key(key)
        return await self.backend.get(full_key)

    async def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存"""
        full_key = self._make_key(key)
        await self.backend.set(full_key, value, ttl)

    async def delete(self, key: str):
        """删除缓存"""
        full_key = self._make_key(key)
        await self.backend.delete(full_key)

    async def clear(self):
        """清空缓存"""
        await self.backend.clear()

    async def get_or_set(
        self,
        key: str,
        fetch_func: callable,
        ttl: int = None
    ) -> Any:
        """获取或设置缓存"""
        value = await self.get(key)

        if value is None:
            value = await fetch_func()
            await self.set(key, value, ttl)

        return value

    async def delete_pattern(self, pattern: str):
        """删除匹配的缓存"""
        if isinstance(self.backend, RedisCache):
            full_pattern = self._make_key(pattern)
            keys = await self.backend.keys(full_pattern)
            for key in keys:
                await self.backend.delete(key)


# 全局缓存管理器
_global_cache: Optional[CacheManager] = None


def init_cache(redis_enabled: bool = False, **redis_config):
    """
    初始化全局缓存管理器

    Args:
        redis_enabled: 是否使用Redis
        **redis_config: Redis配置参数
    """
    global _global_cache

    if redis_enabled:
        backend = RedisCache(**redis_config)
        logger.info("使用Redis缓存")
    else:
        backend = MemoryCache()
        logger.info("使用内存缓存")

    _global_cache = CacheManager(backend)


def get_cache() -> CacheManager:
    """获取全局缓存管理器"""
    if _global_cache is None:
        # 默认使用内存缓存
        init_cache(redis_enabled=False)
    return _global_cache


def cached(ttl: int = None, key_prefix: str = None):
    """
    缓存装饰器

    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀

    Usage:
        @cached(ttl=60, key_prefix="ticker")
        async def get_ticker(symbol: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # 生成缓存键
            if key_prefix:
                cache_key = f"{key_prefix}:{args}:{kwargs}"
            else:
                cache_key = f"{func.__name__}:{args}:{kwargs}"

            # 尝试从缓存获取
            value = await cache.get(cache_key)

            if value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return value

            # 缓存未命中，调用函数
            logger.debug(f"缓存未命中: {cache_key}")
            result = await func(*args, **kwargs)

            # 存入缓存
            await cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


async def clear_cache(pattern: str = None):
    """
    清空缓存

    Args:
        pattern: 匹配模式（可选），如果为None则清空所有缓存
    """
    cache = get_cache()

    if pattern:
        await cache.delete_pattern(pattern)
        logger.info(f"清空缓存: {pattern}")
    else:
        await cache.clear()
        logger.info("清空所有缓存")



def cached(ttl: int = 300, key_prefix: str = ""):
    """
    缓存装饰器

    Args:
        ttl: 缓存时间（秒）
        key_prefix: 键前缀
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{str(args)}"
            if kwargs:
                cache_key += f":{str(sorted(kwargs.items()))}"

            # 尝试从缓存获取
            cache_manager = CacheManager()
            cached_value = await cache_manager.get(cache_key)

            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 设置缓存
            await cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


# 全局缓存管理器实例
cache_manager = CacheManager()


# 预定义的缓存键前缀
class CacheKey:
    """缓存键常量"""
    USER = "user"
    BOT = "bot"
    TRADE = "trade"
    ORDER = "order"
    MARKET_DATA = "market_data"
    TRADE_STATS = "trade_stats"
    BOT_STATUS = "bot_status"
    RISK_REPORT = "risk_report"
    BACKTEST_RESULT = "backtest_result"

    @staticmethod
    def user(user_id: int) -> str:
        """生成用户缓存键"""
        return f"{CacheKey.USER}:{user_id}"

    @staticmethod
    def bot(bot_id: int) -> str:
        """生成机器人缓存键"""
        return f"{CacheKey.BOT}:{bot_id}"

    @staticmethod
    def bot_status(bot_id: int) -> str:
        """生成机器人状态缓存键"""
        return f"{CacheKey.BOT_STATUS}:{bot_id}"

    @staticmethod
    def trade_stats(bot_id: int, days: int = 30) -> str:
        """生成交易统计缓存键"""
        return f"{CacheKey.TRADE_STATS}:{bot_id}:{days}days"

    @staticmethod
    def market_data(symbol: str) -> str:
        """生成市场数据缓存键"""
        return f"{CacheKey.MARKET_DATA}:{symbol}"
