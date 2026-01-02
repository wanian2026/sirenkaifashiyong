from pydantic import BaseModel, EmailStr
from typing import Optional
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
