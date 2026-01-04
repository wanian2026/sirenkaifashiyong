#!/usr/bin/env python3
"""
更新admin用户的角色为admin
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User


def update_admin_role():
    """更新admin用户的角色"""
    db: Session = SessionLocal()

    try:
        # 查询admin用户
        admin_user = db.query(User).filter(User.username == "admin").first()

        if not admin_user:
            print("❌ Admin用户不存在")
            return

        print("="*60)
        print("  更新Admin用户角色")
        print("="*60)
        print(f"当前角色: {admin_user.role}")

        # 更新角色为admin
        admin_user.role = "admin"
        db.commit()

        print(f"更新后角色: {admin_user.role}")
        print("✅ Admin用户角色更新成功")
        print("="*60)

    except Exception as e:
        db.rollback()
        print(f"❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    update_admin_role()
