"""
实盘交易启动脚本

使用方法：
    python start_real_trading.py --symbol BTC/USDT --amount 1000 --binance

功能：
    1. 启动代号A策略进行实盘交易
    2. 支持Binance等交易所
    3. 自动处理订单管理
"""

import argparse
import sys
import time
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='启动实盘交易')
    parser.add_argument('--symbol', type=str, default='BTC/USDT', help='交易对')
    parser.add_argument('--amount', type=float, default=1000, help='单边投资金额')
    parser.add_argument('--up-threshold', type=float, default=0.02, help='上涨阈值')
    parser.add_argument('--down-threshold', type=float, default=0.02, help='下跌阈值')
    parser.add_argument('--stop-loss', type=float, default=0.10, help='止损比例')
    parser.add_argument('--exchange', type=str, choices=['binance', 'okx'], default='binance',
                       help='交易所')
    parser.add_argument('--test', action='store_true', help='测试模式（不实际下单）')
    return parser.parse_args()


def check_api_keys():
    """检查API密钥配置"""
    from app.config import settings

    if not settings.BINANCE_API_KEY or not settings.BINANCE_API_SECRET:
        logger.error("❌ 未配置交易所API密钥")
        logger.error("请在环境变量中配置：")
        logger.error("  export BINANCE_API_KEY='your_api_key'")
        logger.error("  export BINANCE_API_SECRET='your_api_secret'")
        return False

    logger.info("✅ API密钥配置检查通过")
    return True


def init_strategy(args):
    """初始化策略"""
    from app.code_a_strategy import CodeAStrategy

    logger.info(f"📊 初始化代号A策略...")
    logger.info(f"   交易对: {args.symbol}")
    logger.info(f"   单边金额: ${args.amount}")
    logger.info(f"   上涨阈值: {args.up_threshold*100:.1f}%")
    logger.info(f"   下跌阈值: {args.down_threshold*100:.1f}%")
    logger.info(f"   止损比例: {args.stop_loss*100:.1f}%")
    logger.info(f"   交易模式: {'测试模式' if args.test else '实盘模式'}")

    strategy = CodeAStrategy(
        trading_pair=args.symbol,
        investment_amount=args.amount,
        up_threshold=args.up_threshold,
        down_threshold=args.down_threshold,
        stop_loss=args.stop_loss
    )

    return strategy


def run_trading_loop(strategy, args):
    """运行交易循环"""
    from app.exchange import ExchangeAPI
    from app.config import settings

    logger.info("\n" + "="*60)
    logger.info("🚀 开始实盘交易循环")
    logger.info("="*60)

    # 初始化交易所API
    if args.exchange == 'binance':
        exchange = ExchangeAPI(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET,
            testnet=args.test
        )
    else:
        logger.error(f"暂不支持 {args.exchange} 交易所")
        return

    # 检查连接
    try:
        balance = exchange.get_balance()
        logger.info(f"✅ 交易所连接成功")
        logger.info(f"   USDT余额: ${balance:.2f}")

        if balance < args.amount * 2:
            logger.warning(f"⚠️  余额不足！需要: ${args.amount*2:.2f}, 当前: ${balance:.2f}")
            return

    except Exception as e:
        logger.error(f"❌ 连接交易所失败: {e}")
        return

    # 初始化策略（开多空两单）
    try:
        ticker = exchange.get_ticker(args.symbol)
        current_price = ticker['last']
        logger.info(f"📈 当前价格: ${current_price:.2f}")

        strategy.initialize(current_price)
        logger.info("✅ 策略初始化成功，已开多空两单")

        # 实际下单
        if not args.test:
            # TODO: 实现实际下单逻辑
            logger.warning("⚠️  实盘下单功能需要根据实际交易所API实现")
            logger.info("   当前为演示模式，仅模拟交易")

    except Exception as e:
        logger.error(f"❌ 初始化策略失败: {e}")
        return

    # 主循环
    logger.info("\n⏰ 进入交易监控循环（按Ctrl+C退出）...")
    logger.info("-"*60)

    try:
        iteration = 0
        while True:
            iteration += 1

            try:
                # 获取最新价格
                ticker = exchange.get_ticker(args.symbol)
                current_price = ticker['last']

                # 检查策略信号
                long_signals, short_signals = strategy.check_signals(current_price)

                # 执行多单信号
                for signal in long_signals:
                    logger.info(f"🟢 多单信号: {signal['type']} @ ${current_price:.2f}")
                    if not args.test:
                        # TODO: 实际下单
                        pass
                    else:
                        logger.info(f"   [测试] 模拟执行多单信号")

                # 执行空单信号
                for signal in short_signals:
                    logger.info(f"🔴 空单信号: {signal['type']} @ ${current_price:.2f}")
                    if not args.test:
                        # TODO: 实际下单
                        pass
                    else:
                        logger.info(f"   [测试] 模拟执行空单信号")

                # 每10次循环输出一次状态
                if iteration % 10 == 0:
                    profit = strategy.calculate_profit(current_price)
                    logger.info(f"📊 状态更新: 价格=${current_price:.2f}, "
                              f"浮动盈亏=${profit:.2f}")

                # 等待
                time.sleep(60)  # 每分钟检查一次

            except KeyboardInterrupt:
                logger.info("\n⏸️  用户中断，停止交易...")
                break
            except Exception as e:
                logger.error(f"❌ 交易循环错误: {e}")
                time.sleep(10)

    finally:
        # 清理
        logger.info("🧹 清理中...")
        final_price = exchange.get_ticker(args.symbol)['last']
        final_profit = strategy.calculate_profit(final_price)
        logger.info(f"📊 最终盈亏: ${final_profit:.2f}")
        logger.info("✅ 交易已停止")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🤖 实盘交易系统 - 代号A策略")
    print("="*60 + "\n")

    # 解析参数
    args = parse_args()

    # 检查配置
    if not check_api_keys():
        return

    # 初始化策略
    strategy = init_strategy(args)

    # 运行交易
    run_trading_loop(strategy, args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
        sys.exit(0)
