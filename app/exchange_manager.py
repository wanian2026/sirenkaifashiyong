"""
多交易所管理器
管理多个交易所的配置、连接和操作
"""

import ccxt
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.exchange_config import ExchangeConfig, ExchangeBalance
from app.encryption import EncryptionManager
from app.database import get_db

logger = logging.getLogger(__name__)


class ExchangeManager:
    """多交易所管理器"""

    # 支持的交易所列表
    SUPPORTED_EXCHANGES = {
        'binance': '币安',
        'okx': '欧易',
        'huobi': '火币',
        'bybit': 'Bybit',
        'gate': 'Gate.io',
        'kucoin': 'KuCoin',
        'bitget': 'Bitget',
    }

    @staticmethod
    def get_supported_exchanges() -> Dict[str, str]:
        """获取支持的交易所列表"""
        return ExchangeManager.SUPPORTED_EXCHANGES

    @staticmethod
    def create_exchange_instance(
        exchange_name: str,
        api_key: str,
        api_secret: str,
        passphrase: str = None,
        is_testnet: bool = False
    ) -> Optional[ccxt.Exchange]:
        """
        创建交易所实例

        Args:
            exchange_name: 交易所名称
            api_key: API密钥
            api_secret: API密钥密钥
            passphrase: 密钥短语（某些交易所需要）
            is_testnet: 是否使用测试网

        Returns:
            交易所实例或None
        """
        try:
            exchange_name_lower = exchange_name.lower()

            # 检查是否支持该交易所
            if exchange_name_lower not in ExchangeManager.SUPPORTED_EXCHANGES:
                logger.error(f"不支持的交易所: {exchange_name}")
                return None

            # 创建交易所配置
            config = {
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
            }

            # 添加passphrase（某些交易所需要）
            if passphrase:
                config['password'] = passphrase

            # 设置测试网
            if is_testnet:
                if exchange_name_lower == 'binance':
                    config['testnet'] = True
                elif exchange_name_lower == 'okx':
                    config['urls'] = {
                        'api': {
                            'public': 'https://www.okx.com',
                            'private': 'https://www.okx.com'
                        }
                    }

            # 创建交易所实例
            exchange_class = getattr(ccxt, exchange_name_lower)
            exchange = exchange_class(config)

            logger.info(f"成功创建交易所实例: {exchange_name}")
            return exchange

        except Exception as e:
            logger.error(f"创建交易所实例失败: {exchange_name}, {e}")
            return None

    @staticmethod
    async def test_connection(
        exchange_name: str,
        api_key: str,
        api_secret: str,
        passphrase: str = None,
        is_testnet: bool = False
    ) -> Dict:
        """
        测试交易所连接

        Args:
            exchange_name: 交易所名称
            api_key: API密钥
            api_secret: API密钥密钥
            passphrase: 密钥短语
            is_testnet: 是否使用测试网

        Returns:
            测试结果字典
        """
        try:
            exchange = ExchangeManager.create_exchange_instance(
                exchange_name=exchange_name,
                api_key=api_key,
                api_secret=api_secret,
                passphrase=passphrase,
                is_testnet=is_testnet
            )

            if not exchange:
                return {
                    'success': False,
                    'message': f'不支持的交易所: {exchange_name}'
                }

            # 获取账户信息测试连接
            balance = await exchange.fetch_balance()

            return {
                'success': True,
                'message': '连接成功',
                'exchange': exchange_name,
                'account_info': {
                    'total_balance': balance.get('total', {}),
                    'timestamp': datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"测试交易所连接失败: {exchange_name}, {e}")
            return {
                'success': False,
                'message': f'连接失败: {str(e)}',
                'exchange': exchange_name
            }

    @staticmethod
    async def get_exchange_balance(
        exchange_name: str,
        api_key: str,
        api_secret: str,
        passphrase: str = None,
        is_testnet: bool = False
    ) -> Dict:
        """
        获取交易所余额

        Args:
            exchange_name: 交易所名称
            api_key: API密钥
            api_secret: API密钥密钥
            passphrase: 密钥短语
            is_testnet: 是否使用测试网

        Returns:
            余额信息字典
        """
        try:
            exchange = ExchangeManager.create_exchange_instance(
                exchange_name=exchange_name,
                api_key=api_key,
                api_secret=api_secret,
                passphrase=passphrase,
                is_testnet=is_testnet
            )

            if not exchange:
                return {
                    'success': False,
                    'message': f'不支持的交易所: {exchange_name}'
                }

            # 获取余额
            balance = await exchange.fetch_balance()

            # 过滤出有余额的资产
            assets = []
            for asset, amount in balance.get('total', {}).items():
                if amount > 0:
                    free = balance.get('free', {}).get(asset, 0)
                    locked = balance.get('used', {}).get(asset, 0)
                    assets.append({
                        'asset': asset,
                        'total': amount,
                        'free': free,
                        'locked': locked
                    })

            return {
                'success': True,
                'exchange': exchange_name,
                'assets': assets,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"获取交易所余额失败: {exchange_name}, {e}")
            return {
                'success': False,
                'message': f'获取余额失败: {str(e)}',
                'exchange': exchange_name
            }

    @staticmethod
    def get_exchange_from_db(
        exchange_id: int,
        db: Session,
        encryption_manager: EncryptionManager
    ) -> Optional[ExchangeConfig]:
        """
        从数据库获取交易所配置

        Args:
            exchange_id: 交易所配置ID
            db: 数据库会话
            encryption_manager: 加密管理器

        Returns:
            交易所配置对象
        """
        try:
            exchange_config = db.query(ExchangeConfig).filter(
                ExchangeConfig.id == exchange_id
            ).first()

            if not exchange_config:
                logger.error(f"交易所配置不存在: {exchange_id}")
                return None

            return exchange_config

        except Exception as e:
            logger.error(f"获取交易所配置失败: {exchange_id}, {e}")
            return None

    @staticmethod
    def create_exchange_from_db(
        exchange_id: int,
        db: Session,
        encryption_manager: EncryptionManager
    ) -> Optional[ccxt.Exchange]:
        """
        从数据库创建交易所实例

        Args:
            exchange_id: 交易所配置ID
            db: 数据库会话
            encryption_manager: 加密管理器

        Returns:
            交易所实例
        """
        try:
            # 获取配置
            exchange_config = ExchangeManager.get_exchange_from_db(
                exchange_id=exchange_id,
                db=db,
                encryption_manager=encryption_manager
            )

            if not exchange_config:
                return None

            # 解密API密钥
            api_key = encryption_manager.decrypt(exchange_config.api_key)
            api_secret = encryption_manager.decrypt(exchange_config.api_secret)
            passphrase = None

            if exchange_config.passphrase:
                passphrase = encryption_manager.decrypt(exchange_config.passphrase)

            # 创建交易所实例
            exchange = ExchangeManager.create_exchange_instance(
                exchange_name=exchange_config.exchange_name,
                api_key=api_key,
                api_secret=api_secret,
                passphrase=passphrase,
                is_testnet=exchange_config.is_testnet
            )

            return exchange

        except Exception as e:
            logger.error(f"从数据库创建交易所实例失败: {exchange_id}, {e}")
            return None

    @staticmethod
    async def update_exchange_balances(
        user_id: int,
        db: Session,
        encryption_manager: EncryptionManager
    ) -> Dict:
        """
        更新用户所有交易所的余额

        Args:
            user_id: 用户ID
            db: 数据库会话
            encryption_manager: 加密管理器

        Returns:
            更新结果
        """
        try:
            # 获取用户所有启用的交易所配置
            exchange_configs = db.query(ExchangeConfig).filter(
                ExchangeConfig.user_id == user_id,
                ExchangeConfig.is_active == True
            ).all()

            results = []

            for config in exchange_configs:
                try:
                    # 创建交易所实例
                    exchange = ExchangeManager.create_exchange_from_db(
                        exchange_id=config.id,
                        db=db,
                        encryption_manager=encryption_manager
                    )

                    if not exchange:
                        continue

                    # 获取余额
                    balance = await exchange.fetch_balance()

                    # 更新数据库中的余额记录
                    for asset, total in balance.get('total', {}).items():
                        if total > 0:
                            # 查找或创建余额记录
                            balance_record = db.query(ExchangeBalance).filter(
                                ExchangeBalance.exchange_id == config.id,
                                ExchangeBalance.asset == asset
                            ).first()

                            if not balance_record:
                                balance_record = ExchangeBalance(
                                    user_id=user_id,
                                    exchange_id=config.id,
                                    asset=asset
                                )
                                db.add(balance_record)

                            # 更新余额
                            balance_record.free = balance.get('free', {}).get(asset, 0)
                            balance_record.locked = balance.get('used', {}).get(asset, 0)
                            balance_record.total = total

                    # 更新连接状态和时间
                    config.connection_status = "connected"
                    config.last_connected_at = datetime.now()

                    results.append({
                        'exchange_id': config.id,
                        'exchange_name': config.exchange_name,
                        'status': 'success'
                    })

                    db.commit()

                except Exception as e:
                    logger.error(f"更新交易所余额失败: {config.exchange_name}, {e}")
                    config.connection_status = "error"
                    results.append({
                        'exchange_id': config.id,
                        'exchange_name': config.exchange_name,
                        'status': 'error',
                        'message': str(e)
                    })

            return {
                'success': True,
                'results': results,
                'total': len(exchange_configs),
                'updated': len([r for r in results if r['status'] == 'success'])
            }

        except Exception as e:
            logger.error(f"更新交易所余额失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    @staticmethod
    def get_user_total_balance(
        user_id: int,
        db: Session
    ) -> Dict:
        """
        获取用户所有交易所的总余额

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            总余额信息
        """
        try:
            # 获取用户所有余额记录
            balances = db.query(ExchangeBalance).filter(
                ExchangeBalance.user_id == user_id
            ).all()

            # 按资产汇总
            asset_totals = {}

            for balance in balances:
                asset = balance.asset
                if asset not in asset_totals:
                    asset_totals[asset] = {
                        'total': 0.0,
                        'free': 0.0,
                        'locked': 0.0,
                        'exchanges': []
                    }

                asset_totals[asset]['total'] += balance.total
                asset_totals[asset]['free'] += balance.free
                asset_totals[asset]['locked'] += balance.locked
                asset_totals[asset]['exchanges'].append(balance.exchange_id)

            # 计算总价值（简化版，实际需要获取实时价格）
            total_usd = sum([v['total'] for k, v in asset_totals.items() if k in ['USDT', 'USDC', 'BUSD']])

            return {
                'success': True,
                'user_id': user_id,
                'assets': asset_totals,
                'total_usd': total_usd,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"获取用户总余额失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }
