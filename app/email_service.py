"""
邮箱验证服务
用于发送邮箱验证邮件和密码重置邮件
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from app.models import PasswordResetToken
from app.database import SessionLocal
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template


class EmailService:
    """邮箱服务"""

    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        use_tls: bool = True
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.use_tls = use_tls

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        发送邮件

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML内容
            text_content: 纯文本内容（可选）

        Returns:
            是否发送成功
        """
        if not self.smtp_username or not self.smtp_password:
            print("警告：未配置SMTP账号，邮件未发送")
            return False

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # 添加纯文本内容
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)

            # 添加HTML内容
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)

            # 发送邮件
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()

            return True
        except Exception as e:
            print(f"发送邮件失败: {str(e)}")
            return False

    def generate_verification_token(self) -> str:
        """
        生成邮箱验证令牌

        Returns:
            验证令牌
        """
        return secrets.token_urlsafe(32)

    def generate_verification_email_content(
        self,
        username: str,
        token: str,
        verification_url: str
    ) -> tuple[str, str]:
        """
        生成邮箱验证邮件内容

        Args:
            username: 用户名
            token: 验证令牌
            verification_url: 验证URL

        Returns:
            (纯文本内容, HTML内容)
        """
        # 纯文本内容
        text_content = f"""
你好 {username}，

感谢您注册加密货币交易系统！

请点击以下链接验证您的邮箱：
{verification_url}

如果链接无法点击，请复制以下URL到浏览器中：
{verification_url}

此链接将在24小时后过期。

如果您没有注册我们的服务，请忽略此邮件。

祝好！
加密货币交易系统团队
"""

        # HTML内容
        html_template = Template('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>邮箱验证</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #4CAF50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .button {
            display: inline-block;
            padding: 12px 24px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin: 20px 0;
        }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>邮箱验证</h1>
        </div>
        <div class="content">
            <p>你好 {{ username }}，</p>
            <p>感谢您注册加密货币交易系统！</p>
            <p>请点击以下按钮验证您的邮箱：</p>
            <div style="text-align: center;">
                <a href="{{ verification_url }}" class="button">验证邮箱</a>
            </div>
            <p>如果按钮无法点击，请复制以下URL到浏览器中：</p>
            <p style="word-break: break-all; color: #666;">{{ verification_url }}</p>
            <p style="color: #666;">此链接将在24小时后过期。</p>
            <p>如果您没有注册我们的服务，请忽略此邮件。</p>
        </div>
        <div class="footer">
            <p>祝好！</p>
            <p>加密货币交易系统团队</p>
        </div>
    </div>
</body>
</html>
''')

        html_content = html_template.render(
            username=username,
            verification_url=verification_url
        )

        return text_content, html_content

    def generate_password_reset_email_content(
        self,
        username: str,
        reset_url: str
    ) -> tuple[str, str]:
        """
        生成密码重置邮件内容

        Args:
            username: 用户名
            reset_url: 重置URL

        Returns:
            (纯文本内容, HTML内容)
        """
        # 纯文本内容
        text_content = f"""
你好 {username}，

我们收到了您的密码重置请求。

请点击以下链接重置您的密码：
{reset_url}

如果链接无法点击，请复制以下URL到浏览器中：
{reset_url}

此链接将在30分钟后过期。

如果您没有请求重置密码，请忽略此邮件。

祝好！
加密货币交易系统团队
"""

        # HTML内容
        html_template = Template('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>密码重置</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #f44336; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .button {
            display: inline-block;
            padding: 12px 24px;
            background: #f44336;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin: 20px 0;
        }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>密码重置</h1>
        </div>
        <div class="content">
            <p>你好 {{ username }}，</p>
            <p>我们收到了您的密码重置请求。</p>
            <p>请点击以下按钮重置您的密码：</p>
            <div style="text-align: center;">
                <a href="{{ reset_url }}" class="button">重置密码</a>
            </div>
            <p>如果按钮无法点击，请复制以下URL到浏览器中：</p>
            <p style="word-break: break-all; color: #666;">{{ reset_url }}</p>
            <p style="color: #666;">此链接将在30分钟后过期。</p>
            <p>如果您没有请求重置密码，请忽略此邮件。</p>
        </div>
        <div class="footer">
            <p>祝好！</p>
            <p>加密货币交易系统团队</p>
        </div>
    </div>
</body>
</html>
''')

        html_content = html_template.render(
            username=username,
            reset_url=reset_url
        )

        return text_content, html_content


class PasswordResetTokenService:
    """密码重置令牌服务"""

    @staticmethod
    def create_reset_token(user_id: int, expires_minutes: int = 30) -> str:
        """
        创建密码重置令牌

        Args:
            user_id: 用户ID
            expires_minutes: 过期时间（分钟）

        Returns:
            重置令牌
        """
        db = SessionLocal()
        try:
            # 生成令牌
            token = secrets.token_urlsafe(32)

            # 计算过期时间
            expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

            # 保存令牌到数据库
            reset_token = PasswordResetToken(
                token=token,
                user_id=user_id,
                expires_at=expires_at,
                used=False
            )
            db.add(reset_token)
            db.commit()

            return token
        finally:
            db.close()

    @staticmethod
    def validate_reset_token(token: str) -> Optional[int]:
        """
        验证密码重置令牌

        Args:
            token: 重置令牌

        Returns:
            如果有效，返回用户ID；否则返回None
        """
        db = SessionLocal()
        try:
            # 查找令牌
            reset_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token,
                PasswordResetToken.used == False,
                PasswordResetToken.expires_at > datetime.utcnow()
            ).first()

            if not reset_token:
                return None

            return reset_token.user_id
        finally:
            db.close()

    @staticmethod
    def mark_token_used(token: str) -> bool:
        """
        标记令牌为已使用

        Args:
            token: 重置令牌

        Returns:
            是否成功标记
        """
        db = SessionLocal()
        try:
            reset_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()

            if not reset_token:
                return False

            reset_token.used = True
            db.commit()

            return True
        finally:
            db.close()

    @staticmethod
    def cleanup_expired_tokens() -> int:
        """
        清理过期的令牌

        Returns:
            清理的令牌数量
        """
        db = SessionLocal()
        try:
            deleted_count = db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at < datetime.utcnow()
            ).delete()

            db.commit()
            return deleted_count
        finally:
            db.close()


# 使用示例
if __name__ == "__main__":
    # 1. 创建邮箱服务（需要配置SMTP）
    email_service = EmailService(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username="your_email@gmail.com",
        smtp_password="your_app_password",
        from_email="noreply@yourapp.com"
    )

    # 2. 生成验证令牌
    verification_token = email_service.generate_verification_token()
    print(f"验证令牌: {verification_token}")

    # 3. 生成邮件内容
    verification_url = f"http://localhost:8000/api/auth/verify-email?token={verification_token}"
    text_content, html_content = email_service.generate_verification_email_content(
        username="testuser",
        token=verification_token,
        verification_url=verification_url
    )

    print("纯文本内容:")
    print(text_content)
    print("\nHTML内容:")
    print(html_content[:200] + "...")

    # 4. 创建密码重置令牌
    reset_token = PasswordResetTokenService.create_reset_token(user_id=1)
    print(f"\n重置令牌: {reset_token}")

    # 5. 验证重置令牌
    user_id = PasswordResetTokenService.validate_reset_token(reset_token)
    print(f"验证结果: {user_id}")
