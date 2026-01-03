#!/usr/bin/env python3
"""
管理界面功能测试脚本
测试所有管理界面功能的可用性
"""

import requests
import json
import sys
from datetime import datetime

# 配置
API_BASE = "http://localhost:8000/api"
TEST_USER = {
    "username": "test_user",
    "email": "test@example.com",
    "password": "Test123456!"
}

class ManagementInterfaceTester:
    def __init__(self):
        self.token = None
        self.test_results = []

    def log_result(self, test_name, success, message=""):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")

    def test_health(self):
        """测试健康检查接口"""
        try:
            response = requests.get(f"{API_BASE.replace('/api', '')}/health", timeout=5)
            self.log_result("健康检查", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("健康检查", False, str(e))
            return False

    def test_auth_login(self):
        """测试用户登录"""
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                data={
                    "username": "admin",
                    "password": "admin123"
                },
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.token = data["access_token"]
                    self.log_result("用户登录", True, "获取到token")
                    return True
                else:
                    self.log_result("用户登录", False, "响应中没有token")
                    return False
            else:
                self.log_result("用户登录", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("用户登录", False, str(e))
            return False

    def get_headers(self):
        """获取认证头"""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def test_bots_list(self):
        """测试机器人列表"""
        try:
            response = requests.get(
                f"{API_BASE}/bots/",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("机器人列表", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("机器人列表", False, str(e))
            return False

    def test_trades_list(self):
        """测试交易记录列表"""
        try:
            response = requests.get(
                f"{API_BASE}/trades/",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("交易记录列表", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("交易记录列表", False, str(e))
            return False

    def test_orders_list(self):
        """测试订单列表"""
        try:
            response = requests.get(
                f"{API_BASE}/orders/",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("订单列表", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("订单列表", False, str(e))
            return False

    def test_analytics_stats(self):
        """测试数据分析统计"""
        try:
            response = requests.get(
                f"{API_BASE}/trades/stats",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("数据分析统计", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("数据分析统计", False, str(e))
            return False

    def test_risk_metrics(self):
        """测试风险管理指标"""
        try:
            response = requests.get(
                f"{API_BASE}/risk/metrics",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("风险管理指标", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("风险管理指标", False, str(e))
            return False

    def test_strategies_list(self):
        """测试策略列表"""
        try:
            response = requests.get(
                f"{API_BASE}/strategies/",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("策略列表", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("策略列表", False, str(e))
            return False

    def test_notifications_list(self):
        """测试通知列表"""
        try:
            response = requests.get(
                f"{API_BASE}/notifications/",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("通知列表", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("通知列表", False, str(e))
            return False

    def test_logs_list(self):
        """测试日志列表"""
        try:
            response = requests.get(
                f"{API_BASE}/logs/",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("日志列表", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("日志列表", False, str(e))
            return False

    # ===== 新增功能模块测试 =====

    def test_rbac_users(self):
        """测试用户管理 - 用户列表"""
        try:
            response = requests.get(
                f"{API_BASE}/rbac/users",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("用户管理 - 用户列表", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("用户管理 - 用户列表", False, str(e))
            return False

    def test_rbac_roles(self):
        """测试用户管理 - 角色列表"""
        try:
            response = requests.get(
                f"{API_BASE}/rbac/roles",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("用户管理 - 角色列表", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("用户管理 - 角色列表", False, str(e))
            return False

    def test_exchanges_list(self):
        """测试交易所管理 - 交易所列表"""
        try:
            response = requests.get(
                f"{API_BASE}/exchanges/",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("交易所管理 - 交易所列表", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("交易所管理 - 交易所列表", False, str(e))
            return False

    def test_exchange_config(self):
        """测试交易所管理 - 获取交易所配置"""
        try:
            response = requests.get(
                f"{API_BASE}/exchanges/binance",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("交易所管理 - 获取配置", response.status_code in [200, 404], f"状态码: {response.status_code}")
            return response.status_code in [200, 404]
        except Exception as e:
            self.log_result("交易所管理 - 获取配置", False, str(e))
            return False

    def test_exchange_test(self):
        """测试交易所管理 - 测试连接"""
        try:
            response = requests.get(
                f"{API_BASE}/exchange/test",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("交易所管理 - 测试连接", response.status_code in [200, 400], f"状态码: {response.status_code}")
            return response.status_code in [200, 400]
        except Exception as e:
            self.log_result("交易所管理 - 测试连接", False, str(e))
            return False

    def test_audit_logs(self):
        """测试审计日志 - 日志列表"""
        try:
            response = requests.get(
                f"{API_BASE}/audit/logs",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("审计日志 - 日志列表", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("审计日志 - 日志列表", False, str(e))
            return False

    def test_performance_metrics(self):
        """测试性能监控 - 性能指标"""
        try:
            response = requests.get(
                f"{API_BASE}/performance/metrics",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("性能监控 - 性能指标", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("性能监控 - 性能指标", False, str(e))
            return False

    def test_performance_api(self):
        """测试性能监控 - API性能"""
        try:
            response = requests.get(
                f"{API_BASE}/performance/api",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("性能监控 - API性能", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("性能监控 - API性能", False, str(e))
            return False

    def test_database_backups(self):
        """测试数据库管理 - 备份列表"""
        try:
            response = requests.get(
                f"{API_BASE}/database/backups",
                headers=self.get_headers(),
                timeout=5
            )
            self.log_result("数据库管理 - 备份列表", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("数据库管理 - 备份列表", False, str(e))
            return False

    def test_database_optimize(self):
        """测试数据库管理 - 数据库优化"""
        try:
            response = requests.post(
                f"{API_BASE}/database/optimize",
                headers=self.get_headers(),
                timeout=30
            )
            self.log_result("数据库管理 - 优化", response.status_code == 200, f"状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_result("数据库管理 - 优化", False, str(e))
            return False

    def test_backtest(self):
        """测试策略回测"""
        try:
            response = requests.post(
                f"{API_BASE}/backtest/run",
                headers=self.get_headers(),
                json={
                    "strategy_type": "hedge_grid",
                    "trading_pair": "BTCUSDT",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                },
                timeout=30
            )
            self.log_result("策略回测", response.status_code in [200, 400], f"状态码: {response.status_code}")
            return response.status_code in [200, 400]
        except Exception as e:
            self.log_result("策略回测", False, str(e))
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("开始测试管理界面功能")
        print("="*60 + "\n")

        # 基础测试
        print("【基础功能测试】")
        self.test_health()
        if not self.test_auth_login():
            print("\n❌ 无法登录，跳过需要认证的测试")
            return self.generate_report()

        # 原有功能测试
        print("\n【原有功能测试】")
        self.test_bots_list()
        self.test_trades_list()
        self.test_orders_list()
        self.test_analytics_stats()
        self.test_risk_metrics()
        self.test_strategies_list()
        self.test_notifications_list()
        self.test_logs_list()
        self.test_backtest()

        # 新增功能测试
        print("\n【新增功能测试】")
        print("--- 用户管理模块 ---")
        self.test_rbac_users()
        self.test_rbac_roles()

        print("\n--- 交易所管理模块 ---")
        self.test_exchanges_list()
        self.test_exchange_config()
        self.test_exchange_test()

        print("\n--- 审计日志模块 ---")
        self.test_audit_logs()

        print("\n--- 性能监控模块 ---")
        self.test_performance_metrics()
        self.test_performance_api()

        print("\n--- 数据库管理模块 ---")
        self.test_database_backups()
        self.test_database_optimize()

        # 生成报告
        print("\n" + "="*60)
        print("测试完成")
        print("="*60 + "\n")
        return self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": round(success_rate, 2)
            },
            "results": self.test_results
        }

        # 保存报告
        with open("management_interface_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 打印摘要
        print(f"总测试数: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"成功率: {success_rate:.2f}%")
        print(f"\n详细报告已保存到: management_interface_test_report.json")

        return report

if __name__ == "__main__":
    tester = ManagementInterfaceTester()
    report = tester.run_all_tests()

    # 如果有失败的测试，返回非0退出码
    if report["summary"]["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
