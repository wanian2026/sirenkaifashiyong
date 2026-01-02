"""
权限管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.rbac import (
    Role,
    Permission,
    RoleManager,
    PermissionChecker,
    get_user_permissions,
    is_admin,
    check_user_permission
)

router = APIRouter()


class RoleResponse(BaseModel):
    name: str
    description: str
    permissions: List[str]
    permission_count: int


class PermissionResponse(BaseModel):
    name: str
    description: str
    category: str


@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出所有角色"""
    # 检查权限
    if not check_user_permission(current_user, Permission.SYSTEM_MONITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问"
        )

    roles_data = RoleManager.get_all_roles()
    return roles_data


@router.get("/roles/{role_name}", response_model=RoleResponse)
async def get_role(
    role_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定角色的详细信息"""
    if not check_user_permission(current_user, Permission.SYSTEM_MONITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问"
        )

    try:
        role = Role(role_name)
        permissions = RoleManager.get_role_permissions(role)

        return RoleResponse(
            name=role.value,
            description=role.value.capitalize(),
            permissions=permissions,
            permission_count=len(permissions)
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"角色 {role_name} 不存在"
        )


@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出所有权限"""
    if not check_user_permission(current_user, Permission.SYSTEM_MONITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问"
        )

    permissions = []
    for perm in Permission:
        perm_category = perm.value.split(':')[0]

        if category and perm_category != category:
            continue

        permissions.append(PermissionResponse(
            name=perm.value,
            description=perm.value.replace(':', ' ').title(),
            category=perm_category
        ))

    return permissions


@router.get("/categories")
async def list_permission_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出权限分类"""
    if not check_user_permission(current_user, Permission.SYSTEM_MONITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问"
        )

    categories = set()
    for perm in Permission:
        category = perm.value.split(':')[0]
        categories.add(category)

    return {
        "categories": sorted(list(categories))
    }


@router.get("/user/my-permissions")
async def get_my_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的权限列表"""
    permissions = get_user_permissions(current_user)

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "permissions": permissions,
        "permission_count": len(permissions),
        "is_admin": is_admin(current_user)
    }


@router.get("/user/{user_id}/permissions")
async def get_user_permissions_api(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定用户的权限列表（需要管理员权限）"""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    permissions = get_user_permissions(user)
    roles = [role.name for role in user.roles] if user.roles else []

    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "roles": roles,
        "permissions": permissions,
        "permission_count": len(permissions),
        "is_admin": is_admin(user)
    }


@router.post("/check")
async def check_permission(
    permission: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """检查当前用户是否有指定权限"""
    try:
        required_permission = Permission(permission)
        has_perm = check_user_permission(current_user, required_permission)

        return {
            "has_permission": has_perm,
            "permission": permission,
            "user_id": current_user.id
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的权限: {permission}"
        )


@router.get("/user/{user_id}/check")
async def check_user_permission_api(
    user_id: int,
    permission: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """检查指定用户是否有指定权限（需要管理员权限）"""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    try:
        required_permission = Permission(permission)
        has_perm = check_user_permission(user, required_permission)

        return {
            "has_permission": has_perm,
            "permission": permission,
            "user_id": user.id,
            "username": user.username
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的权限: {permission}"
        )


@router.get("/stats")
async def get_permission_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取权限统计信息"""
    if not check_user_permission(current_user, Permission.SYSTEM_MONITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问"
        )

    # 统计各分类的权限数量
    category_stats = {}
    for perm in Permission:
        category = perm.value.split(':')[0]
        category_stats[category] = category_stats.get(category, 0) + 1

    return {
        "total_permissions": len(Permission),
        "total_roles": len(Role),
        "category_stats": category_stats
    }
