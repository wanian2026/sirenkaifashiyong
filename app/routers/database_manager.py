"""
数据库管理API路由
提供数据库备份、恢复、清理等管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.database_manager import DatabaseManager
from app.config import settings
from app.rbac import Permission, PermissionChecker
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(tags=["数据库管理"])

# 全局数据库管理器实例
db_manager = None


def get_database_manager():
    """获取数据库管理器实例"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager(settings.DATABASE_URL)
    return db_manager


@router.post("/api/database/backup")
async def create_database_backup(
    description: str = Query(None, description="备份描述"),
    compress: bool = Query(True, description="是否压缩"),
    current_user: User = Depends(get_current_user)
):
    """
    创建数据库备份

    需要权限: system:backup 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="无权创建数据库备份"
            )

    try:
        # 获取数据库管理器
        manager = get_database_manager()

        # 创建备份
        backup_file = manager.backup_database(
            description=description,
            compress=compress
        )

        return {
            "success": True,
            "message": "数据库备份创建成功",
            "backup_file": backup_file
        }

    except Exception as e:
        logger.error(f"创建数据库备份失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"创建数据库备份失败: {str(e)}"
        )


@router.get("/api/database/backups")
async def list_database_backups(
    current_user: User = Depends(get_current_user)
):
    """
    列出所有数据库备份

    需要权限: system:backup 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="无权访问数据库备份列表"
            )

    try:
        # 获取数据库管理器
        manager = get_database_manager()

        # 列出备份
        backups = manager.list_backups()

        return {
            "success": True,
            "data": backups,
            "total": len(backups)
        }

    except Exception as e:
        logger.error(f"获取数据库备份列表失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取数据库备份列表失败: {str(e)}"
        )


@router.post("/api/database/restore")
async def restore_database(
    filename: str = Query(..., description="备份文件名"),
    current_user: User = Depends(get_current_user)
):
    """
    从备份文件恢复数据库

    ⚠️ 警告：此操作将覆盖当前数据库！

    需要权限: system:backup 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="无权恢复数据库"
            )

    try:
        # 获取数据库管理器
        manager = get_database_manager()

        # 构建备份文件路径
        backup_file = os.path.join(manager.backup_dir, filename)

        # 恢复数据库
        result = manager.restore_database(backup_file)

        return {
            "success": True,
            "message": "数据库恢复成功",
            "result": result
        }

    except FileNotFoundError as e:
        logger.error(f"备份文件不存在: {e}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"恢复数据库失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"恢复数据库失败: {str(e)}"
        )


@router.delete("/api/database/backup/{filename}")
async def delete_database_backup(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """
    删除数据库备份文件

    需要权限: system:backup 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="无权删除数据库备份"
            )

    try:
        # 获取数据库管理器
        manager = get_database_manager()

        # 删除备份
        success = manager.delete_backup(filename)

        return {
            "success": True,
            "message": f"备份文件 {filename} 删除成功"
        }

    except FileNotFoundError as e:
        logger.error(f"备份文件不存在: {e}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"删除备份文件失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"删除备份文件失败: {str(e)}"
        )


@router.post("/api/database/cleanup-backups")
async def cleanup_old_backups(
    keep_days: int = Query(30, ge=1, description="保留天数"),
    current_user: User = Depends(get_current_user)
):
    """
    清理旧的数据库备份文件

    需要权限: system:backup 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="无权清理数据库备份"
            )

    try:
        # 获取数据库管理器
        manager = get_database_manager()

        # 清理旧备份
        deleted_count = manager.cleanup_old_backups(keep_days)

        return {
            "success": True,
            "message": f"清理完成，删除了 {deleted_count} 个旧备份文件",
            "deleted_count": deleted_count
        }

    except Exception as e:
        logger.error(f"清理旧备份失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"清理旧备份失败: {str(e)}"
        )


@router.post("/api/database/cleanup-data")
async def cleanup_old_data(
    days: int = Query(90, ge=1, description="保留天数"),
    tables: Optional[List[str]] = Query(None, description="要清理的表列表"),
    current_user: User = Depends(get_current_user)
):
    """
    清理旧的数据库数据

    需要权限: system:backup 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="无权清理数据库数据"
            )

    try:
        # 获取数据库管理器
        manager = get_database_manager()

        # 清理旧数据
        results = manager.cleanup_old_data(days, tables)

        return {
            "success": True,
            "message": f"数据清理完成，总共删除了 {results['total_deleted']} 条记录",
            "results": results
        }

    except Exception as e:
        logger.error(f"清理旧数据失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"清理旧数据失败: {str(e)}"
        )


@router.get("/api/database/stats")
async def get_database_stats(
    current_user: User = Depends(get_current_user)
):
    """
    获取数据库统计信息

    需要权限: system:backup 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="无权访问数据库统计信息"
            )

    try:
        # 获取数据库管理器
        manager = get_database_manager()

        # 获取统计信息
        stats = manager.get_database_stats()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"获取数据库统计信息失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取数据库统计信息失败: {str(e)}"
        )


@router.post("/api/database/optimize")
async def optimize_database(
    current_user: User = Depends(get_current_user)
):
    """
    优化数据库

    需要权限: system:backup 或 ADMIN角色
    """
    # 检查权限
    if current_user.role != "admin":
        user_permissions = []
        if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="无权优化数据库"
            )

    try:
        # 获取数据库管理器
        manager = get_database_manager()

        # 优化数据库
        results = manager.optimize_database()

        return {
            "success": True,
            "message": "数据库优化完成",
            "results": results
        }

    except Exception as e:
        logger.error(f"优化数据库失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"优化数据库失败: {str(e)}"
        )
