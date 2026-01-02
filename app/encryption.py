"""
加密工具模块
使用Fernet对称加密算法加密敏感数据（如API密钥）
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class EncryptionManager:
    """加密管理器"""

    def __init__(self, encryption_key: str = None):
        """
        初始化加密管理器

        Args:
            encryption_key: 加密密钥（可选，默认使用配置中的密钥）
        """
        self.encryption_key = encryption_key or settings.ENCRYPTION_KEY
        self.fernet = self._get_fernet_instance()

    def _get_fernet_instance(self) -> Fernet:
        """
        获取Fernet实例

        Returns:
            Fernet实例
        """
        # 检查密钥长度
        if len(self.encryption_key) != settings.ENCRYPTION_KEY_LENGTH:
            # 如果密钥长度不对，使用PBKDF2HDF生成正确的密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'crypto_bot_salt',  # 固定salt（生产环境应该使用随机salt）
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
            self.fernet = Fernet(key)
        else:
            self.fernet = Fernet(self.encryption_key.encode())

        return self.fernet

    def encrypt(self, plaintext: str) -> str:
        """
        加密文本

        Args:
            plaintext: 明文

        Returns:
            加密后的密文（base64编码）
        """
        try:
            if not plaintext:
                return ""

            encrypted_bytes = self.fernet.encrypt(plaintext.encode())
            encrypted_text = base64.urlsafe_b64encode(encrypted_bytes).decode()
            return encrypted_text
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        解密文本

        Args:
            ciphertext: 密文（base64编码）

        Returns:
            解密后的明文
        """
        try:
            if not ciphertext:
                return ""

            encrypted_bytes = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            decrypted_text = decrypted_bytes.decode()
            return decrypted_text
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise

    def encrypt_dict(self, data: dict, fields: list) -> dict:
        """
        加密字典中的指定字段

        Args:
            data: 原始字典
            fields: 需要加密的字段列表

        Returns:
            加密后的字典
        """
        encrypted_data = data.copy()

        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))

        return encrypted_data

    def decrypt_dict(self, data: dict, fields: list) -> dict:
        """
        解密字典中的指定字段

        Args:
            data: 加密的字典
            fields: 需要解密的字段列表

        Returns:
            解密后的字典
        """
        decrypted_data = data.copy()

        for field in fields:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = self.decrypt(decrypted_data[field])

        return decrypted_data

    def encrypt_api_keys(self, api_key: str, api_secret: str) -> tuple:
        """
        加密API密钥对

        Args:
            api_key: API密钥
            api_secret: API密钥密钥

        Returns:
            (加密的api_key, 加密的api_secret)
        """
        encrypted_key = self.encrypt(api_key) if api_key else ""
        encrypted_secret = self.encrypt(api_secret) if api_secret else ""

        return encrypted_key, encrypted_secret

    def decrypt_api_keys(self, encrypted_key: str, encrypted_secret: str) -> tuple:
        """
        解密API密钥对

        Args:
            encrypted_key: 加密的API密钥
            encrypted_secret: 加密的API密钥密钥

        Returns:
            (api_key, api_secret)
        """
        api_key = self.decrypt(encrypted_key) if encrypted_key else ""
        api_secret = self.decrypt(encrypted_secret) if encrypted_secret else ""

        return api_key, api_secret


# 全局加密管理器实例
encryption_manager = EncryptionManager()


def generate_encryption_key() -> str:
    """
    生成新的加密密钥

    Returns:
        44字符的Fernet密钥（base64编码）
    """
    key = Fernet.generate_key()
    return key.decode()


def is_encrypted(text: str) -> bool:
    """
    检查文本是否已加密

    Args:
        text: 要检查的文本

    Returns:
        是否已加密
    """
    try:
        # 尝试解码base64
        decoded = base64.urlsafe_b64decode(text.encode())
        # 尝试解密
        encryption_manager.fernet.decrypt(decoded)
        return True
    except Exception:
        return False
