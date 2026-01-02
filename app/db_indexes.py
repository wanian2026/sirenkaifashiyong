"""
数据库索引管理模块
用于创建、检查和管理数据库索引
"""

from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
from app.database import engine
import logging

logger = logging.getLogger(__name__)


class IndexManager:
    """索引管理器"""

    def __init__(self, engine: Engine = None):
        self.engine = engine or engine

    def get_existing_indexes(self, table_name: str) -> list:
        """
        获取表的现有索引

        Args:
            table_name: 表名

        Returns:
            索引列表
        """
        try:
            inspector = inspect(self.engine)
            indexes = inspector.get_indexes(table_name)
            return [idx['name'] for idx in indexes]
        except Exception as e:
            logger.error(f"获取表 {table_name} 的索引失败: {e}")
            return []

    def index_exists(self, table_name: str, index_name: str) -> bool:
        """
        检查索引是否存在

        Args:
            table_name: 表名
            index_name: 索引名

        Returns:
            是否存在
        """
        existing_indexes = self.get_existing_indexes(table_name)
        return index_name in existing_indexes

    def create_index(
        self,
        table_name: str,
        index_name: str,
        columns: list,
        unique: bool = False
    ) -> bool:
        """
        创建索引

        Args:
            table_name: 表名
            index_name: 索引名
            columns: 列列表
            unique: 是否唯一索引

        Returns:
            是否成功
        """
        try:
            # 检查索引是否已存在
            if self.index_exists(table_name, index_name):
                logger.info(f"索引 {index_name} 已存在，跳过创建")
                return True

            # 创建索引
            with self.engine.connect() as conn:
                unique_sql = "UNIQUE " if unique else ""
                columns_sql = ", ".join(columns)
                sql = f"CREATE {unique_sql}INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_sql})"

                logger.info(f"创建索引: {sql}")
                conn.execute(text(sql))
                conn.commit()

                logger.info(f"成功创建索引: {index_name}")
                return True

        except Exception as e:
            logger.error(f"创建索引 {index_name} 失败: {e}")
            return False

    def drop_index(self, table_name: str, index_name: str) -> bool:
        """
        删除索引

        Args:
            table_name: 表名
            index_name: 索引名

        Returns:
            是否成功
        """
        try:
            if not self.index_exists(table_name, index_name):
                logger.warning(f"索引 {index_name} 不存在，无法删除")
                return False

            with self.engine.connect() as conn:
                sql = f"DROP INDEX IF EXISTS {index_name}"
                conn.execute(text(sql))
                conn.commit()

                logger.info(f"成功删除索引: {index_name}")
                return True

        except Exception as e:
            logger.error(f"删除索引 {index_name} 失败: {e}")
            return False

    def create_all_indexes(self) -> dict:
        """
        创建所有推荐的索引

        Returns:
            创建结果
        """
        results = {
            'success': [],
            'failed': []
        }

        # 定义需要创建的索引
        indexes_to_create = [
            {
                'table': 'trading_bots',
                'name': 'idx_trading_bots_user_status',
                'columns': ['user_id', 'status'],
                'unique': False
            },
            {
                'table': 'grid_orders',
                'name': 'idx_grid_orders_bot_status',
                'columns': ['bot_id', 'status'],
                'unique': False
            },
            {
                'table': 'grid_orders',
                'name': 'idx_grid_orders_bot_level',
                'columns': ['bot_id', 'level'],
                'unique': False
            },
            {
                'table': 'trades',
                'name': 'idx_trades_bot_created',
                'columns': ['bot_id', 'created_at'],
                'unique': False
            },
            {
                'table': 'trades',
                'name': 'idx_trades_bot_side_created',
                'columns': ['bot_id', 'side', 'created_at'],
                'unique': False
            },
            {
                'table': 'grid_orders',
                'name': 'idx_grid_orders_trading_pair',
                'columns': ['trading_pair'],
                'unique': False
            },
            {
                'table': 'trades',
                'name': 'idx_trades_trading_pair',
                'columns': ['trading_pair'],
                'unique': False
            }
        ]

        # 批量创建索引
        for index_info in indexes_to_create:
            success = self.create_index(
                table_name=index_info['table'],
                index_name=index_info['name'],
                columns=index_info['columns'],
                unique=index_info.get('unique', False)
            )

            if success:
                results['success'].append(index_info['name'])
            else:
                results['failed'].append(index_info['name'])

        return results

    def analyze_index_usage(self) -> dict:
        """
        分析索引使用情况（SQLite简化版）

        Returns:
            索引使用分析
        """
        results = {}

        try:
            with self.engine.connect() as conn:
                # 获取所有表
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()

                for table_name in tables:
                    indexes = inspector.get_indexes(table_name)

                    results[table_name] = {
                        'index_count': len(indexes),
                        'indexes': [
                            {
                                'name': idx['name'],
                                'columns': idx['column_names'],
                                'unique': idx['unique']
                            }
                            for idx in indexes
                        ]
                    }

        except Exception as e:
            logger.error(f"分析索引使用情况失败: {e}")
            results['error'] = str(e)

        return results

    def get_optimization_recommendations(self) -> list:
        """
        获取索引优化建议

        Returns:
            优化建议列表
        """
        recommendations = []

        # 分析现有索引
        index_usage = self.analyze_index_usage()

        # 检查是否有表没有适当的索引
        tables_without_indexes = [
            table for table, info in index_usage.items()
            if isinstance(info, dict) and info.get('index_count', 0) == 0
        ]

        if tables_without_indexes:
            recommendations.append(
                f"以下表没有索引，建议添加: {', '.join(tables_without_indexes)}"
            )

        # 检查是否有重复索引
        # （简化版本，实际实现需要更复杂的逻辑）

        # 建议定期分析
        recommendations.append("建议定期执行 ANALYZE 命令更新统计信息")
        recommendations.append("建议定期执行 VACUUM 命令回收空间")

        return recommendations


# ==================== 快捷函数 ====================

def create_all_database_indexes():
    """
    创建所有数据库索引的快捷函数

    Returns:
        创建结果
    """
    manager = IndexManager()
    return manager.create_all_indexes()


def analyze_database_indexes():
    """
    分析数据库索引的快捷函数

    Returns:
        分析结果
    """
    manager = IndexManager()
    return manager.analyze_index_usage()


def get_index_recommendations():
    """
    获取索引优化建议的快捷函数

    Returns:
        建议列表
    """
    manager = IndexManager()
    return manager.get_optimization_recommendations()


if __name__ == "__main__":
    # 测试代码
    print("=== 创建所有数据库索引 ===")
    result = create_all_database_indexes()
    print(f"成功: {len(result['success'])}, 失败: {len(result['failed'])}")
    print(f"成功创建的索引: {result['success']}")
    if result['failed']:
        print(f"失败的索引: {result['failed']}")

    print("\n=== 分析数据库索引 ===")
    analysis = analyze_database_indexes()
    for table, info in analysis.items():
        if isinstance(info, dict):
            print(f"{table}: {info['index_count']} 个索引")

    print("\n=== 优化建议 ===")
    recommendations = get_index_recommendations()
    for rec in recommendations:
        print(f"- {rec}")
