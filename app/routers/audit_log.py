"""
审计日志API路由
提供审计日志查询和管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.audit_log import AuditLog, AuditLogAction, AuditLogLevel
from app.auth import get_current_user
from app.models import User
from app.rbac import Permission, PermissionChecker

router = APIRouter(tags=["审计日志"])


@router.get("/api/audit-logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    user_id: Optional[int] = Query(None, description="按用户ID筛选"),
    username: Optional[str] = Query(None, description="按用户名筛选"),
    action: Optional[str] = Query(None, description="按操作类型筛选"),
    resource: Optional[str] = Query(None, description="按资源类型筛选"),
    level: Optional[str] = Query(None, description="按日志级别筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    success: Optional[bool] = Query(None, description="按成功状态筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取审计日志列表

    需要权限: system:log 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        # 获取用户权限列表（简化处理）
        user_permissions = []  # 实际应该从数据库获取
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_LOG):
            raise HTTPException(
                status_code=403,
                detail="无权访问审计日志"
            )

    # 构建查询
    query = db.query(AuditLog)

    # 非管理员只能查看自己的日志
    if current_user.role != "admin":
        query = query.filter(AuditLog.user_id == current_user.id)

    # 应用筛选条件
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    if username is not None:
        query = query.filter(AuditLog.username.like(f"%{username}%"))

    if action is not None:
        query = query.filter(AuditLog.action == action)

    if resource is not None:
        query = query.filter(AuditLog.resource == resource)

    if level is not None:
        query = query.filter(AuditLog.level == level)

    if start_date is not None:
        query = query.filter(AuditLog.created_at >= start_date)

    if end_date is not None:
        query = query.filter(AuditLog.created_at <= end_date)

    if success is not None:
        query = query.filter(AuditLog.success == success)

    # 按时间倒序排序
    query = query.order_by(AuditLog.created_at.desc())

    # 分页
    total = query.count()
    logs = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": [log.to_dict() for log in logs]
    }


@router.get("/api/audit-logs/{log_id}")
async def get_audit_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取审计日志详情

    需要权限: system:log 或 ADMIN角色
    """
    # 获取日志
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()

    if not log:
        raise HTTPException(status_code=404, detail="审计日志不存在")

    # 检查权限
    if current_user.role != "admin" and log.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="无权访问此审计日志"
        )

    return log.to_dict()


@router.get("/api/audit-logs/statistics")
async def get_audit_statistics(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取审计日志统计信息

    需要权限: system:log 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        # 获取用户权限列表
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_LOG):
            raise HTTPException(
                status_code=403,
                detail="无权访问审计日志统计"
            )

    # 构建查询
    query = db.query(AuditLog)

    # 非管理员只能统计自己的日志
    if current_user.role != "admin":
        query = query.filter(AuditLog.user_id == current_user.id)

    # 应用时间范围
    if start_date is not None:
        query = query.filter(AuditLog.created_at >= start_date)

    if end_date is not None:
        query = query.filter(AuditLog.created_at <= end_date)

    # 统计总数
    total_logs = query.count()

    # 按操作类型统计
    action_stats = {}
    for action in AuditLogAction:
        count = query.filter(AuditLog.action == action.value).count()
        if count > 0:
            action_stats[action.value] = count

    # 按资源类型统计
    resource_stats = {}
    resources = query.with_entities(AuditLog.resource).distinct().all()
    for resource in resources:
        count = query.filter(AuditLog.resource == resource[0]).count()
        resource_stats[resource[0]] = count

    # 按日志级别统计
    level_stats = {}
    for level in AuditLogLevel:
        count = query.filter(AuditLog.level == level.value).count()
        if count > 0:
            level_stats[level.value] = count

    # 成功率统计
    success_count = query.filter(AuditLog.success == True).count()
    failure_count = query.filter(AuditLog.success == False).count()

    return {
        "total_logs": total_logs,
        "action_stats": action_stats,
        "resource_stats": resource_stats,
        "level_stats": level_stats,
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": (success_count / total_logs * 100) if total_logs > 0 else 0
    }


@router.get("/api/audit-logs/user/{user_id}")
async def get_user_audit_logs(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定用户的审计日志

    需要权限: user:read 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin" and current_user.id != user_id:
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.USER_READ):
            raise HTTPException(
                status_code=403,
                detail="无权查看其他用户的审计日志"
            )

    # 构建查询
    query = db.query(AuditLog).filter(AuditLog.user_id == user_id)

    # 按时间倒序排序
    query = query.order_by(AuditLog.created_at.desc())

    # 分页
    total = query.count()
    logs = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": [log.to_dict() for log in logs]
    }


@router.get("/api/audit-logs/recent")
async def get_recent_audit_logs(
    hours: int = Query(24, ge=1, le=168, description="最近小时数（最多7天）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取最近的审计日志

    默认最近24小时
    """
    # 计算时间范围
    start_date = datetime.now() - timedelta(hours=hours)

    # 构建查询
    query = db.query(AuditLog).filter(
        AuditLog.created_at >= start_date
    )

    # 非管理员只能查看自己的日志
    if current_user.role != "admin":
        query = query.filter(AuditLog.user_id == current_user.id)

    # 按时间倒序排序
    query = query.order_by(AuditLog.created_at.desc())

    # 限制返回100条
    logs = query.limit(100).all()

    return {
        "hours": hours,
        "logs": [log.to_dict() for log in logs]
    }
