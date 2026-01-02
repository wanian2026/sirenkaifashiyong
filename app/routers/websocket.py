"""
WebSocket API路由
提供实时数据推送功能
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from typing import Optional
from app.websocket import manager
from app.websocket import (
    market_overview_stream,
    bot_status_stream,
    market_data_stream,
    kline_data_stream,
    order_book_stream,
    trades_stream
)
from app.auth import get_current_user_ws

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    token: str = Query(..., description="JWT Token"),
    trading_pair: Optional[str] = Query(None, description="交易对"),
    timeframe: Optional[str] = Query(None, description="时间周期 (1m/5m/15m/1h/4h/1d)"),
    bot_id: Optional[int] = Query(None, description="机器人ID"),
    limit: Optional[int] = Query(20, description="数据数量限制")
):
    """
    WebSocket统一端点，支持多个频道的实时数据推送

    支持的频道:
    - market_overview: 市场概览（主要交易对的涨跌幅、成交量）
    - market_data: 市场数据（特定交易对的价格、24h涨跌幅等）
    - kline_data: K线数据（特定交易对和时间周期）
    - order_book: 深度数据（特定交易对的订单簿）
    - trades: 成交明细（特定交易对的成交记录）
    - bot_status: 机器人状态（特定机器人的实时状态）

    示例:
    - ws://localhost:8000/api/ws/market_overview?token=xxx
    - ws://localhost:8000/api/ws/market_data?token=xxx&trading_pair=BTC/USDT
    - ws://localhost:8000/api/ws/kline_data?token=xxx&trading_pair=BTC/USDT&timeframe=1h
    - ws://localhost:8000/api/ws/order_book?token=xxx&trading_pair=BTC/USDT&limit=20
    - ws://localhost:8000/api/ws/trades?token=xxx&trading_pair=BTC/USDT&limit=50
    - ws://localhost:8000/api/ws/bot_status?token=xxx&bot_id=1
    """
    # 验证用户身份
    try:
        user = await get_current_user_ws(token)
        user_id = user.id
    except Exception as e:
        await websocket.close(code=1008, reason="Invalid token")
        return

    # 接受WebSocket连接
    await manager.connect(user_id, websocket)

    try:
        # 根据频道路由到不同的数据流
        if channel == "market_overview":
            await market_overview_stream(websocket, user_id)

        elif channel == "market_data":
            if not trading_pair:
                await websocket.send_json({
                    "error": "trading_pair is required for market_data channel"
                })
                return
            await market_data_stream(trading_pair, websocket, user_id)

        elif channel == "kline_data":
            if not trading_pair:
                await websocket.send_json({
                    "error": "trading_pair is required for kline_data channel"
                })
                return
            timeframe = timeframe or '1h'
            await kline_data_stream(trading_pair, timeframe, websocket, user_id)

        elif channel == "order_book":
            if not trading_pair:
                await websocket.send_json({
                    "error": "trading_pair is required for order_book channel"
                })
                return
            await order_book_stream(trading_pair, limit, websocket, user_id)

        elif channel == "trades":
            if not trading_pair:
                await websocket.send_json({
                    "error": "trading_pair is required for trades channel"
                })
                return
            await trades_stream(trading_pair, limit, websocket, user_id)

        elif channel == "bot_status":
            if not bot_id:
                await websocket.send_json({
                    "error": "bot_id is required for bot_status channel"
                })
                return
            await bot_status_stream(bot_id, websocket, user_id)

        else:
            await websocket.send_json({
                "error": f"Unknown channel: {channel}"
            })

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(user_id, websocket)


@router.websocket("/ws/bot/{bot_id}")
async def websocket_bot_endpoint(
    websocket: WebSocket,
    bot_id: int,
    token: str = Query(..., description="JWT Token")
):
    """
    机器人专用WebSocket端点（简化版）

    自动订阅机器人的所有相关数据:
    - 机器人状态
    - 市场数据（交易对）
    - K线数据
    - 深度数据
    - 成交明细

    示例:
    - ws://localhost:8000/api/ws/bot/1?token=xxx
    """
    # 验证用户身份
    try:
        user = await get_current_user_ws(token)
        user_id = user.id
    except Exception as e:
        await websocket.close(code=1008, reason="Invalid token")
        return

    # 接受连接
    await manager.connect(user_id, websocket)

    try:
        from app.database import SessionLocal
        from app.models import TradingBot

        db = SessionLocal()
        bot = db.query(TradingBot).filter(TradingBot.id == bot_id).first()

        if not bot:
            await websocket.send_json({"error": "Bot not found"})
            return

        trading_pair = bot.trading_pair
        db.close()

        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected to bot {bot_id}",
            "trading_pair": trading_pair
        })

        # 订阅所有相关数据流（使用asyncio.gather并行执行）
        import asyncio
        await asyncio.gather(
            bot_status_stream(bot_id, websocket, user_id),
            market_data_stream(trading_pair, websocket, user_id),
            kline_data_stream(trading_pair, '1h', websocket, user_id),
            order_book_stream(trading_pair, 20, websocket, user_id),
            trades_stream(trading_pair, 50, websocket, user_id),
            return_exceptions=True
        )

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        print(f"WebSocket bot error: {e}")
        manager.disconnect(user_id, websocket)
