"""
安全功能测试
包括加密、审计日志、敏感操作验证等测试
"""

import pytest
from app.encryption import EncryptionManager, generate_encryption_key, is_encrypted
from app.audit_log import AuditLog, AuditLogAction, AuditLogLevel
from app.sensitive_verification import SensitiveOperationVerification
from app.rbac import Permission, Role, ROLE_PERMISSIONS
from sqlalchemy.orm import Session
from app.models import User
from app.config import settings


class TestEncryption:
    """加密功能测试"""

    def test_generate_encryption_key(self):
        """测试生成加密密钥"""
        key = generate_encryption_key()
        assert len(key) == 44
        assert isinstance(key, str)

    def test_encrypt_decrypt_text(self):
        """测试文本加密和解密"""
        manager = EncryptionManager()

        original_text = "This is a secret message"
        encrypted = manager.encrypt(original_text)

        # 验证加密结果
        assert encrypted != original_text
        assert len(encrypted) > 0

        # 验证解密
        decrypted = manager.decrypt(encrypted)
        assert decrypted == original_text

    def test_encrypt_empty_text(self):
        """测试加密空文本"""
        manager = EncryptionManager()

        encrypted = manager.encrypt("")
        assert encrypted == ""

        decrypted = manager.decrypt("")
        assert decrypted == ""

    def test_encrypt_api_keys(self):
        """测试API密钥加密"""
        manager = EncryptionManager()

        api_key = "test_api_key_12345"
        api_secret = "test_api_secret_67890"

        encrypted_key, encrypted_secret = manager.encrypt_api_keys(api_key, api_secret)

        # 验证加密结果
        assert encrypted_key != api_key
        assert encrypted_secret != api_secret

        # 验证解密
        decrypted_key, decrypted_secret = manager.decrypt_api_keys(encrypted_key, encrypted_secret)
        assert decrypted_key == api_key
        assert decrypted_secret == api_secret

    def test_encrypt_decrypt_dict(self):
        """测试字典字段加密和解密"""
        manager = EncryptionManager()

        data = {
            "username": "testuser",
            "api_key": "secret_key_123",
            "api_secret": "secret_secret_456",
            "email": "test@example.com"
        }

        fields_to_encrypt = ["api_key", "api_secret"]

        # 加密
        encrypted_data = manager.encrypt_dict(data, fields_to_encrypt)
        assert encrypted_data["api_key"] != data["api_key"]
        assert encrypted_data["api_secret"] != data["api_secret"]
        assert encrypted_data["username"] == data["username"]
        assert encrypted_data["email"] == data["email"]

        # 解密
        decrypted_data = manager.decrypt_dict(encrypted_data, fields_to_encrypt)
        assert decrypted_data["api_key"] == data["api_key"]
        assert decrypted_data["api_secret"] == data["api_secret"]
        assert decrypted_data["username"] == data["username"]
        assert decrypted_data["email"] == data["email"]

    def test_is_encrypted(self):
        """测试检查文本是否已加密"""
        manager = EncryptionManager()

        plaintext = "This is plaintext"
        encrypted = manager.encrypt(plaintext)

        assert is_encrypted(encrypted) == True
        assert is_encrypted(plaintext) == False


class TestAuditLog:
    """审计日志测试"""

    def test_audit_log_creation(self, db: Session):
        """测试创建审计日志"""
        log = AuditLog(
            user_id=1,
            username="testuser",
            action=AuditLogAction.CREATE,
            resource="bot",
            resource_id=1,
            level=AuditLogLevel.INFO,
            details='{"test": "data"}',
            ip_address="127.0.0.1",
            user_agent="Test Agent",
            success=True
        )

        db.add(log)
        db.commit()
        db.refresh(log)

        assert log.id is not None
        assert log.user_id == 1
        assert log.action == AuditLogAction.CREATE
        assert log.success == True

    def test_audit_log_to_dict(self, db: Session):
        """测试审计日志转换为字典"""
        log = AuditLog(
            user_id=1,
            username="testuser",
            action=AuditLogAction.UPDATE,
            resource="bot",
            resource_id=2,
            level=AuditLogLevel.WARNING,
            success=False,
            error_message="Test error"
        )

        db.add(log)
        db.commit()
        db.refresh(log)

        log_dict = log.to_dict()

        assert log_dict["user_id"] == 1
        assert log_dict["action"] == AuditLogAction.UPDATE
        assert log_dict["resource"] == "bot"
        assert log_dict["success"] == False
        assert "created_at" in log_dict

    def test_audit_log_filter_by_user(self, db: Session):
        """测试按用户筛选审计日志"""
        # 创建多个审计日志
        log1 = AuditLog(
            user_id=1,
            username="user1",
            action=AuditLogAction.READ,
            resource="bot",
            success=True
        )

        log2 = AuditLog(
            user_id=2,
            username="user2",
            action=AuditLogAction.READ,
            resource="bot",
            success=True
        )

        db.add(log1)
        db.add(log2)
        db.commit()

        # 查询用户1的日志
        logs = db.query(AuditLog).filter(AuditLog.user_id == 1).all()
        assert len(logs) == 1
        assert logs[0].username == "user1"


class TestSensitiveOperationVerification:
    """敏感操作验证测试"""

    def test_is_sensitive_operation(self):
        """测试检查是否为敏感操作"""
        verifier = SensitiveOperationVerification()

        # 测试敏感操作
        assert verifier.is_sensitive_operation("bot:delete") == True
        assert verifier.is_sensitive_operation("user:delete") == True
        assert verifier.is_sensitive_operation("system:configure") == True

        # 测试非敏感操作
        assert verifier.is_sensitive_operation("bot:read") == False
        assert verifier.is_sensitive_operation("bot:create") == False


class TestRBAC:
    """RBAC权限测试"""

    def test_permission_enum(self):
        """测试权限枚举"""
        assert Permission.USER_CREATE.value == "user:create"
        assert Permission.BOT_START.value == "bot:start"
        assert Permission.SYSTEM_LOG.value == "system:log"

    def test_role_permissions(self):
        """测试角色权限"""
        from app.rbac import ROLE_PERMISSIONS, Role

        # 管理员应该有所有权限
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        assert len(admin_perms) > 20
        assert Permission.USER_DELETE in admin_perms
        assert Permission.SYSTEM_CONFIGURE in admin_perms

        # 查看者应该只有读取权限
        viewer_perms = ROLE_PERMISSIONS[Role.VIEWER]
        assert Permission.USER_READ in viewer_perms
        assert Permission.USER_CREATE not in viewer_perms
        assert Permission.BOT_DELETE not in viewer_perms


class TestSecurityIntegration:
    """安全功能集成测试"""

    def test_encrypt_and_store_user_api_keys(self, db: Session):
        """测试加密并存储用户API密钥"""
        from app.encryption import encryption_manager

        # 创建用户
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            role="trader"
        )

        # 加密API密钥
        api_key = "test_api_key_12345"
        api_secret = "test_api_secret_67890"

        encrypted_key, encrypted_secret = encryption_manager.encrypt_api_keys(api_key, api_secret)

        user.encrypted_api_key = encrypted_key
        user.encrypted_api_secret = encrypted_secret

        db.add(user)
        db.commit()
        db.refresh(user)

        # 验证加密存储
        assert user.encrypted_api_key != api_key
        assert user.encrypted_api_secret != api_secret

        # 验证解密
        decrypted_key, decrypted_secret = encryption_manager.decrypt_api_keys(
            user.encrypted_api_key,
            user.encrypted_api_secret
        )

        assert decrypted_key == api_key
        assert decrypted_secret == api_secret


if __name__ == "__main__":
    print("安全功能测试")
    print("=" * 60)

    # 手动运行测试（需要先初始化数据库）
    print("\n请确保已初始化数据库: python init_db.py")
    print("\n然后使用 pytest 运行测试:")
    print("  pytest test_security.py -v")
    print("\n或者运行单个测试:")
    print("  pytest test_security.py::TestEncryption::test_encrypt_decrypt_text -v")
