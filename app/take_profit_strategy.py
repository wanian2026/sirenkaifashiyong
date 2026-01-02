"""
止盈策略模块
实现4种止盈策略：固定、动态、阶梯、部分
"""
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from datetime import datetime


class TakeProfitConfig(BaseModel):
    """止盈配置"""
    strategy_type: str = Field(..., description="止盈策略类型: fixed, dynamic, ladder, partial")
    entry_price: float = Field(..., description="入场价格")
    position_size: float = Field(..., description="仓位大小")
    
    # 固定止盈参数
    take_profit_percent: Optional[float] = Field(None, description="止盈百分比")
    
    # 动态止盈参数
    rsi_period: Optional[int] = Field(14, description="RSI周期")
    rsi_overbought: Optional[float] = Field(70.0, description="RSI超买阈值")
    
    # 阶梯止盈参数
    ladder_steps: Optional[List[Dict]] = Field(None, description="阶梯级别配置")
    
    # 部分止盈参数
    partial_steps: Optional[List[Dict]] = Field(None, description="部分止盈步骤")
    
    # 通用参数
    max_profit_amount: Optional[float] = Field(None, description="最大盈利金额")
    trailing_percent: Optional[float] = Field(None, description="回撤百分比（用于动态止盈）")


class TakeProfitStrategy(ABC):
    """止盈策略抽象基类"""
    
    def __init__(self, config: TakeProfitConfig):
        self.config = config
        self.current_take_profit = None
        self.highest_price = config.entry_price
        self.is_active = False
        self.ladder_step_index = 0
        self.partial_step_index = 0
        self.closed_amount = 0.0
    
    @abstractmethod
    def calculate_take_profit(self, current_price: float, **kwargs) -> float:
        """计算止盈价格"""
        pass
    
    @abstractmethod
    def should_close_position(self, current_price: float, **kwargs) -> tuple[bool, str, float]:
        """判断是否应该平仓 (is_close, reason, close_amount)"""
        pass
    
    @abstractmethod
    def get_closed_amount(self) -> float:
        """获取已平仓数量"""
        pass


class FixedTakeProfit(TakeProfitStrategy):
    """固定止盈策略"""
    
    def calculate_take_profit(self, current_price: float, **kwargs) -> float:
        """固定百分比止盈"""
        if self.config.take_profit_percent:
            take_profit = self.config.entry_price * (1 + self.config.take_profit_percent)
            
            # 如果设置了最大盈利金额，也考虑
            if self.config.max_profit_amount:
                price_by_amount = self.config.entry_price + (self.config.max_profit_amount / self.config.position_size)
                take_profit = min(take_profit, price_by_amount)
            
            self.current_take_profit = take_profit
            return take_profit
        return self.config.entry_price * 1.10  # 默认10%止盈
    
    def should_close_position(self, current_price: float, **kwargs) -> tuple[bool, str, float]:
        """判断是否触发止盈"""
        take_profit = self.calculate_take_profit(current_price)
        
        if current_price >= take_profit:
            close_amount = self.config.position_size - self.closed_amount
            return True, f"固定止盈触发: 价格{current_price} >= 止盈线{take_profit}", close_amount
        
        # 检查最大盈利金额限制
        if self.config.max_profit_amount:
            potential_profit = (current_price - self.config.entry_price) * self.config.position_size
            if potential_profit >= self.config.max_profit_amount:
                close_amount = self.config.position_size - self.closed_amount
                return True, f"达到最大盈利限制: {potential_profit:.2f} >= {self.config.max_profit_amount}", close_amount
        
        return False, "", 0.0
    
    def get_closed_amount(self) -> float:
        """获取已平仓数量"""
        return self.closed_amount


class DynamicTakeProfit(TakeProfitStrategy):
    """动态止盈策略（基于RSI和回撤）"""
    
    def calculate_take_profit(self, current_price: float, rsi: Optional[float] = None, **kwargs) -> float:
        """基于RSI的动态止盈"""
        # 更新最高价
        self.highest_price = max(self.highest_price, current_price)
        
        # 计算当前盈利百分比
        profit_percent = (current_price - self.config.entry_price) / self.config.entry_price
        
        # 如果有RSI且超买，触发止盈
        if rsi and rsi > self.config.rsi_overbought:
            self.is_active = True
        
        # 计算动态止盈线（基于回撤）
        if self.is_active and self.config.trailing_percent:
            take_profit = self.highest_price * (1 - self.config.trailing_percent)
            self.current_take_profit = take_profit
            return take_profit
        
        # 如果达到一定盈利后激活
        if profit_percent > 0.05:  # 盈利5%后激活
            self.is_active = True
            if self.config.trailing_percent:
                take_profit = self.highest_price * (1 - self.config.trailing_percent)
                self.current_take_profit = take_profit
                return take_profit
        
        # 未激活时，返回一个较高的止盈线
        return self.config.entry_price * (1 + self.config.take_profit_percent if self.config.take_profit_percent else 1.15)
    
    def should_close_position(self, current_price: float, rsi: Optional[float] = None, **kwargs) -> tuple[bool, str, float]:
        """判断是否触发止盈"""
        take_profit = self.calculate_take_profit(current_price, rsi)
        
        # 检查最大盈利金额限制
        if self.config.max_profit_amount:
            potential_profit = (current_price - self.config.entry_price) * self.config.position_size
            if potential_profit >= self.config.max_profit_amount:
                close_amount = self.config.position_size - self.closed_amount
                return True, f"达到最大盈利限制: {potential_profit:.2f} >= {self.config.max_profit_amount}", close_amount
        
        if self.is_active:
            if current_price <= take_profit:
                close_amount = self.config.position_size - self.closed_amount
                return True, f"动态止盈触发: 价格{current_price} <= 止盈线{take_profit:.4f}", close_amount
        else:
            # 未激活时，检查固定止盈
            fixed_tp = self.config.entry_price * (1 + self.config.take_profit_percent if self.config.take_profit_percent else 1.15)
            if current_price >= fixed_tp:
                close_amount = self.config.position_size - self.closed_amount
                return True, f"固定止盈触发: 价格{current_price} >= 止盈线{fixed_tp:.4f}", close_amount
        
        # RSI超买直接止盈
        if rsi and rsi > self.config.rsi_overbought:
            close_amount = self.config.position_size - self.closed_amount
            return True, f"RSI超买触发止盈: RSI={rsi:.2f}", close_amount
        
        return False, "", 0.0
    
    def get_closed_amount(self) -> float:
        """获取已平仓数量"""
        return self.closed_amount


class LadderTakeProfit(TakeProfitStrategy):
    """阶梯止盈策略"""
    
    def __init__(self, config: TakeProfitConfig):
        super().__init__(config)
        # 默认阶梯配置
        if not config.ladder_steps:
            self.config.ladder_steps = [
                {"profit_percent": 0.05, "take_profit_percent": 0.03, "close_percent": 0.3},
                {"profit_percent": 0.10, "take_profit_percent": 0.05, "close_percent": 0.3},
                {"profit_percent": 0.15, "take_profit_percent": 0.08, "close_percent": 0.4},
            ]
    
    def calculate_take_profit(self, current_price: float, **kwargs) -> float:
        """阶梯止盈计算"""
        # 检查当前盈利情况
        profit_percent = (current_price - self.config.entry_price) / self.config.entry_price
        
        # 找到当前应该使用的阶梯
        current_step = None
        for i, step in enumerate(self.config.ladder_steps):
            if profit_percent >= step["profit_percent"] and self.ladder_step_index <= i:
                current_step = step
                break
        
        if current_step:
            take_profit = self.config.entry_price * (1 + current_step["take_profit_percent"])
        else:
            take_profit = self.config.entry_price * (1 + self.config.take_profit_percent if self.config.take_profit_percent else 1.10)
        
        self.current_take_profit = take_profit
        return take_profit
    
    def should_close_position(self, current_price: float, **kwargs) -> tuple[bool, str, float]:
        """判断是否触发止盈"""
        profit_percent = (current_price - self.config.entry_price) / self.config.entry_price
        
        # 检查最大盈利金额限制
        if self.config.max_profit_amount:
            potential_profit = (current_price - self.config.entry_price) * self.config.position_size
            if potential_profit >= self.config.max_profit_amount:
                close_amount = self.config.position_size - self.closed_amount
                return True, f"达到最大盈利限制: {potential_profit:.2f} >= {self.config.max_profit_amount}", close_amount
        
        # 检查是否达到某个阶梯
        for i, step in enumerate(self.config.ladder_steps):
            if profit_percent >= step["profit_percent"] and self.ladder_step_index == i:
                # 触发阶梯止盈
                close_amount = self.config.position_size * step["close_percent"]
                
                # 检查是否超过剩余仓位
                remaining = self.config.position_size - self.closed_amount
                if close_amount > remaining:
                    close_amount = remaining
                
                self.closed_amount += close_amount
                self.ladder_step_index += 1
                
                return True, f"阶梯{i+1}止盈触发: 盈利{profit_percent*100:.2f}%，平仓{close_amount}", close_amount
        
        # 检查是否达到当前阶梯的止盈线
        if self.ladder_step_index > 0 and self.ladder_step_index <= len(self.config.ladder_steps):
            take_profit = self.calculate_take_profit(current_price)
            if current_price >= take_profit:
                remaining = self.config.position_size - self.closed_amount
                if remaining > 0:
                    self.closed_amount += remaining
                    return True, f"阶梯止盈触发: 价格{current_price} >= 止盈线{take_profit:.4f}", remaining
        
        return False, "", 0.0
    
    def get_closed_amount(self) -> float:
        """获取已平仓数量"""
        return self.closed_amount


class PartialTakeProfit(TakeProfitStrategy):
    """部分止盈策略"""
    
    def __init__(self, config: TakeProfitConfig):
        super().__init__(config)
        # 默认部分止盈配置
        if not config.partial_steps:
            self.config.partial_steps = [
                {"profit_percent": 0.03, "close_percent": 0.3},
                {"profit_percent": 0.06, "close_percent": 0.3},
                {"profit_percent": 0.10, "close_percent": 0.2},
                {"profit_percent": 0.15, "close_percent": 0.2},
            ]
    
    def calculate_take_profit(self, current_price: float, **kwargs) -> float:
        """部分止盈计算"""
        # 计算当前盈利百分比
        profit_percent = (current_price - self.config.entry_price) / self.config.entry_price
        
        # 找到下一个未触发的止盈点
        for i, step in enumerate(self.config.partial_steps):
            if self.partial_step_index <= i and profit_percent >= step["profit_percent"]:
                # 返回入场价格作为触发信号（实际在should_close中处理）
                return current_price
        
        return self.config.entry_price * (1 + self.config.take_profit_percent if self.config.take_profit_percent else 1.15)
    
    def should_close_position(self, current_price: float, **kwargs) -> tuple[bool, str, float]:
        """判断是否触发部分止盈"""
        profit_percent = (current_price - self.config.entry_price) / self.config.entry_price
        
        # 检查最大盈利金额限制
        if self.config.max_profit_amount:
            potential_profit = (current_price - self.config.entry_price) * self.config.position_size
            if potential_profit >= self.config.max_profit_amount:
                remaining = self.config.position_size - self.closed_amount
                if remaining > 0:
                    return True, f"达到最大盈利限制: {potential_profit:.2f} >= {self.config.max_profit_amount}", remaining
        
        # 检查是否达到部分止盈点
        for i, step in enumerate(self.config.partial_steps):
            if self.partial_step_index <= i and profit_percent >= step["profit_percent"]:
                close_amount = self.config.position_size * step["close_percent"]
                
                # 检查是否超过剩余仓位
                remaining = self.config.position_size - self.closed_amount
                if close_amount > remaining:
                    close_amount = remaining
                
                self.closed_amount += close_amount
                self.partial_step_index += 1
                
                remaining_after = self.config.position_size - self.closed_amount
                status = "全部平仓" if remaining_after == 0 else f"剩余仓位{remaining_after:.4f}"
                
                return True, f"部分止盈{self.partial_step_index}触发: 盈利{profit_percent*100:.2f}%，平仓{close_amount:.4f}，{status}", close_amount
        
        return False, "", 0.0
    
    def get_closed_amount(self) -> float:
        """获取已平仓数量"""
        return self.closed_amount


class TakeProfitStrategyFactory:
    """止盈策略工厂"""
    
    @staticmethod
    def create_strategy(config: TakeProfitConfig) -> TakeProfitStrategy:
        """创建止盈策略"""
        strategy_map = {
            "fixed": FixedTakeProfit,
            "dynamic": DynamicTakeProfit,
            "ladder": LadderTakeProfit,
            "partial": PartialTakeProfit,
        }
        
        strategy_class = strategy_map.get(config.strategy_type)
        if not strategy_class:
            raise ValueError(f"不支持的止盈策略类型: {config.strategy_type}")
        
        return strategy_class(config)
    
    @staticmethod
    def get_available_strategies() -> list[str]:
        """获取可用的止盈策略列表"""
        return ["fixed", "dynamic", "ladder", "partial"]


# 使用示例
if __name__ == "__main__":
    # 固定止盈示例
    fixed_config = TakeProfitConfig(
        strategy_type="fixed",
        entry_price=100.0,
        position_size=1.0,
        take_profit_percent=0.10
    )
    fixed_strategy = TakeProfitStrategyFactory.create_strategy(fixed_config)
    print(f"固定止盈价格: {fixed_strategy.calculate_take_profit(95.0)}")
    
    # 部分止盈示例
    partial_config = TakeProfitConfig(
        strategy_type="partial",
        entry_price=100.0,
        position_size=1.0
    )
    partial_strategy = TakeProfitStrategyFactory.create_strategy(partial_config)
    should_close, reason, amount = partial_strategy.should_close_position(103.0)
    print(f"部分止盈测试: {should_close}, {reason}, {amount}")
