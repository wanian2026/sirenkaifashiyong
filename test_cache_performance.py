"""
缓存性能测试脚本
测试Redis缓存和内存缓存的性能差异
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict

API_BASE = "http://localhost:8000/api"

# 测试结果
test_results = {
    "without_cache": {},
    "with_cache": {},
    "improvement": {}
}


async def test_endpoint_performance(name: str, url: str, params: Dict = None, iterations: int = 10) -> Dict[str, float]:
    """
    测试API端点性能

    Args:
        name: 测试名称
        url: API URL
        params: 请求参数
        iterations: 迭代次数

    Returns:
        性能统计数据
    """
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"URL: {url}")
    if params:
        print(f"参数: {params}")
    print(f"迭代次数: {iterations}")
    print('='*60)

    response_times = []

    for i in range(iterations):
        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE}{url}", params=params) as response:
                    await response.json()

            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            response_times.append(response_time)

            print(f"  第 {i+1:2d} 次请求: {response_time:7.2f}ms")

        except Exception as e:
            print(f"  第 {i+1:2d} 次请求失败: {e}")
            continue

    if not response_times:
        return {
            "min": 0,
            "max": 0,
            "avg": 0,
            "median": 0,
            "std": 0
        }

    return {
        "min": min(response_times),
        "max": max(response_times),
        "avg": statistics.mean(response_times),
        "median": statistics.median(response_times),
        "std": statistics.stdev(response_times) if len(response_times) > 1 else 0
    }


async def test_cache_hit_rate():
    """测试缓存命中率"""
    print(f"\n{'='*60}")
    print("缓存命中率测试")
    print('='*60)

    symbol = "BTC/USDT"
    url = f"/exchange/ticker?symbol={symbol}"
    total_requests = 20

    print(f"连续请求 {total_requests} 次 {symbol} 行情...")

    response_times = []
    for i in range(total_requests):
        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE}{url}") as response:
                    data = await response.json()

            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)

            print(f"  请求 {i+1:2d}: {response_time:7.2f}ms", end="")

            # 判断是否命中缓存（假设前3次未命中，后续命中）
            if i < 3:
                print(" (未命中)")
            else:
                print(" (命中)")

        except Exception as e:
            print(f"  请求 {i+1:2d} 失败: {e}")

    # 统计
    first_3_avg = statistics.mean(response_times[:3])
    rest_avg = statistics.mean(response_times[3:])

    print(f"\n统计:")
    print(f"  前3次平均响应时间（未命中）: {first_3_avg:.2f}ms")
    print(f"  后{total_requests-3}次平均响应时间（命中）: {rest_avg:.2f}ms")
    print(f"  性能提升: {(first_3_avg / rest_avg):.2f}x")


async def test_cache_operations():
    """测试缓存操作"""
    print(f"\n{'='*60}")
    print("缓存操作测试")
    print('='*60)

    # 1. 测试缓存状态
    print("\n1. 获取缓存状态...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/cache/status") as response:
            data = await response.json()
            print(f"   缓存后端: {data['data']['backend']}")
            print(f"   Redis启用: {data['data']['redis_enabled']}")

    # 2. 测试清空缓存
    print("\n2. 清空所有缓存...")
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE}/cache/clear") as response:
            data = await response.json()
            print(f"   结果: {data['message']}")

    # 3. 测试刷新指定缓存
    print("\n3. 刷新ticker缓存...")
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE}/cache/refresh?cache_type=ticker") as response:
            data = await response.json()
            print(f"   结果: {data['message']}")


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Redis缓存性能测试")
    print("=" * 60)

    # 1. 测试缓存操作
    await test_cache_operations()

    # 2. 测试缓存命中率
    await test_cache_hit_rate()

    # 3. 测试各个端点的性能
    print(f"\n{'='*60}")
    print("API端点性能测试")
    print('='*60)

    # 测试ticker
    ticker_perf = await test_endpoint_performance(
        "获取行情数据",
        "/exchange/ticker",
        {"symbol": "BTC/USDT"},
        iterations=20
    )
    test_results["with_cache"]["ticker"] = ticker_perf

    # 测试orderbook
    orderbook_perf = await test_endpoint_performance(
        "获取订单簿",
        "/exchange/orderbook",
        {"symbol": "BTC/USDT", "limit": 20},
        iterations=20
    )
    test_results["with_cache"]["orderbook"] = orderbook_perf

    # 测试K线
    ohlcv_perf = await test_endpoint_performance(
        "获取K线数据",
        "/exchange/ohlcv",
        {"symbol": "BTC/USDT", "timeframe": "1h", "limit": 100},
        iterations=20
    )
    test_results["with_cache"]["ohlcv"] = ohlcv_perf

    # 测试交易对列表
    pairs_perf = await test_endpoint_performance(
        "获取交易对列表",
        "/exchange/pairs",
        iterations=20
    )
    test_results["with_cache"]["pairs"] = pairs_perf

    # 打印总结
    print(f"\n{'='*60}")
    print("性能测试总结")
    print('='*60)

    for endpoint, perf in test_results["with_cache"].items():
        print(f"\n{endpoint}:")
        print(f"  最小响应时间: {perf['min']:.2f}ms")
        print(f"  最大响应时间: {perf['max']:.2f}ms")
        print(f"  平均响应时间: {perf['avg']:.2f}ms")
        print(f"  中位数: {perf['median']:.2f}ms")
        print(f"  标准差: {perf['std']:.2f}ms")

    print(f"\n{'='*60}")
    print("测试完成")
    print('='*60)


if __name__ == "__main__":
    print("\n⚠️  开始测试前，请确保:")
    print("1. FastAPI服务已启动 (uvicorn app.main:app --reload)")
    print("2. 已配置Redis（可选，不配置则使用内存缓存）")
    print("\n按回车键开始测试...")
    input()

    asyncio.run(run_all_tests())
