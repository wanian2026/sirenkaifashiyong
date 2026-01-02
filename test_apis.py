#!/usr/bin/env python3
"""
API功能测试脚本
测试数据分析、风险管理和通知系统功能
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# API基础URL
BASE_URL = "http://localhost:8000"


async def test_api_health():
    """测试API健康检查"""
    print("\n" + "="*50)
    print("测试API健康检查")
    print("="*50)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
            return True
        except Exception as e:
            print(f"错误: {e}")
            return False


async def test_system_info():
    """测试系统信息"""
    print("\n" + "="*50)
    print("测试系统信息")
    print("="*50)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/system/info")
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return True
        except Exception as e:
            print(f"错误: {e}")
            return False


async def test_analytics_endpoints():
    """测试数据分析API端点（需要认证）"""
    print("\n" + "="*50)
    print("测试数据分析API端点")
    print("="*50)

    # 这些端点需要认证，我们先测试端点是否存在
    endpoints = [
        "/api/analytics/dashboard",
        "/api/analytics/profit-curve",
        "/api/analytics/trade-statistics",
        "/api/analytics/hourly-trades",
        "/api/analytics/overview"
    ]

    async with httpx.AsyncClient() as client:
        for endpoint in endpoints:
            try:
                response = await client.get(f"{BASE_URL}{endpoint}")
                status = "✓" if response.status_code in [200, 401] else "✗"
                print(f"{status} {endpoint} - 状态码: {response.status_code}")
            except Exception as e:
                print(f"✗ {endpoint} - 错误: {e}")


async def test_risk_endpoints():
    """测试风险管理API端点"""
    print("\n" + "="*50)
    print("测试风险管理API端点")
    print("="*50)

    # 测试计算工具（不需要认证）
    calc_endpoints = [
        ("POST", "/api/risk/calculate/position-size?account_balance=10000&entry_price=50000&stop_loss_price=49000&risk_percent=0.02", None),
        ("POST", "/api/risk/calculate/risk-reward-ratio?entry_price=50000&stop_loss_price=49000&take_profit_price=52000", None)
    ]

    async with httpx.AsyncClient() as client:
        for method, endpoint, data in calc_endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}", json=data)
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")

                status = "✓" if response.status_code == 200 else "✗"
                print(f"{status} {method} {endpoint.split('?')[0]} - 状态码: {response.status_code}")
                if response.status_code == 200:
                    print(f"   响应: {json.dumps(response.json(), indent=2)}")
            except Exception as e:
                print(f"✗ {method} {endpoint.split('?')[0]} - 错误: {e}")


async def test_notification_endpoints():
    """测试通知系统API端点"""
    print("\n" + "="*50)
    print("测试通知系统API端点")
    print("="*50)

    # 测试配置端点（需要认证，只测试端点存在）
    config_endpoints = [
        "/api/notifications/configure/email",
        "/api/notifications/configure/dingtalk",
        "/api/notifications/configure/feishu",
        "/api/notifications/configure/telegram",
        "/api/notifications/configure/webhook",
        "/api/notifications/send",
        "/api/notifications/history"
    ]

    async with httpx.AsyncClient() as client:
        for endpoint in config_endpoints:
            try:
                response = await client.post(f"{BASE_URL}{endpoint}", json={})
                status = "✓" if response.status_code in [200, 401, 422] else "✗"
                print(f"{status} {endpoint} - 状态码: {response.status_code}")
            except Exception as e:
                print(f"✗ {endpoint} - 错误: {e}")


async def test_cache_endpoints():
    """测试缓存API端点"""
    print("\n" + "="*50)
    print("测试缓存API端点")
    print("="*50)

    cache_endpoints = [
        ("/api/cache/status", "GET"),
        ("/api/cache/stats", "GET")
    ]

    async with httpx.AsyncClient() as client:
        for endpoint, method in cache_endpoints:
            try:
                response = await client.get(f"{BASE_URL}{endpoint}")
                status = "✓" if response.status_code == 200 else "✗"
                print(f"{status} {method} {endpoint} - 状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   缓存后端: {data.get('data', {}).get('backend', 'N/A')}")
                    print(f"   Redis已启用: {data.get('data', {}).get('redis_enabled', False)}")
            except Exception as e:
                print(f"✗ {method} {endpoint} - 错误: {e}")


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("加密货币交易系统 - API功能测试")
    print("="*60)

    # 测试基础功能
    results = []
    results.append(await test_api_health())
    results.append(await test_system_info())

    # 测试各个模块的端点
    await test_analytics_endpoints()
    await test_risk_endpoints()
    await test_notification_endpoints()
    await test_cache_endpoints()

    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    if all(results):
        print("✓ 基础API测试通过")
    else:
        print("✗ 部分基础API测试失败")

    print("\n说明: 部分端点需要用户认证，状态码401表示端点存在但需要登录")
    print("      状态码422表示请求参数验证失败（端点存在但参数不正确）")


if __name__ == "__main__":
    asyncio.run(main())
