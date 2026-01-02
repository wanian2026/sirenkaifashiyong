from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class TradingBotState(BaseModel):
    """交易机器人状态"""
    bot_id: int = Field(..., description="机器人ID")
    bot_name: str = Field(..., description="机器人名称")
    exchange: str = Field(..., description="交易所")
    trading_pair: str = Field(..., description="交易对")
    strategy_config: Dict = Field(default_factory=dict, description="策略配置")
    status: str = Field(default="stopped", description="状态: running, stopped, error")
    current_price: float = Field(default=0.0, description="当前价格")
    total_invested: float = Field(default=0.0, description="总投入")
    realized_profit: float = Field(default=0.0, description="已实现利润")
    orders: List[Dict] = Field(default_factory=list, description="订单列表")
    trades: List[Dict] = Field(default_factory=list, description="交易记录")
    error_message: Optional[str] = Field(None, description="错误信息")


class MarketDataInput(BaseModel):
    """市场数据输入"""
    trading_pair: str = Field(..., description="交易对")
    price: float = Field(..., description="当前价格")
    volume: Optional[float] = Field(None, description="成交量")


class MarketDataOutput(BaseModel):
    """市场数据输出"""
    price: float = Field(..., description="处理后的价格")
    trend: str = Field(default="neutral", description="趋势: up, down, neutral")
    volatility: float = Field(default=0.0, description="波动率")


class StrategyInput(BaseModel):
    """策略输入"""
    state: TradingBotState = Field(..., description="当前机器人状态")
    market_data: MarketDataOutput = Field(..., description="市场数据")


class StrategyOutput(BaseModel):
    """策略输出"""
    signals: List[Dict] = Field(default_factory=list, description="交易信号")
    updated_state: TradingBotState = Field(..., description="更新后的状态")


class ExecutionInput(BaseModel):
    """执行输入"""
    signals: List[Dict] = Field(default_factory=list, description="交易信号")
    state: TradingBotState = Field(..., description="机器人状态")


class ExecutionOutput(BaseModel):
    """执行输出"""
    executed_orders: List[Dict] = Field(default_factory=list, description="已执行的订单")
    updated_state: TradingBotState = Field(..., description="更新后的状态")
    success: bool = Field(..., description="是否成功")


class RiskCheckInput(BaseModel):
    """风险检查输入"""
    signals: List[Dict] = Field(default_factory=list, description="交易信号")
    state: TradingBotState = Field(..., description="机器人状态")


class RiskCheckOutput(BaseModel):
    """风险检查输出"""
    approved: bool = Field(..., description="是否通过风险检查")
    filtered_signals: List[Dict] = Field(default_factory=list, description="过滤后的信号")
    risk_level: str = Field(default="low", description="风险等级: low, medium, high")
