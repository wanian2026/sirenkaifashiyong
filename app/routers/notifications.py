"""
通知管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel
import json

from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.notifications import (
    NotificationManager,
    NotificationChannel,
    NotificationLevel,
    EmailNotifier,
    DingTalkNotifier,
    FeishuNotifier,
    WebhookNotifier,
    notification_manager
)

router = APIRouter()


class EmailConfig(BaseModel):
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    from_email: str
    use_tls: bool = True


class DingTalkConfig(BaseModel):
    webhook_url: str
    secret: Optional[str] = None


class FeishuConfig(BaseModel):
    webhook_url: str


class WebhookConfig(BaseModel):
    webhook_url: str
    headers: Optional[Dict] = None


class SendNotificationRequest(BaseModel):
    title: str
    content: str
    channels: List[str] = ["email"]
    level: str = "info"


@router.post("/configure/email")
async def configure_email(
    config: EmailConfig,
    current_user: User = Depends(get_current_user)
):
    """配置邮件通知"""
    try:
        notifier = EmailNotifier(
            smtp_server=config.smtp_server,
            smtp_port=config.smtp_port,
            username=config.username,
            password=config.password,
            from_email=config.from_email,
            use_tls=config.use_tls
        )

        notification_manager.add_notifier(NotificationChannel.EMAIL, notifier)

        return {
            "message": "邮件通知配置成功",
            "channel": "email"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置失败: {str(e)}"
        )


@router.post("/configure/dingtalk")
async def configure_dingtalk(
    config: DingTalkConfig,
    current_user: User = Depends(get_current_user)
):
    """配置钉钉通知"""
    try:
        notifier = DingTalkNotifier(
            webhook_url=config.webhook_url,
            secret=config.secret
        )

        notification_manager.add_notifier(NotificationChannel.DINGTALK, notifier)

        return {
            "message": "钉钉通知配置成功",
            "channel": "dingtalk"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置失败: {str(e)}"
        )


@router.post("/configure/feishu")
async def configure_feishu(
    config: FeishuConfig,
    current_user: User = Depends(get_current_user)
):
    """配置飞书通知"""
    try:
        notifier = FeishuNotifier(webhook_url=config.webhook_url)
        notification_manager.add_notifier(NotificationChannel.FEISHU, notifier)

        return {
            "message": "飞书通知配置成功",
            "channel": "feishu"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置失败: {str(e)}"
        )


@router.post("/configure/webhook")
async def configure_webhook(
    config: WebhookConfig,
    current_user: User = Depends(get_current_user)
):
    """配置Webhook通知"""
    try:
        notifier = WebhookNotifier(
            webhook_url=config.webhook_url,
            headers=config.headers
        )

        notification_manager.add_notifier(NotificationChannel.WEBHOOK, notifier)

        return {
            "message": "Webhook通知配置成功",
            "channel": "webhook"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置失败: {str(e)}"
        )


@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """发送通知"""
    try:
        # 转换渠道字符串为枚举
        channels = []
        for channel_str in request.channels:
            try:
                channels.append(NotificationChannel(channel_str))
            except ValueError:
                continue

        # 转换级别字符串为枚举
        try:
            level = NotificationLevel(request.level)
        except ValueError:
            level = NotificationLevel.INFO

        # 发送通知
        results = await notification_manager.send_notification(
            title=request.title,
            content=request.content,
            channels=channels if channels else None,
            level=level
        )

        # 格式化结果
        formatted_results = {}
        for channel, success in results.items():
            formatted_results[channel.value] = success

        return {
            "message": "通知发送完成",
            "results": formatted_results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送通知失败: {str(e)}"
        )


@router.post("/test")
async def test_notification(
    channel: str = Query(..., regex="^(email|dingtalk|feishu|webhook)$"),
    current_user: User = Depends(get_current_user)
):
    """测试通知"""
    try:
        notification_channel = NotificationChannel(channel)

        results = await notification_manager.send_notification(
            title="测试通知",
            content=f"这是一条测试通知\n\n发送时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n发送用户: {current_user.username}",
            channels=[notification_channel],
            level=NotificationLevel.INFO
        )

        return {
            "message": "测试通知已发送",
            "channel": channel,
            "success": results.get(notification_channel, False)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试失败: {str(e)}"
        )


@router.get("/history")
async def get_notification_history(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """获取通知历史"""
    history = notification_manager.get_notification_history(limit=limit)

    return {
        "total": len(history),
        "history": history
    }


@router.get("/channels")
async def list_notification_channels():
    """列出所有可用的通知渠道"""
    return {
        "channels": [
            {
                "id": "email",
                "name": "邮件通知",
                "description": "通过SMTP服务器发送邮件通知"
            },
            {
                "id": "dingtalk",
                "name": "钉钉通知",
                "description": "通过钉钉机器人发送群消息"
            },
            {
                "id": "feishu",
                "name": "飞书通知",
                "description": "通过飞书机器人发送群消息"
            },
            {
                "id": "webhook",
                "name": "Webhook通知",
                "description": "通过自定义Webhook发送通知"
            }
        ]
    }


@router.get("/templates")
async def list_notification_templates():
    """列出所有可用的通知模板"""
    from app.notifications import NotificationTemplate

    return {
        "templates": [
            {
                "id": "trade_executed",
                "name": "交易执行通知",
                "title": NotificationTemplate.TRADE_EXECUTED['title'],
                "content": NotificationTemplate.TRADE_EXECUTED['content']
            },
            {
                "id": "risk_alert",
                "name": "风险告警",
                "title": NotificationTemplate.RISK_ALERT['title'],
                "content": NotificationTemplate.RISK_ALERT['content']
            },
            {
                "id": "strategy_status",
                "name": "策略状态变更",
                "title": NotificationTemplate.STRATEGY_STATUS['title'],
                "content": NotificationTemplate.STRATEGY_STATUS['content']
            },
            {
                "id": "system_notification",
                "name": "系统通知",
                "title": NotificationTemplate.SYSTEM_NOTIFICATION['title'],
                "content": NotificationTemplate.SYSTEM_NOTIFICATION['content']
            }
        ]
    }
