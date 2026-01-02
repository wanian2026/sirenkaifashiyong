"""
基于角色的访问控制（RBAC）模块
提供用户、角色、权限管理功能
"""

from typing import List, Dict, Optional
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import logging

logger = logging.getLogger(__name__)


# 定义权限枚举
class Permission(Enum):
    """系统权限"""
    # 用户管理
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # 机器人管理
    BOT_CREATE = "bot:create"
    BOT_READ = "bot:read"
    BOT_UPDATE = "bot:update"
    BOT_DELETE = "bot:delete"
    BOT_START = "bot:start"
    BOT_STOP = "bot:stop"

    # 交易管理
    TRADE_READ = "trade:read"
    TRADE_EXPORT = "trade:export"

    # 订单管理
    ORDER_READ = "order:read"
    ORDER_CREATE = "order:create"
    ORDER_CANCEL = "order:cancel"

    # 风险管理
    RISK_READ = "risk:read"
    RISK_CONFIGURE = "risk:configure"

    # 回测功能
    BACKTEST_RUN = "backtest:run"
    BACKTEST_EXPORT = "backtest:export"

    # 通知管理
    NOTIFICATION_CONFIGURE = "notification:configure"
    NOTIFICATION_SEND = "notification:send"

    # 系统管理
    SYSTEM_CONFIGURE = "system:configure"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_LOG = "system:log"


# 定义角色枚举
class Role(Enum):
    """系统角色"""
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"


# 角色权限映射
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        # 所有权限
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.BOT_CREATE,
        Permission.BOT_READ,
        Permission.BOT_UPDATE,
        Permission.BOT_DELETE,
        Permission.BOT_START,
        Permission.BOT_STOP,
        Permission.TRADE_READ,
        Permission.TRADE_EXPORT,
        Permission.ORDER_READ,
        Permission.ORDER_CREATE,
        Permission.ORDER_CANCEL,
        Permission.RISK_READ,
        Permission.RISK_CONFIGURE,
        Permission.BACKTEST_RUN,
        Permission.BACKTEST_EXPORT,
        Permission.NOTIFICATION_CONFIGURE,
        Permission.NOTIFICATION_SEND,
        Permission.SYSTEM_CONFIGURE,
        Permission.SYSTEM_MONITOR,
        Permission.SYSTEM_LOG,
    ],
    Role.TRADER: [
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.BOT_CREATE,
        Permission.BOT_READ,
        Permission.BOT_UPDATE,
        Permission.BOT_START,
        Permission.BOT_STOP,
        Permission.TRADE_READ,
        Permission.TRADE_EXPORT,
        Permission.ORDER_READ,
        Permission.ORDER_CANCEL,
        Permission.RISK_READ,
        Permission.BACKTEST_RUN,
        Permission.BACKTEST_EXPORT,
        Permission.NOTIFICATION_CONFIGURE,
        Permission.NOTIFICATION_SEND,
    ],
    Role.VIEWER: [
        Permission.USER_READ,
        Permission.BOT_READ,
        Permission.TRADE_READ,
        Permission.ORDER_READ,
        Permission.RISK_READ,
        Permission.BACKTEST_RUN,
        Permission.SYSTEM_MONITOR,
    ]
}


# 多对多关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class RoleModel(Base):
    """角色表"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # admin, trader, viewer
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("PermissionModel", secondary=role_permissions, back_populates="roles")


class PermissionModel(Base):
    """权限表"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # user:create, bot:start, etc.
    description = Column(String)
    category = Column(String)  # user, bot, trade, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    roles = relationship("RoleModel", secondary=role_permissions, back_populates="permissions")


class PermissionChecker:
    """权限检查器"""

    @staticmethod
    def has_permission(
        user_permissions: List[str],
        required_permission: Permission
    ) -> bool:
        """检查用户是否有指定权限"""
        return required_permission.value in user_permissions

    @staticmethod
    def has_any_permission(
        user_permissions: List[str],
        required_permissions: List[Permission]
    ) -> bool:
        """检查用户是否有任意一个指定权限"""
        for perm in required_permissions:
            if perm.value in user_permissions:
                return True
        return False

    @staticmethod
    def has_all_permissions(
        user_permissions: List[str],
        required_permissions: List[Permission]
    ) -> bool:
        """检查用户是否有所有指定权限"""
        for perm in required_permissions:
            if perm.value not in user_permissions:
                return False
        return True


class RoleManager:
    """角色管理器"""

    @staticmethod
    def get_role_permissions(role: Role) -> List[str]:
        """获取角色的所有权限"""
        return [perm.value for perm in ROLE_PERMISSIONS.get(role, [])]

    @staticmethod
    def add_permission_to_role(role: Role, permission: Permission):
        """为角色添加权限"""
        if role not in ROLE_PERMISSIONS:
            ROLE_PERMISSIONS[role] = []

        if permission not in ROLE_PERMISSIONS[role]:
            ROLE_PERMISSIONS[role].append(permission)
            logger.info(f"为角色 {role.value} 添加权限 {permission.value}")

    @staticmethod
    def remove_permission_from_role(role: Role, permission: Permission):
        """从角色移除权限"""
        if role in ROLE_PERMISSIONS and permission in ROLE_PERMISSIONS[role]:
            ROLE_PERMISSIONS[role].remove(permission)
            logger.info(f"从角色 {role.value} 移除权限 {permission.value}")

    @staticmethod
    def get_all_roles() -> List[Dict]:
        """获取所有角色及其权限"""
        roles = []
        for role in Role:
            permissions = ROLE_PERMISSIONS.get(role, [])
            roles.append({
                'name': role.value,
                'description': role.value.capitalize(),
                'permissions': [perm.value for perm in permissions],
                'permission_count': len(permissions)
            })
        return roles


def require_permission(required_permission: Permission):
    """权限检查装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 这里应该从上下文获取用户和权限
            # 简化版本，实际应该在依赖注入中实现
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(required_role: Role):
    """角色检查装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 这里应该从上下文获取用户和角色
            # 简化版本，实际应该在依赖注入中实现
            return func(*args, **kwargs)
        return wrapper
    return decorator


def check_user_permission(user, required_permission: Permission) -> bool:
    """
    检查用户是否有指定权限

    兼容两种角色模式：
    1. user.role 字符串（"admin", "trader", "viewer"）
    2. user.roles 关系列表

    Args:
        user: 用户对象（包含role或roles属性）
        required_permission: 需要的权限

    Returns:
        是否有权限
    """
    if not user:
        return False

    # 收集用户所有角色的权限
    user_permissions = set()

    # 方式1：从 user.roles 关系获取（RBAC多对多模式）
    if hasattr(user, 'roles') and user.roles:
        for role_obj in user.roles:
            role = Role(role_obj.name)
            role_perms = RoleManager.get_role_permissions(role)
            user_permissions.update(role_perms)

    # 方式2：从 user.role 字符串获取（简化模式）
    elif hasattr(user, 'role') and user.role:
        try:
            role = Role(user.role)
            role_perms = RoleManager.get_role_permissions(role)
            user_permissions.update(role_perms)
        except ValueError:
            logger.warning(f"无效的角色: {user.role}")

    # 检查是否有需要的权限
    return required_permission.value in user_permissions


def get_user_permissions(user) -> List[str]:
    """
    获取用户的所有权限

    兼容两种角色模式：
    1. user.role 字符串（"admin", "trader", "viewer"）
    2. user.roles 关系列表

    Args:
        user: 用户对象

    Returns:
        权限列表
    """
    if not user:
        return []

    permissions = set()

    # 方式1：从 user.roles 关系获取（RBAC多对多模式）
    if hasattr(user, 'roles') and user.roles:
        for role_obj in user.roles:
            role = Role(role_obj.name)
            role_perms = RoleManager.get_role_permissions(role)
            permissions.update(role_perms)

    # 方式2：从 user.role 字符串获取（简化模式）
    elif hasattr(user, 'role') and user.role:
        try:
            role = Role(user.role)
            role_perms = RoleManager.get_role_permissions(role)
            permissions.update(role_perms)
        except ValueError:
            logger.warning(f"无效的角色: {user.role}")

    return list(permissions)


def is_admin(user) -> bool:
    """
    检查用户是否是管理员

    兼容两种角色模式：
    1. user.role 字符串（"admin"）
    2. user.roles 关系列表

    Args:
        user: 用户对象

    Returns:
        是否是管理员
    """
    if not user:
        return False

    # 方式1：从 user.roles 关系获取
    if hasattr(user, 'roles') and user.roles:
        for role_obj in user.roles:
            if role_obj.name == Role.ADMIN.value:
                return True

    # 方式2：从 user.role 字符串获取
    if hasattr(user, 'role') and user.role:
        return user.role == Role.ADMIN.value

    return False
