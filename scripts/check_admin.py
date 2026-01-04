#!/usr/bin/env python3
"""
检查admin用户信息
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.auth import verify_password, get_password_hash


def check_admin_user():
    """检查admin用户"""
    db: Session = SessionLocal()

    try:
        # 查询admin用户
        admin_user = db.query(User).filter(User.username == "admin").first()

        if not admin_user:
            print("❌ Admin用户不存在")
            return

        print("="*60)
        print("  Admin用户信息")
        print("="*60)
        print(f"用户ID: {admin_user.id}")
        print(f"用户名: {admin_user.username}")
        print(f"邮箱: {admin_user.email}")
        print(f"角色: {admin_user.role}")
        print(f"是否激活: {admin_user.is_active}")
        print(f"创建时间: {admin_user.created_at}")
        print(f"密码哈希: {admin_user.hashed_password[:50]}...")
        print("="*60)
        print()

        # 测试密码验证
        test_password = "admin123"
        print(f"测试密码: {test_password}")
        print(f"验证结果: ", end="")

        if verify_password(test_password, admin_user.hashed_password):
            print("✅ 密码正确")
        else:
            print("❌ 密码错误")

        print()

        # 如果密码错误，询问是否重置
        if not verify_password(test_password, admin_user.hashed_password):
            print("建议：删除现有admin用户并重新创建")
            print("运行命令：")
            print("  1. 删除admin用户:")
            print("     db.query(User).filter(User.username == 'admin').delete()")
            print("     db.commit()")
            print("  2. 重新运行: python scripts/init_db.py")

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_admin_user()
