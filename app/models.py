import json
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.rbac import user_roles, RoleModel


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

    # 多因素认证相关字段
    mfa_enabled = Column(Boolean, default=False)  # 是否启用多因素认证
    mfa_secret = Column(String, nullable=True)  # MFA密钥（用于生成TOTP）
    mfa_backup_codes = Column(Text, nullable=True)  # MFA备用验证码（JSON格式存储）

    # 邮箱验证相关字段
    email_verified = Column(Boolean, default=False)  # 邮箱是否已验证
    email_verification_token = Column(String, nullable=True)  # 邮箱验证令牌
    email_verification_token_expires = Column(DateTime(timezone=True), nullable=True)  # 邮箱验证令牌过期时间

    # 关系
    roles = relationship("RoleModel", secondary="user_roles", back_populates="users")


class PasswordResetToken(Base):
    """密码重置令牌表"""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False, index=True)  # 重置令牌
    user_id = Column(Integer, nullable=False)  # 关联的用户ID
    expires_at = Column(DateTime(timezone=True), nullable=False)  # 令牌过期时间
    used = Column(Boolean, default=False)  # 令牌是否已使用
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 索引
    __table_args__ = (
        Index('idx_password_reset_token_user', 'user_id'),
        Index('idx_password_reset_token_expires', 'expires_at'),
    )


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

    # 复合索引：用户机器人列表查询优化
    __table_args__ = (
        Index('idx_trading_bots_user_status', 'user_id', 'status'),
    )

    @property
    def config_dict(self):
        """将config JSON字符串转换为dict"""
        if self.config is None:
            return {}
        try:
            return json.loads(self.config)
        except (json.JSONDecodeError, TypeError):
            return {}


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

    # 复合索引：优化订单查询
    __table_args__ = (
        Index('idx_grid_orders_bot_status', 'bot_id', 'status'),
        Index('idx_grid_orders_bot_level', 'bot_id', 'level'),
    )


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

    # 复合索引：优化交易记录查询
    __table_args__ = (
        Index('idx_trades_bot_created', 'bot_id', 'created_at'),
        Index('idx_trades_bot_side_created', 'bot_id', 'side', 'created_at'),
    )
