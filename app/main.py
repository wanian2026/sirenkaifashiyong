from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import auth, bots, trades, orders, risk, backtest, notifications, rbac, optimization, exchange
from app.websocket import manager, bot_status_stream, market_data_stream
from typing import Dict
import json

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title="加密货币交易系统",
    description="基于LangGraph的加密货币合约交易系统，支持对冲网格策略",
    version="1.0.0"
)

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
            "回测引擎",
            "马丁策略",
            "均值回归策略",
            "通知系统",
            "RBAC权限管理",
            "实时市场数据",
            "K线图表",
            "深度图表",
            "WebSocket实时推送"
        ]
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    # 验证token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    # 这里应该验证token获取user_id
    # 为简化，使用固定user_id=1
    user_id = 1

    await manager.connect(user_id, websocket)
    try:
        # 广播市场数据
        import random
        while True:
            price = 50000 + random.uniform(-100, 100)
            message = {
                "type": "market_data",
                "data": {
                    "price": price,
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                }
            }
            await manager.send_personal_message(message, user_id)
            await __import__('asyncio').sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
