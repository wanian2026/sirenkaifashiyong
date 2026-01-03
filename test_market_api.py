#!/usr/bin/env python3
"""
测试实时行情API功能
"""

import requests
import json

API_BASE = "http://localhost:8000/api"

def test_market_api():
    """测试市场行情API"""

    print("=" * 60)
    print("测试实时行情API功能")
    print("=" * 60)

    # 测试1: 获取交易对列表
    print("\n1. 测试获取交易对列表...")
    try:
        response = requests.get(f"{API_BASE}/exchange/pairs")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                pairs = data.get('data', [])
                print(f"   ✅ 成功获取 {len(pairs)} 个交易对")
                if pairs:
                    print(f"   示例: {pairs[0]}")
            else:
                print(f"   ❌ 失败: {data}")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")

    # 测试2: 获取单个交易对行情
    print("\n2. 测试获取单个交易对行情 (BTC/USDT)...")
    try:
        response = requests.get(f"{API_BASE}/exchange/ticker?symbol=BTC/USDT")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                ticker = data.get('data', {})
                print(f"   ✅ 成功获取行情")
                print(f"   最新价: {ticker.get('last')}")
                print(f"   24h涨跌: {ticker.get('percentage')}%")
                print(f"   数据来源: {data.get('source')}")
            else:
                print(f"   ❌ 失败: {data}")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")

    # 测试3: 批量获取多个交易对行情
    print("\n3. 测试批量获取交易对行情...")
    try:
        symbols = "BTC/USDT,ETH/USDT,BNB/USDT"
        response = requests.get(f"{API_BASE}/exchange/tickers/batch?symbols={symbols}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                tickers = data.get('data', [])
                print(f"   ✅ 成功获取 {len(tickers)} 个交易对行情")
                for ticker in tickers:
                    print(f"   {ticker['symbol']}: {ticker.get('last')} ({ticker.get('percentage')}%)")
            else:
                print(f"   ❌ 失败: {data}")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_market_api()
