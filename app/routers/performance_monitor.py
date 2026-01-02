"""
性能监控API路由
提供系统指标、性能指标等监控功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.performance_monitor import performance_monitor
from app.rbac import Permission, PermissionChecker
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["性能监控"])


@router.get("/api/performance/system-status")
async def get_system_status(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前系统状态

    需要权限: system:monitor 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_MONITOR):
            raise HTTPException(
                status_code=403,
                detail="无权访问系统状态"
            )

    try:
        # 获取系统状态
        status = performance_monitor.get_system_status()

        return {
            "success": True,
            "data": status
        }

    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取系统状态失败: {str(e)}"
        )


@router.get("/api/performance/metrics/{metric_type}")
async def get_metrics_history(
    metric_type: str,
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_user)
):
    """
    获取指标历史数据

    指标类型: cpu, memory, disk, network, api_performance, db_performance

    需要权限: system:monitor 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_MONITOR):
            raise HTTPException(
                status_code=403,
                detail="无权访问性能指标"
            )

    try:
        # 获取指标历史
        metrics = performance_monitor.get_metrics_history(metric_type, limit)

        return {
            "success": True,
            "data": metrics,
            "total": len(metrics)
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取指标历史失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取指标历史失败: {str(e)}"
        )


@router.get("/api/performance/summary")
async def get_performance_summary(
    current_user: User = Depends(get_current_user)
):
    """
    获取性能摘要

    需要权限: system:monitor 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_MONITOR):
            raise HTTPException(
                status_code=403,
                detail="无权访问性能摘要"
            )

    try:
        # 获取性能摘要
        summary = performance_monitor.get_performance_summary()

        return {
            "success": True,
            "data": summary
        }

    except Exception as e:
        logger.error(f"获取性能摘要失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取性能摘要失败: {str(e)}"
        )


@router.get("/api/performance/health")
async def check_system_health(
    current_user: User = Depends(get_current_user)
):
    """
    检查系统健康状态

    需要权限: system:monitor 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_MONITOR):
            raise HTTPException(
                status_code=403,
                detail="无权检查系统健康状态"
            )

    try:
        # 检查健康状态
        health = performance_monitor.check_health()

        return {
            "success": True,
            "data": health
        }

    except Exception as e:
        logger.error(f"检查系统健康状态失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"检查系统健康状态失败: {str(e)}"
        )


@router.post("/api/performance/monitoring/start")
async def start_monitoring(
    interval: int = Query(5, ge=1, le=60, description="监控间隔（秒）"),
    current_user: User = Depends(get_current_user)
):
    """
    启动性能监控

    需要权限: system:monitor 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_MONITOR):
            raise HTTPException(
                status_code=403,
                detail="无权启动性能监控"
            )

    try:
        # 启动监控
        performance_monitor.start_monitoring(interval)

        return {
            "success": True,
            "message": f"性能监控已启动，监控间隔: {interval}秒"
        }

    except Exception as e:
        logger.error(f"启动性能监控失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"启动性能监控失败: {str(e)}"
        )


@router.post("/api/performance/monitoring/stop")
async def stop_monitoring(
    current_user: User = Depends(get_current_user)
):
    """
    停止性能监控

    需要权限: system:monitor 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_MONITOR):
            raise HTTPException(
                status_code=403,
                detail="无权停止性能监控"
            )

    try:
        # 停止监控
        performance_monitor.stop_monitoring()

        return {
            "success": True,
            "message": "性能监控已停止"
        }

    except Exception as e:
        logger.error(f"停止性能监控失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"停止性能监控失败: {str(e)}"
        )


@router.delete("/api/performance/history")
async def clear_metrics_history(
    metric_type: Optional[str] = Query(None, description="指标类型，不指定则清除所有"),
    current_user: User = Depends(get_current_user)
):
    """
    清除指标历史

    指标类型: cpu, memory, disk, network, api_performance, db_performance

    需要权限: system:monitor 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_MONITOR):
            raise HTTPException(
                status_code=403,
                detail="无权清除指标历史"
            )

    try:
        # 清除历史
        performance_monitor.clear_history(metric_type)

        return {
            "success": True,
            "message": f"指标历史已清除: {metric_type or '全部'}"
        }

    except Exception as e:
        logger.error(f"清除指标历史失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"清除指标历史失败: {str(e)}"
        )
