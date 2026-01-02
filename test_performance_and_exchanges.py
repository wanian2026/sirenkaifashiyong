"""
性能优化和多交易所功能测试脚本
"""

import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import time

from app.database import Base, get_db
from app.models import User, TradingBot, GridOrder, Trade
from app.cache import MemoryCache, CacheManager, CacheKey, get_cache, init_cache
from app.db_indexes import IndexManager, create_all_database_indexes, analyze_database_indexes
from app.exchange_manager import ExchangeManager
from app.encryption import EncryptionManager


class TestDatabaseOptimization:
    """数据库优化测试"""

    @pytest.fixture
    def db_session(self):
        """创建测试数据库会话"""
        # 使用内存SQLite数据库
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    def test_create_indexes(self):
        """测试创建数据库索引"""
        print("\n=== 测试创建数据库索引 ===")

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)

        index_manager = IndexManager(engine)

        # 创建所有索引
        result = index_manager.create_all_indexes()

        print(f"成功创建索引: {len(result['success'])}")
        print(f"失败的索引: {len(result['failed'])}")

        assert len(result['success']) > 0, "应该成功创建至少一个索引"
        print("✓ 索引创建测试通过")

    def test_index_analysis(self):
        """测试索引分析"""
        print("\n=== 测试索引分析 ===")

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)

        # 创建索引
        index_manager = IndexManager(engine)
        index_manager.create_all_indexes()

        # 分析索引
        analysis = index_manager.analyze_index_usage()

        print(f"分析的表数量: {len(analysis)}")

        # 验证某些表有索引
        assert 'trading_bots' in analysis
        assert 'grid_orders' in analysis
        assert 'trades' in analysis

        print("✓ 索引分析测试通过")


class TestCachePerformance:
    """缓存性能测试"""

    def test_memory_cache(self):
        """测试内存缓存"""
        print("\n=== 测试内存缓存 ===")

        cache = MemoryCache()

        # 测试设置和获取
        asyncio.run(cache.set("test_key", {"data": "test_value"}))
        value = asyncio.run(cache.get("test_key"))

        assert value == {"data": "test_value"}, "缓存值应该匹配"
        print("✓ 内存缓存测试通过")

    def test_cache_manager(self):
        """测试缓存管理器"""
        print("\n=== 测试缓存管理器 ===")

        # 初始化缓存
        init_cache(redis_enabled=False)
        cache = get_cache()

        # 测试设置和获取
        test_data = {
            "user_id": 1,
            "username": "test_user"
        }

        asyncio.run(cache.set("user:1", test_data))
        cached_data = asyncio.run(cache.get("user:1"))

        assert cached_data == test_data, "缓存数据应该匹配"

        # 测试删除
        asyncio.run(cache.delete("user:1"))
        deleted_data = asyncio.run(cache.get("user:1"))

        assert deleted_data is None, "删除后应该为None"

        print("✓ 缓存管理器测试通过")

    def test_cache_keys(self):
        """测试缓存键生成"""
        print("\n=== 测试缓存键生成 ===")

        # 测试用户键
        user_key = CacheKey.user(123)
        assert user_key == "user:123", "用户键格式应该正确"

        # 测试机器人键
        bot_key = CacheKey.bot(456)
        assert bot_key == "bot:456", "机器人键格式应该正确"

        # 测试交易统计键
        stats_key = CacheKey.trade_stats(456, 30)
        assert stats_key == "trade_stats:456:30days", "交易统计键格式应该正确"

        print("✓ 缓存键生成测试通过")

    def test_cache_performance(self):
        """测试缓存性能"""
        print("\n=== 测试缓存性能 ===")

        # 初始化缓存
        init_cache(redis_enabled=False)
        cache = get_cache()

        # 测试数据
        test_data = {"value": "x" * 1000}  # 1KB数据

        # 测试写入性能
        start_time = time.time()
        for i in range(1000):
            asyncio.run(cache.set(f"key_{i}", test_data))
        write_time = time.time() - start_time

        print(f"写入1000条数据耗时: {write_time:.3f}秒")
        assert write_time < 1.0, "写入1000条数据应该在1秒内完成"

        # 测试读取性能
        start_time = time.time()
        for i in range(1000):
            asyncio.run(cache.get(f"key_{i}"))
        read_time = time.time() - start_time

        print(f"读取1000条数据耗时: {read_time:.3f}秒")
        assert read_time < 1.0, "读取1000条数据应该在1秒内完成"

        print("✓ 缓存性能测试通过")


class TestExchangeManager:
    """交易所管理器测试"""

    def test_supported_exchanges(self):
        """测试支持的交易所列表"""
        print("\n=== 测试支持的交易所列表 ===")

        exchanges = ExchangeManager.get_supported_exchanges()

        print(f"支持的交易所数量: {len(exchanges)}")
        print(f"支持的交易所: {list(exchanges.keys())}")

        assert 'binance' in exchanges, "应该支持币安"
        assert 'okx' in exchanges, "应该支持欧易"
        assert 'huobi' in exchanges, "应该支持火币"

        print("✓ 支持的交易所列表测试通过")

    def test_create_exchange_instance(self):
        """测试创建交易所实例"""
        print("\n=== 测试创建交易所实例 ===")

        # 测试创建币安实例（使用测试密钥）
        exchange = ExchangeManager.create_exchange_instance(
            exchange_name="binance",
            api_key="test_key",
            api_secret="test_secret",
            is_testnet=True
        )

        assert exchange is not None, "应该成功创建交易所实例"
        assert exchange.id == "binance", "交易所ID应该匹配"

        print("✓ 创建交易所实例测试通过")

    def test_create_exchange_invalid(self):
        """测试创建不支持的交易所"""
        print("\n=== 测试创建不支持的交易所 ===")

        exchange = ExchangeManager.create_exchange_instance(
            exchange_name="invalid_exchange",
            api_key="test_key",
            api_secret="test_secret"
        )

        assert exchange is None, "不支持的交易所应该返回None"

        print("✓ 创建不支持的交易所测试通过")


class TestEncryption:
    """加密功能测试"""

    def test_encryption_decryption(self):
        """测试加密和解密"""
        print("\n=== 测试加密和解密 ===")

        encryption_manager = EncryptionManager()

        # 测试字符串加密
        original_text = "my_api_key_123456"
        encrypted = encryption_manager.encrypt(original_text)
        decrypted = encryption_manager.decrypt(encrypted)

        assert decrypted == original_text, "解密后应该与原文一致"
        assert encrypted != original_text, "加密后应该与原文不同"

        print("✓ 加密和解密测试通过")

    def test_dictionary_encryption(self):
        """测试字典加密"""
        print("\n=== 测试字典加密 ===")

        encryption_manager = EncryptionManager()

        # 测试字典加密
        original_dict = {
            "api_key": "my_api_key",
            "api_secret": "my_api_secret",
            "extra_field": "test_value"
        }

        # 加密指定字段
        encrypted_dict = encryption_manager.encrypt_dict(original_dict, fields=["api_key", "api_secret"])
        decrypted_dict = encryption_manager.decrypt_dict(encrypted_dict, fields=["api_key", "api_secret"])

        assert decrypted_dict == original_dict, "解密后应该与原文一致"
        assert encrypted_dict["api_key"] != original_dict["api_key"], "加密后应该与原文不同"
        assert encrypted_dict["api_secret"] != original_dict["api_secret"], "加密后应该与原文不同"
        assert encrypted_dict["extra_field"] == original_dict["extra_field"], "未加密字段应该保持不变"

        print("✓ 字典加密测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始运行性能优化和多交易所功能测试")
    print("=" * 60)

    # 数据库优化测试
    db_test = TestDatabaseOptimization()
    try:
        db_test.test_create_indexes()
        db_test.test_index_analysis()
        print("\n✅ 数据库优化测试全部通过")
    except Exception as e:
        print(f"\n❌ 数据库优化测试失败: {e}")

    # 缓存性能测试
    cache_test = TestCachePerformance()
    try:
        cache_test.test_memory_cache()
        cache_test.test_cache_manager()
        cache_test.test_cache_keys()
        cache_test.test_cache_performance()
        print("\n✅ 缓存性能测试全部通过")
    except Exception as e:
        print(f"\n❌ 缓存性能测试失败: {e}")

    # 交易所管理器测试
    exchange_test = TestExchangeManager()
    try:
        exchange_test.test_supported_exchanges()
        exchange_test.test_create_exchange_instance()
        exchange_test.test_create_exchange_invalid()
        print("\n✅ 交易所管理器测试全部通过")
    except Exception as e:
        print(f"\n❌ 交易所管理器测试失败: {e}")

    # 加密功能测试
    encryption_test = TestEncryption()
    try:
        encryption_test.test_encryption_decryption()
        encryption_test.test_dictionary_encryption()
        print("\n✅ 加密功能测试全部通过")
    except Exception as e:
        print(f"\n❌ 加密功能测试失败: {e}")

    print("\n" + "=" * 60)
    print("测试运行完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
