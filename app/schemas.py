from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class OrderType(str):
    ALLOWED_VALUES = Literal['buy', 'sell', 'market', 'limit', 'stop', 'stop_limit']


class OrderCreate(BaseModel):
    """创建订单请求"""
    bot_id: int
    order_type: Literal['buy', 'sell']
    order_category: Literal['limit', 'market', 'stop_loss', 'take_profit'] = 'limit'
    price: Optional[float] = None  # 市价单不需要价格
    amount: float
    level: Optional[int] = None
    trading_pair: Optional[str] = None  # 交易对，如果不提供则从机器人获取
    stop_price: Optional[float] = None  # 触发价格（止损/止盈单）
    stop_loss_price: Optional[float] = None  # 止损价格
    take_profit_price: Optional[float] = None  # 止盈价格
    max_retry: Optional[int] = 3  # 最大重试次数


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    bot_id: int
    level: int
    order_type: str  # buy or sell
    order_category: str  # limit, market, stop_loss, take_profit
    price: float
    amount: float
    status: str
    order_id: Optional[str]
    exchange_order_id: Optional[str]
    side: str  # buy or sell
    trading_pair: str
    filled_amount: float
    filled_price: Optional[float]
    fee: float
    stop_price: Optional[float]
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    retry_count: int
    max_retry: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    filled_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    """更新订单请求"""
    price: Optional[float] = None
    amount: Optional[float] = None
    stop_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    max_retry: Optional[int] = None


class TradeFilter(BaseModel):
    bot_id: Optional[int] = None
    trading_pair: Optional[str] = None
    side: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class BotCreate(BaseModel):
    name: str
    exchange: str
    trading_pair: str
    strategy: str
    config: Optional[dict] = None


class BotResponse(BaseModel):
    id: int
    name: str
    exchange: str
    trading_pair: str
    strategy: str
    status: str
    config: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class BotUpdate(BaseModel):
    name: Optional[str] = None
    exchange: Optional[str] = None
    trading_pair: Optional[str] = None
    strategy: Optional[str] = None
    config: Optional[dict] = None


class BotStatus(BaseModel):
    current_price: float
    total_invested: float
    realized_profit: float
    pending_orders: int
    filled_orders: int


class TradeResponse(BaseModel):
    id: int
    bot_id: int
    trading_pair: str
    side: str
    price: float
    amount: float
    profit: float
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 风险管理相关 Schema ============

class RiskConfig(BaseModel):
    """风险管理配置"""
    max_position: float = 10000
    max_daily_loss: float = 1000
    max_total_loss: float = 5000
    max_orders: int = 50
    max_single_order: float = 1000
    stop_loss_threshold: float = 0.05
    take_profit_threshold: float = 0.10
    enable_auto_stop: bool = True


class RiskCheckRequest(BaseModel):
    """风险检查请求"""
    position_value: float = 0
    order_value: float = 0


class RiskCheckResponse(BaseModel):
    """风险检查响应"""
    passed: bool
    errors: list
    risk_report: dict
    risk_level: str
    recommendation: str


class PositionSizeRequest(BaseModel):
    """仓位计算请求"""
    account_balance: float
    entry_price: float
    stop_loss_price: float
    risk_percent: float = 0.02


class PositionSizeResponse(BaseModel):
    """仓位计算响应"""
    account_balance: float
    risk_percent: float
    risk_amount: float
    entry_price: float
    stop_loss_price: float
    position_size: float
    position_value: float
    loss_per_unit: float
    risk_reward_ratio_warning: bool


class RiskRewardRatioRequest(BaseModel):
    """风险收益比计算请求"""
    entry_price: float
    stop_loss_price: float
    take_profit_price: float


class RiskRewardRatioResponse(BaseModel):
    """风险收益比计算响应"""
    entry_price: float
    stop_loss_price: float
    take_profit_price: float
    risk: float
    reward: float
    risk_reward_ratio: float
    suggestion: str


class RiskLevelEvaluateRequest(BaseModel):
    """风险等级评估请求"""
    position_value: float
    unrealized_pnl: float
    volatility: float = 0


class RiskLevelEvaluateResponse(BaseModel):
    """风险等级评估响应"""
    risk_level: str
    advice: str
    position_value: float
    unrealized_pnl: float
    volatility: float


class RiskAlert(BaseModel):
    """风险警报"""
    type: str
    message: str
    severity: str
    symbol: str

