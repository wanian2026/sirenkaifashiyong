"""
机器人性能统计和配置模板API路由
提供机器人性能分析、资源监控、配置模板管理等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_user
from app.models import User, TradingBot
from app.bot_performance import BotPerformanceTracker, BotConfigTemplate
from app.routers.bots import running_bots, bot_risk_managers
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(tags=["机器人性能管理"])


@router.get("/api/bot-performance/{bot_id}/stats")
async def get_bot_performance_stats(
    bot_id: int,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取机器人性能统计

    需要权限: bot:view 或 用户本人
    """
    # 验证机器人所有权
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=404,
            detail="机器人不存在"
        )

    try:
        # 获取性能统计
        tracker = BotPerformanceTracker(db)
        stats = tracker.get_bot_performance_stats(bot_id, days)

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"获取机器人性能统计失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取机器人性能统计失败: {str(e)}"
        )


@router.get("/api/bot-performance/{bot_id}/resource-usage")
async def get_bot_resource_usage(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取机器人资源使用情况

    需要权限: bot:view 或 用户本人
    """
    # 验证机器人所有权
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=404,
            detail="机器人不存在"
        )

    try:
        # 获取资源使用情况
        tracker = BotPerformanceTracker(db)
        usage = tracker.get_bot_resource_usage(bot_id)

        return {
            "success": True,
            "data": usage
        }

    except Exception as e:
        logger.error(f"获取机器人资源使用情况失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取机器人资源使用情况失败: {str(e)}"
        )


@router.post("/api/bot-performance/compare")
async def compare_bots_performance(
    bot_ids: List[int],
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    比较多个机器人的性能

    需要权限: bot:view 或 用户本人
    """
    # 验证所有权（所有机器人都必须属于当前用户）
    from app.models import TradingBot

    bots = db.query(TradingBot).filter(
        TradingBot.id.in_(bot_ids),
        TradingBot.user_id == current_user.id
    ).all()

    if len(bots) != len(bot_ids):
        raise HTTPException(
            status_code=400,
            detail="部分机器人不存在或无权访问"
        )

    try:
        # 比较性能
        tracker = BotPerformanceTracker(db)
        comparison = tracker.compare_bots_performance(bot_ids, days)

        return {
            "success": True,
            "data": comparison
        }

    except Exception as e:
        logger.error(f"比较机器人性能失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"比较机器人性能失败: {str(e)}"
        )


# ========== 配置模板管理 ==========

@router.post("/api/bot-templates")
async def save_config_template(
    template_name: str = Query(..., description="模板名称"),
    bot_id: int = Query(..., description="机器人ID"),
    description: str = Query(None, description="模板描述"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    保存机器人配置为模板

    需要权限: bot:edit 或 用户本人
    """
    try:
        # 保存模板
        template_manager = BotConfigTemplate(db)
        template_id = template_manager.save_config_template(
            template_name=template_name,
            bot_id=bot_id,
            user_id=current_user.id,
            description=description
        )

        return {
            "success": True,
            "message": "配置模板已保存",
            "template_id": template_id
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"保存配置模板失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"保存配置模板失败: {str(e)}"
        )


@router.get("/api/bot-templates")
async def list_config_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    列出用户的所有配置模板

    需要权限: bot:view 或 用户本人
    """
    try:
        # 列出模板
        template_manager = BotConfigTemplate(db)
        templates = template_manager.list_config_templates(current_user.id)

        return {
            "success": True,
            "data": templates,
            "total": len(templates)
        }

    except Exception as e:
        logger.error(f"列出配置模板失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"列出配置模板失败: {str(e)}"
        )


@router.get("/api/bot-templates/{template_id}")
async def get_config_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取配置模板详情

    需要权限: bot:view 或 用户本人
    """
    try:
        # 加载模板
        template_manager = BotConfigTemplate(db)
        template = template_manager.load_config_template(template_id, current_user.id)

        return {
            "success": True,
            "data": template
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取配置模板失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取配置模板失败: {str(e)}"
        )


@router.delete("/api/bot-templates/{template_id}")
async def delete_config_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除配置模板

    需要权限: bot:edit 或 用户本人
    """
    try:
        # 删除模板
        template_manager = BotConfigTemplate(db)
        success = template_manager.delete_config_template(template_id, current_user.id)

        return {
            "success": success,
            "message": "配置模板已删除"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"删除配置模板失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"删除配置模板失败: {str(e)}"
        )
