"""
多因素认证（MFA）服务
使用TOTP（Time-based One-Time Password）实现双因素认证
"""
import pyotp
import qrcode
from io import BytesIO
import base64
import secrets
from typing import Tuple, List, Optional


class MFAService:
    """多因素认证服务"""

    @staticmethod
    def generate_secret() -> str:
        """
        生成MFA密钥

        Returns:
            16字符的base32编码密钥
        """
        return pyotp.random_base32()

    @staticmethod
    def generate_qr_code_url(
        secret: str,
        username: str,
        issuer_name: str = "加密货币交易系统"
    ) -> str:
        """
        生成QR码URL

        Args:
            secret: MFA密钥
            username: 用户名
            issuer_name: 发行者名称

        Returns:
            QR码的URL（用于显示）
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=username,
            issuer_name=issuer_name
        )

    @staticmethod
    def generate_qr_code_image(qr_code_url: str) -> str:
        """
        生成QR码图片的base64编码

        Args:
            qr_code_url: QR码URL

        Returns:
            QR码图片的base64编码字符串
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"

    @staticmethod
    def verify_totp(secret: str, code: str, valid_window: int = 1) -> bool:
        """
        验证TOTP验证码

        Args:
            secret: MFA密钥
            code: 用户输入的6位验证码
            valid_window: 有效时间窗口（前后多少个周期），默认为1（±30秒）

        Returns:
            验证码是否有效
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=valid_window)

    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """
        生成备用验证码

        Args:
            count: 要生成的验证码数量

        Returns:
            备用验证码列表
        """
        return [secrets.token_hex(4).upper() for _ in range(count)]

    @staticmethod
    def verify_backup_code(
        stored_codes: List[str],
        provided_code: str
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        验证备用验证码

        Args:
            stored_codes: 存储的备用验证码列表
            provided_code: 用户提供的验证码

        Returns:
            (是否有效, 剩余的备用验证码列表)
        """
        # 将用户输入的验证码转换为大写并移除空格
        provided_code = provided_code.upper().replace(" ", "")

        if provided_code in stored_codes:
            # 移除已使用的验证码
            remaining_codes = [code for code in stored_codes if code != provided_code]
            return True, remaining_codes

        return False, stored_codes


# 使用示例
if __name__ == "__main__":
    # 1. 生成密钥
    secret = MFAService.generate_secret()
    print(f"MFA密钥: {secret}")

    # 2. 生成QR码URL
    qr_url = MFAService.generate_qr_code_url(secret, "testuser")
    print(f"QR码URL: {qr_url}")

    # 3. 生成QR码图片（base64）
    qr_image = MFAService.generate_qr_code_image(qr_url)
    print(f"QR码图片长度: {len(qr_image)}")

    # 4. 生成TOTP验证码
    totp = pyotp.TOTP(secret)
    current_code = totp.now()
    print(f"当前验证码: {current_code}")

    # 5. 验证验证码
    is_valid = MFAService.verify_totp(secret, current_code)
    print(f"验证码有效: {is_valid}")

    # 6. 生成备用验证码
    backup_codes = MFAService.generate_backup_codes(10)
    print(f"备用验证码: {backup_codes}")
