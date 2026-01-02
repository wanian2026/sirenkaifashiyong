"""
交易所API路由
提供市场数据查询接口（基于真实交易所数据）
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.exchange import get_exchange_api
from app.config import settings
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter()

# 兼容性：如果连接失败，回退到模拟数据生成器
def generate_ticker_data(symbol: str) -> Dict:
    """生成模拟的行情数据"""
    base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 100
    price = base_price + random.uniform(-500, 500)

    return {
        "symbol": symbol,
        "last": price,
        "high": price * 1.02,
        "low": price * 0.98,
        "bid": price - random.uniform(0, 10),
        "ask": price + random.uniform(0, 10),
        "volume": random.uniform(1000, 10000),
        "quoteVolume": price * random.uniform(1000, 10000),
        "change": random.uniform(-5, 5),
        "percentage": random.uniform(-5, 5),
        "timestamp": int(datetime.now().timestamp() * 1000)
    }


def generate_orderbook_data(symbol: str, limit: int = 20) -> Dict:
    """生成模拟的深度数据"""
    base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 100

    # 生成买单（从当前价格向下）
    bids = []
    for i in range(limit):
        price = base_price - (i + 1) * random.uniform(0.5, 2)
        amount = random.uniform(0.1, 5)
        bids.append([price, amount])

    # 生成卖单（从当前价格向上）
    asks = []
    for i in range(limit):
        price = base_price + (i + 1) * random.uniform(0.5, 2)
        amount = random.uniform(0.1, 5)
        asks.append([price, amount])

    return {
        "symbol": symbol,
        "bids": bids,
        "asks": asks,
        "timestamp": int(datetime.now().timestamp() * 1000)
    }


def generate_ohlcv_data(symbol: str, timeframe: str, limit: int = 100) -> List[List]:
    """生成模拟的K线数据"""
    base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 100
    data = []

    now = int(datetime.now().timestamp() * 1000)

    # 时间周期对应的毫秒数
    timeframe_ms = {
        '1m': 60 * 1000,
        '5m': 5 * 60 * 1000,
        '15m': 15 * 60 * 1000,
        '1h': 60 * 60 * 1000,
        '4h': 4 * 60 * 60 * 1000,
        '1d': 24 * 60 * 60 * 1000
    }

    interval = timeframe_ms.get(timeframe, 60 * 60 * 1000)

    for i in range(limit):
        timestamp = now - (limit - i - 1) * interval

        # 生成OHLCV数据
        open_price = base_price + random.uniform(-100, 100)
        close_price = open_price + random.uniform(-20, 20)
        high_price = max(open_price, close_price) + random.uniform(0, 10)
        low_price = min(open_price, close_price) - random.uniform(0, 10)
        volume = random.uniform(100, 1000)

        data.append([timestamp, open_price, high_price, low_price, close_price, volume])

        base_price = close_price  # 下一根K线的基准价

    return data


def generate_trades_data(symbol: str, limit: int = 50) -> List[Dict]:
    """生成模拟的成交记录"""
    base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 100
    trades = []

    now = int(datetime.now().timestamp() * 1000)

    for i in range(limit):
        timestamp = now - random.uniform(0, 60000) * 1000
        price = base_price + random.uniform(-50, 50)
        amount = random.uniform(0.01, 2)
        side = 'buy' if random.random() > 0.5 else 'sell'

        trades.append({
            "id": str(int(timestamp)),
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp / 1000).isoformat(),
            "symbol": symbol,
            "order": None,
            "type": "market",
            "side": side,
            "price": price,
            "amount": amount,
            "cost": price * amount,
            "fee": {
                "cost": price * amount * 0.001,
                "currency": "USDT"
            }
        })

    return sorted(trades, key=lambda x: x['timestamp'], reverse=True)[:limit]


@router.get("/ticker")
async def get_ticker(
    symbol: str = Query(..., description="交易对，如 BTC/USDT")
):
    """
    获取行情信息

    Args:
        symbol: 交易对

    Returns:
        行情数据（包含最新价、24h最高最低、成交量等）
    """
    try:
        logger.info(f"获取行情: {symbol}")

        # 尝试从真实交易所获取数据
        try:
            exchange_api = get_exchange_api()
            data = await exchange_api.get_ticker(symbol)
            return {
                "success": True,
                "data": data,
                "source": "real"
            }
        except Exception as e:
            logger.warning(f"从真实交易所获取数据失败，使用模拟数据: {e}")
            # 回退到模拟数据
            data = generate_ticker_data(symbol)
            return {
                "success": True,
                "data": data,
                "source": "simulated",
                "warning": "当前使用模拟数据，请检查交易所配置"
            }
    except Exception as e:
        logger.error(f"获取行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orderbook")
async def get_orderbook(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    limit: int = Query(20, ge=5, le=100, description="深度数量")
):
    """
    获取深度数据

    Args:
        symbol: 交易对
        limit: 深度数量（买单和卖单各N档）

    Returns:
        深度数据（包含买单和卖单）
    """
    try:
        logger.info(f"获取深度数据: {symbol}, limit={limit}")

        # 尝试从真实交易所获取数据
        try:
            exchange_api = get_exchange_api()
            data = await exchange_api.get_orderbook(symbol, limit)
            return {
                "success": True,
                "data": data,
                "source": "real"
            }
        except Exception as e:
            logger.warning(f"从真实交易所获取数据失败，使用模拟数据: {e}")
            # 回退到模拟数据
            data = generate_orderbook_data(symbol, limit)

            # 计算累计量用于深度条
            total_bid_volume = sum([bid[1] for bid in data['bids']])
            total_ask_volume = sum([ask[1] for ask in data['asks']])

            return {
                "success": True,
                "data": {
                    "symbol": symbol,
                    "bids": [
                        {
                            "price": bid[0],
                            "amount": bid[1],
                            "total": sum([b[1] for b in data['bids'][:i+1]]),
                            "total_percent": (sum([b[1] for b in data['bids'][:i+1]]) / total_bid_volume * 100) if total_bid_volume > 0 else 0
                        }
                        for i, bid in enumerate(data['bids'])
                    ],
                    "asks": [
                        {
                            "price": ask[0],
                            "amount": ask[1],
                            "total": sum([a[1] for a in data['asks'][:i+1]]),
                            "total_percent": (sum([a[1] for a in data['asks'][:i+1]]) / total_ask_volume * 100) if total_ask_volume > 0 else 0
                        }
                        for i, ask in enumerate(data['asks'])
                    ],
                    "timestamp": data['timestamp']
                },
                "source": "simulated",
                "warning": "当前使用模拟数据，请检查交易所配置"
            }
    except Exception as e:
        logger.error(f"获取深度数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ohlcv")
async def get_ohlcv(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str = Query('1h', description="时间周期: 1m, 5m, 15m, 1h, 4h, 1d"),
    limit: int = Query(100, ge=10, le=1000, description="K线数量")
):
    """
    获取K线数据

    Args:
        symbol: 交易对
        timeframe: 时间周期（1m, 5m, 15m, 1h, 4h, 1d）
        limit: K线数量

    Returns:
        K线数据列表 [[timestamp, open, high, low, close, volume], ...]
    """
    try:
        logger.info(f"获取K线数据: {symbol}, timeframe={timeframe}, limit={limit}")

        # 尝试从真实交易所获取数据
        try:
            exchange_api = get_exchange_api()
            data = await exchange_api.get_ohlcv(symbol, timeframe, limit)
            return {
                "success": True,
                "data": data,
                "source": "real"
            }
        except Exception as e:
            logger.warning(f"从真实交易所获取数据失败，使用模拟数据: {e}")
            # 回退到模拟数据
            data = generate_ohlcv_data(symbol, timeframe, limit)
            return {
                "success": True,
                "data": data,
                "source": "simulated",
                "warning": "当前使用模拟数据，请检查交易所配置"
            }
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades")
async def get_trades(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    limit: int = Query(50, ge=10, le=200, description="成交记录数量")
):
    """
    获取成交记录

    Args:
        symbol: 交易对
        limit: 成交记录数量

    Returns:
        成交记录列表
    """
    try:
        logger.info(f"获取成交记录: {symbol}, limit={limit}")

        # 尝试从真实交易所获取数据
        try:
            exchange_api = get_exchange_api()
            data = await exchange_api.get_trades(symbol, limit)
            return {
                "success": True,
                "data": data,
                "source": "real"
            }
        except Exception as e:
            logger.warning(f"从真实交易所获取数据失败，使用模拟数据: {e}")
            # 回退到模拟数据
            data = generate_trades_data(symbol, limit)
            return {
                "success": True,
                "data": data,
                "source": "simulated",
                "warning": "当前使用模拟数据，请检查交易所配置"
            }
    except Exception as e:
        logger.error(f"获取成交记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pairs")
async def get_supported_pairs():
    """
    获取支持的交易对列表

    Returns:
        交易对列表
    """
    try:
        # 尝试从真实交易所获取数据
        try:
            exchange_api = get_exchange_api()
            data = await exchange_api.get_pairs()
            return {
                "success": True,
                "data": data,
                "source": "real"
            }
        except Exception as e:
            logger.warning(f"从真实交易所获取数据失败，使用默认交易对: {e}")
            # 回退到默认交易对
            pairs = [
                {"symbol": "BTC/USDT", "name": "Bitcoin", "base": "BTC", "quote": "USDT"},
                {"symbol": "ETH/USDT", "name": "Ethereum", "base": "ETH", "quote": "USDT"},
                {"symbol": "BNB/USDT", "name": "Binance Coin", "base": "BNB", "quote": "USDT"},
                {"symbol": "SOL/USDT", "name": "Solana", "base": "SOL", "quote": "USDT"},
                {"symbol": "XRP/USDT", "name": "Ripple", "base": "XRP", "quote": "USDT"},
            ]
            return {
                "success": True,
                "data": pairs,
                "source": "simulated",
                "warning": "当前使用默认交易对，请检查交易所配置"
            }
    except Exception as e:
        logger.error(f"获取交易对列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/24h-stats")
async def get_24h_stats(
    symbol: str = Query(..., description="交易对，如 BTC/USDT")
):
    """
    获取24小时统计数据

    Args:
        symbol: 交易对

    Returns:
        24小时统计数据（最高、最低、成交量、成交额）
    """
    try:
        # 尝试从真实交易所获取数据
        try:
            exchange_api = get_exchange_api()
            data = await exchange_api.get_24h_stats(symbol)
            return {
                "success": True,
                "data": data,
                "source": "real"
            }
        except Exception as e:
            logger.warning(f"从真实交易所获取数据失败，使用模拟数据: {e}")
            # 回退到模拟数据
            ticker = generate_ticker_data(symbol)
            stats = {
                "symbol": symbol,
                "high": ticker['high'],
                "low": ticker['low'],
                "volume": ticker['volume'],
                "quoteVolume": ticker['quoteVolume'],
                "change": ticker['change'],
                "changePercent": ticker['percentage'],
                "open": ticker['low'] / 0.98,  # 估算开盘价
                "close": ticker['last'],
                "timestamp": ticker['timestamp']
            }
            return {
                "success": True,
                "data": stats,
                "source": "simulated",
                "warning": "当前使用模拟数据，请检查交易所配置"
            }
    except Exception as e:
        logger.error(f"获取24小时统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-connection")
async def test_connection():
    """
    测试交易所连接

    Returns:
        连接状态信息
    """
    try:
        exchange_api = get_exchange_api()
        result = await exchange_api.test_connection()
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"测试连接失败: {e}")
        return {
            "success": False,
            "data": {
                "exchange": settings.EXCHANGE_ID,
                "error": str(e),
                "message": "连接失败"
            }
        }

