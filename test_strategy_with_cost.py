"""
带成本计算的策略测试脚本

使用方法：
    python test_strategy_with_cost.py

功能：
    1. 测试代号A策略的有效性
    2. 使用模拟数据进行回测
    3. 详细的交易成本分析（手续费、滑点、资金占用）
    4. 输出完整的性能指标
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 导入策略和回测模块
from app.code_a_strategy import CodeAStrategy
from app.backtest import BacktestEngine, BacktestConfig
from app.cost_calculator import (
    CostCalculator,
    CostConfig,
    calculate_capital_efficiency,
    estimate_break_even_trades
)


def generate_sample_data(
    start_date: datetime,
    end_date: datetime,
    initial_price: float = 50000,
    volatility: float = 0.02,
    trend: float = 0.0001  # 每日趋势
) -> pd.DataFrame:
    """生成模拟价格数据"""
    dates = pd.date_range(start=start_date, end=end_date, freq='h')  # 每小时数据

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


class CostAwareCodeABacktest:
    """带成本计算的对冲马丁格尔策略回测"""

    def __init__(
        self,
        investment_amount: float = 1000,
        up_threshold: float = 0.02,
        down_threshold: float = 0.02,
        stop_loss: float = 0.10,
        cost_config: CostConfig = None
    ):
        self.investment_amount = investment_amount
        self.up_threshold = up_threshold
        self.down_threshold = down_threshold
        self.stop_loss = stop_loss

        # 成本计算器
        self.cost_config = cost_config or CostConfig()
        self.cost_calculator = CostCalculator(self.cost_config)

        self.trades = []
        self.long_positions = []
        self.short_positions = []

    def execute(self, data: pd.DataFrame) -> tuple:
        """执行回测，返回(交易记录, 成本明细)"""
        # 初始化：同时开多空两单
        initial_price = data.iloc[0]['close']
        initial_time = data.iloc[0]['timestamp']
        amount = self.investment_amount / initial_price

        # 开多单
        long_pos = {
            'position_id': 'long_1',
            'entry_price': initial_price,
            'amount': amount,
            'entry_time': initial_time
        }
        self.long_positions.append(long_pos)

        # 计算开多成本
        open_cost = self.cost_calculator.calculate_open_cost(
            trade_id='long_open_1',
            timestamp=initial_time,
            symbol='BTC/USDT',
            side='long',
            price=initial_price,
            amount=amount
        )

        # 开空单
        short_pos = {
            'position_id': 'short_1',
            'entry_price': initial_price,
            'amount': amount,
            'entry_time': initial_time
        }
        self.short_positions.append(short_pos)

        # 计算开空成本
        self.cost_calculator.calculate_open_cost(
            trade_id='short_open_1',
            timestamp=initial_time,
            symbol='BTC/USDT',
            side='short',
            price=initial_price,
            amount=amount
        )

        # 逐K线处理
        trade_counter = 0
        for idx, row in data.iterrows():
            current_price = row['close']
            current_time = row['timestamp']

            # 处理多单
            for pos in self.long_positions[:]:
                entry_price = pos['entry_price']
                entry_time = pos['entry_time']
                holding_time = current_time - entry_time

                # 上涨触发：平多开多
                if current_price >= entry_price * (1 + self.up_threshold):
                    # 计算毛利润
                    gross_profit = (current_price - entry_price) * pos['amount']

                    # 计算平仓成本
                    trade_counter += 1
                    close_cost = self.cost_calculator.calculate_close_cost(
                        trade_id=f'long_close_{trade_counter}',
                        timestamp=current_time,
                        symbol='BTC/USDT',
                        side='long',
                        entry_price=entry_price,
                        close_price=current_price,
                        amount=pos['amount'],
                        holding_time=holding_time
                    )

                    self.trades.append({
                        'timestamp': current_time,
                        'type': 'long_profit',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'amount': pos['amount'],
                        'gross_profit': gross_profit,
                        'commission': close_cost.commission,
                        'slippage': close_cost.slippage,
                        'funding_cost': close_cost.funding_cost,
                        'total_cost': close_cost.total_cost,
                        'net_profit': close_cost.net_profit
                    })

                    # 重新开多
                    pos['entry_price'] = current_price
                    pos['entry_time'] = current_time

                    # 计算新开仓成本
                    trade_counter += 1
                    new_open_cost = self.cost_calculator.calculate_open_cost(
                        trade_id=f'long_reopen_{trade_counter}',
                        timestamp=current_time,
                        symbol='BTC/USDT',
                        side='long',
                        price=current_price,
                        amount=pos['amount']
                    )

                # 止损触发
                elif current_price <= entry_price * (1 - self.stop_loss):
                    gross_profit = (current_price - entry_price) * pos['amount']

                    trade_counter += 1
                    close_cost = self.cost_calculator.calculate_close_cost(
                        trade_id=f'long_stoploss_{trade_counter}',
                        timestamp=current_time,
                        symbol='BTC/USDT',
                        side='long',
                        entry_price=entry_price,
                        close_price=current_price,
                        amount=pos['amount'],
                        holding_time=holding_time
                    )

                    self.trades.append({
                        'timestamp': current_time,
                        'type': 'long_loss',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'amount': pos['amount'],
                        'gross_profit': gross_profit,
                        'commission': close_cost.commission,
                        'slippage': close_cost.slippage,
                        'funding_cost': close_cost.funding_cost,
                        'total_cost': close_cost.total_cost,
                        'net_profit': close_cost.net_profit
                    })

                    self.long_positions.remove(pos)

            # 处理空单
            for pos in self.short_positions[:]:
                entry_price = pos['entry_price']
                entry_time = pos['entry_time']
                holding_time = current_time - entry_time

                # 下跌触发：平空开空
                if current_price <= entry_price * (1 - self.down_threshold):
                    gross_profit = (entry_price - current_price) * pos['amount']

                    trade_counter += 1
                    close_cost = self.cost_calculator.calculate_close_cost(
                        trade_id=f'short_close_{trade_counter}',
                        timestamp=current_time,
                        symbol='BTC/USDT',
                        side='short',
                        entry_price=entry_price,
                        close_price=current_price,
                        amount=pos['amount'],
                        holding_time=holding_time
                    )

                    self.trades.append({
                        'timestamp': current_time,
                        'type': 'short_profit',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'amount': pos['amount'],
                        'gross_profit': gross_profit,
                        'commission': close_cost.commission,
                        'slippage': close_cost.slippage,
                        'funding_cost': close_cost.funding_cost,
                        'total_cost': close_cost.total_cost,
                        'net_profit': close_cost.net_profit
                    })

                    # 重新开空
                    pos['entry_price'] = current_price
                    pos['entry_time'] = current_time

                    trade_counter += 1
                    new_open_cost = self.cost_calculator.calculate_open_cost(
                        trade_id=f'short_reopen_{trade_counter}',
                        timestamp=current_time,
                        symbol='BTC/USDT',
                        side='short',
                        price=current_price,
                        amount=pos['amount']
                    )

                # 止损触发
                elif current_price >= entry_price * (1 + self.stop_loss):
                    gross_profit = (entry_price - current_price) * pos['amount']

                    trade_counter += 1
                    close_cost = self.cost_calculator.calculate_close_cost(
                        trade_id=f'short_stoploss_{trade_counter}',
                        timestamp=current_time,
                        symbol='BTC/USDT',
                        side='short',
                        entry_price=entry_price,
                        close_price=current_price,
                        amount=pos['amount'],
                        holding_time=holding_time
                    )

                    self.trades.append({
                        'timestamp': current_time,
                        'type': 'short_loss',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'amount': pos['amount'],
                        'gross_profit': gross_profit,
                        'commission': close_cost.commission,
                        'slippage': close_cost.slippage,
                        'funding_cost': close_cost.funding_cost,
                        'total_cost': close_cost.total_cost,
                        'net_profit': close_cost.net_profit
                    })

                    self.short_positions.remove(pos)

        # 转换为DataFrame
        trades_df = pd.DataFrame(self.trades)
        cost_summary = self.cost_calculator.get_cost_summary()

        return trades_df, cost_summary


def print_backtest_results(trades_df: pd.DataFrame, cost_summary: dict, initial_capital: float):
    """打印回测结果（含成本分析）"""
    print("\n" + "="*60)
    print("回测结果报告（含成本分析）")
    print("="*60)

    if len(trades_df) == 0:
        print("❌ 未产生任何交易")
        return

    # 基本统计
    total_gross_profit = trades_df['gross_profit'].sum()
    total_net_profit = trades_df['net_profit'].sum()
    total_trades = len(trades_df)

    profit_trades = trades_df[trades_df['net_profit'] > 0]
    loss_trades = trades_df[trades_df['net_profit'] < 0]

    win_trades = len(profit_trades)
    lose_trades = len(loss_trades)
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

    avg_gross_profit = trades_df['gross_profit'].mean()
    avg_net_profit = trades_df['net_profit'].mean()
    max_net_profit = profit_trades['net_profit'].max() if len(profit_trades) > 0 else 0
    max_net_loss = loss_trades['net_profit'].min() if len(loss_trades) > 0 else 0

    # 按类型分组统计
    long_profit_trades = trades_df[trades_df['type'] == 'long_profit']
    long_loss_trades = trades_df[trades_df['type'] == 'long_loss']
    short_profit_trades = trades_df[trades_df['type'] == 'short_profit']
    short_loss_trades = trades_df[trades_df['type'] == 'short_loss']

    print(f"\n【基本统计】")
    print(f"  初始资金:      ${initial_capital:,.2f}")
    print(f"  总交易次数:    {total_trades}")
    print(f"  毛利润:        ${total_gross_profit:,.2f} ({total_gross_profit/initial_capital*100:+.2f}%)")
    print(f"  总成本:        ${cost_summary.get('total_cost', 0):,.2f} ({cost_summary.get('cost_rate', 0)*100:.2f}%)")
    print(f"  净利润:        ${total_net_profit:,.2f} ({total_net_profit/initial_capital*100:+.2f}%)")

    print(f"\n【成本明细】")
    print(f"  手续费:        ${cost_summary.get('total_commission', 0):,.2f} ({cost_summary.get('commission_rate', 0)*100:.3f}%)")
    print(f"  滑点成本:      ${cost_summary.get('total_slippage', 0):,.2f} ({cost_summary.get('slippage_rate', 0)*100:.3f}%)")
    print(f"  资金费:        ${cost_summary.get('total_funding', 0):,.2f}")
    print(f"  平均每笔成本:  ${cost_summary.get('avg_cost_per_trade', 0):,.4f}")

    if 'cost_breakdown' in cost_summary:
        breakdown = cost_summary['cost_breakdown']
        print(f"\n【成本构成】")
        print(f"  手续费占比:    {breakdown.get('commission', 0):.1f}%")
        print(f"  滑点占比:      {breakdown.get('slippage', 0):.1f}%")
        print(f"  资金费占比:    {breakdown.get('funding', 0):.1f}%")

    print(f"\n【胜率分析】")
    print(f"  盈利次数:      {win_trades}")
    print(f"  亏损次数:      {lose_trades}")
    print(f"  胜率:          {win_rate:.2f}%")

    print(f"\n【盈亏分析】")
    print(f"  平均毛利润:    ${avg_gross_profit:,.2f}")
    print(f"  平均净利润:    ${avg_net_profit:,.2f}")
    print(f"  最大净利润:    ${max_net_profit:,.2f}")
    print(f"  最大净亏损:    ${max_net_loss:,.2f}")

    print(f"\n【多单统计】")
    print(f"  盈利次数:      {len(long_profit_trades)}")
    print(f"  亏损次数:      {len(long_loss_trades)}")
    if len(long_profit_trades) > 0 or len(long_loss_trades) > 0:
        long_net = long_profit_trades['net_profit'].sum() + long_loss_trades['net_profit'].sum()
        print(f"  多单净利润:    ${long_net:,.2f}")

    print(f"\n【空单统计】")
    print(f"  盈利次数:      {len(short_profit_trades)}")
    print(f"  亏损次数:      {len(short_loss_trades)}")
    if len(short_profit_trades) > 0 or len(short_loss_trades) > 0:
        short_net = short_profit_trades['net_profit'].sum() + short_loss_trades['net_profit'].sum()
        print(f"  空单净利润:    ${short_net:,.2f}")

    # 资金效率分析
    trading_days = 30
    capital_eff = calculate_capital_efficiency(
        total_profit=total_net_profit,
        initial_capital=initial_capital,
        trading_days=trading_days
    )

    print(f"\n【资金效率】")
    print(f"  年化收益率:    {capital_eff.get('annual_return', 0)*100:.2f}%")
    print(f"  日均收益率:    {capital_eff.get('daily_return', 0)*100:.4f}%")
    print(f"  资金效率比:    {capital_eff.get('capital_efficiency', 0):.2f}")

    # 盈亏平衡分析
    break_even = estimate_break_even_trades(
        avg_profit_per_trade=avg_gross_profit,
        avg_cost_per_trade=cost_summary.get('avg_cost_per_trade', 0)
    )

    print(f"\n【盈亏平衡分析】")
    print(f"  每笔需覆盖成本: ${break_even.get('break_even_profit', 0):,.4f}")
    print(f"  策略是否盈利:   {'✅ 是' if break_even.get('is_profitable') else '❌ 否'}")
    if not break_even.get('is_profitable'):
        print(f"  预计需交易次数: {break_even.get('trades_to_break_even', 0)} 笔")

    # 风险评估
    print(f"\n【风险评估】")
    if total_net_profit > 0:
        print(f"  ✅ 策略盈利")
    else:
        print(f"  ⚠️  策略亏损")

    if win_rate > 50:
        print(f"  ✅ 胜率良好")
    else:
        print(f"  ⚠️  胜率偏低")

    if cost_summary.get('cost_rate', 0) < 0.01:
        print(f"  ✅ 成本控制良好")
    elif cost_summary.get('cost_rate', 0) < 0.02:
        print(f"  ⚠️  成本偏高")
    else:
        print(f"  ❌ 成本过高")

    print("\n" + "="*60)


def main():
    """主函数"""
    print("\n🚀 开始测试代号A策略（含成本分析）...")
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

        # 创建成本配置
        cost_config = CostConfig(
            commission_rate=0.001,  # 0.1% 手续费
            slippage_rate=0.0005,  # 0.05% 滑点
            enable_funding_cost=False  # 不计算资金费
        )

        # 执行回测
        strategy = CostAwareCodeABacktest(
            investment_amount=config['investment'],
            up_threshold=config['up_threshold'],
            down_threshold=config['down_threshold'],
            stop_loss=config['stop_loss'],
            cost_config=cost_config
        )

        trades_df, cost_summary = strategy.execute(data)

        # 打印结果
        print_backtest_results(trades_df, cost_summary, config['investment'] * 2)

        # 保存结果
        if len(trades_df) > 0:
            results.append({
                'config': config,
                'total_net_profit': trades_df['net_profit'].sum(),
                'total_cost': cost_summary.get('total_cost', 0),
                'cost_rate': cost_summary.get('cost_rate', 0),
                'win_rate': len(trades_df[trades_df['net_profit'] > 0]) / len(trades_df) * 100,
                'total_trades': len(trades_df)
            })

    # 总结
    print("\n" + "="*60)
    print("📈 策略对比总结（扣除成本后）")
    print("="*60)

    for result in results:
        config = result['config']
        print(f"\n{config['name']}:")
        print(f"  净利润: ${result['total_net_profit']:,.2f}")
        print(f"  总成本: ${result['total_cost']:,.2f} ({result['cost_rate']*100:.2f}%)")
        print(f"  胜率:   {result['win_rate']:.2f}%")
        print(f"  交易数: {result['total_trades']}")

    # 推荐最佳策略
    if results:
        best = max(results, key=lambda x: x['total_net_profit'])
        print(f"\n💡 推荐策略: {best['config']['name']}")
        print(f"   原因: 该策略在扣除成本后获得了最高的净利润")

    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
