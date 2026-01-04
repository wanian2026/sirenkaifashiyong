"""
最简单的策略测试脚本

使用方法：
    python test_strategy_simple.py

功能：
    1. 测试代号A策略的有效性
    2. 使用模拟数据进行回测
    3. 输出详细的性能指标
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal

# 导入策略和回测模块
from app.code_a_strategy import CodeAStrategy
from app.backtest import BacktestEngine, BacktestConfig


def generate_sample_data(
    start_date: datetime,
    end_date: datetime,
    initial_price: float = 50000,
    volatility: float = 0.02,
    trend: float = 0.0001  # 每日趋势
) -> pd.DataFrame:
    """
    生成模拟价格数据

    Args:
        start_date: 开始日期
        end_date: 结束日期
        initial_price: 初始价格
        volatility: 波动率
        trend: 趋势（正数为上涨趋势，负数为下跌趋势）

    Returns:
        DataFrame包含 ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='H')  # 每小时数据

    data = []
    price = initial_price

    for i, date in enumerate(dates):
        # 随机游走
        daily_return = np.random.normal(trend, volatility / np.sqrt(24))
        price = price * (1 + daily_return)

        # 生成OHLCV数据
        high = price * (1 + abs(np.random.normal(0, 0.005)))
        low = price * (1 - abs(np.random.normal(0, 0.005)))
        open_price = low + (high - low) * np.random.random()
        close_price = low + (high - low) * np.random.random()

        volume = np.random.lognormal(10, 1)

        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })

    return pd.DataFrame(data)


class SimpleCodeABacktest:
    """简化版代号A策略回测"""

    def __init__(
        self,
        investment_amount: float = 1000,
        up_threshold: float = 0.02,
        down_threshold: float = 0.02,
        stop_loss: float = 0.10
    ):
        self.investment_amount = investment_amount
        self.up_threshold = up_threshold
        self.down_threshold = down_threshold
        self.stop_loss = stop_loss

        self.trades = []
        self.long_positions = []
        self.short_positions = []

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """执行回测"""
        # 初始化：同时开多空两单
        initial_price = data.iloc[0]['close']
        amount = self.investment_amount / initial_price

        self.long_positions.append({
            'entry_price': initial_price,
            'amount': amount,
            'entry_time': data.iloc[0]['timestamp']
        })

        self.short_positions.append({
            'entry_price': initial_price,
            'amount': amount,
            'entry_time': data.iloc[0]['timestamp']
        })

        balance = self.investment_amount * 2  # 多空各投资
        capital_used = balance

        # 逐K线处理
        for idx, row in data.iterrows():
            current_price = row['close']

            # 处理多单
            for pos in self.long_positions[:]:
                entry_price = pos['entry_price']

                # 上涨触发：平多开多
                if current_price >= entry_price * (1 + self.up_threshold):
                    profit = (current_price - entry_price) * pos['amount']
                    balance += profit
                    self.trades.append({
                        'timestamp': row['timestamp'],
                        'type': 'long_profit',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'profit': profit
                    })
                    # 重新开多
                    pos['entry_price'] = current_price
                    self.long_positions.remove(pos)
                    self.long_positions.append(pos)

                # 止损触发
                elif current_price <= entry_price * (1 - self.stop_loss):
                    profit = (current_price - entry_price) * pos['amount']
                    balance += profit
                    self.trades.append({
                        'timestamp': row['timestamp'],
                        'type': 'long_loss',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'profit': profit
                    })
                    self.long_positions.remove(pos)

            # 处理空单
            for pos in self.short_positions[:]:
                entry_price = pos['entry_price']

                # 下跌触发：平空开空
                if current_price <= entry_price * (1 - self.down_threshold):
                    profit = (entry_price - current_price) * pos['amount']
                    balance += profit
                    self.trades.append({
                        'timestamp': row['timestamp'],
                        'type': 'short_profit',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'profit': profit
                    })
                    # 重新开空
                    pos['entry_price'] = current_price
                    self.short_positions.remove(pos)
                    self.short_positions.append(pos)

                # 止损触发
                elif current_price >= entry_price * (1 + self.stop_loss):
                    profit = (entry_price - current_price) * pos['amount']
                    balance += profit
                    self.trades.append({
                        'timestamp': row['timestamp'],
                        'type': 'short_loss',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'profit': profit
                    })
                    self.short_positions.remove(pos)

        # 计算最终盈亏
        total_profit = sum([t['profit'] for t in self.trades])

        return pd.DataFrame(self.trades)


def print_backtest_results(trades_df: pd.DataFrame, initial_capital: float):
    """打印回测结果"""
    print("\n" + "="*60)
    print("回测结果报告")
    print("="*60)

    if len(trades_df) == 0:
        print("❌ 未产生任何交易")
        return

    # 基本统计
    total_profit = trades_df['profit'].sum()
    total_trades = len(trades_df)

    profit_trades = trades_df[trades_df['profit'] > 0]
    loss_trades = trades_df[trades_df['profit'] < 0]

    win_trades = len(profit_trades)
    lose_trades = len(loss_trades)
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

    avg_profit = profit_trades['profit'].mean() if len(profit_trades) > 0 else 0
    avg_loss = loss_trades['profit'].mean() if len(loss_trades) > 0 else 0
    max_profit = profit_trades['profit'].max() if len(profit_trades) > 0 else 0
    max_loss = loss_trades['profit'].min() if len(loss_trades) > 0 else 0

    # 按类型分组统计
    long_profit_trades = trades_df[trades_df['type'] == 'long_profit']
    long_loss_trades = trades_df[trades_df['type'] == 'long_loss']
    short_profit_trades = trades_df[trades_df['type'] == 'short_profit']
    short_loss_trades = trades_df[trades_df['type'] == 'short_loss']

    print(f"\n【基本统计】")
    print(f"  初始资金:      ${initial_capital:,.2f}")
    print(f"  总交易次数:    {total_trades}")
    print(f"  总盈亏:        ${total_profit:,.2f} ({total_profit/initial_capital*100:+.2f}%)")

    print(f"\n【胜率分析】")
    print(f"  盈利次数:      {win_trades}")
    print(f"  亏损次数:      {lose_trades}")
    print(f"  胜率:          {win_rate:.2f}%")

    print(f"\n【盈亏分析】")
    print(f"  平均盈利:      ${avg_profit:,.2f}")
    print(f"  平均亏损:      ${avg_loss:,.2f}")
    print(f"  最大盈利:      ${max_profit:,.2f}")
    print(f"  最大亏损:      ${max_loss:,.2f}")
    print(f"  盈亏比:        {abs(avg_profit/avg_loss):.2f}" if avg_loss != 0 else "  盈亏比:        N/A")

    print(f"\n【多单统计】")
    print(f"  盈利次数:      {len(long_profit_trades)}")
    print(f"  亏损次数:      {len(long_loss_trades)}")
    print(f"  多单总盈亏:    ${long_profit_trades['profit'].sum() + long_loss_trades['profit'].sum():,.2f}")

    print(f"\n【空单统计】")
    print(f"  盈利次数:      {len(short_profit_trades)}")
    print(f"  亏损次数:      {len(short_loss_trades)}")
    print(f"  空单总盈亏:    ${short_profit_trades['profit'].sum() + short_loss_trades['profit'].sum():,.2f}")

    # 风险评估
    print(f"\n【风险评估】")
    if total_profit > 0:
        print(f"  ✅ 策略盈利")
    else:
        print(f"  ⚠️  策略亏损")

    if win_rate > 50:
        print(f"  ✅ 胜率良好")
    else:
        print(f"  ⚠️  胜率偏低")

    print("\n" + "="*60)


def main():
    """主函数"""
    print("\n🚀 开始测试代号A策略...")
    print("-"*60)

    # 生成测试数据
    print("\n📊 生成模拟数据...")
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()

    data = generate_sample_data(
        start_date=start_date,
        end_date=end_date,
        initial_price=50000,
        volatility=0.02,
        trend=0.0001
    )

    print(f"  数据范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    print(f"  数据点数: {len(data)}")
    print(f"  价格范围: ${data['low'].min():,.2f} - ${data['high'].max():,.2f}")
    print(f"  最终价格: ${data.iloc[-1]['close']:,.2f}")

    # 测试不同参数组合
    test_configs = [
        {
            'name': '保守策略',
            'investment': 1000,
            'up_threshold': 0.03,
            'down_threshold': 0.03,
            'stop_loss': 0.05
        },
        {
            'name': '平衡策略',
            'investment': 1000,
            'up_threshold': 0.02,
            'down_threshold': 0.02,
            'stop_loss': 0.10
        },
        {
            'name': '激进策略',
            'investment': 1000,
            'up_threshold': 0.015,
            'down_threshold': 0.015,
            'stop_loss': 0.15
        }
    ]

    results = []

    for config in test_configs:
        print(f"\n🔬 测试策略: {config['name']}")
        print(f"   参数: 上涨阈值={config['up_threshold']*100:.1f}%, "
              f"下跌阈值={config['down_threshold']*100:.1f}%, "
              f"止损={config['stop_loss']*100:.1f}%")

        # 执行回测
        strategy = SimpleCodeABacktest(
            investment_amount=config['investment'],
            up_threshold=config['up_threshold'],
            down_threshold=config['down_threshold'],
            stop_loss=config['stop_loss']
        )

        trades_df = strategy.execute(data)

        # 打印结果
        print_backtest_results(trades_df, config['investment'] * 2)

        # 保存结果
        if len(trades_df) > 0:
            results.append({
                'config': config,
                'total_profit': trades_df['profit'].sum(),
                'win_rate': len(trades_df[trades_df['profit'] > 0]) / len(trades_df) * 100,
                'total_trades': len(trades_df)
            })

    # 总结
    print("\n" + "="*60)
    print("📈 策略对比总结")
    print("="*60)

    for result in results:
        config = result['config']
        print(f"\n{config['name']}:")
        print(f"  总盈亏: ${result['total_profit']:,.2f}")
        print(f"  胜率:   {result['win_rate']:.2f}%")
        print(f"  交易数: {result['total_trades']}")

    # 推荐最佳策略
    if results:
        best = max(results, key=lambda x: x['total_profit'])
        print(f"\n💡 推荐策略: {best['config']['name']}")
        print(f"   原因: 该策略在测试期间获得了最高的盈利")

    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
