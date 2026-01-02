from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict
import json
import asyncio
from app.routers.bots import running_bots
from app.models import User
from app.database import SessionLocal


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

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


manager = ConnectionManager()


async def bot_status_stream(bot_id: int, websocket: WebSocket, user_id: int):
    """机器人状态实时推送"""
    try:
        while True:
            if bot_id in running_bots:
                status = await running_bots[bot_id].get_strategy_status()
                message = {
                    "type": "bot_status",
                    "bot_id": bot_id,
                    "data": status
                }
                await websocket.send_json(message)

            await asyncio.sleep(2)  # 每2秒推送一次

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, bot_id={bot_id}")
    except Exception as e:
        print(f"WebSocket错误: {e}")


async def market_data_stream(trading_pair: str, websocket: WebSocket, user_id: int):
    """市场数据实时推送"""
    try:
        while True:
            # 模拟市场数据更新
            import random
            price = 50000 + random.uniform(-100, 100)

            message = {
                "type": "market_data",
                "trading_pair": trading_pair,
                "data": {
                    "price": price,
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                }
            }

            await websocket.send_json(message)
            await asyncio.sleep(1)  # 每1秒推送一次

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"WebSocket错误: {e}")
