from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import verify_password, get_password_hash, create_access_token, verify_token
from app.schemas import (
    UserCreate, UserResponse, Token, PasswordChange, PasswordReset, PasswordResetConfirm,
    UserUpdate, MFAEnableRequest, MFAEnableResponse, MFAVerifyRequest,
    MFADisableRequest, EmailVerifyRequest, EmailResendRequest
)
from app.mfa_service import MFAService
from app.email_service import EmailService, PasswordResetTokenService
from datetime import datetime, timedelta
from app.config import settings
from typing import Optional
import secrets
import json

router = APIRouter()


async def get_current_user_from_token(token: str, db: Session):
    """从 token 获取当前用户"""
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
        )

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证密码
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str,
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    user = await get_current_user_from_token(token, db)
    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    token: str,
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    user = await get_current_user_from_token(token, db)

    if user_update.email:
        # 检查邮箱是否已被使用
        existing_email = db.query(User).filter(
            User.email == user_update.email,
            User.id != user.id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
        user.email = user_update.email

    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    token: str,
    db: Session = Depends(get_db)
):
    """修改密码"""
    user = await get_current_user_from_token(token, db)

    # 验证旧密码
    if not verify_password(password_change.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    # 更新密码
    user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()

    return {"message": "密码修改成功"}


@router.post("/reset-password")
async def request_password_reset(
    password_reset: PasswordReset,
    db: Session = Depends(get_db)
):
    """请求重置密码"""
    user = db.query(User).filter(User.email == password_reset.email).first()

    if not user:
        # 不暴露用户是否存在，返回成功消息
        return {"message": "如果邮箱存在，重置链接已发送"}

    # 创建重置令牌
    reset_token = PasswordResetTokenService.create_reset_token(
        user_id=user.id,
        expires_minutes=30
    )

    # 创建邮箱服务
    email_service = EmailService(
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        smtp_username=settings.SMTP_USERNAME,
        smtp_password=settings.SMTP_PASSWORD,
        from_email=settings.SMTP_FROM_EMAIL
    )

    # 生成重置URL
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    # 生成邮件内容
    text_content, html_content = email_service.generate_password_reset_email_content(
        username=user.username,
        reset_url=reset_url
    )

    # 发送邮件
    email_service.send_email(
        to_email=user.email,
        subject="重置您的密码 - 加密货币交易系统",
        html_content=html_content,
        text_content=text_content
    )

    return {
        "message": "重置邮件已发送",
        "note": "请检查您的邮箱，包含重置密码的链接"
    }


@router.post("/reset-password/confirm")
async def confirm_password_reset(
    password_reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """确认重置密码"""
    # 验证重置令牌
    user_id = PasswordResetTokenService.validate_reset_token(password_reset_confirm.token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效或已过期的重置令牌"
        )

    # 获取用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 更新密码
    user.hashed_password = get_password_hash(password_reset_confirm.new_password)
    db.commit()

    # 标记令牌为已使用
    PasswordResetTokenService.mark_token_used(password_reset_confirm.token)

    return {"message": "密码重置成功"}


# ==================== MFA相关端点 ====================

@router.post("/mfa/enable", response_model=MFAEnableResponse)
async def enable_mfa(
    request: MFAEnableRequest,
    token: str,
    db: Session = Depends(get_db)
):
    """启用多因素认证（MFA）"""
    # 获取当前用户
    user = await get_current_user_from_token(token, db)

    # 验证密码
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码错误"
        )

    # 如果已经启用MFA，返回错误
    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA已启用"
        )

    # 生成MFA密钥
    secret = MFAService.generate_secret()

    # 生成备用验证码
    backup_codes = MFAService.generate_backup_codes(10)

    # 生成QR码URL
    qr_code_url = MFAService.generate_qr_code_url(
        secret=secret,
        username=user.username,
        issuer_name="加密货币交易系统"
    )

    # 生成QR码图片（base64）
    qr_code_image = MFAService.generate_qr_code_image(qr_code_url)

    # 保存MFA信息到数据库（但暂不启用）
    user.mfa_secret = secret
    user.mfa_backup_codes = json.dumps(backup_codes)
    db.commit()

    return MFAEnableResponse(
        secret=secret,
        qr_code_url=qr_code_image,
        backup_codes=backup_codes
    )


@router.post("/mfa/verify")
async def verify_mfa(
    request: MFAVerifyRequest,
    token: str,
    db: Session = Depends(get_db)
):
    """验证MFA代码并启用MFA"""
    # 获取当前用户
    user = await get_current_user_from_token(token, db)

    # 如果MFA已经启用，返回错误
    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA已启用"
        )

    # 验证MFA代码
    if not user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA未初始化"
        )

    is_valid = MFAService.verify_totp(user.mfa_secret, request.code)

    # 检查是否是备用验证码
    if not is_valid and user.mfa_backup_codes:
        backup_codes = json.loads(user.mfa_backup_codes)
        is_valid, remaining_codes = MFAService.verify_backup_code(backup_codes, request.code)
        if is_valid:
            user.mfa_backup_codes = json.dumps(remaining_codes)
            db.commit()

    if is_valid:
        # 启用MFA
        user.mfa_enabled = True
        db.commit()

        return {"message": "MFA已启用"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的验证码"
        )


@router.post("/mfa/disable")
async def disable_mfa(
    request: MFADisableRequest,
    token: str,
    db: Session = Depends(get_db)
):
    """禁用多因素认证（MFA）"""
    # 获取当前用户
    user = await get_current_user_from_token(token, db)

    # 验证密码
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码错误"
        )

    # 禁用MFA
    user.mfa_enabled = False
    user.mfa_secret = None
    user.mfa_backup_codes = None
    db.commit()

    return {"message": "MFA已禁用"}


# ==================== 邮箱验证相关端点 ====================

@router.post("/verify-email")
async def verify_email(
    request: EmailVerifyRequest,
    db: Session = Depends(get_db)
):
    """验证邮箱"""
    # 查找用户
    user = db.query(User).filter(
        User.email_verification_token == request.token,
        User.email_verification_token_expires > datetime.utcnow()
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效或已过期的验证令牌"
        )

    # 验证邮箱
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_token_expires = None
    db.commit()

    return {"message": "邮箱验证成功"}


@router.post("/resend-verification-email")
async def resend_verification_email(
    request: EmailResendRequest,
    db: Session = Depends(get_db)
):
    """重新发送验证邮件"""
    # 查找用户
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        # 不暴露用户是否存在
        return {"message": "如果邮箱存在，验证邮件已发送"}

    # 如果已经验证
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已验证"
        )

    # 创建邮箱服务
    email_service = EmailService(
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        smtp_username=settings.SMTP_USERNAME,
        smtp_password=settings.SMTP_PASSWORD,
        from_email=settings.SMTP_FROM_EMAIL
    )

    # 生成验证令牌
    verification_token = email_service.generate_verification_token()
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

    # 更新用户记录
    user.email_verification_token = verification_token
    user.email_verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()

    # 生成邮件内容
    text_content, html_content = email_service.generate_verification_email_content(
        username=user.username,
        token=verification_token,
        verification_url=verification_url
    )

    # 发送邮件
    email_service.send_email(
        to_email=user.email,
        subject="验证您的邮箱 - 加密货币交易系统",
        html_content=html_content,
        text_content=text_content
    )

    return {"message": "验证邮件已发送"}
