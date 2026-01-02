"""
手动测试LangGraph工作流
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graphs.graph import main_graph
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import new_context, Context
import json


def run_manual_test():
    """手动运行工作流测试"""
    print("\n" + "=" * 60)
    print("开始手动测试LangGraph工作流")
    print("=" * 60)

    # 测试输入
    test_input = {
        "exchange": "binance",
        "trading_pair": "BTC/USDT",
        "is_simulation": True,
        "long_threshold": 0.02,
        "short_threshold": 0.02,
        "stop_loss_ratio": 0.05,
        "position_size": 0.01,
        "max_positions": 10,
        "action": "start"
    }

    print("\n测试输入:")
    print(json.dumps(test_input, indent=2))

    try:
        # 创建上下文
        ctx = new_context("manual_test")

        # 创建运行配置
        config = RunnableConfig(
            configurable={"thread_id": ctx.run_id}
        )

        print("\n开始执行工作流...")

        # 运行工作流
        result = main_graph.invoke(test_input, config=config, context=ctx)

        print("\n执行结果:")
        print(json.dumps(result, indent=2, default=str))

        print("\n✅ 工作流执行成功")
        return True

    except Exception as e:
        print(f"\n❌ 工作流执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_manual_test()
    sys.exit(0 if success else 1)
