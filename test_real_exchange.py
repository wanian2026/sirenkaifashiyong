"""
真实交易所API测试脚本
测试所有Exchange API端点是否正常工作
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any
import sys

API_BASE = "http://localhost:8000/api"

# 测试结果
test_results = {
    "passed": 0,
    "failed": 0,
    "details": []
}


async def test_endpoint(name: str, url: str, params: Dict = None) -> bool:
    """
    测试API端点

    Args:
        name: 测试名称
        url: API URL
        params: 请求参数

    Returns:
        测试是否通过
    """
    try:
        async with aiohttp.ClientSession() as session:
            full_url = f"{API_BASE}{url}"
            print(f"\n{'='*60}")
            print(f"测试: {name}")
            print(f"URL: {full_url}")
            if params:
                print(f"参数: {params}")

            async with session.get(full_url, params=params) as response:
                data = await response.json()

                if response.status == 200 and data.get('success', False):
                    print(f"✅ 通过")

                    # 检查数据来源
                    if 'source' in data:
                        print(f"   数据来源: {data['source']}")
                        if data['source'] == 'real':
                            print(f"   🎉 使用真实交易所数据!")
                        elif data['source'] == 'simulated':
                            print(f"   ⚠️  使用模拟数据: {data.get('warning', '未知原因')}")

                    # 显示部分数据
                    if 'data' in data:
                        sample_data = data['data']
                        if isinstance(sample_data, list) and len(sample_data) > 0:
                            print(f"   数据示例: {json.dumps(sample_data[0] if isinstance(sample_data[0], dict) else sample_data[:2], indent=2, ensure_ascii=False)}")
                        elif isinstance(sample_data, dict):
                            print(f"   数据键: {list(sample_data.keys())}")

                    test_results["passed"] += 1
                    test_results["details"].append({
                        "name": name,
                        "status": "passed",
                        "source": data.get('source', 'unknown')
                    })
                    return True
                else:
                    print(f"❌ 失败")
                    print(f"   状态码: {response.status}")
                    print(f"   响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    test_results["failed"] += 1
                    test_results["details"].append({
                        "name": name,
                        "status": "failed",
                        "error": data.get('detail', 'Unknown error')
                    })
                    return False

    except Exception as e:
        print(f"❌ 失败")
        print(f"   异常: {str(e)}")
        test_results["failed"] += 1
        test_results["details"].append({
            "name": name,
            "status": "failed",
            "error": str(e)
        })
        return False


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("真实交易所API测试")
    print("=" * 60)

    # 1. 测试连接
    await test_endpoint(
        "测试交易所连接",
        "/exchange/test-connection"
    )

    # 2. 获取交易对列表
    await test_endpoint(
        "获取交易对列表",
        "/exchange/pairs"
    )

    # 3. 获取行情数据
    await test_endpoint(
        "获取BTC/USDT行情",
        "/exchange/ticker",
        {"symbol": "BTC/USDT"}
    )

    await test_endpoint(
        "获取ETH/USDT行情",
        "/exchange/ticker",
        {"symbol": "ETH/USDT"}
    )

    # 4. 获取订单簿深度数据
    await test_endpoint(
        "获取BTC/USDT订单簿",
        "/exchange/orderbook",
        {"symbol": "BTC/USDT", "limit": 20}
    )

    # 5. 获取K线数据
    await test_endpoint(
        "获取BTC/USDT K线(15分钟)",
        "/exchange/ohlcv",
        {"symbol": "BTC/USDT", "timeframe": "15m", "limit": 50}
    )

    await test_endpoint(
        "获取BTC/USDT K线(1小时)",
        "/exchange/ohlcv",
        {"symbol": "BTC/USDT", "timeframe": "1h", "limit": 20}
    )

    # 6. 获取成交记录
    await test_endpoint(
        "获取BTC/USDT成交记录",
        "/exchange/trades",
        {"symbol": "BTC/USDT", "limit": 20}
    )

    # 7. 获取24小时统计数据
    await test_endpoint(
        "获取BTC/USDT 24小时统计",
        "/exchange/24h-stats",
        {"symbol": "BTC/USDT"}
    )

    # 打印测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总计: {test_results['passed'] + test_results['failed']} 个测试")
    print(f"通过: {test_results['passed']} ✅")
    print(f"失败: {test_results['failed']} ❌")

    # 统计数据来源
    real_count = sum(1 for d in test_results['details'] if d.get('source') == 'real')
    simulated_count = sum(1 for d in test_results['details'] if d.get('source') == 'simulated')

    print(f"\n数据来源统计:")
    print(f"  真实数据: {real_count} 个")
    print(f"  模拟数据: {simulated_count} 个")

    if simulated_count > 0:
        print(f"\n⚠️  注意: {simulated_count} 个API端点使用了模拟数据")
        print("   这可能是因为:")
        print("   1. 未配置交易所API密钥")
        print("   2. 网络连接问题")
        print("   3. 交易所API限流")
        print("   建议: 检查 .env 文件中的交易所配置")

    # 保存测试结果
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)

    print(f"\n测试结果已保存到: test_results.json")

    return test_results['failed'] == 0


if __name__ == "__main__":
    print("\n⚠️  开始测试前，请确保:")
    print("1. FastAPI服务已启动 (uvicorn app.main:app --reload)")
    print("2. 如需使用真实数据，请在.env中配置交易所API密钥")
    print("\n按回车键开始测试...")
    input()

    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
