"""
风险管理辅助函数
用于在策略执行中集成风险管理功能
"""

from typing import Dict, Tuple, Optional
from app.risk_management import RiskManager, RiskLevel
import logging

logger = logging.getLogger(__name__)


async def pre_trade_risk_check(
    risk_manager: RiskManager,
    position_value: float = 0,
    order_value: float = 0,
    symbol: str = None
) -> Tuple[bool, list, str]:
    """
    交易前风险检查

    Args:
        risk_manager: 风险管理器实例
        position_value: 新增持仓价值
        order_value: 订单价值
        symbol: 交易对

    Returns:
        (是否通过, 错误列表, 建议操作)
    """
    # 检查所有限制
    passed, errors = risk_manager.check_all_limits(
        position_value=position_value,
        order_value=order_value
    )

    if not passed:
        logger.warning(f"风险检查未通过: {symbol}, 错误: {errors}")
        recommendation = "建议: 暂停交易或调整仓位大小"
        return False, errors, recommendation

    # 评估风险等级
    risk_report = risk_manager.get_risk_report()
    risk_level = risk_manager.evaluate_risk_level(
        position_value=risk_report['current_position'] + position_value,
        unrealized_pnl=risk_report['daily_pnl']
    )

    if risk_level == RiskLevel.HIGH:
        logger.warning(f"风险等级较高: {symbol}, 风险等级: {risk_level.value}")
        recommendation = "建议: 降低交易频率或减少单笔交易金额"
        return True, [], recommendation
    elif risk_level == RiskLevel.CRITICAL:
        logger.error(f"风险等级极高: {symbol}, 风险等级: {risk_level.value}")
        recommendation = "建议: 立即停止交易"
        return False, [f"风险等级极高: {risk_level.value}"], recommendation
    else:
        return True, [], "可以继续交易"


async def post_trade_update(
    risk_manager: RiskManager,
    pnl: float,
    amount: float,
    price: float,
    side: str,
    symbol: str
) -> Dict:
    """
    交易后更新风险管理器

    Args:
        risk_manager: 风险管理器实例
        pnl: 交易盈亏
        amount: 交易数量
        price: 交易价格
        side: 交易方向 (buy/sell)
        symbol: 交易对

    Returns:
        更新后的风险报告
    """
    # 更新持仓
    if side == "buy":
        risk_manager.update_position(amount, price)
    else:
        risk_manager.update_position(-amount, price)

    # 更新盈亏
    risk_manager.update_pnl(pnl)

    # 记录交易
    risk_manager.record_trade({
        'symbol': symbol,
        'side': side,
        'price': price,
        'amount': amount,
        'pnl': pnl
    })

    logger.info(
        f"交易完成: {symbol} {side} {amount} @ {price}, "
        f"PnL: {pnl:.2f}, "
        f"持仓: {risk_manager.current_position:.2f}, "
        f"日盈亏: {risk_manager.daily_pnl:.2f}"
    )

    return risk_manager.get_risk_report()


def check_position_risk(
    risk_manager: RiskManager,
    current_price: float,
    entry_price: float,
    amount: float,
    symbol: str
) -> Tuple[bool, str, float]:
    """
    检查持仓风险（止损/止盈）

    Args:
        risk_manager: 风险管理器实例
        current_price: 当前价格
        entry_price: 入场价格
        amount: 持仓数量
        symbol: 交易对

    Returns:
        (是否触发操作, 操作类型, 触发百分比)
    """
    # 检查是否启用自动止损
    if not risk_manager.enable_auto_stop:
        return False, "", 0.0

    # 检查止损
    if risk_manager.should_trigger_stop_loss(current_price, entry_price):
        loss_percent = (entry_price - current_price) / entry_price
        logger.warning(
            f"触发止损: {symbol}, "
            f"入场价: {entry_price}, "
            f"当前价: {current_price}, "
            f"亏损: {loss_percent:.2%}"
        )
        return True, "stop_loss", loss_percent

    # 检查止盈
    if risk_manager.should_trigger_take_profit(current_price, entry_price):
        profit_percent = (current_price - entry_price) / entry_price
        logger.info(
            f"触发止盈: {symbol}, "
            f"入场价: {entry_price}, "
            f"当前价: {current_price}, "
            f"盈利: {profit_percent:.2%}"
        )
        return True, "take_profit", profit_percent

    return False, "", 0.0


def calculate_safe_position_size(
    risk_manager: RiskManager,
    account_balance: float,
    entry_price: float,
    stop_loss_price: float,
    max_risk_percent: float = 0.02
) -> float:
    """
    计算安全的仓位大小

    Args:
        risk_manager: 风险管理器实例
        account_balance: 账户余额
        entry_price: 入场价
        stop_loss_price: 止损价
        max_risk_percent: 最大风险百分比

    Returns:
        建议的仓位大小
    """
    from app.risk_management import calculate_position_size

    # 基础仓位计算
    position_size = calculate_position_size(
        account_balance=account_balance,
        risk_percent=max_risk_percent,
        entry_price=entry_price,
        stop_loss_price=stop_loss_price
    )

    # 检查持仓限制
    position_value = position_size * entry_price
    passed, _ = risk_manager.check_position_limit(position_value)

    if not passed:
        # 如果超出持仓限制，计算最大允许仓位
        max_available = risk_manager.max_position - risk_manager.current_position
        if max_available > 0:
            position_size = min(position_size, max_available / entry_price)
        else:
            position_size = 0
            logger.warning("已达到最大持仓限制，无法开仓")

    # 检查单笔订单限制
    if position_value > risk_manager.max_single_order:
        position_size = risk_manager.max_single_order / entry_price
        logger.info(f"订单金额超出限制，已调整为 {position_size}")

    return position_size


def get_risk_alert(
    risk_manager: RiskManager,
    symbol: str = "N/A"
) -> Optional[Dict]:
    """
    获取风险警报

    Args:
        risk_manager: 风险管理器实例
        symbol: 交易对

    Returns:
        风险警报字典（无警报时返回None）
    """
    risk_report = risk_manager.get_risk_report()

    # 检查单日亏损
    if risk_report['daily_pnl'] < -risk_manager.max_daily_loss * 0.8:
        return {
            'type': 'warning',
            'message': f'单日亏损接近限制 ({risk_report["daily_pnl"]:.2f} / -{risk_manager.max_daily_loss})',
            'severity': 'high',
            'symbol': symbol
        }

    # 检查总亏损
    if risk_report['total_pnl'] < -risk_manager.max_total_loss * 0.8:
        return {
            'type': 'warning',
            'message': f'总亏损接近限制 ({risk_report["total_pnl"]:.2f} / -{risk_manager.max_total_loss})',
            'severity': 'critical',
            'symbol': symbol
        }

    # 检查持仓使用率
    position_usage = risk_report['position_usage_ratio']
    if position_usage > 0.9:
        return {
            'type': 'warning',
            'message': f'持仓使用率过高 ({position_usage:.1%})',
            'severity': 'medium',
            'symbol': symbol
        }

    # 检查订单数
    if risk_report['order_count'] >= risk_manager.max_orders * 0.9:
        return {
            'type': 'warning',
            'message': f'订单数接近限制 ({risk_report["order_count"]} / {risk_manager.max_orders})',
            'severity': 'medium',
            'symbol': symbol
        }

    return None
