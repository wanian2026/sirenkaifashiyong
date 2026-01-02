"""
性能监控模块
提供系统指标监控、性能指标收集等功能
"""

import psutil
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque
from threading import Thread, Lock
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import engine

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.metrics_history = {
            "cpu": deque(maxlen=max_history),
            "memory": deque(maxlen=max_history),
            "disk": deque(maxlen=max_history),
            "network": deque(maxlen=max_history),
            "api_performance": deque(maxlen=max_history),
            "db_performance": deque(maxlen=max_history)
        }
        self.lock = Lock()
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self, interval: int = 5):
        """
        启动性能监控

        Args:
            interval: 监控间隔（秒）
        """
        if self.monitoring:
            logger.warning("性能监控已经在运行")
            return

        self.monitoring = True
        self.monitor_thread = Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self.monitor_thread.start()
        logger.info(f"性能监控已启动，监控间隔: {interval}秒")

    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("性能监控已停止")

    def _monitor_loop(self, interval: int):
        """监控循环"""
        while self.monitoring:
            try:
                # 收集系统指标
                self._collect_system_metrics()

                # 收集API性能指标
                self._collect_api_performance()

                # 收集数据库性能指标
                self._collect_db_performance()

            except Exception as e:
                logger.error(f"收集性能指标失败: {e}")

            time.sleep(interval)

    def _collect_system_metrics(self):
        """收集系统指标"""
        timestamp = datetime.now()

        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # 内存指标
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # 磁盘指标
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()

        # 网络指标
        network = psutil.net_io_counters()

        metrics = {
            "timestamp": timestamp.isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "freq_current": cpu_freq.current if cpu_freq else 0,
                "freq_max": cpu_freq.max if cpu_freq else 0
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "percent": swap.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
                "errors_in": network.errin,
                "errors_out": network.errout
            }
        }

        # 如果有磁盘IO指标，添加到metrics
        if disk_io:
            metrics["disk_io"] = {
                "read_bytes": disk_io.read_bytes,
                "write_bytes": disk_io.write_bytes,
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count
            }

        with self.lock:
            self.metrics_history["cpu"].append(metrics)
            self.metrics_history["memory"].append(metrics)
            self.metrics_history["disk"].append(metrics)
            self.metrics_history["network"].append(metrics)

        logger.debug(f"系统指标收集完成: CPU {cpu_percent}%, 内存 {memory.percent}%")

    def _collect_api_performance(self):
        """收集API性能指标（示例）"""
        timestamp = datetime.now()

        # 这里可以从中间件或日志中收集真实的API性能数据
        # 暂时使用模拟数据
        metrics = {
            "timestamp": timestamp.isoformat(),
            "request_count": 0,  # 需要从实际请求中收集
            "avg_response_time": 0.0,
            "error_count": 0,
            "slow_requests": 0
        }

        with self.lock:
            self.metrics_history["api_performance"].append(metrics)

    def _collect_db_performance(self):
        """收集数据库性能指标"""
        timestamp = datetime.now()

        try:
            # 测试数据库连接时间
            start_time = time.time()
            from contextlib import contextmanager

            @contextmanager
            def get_db_session():
                from app.database import SessionLocal
                db = SessionLocal()
                try:
                    yield db
                finally:
                    db.close()

            with get_db_session() as db:
                db.execute(text("SELECT 1"))
            connection_time = (time.time() - start_time) * 1000  # 转换为毫秒

            # 查询数据库表行数
            start_time = time.time()
            with get_db_session() as db:
                result = db.execute(text("SELECT COUNT(*) FROM trades"))
                result.fetchone()
            query_time = (time.time() - start_time) * 1000  # 转换为毫秒

            metrics = {
                "timestamp": timestamp.isoformat(),
                "connection_time_ms": connection_time,
                "query_time_ms": query_time,
                "total_queries": 1,  # 示例
                "slow_queries": 0
            }

        except Exception as e:
            logger.error(f"收集数据库性能指标失败: {e}")
            metrics = {
                "timestamp": timestamp.isoformat(),
                "error": str(e)
            }

        with self.lock:
            self.metrics_history["db_performance"].append(metrics)

    def get_system_status(self) -> Dict[str, Any]:
        """
        获取当前系统状态

        Returns:
            系统状态信息
        """
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # 内存
        memory = psutil.virtual_memory()

        # 磁盘
        disk = psutil.disk_usage('/')

        # 进程
        process = psutil.Process()
        process_memory = process.memory_info()

        # 启动时间
        boot_time = datetime.fromtimestamp(psutil.boot_time())

        return {
            "timestamp": datetime.now().isoformat(),
            "hostname": psutil.os.uname().nodename,
            "system": psutil.os.uname().system,
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "freq_current": cpu_freq.current if cpu_freq else 0,
                "freq_max": cpu_freq.max if cpu_freq else 0
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "process": {
                "pid": process.pid,
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process.cpu_percent()
            },
            "boot_time": boot_time.isoformat(),
            "uptime": str(datetime.now() - boot_time)
        }

    def get_metrics_history(
        self,
        metric_type: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取指标历史数据

        Args:
            metric_type: 指标类型 (cpu, memory, disk, network, api_performance, db_performance)
            limit: 返回记录数

        Returns:
            指标历史数据
        """
        with self.lock:
            if metric_type not in self.metrics_history:
                raise ValueError(f"不支持的指标类型: {metric_type}")

            history = list(self.metrics_history[metric_type])
            return history[-limit:]

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要

        Returns:
            性能摘要
        """
        summary = {}

        # CPU摘要
        cpu_history = self.get_metrics_history("cpu")
        if cpu_history:
            cpu_values = [m["cpu"]["percent"] for m in cpu_history]
            summary["cpu"] = {
                "current": cpu_values[-1] if cpu_values else 0,
                "min": min(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
                "avg": sum(cpu_values) / len(cpu_values) if cpu_values else 0
            }

        # 内存摘要
        memory_history = self.get_metrics_history("memory")
        if memory_history:
            memory_values = [m["memory"]["percent"] for m in memory_history]
            summary["memory"] = {
                "current": memory_values[-1] if memory_values else 0,
                "min": min(memory_values) if memory_values else 0,
                "max": max(memory_values) if memory_values else 0,
                "avg": sum(memory_values) / len(memory_values) if memory_values else 0
            }

        # 数据库性能摘要
        db_history = self.get_metrics_history("db_performance")
        if db_history:
            valid_db = [m for m in db_history if "error" not in m]
            if valid_db:
                conn_times = [m["connection_time_ms"] for m in valid_db]
                query_times = [m["query_time_ms"] for m in valid_db]
                summary["database"] = {
                    "connection_time": {
                        "current": conn_times[-1] if conn_times else 0,
                        "min": min(conn_times) if conn_times else 0,
                        "max": max(conn_times) if conn_times else 0,
                        "avg": sum(conn_times) / len(conn_times) if conn_times else 0
                    },
                    "query_time": {
                        "current": query_times[-1] if query_times else 0,
                        "min": min(query_times) if query_times else 0,
                        "max": max(query_times) if query_times else 0,
                        "avg": sum(query_times) / len(query_times) if query_times else 0
                    }
                }

        return summary

    def check_health(self) -> Dict[str, Any]:
        """
        检查系统健康状态

        Returns:
            健康状态
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "checks": {}
        }

        # 检查CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_status = "ok" if cpu_percent < 80 else "warning" if cpu_percent < 90 else "critical"
        status["checks"]["cpu"] = {
            "status": cpu_status,
            "value": cpu_percent,
            "message": f"CPU使用率 {cpu_percent}%"
        }

        # 检查内存使用率
        memory = psutil.virtual_memory()
        memory_status = "ok" if memory.percent < 80 else "warning" if memory.percent < 90 else "critical"
        status["checks"]["memory"] = {
            "status": memory_status,
            "value": memory.percent,
            "message": f"内存使用率 {memory.percent}%"
        }

        # 检查磁盘使用率
        disk = psutil.disk_usage('/')
        disk_status = "ok" if disk.percent < 80 else "warning" if disk.percent < 90 else "critical"
        status["checks"]["disk"] = {
            "status": disk_status,
            "value": disk.percent,
            "message": f"磁盘使用率 {disk.percent}%"
        }

        # 检查数据库连接
        try:
            from contextlib import contextmanager

            @contextmanager
            def get_db_session():
                from app.database import SessionLocal
                db = SessionLocal()
                try:
                    yield db
                finally:
                    db.close()

            with get_db_session() as db:
                db.execute(text("SELECT 1"))

            status["checks"]["database"] = {
                "status": "ok",
                "message": "数据库连接正常"
            }
        except Exception as e:
            status["checks"]["database"] = {
                "status": "critical",
                "message": f"数据库连接失败: {str(e)}"
            }

        # 检查监控状态
        status["checks"]["monitoring"] = {
            "status": "ok" if self.monitoring else "warning",
            "message": "监控运行中" if self.monitoring else "监控未启动"
        }

        # 确定整体状态
        if any(check["status"] == "critical" for check in status["checks"].values()):
            status["status"] = "critical"
        elif any(check["status"] == "warning" for check in status["checks"].values()):
            status["status"] = "warning"

        return status

    def clear_history(self, metric_type: Optional[str] = None):
        """
        清除指标历史

        Args:
            metric_type: 指标类型，None表示清除所有
        """
        with self.lock:
            if metric_type:
                if metric_type in self.metrics_history:
                    self.metrics_history[metric_type].clear()
                    logger.info(f"清除 {metric_type} 指标历史")
            else:
                for key in self.metrics_history:
                    self.metrics_history[key].clear()
                logger.info("清除所有指标历史")


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()
