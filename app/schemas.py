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
    bot_id: int
    order_type: Literal['buy', 'sell']
    price: float
    amount: float
    level: Optional[int] = None


class OrderResponse(BaseModel):
    id: int
    bot_id: int
    level: int
    order_type: str
    price: float
    amount: float
    status: str
    order_id: Optional[str]
    filled_amount: float
    created_at: datetime
    filled_at: Optional[datetime]

    class Config:
        from_attributes = True


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
