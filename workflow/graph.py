from typing import Literal
from langgraph.graph import StateGraph, END
from workflow.state import TradingBotState
from workflow.nodes import (
    market_data_node,
    strategy_node,
    risk_check_node,
    execution_node,
    MarketDataInput,
    MarketDataOutput,
    StrategyInput,
    StrategyOutput,
    RiskCheckInput,
    RiskCheckOutput,
    ExecutionInput,
    ExecutionOutput
)


def should_continue(state: dict) -> Literal["continue", "stop"]:
    """
    title: 决策是否继续
    desc: 根据风险检查结果决定是否继续执行订单
    """
    if state.get('approved', False):
        return "continue"
    else:
        return "stop"


def build_trading_graph() -> StateGraph:
    """
    构建交易工作流图
    """
    # 创建工作流图
    workflow = StateGraph(dict)

    # 添加节点
    workflow.add_node("market_data", lambda x: {"market_output": market_data_node(**x['market_input'])})
    workflow.add_node("strategy", lambda x: {"strategy_output": strategy_node(**{
        'state': x['state'],
        'market_data': x['market_output']
    })})
    workflow.add_node("risk_check", lambda x: {"risk_output": risk_check_node(**{
        'signals': x['strategy_output'].signals,
        'state': x['state']
    })})
    workflow.add_node("execution", lambda x: {"execution_output": execution_node(**{
        'signals': x['risk_output'].filtered_signals,
        'state': x['state']
    })})

    # 设置入口点
    workflow.set_entry_point("market_data")

    # 添加边
    workflow.add_edge("market_data", "strategy")
    workflow.add_edge("strategy", "risk_check")

    # 添加条件边
    workflow.add_conditional_edges(
        "risk_check",
        should_continue,
        {
            "continue": "execution",
            "stop": END
        }
    )

    workflow.add_edge("execution", END)

    return workflow.compile()


# 创建全局图实例
trading_graph = build_trading_graph()
