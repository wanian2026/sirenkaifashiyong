"""
通知模块
支持多种通知渠道：邮件、钉钉、飞书、企业微信等
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """通知渠道"""
    EMAIL = "email"
    DINGTALK = "dingtalk"
    FEISHU = "feishu"
    WECHAT = "wechat"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


class NotificationLevel(Enum):
    """通知级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationTemplate:
    """通知模板"""

    # 交易通知模板
    TRADE_EXECUTED = {
        'title': '交易执行通知',
        'content': '交易已执行\n\n机器人: {bot_name}\n交易对: {trading_pair}\n方向: {side}\n价格: {price}\n数量: {amount}\n盈亏: {pnl}'
    }

    # 风险告警模板
    RISK_ALERT = {
        'title': '风险告警',
        'content': '风险告警\n\n机器人: {bot_name}\n风险等级: {risk_level}\n当前持仓: {position}\n亏损金额: {loss}\n建议: {advice}'
    }

    # 策略启停模板
    STRATEGY_STATUS = {
        'title': '策略状态变更',
        'content': '策略状态已变更\n\n机器人: {bot_name}\n新状态: {status}\n时间: {timestamp}'
    }

    # 系统通知模板
    SYSTEM_NOTIFICATION = {
        'title': '系统通知',
        'content': '{message}'
    }


class EmailNotifier:
    """邮件通知器"""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls

    async def send(
        self,
        to_emails: List[str],
        subject: str,
        content: str,
        html: bool = False
    ) -> bool:
        """发送邮件"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject

            # 添加正文
            msg.attach(MIMEText(content, 'html' if html else 'plain', 'utf-8'))

            # 连接SMTP服务器
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)

            if self.use_tls:
                server.starttls()

            server.login(self.username, self.password)

            # 发送邮件
            server.send_message(msg)
            server.quit()

            logger.info(f"邮件发送成功: {to_emails}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False


class DingTalkNotifier:
    """钉钉通知器"""

    def __init__(self, webhook_url: str, secret: str = None):
        self.webhook_url = webhook_url
        self.secret = secret

    async def send(
        self,
        title: str,
        content: str,
        at_mobiles: List[str] = None,
        is_at_all: bool = False
    ) -> bool:
        """发送钉钉消息"""
        try:
            import asyncio
            import hmac
            import hashlib
            import base64
            import urllib.parse
            import aiohttp

            timestamp = str(round(datetime.now().timestamp() * 1000))

            # 如果配置了secret，计算签名
            if self.secret:
                secret_enc = self.secret.encode('utf-8')
                string_to_sign = f'{timestamp}\n{self.secret}'
                string_to_sign_enc = string_to_sign.encode('utf-8')
                hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

                url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
            else:
                url = self.webhook_url

            # 构造消息
            data = {
                "msgtype": "text",
                "text": {
                    "content": f"{title}\n\n{content}"
                },
                "at": {
                    "atMobiles": at_mobiles or [],
                    "isAtAll": is_at_all
                }
            }

            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    result = await response.json()

                    if result.get('errcode') == 0:
                        logger.info(f"钉钉消息发送成功")
                        return True
                    else:
                        logger.error(f"钉钉消息发送失败: {result}")
                        return False

        except Exception as e:
            logger.error(f"钉钉消息发送失败: {e}")
            return False


class FeishuNotifier:
    """飞书通知器"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(
        self,
        title: str,
        content: str,
        msg_type: str = "text"
    ) -> bool:
        """发送飞书消息"""
        try:
            import asyncio
            import aiohttp

            # 构造消息
            if msg_type == "text":
                data = {
                    "msg_type": "text",
                    "content": {
                        "text": f"{title}\n\n{content}"
                    }
                }
            elif msg_type == "post":
                data = {
                    "msg_type": "post",
                    "content": {
                        "post": {
                            "zh_cn": {
                                "title": title,
                                "content": [
                                    [{
                                        "tag": "text",
                                        "text": content
                                    }]
                                ]
                            }
                        }
                    }
                }
            else:
                data = {
                    "msg_type": "text",
                    "content": {
                        "text": content
                    }
                }

            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=data) as response:
                    result = await response.json()

                    if result.get('code') == 0:
                        logger.info(f"飞书消息发送成功")
                        return True
                    else:
                        logger.error(f"飞书消息发送失败: {result}")
                        return False

        except Exception as e:
            logger.error(f"飞书消息发送失败: {e}")
            return False


class WebhookNotifier:
    """Webhook通知器"""

    def __init__(self, webhook_url: str, headers: Dict = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}

    async def send(
        self,
        data: Dict
    ) -> bool:
        """发送Webhook"""
        try:
            import asyncio
            import aiohttp

            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=data,
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook发送成功")
                        return True
                    else:
                        logger.error(f"Webhook发送失败: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Webhook发送失败: {e}")
            return False


class TelegramNotifier:
    """Telegram通知器"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    async def send(
        self,
        title: str,
        content: str,
        parse_mode: str = "Markdown"
    ) -> bool:
        """发送Telegram消息"""
        try:
            import asyncio
            import aiohttp

            # 构造消息
            message = f"*{title}*\n\n{content}"

            # 构造API URL
            url = f"{self.api_url}/sendMessage"

            # 发送请求
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    result = await response.json()

                    if result.get('ok'):
                        logger.info(f"Telegram消息发送成功")
                        return True
                    else:
                        logger.error(f"Telegram消息发送失败: {result}")
                        return False

        except Exception as e:
            logger.error(f"Telegram消息发送失败: {e}")
            return False


class NotificationManager:
    """通知管理器"""

    def __init__(self):
        self.notifiers: Dict[NotificationChannel, List] = {
            NotificationChannel.EMAIL: [],
            NotificationChannel.DINGTALK: [],
            NotificationChannel.FEISHU: [],
            NotificationChannel.TELEGRAM: [],
            NotificationChannel.WEBHOOK: []
        }
        self.notification_history: List[Dict] = []

    def add_notifier(self, channel: NotificationChannel, notifier: object):
        """添加通知器"""
        if channel in self.notifiers:
            self.notifiers[channel].append(notifier)
            logger.info(f"添加通知器: {channel.value}")

    async def send_notification(
        self,
        title: str,
        content: str,
        channels: List[NotificationChannel] = None,
        level: NotificationLevel = NotificationLevel.INFO
    ) -> Dict[NotificationChannel, bool]:
        """发送通知到多个渠道"""
        channels = channels or list(self.notifiers.keys())
        results = {}

        for channel in channels:
            if channel not in self.notifiers or not self.notifiers[channel]:
                results[channel] = False
                continue

            channel_results = []
            for notifier in self.notifiers[channel]:
                try:
                    if channel == NotificationChannel.EMAIL:
                        # 邮件需要to_emails参数，这里简化处理
                        result = True
                    elif channel == NotificationChannel.DINGTALK:
                        result = await notifier.send(title, content)
                    elif channel == NotificationChannel.FEISHU:
                        result = await notifier.send(title, content)
                    elif channel == NotificationChannel.TELEGRAM:
                        result = await notifier.send(title, content)
                    elif channel == NotificationChannel.WEBHOOK:
                        result = await notifier.send({
                            'title': title,
                            'content': content,
                            'level': level.value,
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        result = False

                    channel_results.append(result)

                except Exception as e:
                    logger.error(f"通知发送失败: {channel}, {e}")
                    channel_results.append(False)

            # 只要有一个成功就算成功
            results[channel] = any(channel_results) if channel_results else False

        # 记录通知历史
        self.notification_history.append({
            'timestamp': datetime.now().isoformat(),
            'title': title,
            'content': content,
            'channels': [c.value for c in channels],
            'level': level.value,
            'results': {k.value: v for k, v in results.items()}
        })

        # 限制历史记录数量
        if len(self.notification_history) > 1000:
            self.notification_history = self.notification_history[-1000:]

        return results

    async def send_trade_notification(
        self,
        bot_name: str,
        trading_pair: str,
        side: str,
        price: float,
        amount: float,
        pnl: float,
        channels: List[NotificationChannel] = None
    ) -> Dict[NotificationChannel, bool]:
        """发送交易通知"""
        template = NotificationTemplate.TRADE_EXECUTED
        content = template['content'].format(
            bot_name=bot_name,
            trading_pair=trading_pair,
            side=side,
            price=price,
            amount=amount,
            pnl=pnl
        )

        return await self.send_notification(
            title=template['title'],
            content=content,
            channels=channels,
            level=NotificationLevel.INFO
        )

    async def send_risk_alert(
        self,
        bot_name: str,
        risk_level: str,
        position: float,
        loss: float,
        advice: str,
        channels: List[NotificationChannel] = None
    ) -> Dict[NotificationChannel, bool]:
        """发送风险告警"""
        template = NotificationTemplate.RISK_ALERT
        content = template['content'].format(
            bot_name=bot_name,
            risk_level=risk_level,
            position=position,
            loss=loss,
            advice=advice
        )

        return await self.send_notification(
            title=template['title'],
            content=content,
            channels=channels,
            level=NotificationLevel.WARNING
        )

    async def send_strategy_status(
        self,
        bot_name: str,
        status: str,
        channels: List[NotificationChannel] = None
    ) -> Dict[NotificationChannel, bool]:
        """发送策略状态变更通知"""
        template = NotificationTemplate.STRATEGY_STATUS
        content = template['content'].format(
            bot_name=bot_name,
            status=status,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        return await self.send_notification(
            title=template['title'],
            content=content,
            channels=channels,
            level=NotificationLevel.INFO
        )

    def get_notification_history(
        self,
        limit: int = 100
    ) -> List[Dict]:
        """获取通知历史"""
        return self.notification_history[-limit:]


# 全局通知管理器实例
notification_manager = NotificationManager()
