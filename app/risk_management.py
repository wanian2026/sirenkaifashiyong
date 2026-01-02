"""
风险管理模块
提供资金限制、止损机制、风险等级评估等功能
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLimitType(Enum):
    """风险限制类型"""
    MAX_POSITION = "max_position"  # 最大持仓
    MAX_DAILY_LOSS = "max_daily_loss"  # 单日最大亏损
    MAX_TOTAL_LOSS = "max_total_loss"  # 总最大亏损
    MAX_ORDERS = "max_orders"  # 最大订单数
    MAX_SINGLE_ORDER = "max_single_order"  # 单笔订单最大金额


class RiskManager:
    """风险管理器"""

    def __init__(
        self,
        max_position: float = 10000,  # 最大持仓金额
        max_daily_loss: float = 1000,  # 单日最大亏损
        max_total_loss: float = 5000,  # 总最大亏损
        max_orders: int = 50,  # 最大订单数
        max_single_order: float = 1000,  # 单笔订单最大金额
        stop_loss_threshold: float = 0.05,  # 止损阈值（5%）
        take_profit_threshold: float = 0.10,  # 止盈阈值（10%）
        enable_auto_stop: bool = True,  # 是否启用自动止损
        max_consecutive_losses: int = 5,  # 最大连续亏损次数
        volatility_threshold: float = 0.05,  # 波动率阈值（5%）
        enable_volatility_protection: bool = True,  # 是否启用波动率保护
        enable_emergency_stop: bool = True  # 是否启用紧急停止
    ):
        self.max_position = max_position
        self.max_daily_loss = max_daily_loss
        self.max_total_loss = max_total_loss
        self.max_orders = max_orders
        self.max_single_order = max_single_order
        self.stop_loss_threshold = stop_loss_threshold
        self.take_profit_threshold = take_profit_threshold
        self.enable_auto_stop = enable_auto_stop
        self.max_consecutive_losses = max_consecutive_losses
        self.volatility_threshold = volatility_threshold
        self.enable_volatility_protection = enable_volatility_protection
        self.enable_emergency_stop = enable_emergency_stop

        # 运行时状态
        self.current_position = 0
        self.daily_pnl = 0
        self.total_pnl = 0
        self.order_count = 0
        self.daily_trades = []
        self.last_reset_date = datetime.now().date()

        # 连续亏损跟踪
        self.consecutive_losses = 0
        self.consecutive_wins = 0

        # 波动率跟踪
        self.price_history: List[Dict] = []  # 价格历史记录

        # 紧急停止状态
        self.emergency_stop_triggered = False
        self.emergency_stop_reason = ""

        # 异常行情检测
        self.last_price = None
        self.price_change_threshold = 0.10  # 价格变化10%视为异常

    def reset_daily_limits(self):
        """重置每日限制"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_pnl = 0
            self.daily_trades = []
            self.order_count = 0
            self.last_reset_date = today
            # 不重置连续亏损次数，跨日也需要跟踪
            logger.info("每日风险限制已重置")

    def check_consecutive_losses(self) -> tuple[bool, str]:
        """检查连续亏损限制"""
        if self.consecutive_losses >= self.max_consecutive_losses:
            return False, f"连续亏损次数过多: {self.consecutive_losses} >= {self.max_consecutive_losses}，建议暂停交易"
        return True, "通过"

    def check_position_limit(self, position_value: float) -> tuple[bool, str]:
        """检查持仓限制"""
        new_position = self.current_position + position_value

        if new_position > self.max_position:
            return False, f"超出最大持仓限制: {new_position} > {self.max_position}"

        return True, "通过"

    def check_daily_loss_limit(self) -> tuple[bool, str]:
        """检查单日亏损限制"""
        self.reset_daily_limits()

        if self.daily_pnl < -self.max_daily_loss:
            return False, f"超出单日最大亏损限制: {self.daily_pnl} < -{self.max_daily_loss}"

        return True, "通过"

    def check_total_loss_limit(self) -> tuple[bool, str]:
        """检查总亏损限制"""
        if self.total_pnl < -self.max_total_loss:
            return False, f"超出总最大亏损限制: {self.total_pnl} < -{self.max_total_loss}"

        return True, "通过"

    def check_order_limit(self) -> tuple[bool, str]:
        """检查订单数限制"""
        self.reset_daily_limits()

        if self.order_count >= self.max_orders:
            return False, f"超出最大订单数限制: {self.order_count} >= {self.max_orders}"

        return True, "通过"

    def check_single_order_limit(self, order_value: float) -> tuple[bool, str]:
        """检查单笔订单限制"""
        if order_value > self.max_single_order:
            return False, f"超出单笔订单最大金额: {order_value} > {self.max_single_order}"

        return True, "通过"

    def check_all_limits(
        self,
        position_value: float = 0,
        order_value: float = 0
    ) -> tuple[bool, List[str]]:
        """检查所有限制"""
        errors = []

        # 检查紧急停止状态
        if self.emergency_stop_triggered:
            errors.append(f"紧急停止已触发: {self.emergency_stop_reason}，禁止新交易")
            return False, errors

        # 检查持仓限制
        passed, msg = self.check_position_limit(position_value)
        if not passed:
            errors.append(msg)

        # 检查单日亏损限制
        passed, msg = self.check_daily_loss_limit()
        if not passed:
            errors.append(msg)

        # 检查总亏损限制
        passed, msg = self.check_total_loss_limit()
        if not passed:
            errors.append(msg)

        # 检查订单数限制
        passed, msg = self.check_order_limit()
        if not passed:
            errors.append(msg)

        # 检查单笔订单限制
        passed, msg = self.check_single_order_limit(order_value)
        if not passed:
            errors.append(msg)

        # 检查连续亏损限制
        passed, msg = self.check_consecutive_losses()
        if not passed:
            errors.append(msg)

        return len(errors) == 0, errors

    def should_trigger_stop_loss(self, current_price: float, entry_price: float) -> bool:
        """是否触发止损"""
        loss_percent = (entry_price - current_price) / entry_price
        return loss_percent >= self.stop_loss_threshold

    def should_trigger_take_profit(self, current_price: float, entry_price: float) -> bool:
        """是否触发止盈"""
        profit_percent = (current_price - entry_price) / entry_price
        return profit_percent >= self.take_profit_threshold

    def evaluate_risk_level(
        self,
        position_value: float,
        unrealized_pnl: float,
        volatility: float = 0
    ) -> RiskLevel:
        """评估风险等级"""
        risk_score = 0

        # 仓位风险评分（0-30分）
        position_ratio = position_value / self.max_position if self.max_position > 0 else 0
        risk_score += position_ratio * 30

        # 亏损风险评分（0-40分）
        loss_ratio = abs(unrealized_pnl) / self.max_daily_loss if self.max_daily_loss > 0 else 0
        risk_score += min(loss_ratio, 1) * 40

        # 波动率风险评分（0-30分）
        volatility_score = min(volatility / 0.1, 1) * 30  # 10%波动率为满分
        risk_score += volatility_score

        # 根据总分确定风险等级
        if risk_score < 30:
            return RiskLevel.LOW
        elif risk_score < 60:
            return RiskLevel.MEDIUM
        elif risk_score < 85:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def update_position(self, amount: float, price: float):
        """更新持仓"""
        value = amount * price
        self.current_position += value
        logger.info(f"持仓更新: {self.current_position:.2f} (增加 {value:.2f})")

    def update_pnl(self, pnl: float):
        """更新盈亏并跟踪连续亏损"""
        self.daily_pnl += pnl
        self.total_pnl += pnl

        # 更新连续亏损/盈利计数
        if pnl > 0:
            self.consecutive_losses = 0
            self.consecutive_wins += 1
        elif pnl < 0:
            self.consecutive_wins = 0
            self.consecutive_losses += 1

        logger.info(f"盈亏更新: 日={self.daily_pnl:.2f}, 总={self.total_pnl:.2f}, 连续亏损={self.consecutive_losses}")

    def record_trade(self, trade: Dict):
        """记录交易"""
        self.daily_trades.append({
            'timestamp': datetime.now().isoformat(),
            'side': trade.get('side'),
            'price': trade.get('price'),
            'amount': trade.get('amount'),
            'pnl': trade.get('pnl', 0)
        })
        self.order_count += 1

    # ==================== 新增：波动率保护机制 ====================

    def calculate_volatility(self, symbol: str, prices: List[float], period: int = 20) -> float:
        """
        计算波动率（标准差/平均价）

        Args:
            symbol: 交易对
            prices: 价格列表
            period: 计算周期

        Returns:
            波动率（小数，如0.05表示5%）
        """
        if len(prices) < 2:
            return 0.0

        import statistics

        try:
            # 计算标准差
            std_dev = statistics.stdev(prices[-period:])
            # 计算平均价
            avg_price = statistics.mean(prices[-period:])
            # 波动率 = 标准差 / 平均价
            volatility = std_dev / avg_price if avg_price > 0 else 0.0
            return volatility
        except Exception as e:
            logger.warning(f"计算波动率失败: {e}")
            return 0.0

    def update_price_history(self, symbol: str, price: float, timestamp: datetime = None):
        """
        更新价格历史记录

        Args:
            symbol: 交易对
            price: 当前价格
            timestamp: 时间戳（默认为当前时间）
        """
        if timestamp is None:
            timestamp = datetime.now()

        self.price_history.append({
            'symbol': symbol,
            'price': price,
            'timestamp': timestamp.isoformat()
        })

        # 保留最近100条记录
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]

        self.last_price = price

    def check_volatility(self, symbol: str) -> tuple[bool, str, float]:
        """
        检查波动率是否过高

        Args:
            symbol: 交易对

        Returns:
            (是否通过, 消息, 当前波动率)
        """
        if not self.enable_volatility_protection:
            return True, "波动率保护未启用", 0.0

        # 获取该交易对的价格历史
        prices = [p['price'] for p in self.price_history if p['symbol'] == symbol]

        if len(prices) < 2:
            return True, "价格数据不足，无法计算波动率", 0.0

        volatility = self.calculate_volatility(symbol, prices)

        if volatility > self.volatility_threshold:
            return False, f"市场波动率过高: {volatility*100:.2f}% > {self.volatility_threshold*100:.2f}%，建议暂停交易", volatility

        return True, f"波动率正常: {volatility*100:.2f}%", volatility

    # ==================== 新增：异常行情检测 ====================

    def detect_abnormal_market(self, symbol: str, current_price: float, volume: float = None) -> Dict:
        """
        检测异常行情

        Args:
            symbol: 交易对
            current_price: 当前价格
            volume: 当前成交量（可选）

        Returns:
            检测结果字典
        """
        result = {
            'is_abnormal': False,
            'reason': '',
            'price_change_percent': 0.0,
            'recommendation': '正常交易'
        }

        if self.last_price is None:
            self.last_price = current_price
            return result

        # 计算价格变化百分比
        price_change = abs(current_price - self.last_price) / self.last_price
        result['price_change_percent'] = price_change * 100

        # 检测价格异常波动
        if price_change > self.price_change_threshold:
            result['is_abnormal'] = True
            result['reason'] = f"价格异常波动: {price_change*100:.2f}% > {self.price_change_threshold*100:.2f}%"
            result['recommendation'] = '暂停交易，等待市场稳定'

        # 检测价格暴跌（单次跌幅超过15%）
        price_drop = (self.last_price - current_price) / self.last_price
        if price_drop > 0.15:
            result['is_abnormal'] = True
            result['reason'] = f"价格暴跌: {price_drop*100:.2f}%"
            result['recommendation'] = '紧急停止交易，平仓避险'

        self.last_price = current_price
        return result

    # ==================== 新增：紧急停止机制 ====================

    def trigger_emergency_stop(self, reason: str = "用户手动触发"):
        """
        触发紧急停止

        Args:
            reason: 停止原因
        """
        self.emergency_stop_triggered = True
        self.emergency_stop_reason = reason
        logger.critical(f"紧急停止已触发! 原因: {reason}")

    def reset_emergency_stop(self):
        """重置紧急停止状态"""
        self.emergency_stop_triggered = False
        self.emergency_stop_reason = ""
        logger.info("紧急停止状态已重置")

    def check_emergency_stop(self) -> tuple[bool, str]:
        """
        检查是否处于紧急停止状态

        Returns:
            (是否可以交易, 原因)
        """
        if self.emergency_stop_triggered:
            return False, f"紧急停止已触发: {self.emergency_stop_reason}，禁止新交易"

        return True, "正常"

    def get_risk_report(self) -> Dict:
        """获取风险报告"""
        return {
            'timestamp': datetime.now().isoformat(),
            'current_position': self.current_position,
            'max_position': self.max_position,
            'position_usage_ratio': self.current_position / self.max_position if self.max_position > 0 else 0,
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'daily_loss_limit': self.max_daily_loss,
            'total_loss_limit': self.max_total_loss,
            'order_count': self.order_count,
            'max_orders': self.max_orders,
            'daily_trades': len(self.daily_trades),
            # 新增：连续亏损统计
            'consecutive_losses': self.consecutive_losses,
            'consecutive_wins': self.consecutive_wins,
            'max_consecutive_losses': self.max_consecutive_losses,
            # 新增：紧急停止状态
            'emergency_stop_triggered': self.emergency_stop_triggered,
            'emergency_stop_reason': self.emergency_stop_reason,
            # 新增：波动率保护
            'volatility_threshold': self.volatility_threshold,
            'enable_volatility_protection': self.enable_volatility_protection,
            'price_history_count': len(self.price_history),
            'limits_status': {
                'position': self.check_position_limit(0)[0],
                'daily_loss': self.check_daily_loss_limit()[0],
                'total_loss': self.check_total_loss_limit()[0],
                'orders': self.check_order_limit()[0],
                'consecutive_losses': self.check_consecutive_losses()[0],
                'emergency_stop': not self.emergency_stop_triggered
            }
        }


class PositionRiskManager:
    """持仓风险管理"""

    def __init__(self, stop_loss_percent: float = 0.05, take_profit_percent: float = 0.10):
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent
        self.positions: Dict[str, Dict] = {}  # {symbol: {entry_price, amount, stop_loss, take_profit}}

    def add_position(self, symbol: str, entry_price: float, amount: float):
        """添加持仓"""
        self.positions[symbol] = {
            'entry_price': entry_price,
            'amount': amount,
            'stop_loss': entry_price * (1 - self.stop_loss_percent),
            'take_profit': entry_price * (1 + self.take_profit_percent),
            'created_at': datetime.now()
        }
        logger.info(f"添加持仓: {symbol}, 入场价={entry_price}, 止损={self.positions[symbol]['stop_loss']}, 止盈={self.positions[symbol]['take_profit']}")

    def remove_position(self, symbol: str):
        """移除持仓"""
        if symbol in self.positions:
            del self.positions[symbol]
            logger.info(f"移除持仓: {symbol}")

    def check_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """检查持仓是否触发止损或止盈"""
        actions = []

        for symbol, position in self.positions.items():
            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]

            # 检查止损
            if current_price <= position['stop_loss']:
                actions.append({
                    'symbol': symbol,
                    'action': 'stop_loss',
                    'reason': f'价格触及止损位: {current_price} <= {position["stop_loss"]}',
                    'current_price': current_price,
                    'entry_price': position['entry_price'],
                    'loss_percent': (position['entry_price'] - current_price) / position['entry_price']
                })

            # 检查止盈
            elif current_price >= position['take_profit']:
                actions.append({
                    'symbol': symbol,
                    'action': 'take_profit',
                    'reason': f'价格触及止盈位: {current_price} >= {position["take_profit"]}',
                    'current_price': current_price,
                    'entry_price': position['entry_price'],
                    'profit_percent': (current_price - position['entry_price']) / position['entry_price']
                })

        return actions

    def get_position_info(self, symbol: str) -> Optional[Dict]:
        """获取持仓信息"""
        return self.positions.get(symbol)

    def get_all_positions(self) -> Dict:
        """获取所有持仓"""
        return self.positions.copy()


def calculate_position_size(
    account_balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss_price: float
) -> float:
    """
    根据风险计算仓位大小

    Args:
        account_balance: 账户余额
        risk_percent: 风险比例（如0.02表示2%）
        entry_price: 入场价
        stop_loss_price: 止损价

    Returns:
        建议的仓位大小
    """
    if entry_price <= 0 or stop_loss_price <= 0:
        return 0

    risk_amount = account_balance * risk_percent
    loss_per_unit = abs(entry_price - stop_loss_price)

    if loss_per_unit <= 0:
        return 0

    position_size = risk_amount / loss_per_unit
    position_value = position_size * entry_price

    # 限制最大仓位为账户余额的100%
    if position_value > account_balance:
        position_size = account_balance / entry_price

    return position_size


def calculate_risk_reward_ratio(
    entry_price: float,
    stop_loss_price: float,
    take_profit_price: float
) -> float:
    """
    计算风险收益比

    Args:
        entry_price: 入场价
        stop_loss_price: 止损价
        take_profit_price: 止盈价

    Returns:
        风险收益比（收益/风险）
    """
    if stop_loss_price <= 0 or entry_price <= 0:
        return 0

    risk = abs(entry_price - stop_loss_price)
    reward = abs(take_profit_price - entry_price)

    if risk == 0:
        return 0

    return reward / risk
