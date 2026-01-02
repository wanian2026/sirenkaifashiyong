"""
日志管理API路由
提供日志导出、日志分析等高级功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.audit_log import AuditLog
from app.auth import get_current_user
from app.models import User
from app.log_manager import LogManager
from app.rbac import Permission, PermissionChecker
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(tags=["日志管理"])


@router.post("/api/logs/export/csv")
async def export_logs_to_csv(
    user_id: Optional[int] = Query(None, description="按用户ID筛选"),
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
    导出审计日志到CSV

    需要权限: system:log 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_LOG):
            raise HTTPException(
                status_code=403,
                detail="无权导出日志"
            )

    try:
        # 创建日志管理器
        log_manager = LogManager(db)

        # 导出日志
        filename = log_manager.export_logs_to_csv(
            user_id=user_id,
            action=action,
            resource=resource,
            level=level,
            start_date=start_date,
            end_date=end_date,
            success=success
        )

        # 检查文件是否存在
        if not os.path.exists(filename):
            raise HTTPException(
                status_code=500,
                detail="导出失败：文件不存在"
            )

        # 返回文件
        return FileResponse(
            filename,
            media_type='text/csv',
            filename=os.path.basename(filename)
        )

    except Exception as e:
        logger.error(f"导出CSV日志失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"导出CSV日志失败: {str(e)}"
        )


@router.post("/api/logs/export/excel")
async def export_logs_to_excel(
    user_id: Optional[int] = Query(None, description="按用户ID筛选"),
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
    导出审计日志到Excel

    需要权限: system:log 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_LOG):
            raise HTTPException(
                status_code=403,
                detail="无权导出日志"
            )

    try:
        # 创建日志管理器
        log_manager = LogManager(db)

        # 导出日志
        filename = log_manager.export_logs_to_excel(
            user_id=user_id,
            action=action,
            resource=resource,
            level=level,
            start_date=start_date,
            end_date=end_date,
            success=success
        )

        # 检查文件是否存在
        if not os.path.exists(filename):
            raise HTTPException(
                status_code=500,
                detail="导出失败：文件不存在"
            )

        # 返回文件
        return FileResponse(
            filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=os.path.basename(filename)
        )

    except Exception as e:
        logger.error(f"导出Excel日志失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"导出Excel日志失败: {str(e)}"
        )


@router.get("/api/logs/analysis/summary")
async def get_log_analysis_summary(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取日志分析摘要

    需要权限: system:log 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_LOG):
            raise HTTPException(
                status_code=403,
                detail="无权访问日志分析"
            )

    try:
        # 创建日志管理器
        log_manager = LogManager(db)

        # 构建查询
        query = db.query(AuditLog)

        # 非管理员只能分析自己的日志
        if current_user.role != "admin":
            query = query.filter(AuditLog.user_id == current_user.id)

        # 应用时间范围
        if start_date is not None:
            query = query.filter(AuditLog.created_at >= start_date)

        if end_date is not None:
            query = query.filter(AuditLog.created_at <= end_date)

        # 获取日志
        logs = query.all()

        # 分析摘要
        summary = log_manager.analyze_logs_summary(logs)

        return {
            "success": True,
            "data": summary
        }

    except Exception as e:
        logger.error(f"获取日志分析摘要失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取日志分析摘要失败: {str(e)}"
        )


@router.get("/api/logs/analysis/by-user")
async def get_log_analysis_by_user(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取按用户分析的日志

    需要权限: system:log 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_LOG):
            raise HTTPException(
                status_code=403,
                detail="无权访问日志分析"
            )

    try:
        # 创建日志管理器
        log_manager = LogManager(db)

        # 构建查询
        query = db.query(AuditLog)

        # 应用时间范围
        if start_date is not None:
            query = query.filter(AuditLog.created_at >= start_date)

        if end_date is not None:
            query = query.filter(AuditLog.created_at <= end_date)

        # 获取日志
        logs = query.all()

        # 按用户分析
        user_stats = log_manager.analyze_logs_by_user(logs)

        return {
            "success": True,
            "data": user_stats
        }

    except Exception as e:
        logger.error(f"获取用户日志分析失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取用户日志分析失败: {str(e)}"
        )


@router.get("/api/logs/analysis/by-action")
async def get_log_analysis_by_action(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取按操作类型分析的日志

    需要权限: system:log 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_LOG):
            raise HTTPException(
                status_code=403,
                detail="无权访问日志分析"
            )

    try:
        # 创建日志管理器
        log_manager = LogManager(db)

        # 构建查询
        query = db.query(AuditLog)

        # 非管理员只能分析自己的日志
        if current_user.role != "admin":
            query = query.filter(AuditLog.user_id == current_user.id)

        # 应用时间范围
        if start_date is not None:
            query = query.filter(AuditLog.created_at >= start_date)

        if end_date is not None:
            query = query.filter(AuditLog.created_at <= end_date)

        # 获取日志
        logs = query.all()

        # 按操作类型分析
        action_stats = log_manager.analyze_logs_by_action(logs)

        return {
            "success": True,
            "data": action_stats
        }

    except Exception as e:
        logger.error(f"获取操作类型日志分析失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取操作类型日志分析失败: {str(e)}"
        )


@router.get("/api/logs/analysis/time-distribution")
async def get_log_time_distribution(
    interval: str = Query("hour", description="时间间隔: hour, day, week, month"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取日志时间分布

    需要权限: system:log 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_LOG):
            raise HTTPException(
                status_code=403,
                detail="无权访问日志分析"
            )

    try:
        # 创建日志管理器
        log_manager = LogManager(db)

        # 构建查询
        query = db.query(AuditLog)

        # 非管理员只能分析自己的日志
        if current_user.role != "admin":
            query = query.filter(AuditLog.user_id == current_user.id)

        # 应用时间范围
        if start_date is not None:
            query = query.filter(AuditLog.created_at >= start_date)

        if end_date is not None:
            query = query.filter(AuditLog.created_at <= end_date)

        # 获取日志
        logs = query.all()

        # 分析时间分布
        time_dist = log_manager.analyze_logs_time_distribution(logs, interval)

        return {
            "success": True,
            "data": time_dist
        }

    except Exception as e:
        logger.error(f"获取日志时间分布失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取日志时间分布失败: {str(e)}"
        )


@router.get("/api/logs/detection/anomalies")
async def detect_log_anomalies(
    threshold: int = Query(10, ge=1, description="异常阈值"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    检测日志中的异常行为

    需要权限: system:log 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_LOG):
            raise HTTPException(
                status_code=403,
                detail="无权访问日志分析"
            )

    try:
        # 创建日志管理器
        log_manager = LogManager(db)

        # 构建查询
        query = db.query(AuditLog)

        # 应用时间范围
        if start_date is not None:
            query = query.filter(AuditLog.created_at >= start_date)

        if end_date is not None:
            query = query.filter(AuditLog.created_at <= end_date)

        # 获取日志
        logs = query.all()

        # 检测异常
        anomalies = log_manager.detect_anomalies(logs, threshold)

        return {
            "success": True,
            "data": {
                "total_anomalies": len(anomalies),
                "anomalies": anomalies
            }
        }

    except Exception as e:
        logger.error(f"检测日志异常失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"检测日志异常失败: {str(e)}"
        )


@router.get("/api/logs/analysis/user-behavior/{user_id}")
async def analyze_user_behavior(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="分析天数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    分析用户行为模式

    需要权限: system:log 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_LOG):
            raise HTTPException(
                status_code=403,
                detail="无权访问日志分析"
            )

    try:
        # 创建日志管理器
        log_manager = LogManager(db)

        # 分析用户行为
        behavior = log_manager.analyze_user_behavior(user_id, days)

        return {
            "success": True,
            "data": behavior
        }

    except Exception as e:
        logger.error(f"分析用户行为失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"分析用户行为失败: {str(e)}"
        )
