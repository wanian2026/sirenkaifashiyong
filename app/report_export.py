"""
报表导出模块
支持CSV和Excel格式导出交易记录、分析报表等
"""

from typing import Dict, List, Optional
from datetime import datetime
import csv
import logging
from fastapi import HTTPException, status
import pandas as pd

logger = logging.getLogger(__name__)


class ReportExporter:
    """报表导出器"""

    def __init__(self):
        self.export_formats = ['csv', 'excel']

    def export_trades_to_csv(
        self,
        trades_data: List[Dict],
        output_file: str = None
    ) -> str:
        """
        导出交易记录到CSV

        Args:
            trades_data: 交易数据列表
            output_file: 输出文件路径（可选）

        Returns:
            文件路径
        """
        try:
            if not trades_data:
                raise ValueError("交易数据为空")

            # 如果没有指定输出文件，生成默认文件名
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"trades_export_{timestamp}.csv"

            # 定义CSV列
            fieldnames = [
                'id', 'bot_id', 'trading_pair', 'side', 'price', 'amount',
                'fee', 'profit', 'created_at'
            ]

            # 写入CSV文件
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for trade in trades_data:
                    # 只写入需要的字段
                    row = {k: trade.get(k, '') for k in fieldnames}
                    writer.writerow(row)

            logger.info(f"交易记录已导出到CSV: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"导出CSV失败: {str(e)}"
            )

    def export_trades_to_excel(
        self,
        trades_data: List[Dict],
        output_file: str = None
    ) -> str:
        """
        导出交易记录到Excel

        Args:
            trades_data: 交易数据列表
            output_file: 输出文件路径（可选）

        Returns:
            文件路径
        """
        try:
            if not trades_data:
                raise ValueError("交易数据为空")

            # 如果没有指定输出文件，生成默认文件名
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"trades_export_{timestamp}.xlsx"

            # 转换为DataFrame
            df = pd.DataFrame(trades_data)

            # 选择需要的列
            columns = [
                'id', 'bot_id', 'trading_pair', 'side', 'price', 'amount',
                'fee', 'profit', 'created_at'
            ]
            df = df[columns]

            # 写入Excel文件
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='交易记录', index=False)

                # 获取工作表并设置列宽
                worksheet = writer.sheets['交易记录']
                for idx, col in enumerate(df.columns, 1):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(col)
                    )
                    worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)

            logger.info(f"交易记录已导出到Excel: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"导出Excel失败: {str(e)}"
            )

    def export_analytics_to_excel(
        self,
        analytics_data: Dict,
        output_file: str = None
    ) -> str:
        """
        导出分析报表到Excel（多Sheet）

        Args:
            analytics_data: 分析数据字典
            output_file: 输出文件路径（可选）

        Returns:
            文件路径
        """
        try:
            # 如果没有指定输出文件，生成默认文件名
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"analytics_report_{timestamp}.xlsx"

            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 导出仪表盘概览
                if 'dashboard' in analytics_data:
                    dashboard = analytics_data['dashboard']

                    # 转换嵌套数据为表格
                    summary_data = []

                    # 机器人统计
                    if 'bots' in dashboard:
                        summary_data.append(['机器人总数', dashboard['bots'].get('total', 0)])
                        summary_data.append(['运行中', dashboard['bots'].get('running', 0)])
                        summary_data.append(['已停止', dashboard['bots'].get('stopped', 0)])

                    # 交易统计
                    if 'trades' in dashboard:
                        summary_data.append([])
                        summary_data.append(['交易总数', dashboard['trades'].get('total', 0)])
                        summary_data.append(['盈利交易', dashboard['trades'].get('winning_trades', 0)])
                        summary_data.append(['亏损交易', dashboard['trades'].get('losing_trades', 0)])

                    # 盈亏统计
                    if 'pnl' in dashboard:
                        summary_data.append([])
                        summary_data.append(['总盈亏', dashboard['pnl'].get('total', 0)])
                        summary_data.append(['今日盈亏', dashboard['pnl'].get('today', 0)])
                        summary_data.append(['平均盈亏', dashboard['pnl'].get('average', 0)])
                        summary_data.append(['最大盈利', dashboard['pnl'].get('max_profit', 0)])
                        summary_data.append(['最大亏损', dashboard['pnl'].get('max_loss', 0)])

                    # 性能指标
                    if 'performance' in dashboard:
                        summary_data.append([])
                        summary_data.append(['胜率 (%)', dashboard['performance'].get('win_rate', 0)])
                        summary_data.append(['总投资金额', dashboard['performance'].get('total_investment', 0)])
                        summary_data.append(['投资回报率 (%)', dashboard['performance'].get('roi', 0)])

                    summary_df = pd.DataFrame(summary_data, columns=['指标', '值'])
                    summary_df.to_excel(writer, sheet_name='仪表盘概览', index=False)

                # 导出交易记录
                if 'recent_trades' in analytics_data and analytics_data['recent_trades']:
                    trades_df = pd.DataFrame(analytics_data['recent_trades'])
                    trades_df.to_excel(writer, sheet_name='最近交易', index=False)

                # 导出收益曲线
                if 'profit_curve' in analytics_data:
                    profit_curve = analytics_data['profit_curve']
                    curve_data = {
                        '日期': profit_curve.get('dates', []),
                        '累计收益': profit_curve.get('profit_curve', []),
                        '每日盈亏': profit_curve.get('daily_pnls', [])
                    }
                    curve_df = pd.DataFrame(curve_data)
                    curve_df.to_excel(writer, sheet_name='收益曲线', index=False)

            logger.info(f"分析报表已导出到Excel: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"导出分析报表失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"导出分析报表失败: {str(e)}"
            )

    def export_time_analysis_to_excel(
        self,
        analysis_data: Dict,
        output_file: str = None
    ) -> str:
        """
        导出时间分析到Excel

        Args:
            analysis_data: 时间分析数据
            output_file: 输出文件路径（可选）

        Returns:
            文件路径
        """
        try:
            # 如果没有指定输出文件，生成默认文件名
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                analysis_type = analysis_data.get('analysis_type', 'unknown')
                output_file = f"time_analysis_{analysis_type}_{timestamp}.xlsx"

            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 导出汇总信息
                if 'summary' in analysis_data:
                    summary = analysis_data['summary']
                    summary_data = []

                    for key, value in summary.items():
                        if isinstance(value, (dict, list)):
                            continue
                        summary_data.append([key, value])

                    summary_df = pd.DataFrame(summary_data, columns=['指标', '值'])
                    summary_df.to_excel(writer, sheet_name='汇总', index=False)

                # 导出统计数据
                stats_key = None
                if 'daily_stats' in analysis_data:
                    stats_key = 'daily_stats'
                elif 'weekly_stats' in analysis_data:
                    stats_key = 'weekly_stats'
                elif 'monthly_stats' in analysis_data:
                    stats_key = 'monthly_stats'

                if stats_key and analysis_data[stats_key]:
                    stats_df = pd.DataFrame(analysis_data[stats_key])
                    stats_df.to_excel(writer, sheet_name='统计数据', index=False)

            logger.info(f"时间分析已导出到Excel: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"导出时间分析失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"导出时间分析失败: {str(e)}"
            )

    def export_pair_analysis_to_excel(
        self,
        analysis_data: Dict,
        output_file: str = None
    ) -> str:
        """
        导出交易对分析到Excel

        Args:
            analysis_data: 交易对分析数据
            output_file: 输出文件路径（可选）

        Returns:
            文件路径
        """
        try:
            # 如果没有指定输出文件，生成默认文件名
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"pair_analysis_{timestamp}.xlsx"

            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 导出汇总信息
                if 'summary' in analysis_data:
                    summary = analysis_data['summary']
                    summary_data = []

                    for key, value in summary.items():
                        if isinstance(value, dict):
                            continue
                        summary_data.append([key, value])

                    summary_df = pd.DataFrame(summary_data, columns=['指标', '值'])
                    summary_df.to_excel(writer, sheet_name='汇总', index=False)

                # 导出交易对统计
                if 'pair_stats' in analysis_data and analysis_data['pair_stats']:
                    pair_stats_df = pd.DataFrame(analysis_data['pair_stats'])
                    pair_stats_df.to_excel(writer, sheet_name='交易对统计', index=False)

            logger.info(f"交易对分析已导出到Excel: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"导出交易对分析失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"导出交易对分析失败: {str(e)}"
            )
