from typing import Dict, List
from workflow.state import (
    MarketDataInput,
    MarketDataOutput,
    StrategyInput,
    StrategyOutput,
    ExecutionInput,
    ExecutionOutput,
    RiskCheckInput,
    RiskCheckOutput,
    TradingBotState
)


def market_data_node(state: MarketDataInput) -> MarketDataOutput:
    """
    title: 市场数据处理
    desc: 获取并处理市场数据，分析价格趋势和波动率
    """
    # 计算简单趋势（实际应该使用更复杂的分析）
    if not hasattr(market_data_node, 'last_price'):
        market_data_node.last_price = state.price

    price_change = (state.price - market_data_node.last_price) / market_data_node.last_price
    market_data_node.last_price = state.price

    trend = "neutral"
    if price_change > 0.005:
        trend = "up"
    elif price_change < -0.005:
        trend = "down"

    # 简单波动率计算
    volatility = abs(price_change)

    return MarketDataOutput(
        price=state.price,
        trend=trend,
        volatility=volatility
    )


def strategy_node(state: StrategyInput) -> StrategyOutput:
    """
    title: 策略生成
    desc: 基于市场数据和当前状态生成交易信号
    """
    signals = []
    updated_state = state.state

    # 网格策略信号生成
    if state.market_data.trend == "down":
        # 价格下跌，生成买入信号
        for order in updated_state.orders:
            if (order['type'] == 'buy' and
                order['status'] == 'pending' and
                state.market_data.price <= order['price']):
                signals.append({
                    'action': 'buy',
                    'price': order['price'],
                    'amount': order['amount'],
                    'order_ref': order
                })

    elif state.market_data.trend == "up":
        # 价格上涨，生成卖出信号
        for order in updated_state.orders:
            if (order['type'] == 'sell' and
                order['status'] == 'pending' and
                state.market_data.price >= order['price']):
                signals.append({
                    'action': 'sell',
                    'price': order['price'],
                    'amount': order['amount'],
                    'order_ref': order
                })

    return StrategyOutput(
        signals=signals,
        updated_state=updated_state
    )


def risk_check_node(state: RiskCheckInput) -> RiskCheckOutput:
    """
    title: 风险检查
    desc: 检查交易信号的风险等级，过滤高风险交易
    """
    approved = True
    filtered_signals = []
    risk_level = "low"

    # 计算总风险敞口
    total_risk = 0
    for signal in state.signals:
        total_risk += signal['price'] * signal['amount']

    # 风险评估
    risk_ratio = total_risk / (state.state.total_invested + 1)  # 避免除零

    if risk_ratio > 0.3:
        risk_level = "high"
        # 高风险只保留部分信号
        filtered_signals = state.signals[:len(state.signals)//2]
    elif risk_ratio > 0.15:
        risk_level = "medium"
        filtered_signals = state.signals
    else:
        risk_level = "low"
        filtered_signals = state.signals

    if not filtered_signals:
        approved = False

    return RiskCheckOutput(
        approved=approved,
        filtered_signals=filtered_signals,
        risk_level=risk_level
    )


def execution_node(state: ExecutionInput) -> ExecutionOutput:
    """
    title: 订单执行
    desc: 执行交易信号，更新订单和状态
    """
    executed_orders = []
    updated_state = state.state
    success = True

    for signal in state.signals:
        try:
            # 模拟订单执行
            order_ref = signal['order_ref']
            order_ref['status'] = 'filled'
            executed_orders.append(signal)

            # 更新状态
            if signal['action'] == 'buy':
                updated_state.total_invested += signal['price'] * signal['amount']
            elif signal['action'] == 'sell':
                profit = (signal['price'] - (signal['price'] / 1.02)) * signal['amount']
                updated_state.realized_profit += profit

            # 记录交易
            updated_state.trades.append({
                'timestamp': __import__('datetime').datetime.now().isoformat(),
                'action': signal['action'],
                'price': signal['price'],
                'amount': signal['amount']
            })

        except Exception as e:
            success = False
            print(f"订单执行失败: {e}")

    return ExecutionOutput(
        executed_orders=executed_orders,
        updated_state=updated_state,
        success=success
    )
