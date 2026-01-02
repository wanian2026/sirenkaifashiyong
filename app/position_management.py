"""
仓位管理模块
实现5种仓位管理方法：Kelly公式、固定比例、ATR基于、风险平价、波动率基于
"""
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
import math


class PositionConfig(BaseModel):
    """仓位配置"""
    strategy_type: str = Field(..., description="仓位策略类型: kelly, fixed_ratio, atr_based, risk_parity, volatility")
    
    # 账户信息
    account_balance: float = Field(..., description="账户余额")
    total_capital: Optional[float] = Field(None, description="总资金（包括未使用资金）")
    
    # 市场信息
    entry_price: float = Field(..., description="入场价格")
    stop_loss_price: Optional[float] = Field(None, description="止损价格")
    atr: Optional[float] = Field(None, description="平均真实波幅")
    volatility: Optional[float] = Field(None, description="波动率")
    
    # 策略特定参数
    # Kelly公式参数
    win_rate: Optional[float] = Field(None, description="胜率 (0-1)")
    avg_win: Optional[float] = Field(None, description="平均盈利")
    avg_loss: Optional[float] = Field(None, description="平均亏损")
    kelly_fraction: Optional[float] = Field(0.25, description="Kelly分数（用于降低风险）")
    
    # 固定比例参数
    fixed_percent: Optional[float] = Field(0.02, description="固定百分比")
    
    # ATR基于参数
    atr_multiplier: Optional[float] = Field(1.0, description="ATR倍数")
    risk_per_trade: Optional[float] = Field(0.02, description="每笔交易风险比例")
    
    # 风险平价参数
    risk_target: Optional[float] = Field(0.02, description="目标风险")
    
    # 波动率基于参数
    volatility_target: Optional[float] = Field(0.15, description="目标波动率")
    position_multiplier: Optional[float] = Field(1.0, description="仓位倍数")
    
    # 通用限制
    max_position_size: Optional[float] = Field(None, description="最大仓位大小")
    min_position_size: Optional[float] = Field(None, description="最小仓位大小")
    max_position_percent: Optional[float] = Field(0.3, description="最大仓位百分比")


class PositionManagementStrategy(ABC):
    """仓位管理策略抽象基类"""
    
    def __init__(self, config: PositionConfig):
        self.config = config
    
    @abstractmethod
    def calculate_position_size(self) -> float:
        """计算仓位大小"""
        pass
    
    def apply_limits(self, position_size: float) -> float:
        """应用仓位限制"""
        max_size = self.config.max_position_size if self.config.max_position_size else float('inf')
        min_size = self.config.min_position_size if self.config.min_position_size else 0.0
        
        # 基于最大百分比限制
        if self.config.max_position_percent:
            max_by_percent = (self.config.total_capital or self.config.account_balance) * self.config.max_position_percent / self.config.entry_price
            max_size = min(max_size, max_by_percent)
        
        # 应用限制
        position_size = max(min_size, min(max_size, position_size))
        
        return position_size
    
    def get_position_value(self, position_size: float) -> float:
        """获取仓位价值"""
        return position_size * self.config.entry_price


class KellyCriterion(PositionManagementStrategy):
    """Kelly公式仓位管理"""
    
    def calculate_position_size(self) -> float:
        """使用Kelly公式计算最优仓位"""
        if not all([self.config.win_rate, self.config.avg_win, self.config.avg_loss]):
            # 如果没有历史数据，使用保守的固定比例
            base_size = self.config.account_balance * (self.config.fixed_percent or 0.02)
            position_size = base_size / self.config.entry_price
        else:
            # Kelly公式: f* = (bp - q) / b
            # b = avg_win / avg_loss (盈亏比)
            # p = win_rate (胜率)
            # q = 1 - p (败率)
            
            b = self.config.avg_win / abs(self.config.avg_loss) if self.config.avg_loss != 0 else 1
            p = self.config.win_rate
            q = 1 - p
            
            # 计算Kelly比例
            kelly_fraction = (b * p - q) / b
            
            # 应用Kelly分数降低风险
            kelly_fraction *= self.config.kelly_fraction or 0.25
            
            # 确保不为负数
            kelly_fraction = max(0, kelly_fraction)
            
            # 计算仓位大小
            position_size = self.config.account_balance * kelly_fraction / self.config.entry_price
        
        # 应用限制
        return self.apply_limits(position_size)


class FixedRatioStrategy(PositionManagementStrategy):
    """固定比例仓位管理"""
    
    def calculate_position_size(self) -> float:
        """使用固定比例计算仓位"""
        percent = self.config.fixed_percent or 0.02
        capital = self.config.total_capital or self.config.account_balance
        
        base_size = capital * percent
        position_size = base_size / self.config.entry_price
        
        # 应用限制
        return self.apply_limits(position_size)


class ATRBasedSizing(PositionManagementStrategy):
    """基于ATR的仓位管理"""
    
    def calculate_position_size(self) -> float:
        """使用ATR计算仓位大小"""
        if not self.config.atr:
            # 如果没有ATR，回退到固定比例
            base_size = self.config.account_balance * (self.config.risk_per_trade or 0.02)
            position_size = base_size / self.config.entry_price
        else:
            # 风险金额 = 账户余额 * 风险比例
            risk_amount = self.config.account_balance * (self.config.risk_per_trade or 0.02)
            
            # 风险单位数 = ATR * 倍数
            risk_per_unit = self.config.atr * (self.config.atr_multiplier or 1.0)
            
            # 仓位大小 = 风险金额 / 风险单位数
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit
            else:
                position_size = 0
        
        # 应用限制
        return self.apply_limits(position_size)


class RiskParityStrategy(PositionManagementStrategy):
    """风险平价仓位管理"""
    
    def calculate_position_size(self) -> float:
        """使用风险平价计算仓位大小"""
        if not self.config.stop_loss_price:
            # 如果没有止损价格，使用固定比例
            return FixedRatioStrategy(self.config).calculate_position_size()
        
        # 计算每单位的风险
        risk_per_unit = abs(self.config.entry_price - self.config.stop_loss_price)
        
        if risk_per_unit == 0:
            return 0
        
        # 目标风险金额 = 账户余额 * 目标风险比例
        target_risk = self.config.account_balance * (self.config.risk_target or 0.02)
        
        # 仓位大小 = 目标风险金额 / 每单位风险
        position_size = target_risk / risk_per_unit
        
        # 应用限制
        return self.apply_limits(position_size)


class VolatilityBasedSizing(PositionManagementStrategy):
    """基于波动率的仓位管理"""
    
    def calculate_position_size(self) -> float:
        """使用波动率计算仓位大小"""
        if not self.config.volatility or self.config.volatility == 0:
            # 如果没有波动率，使用固定比例
            return FixedRatioStrategy(self.config).calculate_position_size()
        
        # 目标波动率
        target_vol = self.config.volatility_target or 0.15
        
        # 当前波动率
        current_vol = self.config.volatility
        
        # 基础仓位比例
        base_percent = target_vol / current_vol
        
        # 应用仓位倍数
        base_percent *= self.config.position_multiplier or 1.0
        
        # 限制在合理范围内 (0-1)
        base_percent = max(0.01, min(1.0, base_percent))
        
        # 计算仓位大小
        capital = self.config.total_capital or self.config.account_balance
        position_size = capital * base_percent / self.config.entry_price
        
        # 应用限制
        return self.apply_limits(position_size)


class PositionManagementFactory:
    """仓位管理工厂"""
    
    @staticmethod
    def create_strategy(config: PositionConfig) -> PositionManagementStrategy:
        """创建仓位管理策略"""
        strategy_map = {
            "kelly": KellyCriterion,
            "fixed_ratio": FixedRatioStrategy,
            "atr_based": ATRBasedSizing,
            "risk_parity": RiskParityStrategy,
            "volatility": VolatilityBasedSizing,
        }
        
        strategy_class = strategy_map.get(config.strategy_type)
        if not strategy_class:
            raise ValueError(f"不支持的仓位管理策略类型: {config.strategy_type}")
        
        return strategy_class(config)
    
    @staticmethod
    def get_available_strategies() -> list[str]:
        """获取可用的仓位管理策略列表"""
        return ["kelly", "fixed_ratio", "atr_based", "risk_parity", "volatility"]


# 使用示例
if __name__ == "__main__":
    # Kelly公式示例
    kelly_config = PositionConfig(
        strategy_type="kelly",
        account_balance=10000.0,
        entry_price=100.0,
        win_rate=0.55,
        avg_win=200.0,
        avg_loss=150.0,
        kelly_fraction=0.25
    )
    kelly_strategy = PositionManagementFactory.create_strategy(kelly_config)
    print(f"Kelly公式仓位大小: {kelly_strategy.calculate_position_size():.4f}")
    
    # 固定比例示例
    fixed_config = PositionConfig(
        strategy_type="fixed_ratio",
        account_balance=10000.0,
        entry_price=100.0,
        fixed_percent=0.02
    )
    fixed_strategy = PositionManagementFactory.create_strategy(fixed_config)
    print(f"固定比例仓位大小: {fixed_strategy.calculate_position_size():.4f}")
    
    # ATR基于示例
    atr_config = PositionConfig(
        strategy_type="atr_based",
        account_balance=10000.0,
        entry_price=100.0,
        atr=5.0,
        atr_multiplier=1.0,
        risk_per_trade=0.02
    )
    atr_strategy = PositionManagementFactory.create_strategy(atr_config)
    print(f"ATR基于仓位大小: {atr_strategy.calculate_position_size():.4f}")
    
    # 风险平价示例
    risk_parity_config = PositionConfig(
        strategy_type="risk_parity",
        account_balance=10000.0,
        entry_price=100.0,
        stop_loss_price=95.0,
        risk_target=0.02
    )
    risk_parity_strategy = PositionManagementFactory.create_strategy(risk_parity_config)
    print(f"风险平价仓位大小: {risk_parity_strategy.calculate_position_size():.4f}")
    
    # 波动率基于示例
    volatility_config = PositionConfig(
        strategy_type="volatility",
        account_balance=10000.0,
        entry_price=100.0,
        volatility=0.2,
        volatility_target=0.15,
        position_multiplier=1.0
    )
    volatility_strategy = PositionManagementFactory.create_strategy(volatility_config)
    print(f"波动率基于仓位大小: {volatility_strategy.calculate_position_size():.4f}")
