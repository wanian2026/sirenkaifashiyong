#!/usr/bin/env python3
"""
初始化数据库：创建默认管理员用户
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import User, Base
from app.auth import get_password_hash


def init_database():
    """初始化数据库表结构"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")


def create_admin_user():
    """创建默认管理员用户"""
    db: Session = SessionLocal()

    try:
        # 检查是否已存在admin用户
        existing_admin = db.query(User).filter(User.username == "admin").first()

        if existing_admin:
            print("⚠️  Admin用户已存在，跳过创建")
            return

        # 创建默认管理员用户
        hashed_password = get_password_hash("admin123")
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_password,
            is_active=True,
            role="admin"  # 角色: viewer, trader, admin
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✅ 默认管理员用户创建成功")
        print(f"   用户名: admin")
        print(f"   密码: admin123")
        print(f"   邮箱: admin@example.com")

    except Exception as e:
        db.rollback()
        print(f"❌ 创建admin用户失败: {e}")
        raise
    finally:
        db.close()


def main():
    """主函数"""
    print("="*60)
    print("  数据库初始化脚本")
    print("="*60)
    print()

    # 创建数据库表
    init_database()
    print()

    # 创建默认管理员用户
    create_admin_user()
    print()

    print("="*60)
    print("  初始化完成！")
    print("="*60)


if __name__ == "__main__":
    main()
