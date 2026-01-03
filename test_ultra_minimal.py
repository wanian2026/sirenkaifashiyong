"""
极简界面功能测试脚本
测试 ultra_minimal.html 中所有功能模块的可用性
"""

import requests
import json
from typing import Dict, List, Tuple

API_BASE = "http://localhost:8000/api"


class APITester:
    def __init__(self):
        self.token = None
        self.test_results = []
    
    def log_result(self, module: str, action: str, success: bool, message: str = ""):
        """记录测试结果"""
        result = {
            "module": module,
            "action": action,
            "success": success,
            "message": message
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {module}: {action}")
        if message:
            print(f"   {message}")
    
    def get_headers(self) -> Dict:
        """获取带认证的请求头"""
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_login(self) -> bool:
        """测试登录功能"""
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                data={"username": "admin", "password": "admin123"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.token = data["access_token"]
                    self.log_result("认证", "登录", True)
                    return True
                else:
                    self.log_result("认证", "登录", False, "响应中缺少 access_token")
                    return False
            else:
                self.log_result("认证", "登录", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("认证", "登录", False, str(e))
            return False
    
    def test_get_bots(self) -> bool:
        """测试获取机器人列表"""
        try:
            response = requests.get(
                f"{API_BASE}/bots",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("机器人管理", "获取机器人列表", True, f"共 {len(data)} 个机器人")
                return True
            else:
                self.log_result("机器人管理", "获取机器人列表", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("机器人管理", "获取机器人列表", False, str(e))
            return False
    
    def test_get_recent_trades(self) -> bool:
        """测试获取最近交易记录"""
        try:
            response = requests.get(
                f"{API_BASE}/trades/recent?limit=10",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("交易记录", "获取最近交易", True, f"共 {len(data)} 条记录")
                return True
            else:
                self.log_result("交易记录", "获取最近交易", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("交易记录", "获取最近交易", False, str(e))
            return False
    
    def test_get_orders(self) -> bool:
        """测试获取订单列表"""
        try:
            response = requests.get(
                f"{API_BASE}/orders",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("订单管理", "获取订单列表", True, f"共 {len(data)} 个订单")
                return True
            else:
                self.log_result("订单管理", "获取订单列表", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("订单管理", "获取订单列表", False, str(e))
            return False
    
    def test_get_exchanges(self) -> bool:
        """测试获取交易所列表"""
        try:
            response = requests.get(
                f"{API_BASE}/exchange",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("交易所管理", "获取交易所列表", True, f"共 {len(data)} 个交易所")
                return True
            else:
                self.log_result("交易所管理", "获取交易所列表", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("交易所管理", "获取交易所列表", False, str(e))
            return False
    
    def test_add_exchange(self) -> bool:
        """测试添加交易所"""
        try:
            response = requests.post(
                f"{API_BASE}/exchange",
                headers=self.get_headers(),
                json={
                    "name": "测试交易所",
                    "exchange_id": "binance",
                    "api_key": "test_key",
                    "api_secret": "test_secret"
                }
            )
            
            if response.status_code == 200 or response.status_code == 201:
                self.log_result("交易所管理", "添加交易所", True)
                return True
            else:
                self.log_result("交易所管理", "添加交易所", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("交易所管理", "添加交易所", False, str(e))
            return False
    
    def test_get_performance_stats(self) -> bool:
        """测试获取性能统计数据"""
        try:
            response = requests.get(
                f"{API_BASE}/performance/stats",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("性能监控", "获取性能统计", True, f"CPU: {data.get('cpu_usage', 'N/A')}%")
                return True
            else:
                self.log_result("性能监控", "获取性能统计", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("性能监控", "获取性能统计", False, str(e))
            return False
    
    def test_database_backup(self) -> bool:
        """测试数据库备份"""
        try:
            response = requests.post(
                f"{API_BASE}/database-manager/backup",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_result("数据库管理", "数据库备份", True)
                return True
            else:
                self.log_result("数据库管理", "数据库备份", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("数据库管理", "数据库备份", False, str(e))
            return False
    
    def test_database_optimize(self) -> bool:
        """测试数据库优化"""
        try:
            response = requests.post(
                f"{API_BASE}/database-manager/optimize",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_result("数据库管理", "数据库优化", True)
                return True
            else:
                self.log_result("数据库管理", "数据库优化", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("数据库管理", "数据库优化", False, str(e))
            return False
    
    def test_get_database_backups(self) -> bool:
        """测试获取数据库备份列表"""
        try:
            response = requests.get(
                f"{API_BASE}/database-manager/backups",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("数据库管理", "获取备份列表", True, f"共 {len(data)} 个备份")
                return True
            else:
                self.log_result("数据库管理", "获取备份列表", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("数据库管理", "获取备份列表", False, str(e))
            return False
    
    def test_create_bot(self) -> bool:
        """测试创建机器人"""
        try:
            response = requests.post(
                f"{API_BASE}/bots",
                headers=self.get_headers(),
                json={
                    "name": "测试机器人",
                    "exchange_id": "binance",
                    "symbol": "BTC/USDT",
                    "strategy_type": "grid",
                    "investment_amount": 1000,
                    "grid_levels": 10,
                    "grid_spacing": 0.02
                }
            )
            
            if response.status_code == 200 or response.status_code == 201:
                self.log_result("机器人管理", "创建机器人", True)
                return True
            else:
                self.log_result("机器人管理", "创建机器人", False, f"状态码: {response.status_code}, 响应: {response.text}")
                return False
        except Exception as e:
            self.log_result("机器人管理", "创建机器人", False, str(e))
            return False
    
    def test_backtest_run(self) -> bool:
        """测试运行回测"""
        try:
            response = requests.post(
                f"{API_BASE}/backtest/run",
                headers=self.get_headers(),
                json={
                    "strategy_type": "grid",
                    "symbol": "BTC/USDT",
                    "timeframe": "1h",
                    "start_time": "2024-01-01",
                    "end_time": "2024-01-31",
                    "grid_levels": 10,
                    "grid_spacing": 0.02
                }
            )
            
            if response.status_code == 200 or response.status_code == 201:
                self.log_result("回测", "运行回测", True)
                return True
            else:
                self.log_result("回测", "运行回测", False, f"状态码: {response.status_code}, 响应: {response.text}")
                return False
        except Exception as e:
            self.log_result("回测", "运行回测", False, str(e))
            return False
    
    def test_user_registration(self) -> bool:
        """测试用户注册"""
        try:
            import random
            username = f"testuser_{random.randint(1000, 9999)}"
            response = requests.post(
                f"{API_BASE}/auth/register",
                json={
                    "username": username,
                    "email": f"{username}@test.com",
                    "password": "test123456"
                }
            )
            
            if response.status_code == 200 or response.status_code == 201:
                self.log_result("用户管理", "用户注册", True, f"用户: {username}")
                return True
            else:
                self.log_result("用户管理", "用户注册", False, f"状态码: {response.status_code}, 响应: {response.text}")
                return False
        except Exception as e:
            self.log_result("用户管理", "用户注册", False, str(e))
            return False
    
    def test_rbac_users(self) -> bool:
        """测试获取用户列表 (RBAC)"""
        try:
            response = requests.get(
                f"{API_BASE}/rbac/users",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("用户管理", "获取用户列表", True, f"共 {len(data)} 个用户")
                return True
            elif response.status_code == 404:
                self.log_result("用户管理", "获取用户列表", False, "端点不存在 (404)")
                return False
            else:
                self.log_result("用户管理", "获取用户列表", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("用户管理", "获取用户列表", False, str(e))
            return False
    
    def test_analytics(self) -> bool:
        """测试数据分析"""
        try:
            response = requests.get(
                f"{API_BASE}/analytics/overview",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_result("数据分析", "获取分析概览", True)
                return True
            else:
                self.log_result("数据分析", "获取分析概览", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("数据分析", "获取分析概览", False, str(e))
            return False
    
    def test_risk(self) -> bool:
        """测试风险管理"""
        try:
            response = requests.get(
                f"{API_BASE}/risk/summary",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_result("风险管理", "获取风险概览", True)
                return True
            else:
                self.log_result("风险管理", "获取风险概览", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("风险管理", "获取风险概览", False, str(e))
            return False
    
    def test_audit_logs(self) -> bool:
        """测试审计日志"""
        try:
            response = requests.get(
                f"{API_BASE}/audit-logs",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("审计日志", "获取审计日志", True, f"共 {len(data.get('logs', []))} 条日志")
                return True
            else:
                self.log_result("审计日志", "获取审计日志", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("审计日志", "获取审计日志", False, str(e))
            return False
    
    def test_notifications(self) -> bool:
        """测试通知管理"""
        try:
            response = requests.get(
                f"{API_BASE}/notifications",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_result("通知管理", "获取通知配置", True)
                return True
            else:
                self.log_result("通知管理", "获取通知配置", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("通知管理", "获取通知配置", False, str(e))
            return False
    
    def test_log_manager(self) -> bool:
        """测试日志管理"""
        try:
            response = requests.get(
                f"{API_BASE}/log-manager/logs",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_result("日志管理", "获取系统日志", True)
                return True
            else:
                self.log_result("日志管理", "获取系统日志", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("日志管理", "获取系统日志", False, str(e))
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("开始测试极简界面所有功能")
        print("=" * 60)
        print()
        
        # 1. 认证测试
        print("【1/16】认证功能")
        if not self.test_login():
            print("\n❌ 登录失败，无法继续测试其他功能")
            return
        print()
        
        # 2. 仪表盘数据
        print("【2/16】仪表盘数据")
        self.test_get_bots()
        self.test_get_recent_trades()
        print()
        
        # 3. 机器人管理
        print("【3/16】机器人管理")
        self.test_get_bots()
        self.test_create_bot()
        print()
        
        # 4. 交易记录
        print("【4/16】交易记录")
        self.test_get_recent_trades()
        print()
        
        # 5. 订单管理
        print("【5/16】订单管理")
        self.test_get_orders()
        print()
        
        # 6. 交易所管理
        print("【6/16】交易所管理")
        self.test_get_exchanges()
        self.test_add_exchange()
        print()
        
        # 7. 风险管理
        print("【7/16】风险管理")
        self.test_risk()
        print()
        
        # 8. 回测
        print("【8/16】回测")
        self.test_backtest_run()
        print()
        
        # 9. 数据分析
        print("【9/16】数据分析")
        self.test_analytics()
        print()
        
        # 10. 用户管理
        print("【10/16】用户管理")
        self.test_user_registration()
        self.test_rbac_users()
        print()
        
        # 11. 审计日志
        print("【11/16】审计日志")
        self.test_audit_logs()
        print()
        
        # 12. 性能监控
        print("【12/16】性能监控")
        self.test_get_performance_stats()
        print()
        
        # 13. 数据库管理
        print("【13/16】数据库管理")
        self.test_database_backup()
        self.test_database_optimize()
        self.test_get_database_backups()
        print()
        
        # 14. 日志管理
        print("【14/16】日志管理")
        self.test_log_manager()
        print()
        
        # 15. 通知管理
        print("【15/16】通知管理")
        self.test_notifications()
        print()
        
        # 16. 系统设置
        print("【16/16】系统设置")
        self.log_result("系统设置", "系统配置", True, "前端功能（无需后端测试）")
        print()
        
        # 打印测试报告
        self.print_report()
    
    def print_report(self):
        """打印测试报告"""
        print("=" * 60)
        print("测试报告")
        print("=" * 60)
        print()
        
        total = len(self.test_results)
        success = sum(1 for r in self.test_results if r["success"])
        failed = total - success
        
        print(f"总计: {total} 个测试")
        print(f"成功: {success} 个")
        print(f"失败: {failed} 个")
        print(f"成功率: {success/total*100:.1f}%")
        print()
        
        if failed > 0:
            print("失败的测试:")
            print("-" * 60)
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['module']}: {result['action']}")
                    if result["message"]:
                        print(f"   {result['message']}")
            print()
        
        # 按模块统计
        print("=" * 60)
        print("模块统计")
        print("=" * 60)
        modules = {}
        for result in self.test_results:
            module = result["module"]
            if module not in modules:
                modules[module] = {"total": 0, "success": 0}
            modules[module]["total"] += 1
            if result["success"]:
                modules[module]["success"] += 1
        
        for module, stats in sorted(modules.items()):
            success_rate = stats["success"] / stats["total"] * 100
            status = "✅" if success_rate == 100 else "⚠️" if success_rate > 0 else "❌"
            print(f"{status} {module}: {stats['success']}/{stats['total']} ({success_rate:.0f}%)")
        
        print()
        
        # 保存测试报告
        self.save_report()
    
    def save_report(self):
        """保存测试报告到文件"""
        import datetime
        
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "successful": sum(1 for r in self.test_results if r["success"]),
            "failed": sum(1 for r in self.test_results if not r["success"]),
            "results": self.test_results
        }
        
        with open("ultra_minimal_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("✅ 测试报告已保存到: ultra_minimal_test_report.json")


if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
