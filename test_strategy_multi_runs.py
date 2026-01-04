"""
多次策略测试脚本（大样本统计）

使用方法：
    python test_strategy_multi_runs.py

功能：
    1. 进行100/200/500/1000次独立回测
    2. 统计平均表现、标准差、成功率
    3. 更可靠的策略评估
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
import json
from collections import defaultdict

# 导入策略和回测模块
from app.code_a_strategy import CodeAStrategy
from app.backtest import BacktestEngine, BacktestConfig
from app.cost_calculator import (
    CostCalculator,
    CostConfig,
    calculate_capital_efficiency
)


def generate_sample_data(
    start_date: datetime,
    end_date: datetime,
    initial_price: float = 50000,
    volatility: float = 0.02,
    trend: float = 0.0001  # 每日趋势
) -> pd.DataFrame:
    """生成模拟价格数据"""
    dates = pd.date_range(start=start_date, end=end_date, freq='h')

    data = []
    price = initial_price

    for i, date in enumerate(dates):
        daily_return = np.random.normal(trend, volatility / np.sqrt(24))
        price = price * (1 + daily_return)

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

        self.cost_config = cost_config or CostConfig()
        self.cost_calculator = CostCalculator(self.cost_config)

        self.trades = []
        self.long_positions = []
        self.short_positions = []

    def execute(self, data: pd.DataFrame) -> tuple:
        """执行回测，返回(交易记录, 成本明细)"""
        # 重置状态
        self.cost_calculator.reset()
        self.trades = []
        self.long_positions = []
        self.short_positions = []

        initial_price = data.iloc[0]['close']
        initial_time = data.iloc[0]['timestamp']
        amount = self.investment_amount / initial_price

        # 开多空两单
        long_pos = {
            'position_id': 'long_1',
            'entry_price': initial_price,
            'amount': amount,
            'entry_time': initial_time
        }
        self.long_positions.append(long_pos)
        self.cost_calculator.calculate_open_cost(
            trade_id='long_open_1',
            timestamp=initial_time,
            symbol='BTC/USDT',
            side='long',
            price=initial_price,
            amount=amount
        )

        short_pos = {
            'position_id': 'short_1',
            'entry_price': initial_price,
            'amount': amount,
            'entry_time': initial_time
        }
        self.short_positions.append(short_pos)
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

                # 上涨触发
                if current_price >= entry_price * (1 + self.up_threshold):
                    gross_profit = (current_price - entry_price) * pos['amount']

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
                        'total_cost': close_cost.total_cost,
                        'net_profit': close_cost.net_profit
                    })

                    pos['entry_price'] = current_price
                    pos['entry_time'] = current_time

                    trade_counter += 1
                    self.cost_calculator.calculate_open_cost(
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
                        'total_cost': close_cost.total_cost,
                        'net_profit': close_cost.net_profit
                    })

                    self.long_positions.remove(pos)

            # 处理空单
            for pos in self.short_positions[:]:
                entry_price = pos['entry_price']
                entry_time = pos['entry_time']
                holding_time = current_time - entry_time

                # 下跌触发
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
                        'total_cost': close_cost.total_cost,
                        'net_profit': close_cost.net_profit
                    })

                    pos['entry_price'] = current_price
                    pos['entry_time'] = current_time

                    trade_counter += 1
                    self.cost_calculator.calculate_open_cost(
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
                        'total_cost': close_cost.total_cost,
                        'net_profit': close_cost.net_profit
                    })

                    self.short_positions.remove(pos)

        trades_df = pd.DataFrame(self.trades)
        cost_summary = self.cost_calculator.get_cost_summary()

        return trades_df, cost_summary


def run_multiple_backtests(
    config: dict,
    num_runs: int,
    cost_config: CostConfig
) -> Dict:
    """
    运行多次回测

    Args:
        config: 策略配置
        num_runs: 运行次数
        cost_config: 成本配置

    Returns:
        统计结果
    """
    print(f"\n  正在运行 {num_runs} 次回测...")

    results = {
        'net_profits': [],
        'gross_profits': [],
        'total_costs': [],
        'cost_rates': [],
        'win_rates': [],
        'total_trades': [],
        'max_drawdowns': [],
        'long_profits': [],
        'short_profits': []
    }

    for i in range(num_runs):
        # 生成随机数据
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        # 每次使用不同的随机种子
        np.random.seed(i + 1000)
        volatility = np.random.uniform(0.015, 0.025)  # 随机波动率
        trend = np.random.uniform(-0.0002, 0.0002)  # 随机趋势

        data = generate_sample_data(
            start_date=start_date,
            end_date=end_date,
            initial_price=50000,
            volatility=volatility,
            trend=trend
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

        if len(trades_df) > 0:
            net_profit = trades_df['net_profit'].sum()
            gross_profit = trades_df['gross_profit'].sum()
            total_cost = cost_summary.get('total_cost', 0)
            cost_rate = cost_summary.get('cost_rate', 0)
            win_rate = len(trades_df[trades_df['net_profit'] > 0]) / len(trades_df) * 100
            total_trades = len(trades_df)

            # 计算最大回撤
            equity_curve = []
            cumulative_profit = 0
            for _, trade in trades_df.iterrows():
                cumulative_profit += trade['net_profit']
                equity_curve.append(cumulative_profit)

            max_drawdown = 0
            if equity_curve:
                peak = equity_curve[0]
                for value in equity_curve:
                    if value > peak:
                        peak = value
                    drawdown = (peak - value) / (peak + 1)  # 避免除零
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown

            # 多空盈亏
            long_trades = trades_df[trades_df['type'].str.contains('long')]
            short_trades = trades_df[trades_df['type'].str.contains('short')]
            long_profit = long_trades['net_profit'].sum() if len(long_trades) > 0 else 0
            short_profit = short_trades['net_profit'].sum() if len(short_trades) > 0 else 0

            results['net_profits'].append(net_profit)
            results['gross_profits'].append(gross_profit)
            results['total_costs'].append(total_cost)
            results['cost_rates'].append(cost_rate)
            results['win_rates'].append(win_rate)
            results['total_trades'].append(total_trades)
            results['max_drawdowns'].append(max_drawdown)
            results['long_profits'].append(long_profit)
            results['short_profits'].append(short_profit)

        # 进度显示
        if (i + 1) % 50 == 0 or i == num_runs - 1:
            print(f"    进度: {i + 1}/{num_runs} ({(i+1)/num_runs*100:.0f}%)")

    # 计算统计指标
    def calculate_stats(values):
        if not values:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0}
        return {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'median': np.median(values)
        }

    return {
        'num_runs': num_runs,
        'net_profit_stats': calculate_stats(results['net_profits']),
        'gross_profit_stats': calculate_stats(results['gross_profits']),
        'total_cost_stats': calculate_stats(results['total_costs']),
        'cost_rate_stats': calculate_stats(results['cost_rates']),
        'win_rate_stats': calculate_stats(results['win_rates']),
        'total_trades_stats': calculate_stats(results['total_trades']),
        'max_drawdown_stats': calculate_stats(results['max_drawdowns']),
        'long_profit_stats': calculate_stats(results['long_profits']),
        'short_profit_stats': calculate_stats(results['short_profits']),
        'success_rate': len([p for p in results['net_profits'] if p > 0]) / len(results['net_profits']) * 100 if results['net_profits'] else 0,
        'all_net_profits': results['net_profits']
    }


def print_multi_run_results(results_list: List[tuple], test_configs: List[Dict]):
    """打印多次回测结果"""
    print("\n" + "="*80)
    print("多次回测统计报告（大样本）")
    print("="*80)

    for results_tuple in results_list:
        results, config = results_tuple
        num_runs = results['num_runs']

        print(f"\n{'='*80}")
        print(f"【{config['name']}】 - {num_runs}次独立回测")
        print(f"{'='*80}")
        print(f"  参数: 上涨={config['up_threshold']*100:.1f}%, "
              f"下跌={config['down_threshold']*100:.1f}%, "
              f"止损={config['stop_loss']*100:.1f}%")

        # 净利润统计
        net_stats = results['net_profit_stats']
        print(f"\n【净利润统计】")
        print(f"  平均净利润:  ${net_stats['mean']:,.2f}")
        print(f"  标准差:      ${net_stats['std']:,.2f} ({net_stats['std']/abs(net_stats['mean'])*100 if net_stats['mean'] != 0 else 0:.1f}%)")
        print(f"  中位数:      ${net_stats['median']:,.2f}")
        print(f"  最大值:      ${net_stats['max']:,.2f}")
        print(f"  最小值:      ${net_stats['min']:,.2f}")
        print(f"  成功率:      {results['success_rate']:.2f}% ({int(results['success_rate']*num_runs/100)}/{num_runs} 次盈利)")

        # 成本统计
        cost_rate_stats = results['cost_rate_stats']
        total_cost_stats = results['total_cost_stats']
        print(f"\n【成本统计】")
        print(f"  平均总成本:  ${total_cost_stats['mean']:,.2f}")
        print(f"  平均成本率:  {cost_rate_stats['mean']*100:.3f}%")
        print(f"  成本率范围:  {cost_rate_stats['min']*100:.3f}% - {cost_rate_stats['max']*100:.3f}%")

        # 交易统计
        win_rate_stats = results['win_rate_stats']
        trades_stats = results['total_trades_stats']
        print(f"\n【交易统计】")
        print(f"  平均胜率:    {win_rate_stats['mean']:.2f}%")
        print(f"  胜率范围:    {win_rate_stats['min']:.2f}% - {win_rate_stats['max']:.2f}%")
        print(f"  平均交易数:  {trades_stats['mean']:.1f}笔")
        print(f"  交易数范围:  {trades_stats['min']:.0f} - {trades_stats['max']:.0f}笔")

        # 风险统计
        dd_stats = results['max_drawdown_stats']
        print(f"\n【风险统计】")
        print(f"  平均最大回撤: {dd_stats['mean']*100:.2f}%")
        print(f"  最大回撤范围: {dd_stats['min']*100:.2f}% - {dd_stats['max']*100:.2f}%")

        # 收益风险比
        if dd_stats['mean'] > 0:
            sharpe = net_stats['mean'] / (config['investment']*2 * dd_stats['mean']) if net_stats['mean'] > 0 else 0
            print(f"  收益风险比:   {sharpe:.2f}")

        # 多空盈亏
        long_stats = results['long_profit_stats']
        short_stats = results['short_profit_stats']
        print(f"\n【多空对比】")
        print(f"  平均多单利润: ${long_stats['mean']:,.2f}")
        print(f"  平均空单利润: ${short_stats['mean']:,.2f}")

        # 风险评估
        print(f"\n【风险评估】")
        if results['success_rate'] >= 70:
            print(f"  ✅ 成功率优秀 ({results['success_rate']:.1f}%)")
        elif results['success_rate'] >= 50:
            print(f"  ⚠️  成功率一般 ({results['success_rate']:.1f}%)")
        else:
            print(f"  ❌ 成功率较低 ({results['success_rate']:.1f}%)")

        if cost_rate_stats['mean'] < 0.002:
            print(f"  ✅ 成本控制良好")
        elif cost_rate_stats['mean'] < 0.005:
            print(f"  ⚠️  成本控制一般")
        else:
            print(f"  ❌ 成本偏高")

        # 分布分析
        print(f"\n【利润分布】")
        profits = results['all_net_profits']
        if profits:
            # 四分位数
            q25 = np.percentile(profits, 25)
            q75 = np.percentile(profits, 75)
            print(f"  25%分位数:  ${q25:,.2f}")
            print(f"  75%分位数:  ${q75:,.2f}")
            print(f"  四分位距:    ${q75-q25:,.2f}")

            # 盈亏分布
            profitable_count = len([p for p in profits if p > 0])
            break_even_count = len([p for p in profits if abs(p) < 10])
            loss_count = len([p for p in profits if p < -10])

            print(f"  盈利次数:    {profitable_count} ({profitable_count/len(profits)*100:.1f}%)")
            print(f"  盈亏平衡:    {break_even_count} ({break_even_count/len(profits)*100:.1f}%)")
            print(f"  亏损次数:    {loss_count} ({loss_count/len(profits)*100:.1f}%)")

    # 对比总结
    print(f"\n{'='*80}")
    print("【策略对比总结】")
    print(f"{'='*80}")

    comparison_data = []
    for results_tuple in results_list:
        results, config = results_tuple
        comparison_data.append({
            'name': config['name'],
            'avg_net_profit': results['net_profit_stats']['mean'],
            'net_profit_std': results['net_profit_stats']['std'],
            'success_rate': results['success_rate'],
            'avg_cost_rate': results['cost_rate_stats']['mean'],
            'avg_win_rate': results['win_rate_stats']['mean'],
            'avg_max_dd': results['max_drawdown_stats']['mean']
        })

    # 按平均净利润排序
    comparison_data.sort(key=lambda x: x['avg_net_profit'], reverse=True)

    print(f"\n{'策略名称':<10} {'平均净利润':<15} {'标准差':<15} {'成功率':<10} {'成本率':<12} {'胜率':<10}")
    print("-"*80)
    for data in comparison_data:
        print(f"{data['name']:<10} ${data['avg_net_profit']:>12,.2f}  ${data['net_profit_std']:>12,.2f}  {data['success_rate']:>8.1f}%  {data['avg_cost_rate']*100:>10.3f}%  {data['avg_win_rate']:>8.1f}%")

    # 推荐策略
    if comparison_data:
        best = comparison_data[0]
        print(f"\n💡 推荐策略: {best['name']}")
        print(f"   原因: 在{results_list[0][0]['num_runs']}次独立回测中，该策略平均净利润最高（${best['avg_net_profit']:,.2f}）")

        # 稳定性分析
        if comparison_data[0]['avg_net_profit'] > 0:
            if comparison_data[0]['net_profit_std'] / abs(comparison_data[0]['avg_net_profit']) < 0.5:
                print(f"   ✅ 策略稳定，波动较小")
            else:
                print(f"   ⚠️  策略收益波动较大，需要注意风险")

    print(f"\n{'='*80}")


def main():
    """主函数"""
    print("\n🚀 开始大规模策略测试（多次独立回测）...")
    print("-"*80)

    # 测试配置
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

    # 成本配置
    cost_config = CostConfig(
        commission_rate=0.001,
        slippage_rate=0.0005,
        enable_funding_cost=False
    )

    # 测试次数配置
    test_runs = [100, 200, 500, 1000]

    # 选择测试次数
    print(f"\n📊 测试次数配置: {', '.join([str(n) for n in test_runs])}")

    # 对每个配置进行多次测试
    all_results = []

    for config in test_configs:
        config_results = {}

        for num_runs in test_runs:
            print(f"\n{'='*80}")
            print(f"开始测试: {config['name']} - {num_runs}次独立回测")
            print(f"{'='*80}")

            results = run_multiple_backtests(config, num_runs, cost_config)
            config_results[num_runs] = results

            # 保存结果用于对比
            if num_runs == 1000:  # 只保存1000次的结果用于最终对比
                all_results.append((results, config))

        # 显示该配置的所有测试次数对比
        print(f"\n{'='*80}")
        print(f"【{config['name']}】不同测试次数对比")
        print(f"{'='*80}")
        print(f"\n{'测试次数':<10} {'平均净利润':<15} {'标准差':<15} {'成功率':<10}")
        print("-"*60)

        for num_runs in [100, 200, 500, 1000]:
            r = config_results[num_runs]
            print(f"{num_runs:<10} ${r['net_profit_stats']['mean']:>12,.2f}  "
                  f"${r['net_profit_stats']['std']:>12,.2f}  "
                  f"{r['success_rate']:>8.1f}%")

    # 打印1000次测试的详细对比
    print_multi_run_results(all_results, test_configs)

    print(f"\n✅ 所有测试完成！")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
