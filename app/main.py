from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import (
    auth, bots, trades, orders, risk, backtest,
    notifications, rbac, optimization, exchange, analytics, strategies, websocket, audit_log
)
from app.middleware import AuditLogMiddleware
from app.websocket import (
    manager,
    bot_status_stream,
    market_data_stream,
    kline_data_stream,
    order_book_stream,
    trades_stream,
    market_overview_stream
)
from app.cache import init_cache, clear_cache, get_cache_stats, reset_cache_stats
from typing import Dict
import json
import asyncio

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 初始化缓存
init_cache(
    redis_enabled=settings.REDIS_ENABLED,
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD
)

# 创建FastAPI应用
app = FastAPI(
    title="加密货币交易系统",
    description="基于LangGraph的加密货币合约交易系统，支持对冲网格策略",
    version="1.0.0"
)

# 添加审计日志中间件
if settings.AUDIT_LOG_ENABLED:
    app.add_middleware(AuditLogMiddleware)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(bots.router, prefix="/api/bots", tags=["机器人"])
app.include_router(trades.router, prefix="/api/trades", tags=["交易记录"])
app.include_router(orders.router, prefix="/api/orders", tags=["订单管理"])
app.include_router(risk.router, prefix="/api/risk", tags=["风险管理"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["回测"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["通知"])
app.include_router(rbac.router, prefix="/api/rbac", tags=["权限管理"])
app.include_router(optimization.router, prefix="/api/optimize", tags=["系统优化"])
app.include_router(exchange.router, prefix="/api/exchange", tags=["交易所"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["数据分析"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["高级策略"])
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(audit_log.router, tags=["审计日志"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "加密货币交易系统API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/api/system/info")
async def system_info():
    """系统信息"""
    return {
        "system": "加密货币交易系统",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "对冲网格策略",
            "均值回归策略",
            "动量策略",
            "回测引擎",
            "马丁策略",
            "通知系统",
            "RBAC权限管理",
            "实时市场数据",
            "K线图表",
            "深度图表",
            "WebSocket实时推送",
            "Redis缓存",
            "风险管理",
            "数据分析仪表盘",
            "收益曲线",
            "交易统计",
            "策略回测"
        ]
    }


@app.post("/api/cache/clear")
async def clear_api_cache(pattern: str = None):
    """
    清空缓存

    Args:
        pattern: 匹配模式（可选），如 "ticker:*" 清空所有ticker缓存

    Returns:
        操作结果
    """
    try:
        await clear_cache(pattern)
        return {
            "success": True,
            "message": f"缓存已清空: {pattern or '全部'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cache/refresh")
async def refresh_cache(cache_type: str = Query(..., description="缓存类型: ticker, orderbook, ohlcv, pairs, all")):
    """
    刷新指定类型的缓存

    Args:
        cache_type: 缓存类型

    Returns:
        操作结果
    """
    try:
        patterns = {
            "ticker": "ticker:*",
            "orderbook": "orderbook:*",
            "ohlcv": "ohlcv:*",
            "pairs": "pairs:*",
            "all": None
        }

        pattern = patterns.get(cache_type, None)
        await clear_cache(pattern)

        return {
            "success": True,
            "message": f"缓存已刷新: {cache_type}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cache/status")
async def get_cache_status():
    """
    获取缓存状态

    Returns:
        缓存状态信息
    """
    from app.cache import get_cache

    cache = get_cache()

    return {
        "success": True,
        "data": {
            "backend": cache.backend.__class__.__name__,
            "redis_enabled": settings.REDIS_ENABLED,
            "redis_host": settings.REDIS_HOST if settings.REDIS_ENABLED else None,
            "redis_port": settings.REDIS_PORT if settings.REDIS_ENABLED else None
        }
    }


@app.get("/api/cache/stats")
async def get_cache_statistics():
    """
    获取缓存统计信息

    Returns:
        缓存统计数据
    """
    stats = get_cache_stats()

    return {
        "success": True,
        "data": stats.to_dict()
    }


@app.post("/api/cache/stats/reset")
async def reset_cache_stats_api():
    """
    重置缓存统计

    Returns:
        操作结果
    """
    reset_cache_stats()

    return {
        "success": True,
        "message": "缓存统计已重置"
    }




@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    通用WebSocket端点 - 支持订阅多个频道

    使用方法：
    - 连接: ws://localhost:8000/ws?token=your_token
    - 订阅频道: 发送JSON消息 {"action": "subscribe", "channel": "kline_data", "params": {"trading_pair": "BTC/USDT", "timeframe": "1h"}}
    - 取消订阅: 发送JSON消息 {"action": "unsubscribe", "channel": "kline_data", "params": {"trading_pair": "BTC/USDT", "timeframe": "1h"}}

    支持的频道：
    - kline_data: K线数据推送
    - order_book: 深度数据推送
    - trades: 成交明细推送
    - market_data: 市场数据推送
    - bot_status: 机器人状态推送
    - market_overview: 市场概览推送（涨跌幅、成交量）
    """
    # 验证token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    # 验证token获取user_id（这里简化处理）
    # 实际应该通过auth.verify_token()验证
    from app.auth import verify_token
    try:
        user_id = verify_token(token)
    except:
        user_id = 1  # 默认user_id，生产环境需要正确验证

    await manager.connect(user_id, websocket)

    # 记录用户订阅的频道
    subscriptions = {}

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()

            action = data.get("action")
            channel = data.get("channel")
            params = data.get("params", {})

            if action == "subscribe":
                # 订阅频道
                if channel == "kline_data":
                    trading_pair = params.get("trading_pair", "BTC/USDT")
                    timeframe = params.get("timeframe", "1h")
                    sub_key = f"{trading_pair}:{timeframe}"

                    # 启动K线数据推送任务
                    task = asyncio.create_task(
                        kline_data_stream(trading_pair, timeframe, websocket, user_id)
                    )
                    subscriptions[sub_key] = task

                    await websocket.send_json({
                        "type": "subscription_success",
                        "channel": "kline_data",
                        "params": params
                    })

                elif channel == "order_book":
                    trading_pair = params.get("trading_pair", "BTC/USDT")
                    limit = params.get("limit", 20)
                    sub_key = f"{trading_pair}:orderbook:{limit}"

                    # 启动深度数据推送任务
                    task = asyncio.create_task(
                        order_book_stream(trading_pair, limit, websocket, user_id)
                    )
                    subscriptions[sub_key] = task

                    await websocket.send_json({
                        "type": "subscription_success",
                        "channel": "order_book",
                        "params": params
                    })

                elif channel == "trades":
                    trading_pair = params.get("trading_pair", "BTC/USDT")
                    limit = params.get("limit", 50)
                    sub_key = f"{trading_pair}:trades"

                    # 启动成交明细推送任务
                    task = asyncio.create_task(
                        trades_stream(trading_pair, limit, websocket, user_id)
                    )
                    subscriptions[sub_key] = task

                    await websocket.send_json({
                        "type": "subscription_success",
                        "channel": "trades",
                        "params": params
                    })

                elif channel == "market_data":
                    trading_pair = params.get("trading_pair", "BTC/USDT")
                    sub_key = f"{trading_pair}:market"

                    # 启动市场数据推送任务
                    task = asyncio.create_task(
                        market_data_stream(trading_pair, websocket, user_id)
                    )
                    subscriptions[sub_key] = task

                    await websocket.send_json({
                        "type": "subscription_success",
                        "channel": "market_data",
                        "params": params
                    })

                elif channel == "bot_status":
                    bot_id = params.get("bot_id")
                    if bot_id:
                        sub_key = f"bot:{bot_id}:status"

                        # 启动机器人状态推送任务
                        task = asyncio.create_task(
                            bot_status_stream(bot_id, websocket, user_id)
                        )
                        subscriptions[sub_key] = task

                        await websocket.send_json({
                            "type": "subscription_success",
                            "channel": "bot_status",
                            "params": params
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "缺少bot_id参数"
                        })

                elif channel == "market_overview":
                    sub_key = "market_overview:global"

                    # 启动市场概览推送任务
                    task = asyncio.create_task(
                        market_overview_stream(websocket, user_id)
                    )
                    subscriptions[sub_key] = task

                    await websocket.send_json({
                        "type": "subscription_success",
                        "channel": "market_overview",
                        "params": params
                    })

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"不支持的频道: {channel}"
                    })

            elif action == "unsubscribe":
                # 取消订阅
                if channel == "kline_data":
                    trading_pair = params.get("trading_pair", "BTC/USDT")
                    timeframe = params.get("timeframe", "1h")
                    sub_key = f"{trading_pair}:{timeframe}"

                    if sub_key in subscriptions:
                        subscriptions[sub_key].cancel()
                        del subscriptions[sub_key]

                        await websocket.send_json({
                            "type": "unsubscribe_success",
                            "channel": "kline_data",
                            "params": params
                        })

                elif channel in ["order_book", "trades", "market_data"]:
                    # 取消其他频道的订阅
                    trading_pair = params.get("trading_pair", "BTC/USDT")
                    sub_key = f"{trading_pair}:{channel}"

                    if sub_key in subscriptions:
                        subscriptions[sub_key].cancel()
                        del subscriptions[sub_key]

                        await websocket.send_json({
                            "type": "unsubscribe_success",
                            "channel": channel,
                            "params": params
                        })

                elif channel == "market_overview":
                    sub_key = "market_overview:global"

                    if sub_key in subscriptions:
                        subscriptions[sub_key].cancel()
                        del subscriptions[sub_key]

                        await websocket.send_json({
                            "type": "unsubscribe_success",
                            "channel": "market_overview",
                            "params": params
                        })

            elif action == "ping":
                # 心跳检测
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"不支持的操作: {action}"
                })

    except WebSocketDisconnect:
        print(f"WebSocket断开连接: user_id={user_id}")
        # 取消所有订阅任务
        for task in subscriptions.values():
            if not task.done():
                task.cancel()
        manager.disconnect(user_id, websocket)

    except Exception as e:
        print(f"WebSocket错误: {e}")
        # 取消所有订阅任务
        for task in subscriptions.values():
            if not task.done():
                task.cancel()
        manager.disconnect(user_id, websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
