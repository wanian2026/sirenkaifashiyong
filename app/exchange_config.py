"""
多交易所配置管理模块
支持多个交易所的配置、连接和资金管理
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import logging

logger = logging.getLogger(__name__)


class ExchangeConfig(Base):
    """交易所配置表"""
    __tablename__ = "exchange_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # 用户ID
    exchange_name = Column(String, nullable=False, index=True)  # 交易所名称：binance, okx, huobi等
    api_key = Column(Text, nullable=False)  # 加密的API密钥
    api_secret = Column(Text, nullable=False)  # 加密的API密钥
    passphrase = Column(Text, nullable=True)  # 加密的passphrase（某些交易所需要，如OKX）
    is_active = Column(Boolean, default=True, index=True)  # 是否启用
    is_testnet = Column(Boolean, default=False)  # 是否使用测试网
    label = Column(String, nullable=True)  # 用户自定义标签
    notes = Column(Text, nullable=True)  # 备注
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_connected_at = Column(DateTime(timezone=True), nullable=True)  # 最后连接时间
    connection_status = Column(String, default="unknown")  # 连接状态：connected, disconnected, error

    # 复合索引：优化用户交易所列表查询
    __table_args__ = (
        {'comment': '交易所配置表'},
    )


class ExchangeBalance(Base):
    """交易所余额表"""
    __tablename__ = "exchange_balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # 用户ID
    exchange_id = Column(Integer, ForeignKey('exchange_configs.id'), nullable=False, index=True)  # 交易所配置ID
    asset = Column(String, nullable=False, index=True)  # 资产名称：USDT, BTC等
    free = Column(Float, default=0.0)  # 可用余额
    locked = Column(Float, default=0.0)  # 冻结余额
    total = Column(Float, default=0.0)  # 总余额
    usd_value = Column(Float, default=0.0)  # 美元价值
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 复合索引：优化余额查询
    __table_args__ = (
        {'comment': '交易所余额表'},
    )


class ExchangeTransfer(Base):
    """交易所转账记录表"""
    __tablename__ = "exchange_transfers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # 用户ID
    from_exchange_id = Column(Integer, ForeignKey('exchange_configs.id'), nullable=True, index=True)  # 源交易所ID
    to_exchange_id = Column(Integer, ForeignKey('exchange_configs.id'), nullable=True, index=True)  # 目标交易所ID
    asset = Column(String, nullable=False)  # 转账资产
    amount = Column(Float, nullable=False)  # 转账数量
    tx_hash = Column(String, nullable=True)  # 区块链交易哈希
    status = Column(String, default="pending")  # 状态：pending, completed, failed
    fee = Column(Float, default=0.0)  # 手续费
    notes = Column(Text, nullable=True)  # 备注
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # 复合索引：优化转账记录查询
    __table_args__ = (
        {'comment': '交易所转账记录表'},
    )
