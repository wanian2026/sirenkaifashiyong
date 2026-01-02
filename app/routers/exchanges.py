"""
交易所配置管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.exchange_config import ExchangeConfig, ExchangeBalance, ExchangeTransfer
from app.exchange_manager import ExchangeManager
from app.encryption import EncryptionManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== 请求和响应模型 ====================

class ExchangeConfigCreate(BaseModel):
    """创建交易所配置请求"""
    exchange_name: str = Field(..., description="交易所名称: binance, okx, huobi等")
    api_key: str = Field(..., description="API密钥")
    api_secret: str = Field(..., description="API密钥密钥")
    passphrase: Optional[str] = Field(None, description="密钥短语（某些交易所需要）")
    label: Optional[str] = Field(None, description="用户自定义标签")
    notes: Optional[str] = Field(None, description="备注")
    is_testnet: bool = Field(False, description="是否使用测试网")


class ExchangeConfigUpdate(BaseModel):
    """更新交易所配置请求"""
    label: Optional[str] = Field(None, description="用户自定义标签")
    notes: Optional[str] = Field(None, description="备注")
    is_active: Optional[bool] = Field(None, description="是否启用")
    api_key: Optional[str] = Field(None, description="API密钥")
    api_secret: Optional[str] = Field(None, description="API密钥密钥")
    passphrase: Optional[str] = Field(None, description="密钥短语")


class ExchangeConfigResponse(BaseModel):
    """交易所配置响应"""
    id: int
    user_id: int
    exchange_name: str
    label: Optional[str]
    notes: Optional[str]
    is_active: bool
    is_testnet: bool
    connection_status: str
    last_connected_at: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TestConnectionRequest(BaseModel):
    """测试连接请求"""
    exchange_name: str = Field(..., description="交易所名称")
    api_key: str = Field(..., description="API密钥")
    api_secret: str = Field(..., description="API密钥密钥")
    passphrase: Optional[str] = Field(None, description="密钥短语")
    is_testnet: bool = Field(False, description="是否使用测试网")


class BalanceResponse(BaseModel):
    """余额响应"""
    asset: str
    total: float
    free: float
    locked: float

    class Config:
        from_attributes = True


# ==================== API端点 ====================

@router.get("/supported")
async def get_supported_exchanges():
    """获取支持的交易所列表"""
    exchanges = ExchangeManager.get_supported_exchanges()
    return {
        "success": True,
        "exchanges": exchanges
    }


@router.post("/test-connection")
async def test_exchange_connection(request: TestConnectionRequest):
    """
    测试交易所连接

    在添加交易所配置之前，可以先测试连接是否正常
    """
    result = await ExchangeManager.test_connection(
        exchange_name=request.exchange_name,
        api_key=request.api_key,
        api_secret=request.api_secret,
        passphrase=request.passphrase,
        is_testnet=request.is_testnet
    )

    return result


@router.post("/", response_model=ExchangeConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_exchange_config(
    config_data: ExchangeConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建交易所配置

    添加一个新的交易所配置，API密钥会自动加密存储
    """
    try:
        # 检查是否支持该交易所
        supported = ExchangeManager.get_supported_exchanges()
        if config_data.exchange_name.lower() not in supported:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的交易所: {config_data.exchange_name}"
            )

        # 先测试连接
        test_result = await ExchangeManager.test_connection(
            exchange_name=config_data.exchange_name,
            api_key=config_data.api_key,
            api_secret=config_data.api_secret,
            passphrase=config_data.passphrase,
            is_testnet=config_data.is_testnet
        )

        if not test_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"连接测试失败: {test_result.get('message')}"
            )

        # 加密API密钥
        encryption_manager = EncryptionManager()
        encrypted_api_key = encryption_manager.encrypt(config_data.api_key)
        encrypted_api_secret = encryption_manager.encrypt(config_data.api_secret)
        encrypted_passphrase = None

        if config_data.passphrase:
            encrypted_passphrase = encryption_manager.encrypt(config_data.passphrase)

        # 创建配置
        new_config = ExchangeConfig(
            user_id=current_user.id,
            exchange_name=config_data.exchange_name.lower(),
            api_key=encrypted_api_key,
            api_secret=encrypted_api_secret,
            passphrase=encrypted_passphrase,
            label=config_data.label,
            notes=config_data.notes,
            is_active=config_data.is_active,
            is_testnet=config_data.is_testnet,
            connection_status="connected",
            last_connected_at=test_result.get('account_info', {}).get('timestamp')
        )

        db.add(new_config)
        db.commit()
        db.refresh(new_config)

        logger.info(f"用户 {current_user.id} 创建交易所配置: {new_config.id}")

        return new_config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建交易所配置失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建交易所配置失败: {str(e)}"
        )


@router.get("/", response_model=List[ExchangeConfigResponse])
async def get_exchange_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有交易所配置"""
    try:
        configs = db.query(ExchangeConfig).filter(
            ExchangeConfig.user_id == current_user.id
        ).order_by(ExchangeConfig.created_at.desc()).all()

        return configs

    except Exception as e:
        logger.error(f"获取交易所配置列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取交易所配置列表失败: {str(e)}"
        )


@router.get("/{config_id}", response_model=ExchangeConfigResponse)
async def get_exchange_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定的交易所配置"""
    try:
        config = db.query(ExchangeConfig).filter(
            ExchangeConfig.id == config_id,
            ExchangeConfig.user_id == current_user.id
        ).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="交易所配置不存在"
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易所配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取交易所配置失败: {str(e)}"
        )


@router.put("/{config_id}", response_model=ExchangeConfigResponse)
async def update_exchange_config(
    config_id: int,
    config_update: ExchangeConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新交易所配置

    可以更新标签、备注、启用状态和API密钥
    """
    try:
        config = db.query(ExchangeConfig).filter(
            ExchangeConfig.id == config_id,
            ExchangeConfig.user_id == current_user.id
        ).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="交易所配置不存在"
            )

        # 更新基本字段
        if config_update.label is not None:
            config.label = config_update.label
        if config_update.notes is not None:
            config.notes = config_update.notes
        if config_update.is_active is not None:
            config.is_active = config_update.is_active

        # 更新API密钥（如果提供）
        encryption_manager = EncryptionManager()

        if config_update.api_key is not None:
            config.api_key = encryption_manager.encrypt(config_update.api_key)
        if config_update.api_secret is not None:
            config.api_secret = encryption_manager.encrypt(config_update.api_secret)
        if config_update.passphrase is not None:
            config.passphrase = encryption_manager.encrypt(config_update.passphrase)

        db.commit()
        db.refresh(config)

        logger.info(f"用户 {current_user.id} 更新交易所配置: {config_id}")

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新交易所配置失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新交易所配置失败: {str(e)}"
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exchange_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除交易所配置"""
    try:
        config = db.query(ExchangeConfig).filter(
            ExchangeConfig.id == config_id,
            ExchangeConfig.user_id == current_user.id
        ).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="交易所配置不存在"
            )

        db.delete(config)
        db.commit()

        logger.info(f"用户 {current_user.id} 删除交易所配置: {config_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除交易所配置失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除交易所配置失败: {str(e)}"
        )


@router.post("/{config_id}/refresh-balance")
async def refresh_exchange_balance(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    刷新指定交易所的余额

    从交易所获取最新的余额数据并更新到数据库
    """
    try:
        # 获取配置
        config = db.query(ExchangeConfig).filter(
            ExchangeConfig.id == config_id,
            ExchangeConfig.user_id == current_user.id
        ).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="交易所配置不存在"
            )

        # 获取余额
        encryption_manager = EncryptionManager()
        exchange = ExchangeManager.create_exchange_from_db(
            exchange_id=config_id,
            db=db,
            encryption_manager=encryption_manager
        )

        if not exchange:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建交易所实例失败"
            )

        balance = await exchange.fetch_balance()

        # 更新余额记录
        updated_assets = []
        for asset, total in balance.get('total', {}).items():
            if total > 0:
                # 查找或创建余额记录
                balance_record = db.query(ExchangeBalance).filter(
                    ExchangeBalance.exchange_id == config_id,
                    ExchangeBalance.asset == asset
                ).first()

                if not balance_record:
                    balance_record = ExchangeBalance(
                        user_id=current_user.id,
                        exchange_id=config_id,
                        asset=asset
                    )
                    db.add(balance_record)

                # 更新余额
                balance_record.free = balance.get('free', {}).get(asset, 0)
                balance_record.locked = balance.get('used', {}).get(asset, 0)
                balance_record.total = total
                updated_assets.append(asset)

        # 更新连接状态和时间
        config.connection_status = "connected"
        config.last_connected_at = datetime.now()

        db.commit()

        return {
            "success": True,
            "message": "余额更新成功",
            "updated_assets": updated_assets,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新交易所余额失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新交易所余额失败: {str(e)}"
        )


@router.get("/{config_id}/balances", response_model=List[BalanceResponse])
async def get_exchange_balances(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定交易所的余额列表"""
    try:
        # 验证交易所配置所有权
        config = db.query(ExchangeConfig).filter(
            ExchangeConfig.id == config_id,
            ExchangeConfig.user_id == current_user.id
        ).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="交易所配置不存在"
            )

        # 获取余额
        balances = db.query(ExchangeBalance).filter(
            ExchangeBalance.exchange_id == config_id
        ).all()

        return balances

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易所余额失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取交易所余额失败: {str(e)}"
        )


@router.post("/balances/refresh-all")
async def refresh_all_balances(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    刷新所有交易所的余额

    批量更新用户所有启用交易所的余额
    """
    try:
        encryption_manager = EncryptionManager()
        result = await ExchangeManager.update_exchange_balances(
            user_id=current_user.id,
            db=db,
            encryption_manager=encryption_manager
        )

        return result

    except Exception as e:
        logger.error(f"刷新所有交易所余额失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新所有交易所余额失败: {str(e)}"
        )


@router.get("/balance/total")
async def get_total_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户所有交易所的总余额

    汇总所有交易所的余额，按资产分类
    """
    try:
        result = ExchangeManager.get_user_total_balance(
            user_id=current_user.id,
            db=db
        )

        return result

    except Exception as e:
        logger.error(f"获取用户总余额失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户总余额失败: {str(e)}"
        )
