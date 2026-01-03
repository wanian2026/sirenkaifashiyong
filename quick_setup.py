#!/usr/bin/env python3
"""
加密货币交易系统 - 快速配置脚本
帮助用户快速配置交易所、创建机器人并启动
"""

import requests
import json
import sys

API_BASE = "http://localhost:8000/api"


class QuickSetup:
    def __init__(self):
        self.token = None
        self.exchange_config_id = None
        self.bot_id = None
    
    def print_header(self, text):
        """打印标题"""
        print("\n" + "="*60)
        print(f"  {text}")
        print("="*60 + "\n")
    
    def print_success(self, text):
        """打印成功信息"""
        print(f"✅ {text}")
    
    def print_error(self, text):
        """打印错误信息"""
        print(f"❌ {text}")
    
    def print_info(self, text):
        """打印信息"""
        print(f"ℹ️  {text}")
    
    def get_headers(self):
        """获取带认证的请求头"""
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}
    
    def login(self):
        """登录系统"""
        self.print_header("步骤 1/4: 登录系统")
        
        print("使用默认管理员账户登录:")
        print("  用户名: admin")
        print("  密码: admin123\n")
        
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                data={"username": "admin", "password": "admin123"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.token = data["access_token"]
                    self.print_success("登录成功!")
                    return True
            
            self.print_error(f"登录失败: {response.status_code}")
            return False
        except Exception as e:
            self.print_error(f"登录异常: {e}")
            return False
    
    def configure_exchange(self):
        """配置交易所"""
        self.print_header("步骤 2/4: 配置交易所API")
        
        # 支持的交易所
        print("支持的交易所:")
        print("  1. binance (币安)")
        print("  2. okx (欧易)")
        print()
        
        # 获取交易所
        exchange_map = {"1": "binance", "2": "okx"}
        exchange_choice = input("请选择交易所 (1-2) [默认: 1]: ").strip() or "1"
        exchange_name = exchange_map.get(exchange_choice, "binance")
        
        # 获取API密钥
        print("\n请输入交易所API信息:")
        api_key = input("API Key: ").strip()
        if not api_key:
            self.print_error("API Key不能为空")
            return False
        
        api_secret = input("API Secret: ").strip()
        if not api_secret:
            self.print_error("API Secret不能为空")
            return False
        
        passphrase = input("Passphrase (OKX需要，其他可按Enter跳过): ").strip() or None
        
        # 是否测试网
        is_testnet = input("\n是否使用测试网? (y/N): ").strip().lower() == "y"
        
        # 标签和备注
        label = input("配置标签 [可选]: ").strip() or f"{exchange_name}配置"
        notes = input("备注 [可选]: ").strip() or ""
        
        self.print_info("正在测试交易所连接...")
        
        # 测试连接
        test_data = {
            "exchange_name": exchange_name,
            "api_key": api_key,
            "api_secret": api_secret,
            "is_testnet": is_testnet
        }
        
        if passphrase:
            test_data["passphrase"] = passphrase
        
        try:
            response = requests.post(
                f"{API_BASE}/exchanges/test-connection",
                json=test_data
            )
            
            if response.status_code != 200:
                result = response.json()
                self.print_error(f"连接测试失败: {result.get('detail', '未知错误')}")
                return False
            
            result = response.json()
            if not result.get('success'):
                self.print_error(f"连接测试失败: {result.get('message', '未知错误')}")
                return False
            
            self.print_success("交易所连接测试通过!")
            
            # 创建配置
            self.print_info("正在保存交易所配置...")
            
            config_data = {
                "exchange_name": exchange_name,
                "api_key": api_key,
                "api_secret": api_secret,
                "label": label,
                "notes": notes,
                "is_testnet": is_testnet
            }
            
            if passphrase:
                config_data["passphrase"] = passphrase
            
            response = requests.post(
                f"{API_BASE}/exchanges/",
                json=config_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 201:
                result = response.json()
                self.exchange_config_id = result.get('id')
                self.print_success(f"交易所配置已创建! (ID: {self.exchange_config_id})")
                self.print_info(f"交易所: {exchange_name}")
                self.print_info(f"测试网: {'是' if is_testnet else '否'}")
                return True
            else:
                result = response.json()
                self.print_error(f"创建配置失败: {result.get('detail', '未知错误')}")
                return False
            
        except Exception as e:
            self.print_error(f"配置交易所异常: {e}")
            return False
    
    def create_bot(self):
        """创建机器人"""
        self.print_header("步骤 3/4: 创建交易机器人")
        
        # 机器人名称
        name = input("机器人名称 [例如: BTC网格机器人]: ").strip() or "默认网格机器人"
        
        # 交易对
        print("\n常用交易对:")
        print("  BTC/USDT")
        print("  ETH/USDT")
        print("  BNB/USDT")
        print("  SOL/USDT")
        trading_pair = input("\n交易对 [例如: BTC/USDT]: ").strip() or "BTC/USDT"
        
        # 策略选择
        print("\n可用策略:")
        print("  1. code_a (Code A策略)")
        strategy_map = {"1": "code_a"}
        strategy_choice = input("请选择策略 (1-1) [默认: 1]: ").strip() or "1"
        strategy = strategy_map.get(strategy_choice, "code_a")

        # 策略配置
        self.print_info("配置策略参数:")

        grid_levels = int(input("网格层数 [默认: 10]: ").strip() or "10")
        grid_spacing = float(input("网格间距，如 0.02 表示 2% [默认: 0.02]: ").strip() or "0.02")
        threshold = float(input("阈值，如 0.01 表示 1% [默认: 0.01]: ").strip() or "0.01")
        investment_amount = float(input("投资金额 USDT [默认: 100]: ").strip() or "100")
        max_position = float(input("最大仓位 USDT [默认: 1000]: ").strip() or "1000")
        stop_loss = float(input("止损阈值，如 0.05 表示 5% [默认: 0.05]: ").strip() or "0.05")
        take_profit = float(input("止盈阈值，如 0.10 表示 10% [默认: 0.10]: ").strip() or "0.10")
        
        # 交易成本参数
        self.print_info("\n配置交易成本参数:")
        commission_rate = float(input("手续费率，如 0.1 表示 0.1% [默认: 0.1]: ").strip() or "0.1")
        slippage_rate = float(input("滑点率，如 0.05 表示 0.05% [默认: 0.05]: ").strip() or "0.05")
        
        # 计算交易成本预估
        self.print_header("💰 交易成本预估")
        commission = investment_amount * (commission_rate / 100)
        slippage = investment_amount * (slippage_rate / 100)
        stop_loss_cost = investment_amount * stop_loss
        total_commission = commission * 2  # 买入和卖出
        total_slippage = slippage * 2  # 买入和卖出
        total_cost = total_commission + total_slippage + stop_loss_cost
        total_percent = (total_cost / investment_amount * 100) if investment_amount > 0 else 0
        
        self.print_info(f"投资金额: {investment_amount:.2f} USDT")
        self.print_info(f"单笔手续费: {commission:.2f} USDT ({commission_rate}%)")
        self.print_info(f"单笔滑点成本: {slippage:.2f} USDT ({slippage_rate}%)")
        self.print_info(f"止损预估损失: {stop_loss_cost:.2f} USDT ({stop_loss*100:.1f}%)")
        self.print_info(f"最大持仓成本: {max_position:.2f} USDT")
        self.print_info(f"总预估成本(单次完整交易): {total_cost:.2f} USDT ({total_percent:.1f}%)")
        self.print_info("\n说明: 成本基于当前参数预估，实际成本可能因市场波动而变化")

        # 构建配置
        config = {
            "grid_levels": grid_levels,
            "grid_spacing": grid_spacing,
            "threshold": threshold,
            "investment_amount": investment_amount,
            "max_position": max_position,
            "stop_loss_threshold": stop_loss,
            "take_profit_threshold": take_profit,
            "commission_rate": commission_rate / 100,  # 转换为小数
            "slippage_rate": slippage_rate / 100,  # 转换为小数
            "enable_auto_stop": True,
            "dynamic_grid": False,
            "batch_build": False
        }
        
        # 创建机器人
        self.print_info("正在创建机器人...")
        
        bot_data = {
            "name": name,
            "exchange": self.exchange_config_id,
            "trading_pair": trading_pair,
            "strategy": strategy,
            "config": config
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/bots/",
                json=bot_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 201:
                result = response.json()
                self.bot_id = result.get('id')
                self.print_success(f"机器人已创建! (ID: {self.bot_id})")
                self.print_info(f"名称: {name}")
                self.print_info(f"交易对: {trading_pair}")
                self.print_info(f"策略: {strategy}")
                self.print_info(f"投资金额: {investment_amount} USDT")
                return True
            else:
                result = response.json()
                self.print_error(f"创建机器人失败: {result.get('detail', '未知错误')}")
                return False
        except Exception as e:
            self.print_error(f"创建机器人异常: {e}")
            return False
    
    def start_bot(self):
        """启动机器人"""
        self.print_header("步骤 4/4: 启动机器人")
        
        if not self.bot_id:
            self.print_error("机器人ID不存在，无法启动")
            return False
        
        confirm = input(f"确认启动机器人 (ID: {self.bot_id})? (y/N): ").strip().lower()
        if confirm != 'y':
            self.print_info("已取消启动")
            return True
        
        self.print_info("正在启动机器人...")
        
        try:
            response = requests.post(
                f"{API_BASE}/bots/{self.bot_id}/start",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                self.print_success("机器人已启动!")
                self.print_info(f"机器人ID: {self.bot_id}")
                if 'risk_management' in result:
                    rm = result['risk_management']
                    self.print_info(f"最大仓位: {rm.get('max_position')} USDT")
                    self.print_info(f"止损阈值: {rm.get('stop_loss_threshold')}%")
                    self.print_info(f"止盈阈值: {rm.get('take_profit_threshold')}%")
                return True
            else:
                result = response.json()
                self.print_error(f"启动机器人失败: {result.get('detail', '未知错误')}")
                return False
        except Exception as e:
            self.print_error(f"启动机器人异常: {e}")
            return False
    
    def run(self):
        """运行配置流程"""
        print("\n" + "="*60)
        print("  加密货币交易系统 - 快速配置向导")
        print("="*60)
        print("\n此脚本将帮助你:")
        print("  1. 登录系统")
        print("  2. 配置交易所API")
        print("  3. 创建交易机器人")
        print("  4. 启动机器人")
        print("\n请在开始前准备好:")
        print("  - 交易所API Key和Secret")
        print("  - 想要交易的交易对 (如 BTC/USDT)")
        print()
        
        input("按Enter键继续...")
        
        # 执行配置流程
        success = True
        success &= self.login()
        
        if success:
            success &= self.configure_exchange()
        
        if success:
            success &= self.create_bot()
        
        if success:
            success &= self.start_bot()
        
        # 最终结果
        self.print_header("配置完成")
        
        if success:
            self.print_success("所有配置已完成!")
            print("\n下一步操作:")
            print("  1. 访问 http://localhost:8000/static/ultra_minimal.html")
            print("  2. 登录账户")
            print("  3. 查看「机器人状态」监控运行情况")
            print("  4. 查看「市场数据」和「交易记录」")
            print("\n提示: 建议先使用小额资金测试!")
        else:
            self.print_error("配置过程中出现错误")
            print("\n请检查:")
            print("  - 后端服务是否正常运行: ps aux | grep uvicorn")
            print("  - 数据库是否已初始化: python init_db.py")
            print("  - API密钥是否正确")
            print("\n然后重新运行此脚本")
        
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    try:
        setup = QuickSetup()
        setup.run()
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n发生异常: {e}")
        sys.exit(1)
