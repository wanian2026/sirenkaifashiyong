"""
风险预警模块
实现5类风险预警：阈值、趋势、波动率、回撤、组合
"""
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from collections import deque
import statistics


class RiskAlertConfig(BaseModel):
    """风险预警配置"""
    alert_type: str = Field(..., description="预警类型: threshold, trend, volatility, drawdown, portfolio")
    
    # 账户信息
    account_balance: float = Field(..., description="当前账户余额")
    initial_balance: Optional[float] = Field(None, description="初始账户余额")
    
    # 市场信息
    current_price: Optional[float] = Field(None, description="当前价格")
    prices_history: Optional[List[float]] = Field(None, description="价格历史")
    
    # 持仓信息
    total_position_value: Optional[float] = Field(None, description="总持仓价值")
    positions: Optional[List[Dict]] = Field(None, description="持仓列表")
    
    # PnL信息
    unrealized_pnl: Optional[float] = Field(None, description="未实现盈亏")
    realized_pnl: Optional[float] = Field(None, description="已实现盈亏")
    
    # 阈值预警参数
    balance_threshold: Optional[float] = Field(None, description="账户余额阈值")
    pnl_threshold: Optional[float] = Field(None, description="盈亏阈值")
    position_threshold: Optional[float] = Field(None, description="持仓阈值")
    
    # 趋势预警参数
    trend_period: Optional[int] = Field(20, description="趋势周期")
    trend_threshold: Optional[float] = Field(0.05, description="趋势变化阈值")
    
    # 波动率预警参数
    volatility_period: Optional[int] = Field(20, description="波动率周期")
    volatility_threshold: Optional[float] = Field(0.05, description="波动率阈值")
    
    # 回撤预警参数
    drawdown_threshold: Optional[float] = Field(0.10, description="回撤阈值")
    peak_balance: Optional[float] = Field(None, description="峰值余额")
    
    # 组合预警参数
    concentration_threshold: Optional[float] = Field(0.5, description="集中度阈值")
    correlation_threshold: Optional[float] = Field(0.8, description="相关性阈值")
    
    # 通用参数
    cooling_period: Optional[int] = Field(300, description="冷却时间（秒）")
    last_alert_time: Optional[datetime] = Field(None, description="上次预警时间")


class RiskAlertStrategy(ABC):
    """风险预警策略抽象基类"""
    
    def __init__(self, config: RiskAlertConfig):
        self.config = config
        self.alert_history = deque(maxlen=100)
    
    @abstractmethod
    def check_alert(self) -> tuple[bool, str, Dict]:
        """检查是否应该触发预警 (is_alert, message, details)"""
        pass
    
    def is_in_cooling_period(self) -> bool:
        """检查是否在冷却期内"""
        if not self.config.last_alert_time:
            return False
        
        now = datetime.now()
        elapsed = (now - self.config.last_alert_time).total_seconds()
        
        return elapsed < self.config.cooling_period
    
    def record_alert(self, message: str, details: Dict):
        """记录预警"""
        alert = {
            "timestamp": datetime.now(),
            "message": message,
            "details": details
        }
        self.alert_history.append(alert)
        self.config.last_alert_time = datetime.now()
    
    def get_alert_history(self, limit: int = 10) -> List[Dict]:
        """获取预警历史"""
        return list(self.alert_history)[-limit:]


class ThresholdAlert(RiskAlertStrategy):
    """阈值预警"""
    
    def check_alert(self) -> tuple[bool, str, Dict]:
        """检查阈值预警"""
        alerts = []
        details = {}
        
        # 检查余额阈值
        if self.config.balance_threshold:
            if self.config.account_balance <= self.config.balance_threshold:
                alerts.append(f"账户余额低于阈值: {self.config.account_balance:.2f} <= {self.config.balance_threshold:.2f}")
                details["balance_alert"] = {
                    "current_balance": self.config.account_balance,
                    "threshold": self.config.balance_threshold,
                    "diff": self.config.account_balance - self.config.balance_threshold
                }
        
        # 检查盈亏阈值
        if self.config.pnl_threshold is not None:
            pnl = self.config.unrealized_pnl or self.config.realized_pnl or 0
            if abs(pnl) >= abs(self.config.pnl_threshold):
                alert_type = "盈利" if pnl > 0 else "亏损"
                alerts.append(f"{alert_type}超过阈值: {pnl:.2f} >= {self.config.pnl_threshold:.2f}")
                details["pnl_alert"] = {
                    "pnl": pnl,
                    "threshold": self.config.pnl_threshold,
                    "type": alert_type
                }
        
        # 检查持仓阈值
        if self.config.position_threshold and self.config.total_position_value:
            if self.config.total_position_value >= self.config.position_threshold:
                alerts.append(f"持仓价值超过阈值: {self.config.total_position_value:.2f} >= {self.config.position_threshold:.2f}")
                details["position_alert"] = {
                    "total_position": self.config.total_position_value,
                    "threshold": self.config.position_threshold,
                    "ratio": self.config.total_position_value / self.config.account_balance
                }
        
        if alerts:
            message = "; ".join(alerts)
            self.record_alert(message, details)
            return True, message, details
        
        return False, "", {}


class TrendAlert(RiskAlertStrategy):
    """趋势预警"""
    
    def check_alert(self) -> tuple[bool, str, Dict]:
        """检查趋势预警"""
        if not self.config.prices_history or len(self.config.prices_history) < self.config.trend_period:
            return False, "", {}
        
        prices = self.config.prices_history[-self.config.trend_period:]
        
        # 计算趋势（简单线性回归）
        n = len(prices)
        x = list(range(n))
        
        # 计算斜率
        x_mean = sum(x) / n
        y_mean = sum(prices) / n
        
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, prices))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        
        if denominator == 0:
            return False, "", {}
        
        slope = numerator / denominator
        
        # 计算趋势变化
        current_price = self.config.current_price or prices[-1]
        price_change = (current_price - prices[0]) / prices[0] if prices[0] != 0 else 0
        
        alerts = []
        details = {
            "slope": slope,
            "price_change": price_change,
            "current_price": current_price,
            "start_price": prices[0]
        }
        
        # 检查趋势变化
        threshold = self.config.trend_threshold or 0.05
        if abs(price_change) >= threshold:
            trend_type = "上涨" if price_change > 0 else "下跌"
            alerts.append(f"价格{trend_type}超过阈值: {abs(price_change)*100:.2f}% >= {threshold*100:.2f}%")
        
        # 检查斜率变化（加速或减速）
        if abs(slope) > threshold * 10:  # 斜率阈值需要调整
            slope_type = "加速上涨" if slope > 0 else "加速下跌"
            alerts.append(f"价格{slope_type}: 斜率={slope:.4f}")
        
        if alerts:
            message = "; ".join(alerts)
            self.record_alert(message, details)
            return True, message, details
        
        return False, "", {}


class VolatilityAlert(RiskAlertStrategy):
    """波动率预警"""
    
    def check_alert(self) -> tuple[bool, str, Dict]:
        """检查波动率预警"""
        if not self.config.prices_history or len(self.config.prices_history) < 2:
            return False, "", {}
        
        period = min(self.config.volatility_period or 20, len(self.config.prices_history))
        prices = self.config.prices_history[-period:]
        
        # 计算收益率
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
        
        if len(returns) < 2:
            return False, "", {}
        
        # 计算波动率（标准差）
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        
        alerts = []
        details = {
            "volatility": volatility,
            "threshold": self.config.volatility_threshold or 0.05,
            "period": period
        }
        
        # 检查波动率阈值
        threshold = self.config.volatility_threshold or 0.05
        if volatility >= threshold:
            alerts.append(f"波动率超过阈值: {volatility*100:.2f}% >= {threshold*100:.2f}%")
        
        # 检查异常波动（超过3倍标准差）
        if len(returns) > 0:
            last_return = returns[-1]
            if abs(last_return) > 3 * volatility:
                alerts.append(f"检测到异常波动: 收益率{last_return*100:.2f}% (3倍标准差: {3*volatility*100:.2f}%)")
                details["anomaly"] = {
                    "last_return": last_return,
                    "threshold": 3 * volatility
                }
        
        if alerts:
            message = "; ".join(alerts)
            self.record_alert(message, details)
            return True, message, details
        
        return False, "", {}


class DrawdownAlert(RiskAlertStrategy):
    """回撤预警"""
    
    def check_alert(self) -> tuple[bool, str, Dict]:
        """检查回撤预警"""
        # 使用峰值余额
        peak = self.config.peak_balance or self.config.account_balance
        current = self.config.account_balance
        
        # 计算回撤
        drawdown = (peak - current) / peak if peak != 0 else 0
        
        alerts = []
        details = {
            "peak_balance": peak,
            "current_balance": current,
            "drawdown": drawdown
        }
        
        # 检查回撤阈值
        threshold = self.config.drawdown_threshold or 0.10
        if drawdown >= threshold:
            alerts.append(f"回撤超过阈值: {drawdown*100:.2f}% >= {threshold*100:.2f}%")
        
        # 检查严重回撤（超过20%）
        if drawdown >= 0.20:
            alerts.append("严重回撤警告: 回撤超过20%")
        
        # 更新峰值
        if current > peak:
            self.config.peak_balance = current
        
        if alerts:
            message = "; ".join(alerts)
            self.record_alert(message, details)
            return True, message, details
        
        return False, "", {}


class PortfolioAlert(RiskAlertStrategy):
    """组合预警"""
    
    def check_alert(self) -> tuple[bool, str, Dict]:
        """检查组合预警"""
        if not self.config.positions:
            return False, "", {}
        
        alerts = []
        details = {
            "total_positions": len(self.config.positions),
            "positions": []
        }
        
        total_value = sum(pos.get("value", 0) for pos in self.config.positions)
        if total_value == 0:
            return False, "", {}
        
        # 检查集中度
        threshold = self.config.concentration_threshold or 0.5
        for pos in self.config.positions:
            pos_value = pos.get("value", 0)
            weight = pos_value / total_value
            
            pos_details = {
                "symbol": pos.get("symbol", "unknown"),
                "value": pos_value,
                "weight": weight
            }
            details["positions"].append(pos_details)
            
            if weight >= threshold:
                alerts.append(f"持仓集中度过高: {pos.get('symbol', 'unknown')} 占比 {weight*100:.2f}% >= {threshold*100:.2f}%")
                pos_details["alert"] = True
        
        # 检查持仓数量
        if len(self.config.positions) > 20:
            alerts.append(f"持仓数量过多: {len(self.config.positions)} 个")
            details["alert"] = "too_many_positions"
        
        # 检查总持仓价值占比
        if self.config.total_position_value:
            position_ratio = self.config.total_position_value / self.config.account_balance
            if position_ratio >= 0.9:
                alerts.append(f"仓位过高: 持仓占比 {position_ratio*100:.2f}% >= 90%")
                details["position_ratio"] = position_ratio
        
        if alerts:
            message = "; ".join(alerts)
            self.record_alert(message, details)
            return True, message, details
        
        return False, "", {}


class RiskAlertStrategyFactory:
    """风险预警策略工厂"""
    
    @staticmethod
    def create_strategy(config: RiskAlertConfig) -> RiskAlertStrategy:
        """创建风险预警策略"""
        strategy_map = {
            "threshold": ThresholdAlert,
            "trend": TrendAlert,
            "volatility": VolatilityAlert,
            "drawdown": DrawdownAlert,
            "portfolio": PortfolioAlert,
        }
        
        strategy_class = strategy_map.get(config.alert_type)
        if not strategy_class:
            raise ValueError(f"不支持的风险预警类型: {config.alert_type}")
        
        return strategy_class(config)
    
    @staticmethod
    def get_available_strategies() -> list[str]:
        """获取可用的风险预警策略列表"""
        return ["threshold", "trend", "volatility", "drawdown", "portfolio"]


# 风险预警管理器
class RiskAlertManager:
    """风险预警管理器"""
    
    def __init__(self):
        self.strategies: Dict[str, RiskAlertStrategy] = {}
    
    def add_strategy(self, name: str, strategy: RiskAlertStrategy):
        """添加预警策略"""
        self.strategies[name] = strategy
    
    def remove_strategy(self, name: str):
        """移除预警策略"""
        if name in self.strategies:
            del self.strategies[name]
    
    def check_all_alerts(self) -> List[Dict]:
        """检查所有预警"""
        results = []
        
        for name, strategy in self.strategies.items():
            # 检查冷却期
            if strategy.is_in_cooling_period():
                continue
            
            # 检查预警
            is_alert, message, details = strategy.check_alert()
            
            if is_alert:
                results.append({
                    "name": name,
                    "message": message,
                    "details": details,
                    "timestamp": datetime.now()
                })
        
        return results
    
    def get_all_alert_history(self) -> Dict[str, List[Dict]]:
        """获取所有预警历史"""
        history = {}
        for name, strategy in self.strategies.items():
            history[name] = strategy.get_alert_history()
        return history


# 使用示例
if __name__ == "__main__":
    # 阈值预警示例
    threshold_config = RiskAlertConfig(
        alert_type="threshold",
        account_balance=9500.0,
        balance_threshold=10000.0,
        unrealized_pnl=-600.0,
        pnl_threshold=-500.0
    )
    threshold_strategy = RiskAlertStrategyFactory.create_strategy(threshold_config)
    is_alert, message, details = threshold_strategy.check_alert()
    print(f"阈值预警: {is_alert}, {message}")
    
    # 波动率预警示例
    volatility_config = RiskAlertConfig(
        alert_type="volatility",
        account_balance=10000.0,
        prices_history=[100, 102, 105, 103, 110, 108, 112, 115, 113, 118]
    )
    volatility_strategy = RiskAlertStrategyFactory.create_strategy(volatility_config)
    is_alert, message, details = volatility_strategy.check_alert()
    print(f"波动率预警: {is_alert}, {message}")
    
    # 回撤预警示例
    drawdown_config = RiskAlertConfig(
        alert_type="drawdown",
        account_balance=9000.0,
        peak_balance=10000.0,
        drawdown_threshold=0.05
    )
    drawdown_strategy = RiskAlertStrategyFactory.create_strategy(drawdown_config)
    is_alert, message, details = drawdown_strategy.check_alert()
    print(f"回撤预警: {is_alert}, {message}")
