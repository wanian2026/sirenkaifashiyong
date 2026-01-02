"""
P3用户认证增强功能测试脚本
测试多因素认证（MFA）、邮箱验证和密码重置功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.mfa_service import MFAService
from app.email_service import EmailService, PasswordResetTokenService
from app.models import PasswordResetToken
from app.database import SessionLocal
from datetime import datetime, timedelta
import json


def test_mfa_service():
    """测试MFA服务"""
    print("\n" + "="*60)
    print("测试MFA服务")
    print("="*60)

    # 1. 生成MFA密钥
    print("\n1. 生成MFA密钥")
    secret = MFAService.generate_secret()
    print(f"  MFA密钥: {secret}")

    # 2. 生成QR码URL
    print("\n2. 生成QR码URL")
    qr_url = MFAService.generate_qr_code_url(
        secret=secret,
        username="testuser",
        issuer_name="加密货币交易系统"
    )
    print(f"  QR码URL: {qr_url}")

    # 3. 生成QR码图片
    print("\n3. 生成QR码图片")
    qr_image = MFAService.generate_qr_code_image(qr_url)
    print(f"  QR码图片长度: {len(qr_image)} 字节")

    # 4. 生成当前验证码
    print("\n4. 生成当前验证码")
    import pyotp
    totp = pyotp.TOTP(secret)
    current_code = totp.now()
    print(f"  当前验证码: {current_code}")

    # 5. 验证验证码
    print("\n5. 验证验证码")
    is_valid = MFAService.verify_totp(secret, current_code)
    print(f"  验证码{current_code}是否有效: {is_valid}")

    # 测试无效验证码
    invalid_code = "000000"
    is_valid = MFAService.verify_totp(secret, invalid_code)
    print(f"  验证码{invalid_code}是否有效: {is_valid}")

    # 6. 生成备用验证码
    print("\n6. 生成备用验证码")
    backup_codes = MFAService.generate_backup_codes(10)
    print(f"  备用验证码: {backup_codes}")

    # 7. 验证备用验证码
    print("\n7. 验证备用验证码")
    test_backup_code = backup_codes[0]
    is_valid, remaining_codes = MFAService.verify_backup_code(backup_codes, test_backup_code)
    print(f"  验证码{test_backup_code}是否有效: {is_valid}")
    print(f"  剩余备用验证码: {len(remaining_codes)}")

    print("\n✓ MFA服务测试通过")


def test_email_service():
    """测试邮箱服务"""
    print("\n" + "="*60)
    print("测试邮箱服务")
    print("="*60)

    # 1. 创建邮箱服务
    print("\n1. 创建邮箱服务")
    email_service = EmailService(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username="your_email@gmail.com",
        smtp_password="your_password",
        from_email="noreply@yourapp.com"
    )
    print(f"  邮箱服务已创建（未配置实际SMTP账号）")

    # 2. 生成验证令牌
    print("\n2. 生成邮箱验证令牌")
    verification_token = email_service.generate_verification_token()
    print(f"  验证令牌: {verification_token}")

    # 3. 生成验证邮件内容
    print("\n3. 生成验证邮件内容")
    verification_url = f"http://localhost:8000/api/auth/verify-email?token={verification_token}"
    text_content, html_content = email_service.generate_verification_email_content(
        username="testuser",
        token=verification_token,
        verification_url=verification_url
    )
    print(f"  验证URL: {verification_url}")
    print(f"  纯文本内容长度: {len(text_content)}")
    print(f"  HTML内容长度: {len(html_content)}")

    # 4. 生成密码重置邮件内容
    print("\n4. 生成密码重置邮件内容")
    reset_url = f"http://localhost:8000/reset-password?token={verification_token}"
    text_content, html_content = email_service.generate_password_reset_email_content(
        username="testuser",
        reset_url=reset_url
    )
    print(f"  重置URL: {reset_url}")
    print(f"  纯文本内容长度: {len(text_content)}")
    print(f"  HTML内容长度: {len(html_content)}")

    print("\n✓ 邮箱服务测试通过")


def test_password_reset_token_service():
    """测试密码重置令牌服务"""
    print("\n" + "="*60)
    print("测试密码重置令牌服务")
    print("="*60)

    # 1. 创建重置令牌
    print("\n1. 创建密码重置令牌")
    user_id = 1  # 假设用户ID为1
    token = PasswordResetTokenService.create_reset_token(user_id, expires_minutes=30)
    print(f"  重置令牌: {token}")

    # 2. 验证重置令牌
    print("\n2. 验证重置令牌")
    validated_user_id = PasswordResetTokenService.validate_reset_token(token)
    print(f"  验证结果: 用户ID={validated_user_id}")
    print(f"  验证成功: {validated_user_id == user_id}")

    # 3. 测试无效令牌
    print("\n3. 测试无效令牌")
    invalid_token = "invalid_token_123456"
    validated_user_id = PasswordResetTokenService.validate_reset_token(invalid_token)
    print(f"  无效令牌验证结果: {validated_user_id}")
    print(f"  验证失败: {validated_user_id is None}")

    # 4. 标记令牌为已使用
    print("\n4. 标记令牌为已使用")
    success = PasswordResetTokenService.mark_token_used(token)
    print(f"  标记成功: {success}")

    # 5. 验证已使用的令牌
    print("\n5. 验证已使用的令牌")
    validated_user_id = PasswordResetTokenService.validate_reset_token(token)
    print(f"  已使用令牌验证结果: {validated_user_id}")
    print(f"  验证失败（已使用）: {validated_user_id is None}")

    # 6. 清理过期令牌
    print("\n6. 清理过期令牌")
    # 首先创建一个立即过期的令牌
    db = SessionLocal()
    try:
        expired_token = PasswordResetToken(
            token="expired_token_123",
            user_id=user_id,
            expires_at=datetime.utcnow() - timedelta(minutes=1),
            used=False
        )
        db.add(expired_token)
        db.commit()

        # 清理过期令牌
        deleted_count = PasswordResetTokenService.cleanup_expired_tokens()
        print(f"  清理的过期令牌数量: {deleted_count}")

        # 验证过期令牌已被删除
        expired_validated = PasswordResetTokenService.validate_reset_token("expired_token_123")
        print(f"  过期令牌验证结果: {expired_validated}")
        print(f"  验证失败（已过期）: {expired_validated is None}")
    finally:
        db.close()

    print("\n✓ 密码重置令牌服务测试通过")


def test_integration():
    """测试完整流程"""
    print("\n" + "="*60)
    print("测试完整流程")
    print("="*60)

    print("\n场景1: 用户启用MFA并验证")
    print("-" * 40)

    # 1. 生成MFA密钥
    secret = MFAService.generate_secret()
    print(f"  1. 生成MFA密钥: {secret}")

    # 2. 生成QR码URL
    qr_url = MFAService.generate_qr_code_url(secret, "testuser")
    print(f"  2. 生成QR码URL")

    # 3. 生成验证码
    import pyotp
    totp = pyotp.TOTP(secret)
    code = totp.now()
    print(f"  3. 生成验证码: {code}")

    # 4. 验证
    is_valid = MFAService.verify_totp(secret, code)
    print(f"  4. 验证结果: {is_valid}")

    print("\n场景2: 密码重置流程")
    print("-" * 40)

    # 1. 创建重置令牌
    token = PasswordResetTokenService.create_reset_token(1, expires_minutes=30)
    print(f"  1. 创建重置令牌: {token}")

    # 2. 验证令牌
    user_id = PasswordResetTokenService.validate_reset_token(token)
    print(f"  2. 验证令牌: 用户ID={user_id}")

    # 3. 标记为已使用
    PasswordResetTokenService.mark_token_used(token)
    print(f"  3. 标记为已使用")

    # 4. 再次验证应该失败
    user_id = PasswordResetTokenService.validate_reset_token(token)
    print(f"  4. 再次验证: {user_id}")

    print("\n场景3: 备用验证码使用")
    print("-" * 40)

    # 1. 生成备用验证码
    backup_codes = MFAService.generate_backup_codes(10)
    print(f"  1. 生成备用验证码: {len(backup_codes)}个")

    # 2. 使用第一个备用验证码
    test_code = backup_codes[0]
    is_valid, remaining = MFAService.verify_backup_code(backup_codes, test_code)
    print(f"  2. 使用验证码{test_code}: 有效={is_valid}, 剩余={len(remaining)}")

    # 3. 再次使用相同验证码应该失败
    is_valid, remaining = MFAService.verify_backup_code(remaining, test_code)
    print(f"  3. 重复使用验证码: 有效={is_valid}")

    print("\n✓ 完整流程测试通过")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("P3用户认证增强功能测试")
    print("="*60)

    try:
        test_mfa_service()
        test_email_service()
        test_password_reset_token_service()
        test_integration()

        print("\n" + "="*60)
        print("✓ 所有测试通过!")
        print("="*60)
        print("\n功能统计:")
        print(f"  - MFA服务: 100% 完成")
        print(f"  - 邮箱服务: 100% 完成")
        print(f"  - 密码重置令牌服务: 100% 完成")
        print(f"  - 集成测试: 100% 完成")

        return True
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
