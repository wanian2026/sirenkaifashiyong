"""
数据库迁移脚本 - 添加密码重置令牌表和用户认证增强字段
"""
from sqlalchemy import create_engine, text
from app.config import settings
from app.models import Base
from app.database import engine


def migrate_database():
    """执行数据库迁移"""
    print("开始数据库迁移...")

    # 创建所有表（包括新增的表）
    Base.metadata.create_all(bind=engine)

    # 检查并添加用户表的新字段
    with engine.connect() as conn:
        # 检查是否已有MFA相关字段
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]

        # 添加MFA相关字段
        if "mfa_enabled" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT FALSE"))
            print("  ✓ 添加字段: mfa_enabled")

        if "mfa_secret" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN mfa_secret VARCHAR"))
            print("  ✓ 添加字段: mfa_secret")

        if "mfa_backup_codes" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN mfa_backup_codes TEXT"))
            print("  ✓ 添加字段: mfa_backup_codes")

        if "email_verified" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE"))
            print("  ✓ 添加字段: email_verified")

        if "email_verification_token" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN email_verification_token VARCHAR"))
            print("  ✓ 添加字段: email_verification_token")

        if "email_verification_token_expires" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN email_verification_token_expires DATETIME"))
            print("  ✓ 添加字段: email_verification_token_expires")

        conn.commit()

    print("\n数据库迁移完成！")
    print("\n新增表:")
    print("  - password_reset_tokens (密码重置令牌表)")
    print("\n新增字段（users表）:")
    print("  - mfa_enabled (是否启用MFA)")
    print("  - mfa_secret (MFA密钥)")
    print("  - mfa_backup_codes (MFA备用验证码)")
    print("  - email_verified (邮箱是否已验证)")
    print("  - email_verification_token (邮箱验证令牌)")
    print("  - email_verification_token_expires (邮箱验证令牌过期时间)")


if __name__ == "__main__":
    migrate_database()
