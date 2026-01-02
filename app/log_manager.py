"""
日志管理增强模块
提供日志导出、日志分析等高级功能
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.audit_log import AuditLog, AuditLogAction, AuditLogLevel
from app.report_export import ReportExporter
import logging
import json
import pandas as pd
from collections import defaultdict

logger = logging.getLogger(__name__)


class LogManager:
    """日志管理器"""

    def __init__(self, db: Session):
        self.db = db
        self.report_exporter = ReportExporter()

    def export_logs_to_csv(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        level: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success: Optional[bool] = None
    ) -> str:
        """
        导出审计日志到CSV

        Args:
            user_id: 用户ID筛选
            action: 操作类型筛选
            resource: 资源类型筛选
            level: 日志级别筛选
            start_date: 开始日期
            end_date: 结束日期
            success: 成功状态筛选

        Returns:
            导出文件的路径
        """
        logger.info(f"开始导出审计日志到CSV")

        # 构建查询
        query = self.db.query(AuditLog)

        # 应用筛选条件
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)

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

        # 按时间排序
        query = query.order_by(AuditLog.created_at.desc())

        # 查询所有日志
        logs = query.all()

        # 转换为DataFrame
        data = []
        for log in logs:
            data.append({
                "ID": log.id,
                "用户ID": log.user_id,
                "用户名": log.username,
                "操作": log.action,
                "资源": log.resource,
                "资源ID": log.resource_id,
                "级别": log.level,
                "详情": log.details,
                "IP地址": log.ip_address,
                "是否成功": "是" if log.success else "否",
                "错误信息": log.error_message,
                "创建时间": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else ""
            })

        df = pd.DataFrame(data)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/audit_logs_{timestamp}.csv"

        # 导出CSV
        df.to_csv(filename, index=False, encoding='utf-8-sig')

        logger.info(f"审计日志导出完成: {filename}, 共 {len(logs)} 条记录")

        return filename

    def export_logs_to_excel(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        level: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success: Optional[bool] = None
    ) -> str:
        """
        导出审计日志到Excel

        Args:
            user_id: 用户ID筛选
            action: 操作类型筛选
            resource: 资源类型筛选
            level: 日志级别筛选
            start_date: 开始日期
            end_date: 结束日期
            success: 成功状态筛选

        Returns:
            导出文件的路径
        """
        logger.info(f"开始导出审计日志到Excel")

        # 构建查询
        query = self.db.query(AuditLog)

        # 应用筛选条件
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)

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

        # 按时间排序
        query = query.order_by(AuditLog.created_at.desc())

        # 查询所有日志
        logs = query.all()

        # 创建Excel写入器
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/audit_logs_{timestamp}.xlsx"

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Sheet 1: 所有日志
            data = []
            for log in logs:
                data.append({
                    "ID": log.id,
                    "用户ID": log.user_id,
                    "用户名": log.username,
                    "操作": log.action,
                    "资源": log.resource,
                    "资源ID": log.resource_id,
                    "级别": log.level,
                    "详情": log.details,
                    "IP地址": log.ip_address,
                    "是否成功": "是" if log.success else "否",
                    "错误信息": log.error_message,
                    "创建时间": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else ""
                })

            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name='所有日志', index=False)

            # 调整列宽
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                writer.sheets['所有日志'].column_dimensions[chr(65 + df.columns.get_loc(column))].width = min(column_width + 2, 50)

            # Sheet 2: 统计摘要
            summary_data = self.analyze_logs_summary(logs)
            summary_df = pd.DataFrame(list(summary_data.items()), columns=['指标', '值'])
            summary_df.to_excel(writer, sheet_name='统计摘要', index=False)

            # Sheet 3: 按用户统计
            user_stats = self.analyze_logs_by_user(logs)
            user_df = pd.DataFrame(user_stats)
            if not user_df.empty:
                user_df.to_excel(writer, sheet_name='按用户统计', index=False)

            # Sheet 4: 按操作类型统计
            action_stats = self.analyze_logs_by_action(logs)
            action_df = pd.DataFrame(list(action_stats.items()), columns=['操作', '次数'])
            action_df.to_excel(writer, sheet_name='按操作统计', index=False)

            # Sheet 5: 按日志级别统计
            level_stats = self.analyze_logs_by_level(logs)
            level_df = pd.DataFrame(list(level_stats.items()), columns=['级别', '次数'])
            level_df.to_excel(writer, sheet_name='按级别统计', index=False)

            # Sheet 6: 错误日志
            error_logs = [log for log in logs if not log.success or log.level == AuditLogLevel.ERROR.value]
            if error_logs:
                error_data = []
                for log in error_logs:
                    error_data.append({
                        "ID": log.id,
                        "用户名": log.username,
                        "操作": log.action,
                        "资源": log.resource,
                        "错误信息": log.error_message,
                        "创建时间": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else ""
                    })
                error_df = pd.DataFrame(error_data)
                error_df.to_excel(writer, sheet_name='错误日志', index=False)

        logger.info(f"审计日志导出完成: {filename}, 共 {len(logs)} 条记录")

        return filename

    def analyze_logs_summary(self, logs: List[AuditLog]) -> Dict[str, Any]:
        """
        分析日志摘要

        Args:
            logs: 日志列表

        Returns:
            摘要统计
        """
        total = len(logs)
        if total == 0:
            return {}

        success_count = sum(1 for log in logs if log.success)
        failure_count = total - success_count

        # 按时间范围
        dates = [log.created_at for log in logs if log.created_at]
        date_range = (min(dates), max(dates)) if dates else (None, None)

        # 统计唯一用户数
        unique_users = len(set(log.user_id for log in logs if log.user_id))

        return {
            "总日志数": total,
            "成功": success_count,
            "失败": failure_count,
            "成功率": f"{(success_count / total * 100):.2f}%",
            "唯一用户数": unique_users,
            "最早时间": date_range[0].strftime("%Y-%m-%d %H:%M:%S") if date_range[0] else "",
            "最晚时间": date_range[1].strftime("%Y-%m-%d %H:%M:%S") if date_range[1] else ""
        }

    def analyze_logs_by_user(self, logs: List[AuditLog]) -> List[Dict[str, Any]]:
        """
        按用户分析日志

        Args:
            logs: 日志列表

        Returns:
            用户统计列表
        """
        user_stats = defaultdict(lambda: {
            "用户ID": 0,
            "用户名": "",
            "操作次数": 0,
            "成功次数": 0,
            "失败次数": 0,
            "成功率": 0.0,
            "最后操作": ""
        })

        for log in logs:
            if not log.user_id:
                continue

            user_id = log.user_id
            user_stats[user_id]["用户ID"] = user_id
            user_stats[user_id]["用户名"] = log.username or ""

            user_stats[user_id]["操作次数"] += 1
            if log.success:
                user_stats[user_id]["成功次数"] += 1
            else:
                user_stats[user_id]["失败次数"] += 1

            # 更新最后操作时间
            if log.created_at:
                current_last = user_stats[user_id]["最后操作"]
                if not current_last or log.created_at > datetime.strptime(current_last, "%Y-%m-%d %H:%M:%S"):
                    user_stats[user_id]["最后操作"] = log.created_at.strftime("%Y-%m-%d %H:%M:%S")

        # 计算成功率
        result = []
        for user_id, stats in user_stats.items():
            total = stats["操作次数"]
            stats["成功率"] = (stats["成功次数"] / total * 100) if total > 0 else 0.0
            stats["成功率"] = f"{stats['成功率']:.2f}%"
            result.append(stats)

        # 按操作次数排序
        result.sort(key=lambda x: x["操作次数"], reverse=True)

        return result

    def analyze_logs_by_action(self, logs: List[AuditLog]) -> Dict[str, int]:
        """
        按操作类型分析日志

        Args:
            logs: 日志列表

        Returns:
            操作类型统计
        """
        action_stats = defaultdict(int)

        for log in logs:
            if log.action:
                action_stats[log.action] += 1

        return dict(action_stats)

    def analyze_logs_by_level(self, logs: List[AuditLog]) -> Dict[str, int]:
        """
        按日志级别分析日志

        Args:
            logs: 日志列表

        Returns:
            日志级别统计
        """
        level_stats = defaultdict(int)

        for log in logs:
            if log.level:
                level_stats[log.level] += 1

        return dict(level_stats)

    def analyze_logs_by_resource(self, logs: List[AuditLog]) -> Dict[str, int]:
        """
        按资源类型分析日志

        Args:
            logs: 日志列表

        Returns:
            资源类型统计
        """
        resource_stats = defaultdict(int)

        for log in logs:
            if log.resource:
                resource_stats[log.resource] += 1

        return dict(resource_stats)

    def analyze_logs_time_distribution(self, logs: List[AuditLog], interval: str = "hour") -> Dict[str, int]:
        """
        分析日志时间分布

        Args:
            logs: 日志列表
            interval: 时间间隔 (hour, day, week, month)

        Returns:
            时间分布统计
        """
        time_stats = defaultdict(int)

        for log in logs:
            if not log.created_at:
                continue

            if interval == "hour":
                key = log.created_at.strftime("%Y-%m-%d %H:00")
            elif interval == "day":
                key = log.created_at.strftime("%Y-%m-%d")
            elif interval == "week":
                key = log.created_at.strftime("%Y-W%U")
            elif interval == "month":
                key = log.created_at.strftime("%Y-%m")
            else:
                continue

            time_stats[key] += 1

        return dict(sorted(time_stats.items()))

    def detect_anomalies(
        self,
        logs: List[AuditLog],
        threshold: int = 10
    ) -> List[Dict[str, Any]]:
        """
        检测异常行为

        Args:
            logs: 日志列表
            threshold: 异常阈值

        Returns:
            异常行为列表
        """
        anomalies = []

        # 1. 检测频繁失败的操作
        action_failures = defaultdict(int)
        for log in logs:
            if not log.success and log.action:
                action_failures[log.action] += 1

        for action, count in action_failures.items():
            if count >= threshold:
                anomalies.append({
                    "类型": "频繁失败",
                    "描述": f"操作 '{action}' 失败次数异常: {count} 次",
                    "严重程度": "高" if count >= threshold * 2 else "中"
                })

        # 2. 检测高频操作
        user_actions = defaultdict(lambda: defaultdict(int))
        for log in logs:
            if log.user_id and log.action:
                user_actions[log.user_id][log.action] += 1

        for user_id, actions in user_actions.items():
            for action, count in actions.items():
                if count >= threshold * 3:  # 操作频率超过阈值3倍
                    anomalies.append({
                        "类型": "高频操作",
                        "描述": f"用户 {user_id} 在短时间内频繁执行 '{action}' 操作: {count} 次",
                        "严重程度": "高" if count >= threshold * 5 else "中"
                    })

        # 3. 检测异常IP
        ip_actions = defaultdict(int)
        for log in logs:
            if log.ip_address:
                ip_actions[log.ip_address] += 1

        for ip, count in ip_actions.items():
            if count >= threshold * 5:
                anomalies.append({
                    "类型": "异常IP",
                    "描述": f"IP {ip} 操作次数异常: {count} 次",
                    "严重程度": "高"
                })

        # 4. 检测未授权访问尝试
        unauthorized = [log for log in logs if not log.success and log.action in ["create", "update", "delete"]]
        if len(unauthorized) >= threshold:
            anomalies.append({
                "类型": "未授权访问",
                "描述": f"检测到 {len(unauthorized)} 次未授权访问尝试",
                "严重程度": "高"
            })

        return anomalies

    def analyze_user_behavior(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        分析用户行为模式

        Args:
            user_id: 用户ID
            days: 分析天数

        Returns:
            用户行为分析结果
        """
        # 获取指定时间段的日志
        start_date = datetime.now() - timedelta(days=days)
        logs = self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= start_date
        ).order_by(AuditLog.created_at.desc()).all()

        if not logs:
            return {
                "用户ID": user_id,
                "分析结果": "该时间段内无活动记录"
            }

        # 基本统计
        total_actions = len(logs)
        success_actions = sum(1 for log in logs if log.success)
        failure_actions = total_actions - success_actions

        # 操作类型分布
        action_distribution = defaultdict(int)
        for log in logs:
            if log.action:
                action_distribution[log.action] += 1

        # 资源类型分布
        resource_distribution = defaultdict(int)
        for log in logs:
            if log.resource:
                resource_distribution[log.resource] += 1

        # 活动时间分布
        hourly_activity = defaultdict(int)
        for log in logs:
            if log.created_at:
                hour = log.created_at.hour
                hourly_activity[hour] += 1

        # 找出最活跃的时间段
        most_active_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else 0

        # IP地址
        unique_ips = set(log.ip_address for log in logs if log.ip_address)

        return {
            "用户ID": user_id,
            "分析天数": days,
            "总操作数": total_actions,
            "成功操作": success_actions,
            "失败操作": failure_actions,
            "成功率": f"{(success_actions / total_actions * 100):.2f}%" if total_actions > 0 else "0%",
            "最常执行的操作": sorted(action_distribution.items(), key=lambda x: x[1], reverse=True)[:5],
            "最常访问的资源": sorted(resource_distribution.items(), key=lambda x: x[1], reverse=True)[:5],
            "最活跃时段": f"{most_active_hour}:00-{most_active_hour+1}:00",
            "使用的IP地址数": len(unique_ips),
            "最近活动时间": logs[0].created_at.strftime("%Y-%m-%d %H:%M:%S") if logs[0].created_at else ""
        }
