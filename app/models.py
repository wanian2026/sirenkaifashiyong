from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    role = Column(String, default="viewer")  # 默认角色: viewer, trader, admin
    encrypted_api_key = Column(Text, nullable=True)  # 加密的API密钥
    encrypted_api_secret = Column(Text, nullable=True)  # 加密的API密钥密钥

    # 关系
    roles = relationship("RoleModel", secondary="user_roles", back_populates="users")


class TradingBot(Base):
    __tablename__ = "trading_bots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    trading_pair = Column(String, nullable=False)
    strategy = Column(String, nullable=False)
    status = Column(String, default="stopped")
    config = Column(Text)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class GridOrder(Base):
    __tablename__ = "grid_orders"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, nullable=False)
    level = Column(Integer, nullable=False)
    order_type = Column(String, nullable=False)  # buy or sell
    order_category = Column(String, default="limit")  # limit, market, stop_loss, take_profit
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, partial, filled, cancelled, failed
    order_id = Column(String)  # 交易所订单ID
    exchange_order_id = Column(String)  # 交易所订单ID（与order_id相同，用于明确）
    side = Column(String, nullable=False)  # buy or sell
    trading_pair = Column(String, nullable=False)  # 交易对，如 BTC/USDT
    filled_amount = Column(Float, default=0)
    filled_price = Column(Float, default=None)  # 实际成交价格（市价单可能不同）
    fee = Column(Float, default=0)  # 手续费
    stop_price = Column(Float, default=None)  # 触发价格（止损/止盈单）
    stop_loss_price = Column(Float, default=None)  # 止损价格
    take_profit_price = Column(Float, default=None)  # 止盈价格
    retry_count = Column(Integer, default=0)  # 重试次数
    max_retry = Column(Integer, default=3)  # 最大重试次数
    last_retry_at = Column(DateTime(timezone=True), default=None)  # 最后重试时间
    error_message = Column(Text, default=None)  # 错误信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    filled_at = Column(DateTime(timezone=True))


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, nullable=False)
    order_id = Column(String, nullable=False)
    trading_pair = Column(String, nullable=False)
    side = Column(String, nullable=False)  # buy or sell
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    fee = Column(Float, default=0)
    profit = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
