#!/usr/bin/env python3
"""测试 Exchange API 端点"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_ticker():
    """测试行情API"""
    print("=== 测试行情API ===")
    try:
        response = requests.get(f"{BASE_URL}/api/exchange/ticker?symbol=BTC/USDT")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"错误: {response.text}")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False

def test_orderbook():
    """测试深度API"""
    print("\n=== 测试深度API ===")
    try:
        response = requests.get(f"{BASE_URL}/api/exchange/orderbook?symbol=BTC/USDT&limit=10")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data['success']}")
            bids_count = len(data['data']['bids'])
            asks_count = len(data['data']['asks'])
            print(f"买单数量: {bids_count}, 卖单数量: {asks_count}")
            return True
        else:
            print(f"错误: {response.text}")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False

def test_ohlcv():
    """测试K线API"""
    print("\n=== 测试K线API ===")
    try:
        response = requests.get(f"{BASE_URL}/api/exchange/ohlcv?symbol=BTC/USDT&timeframe=1h&limit=50")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data['success']}")
            ohlcv_count = len(data['data'])
            print(f"K线数量: {ohlcv_count}")
            return True
        else:
            print(f"错误: {response.text}")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False

def test_trades():
    """测试成交记录API"""
    print("\n=== 测试成交记录API ===")
    try:
        response = requests.get(f"{BASE_URL}/api/exchange/trades?symbol=BTC/USDT&limit=20")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data['success']}")
            trades_count = len(data['data'])
            print(f"成交记录数量: {trades_count}")
            return True
        else:
            print(f"错误: {response.text}")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False

def test_24h_stats():
    """测试24小时统计数据API"""
    print("\n=== 测试24小时统计数据API ===")
    try:
        response = requests.get(f"{BASE_URL}/api/exchange/24h-stats?symbol=BTC/USDT")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data['success']}")
            stats = data['data']
            print(f"最高价: {stats['high']:.2f}")
            print(f"最低价: {stats['low']:.2f}")
            print(f"成交量: {stats['volume']:.2f}")
            return True
        else:
            print(f"错误: {response.text}")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False

if __name__ == "__main__":
    print("开始测试 Exchange API 端点...")
    print("=" * 50)

    results = []
    results.append(("行情API", test_ticker()))
    results.append(("深度API", test_orderbook()))
    results.append(("K线API", test_ohlcv()))
    results.append(("成交记录API", test_trades()))
    results.append(("24小时统计API", test_24h_stats()))

    print("\n" + "=" * 50)
    print("测试结果汇总:")
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name}: {status}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
