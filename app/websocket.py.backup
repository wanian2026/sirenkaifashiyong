from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict, Optional
import json
import asyncio
from datetime import datetime
from app.routers.bots import running_bots
from app.models import User, TradingBot
from app.database import SessionLocal
from app.exchange import ExchangeAPI
from sqlalchemy.orm import Session


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.subscribers: Dict[str, Dict[int, List[WebSocket]]] = {
            'bot_status': {},
            'market_data': {},
            'kline_data': {},
            'order_book': {},
            'trades': {},
            'market_overview': {}
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

    def unsubscribe(self, channel: str, sub_id: str, user_id: int, websocket: WebSocket):
        """取消订阅特定频道"""
        if channel not in self.subscribers or sub_id not in self.subscribers[channel]:
            return

        if user_id in self.subscribers[channel][sub_id]:
            if websocket in self.subscribers[channel][sub_id][user_id]:
                self.subscribers[channel][sub_id][user_id].remove(websocket)

            # 如果用户没有其他连接，删除用户记录
            if not self.subscribers[channel][sub_id][user_id]:
                del self.subscribers[channel][sub_id][user_id]

            # 如果没有订阅者，删除频道
            if not self.subscribers[channel][sub_id]:
                del self.subscribers[channel][sub_id]

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


async def market_overview_stream(websocket: WebSocket, user_id: int):
    """
    市场概览数据实时推送（主要交易对的涨跌幅、成交量等）

    Args:
        websocket: WebSocket连接
        user_id: 用户ID
    """
    # 订阅市场概览频道
    manager.subscribe('market_overview', 'global', user_id, websocket)

    try:
        db = SessionLocal()

        # 获取所有活跃的机器人，收集交易对
        bots = db.query(TradingBot).filter(TradingBot.status == 'running').all()

        exchange_apis = {}
        trading_pairs = set()

        for bot in bots:
            trading_pairs.add(bot.trading_pair)

            if bot.config:
                config = json.loads(bot.config)
                exchange_api = ExchangeAPI(
                    exchange_id=bot.exchange,
                    api_key=config.get('api_key'),
                    api_secret=config.get('api_secret')
                )
                exchange_apis[bot.trading_pair] = exchange_api

        # 如果没有机器人，使用默认交易对
        if not trading_pairs:
            trading_pairs = {'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT'}

        db.close()

        while True:
            try:
                market_data = []

                for trading_pair in trading_pairs:
                    try:
                        exchange_api = exchange_apis.get(trading_pair)

                        if exchange_api:
                            ticker = await exchange_api.get_ticker(trading_pair)
                            data = {
                                "symbol": trading_pair,
                                "price": ticker['last'],
                                "change": ticker['change'],
                                "percentage": ticker['percentage'],
                                "volume": ticker['baseVolume'],
                                "quoteVolume": ticker['quoteVolume'],
                                "high": ticker['high'],
                                "low": ticker['low']
                            }
                        else:
                            # 模拟数据
                            import random
                            base_price = 50000 if 'BTC' in trading_pair else 3000 if 'ETH' in trading_pair else 100
                            price = base_price + random.uniform(-500, 500)
                            change = random.uniform(-200, 200)
                            percentage = (change / base_price) * 100

                            data = {
                                "symbol": trading_pair,
                                "price": price,
                                "change": change,
                                "percentage": percentage,
                                "volume": random.uniform(1000, 10000),
                                "quoteVolume": price * random.uniform(1000, 10000),
                                "high": price * 1.01,
                                "low": price * 0.99
                            }

                        market_data.append(data)

                    except Exception as e:
                        print(f"获取 {trading_pair} 数据失败: {e}")
                        continue

                # 计算市场概览统计
                total_volume = sum(item['quoteVolume'] for item in market_data)
                gainers = [item for item in market_data if item['percentage'] > 0]
                losers = [item for item in market_data if item['percentage'] < 0]
                avg_change = sum(item['percentage'] for item in market_data) / len(market_data) if market_data else 0

                overview = {
                    "type": "market_overview",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "market_data": market_data,
                        "summary": {
                            "total_pairs": len(market_data),
                            "gainers": len(gainers),
                            "losers": len(losers),
                            "avg_change": round(avg_change, 2),
                            "total_volume": round(total_volume, 2)
                        }
                    }
                }

                await manager.send_to_subscribers('market_overview', 'global', overview)
                await asyncio.sleep(3)  # 每3秒推送一次

            except Exception as e:
                print(f"市场概览推送错误: {e}")
                await asyncio.sleep(10)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}")
    except Exception as e:
        print(f"市场概览流错误: {e}")


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


async def kline_data_stream(
    trading_pair: str,
    timeframe: str = '1h',
    websocket: WebSocket = None,
    user_id: int = None
):
    """
    K线数据实时推送

    Args:
        trading_pair: 交易对 (如 BTC/USDT)
        timeframe: 时间周期 (1m/5m/15m/1h/4h/1d)
        websocket: WebSocket连接
        user_id: 用户ID
    """
    # 订阅K线数据频道
    channel_key = f"{trading_pair}:{timeframe}"
    if websocket and user_id:
        manager.subscribe('kline_data', channel_key, user_id, websocket)

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

        # 上一次的K线数据，用于判断是否更新
        last_kline = None

        while True:
            try:
                if exchange_api:
                    ohlcv = await exchange_api.get_ohlcv(trading_pair, timeframe, limit=1)

                    if ohlcv:
                        current_kline = ohlcv[0]

                        # 只有当K线更新时才推送
                        if last_kline is None or current_kline[0] != last_kline[0]:
                            data = {
                                "symbol": trading_pair,
                                "timeframe": timeframe,
                                "timestamp": current_kline[0],
                                "open": current_kline[1],
                                "high": current_kline[2],
                                "low": current_kline[3],
                                "close": current_kline[4],
                                "volume": current_kline[5]
                            }

                            message = {
                                "type": "kline_data",
                                "trading_pair": trading_pair,
                                "timeframe": timeframe,
                                "timestamp": datetime.now().isoformat(),
                                "data": data
                            }

                            await manager.send_to_subscribers('kline_data', channel_key, message)
                            last_kline = current_kline
                else:
                    # 模拟数据（每5秒生成一次新K线）
                    import random
                    if last_kline is None:
                        price = 50000
                        last_kline = [
                            int(datetime.now().timestamp() * 1000),
                            price, price * 1.01, price * 0.99, price, random.uniform(100, 1000)
                        ]
                    else:
                        # 更新K线
                        last_kline[4] += random.uniform(-100, 100)  # close price
                        last_kline[2] = max(last_kline[2], last_kline[4])  # high
                        last_kline[3] = min(last_kline[3], last_kline[4])  # low
                        last_kline[5] += random.uniform(10, 50)  # volume

                    data = {
                        "symbol": trading_pair,
                        "timeframe": timeframe,
                        "timestamp": last_kline[0],
                        "open": last_kline[1],
                        "high": last_kline[2],
                        "low": last_kline[3],
                        "close": last_kline[4],
                        "volume": last_kline[5]
                    }

                    message = {
                        "type": "kline_data",
                        "trading_pair": trading_pair,
                        "timeframe": timeframe,
                        "timestamp": datetime.now().isoformat(),
                        "data": data
                    }

                    await manager.send_to_subscribers('kline_data', channel_key, message)

                await asyncio.sleep(5)  # 每5秒检查一次

            except Exception as e:
                print(f"K线数据推送错误: {e}")
                await asyncio.sleep(10)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"K线数据流错误: {e}")


async def order_book_stream(
    trading_pair: str,
    limit: int = 20,
    websocket: WebSocket = None,
    user_id: int = None
):
    """
    深度数据实时推送

    Args:
        trading_pair: 交易对
        limit: 深度数量
        websocket: WebSocket连接
        user_id: 用户ID
    """
    # 订阅深度数据频道
    channel_key = f"{trading_pair}:{limit}"
    if websocket and user_id:
        manager.subscribe('order_book', channel_key, user_id, websocket)

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
                    orderbook = await exchange_api.get_orderbook(trading_pair, limit)

                    message = {
                        "type": "order_book",
                        "trading_pair": trading_pair,
                        "limit": limit,
                        "timestamp": datetime.now().isoformat(),
                        "data": orderbook
                    }

                    await manager.send_to_subscribers('order_book', channel_key, message)
                else:
                    # 模拟数据
                    import random
                    base_price = 50000 + random.uniform(-50, 50)

                    bids = []
                    asks = []
                    for i in range(limit):
                        bid_price = base_price - (i + 1) * random.uniform(0.5, 2)
                        ask_price = base_price + (i + 1) * random.uniform(0.5, 2)
                        bids.append([bid_price, random.uniform(0.1, 5)])
                        asks.append([ask_price, random.uniform(0.1, 5)])

                    data = {
                        "bids": bids,
                        "asks": asks
                    }

                    message = {
                        "type": "order_book",
                        "trading_pair": trading_pair,
                        "limit": limit,
                        "timestamp": datetime.now().isoformat(),
                        "data": data
                    }

                    await manager.send_to_subscribers('order_book', channel_key, message)

                await asyncio.sleep(2)  # 每2秒推送一次

            except Exception as e:
                print(f"深度数据推送错误: {e}")
                await asyncio.sleep(5)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"深度数据流错误: {e}")


async def trades_stream(
    trading_pair: str,
    limit: int = 50,
    websocket: WebSocket = None,
    user_id: int = None
):
    """
    成交明细实时推送

    Args:
        trading_pair: 交易对
        limit: 成交记录数量
        websocket: WebSocket连接
        user_id: 用户ID
    """
    # 订阅成交数据频道
    channel_key = f"{trading_pair}:trades"
    if websocket and user_id:
        manager.subscribe('trades', channel_key, user_id, websocket)

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

        # 记录上次推送的交易ID，避免重复推送
        last_trade_ids = set()

        while True:
            try:
                if exchange_api:
                    trades = await exchange_api.get_trades(trading_pair, limit)

                    # 过滤出新交易
                    new_trades = [
                        trade for trade in trades
                        if trade['id'] not in last_trade_ids
                    ]

                    if new_trades:
                        # 更新已推送的交易ID
                        for trade in new_trades:
                            last_trade_ids.add(trade['id'])

                        # 只保留最近的100个交易ID，避免内存无限增长
                        if len(last_trade_ids) > 100:
                            last_trade_ids = set(list(last_trade_ids)[-100:])

                        message = {
                            "type": "trades",
                            "trading_pair": trading_pair,
                            "timestamp": datetime.now().isoformat(),
                            "data": new_trades
                        }

                        await manager.send_to_subscribers('trades', channel_key, message)
                else:
                    # 模拟数据（随机生成交易）
                    import random
                    new_trade = {
                        "id": str(int(datetime.now().timestamp() * 1000)),
                        "timestamp": int(datetime.now().timestamp() * 1000),
                        "datetime": datetime.now().isoformat(),
                        "symbol": trading_pair,
                        "side": 'buy' if random.random() > 0.5 else 'sell',
                        "price": 50000 + random.uniform(-50, 50),
                        "amount": random.uniform(0.01, 2),
                        "cost": 0,
                        "fee": {
                            "cost": 0,
                            "currency": "USDT"
                        }
                    }
                    new_trade['cost'] = new_trade['price'] * new_trade['amount']
                    new_trade['fee']['cost'] = new_trade['cost'] * 0.001

                    message = {
                        "type": "trades",
                        "trading_pair": trading_pair,
                        "timestamp": datetime.now().isoformat(),
                        "data": [new_trade]
                    }

                    await manager.send_to_subscribers('trades', channel_key, message)

                await asyncio.sleep(3)  # 每3秒检查一次

            except Exception as e:
                print(f"成交数据推送错误: {e}")
                await asyncio.sleep(5)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"成交数据流错误: {e}")
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


async def kline_data_stream(
    trading_pair: str,
    timeframe: str = '1h',
    websocket: WebSocket = None,
    user_id: int = None
):
    """
    K线数据实时推送

    Args:
        trading_pair: 交易对 (如 BTC/USDT)
        timeframe: 时间周期 (1m/5m/15m/1h/4h/1d)
        websocket: WebSocket连接
        user_id: 用户ID
    """
    # 订阅K线数据频道
    channel_key = f"{trading_pair}:{timeframe}"
    if websocket and user_id:
        manager.subscribe('kline_data', channel_key, user_id, websocket)

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

        # 上一次的K线数据，用于判断是否更新
        last_kline = None

        while True:
            try:
                if exchange_api:
                    ohlcv = await exchange_api.get_ohlcv(trading_pair, timeframe, limit=1)

                    if ohlcv:
                        current_kline = ohlcv[0]

                        # 只有当K线更新时才推送
                        if last_kline is None or current_kline[0] != last_kline[0]:
                            data = {
                                "symbol": trading_pair,
                                "timeframe": timeframe,
                                "timestamp": current_kline[0],
                                "open": current_kline[1],
                                "high": current_kline[2],
                                "low": current_kline[3],
                                "close": current_kline[4],
                                "volume": current_kline[5]
                            }

                            message = {
                                "type": "kline_data",
                                "trading_pair": trading_pair,
                                "timeframe": timeframe,
                                "timestamp": datetime.now().isoformat(),
                                "data": data
                            }

                            await manager.send_to_subscribers('kline_data', channel_key, message)
                            last_kline = current_kline
                else:
                    # 模拟数据（每5秒生成一次新K线）
                    import random
                    if last_kline is None:
                        price = 50000
                        last_kline = [
                            int(datetime.now().timestamp() * 1000),
                            price, price * 1.01, price * 0.99, price, random.uniform(100, 1000)
                        ]
                    else:
                        # 更新K线
                        last_kline[4] += random.uniform(-100, 100)  # close price
                        last_kline[2] = max(last_kline[2], last_kline[4])  # high
                        last_kline[3] = min(last_kline[3], last_kline[4])  # low
                        last_kline[5] += random.uniform(10, 50)  # volume

                    data = {
                        "symbol": trading_pair,
                        "timeframe": timeframe,
                        "timestamp": last_kline[0],
                        "open": last_kline[1],
                        "high": last_kline[2],
                        "low": last_kline[3],
                        "close": last_kline[4],
                        "volume": last_kline[5]
                    }

                    message = {
                        "type": "kline_data",
                        "trading_pair": trading_pair,
                        "timeframe": timeframe,
                        "timestamp": datetime.now().isoformat(),
                        "data": data
                    }

                    await manager.send_to_subscribers('kline_data', channel_key, message)

                await asyncio.sleep(5)  # 每5秒检查一次

            except Exception as e:
                print(f"K线数据推送错误: {e}")
                await asyncio.sleep(10)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"K线数据流错误: {e}")


async def order_book_stream(
    trading_pair: str,
    limit: int = 20,
    websocket: WebSocket = None,
    user_id: int = None
):
    """
    深度数据实时推送

    Args:
        trading_pair: 交易对
        limit: 深度数量
        websocket: WebSocket连接
        user_id: 用户ID
    """
    # 订阅深度数据频道
    channel_key = f"{trading_pair}:{limit}"
    if websocket and user_id:
        manager.subscribe('order_book', channel_key, user_id, websocket)

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
                    orderbook = await exchange_api.get_orderbook(trading_pair, limit)

                    message = {
                        "type": "order_book",
                        "trading_pair": trading_pair,
                        "limit": limit,
                        "timestamp": datetime.now().isoformat(),
                        "data": orderbook
                    }

                    await manager.send_to_subscribers('order_book', channel_key, message)
                else:
                    # 模拟数据
                    import random
                    base_price = 50000 + random.uniform(-50, 50)

                    bids = []
                    asks = []
                    for i in range(limit):
                        bid_price = base_price - (i + 1) * random.uniform(0.5, 2)
                        ask_price = base_price + (i + 1) * random.uniform(0.5, 2)
                        bids.append([bid_price, random.uniform(0.1, 5)])
                        asks.append([ask_price, random.uniform(0.1, 5)])

                    data = {
                        "bids": bids,
                        "asks": asks
                    }

                    message = {
                        "type": "order_book",
                        "trading_pair": trading_pair,
                        "limit": limit,
                        "timestamp": datetime.now().isoformat(),
                        "data": data
                    }

                    await manager.send_to_subscribers('order_book', channel_key, message)

                await asyncio.sleep(2)  # 每2秒推送一次

            except Exception as e:
                print(f"深度数据推送错误: {e}")
                await asyncio.sleep(5)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"深度数据流错误: {e}")


async def trades_stream(
    trading_pair: str,
    limit: int = 50,
    websocket: WebSocket = None,
    user_id: int = None
):
    """
    成交明细实时推送

    Args:
        trading_pair: 交易对
        limit: 成交记录数量
        websocket: WebSocket连接
        user_id: 用户ID
    """
    # 订阅成交数据频道
    channel_key = f"{trading_pair}:trades"
    if websocket and user_id:
        manager.subscribe('trades', channel_key, user_id, websocket)

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

        # 记录上次推送的交易ID，避免重复推送
        last_trade_ids = set()

        while True:
            try:
                if exchange_api:
                    trades = await exchange_api.get_trades(trading_pair, limit)

                    # 过滤出新交易
                    new_trades = [
                        trade for trade in trades
                        if trade['id'] not in last_trade_ids
                    ]

                    if new_trades:
                        # 更新已推送的交易ID
                        for trade in new_trades:
                            last_trade_ids.add(trade['id'])

                        # 只保留最近的100个交易ID，避免内存无限增长
                        if len(last_trade_ids) > 100:
                            last_trade_ids = set(list(last_trade_ids)[-100:])

                        message = {
                            "type": "trades",
                            "trading_pair": trading_pair,
                            "timestamp": datetime.now().isoformat(),
                            "data": new_trades
                        }

                        await manager.send_to_subscribers('trades', channel_key, message)
                else:
                    # 模拟数据（随机生成交易）
                    import random
                    new_trade = {
                        "id": str(int(datetime.now().timestamp() * 1000)),
                        "timestamp": int(datetime.now().timestamp() * 1000),
                        "datetime": datetime.now().isoformat(),
                        "symbol": trading_pair,
                        "side": 'buy' if random.random() > 0.5 else 'sell',
                        "price": 50000 + random.uniform(-50, 50),
                        "amount": random.uniform(0.01, 2),
                        "cost": 0,
                        "fee": {
                            "cost": 0,
                            "currency": "USDT"
                        }
                    }
                    new_trade['cost'] = new_trade['price'] * new_trade['amount']
                    new_trade['fee']['cost'] = new_trade['cost'] * 0.001

                    message = {
                        "type": "trades",
                        "trading_pair": trading_pair,
                        "timestamp": datetime.now().isoformat(),
                        "data": [new_trade]
                    }

                    await manager.send_to_subscribers('trades', channel_key, message)

                await asyncio.sleep(3)  # 每3秒检查一次

            except Exception as e:
                print(f"成交数据推送错误: {e}")
                await asyncio.sleep(5)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"成交数据流错误: {e}")
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


async def kline_data_stream(
    trading_pair: str,
    timeframe: str = '1h',
    websocket: WebSocket = None,
    user_id: int = None
):
    """
    K线数据实时推送

    Args:
        trading_pair: 交易对 (如 BTC/USDT)
        timeframe: 时间周期 (1m/5m/15m/1h/4h/1d)
        websocket: WebSocket连接
        user_id: 用户ID
    """
    # 订阅K线数据频道
    channel_key = f"{trading_pair}:{timeframe}"
    if websocket and user_id:
        manager.subscribe('kline_data', channel_key, user_id, websocket)

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

        # 上一次的K线数据，用于判断是否更新
        last_kline = None

        while True:
            try:
                if exchange_api:
                    ohlcv = await exchange_api.get_ohlcv(trading_pair, timeframe, limit=1)

                    if ohlcv:
                        current_kline = ohlcv[0]

                        # 只有当K线更新时才推送
                        if last_kline is None or current_kline[0] != last_kline[0]:
                            data = {
                                "symbol": trading_pair,
                                "timeframe": timeframe,
                                "timestamp": current_kline[0],
                                "open": current_kline[1],
                                "high": current_kline[2],
                                "low": current_kline[3],
                                "close": current_kline[4],
                                "volume": current_kline[5]
                            }

                            message = {
                                "type": "kline_data",
                                "trading_pair": trading_pair,
                                "timeframe": timeframe,
                                "timestamp": datetime.now().isoformat(),
                                "data": data
                            }

                            await manager.send_to_subscribers('kline_data', channel_key, message)
                            last_kline = current_kline
                else:
                    # 模拟数据（每5秒生成一次新K线）
                    import random
                    if last_kline is None:
                        price = 50000
                        last_kline = [
                            int(datetime.now().timestamp() * 1000),
                            price, price * 1.01, price * 0.99, price, random.uniform(100, 1000)
                        ]
                    else:
                        # 更新K线
                        last_kline[4] += random.uniform(-100, 100)  # close price
                        last_kline[2] = max(last_kline[2], last_kline[4])  # high
                        last_kline[3] = min(last_kline[3], last_kline[4])  # low
                        last_kline[5] += random.uniform(10, 50)  # volume

                    data = {
                        "symbol": trading_pair,
                        "timeframe": timeframe,
                        "timestamp": last_kline[0],
                        "open": last_kline[1],
                        "high": last_kline[2],
                        "low": last_kline[3],
                        "close": last_kline[4],
                        "volume": last_kline[5]
                    }

                    message = {
                        "type": "kline_data",
                        "trading_pair": trading_pair,
                        "timeframe": timeframe,
                        "timestamp": datetime.now().isoformat(),
                        "data": data
                    }

                    await manager.send_to_subscribers('kline_data', channel_key, message)

                await asyncio.sleep(5)  # 每5秒检查一次

            except Exception as e:
                print(f"K线数据推送错误: {e}")
                await asyncio.sleep(10)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"K线数据流错误: {e}")


async def order_book_stream(
    trading_pair: str,
    limit: int = 20,
    websocket: WebSocket = None,
    user_id: int = None
):
    """
    深度数据实时推送

    Args:
        trading_pair: 交易对
        limit: 深度数量
        websocket: WebSocket连接
        user_id: 用户ID
    """
    # 订阅深度数据频道
    channel_key = f"{trading_pair}:{limit}"
    if websocket and user_id:
        manager.subscribe('order_book', channel_key, user_id, websocket)

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
                    orderbook = await exchange_api.get_orderbook(trading_pair, limit)

                    message = {
                        "type": "order_book",
                        "trading_pair": trading_pair,
                        "limit": limit,
                        "timestamp": datetime.now().isoformat(),
                        "data": orderbook
                    }

                    await manager.send_to_subscribers('order_book', channel_key, message)
                else:
                    # 模拟数据
                    import random
                    base_price = 50000 + random.uniform(-50, 50)

                    bids = []
                    asks = []
                    for i in range(limit):
                        bid_price = base_price - (i + 1) * random.uniform(0.5, 2)
                        ask_price = base_price + (i + 1) * random.uniform(0.5, 2)
                        bids.append([bid_price, random.uniform(0.1, 5)])
                        asks.append([ask_price, random.uniform(0.1, 5)])

                    data = {
                        "bids": bids,
                        "asks": asks
                    }

                    message = {
                        "type": "order_book",
                        "trading_pair": trading_pair,
                        "limit": limit,
                        "timestamp": datetime.now().isoformat(),
                        "data": data
                    }

                    await manager.send_to_subscribers('order_book', channel_key, message)

                await asyncio.sleep(2)  # 每2秒推送一次

            except Exception as e:
                print(f"深度数据推送错误: {e}")
                await asyncio.sleep(5)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"深度数据流错误: {e}")


async def trades_stream(
    trading_pair: str,
    limit: int = 50,
    websocket: WebSocket = None,
    user_id: int = None
):
    """
    成交明细实时推送

    Args:
        trading_pair: 交易对
        limit: 成交记录数量
        websocket: WebSocket连接
        user_id: 用户ID
    """
    # 订阅成交数据频道
    channel_key = f"{trading_pair}:trades"
    if websocket and user_id:
        manager.subscribe('trades', channel_key, user_id, websocket)

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

        # 记录上次推送的交易ID，避免重复推送
        last_trade_ids = set()

        while True:
            try:
                if exchange_api:
                    trades = await exchange_api.get_trades(trading_pair, limit)

                    # 过滤出新交易
                    new_trades = [
                        trade for trade in trades
                        if trade['id'] not in last_trade_ids
                    ]

                    if new_trades:
                        # 更新已推送的交易ID
                        for trade in new_trades:
                            last_trade_ids.add(trade['id'])

                        # 只保留最近的100个交易ID，避免内存无限增长
                        if len(last_trade_ids) > 100:
                            last_trade_ids = set(list(last_trade_ids)[-100:])

                        message = {
                            "type": "trades",
                            "trading_pair": trading_pair,
                            "timestamp": datetime.now().isoformat(),
                            "data": new_trades
                        }

                        await manager.send_to_subscribers('trades', channel_key, message)
                else:
                    # 模拟数据（随机生成交易）
                    import random
                    new_trade = {
                        "id": str(int(datetime.now().timestamp() * 1000)),
                        "timestamp": int(datetime.now().timestamp() * 1000),
                        "datetime": datetime.now().isoformat(),
                        "symbol": trading_pair,
                        "side": 'buy' if random.random() > 0.5 else 'sell',
                        "price": 50000 + random.uniform(-50, 50),
                        "amount": random.uniform(0.01, 2),
                        "cost": 0,
                        "fee": {
                            "cost": 0,
                            "currency": "USDT"
                        }
                    }
                    new_trade['cost'] = new_trade['price'] * new_trade['amount']
                    new_trade['fee']['cost'] = new_trade['cost'] * 0.001

                    message = {
                        "type": "trades",
                        "trading_pair": trading_pair,
                        "timestamp": datetime.now().isoformat(),
                        "data": [new_trade]
                    }

                    await manager.send_to_subscribers('trades', channel_key, message)

                await asyncio.sleep(3)  # 每3秒检查一次

            except Exception as e:
                print(f"成交数据推送错误: {e}")
                await asyncio.sleep(5)

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}, trading_pair={trading_pair}")
    except Exception as e:
        print(f"成交数据流错误: {e}")
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
