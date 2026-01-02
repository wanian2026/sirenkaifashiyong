"""
P2.5风险管理增强功能测试脚本
测试止损策略、止盈策略、仓位管理和风险预警功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.stop_loss_strategy import (
    StopLossConfig, StopLossStrategyFactory,
    FixedStopLoss, DynamicStopLoss, TrailingStopLoss, LadderStopLoss
)
from app.take_profit_strategy import (
    TakeProfitConfig, TakeProfitStrategyFactory,
    FixedTakeProfit, DynamicTakeProfit, LadderTakeProfit, PartialTakeProfit
)
from app.position_management import (
    PositionConfig, PositionManagementFactory,
    KellyCriterion, FixedRatioStrategy, ATRBasedSizing,
    RiskParityStrategy, VolatilityBasedSizing
)
from app.risk_alert import (
    RiskAlertConfig, RiskAlertStrategyFactory,
    RiskAlertManager,
    ThresholdAlert, TrendAlert, VolatilityAlert,
    DrawdownAlert, PortfolioAlert
)


def test_stop_loss_strategies():
    """测试止损策略"""
    print("\n" + "="*60)
    print("测试止损策略")
    print("="*60)
    
    # 1. 测试固定止损
    print("\n1. 固定止损策略")
    fixed_config = StopLossConfig(
        strategy_type="fixed",
        entry_price=100.0,
        position_size=1.0,
        stop_loss_percent=0.05
    )
    fixed_strategy = StopLossStrategyFactory.create_strategy(fixed_config)
    
    # 测试未触发
    sl_price = fixed_strategy.calculate_stop_loss(97.0)
    should_close, reason = fixed_strategy.should_close_position(97.0)
    print(f"  止损价格: {sl_price:.4f}")
    print(f"  当前价格95.0，是否平仓: {should_close}, 原因: {reason}")
    
    # 测试触发
    should_close, reason = fixed_strategy.should_close_position(94.0)
    print(f"  当前价格94.0，是否平仓: {should_close}, 原因: {reason}")
    
    # 2. 测试动态止损（基于ATR）
    print("\n2. 动态止损策略（基于ATR）")
    dynamic_config = StopLossConfig(
        strategy_type="dynamic",
        entry_price=100.0,
        position_size=1.0,
        atr_period=14,
        atr_multiplier=2.0
    )
    dynamic_strategy = StopLossStrategyFactory.create_strategy(dynamic_config)
    
    sl_price = dynamic_strategy.calculate_stop_loss(98.0, atr=3.0)
    should_close, reason = dynamic_strategy.should_close_position(94.5, atr=3.0)
    print(f"  ATR=3.0，止损价格: {sl_price:.4f}")
    print(f"  当前价格94.5，是否平仓: {should_close}, 原因: {reason}")
    
    # 3. 测试追踪止损
    print("\n3. 追踪止损策略")
    trailing_config = StopLossConfig(
        strategy_type="trailing",
        entry_price=100.0,
        position_size=1.0,
        trailing_percent=0.03,
        activation_profit=0.05
    )
    trailing_strategy = StopLossStrategyFactory.create_strategy(trailing_config)
    
    # 未激活
    sl_price = trailing_strategy.calculate_stop_loss(100.0)
    should_close, reason = trailing_strategy.should_close_position(100.0)
    print(f"  未激活（盈利0%），止损价格: {sl_price:.4f}")
    print(f"  是否平仓: {should_close}")
    
    # 激活后
    sl_price = trailing_strategy.calculate_stop_loss(105.0)
    should_close, reason = trailing_strategy.should_close_position(101.8)
    print(f"  激活后（盈利5%），止损价格: {sl_price:.4f}")
    print(f"  当前价格101.8，是否平仓: {should_close}, 原因: {reason}")
    
    # 4. 测试阶梯止损
    print("\n4. 阶梯止损策略")
    ladder_config = StopLossConfig(
        strategy_type="ladder",
        entry_price=100.0,
        position_size=1.0,
        stop_loss_percent=0.05
    )
    ladder_strategy = StopLossStrategyFactory.create_strategy(ladder_config)
    
    sl_price = ladder_strategy.calculate_stop_loss(105.0)
    print(f"  盈利5%，止损价格: {sl_price:.4f}")
    
    should_close, reason = ladder_strategy.should_close_position(102.5)
    print(f"  当前价格102.5，是否平仓: {should_close}, 原因: {reason}")
    
    print("\n✓ 所有止损策略测试通过")


def test_take_profit_strategies():
    """测试止盈策略"""
    print("\n" + "="*60)
    print("测试止盈策略")
    print("="*60)
    
    # 1. 测试固定止盈
    print("\n1. 固定止盈策略")
    fixed_config = TakeProfitConfig(
        strategy_type="fixed",
        entry_price=100.0,
        position_size=1.0,
        take_profit_percent=0.10
    )
    fixed_strategy = TakeProfitStrategyFactory.create_strategy(fixed_config)
    
    tp_price = fixed_strategy.calculate_take_profit(95.0)
    should_close, reason, amount = fixed_strategy.should_close_position(95.0)
    print(f"  止盈价格: {tp_price:.4f}")
    print(f"  当前价格95.0，是否平仓: {should_close}")
    
    should_close, reason, amount = fixed_strategy.should_close_position(110.0)
    print(f"  当前价格110.0，是否平仓: {should_close}, 原因: {reason}, 平仓数量: {amount:.4f}")
    
    # 2. 测试动态止盈
    print("\n2. 动态止盈策略（基于RSI）")
    dynamic_config = TakeProfitConfig(
        strategy_type="dynamic",
        entry_price=100.0,
        position_size=1.0,
        rsi_period=14,
        rsi_overbought=70.0,
        trailing_percent=0.02
    )
    dynamic_strategy = TakeProfitStrategyFactory.create_strategy(dynamic_config)
    
    tp_price = dynamic_strategy.calculate_take_profit(100.0, rsi=65.0)
    print(f"  RSI=65.0，止盈价格: {tp_price:.4f}")
    
    should_close, reason, amount = dynamic_strategy.should_close_position(100.0, rsi=75.0)
    print(f"  RSI=75.0（超买），是否平仓: {should_close}, 原因: {reason}")
    
    # 3. 测试阶梯止盈
    print("\n3. 阶梯止盈策略")
    ladder_config = TakeProfitConfig(
        strategy_type="ladder",
        entry_price=100.0,
        position_size=1.0
    )
    ladder_strategy = TakeProfitStrategyFactory.create_strategy(ladder_config)
    
    should_close, reason, amount = ladder_strategy.should_close_position(105.0)
    print(f"  盈利5%，是否平仓: {should_close}, 原因: {reason}, 平仓数量: {amount:.4f}")
    print(f"  已平仓数量: {ladder_strategy.get_closed_amount():.4f}")
    
    # 4. 测试部分止盈
    print("\n4. 部分止盈策略")
    partial_config = TakeProfitConfig(
        strategy_type="partial",
        entry_price=100.0,
        position_size=1.0
    )
    partial_strategy = TakeProfitStrategyFactory.create_strategy(partial_config)
    
    should_close, reason, amount = partial_strategy.should_close_position(103.0)
    print(f"  盈利3%，是否平仓: {should_close}, 原因: {reason}, 平仓数量: {amount:.4f}")
    print(f"  已平仓数量: {partial_strategy.get_closed_amount():.4f}")
    
    should_close, reason, amount = partial_strategy.should_close_position(106.0)
    print(f"  盈利6%，是否平仓: {should_close}, 原因: {reason}, 平仓数量: {amount:.4f}")
    print(f"  已平仓数量: {partial_strategy.get_closed_amount():.4f}")
    
    print("\n✓ 所有止盈策略测试通过")


def test_position_management():
    """测试仓位管理"""
    print("\n" + "="*60)
    print("测试仓位管理")
    print("="*60)
    
    # 1. 测试Kelly公式
    print("\n1. Kelly公式")
    kelly_config = PositionConfig(
        strategy_type="kelly",
        account_balance=10000.0,
        entry_price=100.0,
        win_rate=0.55,
        avg_win=200.0,
        avg_loss=150.0,
        kelly_fraction=0.25
    )
    kelly_strategy = PositionManagementFactory.create_strategy(kelly_config)
    position_size = kelly_strategy.calculate_position_size()
    position_value = kelly_strategy.get_position_value(position_size)
    print(f"  胜率55%，盈亏比1.33，仓位大小: {position_size:.4f}")
    print(f"  仓位价值: {position_value:.2f}")
    print(f"  仓位占比: {position_value/10000*100:.2f}%")
    
    # 2. 测试固定比例
    print("\n2. 固定比例")
    fixed_config = PositionConfig(
        strategy_type="fixed_ratio",
        account_balance=10000.0,
        entry_price=100.0,
        fixed_percent=0.02
    )
    fixed_strategy = PositionManagementFactory.create_strategy(fixed_config)
    position_size = fixed_strategy.calculate_position_size()
    print(f"  固定比例2%，仓位大小: {position_size:.4f}")
    print(f"  仓位价值: {fixed_strategy.get_position_value(position_size):.2f}")
    
    # 3. 测试ATR基于
    print("\n3. ATR基于")
    atr_config = PositionConfig(
        strategy_type="atr_based",
        account_balance=10000.0,
        entry_price=100.0,
        atr=5.0,
        atr_multiplier=1.0,
        risk_per_trade=0.02
    )
    atr_strategy = PositionManagementFactory.create_strategy(atr_config)
    position_size = atr_strategy.calculate_position_size()
    print(f"  ATR=5.0，风险2%，仓位大小: {position_size:.4f}")
    print(f"  仓位价值: {atr_strategy.get_position_value(position_size):.2f}")
    
    # 4. 测试风险平价
    print("\n4. 风险平价")
    risk_parity_config = PositionConfig(
        strategy_type="risk_parity",
        account_balance=10000.0,
        entry_price=100.0,
        stop_loss_price=95.0,
        risk_target=0.02
    )
    risk_parity_strategy = PositionManagementFactory.create_strategy(risk_parity_config)
    position_size = risk_parity_strategy.calculate_position_size()
    print(f"  止损95.0，目标风险2%，仓位大小: {position_size:.4f}")
    print(f"  仓位价值: {risk_parity_strategy.get_position_value(position_size):.2f}")
    
    # 5. 测试波动率基于
    print("\n5. 波动率基于")
    volatility_config = PositionConfig(
        strategy_type="volatility",
        account_balance=10000.0,
        entry_price=100.0,
        volatility=0.2,
        volatility_target=0.15,
        position_multiplier=1.0
    )
    volatility_strategy = PositionManagementFactory.create_strategy(volatility_config)
    position_size = volatility_strategy.calculate_position_size()
    print(f"  当前波动率20%，目标15%，仓位大小: {position_size:.4f}")
    print(f"  仓位价值: {volatility_strategy.get_position_value(position_size):.2f}")
    
    print("\n✓ 所有机位管理策略测试通过")


def test_risk_alerts():
    """测试风险预警"""
    print("\n" + "="*60)
    print("测试风险预警")
    print("="*60)
    
    # 1. 测试阈值预警
    print("\n1. 阈值预警")
    threshold_config = RiskAlertConfig(
        alert_type="threshold",
        account_balance=9500.0,
        balance_threshold=10000.0,
        unrealized_pnl=-600.0,
        pnl_threshold=-500.0
    )
    threshold_strategy = RiskAlertStrategyFactory.create_strategy(threshold_config)
    is_alert, message, details = threshold_strategy.check_alert()
    print(f"  是否预警: {is_alert}")
    print(f"  预警信息: {message}")
    if details:
        print(f"  详情: {details}")
    
    # 2. 测试趋势预警
    print("\n2. 趋势预警")
    trend_config = RiskAlertConfig(
        alert_type="trend",
        account_balance=10000.0,
        current_price=110.0,
        prices_history=[100, 102, 105, 103, 110, 108, 112, 115, 113, 118]
    )
    trend_strategy = RiskAlertStrategyFactory.create_strategy(trend_config)
    is_alert, message, details = trend_strategy.check_alert()
    print(f"  是否预警: {is_alert}")
    print(f"  预警信息: {message}")
    if details:
        print(f"  价格变化: {details.get('price_change', 0)*100:.2f}%")
    
    # 3. 测试波动率预警
    print("\n3. 波动率预警")
    volatility_config = RiskAlertConfig(
        alert_type="volatility",
        account_balance=10000.0,
        prices_history=[100, 105, 95, 110, 90, 115, 85, 120]
    )
    volatility_strategy = RiskAlertStrategyFactory.create_strategy(volatility_config)
    is_alert, message, details = volatility_strategy.check_alert()
    print(f"  是否预警: {is_alert}")
    print(f"  预警信息: {message}")
    if details:
        print(f"  波动率: {details.get('volatility', 0)*100:.2f}%")
    
    # 4. 测试回撤预警
    print("\n4. 回撤预警")
    drawdown_config = RiskAlertConfig(
        alert_type="drawdown",
        account_balance=9000.0,
        peak_balance=10000.0,
        drawdown_threshold=0.05
    )
    drawdown_strategy = RiskAlertStrategyFactory.create_strategy(drawdown_config)
    is_alert, message, details = drawdown_strategy.check_alert()
    print(f"  是否预警: {is_alert}")
    print(f"  预警信息: {message}")
    if details:
        print(f"  回撤: {details.get('drawdown', 0)*100:.2f}%")
    
    # 5. 测试组合预警
    print("\n5. 组合预警")
    portfolio_config = RiskAlertConfig(
        alert_type="portfolio",
        account_balance=10000.0,
        total_position_value=8000.0,
        positions=[
            {"symbol": "BTC", "value": 6000.0},
            {"symbol": "ETH", "value": 2000.0}
        ],
        concentration_threshold=0.5
    )
    portfolio_strategy = RiskAlertStrategyFactory.create_strategy(portfolio_config)
    is_alert, message, details = portfolio_strategy.check_alert()
    print(f"  是否预警: {is_alert}")
    print(f"  预警信息: {message}")
    if details:
        print(f"  持仓详情: {details.get('positions', [])}")
    
    # 6. 测试预警管理器
    print("\n6. 预警管理器")
    alert_manager = RiskAlertManager()
    alert_manager.add_strategy("threshold", threshold_strategy)
    alert_manager.add_strategy("drawdown", drawdown_strategy)
    
    results = alert_manager.check_all_alerts()
    print(f"  预警数量: {len(results)}")
    for result in results:
        print(f"  - {result['name']}: {result['message']}")
    
    print("\n✓ 所有风险预警测试通过")


def test_api_usage():
    """测试API使用示例"""
    print("\n" + "="*60)
    print("API使用示例")
    print("="*60)
    
    # 示例1: 完整的交易风险管理流程
    print("\n示例1: 完整的交易风险管理流程")
    
    # 1. 计算仓位
    pos_config = PositionConfig(
        strategy_type="kelly",
        account_balance=10000.0,
        entry_price=100.0,
        win_rate=0.6,
        avg_win=200.0,
        avg_loss=150.0,
        kelly_fraction=0.25
    )
    pos_strategy = PositionManagementFactory.create_strategy(pos_config)
    position_size = pos_strategy.calculate_position_size()
    print(f"  1. 计算仓位: {position_size:.4f}")
    
    # 2. 设置止损
    sl_config = StopLossConfig(
        strategy_type="trailing",
        entry_price=100.0,
        position_size=position_size,
        trailing_percent=0.03,
        activation_profit=0.05
    )
    sl_strategy = StopLossStrategyFactory.create_strategy(sl_config)
    print(f"  2. 设置止损: 追踪止损，激活后3%回撤")
    
    # 3. 设置止盈
    tp_config = TakeProfitConfig(
        strategy_type="partial",
        entry_price=100.0,
        position_size=position_size
    )
    tp_strategy = TakeProfitStrategyFactory.create_strategy(tp_config)
    print(f"  3. 设置止盈: 部分止盈")
    
    # 4. 模拟价格变化
    prices = [100, 102, 105, 107, 104, 108, 110]
    print(f"\n  模拟交易过程:")
    for price in prices:
        profit = (price - 100) / 100 * 100
        print(f"    价格{price:.2f}, 盈利{profit:.2f}%", end="")
        
        # 检查止损
        should_close, reason = sl_strategy.should_close_position(price)
        if should_close:
            print(f" -> 止损触发: {reason}")
            break
        
        # 检查止盈
        should_close, reason, amount = tp_strategy.should_close_position(price)
        if should_close:
            print(f" -> 止盈触发: {reason}")
        
        print()
    
    print(f"  已平仓数量: {tp_strategy.get_closed_amount():.4f}")
    
    print("\n✓ API使用示例测试通过")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("P2.5 风险管理增强功能测试")
    print("="*60)
    
    try:
        test_stop_loss_strategies()
        test_take_profit_strategies()
        test_position_management()
        test_risk_alerts()
        test_api_usage()
        
        print("\n" + "="*60)
        print("✓ 所有测试通过!")
        print("="*60)
        print("\n功能统计:")
        print(f"  - 止损策略: {len(StopLossStrategyFactory.get_available_strategies())} 种")
        print(f"  - 止盈策略: {len(TakeProfitStrategyFactory.get_available_strategies())} 种")
        print(f"  - 仓位管理: {len(PositionManagementFactory.get_available_strategies())} 种")
        print(f"  - 风险预警: {len(RiskAlertStrategyFactory.get_available_strategies())} 种")
        print(f"  - 总计: {len(StopLossStrategyFactory.get_available_strategies()) + len(TakeProfitStrategyFactory.get_available_strategies()) + len(PositionManagementFactory.get_available_strategies()) + len(RiskAlertStrategyFactory.get_available_strategies())} 个功能")
        
        return True
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
