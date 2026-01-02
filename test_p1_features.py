"""
P1优先级功能测试脚本
测试风险管理增强和数据分析增强功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from app.risk_management import RiskManager, PositionRiskManager, calculate_position_size, calculate_risk_reward_ratio
from app.analytics import AnalyticsEngine
from app.database import SessionLocal, engine
from app.models import TradingBot, Trade, User
from sqlalchemy import func
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_risk_management_enhancements():
    """测试风险管理增强功能"""
    logger.info("=" * 60)
    logger.info("测试风险管理增强功能")
    logger.info("=" * 60)

    try:
        # 创建风险管理器（启用所有新功能）
        risk_manager = RiskManager(
            max_position=10000,
            max_daily_loss=1000,
            max_total_loss=5000,
            max_orders=50,
            max_single_order=1000,
            stop_loss_threshold=0.05,
            take_profit_threshold=0.10,
            enable_auto_stop=True,
            max_consecutive_losses=3,  # 连续亏损3次停止
            volatility_threshold=0.05,  # 波动率5%阈值
            enable_volatility_protection=True,
            enable_emergency_stop=True
        )

        # 测试1: 连续亏损跟踪
        logger.info("\n测试1: 连续亏损跟踪")
        risk_manager.update_pnl(-100)
        logger.info(f"连续亏损次数: {risk_manager.consecutive_losses}")
        assert risk_manager.consecutive_losses == 1

        risk_manager.update_pnl(-50)
        logger.info(f"连续亏损次数: {risk_manager.consecutive_losses}")
        assert risk_manager.consecutive_losses == 2

        risk_manager.update_pnl(-30)
        logger.info(f"连续亏损次数: {risk_manager.consecutive_losses}")
        assert risk_manager.consecutive_losses == 3

        # 检查连续亏损限制
        passed, msg = risk_manager.check_consecutive_losses()
        logger.info(f"连续亏损检查: {passed}, {msg}")
        assert not passed  # 应该失败

        # 盈利后重置连续亏损
        risk_manager.update_pnl(50)
        logger.info(f"盈利后连续亏损次数: {risk_manager.consecutive_losses}")
        assert risk_manager.consecutive_losses == 0
        logger.info("✓ 测试1通过")

        # 测试2: 波动率计算
        logger.info("\n测试2: 波动率计算")
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109] * 2
        for price in prices:
            risk_manager.update_price_history("BTC/USDT", price)

        passed, msg, volatility = risk_manager.check_volatility("BTC/USDT")
        logger.info(f"波动率检查: {passed}, {msg}, 波动率: {volatility*100:.2f}%")
        assert passed  # 正常波动应该通过
        logger.info("✓ 测试2通过")

        # 测试3: 高波动率检测
        logger.info("\n测试3: 高波动率检测")
        # 添加高波动数据
        high_vol_prices = [200, 190, 210, 180, 220]  # 波动较大
        for price in high_vol_prices:
            risk_manager.update_price_history("BTC/USDT", price)

        passed, msg, volatility = risk_manager.check_volatility("BTC/USDT")
        logger.info(f"高波动率检查: {passed}, {msg}, 波动率: {volatility*100:.2f}%")
        logger.info("✓ 测试3通过")

        # 测试4: 异常行情检测
        logger.info("\n测试4: 异常行情检测")
        # 重置last_price，避免受之前测试的影响
        risk_manager.last_price = None

        result = risk_manager.detect_abnormal_market("BTC/USDT", 100)
        logger.info(f"初始价格检测: {result}")
        assert not result['is_abnormal']  # 初始价格不应该异常

        # 模拟小幅波动（10%以内）
        result = risk_manager.detect_abnormal_market("BTC/USDT", 95)  # 跌幅5%
        logger.info(f"小幅波动检测: {result}")
        assert not result['is_abnormal']  # 10%以内不应该异常

        # 模拟暴跌（超过15%）
        result = risk_manager.detect_abnormal_market("BTC/USDT", 80)  # 跌幅约15.8%
        logger.info(f"暴跌检测: {result}")
        assert result['is_abnormal']  # 应该检测到异常
        logger.info("✓ 测试4通过")

        # 测试5: 紧急停止机制
        logger.info("\n测试5: 紧急停止机制")
        risk_manager.trigger_emergency_stop("市场异常波动")
        logger.info(f"紧急停止状态: {risk_manager.emergency_stop_triggered}")
        assert risk_manager.emergency_stop_triggered

        passed, msg = risk_manager.check_emergency_stop()
        logger.info(f"紧急停止检查: {passed}, {msg}")
        assert not passed  # 应该禁止交易

        # 重置紧急停止
        risk_manager.reset_emergency_stop()
        logger.info(f"重置后紧急停止状态: {risk_manager.emergency_stop_triggered}")
        assert not risk_manager.emergency_stop_triggered
        logger.info("✓ 测试5通过")

        # 测试6: 风险报告
        logger.info("\n测试6: 风险报告")
        report = risk_manager.get_risk_report()
        logger.info(f"风险报告连续亏损: {report.get('consecutive_losses')}")
        logger.info(f"风险报告波动率阈值: {report.get('volatility_threshold')}")
        logger.info(f"风险报告紧急停止: {report.get('emergency_stop_triggered')}")
        assert 'consecutive_losses' in report
        assert 'volatility_threshold' in report
        assert 'emergency_stop_triggered' in report
        logger.info("✓ 测试6通过")

        logger.info("\n✅ 风险管理增强功能测试全部通过！")
        return True

    except Exception as e:
        logger.error(f"❌ 风险管理增强功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analytics_enhancements():
    """测试数据分析增强功能"""
    logger.info("\n" + "=" * 60)
    logger.info("测试数据分析增强功能")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        # 创建测试用户和机器人
        user = db.query(User).filter(User.username == "testuser").first()
        if not user:
            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password="hashed_password",
                role="admin"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 创建测试机器人
        bot = db.query(TradingBot).filter(TradingBot.name == "Test Bot P1").first()
        if not bot:
            bot = TradingBot(
                name="Test Bot P1",
                exchange="binance",
                trading_pair="BTC/USDT",
                strategy="grid",
                status="stopped",
                user_id=user.id,
                config='{"investment_amount": 10000, "grid_levels": 10}'
            )
            db.add(bot)
            db.commit()
            db.refresh(bot)

        # 添加测试交易记录（模拟30天的数据）
        logger.info("\n添加测试交易记录...")
        test_trades = []
        for i in range(30):
            trade_date = datetime.now() - timedelta(days=i)

            # 每天添加1-3笔交易
            for j in range(3):
                profit = (50 if j % 2 == 0 else -30) * (i % 3 + 1)  # 随机盈亏
                trade = Trade(
                    bot_id=bot.id,
                    order_id=f"order_{i}_{j}",
                    trading_pair=["BTC/USDT", "ETH/USDT", "BNB/USDT"][i % 3],
                    side="buy" if j % 2 == 0 else "sell",
                    price=50000 + i * 100,
                    amount=0.1,
                    fee=5,
                    profit=profit,
                    created_at=trade_date
                )
                test_trades.append(trade)

        db.add_all(test_trades)
        db.commit()
        logger.info(f"✓ 添加了{len(test_trades)}条测试交易记录")

        # 测试1: 每日分析
        logger.info("\n测试1: 每日分析")
        analytics = AnalyticsEngine(db)
        daily_analysis = analytics.get_time_based_analysis(
            user_id=user.id,
            bot_id=bot.id,
            analysis_type="daily"
        )
        logger.info(f"每日统计天数: {len(daily_analysis.get('daily_stats', []))}")
        logger.info(f"汇总 - 总盈亏: {daily_analysis.get('summary', {}).get('total_pnl', 0)}")
        logger.info(f"汇总 - 盈利天数: {daily_analysis.get('summary', {}).get('winning_days', 0)}")
        logger.info(f"汇总 - 亏损天数: {daily_analysis.get('summary', {}).get('losing_days', 0)}")
        assert len(daily_analysis.get('daily_stats', [])) > 0
        logger.info("✓ 测试1通过")

        # 测试2: 每周分析
        logger.info("\n测试2: 每周分析")
        weekly_analysis = analytics.get_time_based_analysis(
            user_id=user.id,
            bot_id=bot.id,
            analysis_type="weekly"
        )
        logger.info(f"每周统计周数: {len(weekly_analysis.get('weekly_stats', []))}")
        logger.info(f"汇总 - 总盈亏: {weekly_analysis.get('summary', {}).get('total_pnl', 0)}")
        logger.info(f"汇总 - 盈利周数: {weekly_analysis.get('summary', {}).get('winning_weeks', 0)}")
        assert len(weekly_analysis.get('weekly_stats', [])) > 0
        logger.info("✓ 测试2通过")

        # 测试3: 每月分析
        logger.info("\n测试3: 每月分析")
        monthly_analysis = analytics.get_time_based_analysis(
            user_id=user.id,
            bot_id=bot.id,
            analysis_type="monthly"
        )
        logger.info(f"每月统计月数: {len(monthly_analysis.get('monthly_stats', []))}")
        logger.info(f"汇总 - 总盈亏: {monthly_analysis.get('summary', {}).get('total_pnl', 0)}")
        logger.info(f"汇总 - 盈利月数: {monthly_analysis.get('summary', {}).get('winning_months', 0)}")
        assert len(monthly_analysis.get('monthly_stats', [])) > 0
        logger.info("✓ 测试3通过")

        # 测试4: 交易对分析
        logger.info("\n测试4: 交易对分析")
        pair_analysis = analytics.get_pair_analysis(
            user_id=user.id,
            bot_id=bot.id
        )
        logger.info(f"交易对数量: {pair_analysis.get('summary', {}).get('total_pairs', 0)}")
        logger.info(f"最佳交易对: {pair_analysis.get('summary', {}).get('best_pair', {}).get('trading_pair')}")
        logger.info(f"最差交易对: {pair_analysis.get('summary', {}).get('worst_pair', {}).get('trading_pair')}")
        logger.info(f"最多交易对: {pair_analysis.get('summary', {}).get('most_traded_pair', {}).get('trading_pair')}")
        assert pair_analysis.get('summary', {}).get('total_pairs', 0) > 0
        logger.info("✓ 测试4通过")

        # 测试5: 交易对详细信息
        logger.info("\n测试5: 交易对详细信息")
        pair_stats = pair_analysis.get('pair_stats', [])
        if pair_stats:
            for stat in pair_stats:
                logger.info(f"交易对: {stat.get('trading_pair')}, "
                          f"交易次数: {stat.get('trade_count')}, "
                          f"胜率: {stat.get('win_rate', 0):.2f}%, "
                          f"总盈利: {stat.get('total_profit', 0):.2f}")
        logger.info("✓ 测试5通过")

        logger.info("\n✅ 数据分析增强功能测试全部通过！")
        return True

    except Exception as e:
        logger.error(f"❌ 数据分析增强功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_report_export():
    """测试报表导出功能"""
    logger.info("\n" + "=" * 60)
    logger.info("测试报表导出功能")
    logger.info("=" * 60)

    try:
        from app.report_export import ReportExporter

        exporter = ReportExporter()

        # 测试数据
        test_trades_data = [
            {
                'id': 1,
                'bot_id': 1,
                'trading_pair': 'BTC/USDT',
                'side': 'buy',
                'price': 50000,
                'amount': 0.1,
                'fee': 5,
                'profit': 100,
                'created_at': '2025-01-01 10:00:00'
            },
            {
                'id': 2,
                'bot_id': 1,
                'trading_pair': 'ETH/USDT',
                'side': 'sell',
                'price': 3000,
                'amount': 1.0,
                'fee': 3,
                'profit': -50,
                'created_at': '2025-01-01 11:00:00'
            }
        ]

        # 测试1: 导出CSV
        logger.info("\n测试1: 导出交易记录到CSV")
        csv_file = exporter.export_trades_to_csv(test_trades_data)
        logger.info(f"CSV文件已导出: {csv_file}")
        assert os.path.exists(csv_file)
        logger.info("✓ 测试1通过")

        # 测试2: 导出Excel
        logger.info("\n测试2: 导出交易记录到Excel")
        excel_file = exporter.export_trades_to_excel(test_trades_data)
        logger.info(f"Excel文件已导出: {excel_file}")
        assert os.path.exists(excel_file)
        logger.info("✓ 测试2通过")

        # 测试3: 导出时间分析
        logger.info("\n测试3: 导出时间分析到Excel")
        time_analysis_data = {
            'analysis_type': 'daily',
            'period': '30d',
            'daily_stats': [
                {'date': '2025-01-01', 'trade_count': 5, 'profit': 100},
                {'date': '2025-01-02', 'trade_count': 3, 'profit': -50}
            ],
            'summary': {
                'total_days': 2,
                'winning_days': 1,
                'losing_days': 1,
                'total_pnl': 50
            }
        }
        time_excel_file = exporter.export_time_analysis_to_excel(time_analysis_data)
        logger.info(f"时间分析Excel文件已导出: {time_excel_file}")
        assert os.path.exists(time_excel_file)
        logger.info("✓ 测试3通过")

        # 测试4: 导出交易对分析
        logger.info("\n测试4: 导出交易对分析到Excel")
        pair_analysis_data = {
            'analysis_type': 'trading_pair',
            'pair_stats': [
                {
                    'trading_pair': 'BTC/USDT',
                    'trade_count': 10,
                    'winning_trades': 6,
                    'losing_trades': 4,
                    'total_profit': 500,
                    'win_rate': 60.0
                }
            ],
            'summary': {
                'total_pairs': 1,
                'total_pnl': 500
            }
        }
        pair_excel_file = exporter.export_pair_analysis_to_excel(pair_analysis_data)
        logger.info(f"交易对分析Excel文件已导出: {pair_excel_file}")
        assert os.path.exists(pair_excel_file)
        logger.info("✓ 测试4通过")

        # 清理测试文件
        for f in [csv_file, excel_file, time_excel_file, pair_excel_file]:
            if os.path.exists(f):
                os.remove(f)
                logger.info(f"已清理测试文件: {f}")

        logger.info("\n✅ 报表导出功能测试全部通过！")
        return True

    except Exception as e:
        logger.error(f"❌ 报表导出功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    logger.info("开始P1优先级功能测试...\n")

    all_passed = True

    # 测试风险管理增强功能
    if not test_risk_management_enhancements():
        all_passed = False

    # 测试数据分析增强功能
    if not test_analytics_enhancements():
        all_passed = False

    # 测试报表导出功能
    if not test_report_export():
        all_passed = False

    # 输出总结
    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("✅ 所有P1优先级功能测试通过！")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("❌ 部分测试失败！")
        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    exit(main())
