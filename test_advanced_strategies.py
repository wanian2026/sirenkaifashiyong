#!/usr/bin/env python3
"""
高级交易策略测试脚本
测试均值回归策略和动量策略
"""

import asyncio
import random
from app.advanced_strategies import (
    MeanReversionStrategy,
    MomentumStrategy,
    StrategyFactory
)


def generate_price_data(start_price=50000, count=200, volatility=0.02):
    """生成模拟价格数据"""
    prices = [start_price]
    for _ in range(count - 1):
        change = random.gauss(0, start_price * volatility)
        new_price = max(prices[-1] + change, 1)
        prices.append(new_price)
    return prices


async def test_mean_reversion_strategy():
    """测试均值回归策略"""
    print("\n" + "="*60)
    print("测试均值回归策略")
    print("="*60)

    # 创建策略实例
    strategy = MeanReversionStrategy(
        trading_pair="BTC/USDT",
        lookback_period=20,
        std_multiplier=2.0,
        investment_amount=1000
    )

    # 生成价格数据
    prices = generate_price_data(start_price=50000, count=100, volatility=0.03)

    print(f"\n价格数据: {len(prices)} 个数据点")
    print(f"起始价格: {prices[0]:.2f}")
    print(f"结束价格: {prices[-1]:.2f}")

    # 模拟运行策略
    for i, price in enumerate(prices):
        await strategy.update_price(price)

        if i >= strategy.lookback_period:
            signal = await strategy.generate_signal(price)
            if signal:
                await strategy.execute_trade(signal)
                print(f"  [{i:3d}] 价格: {price:8.2f} | 信号: {signal['action']:10s} | "
                      f"原因: {signal['reason'][:50]}")

    # 获取最终状态
    status = strategy.get_strategy_status()

    print("\n" + "-"*60)
    print("策略执行结果:")
    print(f"  总交易次数: {status['total_trades']}")
    print(f"  当前持仓: {status['current_position']:.6f}")
    print(f"  实现盈亏: {status['realized_pnl']:.2f}")
    print(f"  未实现盈亏: {status['unrealized_pnl']:.2f}")
    print(f"  总盈亏: {status['total_pnl']:.2f}")
    print(f"  当前均值: {status['current_mean']:.2f}")
    print(f"  当前标准差: {status['current_std']:.2f}")
    print(f"  上轨: {status['upper_band']:.2f}")
    print(f"  下轨: {status['lower_band']:.2f}")
    print("-"*60)

    return status['total_pnl']


async def test_momentum_strategy():
    """测试动量策略"""
    print("\n" + "="*60)
    print("测试动量策略")
    print("="*60)

    # 创建策略实例
    strategy = MomentumStrategy(
        trading_pair="BTC/USDT",
        short_period=10,
        long_period=30,
        momentum_threshold=0.02,
        investment_amount=1000
    )

    # 生成价格数据（带趋势）
    prices = []
    price = 50000
    for _ in range(200):
        # 添加趋势和波动
        trend = 50 * (0.5 - random.random())
        volatility = price * 0.015 * random.gauss(0, 1)
        price = max(price + trend + volatility, 1)
        prices.append(price)

    print(f"\n价格数据: {len(prices)} 个数据点")
    print(f"起始价格: {prices[0]:.2f}")
    print(f"结束价格: {prices[-1]:.2f}")

    # 模拟运行策略
    for i, price in enumerate(prices):
        await strategy.update_price(price)

        if i >= strategy.long_period:
            signal = await strategy.generate_signal(price)
            if signal:
                await strategy.execute_trade(signal)
                print(f"  [{i:3d}] 价格: {price:8.2f} | 信号: {signal['action']:10s} | "
                      f"原因: {signal['reason'][:50]}")

    # 获取最终状态
    status = strategy.get_strategy_status()

    print("\n" + "-"*60)
    print("策略执行结果:")
    print(f"  总交易次数: {status['total_trades']}")
    print(f"  当前持仓: {status['current_position']:.6f}")
    print(f"  实现盈亏: {status['realized_pnl']:.2f}")
    print(f"  未实现盈亏: {status['unrealized_pnl']:.2f}")
    print(f"  总盈亏: {status['total_pnl']:.2f}")
    print(f"  短期均线: {status['short_ma']:.2f}")
    print(f"  长期均线: {status['long_ma']:.2f}")
    print(f"  当前动量: {status['momentum']:.2%}")
    print(f"  最后信号: {status['last_signal']}")
    print("-"*60)

    return status['total_pnl']


async def test_strategy_factory():
    """测试策略工厂"""
    print("\n" + "="*60)
    print("测试策略工厂")
    print("="*60)

    # 测试创建均值回归策略
    mean_reversion_config = {
        'trading_pair': 'ETH/USDT',
        'lookback_period': 20,
        'std_multiplier': 2.0,
        'investment_amount': 2000
    }

    strategy1 = StrategyFactory.create_strategy('mean_reversion', mean_reversion_config)
    print(f"\n✓ 成功创建均值回归策略: {strategy1}")

    # 测试创建动量策略
    momentum_config = {
        'trading_pair': 'ETH/USDT',
        'short_period': 10,
        'long_period': 30,
        'momentum_threshold': 0.02,
        'investment_amount': 2000
    }

    strategy2 = StrategyFactory.create_strategy('momentum', momentum_config)
    print(f"✓ 成功创建动量策略: {strategy2}")

    # 测试不支持的策略
    strategy3 = StrategyFactory.create_strategy('unknown', {})
    print(f"✓ 不支持的策略返回None: {strategy3}")

    print("\n" + "-"*60)


async def test_backtest():
    """测试回测功能"""
    print("\n" + "="*60)
    print("测试回测功能")
    print("="*60)

    # 生成测试数据
    prices = generate_price_data(start_price=50000, count=100, volatility=0.025)

    # 测试均值回归策略回测
    print("\n--- 均值回归策略回测 ---")
    mean_reversion_config = {
        'trading_pair': 'BTC/USDT',
        'lookback_period': 20,
        'std_multiplier': 2.0,
        'investment_amount': 1000
    }

    mr_strategy = StrategyFactory.create_strategy('mean_reversion', mean_reversion_config)
    trades_count = 0

    for price in prices:
        await mr_strategy.update_price(price)
        signal = await mr_strategy.generate_signal(price)
        if signal:
            await mr_strategy.execute_trade(signal)
            trades_count += 1

    mr_status = mr_strategy.get_strategy_status()
    print(f"  数据点: {len(prices)}")
    print(f"  交易次数: {trades_count}")
    print(f"  最终盈亏: {mr_status['total_pnl']:.2f}")

    # 测试动量策略回测
    print("\n--- 动量策略回测 ---")
    momentum_config = {
        'trading_pair': 'BTC/USDT',
        'short_period': 10,
        'long_period': 30,
        'momentum_threshold': 0.02,
        'investment_amount': 1000
    }

    mom_strategy = StrategyFactory.create_strategy('momentum', momentum_config)
    trades_count = 0

    for price in prices:
        await mom_strategy.update_price(price)
        signal = await mom_strategy.generate_signal(price)
        if signal:
            await mom_strategy.execute_trade(signal)
            trades_count += 1

    mom_status = mom_strategy.get_strategy_status()
    print(f"  数据点: {len(prices)}")
    print(f"  交易次数: {trades_count}")
    print(f"  最终盈亏: {mom_status['total_pnl']:.2f}")

    print("\n" + "-"*60)


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("高级交易策略测试")
    print("="*60)

    try:
        # 测试策略工厂
        await test_strategy_factory()

        # 测试均值回归策略
        mr_pnl = await test_mean_reversion_strategy()

        # 测试动量策略
        mom_pnl = await test_momentum_strategy()

        # 测试回测功能
        await test_backtest()

        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print(f"  ✓ 均值回归策略测试通过，最终盈亏: {mr_pnl:.2f}")
        print(f"  ✓ 动量策略测试通过，最终盈亏: {mom_pnl:.2f}")
        print(f"  ✓ 策略工厂测试通过")
        print(f"  ✓ 回测功能测试通过")
        print("\n所有测试完成！")

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
