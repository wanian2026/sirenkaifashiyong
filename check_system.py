#!/usr/bin/env python3
"""
系统状态检查脚本
检查系统是否可以正常运行
"""

import requests
import subprocess
import sys


def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_success(text):
    print(f"✅ {text}")


def print_error(text):
    print(f"❌ {text}")


def print_info(text):
    print(f"ℹ️  {text}")


def check_backend_service():
    """检查后端服务"""
    print_section("1. 检查后端服务")
    
    try:
        # 检查进程
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        
        if "uvicorn" in result.stdout and "app.main:app" in result.stdout:
            print_success("后端服务进程正在运行")
        else:
            print_error("后端服务进程未找到")
            return False
        
        # 检查端口
        result = subprocess.run(
            ["lsof", "-i", ":8000"],
            capture_output=True,
            text=True
        )
        
        if "LISTEN" in result.stdout:
            print_success("后端服务正在监听8000端口")
        else:
            print_error("后端服务未监听8000端口")
            return False
        
        # 检查API健康
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print_success("API健康检查通过")
        else:
            print_error(f"API健康检查失败: {response.status_code}")
            return False
        
        return True
    
    except Exception as e:
        print_error(f"检查后端服务异常: {e}")
        return False


def check_database():
    """检查数据库"""
    print_section("2. 检查数据库")
    
    try:
        # 检查数据库文件
        result = subprocess.run(
            ["ls", "-la", "*.db"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("找到数据库文件")
            for line in result.stdout.split('\n'):
                if line.endswith('.db'):
                    print_info(f"  {line}")
        else:
            print_error("未找到数据库文件")
            return False
        
        # 检查数据库表
        result = subprocess.run(
            ["sqlite3", "trading.db", ".tables"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            tables = result.stdout.strip().split()
            print_success(f"数据库包含 {len(tables)} 个表")
            print_info(f"  表: {', '.join(tables)}")
        else:
            print_error("无法读取数据库表")
            return False
        
        return True
    
    except Exception as e:
        print_error(f"检查数据库异常: {e}")
        return False


def check_auth():
    """检查认证功能"""
    print_section("3. 检查认证功能")
    
    try:
        # 尝试登录
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            data={"username": "admin", "password": "admin123"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print_success("认证功能正常")
                print_info(f"  Token类型: {data.get('token_type', 'bearer')}")
                return True
            else:
                print_error("登录响应缺少access_token")
                return False
        else:
            print_error(f"登录失败: {response.status_code}")
            print_info(f"  {response.text}")
            return False
    
    except Exception as e:
        print_error(f"检查认证异常: {e}")
        return False


def check_api_endpoints():
    """检查API端点"""
    print_section("4. 检查关键API端点")
    
    # 先获取token
    try:
        login_response = requests.post(
            "http://localhost:8000/api/auth/login",
            data={"username": "admin", "password": "admin123"},
            timeout=5
        )
        
        if login_response.status_code != 200:
            print_error("无法获取认证token")
            return False
        
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
    except Exception as e:
        print_error(f"获取token异常: {e}")
        return False
    
    endpoints = [
        ("交易所配置", "/api/exchanges"),
        ("机器人列表", "/api/bots"),
        ("交易记录", "/api/trades/recent"),
        ("订单管理", "/api/orders"),
    ]
    
    all_ok = True
    for name, endpoint in endpoints:
        try:
            response = requests.get(
                f"http://localhost:8000{endpoint}",
                headers=headers,
                timeout=5
            )
            
            if response.status_code in [200, 404]:  # 404表示路由存在但没有数据
                print_success(f"{name}: 正常")
            else:
                print_error(f"{name}: 异常 ({response.status_code})")
                all_ok = False
        except Exception as e:
            print_error(f"{name}: 异常 ({e})")
            all_ok = False
    
    return all_ok


def check_dependencies():
    """检查依赖包"""
    print_section("5. 检查关键依赖包")
    
    packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "ccxt",
        "requests",
        "pydantic",
        "langchain",
        "langgraph",
    ]
    
    all_ok = True
    for package in packages:
        try:
            __import__(package)
            print_success(f"{package}: 已安装")
        except ImportError:
            print_error(f"{package}: 未安装")
            all_ok = False
    
    return all_ok


def check_static_files():
    """检查静态文件"""
    print_section("6. 检查前端文件")
    
    try:
        result = subprocess.run(
            ["ls", "-la", "static/"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("静态文件目录存在")
            if "ultra_minimal.html" in result.stdout:
                print_success("ultra_minimal.html 存在")
            else:
                print_error("ultra_minimal.html 不存在")
                return False
        else:
            print_error("静态文件目录不存在")
            return False
        
        return True
    
    except Exception as e:
        print_error(f"检查静态文件异常: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  加密货币交易系统 - 系统状态检查")
    print("="*60)
    
    checks = [
        ("后端服务", check_backend_service),
        ("数据库", check_database),
        ("认证功能", check_auth),
        ("API端点", check_api_endpoints),
        ("依赖包", check_dependencies),
        ("前端文件", check_static_files),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"{name}检查异常: {e}")
            results[name] = False
    
    # 总结
    print_section("检查结果总结")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 项通过")
    
    if passed == total:
        print_success("所有检查通过，系统状态良好!")
        print("\n下一步:")
        print("  1. 运行快速配置: python quick_setup.py")
        print("  2. 或者手动配置交易所和机器人")
        return 0
    else:
        print_error("部分检查未通过，请修复上述问题")
        print("\n常见解决方案:")
        print("  - 后端服务未运行: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        print("  - 数据库未初始化: python init_db.py")
        print("  - 依赖包缺失: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        sys.exit(0)
