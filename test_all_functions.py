#!/usr/bin/env python3
"""
全面测试加密货币交易系统的所有功能
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api"

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.not_implemented = []

    def add_pass(self, test_name, detail=""):
        self.passed.append({"name": test_name, "detail": detail})
        print(f"✅ PASS: {test_name}")

    def add_fail(self, test_name, error):
        self.failed.append({"name": test_name, "error": error})
        print(f"❌ FAIL: {test_name} - {error}")

    def add_not_implemented(self, test_name):
        self.not_implemented.append({"name": test_name})
        print(f"⚠️  NOT IMPLEMENTED: {test_name}")

    def report(self):
        total = len(self.passed) + len(self.failed) + len(self.not_implemented)
        print(f"\n{'='*60}")
        print(f"测试总结: {len(self.passed)}/{total} 通过")
        print(f"{'='*60}")
        if self.passed:
            print(f"\n✅ 通过的功能 ({len(self.passed)}):")
            for test in self.passed:
                print(f"  - {test['name']}")
        if self.failed:
            print(f"\n❌ 失败的功能 ({len(self.failed)}):")
            for test in self.failed:
                print(f"  - {test['name']}: {test['error']}")
        if self.not_implemented:
            print(f"\n⚠️  未实现的功能 ({len(self.not_implemented)}):")
            for test in self.not_implemented:
                print(f"  - {test['name']}")


def test_auth(results):
    """测试认证功能"""
    print("\n" + "="*60)
    print("测试认证功能")
    print("="*60)

    try:
        # 登录
        response = requests.post(
            f"{API_BASE}/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            results.add_pass("登录功能")
            return token
        else:
            results.add_fail("登录功能", response.text)
            return None
    except Exception as e:
        results.add_fail("登录功能", str(e))
        return None


def test_bots(results, token):
    """测试机器人管理功能"""
    print("\n" + "="*60)
    print("测试机器人管理功能")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # 创建机器人
    try:
        response = requests.post(
            f"{API_BASE}/bots/",
            json={
                "name": "测试机器人",
                "strategy": "hedge_grid",
                "trading_pair": "BTCUSDT",
                "exchange": "binance",
                "config": {"initial_capital": 1000}
            },
            headers=headers
        )
        if response.status_code == 201:
            bot_id = response.json()["id"]
            results.add_pass("创建机器人")
        else:
            results.add_fail("创建机器人", response.text)
            bot_id = None
    except Exception as e:
        results.add_fail("创建机器人", str(e))
        bot_id = None

    # 获取机器人列表
    try:
        response = requests.get(f"{API_BASE}/bots/", headers=headers)
        if response.status_code == 200:
            results.add_pass("获取机器人列表")
        else:
            results.add_fail("获取机器人列表", response.text)
    except Exception as e:
        results.add_fail("获取机器人列表", str(e))

    # 启动所有机器人
    try:
        response = requests.post(f"{API_BASE}/bots/start-all", headers=headers)
        if response.status_code == 200:
            results.add_pass("启动所有机器人")
        else:
            results.add_fail("启动所有机器人", response.text)
    except Exception as e:
        results.add_fail("启动所有机器人", str(e))

    # 停止所有机器人
    try:
        response = requests.post(f"{API_BASE}/bots/stop-all", headers=headers)
        if response.status_code == 200:
            results.add_pass("停止所有机器人")
        else:
            results.add_fail("停止所有机器人", response.text)
    except Exception as e:
        results.add_fail("停止所有机器人", str(e))

    # 测试交易所连接
    try:
        response = requests.get(f"{API_BASE}/exchange/test")
        if response.status_code == 200:
            results.add_pass("测试交易所连接")
        else:
            results.add_fail("测试交易所连接", response.text)
    except Exception as e:
        results.add_fail("测试交易所连接", str(e))

    return bot_id


def test_trades(results, token):
    """测试交易功能"""
    print("\n" + "="*60)
    print("测试交易功能")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # 获取交易记录
    try:
        response = requests.get(f"{API_BASE}/trades/?limit=10", headers=headers)
        if response.status_code == 200:
            results.add_pass("获取交易记录")
        else:
            results.add_fail("获取交易记录", response.text)
    except Exception as e:
        results.add_fail("获取交易记录", str(e))


def test_orders(results, token):
    """测试订单功能"""
    print("\n" + "="*60)
    print("测试订单功能")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # 获取订单列表
    try:
        response = requests.get(f"{API_BASE}/orders/", headers=headers)
        if response.status_code == 200:
            results.add_pass("获取订单列表")
        else:
            results.add_fail("获取订单列表", response.text)
    except Exception as e:
        results.add_fail("获取订单列表", str(e))


def test_backtest(results, token):
    """测试回测功能"""
    print("\n" + "="*60)
    print("测试回测功能")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # 运行回测
    try:
        response = requests.post(
            f"{API_BASE}/backtest/run?strategy_type=hedge_grid&trading_pair=BTCUSDT&start_date=2024-01-01&end_date=2024-12-31&initial_capital=10000",
            headers=headers
        )
        if response.status_code == 200:
            results.add_pass("运行回测")
        else:
            results.add_fail("运行回测", response.text)
    except Exception as e:
        results.add_fail("运行回测", str(e))


def test_risk(results, token):
    """测试风险管理功能"""
    print("\n" + "="*60)
    print("测试风险管理功能")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # 获取风险指标
    try:
        response = requests.get(f"{API_BASE}/risk/metrics", headers=headers)
        if response.status_code == 200:
            results.add_pass("获取风险指标")
        else:
            results.add_fail("获取风险指标", response.text)
    except Exception as e:
        results.add_fail("获取风险指标", str(e))

    # 风险检查
    try:
        response = requests.post(
            f"{API_BASE}/risk/check",
            json={"bot_id": 1},
            headers=headers
        )
        if response.status_code == 200:
            results.add_pass("风险检查")
        else:
            results.add_fail("风险检查", response.text)
    except Exception as e:
        results.add_fail("风险检查", str(e))


def test_notifications(results, token):
    """测试通知功能"""
    print("\n" + "="*60)
    print("测试通知功能")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # 获取通知列表
    try:
        response = requests.get(f"{API_BASE}/notifications/", headers=headers)
        if response.status_code == 200:
            results.add_pass("获取通知列表")
        else:
            results.add_fail("获取通知列表", response.text)
    except Exception as e:
        results.add_fail("获取通知列表", str(e))


def test_system(results, token=None):
    if not token:
        headers = {}
    else:
        headers = {"Authorization": f"Bearer {token}"}
    """测试系统功能"""
    print("\n" + "="*60)
    print("测试系统功能")
    print("="*60)

    # 清空缓存
    try:
        response = requests.post(f"{API_BASE}/cache/clear", headers=headers)
        if response.status_code == 200:
            results.add_pass("清空缓存")
        else:
            results.add_fail("清空缓存", response.text)
    except Exception as e:
        results.add_fail("清空缓存", str(e))

    # 系统信息
    try:
        response = requests.get(f"{API_BASE}/system/info")
        if response.status_code == 200:
            results.add_pass("获取系统信息")
        else:
            results.add_fail("获取系统信息", response.text)
    except Exception as e:
        results.add_fail("获取系统信息", str(e))


def check_frontend_functions(results):
    """检查前端调用的API是否存在"""
    print("\n" + "="*60)
    print("检查前端功能对应的API")
    print("="*60)

    # 检查克隆机器人
    results.add_not_implemented("克隆机器人")

    # 检查导入配置
    results.add_not_implemented("导入配置")

    # 检查导出交易
    results.add_not_implemented("导出交易")

    # 检查取消所有订单
    results.add_not_implemented("取消所有订单")

    # 检查配置策略
    results.add_not_implemented("配置策略")

    # 检查运行优化
    results.add_not_implemented("运行优化")

    # 检查加载/清空通知
    results.add_not_implemented("加载/清空通知")

    # 检查通知设置
    results.add_not_implemented("通知设置")

    # 检查加载/清空日志
    results.add_not_implemented("加载/清空日志")

    # 检查下载日志
    results.add_not_implemented("下载日志")

    # 检查测试API连接
    results.add_not_implemented("测试API连接")

    # 检查保存API设置
    results.add_not_implemented("保存API设置")

    # 检查保存系统设置
    results.add_not_implemented("保存系统设置")

    # 检查备份数据库
    results.add_not_implemented("备份数据库")

    # 检查优化数据库
    results.add_not_implemented("优化数据库")

    # 检查清空数据库
    results.add_not_implemented("清空数据库")

    # 检查保存风险设置
    results.add_not_implemented("保存风险设置")


def main():
    print("="*60)
    print("开始全面测试加密货币交易系统")
    print("="*60)

    results = TestResults()

    # 测试认证
    token = test_auth(results)
    if not token:
        print("\n❌ 认证失败，停止测试")
        results.report()
        return

    # 测试机器人管理
    test_bots(results, token)

    # 测试交易
    test_trades(results, token)

    # 测试订单
    test_orders(results, token)

    # 测试回测
    test_backtest(results, token)

    # 测试风险管理
    test_risk(results, token)

    # 测试通知
    test_notifications(results, token)

    # 测试系统功能
    test_system(results)

    # 检查前端功能
    check_frontend_functions(results)

    # 生成报告
    results.report()


if __name__ == "__main__":
    main()
