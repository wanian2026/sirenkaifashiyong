"""
审计日志中间件
自动记录系统中的关键操作
"""

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json
import logging
from datetime import datetime
from typing import Optional, Callable
from sqlalchemy.orm import Session
from app.config import settings
from app.audit_log import AuditLog, AuditLogAction, AuditLogLevel
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """审计日志中间件"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录审计日志

        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            Response: 响应对象
        """
        # 如果审计日志未启用，直接处理请求
        if not settings.AUDIT_LOG_ENABLED:
            return await call_next(request)

        # 记录请求开始时间
        start_time = datetime.now()

        # 获取请求信息
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # 获取用户信息（如果有JWT token）
        user_id, username = self._get_user_info(request)

        try:
            # 处理请求
            response = await call_next(request)

            # 记录审计日志
            self._log_audit_entry(
                user_id=user_id,
                username=username,
                action=self._get_action_from_method(method),
                resource=self._get_resource_from_path(path),
                method=method,
                path=path,
                query_params=query_params,
                status_code=response.status_code,
                success=200 <= response.status_code < 300,
                ip_address=client_ip,
                user_agent=user_agent,
                duration=(datetime.now() - start_time).total_seconds()
            )

            return response

        except Exception as e:
            # 记录错误审计日志
            self._log_audit_entry(
                user_id=user_id,
                username=username,
                action=self._get_action_from_method(method),
                resource=self._get_resource_from_path(path),
                method=method,
                path=path,
                query_params=query_params,
                status_code=500,
                success=False,
                error_message=str(e),
                ip_address=client_ip,
                user_agent=user_agent,
                duration=(datetime.now() - start_time).total_seconds()
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查X-Forwarded-For头（代理服务器）
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # 检查X-Real-IP头
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 直接获取客户端地址
        if request.client:
            return request.client.host

        return "unknown"

    def _get_user_info(self, request: Request) -> tuple:
        """
        从请求中获取用户信息

        Args:
            request: 请求对象

        Returns:
            (user_id, username) 元组
        """
        try:
            # 从请求state中获取用户信息（由auth依赖设置）
            if hasattr(request.state, "user"):
                user = request.state.user
                return user.id, user.username

            # 从JWT token中解析
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                from app.auth import verify_token
                token = auth_header[7:]
                payload = verify_token(token)
                if payload:
                    sub = payload.get("sub", "")
                    # 从username获取user_id（这里简化处理）
                    db = SessionLocal()
                    try:
                        from app.models import User
                        user = db.query(User).filter(User.username == sub).first()
                        if user:
                            return user.id, user.username
                    finally:
                        db.close()

        except Exception as e:
            logger.warning(f"获取用户信息失败: {e}")

        return None, None

    def _get_action_from_method(self, method: str) -> str:
        """
        从HTTP方法获取操作类型

        Args:
            method: HTTP方法

        Returns:
            操作类型
        """
        action_map = {
            "GET": AuditLogAction.READ,
            "POST": AuditLogAction.CREATE,
            "PUT": AuditLogAction.UPDATE,
            "PATCH": AuditLogAction.UPDATE,
            "DELETE": AuditLogAction.DELETE,
        }
        return action_map.get(method, AuditLogAction.READ)

    def _get_resource_from_path(self, path: str) -> str:
        """
        从路径获取资源类型

        Args:
            path: 请求路径

        Returns:
            资源类型
        """
        # 解析路径获取资源类型
        parts = path.strip("/").split("/")

        if len(parts) >= 2:
            resource = parts[1]
            # 映射到资源名称
            resource_map = {
                "auth": "auth",
                "bots": "bot",
                "trades": "trade",
                "orders": "order",
                "risk": "risk",
                "backtest": "backtest",
                "notifications": "notification",
                "rbac": "rbac",
                "optimize": "system",
                "exchange": "exchange",
                "analytics": "analytics",
                "strategies": "strategy",
                "ws": "websocket",
            }
            return resource_map.get(resource, resource)

        return "unknown"

    def _log_audit_entry(
        self,
        user_id: Optional[int],
        username: Optional[str],
        action: str,
        resource: str,
        method: str,
        path: str,
        query_params: dict,
        status_code: int,
        success: bool,
        error_message: Optional[str] = None,
        ip_address: str = "unknown",
        user_agent: str = "",
        duration: float = 0.0
    ):
        """
        记录审计日志

        Args:
            user_id: 用户ID
            username: 用户名
            action: 操作类型
            resource: 资源类型
            method: HTTP方法
            path: 请求路径
            query_params: 查询参数
            status_code: 状态码
            success: 是否成功
            error_message: 错误信息
            ip_address: IP地址
            user_agent: User-Agent
            duration: 请求持续时间（秒）
        """
        try:
            db = SessionLocal()

            # 确定日志级别
            level = AuditLogLevel.INFO
            if not success:
                if status_code >= 500:
                    level = AuditLogLevel.ERROR
                else:
                    level = AuditLogLevel.WARNING

            # 构建详情信息
            details = {
                "method": method,
                "path": path,
                "query_params": query_params,
                "status_code": status_code,
                "duration": duration,
            }

            # 创建审计日志
            audit_log = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource=resource,
                level=level,
                details=json.dumps(details),
                ip_address=ip_address,
                user_agent=user_agent[:500] if user_agent else "",  # 限制长度
                success=success,
                error_message=error_message
            )

            db.add(audit_log)
            db.commit()

            logger.debug(f"审计日志已记录: {username} {action} {resource}")

        except Exception as e:
            logger.error(f"记录审计日志失败: {e}")
        finally:
            if 'db' in locals():
                db.close()
