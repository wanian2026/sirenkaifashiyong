from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import verify_password, get_password_hash, create_access_token, verify_token
from app.schemas import UserCreate, UserResponse, Token, PasswordChange, PasswordReset, PasswordResetConfirm, UserUpdate
from datetime import datetime, timedelta
from app.config import settings
from typing import Optional
import secrets

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

    # 生成重置令牌
    reset_token = secrets.token_urlsafe(32)

    # 在实际应用中，这里应该：
    # 1. 将令牌保存到数据库（带过期时间）
    # 2. 发送邮件给用户，包含重置链接
    # 为了简化，这里只返回令牌（仅用于演示）

    # TODO: 保存令牌到数据库，设置过期时间（如30分钟）
    # TODO: 发送邮件给用户

    return {
        "message": "重置令牌已生成",
        "token": reset_token,  # 仅用于演示，生产环境应通过邮件发送
        "note": "在生产环境中，令牌应该通过邮件发送给用户"
    }


@router.post("/reset-password/confirm")
async def confirm_password_reset(
    password_reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """确认重置密码"""
    # TODO: 从数据库验证重置令牌是否有效且未过期
    # TODO: 检查令牌是否已被使用

    # 为了简化，这里假设令牌有效
    # 在生产环境中，应该：
    # 1. 查找数据库中的令牌
    # 2. 验证令牌未过期
    # 3. 获取关联的用户ID
    # 4. 更新用户密码
    # 5. 删除令牌

    return {
        "message": "密码重置成功",
        "note": "请在生产环境中实现令牌验证逻辑"
    }
