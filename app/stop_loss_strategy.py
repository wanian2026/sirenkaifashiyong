"""
止损策略模块
实现4种止损策略：固定、动态、追踪、阶梯
"""
from typing import Dict, Optional
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from datetime import datetime


class StopLossConfig(BaseModel):
    """止损配置"""
    strategy_type: str = Field(..., description="止损策略类型: fixed, dynamic, trailing, ladder")
    entry_price: float = Field(..., description="入场价格")
    position_size: float = Field(..., description="仓位大小")
    
    # 固定止损参数
    stop_loss_percent: Optional[float] = Field(None, description="止损百分比")
    
    # 动态止损参数
    atr_period: Optional[int] = Field(14, description="ATR周期")
    atr_multiplier: Optional[float] = Field(2.0, description="ATR倍数")
    
    # 追踪止损参数
    trailing_percent: Optional[float] = Field(None, description="追踪百分比")
    activation_profit: Optional[float] = Field(None, description="激活盈利百分比")
    
    # 阶梯止损参数
    ladder_steps: Optional[list] = Field(None, description="阶梯级别配置")
    
    # 通用参数
    max_loss_amount: Optional[float] = Field(None, description="最大亏损金额")


class StopLossStrategy(ABC):
    """止损策略抽象基类"""
    
    def __init__(self, config: StopLossConfig):
        self.config = config
        self.current_stop_loss = None
        self.highest_price = config.entry_price
        self.lowest_price = config.entry_price
        self.is_active = False
        self.ladder_step_index = 0
    
    @abstractmethod
    def calculate_stop_loss(self, current_price: float, atr: Optional[float] = None) -> float:
        """计算止损价格"""
        pass
    
    @abstractmethod
    def should_close_position(self, current_price: float, atr: Optional[float] = None) -> tuple[bool, str]:
        """判断是否应该平仓"""
        pass


class FixedStopLoss(StopLossStrategy):
    """固定止损策略"""
    
    def calculate_stop_loss(self, current_price: float, atr: Optional[float] = None) -> float:
        """固定百分比止损"""
        if self.config.stop_loss_percent:
            stop_loss = self.config.entry_price * (1 - self.config.stop_loss_percent)
            
            # 如果设置了最大亏损金额，也考虑
            if self.config.max_loss_amount:
                price_by_amount = self.config.entry_price - (self.config.max_loss_amount / self.config.position_size)
                stop_loss = max(stop_loss, price_by_amount)
            
            self.current_stop_loss = stop_loss
            return stop_loss
        return self.config.entry_price * 0.95  # 默认5%止损
    
    def should_close_position(self, current_price: float, atr: Optional[float] = None) -> tuple[bool, str]:
        """判断是否触发止损"""
        stop_loss = self.calculate_stop_loss(current_price)
        if current_price <= stop_loss:
            return True, f"固定止损触发: 价格{current_price} <= 止损线{stop_loss}"
        return False, ""


class DynamicStopLoss(StopLossStrategy):
    """动态止损策略（基于ATR）"""
    
    def calculate_stop_loss(self, current_price: float, atr: Optional[float] = None) -> float:
        """基于ATR的动态止损"""
        if atr:
            stop_loss = current_price - (atr * self.config.atr_multiplier)
            self.current_stop_loss = stop_loss
            return stop_loss
        
        # 如果没有ATR，使用固定百分比作为后备
        return self.config.entry_price * (1 - self.config.stop_loss_percent if self.config.stop_loss_percent else 0.95)
    
    def should_close_position(self, current_price: float, atr: Optional[float] = None) -> tuple[bool, str]:
        """判断是否触发止损"""
        stop_loss = self.calculate_stop_loss(current_price, atr)
        
        # 检查最大亏损金额限制
        if self.config.max_loss_amount:
            potential_loss = (self.config.entry_price - current_price) * self.config.position_size
            if potential_loss >= self.config.max_loss_amount:
                return True, f"达到最大亏损限制: {potential_loss:.2f} >= {self.config.max_loss_amount}"
        
        if current_price <= stop_loss:
            return True, f"动态止损触发: 价格{current_price} <= 止损线{stop_loss:.4f}"
        return False, ""


class TrailingStopLoss(StopLossStrategy):
    """追踪止损策略"""
    
    def calculate_stop_loss(self, current_price: float, atr: Optional[float] = None) -> float:
        """追踪止损计算"""
        # 更新最高价
        self.highest_price = max(self.highest_price, current_price)
        
        # 检查是否达到激活盈利条件
        profit_percent = (current_price - self.config.entry_price) / self.config.entry_price * 100
        if not self.is_active and self.config.activation_profit and profit_percent >= self.config.activation_profit:
            self.is_active = True
        
        # 计算追踪止损线
        if self.is_active and self.config.trailing_percent:
            stop_loss = self.highest_price * (1 - self.config.trailing_percent)
            self.current_stop_loss = stop_loss
            return stop_loss
        
        # 未激活时，使用固定止损
        return self.config.entry_price * (1 - self.config.stop_loss_percent if self.config.stop_loss_percent else 0.95)
    
    def should_close_position(self, current_price: float, atr: Optional[float] = None) -> tuple[bool, str]:
        """判断是否触发止损"""
        stop_loss = self.calculate_stop_loss(current_price)
        
        if self.is_active:
            if current_price <= stop_loss:
                return True, f"追踪止损触发: 价格{current_price} <= 止损线{stop_loss:.4f}"
        else:
            # 未激活时，检查固定止损
            fixed_stop = self.config.entry_price * (1 - self.config.stop_loss_percent if self.config.stop_loss_percent else 0.95)
            if current_price <= fixed_stop:
                return True, f"初始止损触发: 价格{current_price} <= 止损线{fixed_stop:.4f}"
        
        # 检查最大亏损金额限制
        if self.config.max_loss_amount:
            potential_loss = (self.config.entry_price - current_price) * self.config.position_size
            if potential_loss >= self.config.max_loss_amount:
                return True, f"达到最大亏损限制: {potential_loss:.2f} >= {self.config.max_loss_amount}"
        
        return False, ""


class LadderStopLoss(StopLossStrategy):
    """阶梯止损策略"""
    
    def __init__(self, config: StopLossConfig):
        super().__init__(config)
        # 默认阶梯配置
        if not config.ladder_steps:
            self.config.ladder_steps = [
                {"profit_percent": 0.02, "stop_loss_percent": 0.01, "close_percent": 0.3},
                {"profit_percent": 0.05, "stop_loss_percent": 0.02, "close_percent": 0.4},
                {"profit_percent": 0.10, "stop_loss_percent": 0.03, "close_percent": 0.5},
            ]
    
    def calculate_stop_loss(self, current_price: float, atr: Optional[float] = None) -> float:
        """阶梯止损计算"""
        # 检查当前盈利情况
        profit_percent = (current_price - self.config.entry_price) / self.config.entry_price
        
        # 找到当前应该使用的阶梯
        current_step = None
        for i, step in enumerate(self.config.ladder_steps):
            if profit_percent >= step["profit_percent"]:
                current_step = step
                self.ladder_step_index = i
            else:
                break
        
        if current_step:
            # 使用阶梯止损
            stop_loss = self.config.entry_price * (1 + current_step["stop_loss_percent"])
        else:
            # 使用初始止损
            stop_loss = self.config.entry_price * (1 - self.config.stop_loss_percent if self.config.stop_loss_percent else 0.95)
        
        self.current_stop_loss = stop_loss
        return stop_loss
    
    def should_close_position(self, current_price: float, atr: Optional[float] = None) -> tuple[bool, str]:
        """判断是否触发止损"""
        stop_loss = self.calculate_stop_loss(current_price)
        
        # 检查最大亏损金额限制
        if self.config.max_loss_amount:
            potential_loss = (self.config.entry_price - current_price) * self.config.position_size
            if potential_loss >= self.config.max_loss_amount:
                return True, f"达到最大亏损限制: {potential_loss:.2f} >= {self.config.max_loss_amount}"
        
        if current_price <= stop_loss:
            step_info = f" (阶梯{self.ladder_step_index + 1})" if self.ladder_step_index < len(self.config.ladder_steps) else ""
            return True, f"阶梯止损触发{step_info}: 价格{current_price} <= 止损线{stop_loss:.4f}"
        
        return False, ""


class StopLossStrategyFactory:
    """止损策略工厂"""
    
    @staticmethod
    def create_strategy(config: StopLossConfig) -> StopLossStrategy:
        """创建止损策略"""
        strategy_map = {
            "fixed": FixedStopLoss,
            "dynamic": DynamicStopLoss,
            "trailing": TrailingStopLoss,
            "ladder": LadderStopLoss,
        }
        
        strategy_class = strategy_map.get(config.strategy_type)
        if not strategy_class:
            raise ValueError(f"不支持的止损策略类型: {config.strategy_type}")
        
        return strategy_class(config)
    
    @staticmethod
    def get_available_strategies() -> list[str]:
        """获取可用的止损策略列表"""
        return ["fixed", "dynamic", "trailing", "ladder"]


# 使用示例
if __name__ == "__main__":
    # 固定止损示例
    fixed_config = StopLossConfig(
        strategy_type="fixed",
        entry_price=100.0,
        position_size=1.0,
        stop_loss_percent=0.05
    )
    fixed_strategy = StopLossStrategyFactory.create_strategy(fixed_config)
    print(f"固定止损价格: {fixed_strategy.calculate_stop_loss(95.0)}")
    
    # 追踪止损示例
    trailing_config = StopLossConfig(
        strategy_type="trailing",
        entry_price=100.0,
        position_size=1.0,
        trailing_percent=0.03,
        activation_profit=0.05
    )
    trailing_strategy = StopLossStrategyFactory.create_strategy(trailing_config)
    print(f"追踪止损价格(未激活): {trailing_strategy.calculate_stop_loss(100.0)}")
    print(f"追踪止损价格(激活后): {trailing_strategy.calculate_stop_loss(105.0)}")
