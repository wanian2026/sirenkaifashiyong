"""
数据库优化API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict

from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.database_optimization import db_optimizer
from app.rbac import Permission, check_user_permission

router = APIRouter()


@router.get("/report")
async def get_optimization_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数据库优化报告"""
    # 检查权限
    if not check_user_permission(current_user, Permission.SYSTEM_MONITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统监控权限"
        )

    try:
        report = db_optimizer.get_optimization_report()
        return report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成报告失败: {str(e)}"
        )


@router.get("/tables")
async def analyze_tables(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """分析表大小和结构"""
    if not check_user_permission(current_user, Permission.SYSTEM_MONITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统监控权限"
        )

    try:
        analysis = db_optimizer.analyze_table_size()
        return {
            "tables": analysis
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析表失败: {str(e)}"
        )


@router.get("/indexes")
async def analyze_indexes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """分析索引"""
    if not check_user_permission(current_user, Permission.SYSTEM_MONITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统监控权限"
        )

    try:
        indexes = db_optimizer.analyze_indexes()
        suggestions = db_optimizer.suggest_indexes()

        return {
            "current_indexes": indexes,
            "suggested_indexes": suggestions
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析索引失败: {str(e)}"
        )


@router.post("/optimize")
async def optimize_database(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行数据库优化"""
    if not check_user_permission(current_user, Permission.SYSTEM_CONFIGURE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统配置权限"
        )

    try:
        result = db_optimizer.optimize_database()
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"优化数据库失败: {str(e)}"
        )


@router.get("/query-performance")
async def analyze_query_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """分析查询性能"""
    if not check_user_permission(current_user, Permission.SYSTEM_MONITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统监控权限"
        )

    try:
        performance = db_optimizer.analyze_query_performance()
        return {
            "query_performance": performance
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析查询性能失败: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache(
    pattern: str = "*",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清空缓存"""
    if not check_user_permission(current_user, Permission.SYSTEM_CONFIGURE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统配置权限"
        )

    try:
        from app.cache import cache_manager

        if pattern == "*":
            await cache_manager.clear()
            return {"message": "所有缓存已清空"}
        else:
            await cache_manager.delete_pattern(pattern)
            return {"message": f"匹配 '{pattern}' 的缓存已清空"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空缓存失败: {str(e)}"
        )


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取缓存统计"""
    if not check_user_permission(current_user, Permission.SYSTEM_MONITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统监控权限"
        )

    try:
        from app.cache import cache_manager

        # 获取缓存信息
        backend_type = type(cache_manager.backend).__name__

        return {
            "backend_type": backend_type,
            "prefix": cache_manager.prefix
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取缓存统计失败: {str(e)}"
        )


@router.get("/health")
async def get_system_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统健康状态"""
    if not check_user_permission(current_user, Permission.SYSTEM_MONITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统监控权限"
        )

    health_status = {
        "database": "unknown",
        "cache": "unknown",
        "overall": "unknown"
    }

    try:
        # 检查数据库连接
        db.execute("SELECT 1").fetchone()
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)}"

    try:
        # 检查缓存
        from app.cache import cache_manager
        await cache_manager.get("health_check")
        health_status["cache"] = "healthy"
    except Exception as e:
        health_status["cache"] = f"unhealthy: {str(e)}"

    # 总体状态
    if health_status["database"] == "healthy" and health_status["cache"] == "healthy":
        health_status["overall"] = "healthy"
    else:
        health_status["overall"] = "unhealthy"

    return health_status
