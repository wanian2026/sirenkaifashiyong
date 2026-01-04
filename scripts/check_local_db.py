#!/usr/bin/env python3
"""
检查本地数据库中的admin用户
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User


def check_admin():
    """检查admin用户"""
    db: Session = SessionLocal()

    try:
        # 查询admin用户
        admin_user = db.query(User).filter(User.username == "admin").first()

        if not admin_user:
            print("❌ Admin用户不存在")
            print()
            print("请运行以下命令创建admin用户：")
            print("  python scripts/init_db.py")
            return

        print("="*60)
        print("  Admin用户信息")
        print("="*60)
        print(f"用户ID: {admin_user.id}")
        print(f"用户名: {admin_user.username}")
        print(f"邮箱: {admin_user.email}")
        print(f"角色: {admin_user.role}")
        print(f"是否激活: {admin_user.is_active}")
        print(f"邮箱已验证: {admin_user.email_verified}")
        print(f"MFA已启用: {admin_user.mfa_enabled}")
        print(f"创建时间: {admin_user.created_at}")
        print(f"密码哈希: {admin_user.hashed_password[:50]}...")
        print("="*60)
        print()

        # 测试密码验证
        test_password = "admin123"
        print(f"测试密码: {test_password}")
        print(f"验证结果: ", end="")

        from app.auth import verify_password
        if verify_password(test_password, admin_user.hashed_password):
            print("✅ 密码正确")
        else:
            print("❌ 密码错误")
            print()
            print("建议：重新初始化数据库")
            print("  python scripts/init_db.py")

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_admin()
