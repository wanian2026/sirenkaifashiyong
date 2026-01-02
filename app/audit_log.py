"""
审计日志模型
记录系统中所有关键操作的审计日志
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from enum import Enum


class AuditLogAction(str, Enum):
    """审计日志操作类型"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    START = "start"
    STOP = "stop"
    EXPORT = "export"
    CONFIGURE = "configure"
    VERIFY = "verify"


class AuditLogLevel(str, Enum):
    """审计日志级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True, nullable=True)
    username = Column(String, index=True, nullable=True)
    action = Column(String, index=True, nullable=False)  # 操作类型: create, read, update, delete, login, logout, etc.
    resource = Column(String, index=True, nullable=False)  # 资源类型: user, bot, order, trade, etc.
    resource_id = Column(Integer, index=True, nullable=True)  # 资源ID
    level = Column(String, default=AuditLogLevel.INFO, index=True)  # 日志级别: info, warning, error, critical
    details = Column(Text, nullable=True)  # 操作详情（JSON格式）
    ip_address = Column(String, nullable=True)  # IP地址
    user_agent = Column(Text, nullable=True)  # User-Agent
    success = Column(Boolean, default=True)  # 是否成功
    error_message = Column(Text, nullable=True)  # 错误信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # 创建时间

    # 关系
    user = relationship("User", backref="audit_logs")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource": self.resource,
            "resource_id": self.resource_id,
            "level": self.level,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
