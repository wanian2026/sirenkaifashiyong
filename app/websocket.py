from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict, Optional
import json
import asyncio
from datetime import datetime
from app.routers.bots import running_bots
from app.models import User, TradingBot
from app.database import SessionLocal
from sqlalchemy.orm import Session


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.subscribers: Dict[str, Dict[int, List[WebSocket]]] = {
            'bot_status': {},
            'market_data': {},
            'kline_data': {},
            'order_book': {}
        }

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f"用户 {user_id} WebSocket 连接成功")

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # 从所有订阅中移除
        for channel in self.subscribers.values():
            for sub_id, connections in channel.items():
                if websocket in connections:
                    connections.remove(websocket)
                if not connections:
                    del channel[sub_id]

        print(f"用户 {user_id} WebSocket 断开连接")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)

            for connection in disconnected:
                self.disconnect(user_id, connection)

    async def broadcast(self, message: dict):
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except:
                    pass

    def subscribe(self, channel: str, sub_id: str, user_id: int, websocket: WebSocket):
        """订阅特定频道"""
        if channel not in self.subscribers:
            return

        if sub_id not in self.subscribers[channel]:
            self.subscribers[channel][sub_id] = {}

        if user_id not in self.subscribers[channel][sub_id]:
            self.subscribers[channel][sub_id][user_id] = []

        if websocket not in self.subscribers[channel][sub_id][user_id]:
            self.subscribers[channel][sub_id][user_id].append(websocket)

    async def send_to_subscribers(self, channel: str, sub_id: str, message: dict):
        """向订阅者发送消息"""
        if channel not in self.subscribers or sub_id not in self.subscribers[channel]:
            return

        disconnected_users = []

        for user_id, connections in self.subscribers[channel][sub_id].items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except:
                    if user_id not in disconnected_users:
                        disconnected_users.append(user_id)

        # 清理断开的连接
        for user_id in disconnected_users:
            if user_id in self.subscribers[channel][sub_id]:
                self.subscribers[channel][sub_id][user_id] = [
                    conn for conn in self.subscribers[channel][sub_id][user_id]
                    if conn in self.active_connections.get(user_id, [])
                ]
                if not self.subscribers[channel][sub_id][user_id]:
                    del self.subscribers[channel][sub_id][user_id]


manager = ConnectionManager()


async def bot_status_stream(bot_id: int, websocket: WebSocket, user_id: int):
    """机器人状态实时推送"""
    # 订阅机器人状态频道
    manager.subscribe('bot_status', str(bot_id), user_id, websocket)

    try:
        while True:
            if bot_id in running_bots:
                status = await running_bots[bot_id].get_strategy_status()
                message = {
                    "type": "bot_status",
                    "bot_id": bot_id,
                    "timestamp": datetime.now().isoformat(),
                    "data": status
                }
                await manager.send_to_subscribers('bot_status', str(bot_id), message)

            await asyncio.sleep(2)  # 每2秒推送一次

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, bot_id={bot_id}")
    except Exception as e:
        print(f"WebSocket错误: {e}")


async def market_data_stream(trading_pair: str, websocket: WebSocket, user_id: int):
    """市场数据实时推送（价格、24h涨跌幅等）"""
    # 订阅市场数据频道
    manager.subscribe('market_data', trading_pair, user_id, websocket)

    try:
        db = SessionLocal()
        bot = db.query(TradingBot).filter(
            TradingBot.trading_pair == trading_pair
        ).first()

        exchange_api = None
        if bot and bot.config:
            import json
            config = json.loads(bot.config)
            from app.exchange import ExchangeAPI
            exchange_api = ExchangeAPI(
                exchange_id=bot.exchange,
                api_key=config.get('api_key'),
                api_secret=config.get('api_secret')
            )

        db.close()

        while True:
            try:
                if exchange_api:
                    ticker = await exchange_api.get_ticker(trading_pair)
                    data = {
                        "price": ticker['last'],
                        "high": ticker['high'],
                        "low": ticker['low'],
                        "volume": ticker['baseVolume'],
                        "change": ticker['change'],
                        "percentage": ticker['percentage']
                    }
                else:
                    # 模拟数据
                    import random
                    price = 50000 + random.uniform(-200, 200)
                    data = {
                        "price": price,
                        "high": price * 1.01,
                        "low": price * 0.99,
                        "volume": random.uniform(1000, 10000),
                        "change": random.uniform(-100, 100),
                        "percentage": random.uniform(-2, 2)
                    }

                message = {
                    "type": "market_data",
                    "trading_pair": trading_pair,
                    "timestamp": datetime.now().isoformat(),
                    "data": data
                }

                await manager.send_to_subscribers('market_data', trading_pair, message)
                await asyncio.sleep(1)  # 每1秒推送一次

            except Exception as e:
                print(f"市场数据推送错误: {e}")
                await asyncio.sleep(5)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"WebSocket错误: {e}")


async def kline_data_stream(
    trading_pair: str,
    websocket: WebSocket,
    user_id: int,
    timeframe: str = '1h'
):
    """K线数据实时推送"""
    # 订阅K线数据频道
    sub_id = f"{trading_pair}_{timeframe}"
    manager.subscribe('kline_data', sub_id, user_id, websocket)

    try:
        db = SessionLocal()
        bot = db.query(TradingBot).filter(
            TradingBot.trading_pair == trading_pair
        ).first()

        strategy = None
        if bot and bot.id in running_bots:
            strategy = running_bots[bot.id]

        db.close()

        while True:
            try:
                if strategy:
                    kline_data = await strategy.get_kline_data(timeframe=timeframe, limit=100)
                else:
                    kline_data = []

                message = {
                    "type": "kline_data",
                    "trading_pair": trading_pair,
                    "timeframe": timeframe,
                    "timestamp": datetime.now().isoformat(),
                    "data": kline_data
                }

                await manager.send_to_subscribers('kline_data', sub_id, message)
                await asyncio.sleep(10)  # 每10秒推送一次（K线数据不需要太频繁）

            except Exception as e:
                print(f"K线数据推送错误: {e}")
                await asyncio.sleep(5)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"WebSocket错误: {e}")


async def order_book_stream(
    trading_pair: str,
    websocket: WebSocket,
    user_id: int
):
    """深度数据实时推送"""
    # 订阅深度数据频道
    manager.subscribe('order_book', trading_pair, user_id, websocket)

    try:
        db = SessionLocal()
        bot = db.query(TradingBot).filter(
            TradingBot.trading_pair == trading_pair
        ).first()

        strategy = None
        if bot and bot.id in running_bots:
            strategy = running_bots[bot.id]

        db.close()

        while True:
            try:
                if strategy:
                    order_book = await strategy.get_order_book_data(limit=20)
                else:
                    import random
                    base_price = 50000
                    order_book = {
                        'bids': [[base_price * (1 - (i + 1) * 0.0001), random.uniform(0.1, 10)] for i in range(20)],
                        'asks': [[base_price * (1 + (i + 1) * 0.0001), random.uniform(0.1, 10)] for i in range(20)],
                        'timestamp': int(datetime.now().timestamp() * 1000)
                    }

                message = {
                    "type": "order_book",
                    "trading_pair": trading_pair,
                    "timestamp": datetime.now().isoformat(),
                    "data": order_book
                }

                await manager.send_to_subscribers('order_book', trading_pair, message)
                await asyncio.sleep(2)  # 每2秒推送一次

            except Exception as e:
                print(f"深度数据推送错误: {e}")
                await asyncio.sleep(5)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"WebSocket错误: {e}")


async def trade_notification_stream(
    bot_id: int,
    websocket: WebSocket,
    user_id: int
):
    """交易通知实时推送"""
    try:
        while True:
            # 检查是否有新的交易记录
            db = SessionLocal()
            from app.models import Trade

            # 获取最近的交易
            recent_trade = db.query(Trade).filter(
                Trade.bot_id == bot_id
            ).order_by(Trade.created_at.desc()).first()

            if recent_trade:
                message = {
                    "type": "trade_notification",
                    "bot_id": bot_id,
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "trade_id": recent_trade.id,
                        "side": recent_trade.side,
                        "price": recent_trade.price,
                        "amount": recent_trade.amount,
                        "profit": recent_trade.profit,
                        "trading_pair": recent_trade.trading_pair
                    }
                }
                await websocket.send_json(message)

            db.close()
            await asyncio.sleep(5)  # 每5秒检查一次

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, bot_id={bot_id}")
    except Exception as e:
        print(f"WebSocket错误: {e}")
