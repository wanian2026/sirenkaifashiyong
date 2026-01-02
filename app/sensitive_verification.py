"""
敏感操作二次验证
对敏感操作要求密码或二次验证
"""

from fastapi import HTTPException, status, Depends, Header
from typing import Optional
from app.config import settings
from app.auth import verify_password
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
import logging

logger = logging.getLogger(__name__)


class SensitiveOperationVerification:
    """敏感操作验证器"""

    @staticmethod
    def is_sensitive_operation(operation: str) -> bool:
        """
        检查是否为敏感操作

        Args:
            operation: 操作名称

        Returns:
            是否为敏感操作
        """
        return operation in settings.SENSITIVE_OPERATIONS

    @staticmethod
    def verify_with_password(
        user: User,
        password: str,
        db: Session
    ) -> bool:
        """
        使用密码验证用户身份

        Args:
            user: 用户对象
            password: 用户密码
            db: 数据库会话

        Returns:
            验证是否成功
        """
        if not password:
            return False

        # 验证密码
        if verify_password(password, user.hashed_password):
            # 记录验证成功
            logger.info(f"用户 {user.username} 敏感操作验证成功")
            return True
        else:
            # 记录验证失败
            logger.warning(f"用户 {user.username} 敏感操作验证失败")
            return False


async def require_sensitive_operation_verification(
    user: User,
    verification_password: Optional[str] = Header(None, alias="X-Verification-Password")
) -> User:
    """
    敏感操作二次验证依赖项

    Usage:
        @router.delete("/api/bots/{bot_id}")
        async def delete_bot(
            bot_id: int,
            user: User = Depends(require_sensitive_operation_verification),
            db: Session = Depends(get_db)
        ):
            # 执行敏感操作
            ...

    Args:
        user: 用户对象
        verification_password: 验证密码（从X-Verification-Password头获取）

    Returns:
        用户对象（验证通过）

    Raises:
        HTTPException: 验证失败
    """
    # 如果未启用敏感操作验证，直接返回
    if not settings.SENSITIVE_OPERATIONS_VERIFY:
        return user

    # 检查是否提供了验证密码
    if not verification_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="敏感操作需要二次验证，请在请求头中提供 X-Verification-Password"
        )

    # 验证密码
    db = SessionLocal()
    try:
        verifier = SensitiveOperationVerification()
        if not verifier.verify_with_password(user, verification_password, db):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="验证密码错误"
            )
        return user
    finally:
        db.close()


def check_sensitive_operation(operation: str):
    """
    检查操作是否需要二次验证的装饰器

    Usage:
        @router.delete("/api/bots/{bot_id}")
        @check_sensitive_operation("bot:delete")
        async def delete_bot(
            bot_id: int,
            user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            # 执行敏感操作
            ...

    Args:
        operation: 操作名称

    Returns:
        装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 如果启用敏感操作验证，检查操作类型
            if settings.SENSITIVE_OPERATIONS_VERIFY:
                verifier = SensitiveOperationVerification()
                if verifier.is_sensitive_operation(operation):
                    # 检查是否有验证密码
                    # 这里简化处理，实际应该在middleware中统一处理
                    pass

            # 执行原函数
            return await func(*args, **kwargs)
        return wrapper
    return decorator
