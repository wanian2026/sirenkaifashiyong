"""
数据库管理模块
提供数据库备份、恢复、清理等管理功能
"""

import os
import shutil
import gzip
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from app.database import engine, get_db
from app.models import (
    Base, User, TradingBot, GridOrder, Trade
)
from app.audit_log import AuditLog

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_url: str = None):
        self.db_url = db_url or str(engine.url)
        self.backup_dir = "backups"
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """确保备份目录存在"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            logger.info(f"创建备份目录: {self.backup_dir}")

    def backup_database(
        self,
        description: str = None,
        compress: bool = True
    ) -> str:
        """
        备份数据库

        Args:
            description: 备份描述
            compress: 是否压缩备份文件

        Returns:
            备份文件路径
        """
        logger.info(f"开始备份数据库: {self.db_url}")

        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.sql"
        filepath = os.path.join(self.backup_dir, filename)

        # 构建备份命令
        if self.db_url.startswith("sqlite"):
            # SQLite备份：直接复制数据库文件
            backup_cmd = self._backup_sqlite(filepath, description)
        elif "postgresql" in self.db_url:
            # PostgreSQL备份：使用pg_dump
            backup_cmd = self._backup_postgresql(filepath, description)
        elif "mysql" in self.db_url:
            # MySQL备份：使用mysqldump
            backup_cmd = self._backup_mysql(filepath, description)
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_url}")

        logger.info(f"数据库备份完成: {filepath}")
        return filepath

    def _backup_sqlite(self, filepath: str, description: str = None) -> str:
        """
        备份SQLite数据库

        Args:
            filepath: 备份文件路径
            description: 备份描述

        Returns:
            备份文件路径
        """
        # 提取SQLite数据库文件路径
        from urllib.parse import urlparse
        parsed = urlparse(self.db_url)
        db_path = parsed.path

        if not os.path.exists(db_path):
            raise FileNotFoundError(f"数据库文件不存在: {db_path}")

        # 复制数据库文件
        shutil.copy2(db_path, filepath)

        # 创建备份元数据
        self._create_backup_metadata(filepath, description, "sqlite")

        logger.info(f"SQLite数据库备份完成: {filepath}")
        return filepath

    def _backup_postgresql(self, filepath: str, description: str = None) -> str:
        """
        备份PostgreSQL数据库

        Args:
            filepath: 备份文件路径
            description: 备份描述

        Returns:
            备份文件路径
        """
        from urllib.parse import urlparse
        parsed = urlparse(self.db_url)

        dbname = parsed.path.lstrip('/')
        username = parsed.username
        password = parsed.password
        host = parsed.hostname or 'localhost'
        port = parsed.port or 5432

        # 构建pg_dump命令
        cmd = f"PGPASSWORD={password} pg_dump -h {host} -p {port} -U {username} -F c {dbname} > {filepath}"

        # 执行备份命令
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"PostgreSQL备份失败: {result.stderr}")

        # 创建备份元数据
        self._create_backup_metadata(filepath, description, "postgresql")

        logger.info(f"PostgreSQL数据库备份完成: {filepath}")
        return filepath

    def _backup_mysql(self, filepath: str, description: str = None) -> str:
        """
        备份MySQL数据库

        Args:
            filepath: 备份文件路径
            description: 备份描述

        Returns:
            备份文件路径
        """
        from urllib.parse import urlparse
        parsed = urlparse(self.db_url)

        dbname = parsed.path.lstrip('/')
        username = parsed.username
        password = parsed.password
        host = parsed.hostname or 'localhost'
        port = parsed.port or 3306

        # 构建mysqldump命令
        cmd = f"mysqldump -h {host} -P {port} -u {username} -p{password} {dbname} > {filepath}"

        # 执行备份命令
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"MySQL备份失败: {result.stderr}")

        # 创建备份元数据
        self._create_backup_metadata(filepath, description, "mysql")

        logger.info(f"MySQL数据库备份完成: {filepath}")
        return filepath

    def _create_backup_metadata(self, filepath: str, description: str, db_type: str):
        """创建备份元数据"""
        metadata = {
            "filename": os.path.basename(filepath),
            "created_at": datetime.now().isoformat(),
            "database_type": db_type,
            "database_url": self.db_url,
            "description": description or "",
            "size": os.path.getsize(filepath)
        }

        metadata_path = filepath + ".meta"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.debug(f"创建备份元数据: {metadata_path}")

    def restore_database(self, backup_file: str) -> Dict[str, Any]:
        """
        从备份文件恢复数据库

        Args:
            backup_file: 备份文件路径

        Returns:
            恢复结果
        """
        logger.info(f"开始恢复数据库: {backup_file}")

        # 检查备份文件是否存在
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f"备份文件不存在: {backup_file}")

        # 检查备份元数据
        metadata_path = backup_file + ".meta"
        if not os.path.exists(metadata_path):
            logger.warning("未找到备份元数据，继续恢复...")

        # 读取元数据
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

        # 根据数据库类型执行恢复
        db_type = metadata.get("database_type", "unknown")

        if db_type == "sqlite":
            result = self._restore_sqlite(backup_file, metadata)
        elif db_type == "postgresql":
            result = self._restore_postgresql(backup_file, metadata)
        elif db_type == "mysql":
            result = self._restore_mysql(backup_file, metadata)
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")

        logger.info(f"数据库恢复完成: {backup_file}")
        return result

    def _restore_sqlite(self, backup_file: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """恢复SQLite数据库"""
        from urllib.parse import urlparse
        parsed = urlparse(self.db_url)
        db_path = parsed.path

        # 备份当前数据库
        current_backup = f"{db_path}.restore_backup"
        if os.path.exists(db_path):
            shutil.copy2(db_path, current_backup)

        try:
            # 恢复数据库
            shutil.copy2(backup_file, db_path)

            return {
                "success": True,
                "message": "SQLite数据库恢复成功",
                "backup_file": backup_file,
                "current_backup": current_backup,
                "metadata": metadata
            }
        except Exception as e:
            # 恢复失败，还原当前数据库
            if os.path.exists(current_backup):
                shutil.copy2(current_backup, db_path)
            raise e

    def _restore_postgresql(self, backup_file: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """恢复PostgreSQL数据库"""
        from urllib.parse import urlparse
        parsed = urlparse(self.db_url)

        dbname = parsed.path.lstrip('/')
        username = parsed.username
        password = parsed.password
        host = parsed.hostname or 'localhost'
        port = parsed.port or 5432

        # 构建pg_restore命令
        cmd = f"PGPASSWORD={password} pg_restore -h {host} -p {port} -U {username} -d {dbname} -c {backup_file}"

        # 执行恢复命令
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"PostgreSQL恢复失败: {result.stderr}")

        return {
            "success": True,
            "message": "PostgreSQL数据库恢复成功",
            "backup_file": backup_file,
            "metadata": metadata
        }

    def _restore_mysql(self, backup_file: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """恢复MySQL数据库"""
        from urllib.parse import urlparse
        parsed = urlparse(self.db_url)

        dbname = parsed.path.lstrip('/')
        username = parsed.username
        password = parsed.password
        host = parsed.hostname or 'localhost'
        port = parsed.port or 3306

        # 构建mysql命令
        cmd = f"mysql -h {host} -P {port} -u {username} -p{password} {dbname} < {backup_file}"

        # 执行恢复命令
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"MySQL恢复失败: {result.stderr}")

        return {
            "success": True,
            "message": "MySQL数据库恢复成功",
            "backup_file": backup_file,
            "metadata": metadata
        }

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        列出所有备份文件

        Returns:
            备份文件列表
        """
        backups = []

        for filename in os.listdir(self.backup_dir):
            filepath = os.path.join(self.backup_dir, filename)

            # 跳过元数据文件
            if filename.endswith(".meta"):
                continue

            # 读取元数据
            metadata_path = filepath + ".meta"
            metadata = {}
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception as e:
                    logger.warning(f"读取备份元数据失败: {e}")

            backups.append({
                "filename": filename,
                "path": filepath,
                "size": os.path.getsize(filepath),
                "created_at": metadata.get("created_at", ""),
                "description": metadata.get("description", ""),
                "database_type": metadata.get("database_type", "unknown")
            })

        # 按创建时间排序
        backups.sort(key=lambda x: x["created_at"], reverse=True)

        return backups

    def delete_backup(self, filename: str) -> bool:
        """
        删除备份文件

        Args:
            filename: 备份文件名

        Returns:
            是否删除成功
        """
        filepath = os.path.join(self.backup_dir, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"备份文件不存在: {filename}")

        # 删除备份文件和元数据
        os.remove(filepath)
        metadata_path = filepath + ".meta"
        if os.path.exists(metadata_path):
            os.remove(metadata_path)

        logger.info(f"删除备份文件: {filepath}")
        return True

    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """
        清理旧的备份文件

        Args:
            keep_days: 保留天数

        Returns:
            删除的文件数量
        """
        logger.info(f"开始清理旧备份文件，保留最近 {keep_days} 天的备份")

        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0

        for filename in os.listdir(self.backup_dir):
            filepath = os.path.join(self.backup_dir, filename)

            # 跳过元数据文件
            if filename.endswith(".meta"):
                continue

            # 获取文件创建时间
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))

            # 如果文件过期，删除
            if file_time < cutoff_date:
                try:
                    self.delete_backup(filename)
                    deleted_count += 1
                    logger.info(f"删除旧备份: {filename}")
                except Exception as e:
                    logger.error(f"删除备份失败: {filename}, 错误: {e}")

        logger.info(f"清理完成，删除了 {deleted_count} 个旧备份文件")
        return deleted_count

    def cleanup_old_data(
        self,
        days: int = 90,
        tables: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        清理旧的数据库数据

        Args:
            days: 保留天数
            tables: 要清理的表列表，None表示所有表

        Returns:
            清理结果
        """
        logger.info(f"开始清理旧数据，保留最近 {days} 天的数据")

        cutoff_date = datetime.now() - timedelta(days=days)
        results = {}

        # 定义可清理的表及其时间字段
        cleanable_tables = {
            "audit_logs": "created_at",
            "trades": "created_at"
        }

        # 如果指定了表，只清理这些表
        if tables:
            cleanable_tables = {k: v for k, v in cleanable_tables.items() if k in tables}

        # 使用数据库会话
        from contextlib import contextmanager

        @contextmanager
        def get_db_session():
            db = next(get_db())
            try:
                yield db
            finally:
                db.close()

        with get_db_session() as db:
            for table_name, date_field in cleanable_tables.items():
                try:
                    # 构建删除SQL
                    delete_sql = text(f"""
                        DELETE FROM {table_name}
                        WHERE {date_field} < :cutoff_date
                    """)

                    # 执行删除
                    result = db.execute(delete_sql, {"cutoff_date": cutoff_date})
                    deleted_count = result.rowcount
                    db.commit()

                    results[table_name] = deleted_count
                    logger.info(f"清理表 {table_name}: 删除了 {deleted_count} 条记录")

                except Exception as e:
                    logger.error(f"清理表 {table_name} 失败: {e}")
                    results[table_name] = -1

        total_deleted = sum(r for r in results.values() if r > 0)
        logger.info(f"数据清理完成，总共删除了 {total_deleted} 条记录")

        return {
            "total_deleted": total_deleted,
            "tables": results
        }

    def get_database_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            数据库统计信息
        """
        stats = {}

        # 使用数据库会话
        from contextlib import contextmanager

        @contextmanager
        def get_db_session():
            db = next(get_db())
            try:
                yield db
            finally:
                db.close()

        with get_db_session() as db:
            # 获取所有表
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            for table_name in tables:
                try:
                    # 获取表记录数
                    count_sql = text(f"SELECT COUNT(*) FROM {table_name}")
                    count_result = db.execute(count_sql).scalar()

                    stats[table_name] = {
                        "records": count_result
                    }

                    # 获取表大小（仅SQLite）
                    if self.db_url.startswith("sqlite"):
                        from urllib.parse import urlparse
                        parsed = urlparse(self.db_url)
                        db_path = parsed.path

                        # 计算表大小（简化版）
                        table_size = os.path.getsize(db_path)
                        stats[table_name]["size_bytes"] = table_size

                except Exception as e:
                    logger.warning(f"获取表 {table_name} 统计信息失败: {e}")
                    stats[table_name] = {
                        "error": str(e)
                    }

        return stats

    def optimize_database(self) -> Dict[str, Any]:
        """
        优化数据库

        Returns:
            优化结果
        """
        logger.info("开始优化数据库")

        results = {}

        from contextlib import contextmanager

        @contextmanager
        def get_db_session():
            db = next(get_db())
            try:
                yield db
            finally:
                db.close()

        with get_db_session() as db:
            if self.db_url.startswith("sqlite"):
                # SQLite优化
                try:
                    db.execute(text("VACUUM"))
                    db.execute(text("ANALYZE"))
                    db.commit()
                    results["message"] = "SQLite数据库优化完成"
                except Exception as e:
                    logger.error(f"SQLite优化失败: {e}")
                    results["error"] = str(e)

            elif "postgresql" in self.db_url:
                # PostgreSQL优化
                try:
                    db.execute(text("VACUUM ANALYZE"))
                    db.commit()
                    results["message"] = "PostgreSQL数据库优化完成"
                except Exception as e:
                    logger.error(f"PostgreSQL优化失败: {e}")
                    results["error"] = str(e)

            elif "mysql" in self.db_url:
                # MySQL优化
                try:
                    db.execute(text("OPTIMIZE TABLE audit_logs"))
                    db.execute(text("OPTIMIZE TABLE trades"))
                    db.commit()
                    results["message"] = "MySQL数据库优化完成"
                except Exception as e:
                    logger.error(f"MySQL优化失败: {e}")
                    results["error"] = str(e)

        logger.info("数据库优化完成")
        return results
