"""
数据库优化模块
提供数据库性能优化建议和工具
"""

from typing import List, Dict, Optional
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
from app.database import engine
import logging

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """数据库优化器"""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.inspector = inspect(engine)

    def analyze_table_size(self) -> Dict[str, Dict]:
        """
        分析表大小

        Returns:
            各表的大小信息
        """
        results = {}

        # 获取所有表名
        tables = self.inspector.get_table_names()

        for table_name in tables:
            try:
                with self.engine.connect() as conn:
                    # SQLite使用page_count * page_size
                    result = conn.execute(text(f"SELECT COUNT(*) as row_count FROM '{table_name}'"))
                    row_count = result.fetchone()[0]

                    # SQLite表大小（估算）
                    result = conn.execute(text(f"PRAGMA table_info('{table_name}')"))
                    columns = result.fetchall()

                    # 估算行大小
                    row_size = sum(col[2] if col[2] else 50 for col in columns)  # 假设列类型平均50字节
                    estimated_size = row_count * row_size

                    results[table_name] = {
                        'row_count': row_count,
                        'estimated_size_bytes': estimated_size,
                        'estimated_size_mb': estimated_size / (1024 * 1024),
                        'columns': len(columns)
                    }

            except Exception as e:
                logger.error(f"分析表 {table_name} 失败: {e}")
                results[table_name] = {
                    'error': str(e)
                }

        return results

    def analyze_indexes(self) -> Dict[str, List[Dict]]:
        """
        分析索引

        Returns:
            各表的索引信息
        """
        results = {}
        tables = self.inspector.get_table_names()

        for table_name in tables:
            try:
                indexes = self.inspector.get_indexes(table_name)
                results[table_name] = [
                    {
                        'name': idx['name'],
                        'columns': idx['column_names'],
                        'unique': idx['unique']
                    }
                    for idx in indexes
                ]
            except Exception as e:
                logger.error(f"分析索引 {table_name} 失败: {e}")
                results[table_name] = []

        return results

    def suggest_indexes(self) -> List[Dict]:
        """
        建议创建的索引

        Returns:
            索引建议列表
        """
        suggestions = []

        # 分析查询模式（基于常见查询）
        common_queries = [
            {
                'table': 'trades',
                'columns': ['bot_id', 'created_at'],
                'reason': '机器人交易记录查询优化'
            },
            {
                'table': 'trades',
                'columns': ['bot_id', 'side', 'created_at'],
                'reason': '交易记录筛选优化'
            },
            {
                'table': 'grid_orders',
                'columns': ['bot_id', 'status'],
                'reason': '订单状态查询优化'
            },
            {
                'table': 'grid_orders',
                'columns': ['bot_id', 'level'],
                'reason': '网格订单层级查询优化'
            },
            {
                'table': 'trading_bots',
                'columns': ['user_id', 'status'],
                'reason': '用户机器人列表查询优化'
            }
        ]

        # 检查索引是否已存在
        current_indexes = self.analyze_indexes()

        for suggestion in common_queries:
            table = suggestion['table']
            columns = suggestion['columns']

            if table in current_indexes:
                # 检查是否已存在相同索引
                existing = any(
                    set(idx['columns']) == set(columns)
                    for idx in current_indexes[table]
                )

                if not existing:
                    suggestions.append({
                        **suggestion,
                        'index_name': f"idx_{table}_{'_'.join(columns)}",
                        'sql': f"CREATE INDEX idx_{table}_{'_'.join(columns)} ON {table} ({', '.join(columns)});"
                    })

        return suggestions

    def analyze_query_performance(self) -> Dict[str, Dict]]:
        """
        分析查询性能

        Returns:
            查询性能分析结果
        """
        results = {}

        # 测试常见查询
        test_queries = [
            {
                'name': '获取用户机器人列表',
                'sql': "SELECT * FROM trading_bots WHERE user_id = 1",
                'params': {}
            },
            {
                'name': '获取机器人交易记录',
                'sql': "SELECT * FROM trades WHERE bot_id = 1 ORDER BY created_at DESC LIMIT 100",
                'params': {}
            },
            {
                'name': '获取机器人订单列表',
                'sql': "SELECT * FROM grid_orders WHERE bot_id = 1 AND status = 'pending'",
                'params': {}
            },
            {
                'name': '交易统计',
                'sql': "SELECT bot_id, COUNT(*) as trade_count, SUM(profit) as total_profit FROM trades GROUP BY bot_id",
                'params': {}
            }
        ]

        for query_info in test_queries:
            try:
                with self.engine.connect() as conn:
                    import time

                    start_time = time.time()
                    result = conn.execute(text(query_info['sql']))
                    rows = result.fetchall()
                    end_time = time.time()

                    execution_time = end_time - start_time

                    results[query_info['name']] = {
                        'sql': query_info['sql'],
                        'rows_returned': len(rows),
                        'execution_time_ms': execution_time * 1000,
                        'performance': 'good' if execution_time < 0.1 else ('fair' if execution_time < 1.0 else 'poor')
                    }

            except Exception as e:
                logger.error(f"查询性能分析失败: {query_info['name']}, {e}")
                results[query_info['name']] = {
                    'error': str(e)
                }

        return results

    def optimize_database(self) -> Dict:
        """
        优化数据库

        Returns:
            优化结果
        """
        results = {
            'vacuum_performed': False,
            'analyze_performed': False,
            'indexes_suggested': []
        }

        try:
            with self.engine.connect() as conn:
                # SQLite VACUUM
                if self.engine.dialect.name == 'sqlite':
                    logger.info("执行 VACUUM...")
                    conn.execute(text("VACUUM"))
                    conn.commit()
                    results['vacuum_performed'] = True

                # ANALYZE
                logger.info("执行 ANALYZE...")
                conn.execute(text("ANALYZE"))
                conn.commit()
                results['analyze_performed'] = True

                # 获取索引建议
                results['indexes_suggested'] = self.suggest_indexes()

        except Exception as e:
            logger.error(f"数据库优化失败: {e}")
            results['error'] = str(e)

        return results

    def get_optimization_report(self) -> Dict:
        """
        获取优化报告

        Returns:
            优化报告
        """
        report = {
            'database_type': self.engine.dialect.name,
            'table_analysis': self.analyze_table_size(),
            'index_analysis': self.analyze_indexes(),
            'index_suggestions': self.suggest_indexes(),
            'query_performance': self.analyze_query_performance(),
            'optimization_performed': self.optimize_database()
        }

        # 添加总体建议
        report['recommendations'] = self._generate_recommendations(report)

        return report

    def _generate_recommendations(self, report: Dict) -> List[str]:
        """
        生成优化建议

        Args:
            report: 优化报告

        Returns:
            建议列表
        """
        recommendations = []

        # 基于索引建议
        if report['index_suggestions']:
            recommendations.append(
                f"建议创建 {len(report['index_suggestions'])} 个索引以提升查询性能"
            )

        # 基于查询性能
        query_perf = report.get('query_performance', {})
        poor_queries = [
            name for name, perf in query_perf.items()
            if perf.get('performance') == 'poor'
        ]

        if poor_queries:
            recommendations.append(
                f"以下查询性能较差，建议优化: {', '.join(poor_queries)}"
            )

        # 基于表大小
        table_size = report.get('table_analysis', {})
        large_tables = [
            (name, info)
            for name, info in table_size.items()
            if info.get('estimated_size_mb', 0) > 100
        ]

        if large_tables:
            recommendations.append(
                f"以下表较大，考虑归档历史数据: {', '.join([name for name, _ in large_tables])}"
            )

        # 通用建议
        recommendations.extend([
            "定期执行 VACUUM 和 ANALYZE 保持数据库性能",
            "为频繁查询的列创建索引",
            "使用连接池管理数据库连接",
            "考虑使用缓存减少数据库压力"
        ])

        return recommendations


# 全局数据库优化器实例
db_optimizer = DatabaseOptimizer(engine)


def cache_query_result(ttl: int = 300):
    """
    缓存查询结果装饰器

    Args:
        ttl: 缓存时间（秒）
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            from app.cache import cache_manager, CacheKey

            # 生成缓存键
            cache_key = f"query:{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)

            if cached_result is not None:
                return cached_result

            # 执行查询
            result = func(*args, **kwargs)

            # 设置缓存
            await cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator
