# WebSocket 实时数据推送指南

> 更新时间：2025年1月2日
> 状态：✅ 已完成

---

## 📋 概述

WebSocket 实时数据推送系统为前端提供高效的实时数据传输能力，支持多种数据类型的实时推送。

### 支持的数据类型

- ✅ **K线数据** (`kline_data`) - 实时K线价格数据
- ✅ **深度数据** (`order_book`) - 实时订单簿深度
- ✅ **成交明细** (`trades`) - 实时成交记录
- ✅ **市场数据** (`market_data`) - 实时价格、24h涨跌等
- ✅ **机器人状态** (`bot_status`) - 机器人运行状态
- ✅ **市场概览** (`market_overview`) - 主要交易对概览（涨跌幅、成交量）

---

## 🔌 连接WebSocket

### 1. 建立连接

```javascript
// 前端JavaScript示例
const token = localStorage.getItem('token'); // 从localStorage获取JWT token
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

// 连接成功
ws.onopen = () => {
    console.log('WebSocket连接成功');
};

// 接收消息
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('收到消息:', message);

    // 根据消息类型处理
    switch(message.type) {
        case 'kline_data':
            // 处理K线数据
            updateKlineChart(message.data);
            break;
        case 'order_book':
            // 处理深度数据
            updateOrderBook(message.data);
            break;
        case 'trades':
            // 处理成交记录
            updateTrades(message.data);
            break;
        case 'market_data':
            // 处理市场数据
            updateMarketData(message.data);
            break;
        case 'bot_status':
            // 处理机器人状态
            updateBotStatus(message.data);
            break;
        case 'market_overview':
            // 处理市场概览
            updateMarketOverview(message.data);
            break;
    }
};

// 连接关闭
ws.onclose = () => {
    console.log('WebSocket连接关闭');
};

// 连接错误
ws.onerror = (error) => {
    console.error('WebSocket错误:', error);
};
```

---

## 📡 订阅频道

### 2. 订阅K线数据

```javascript
// 订阅BTC/USDT的1小时K线数据
ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'kline_data',
    params: {
        trading_pair: 'BTC/USDT',
        timeframe: '1h'
    }
}));

// 服务器响应
{
    "type": "subscription_success",
    "channel": "kline_data",
    "params": {
        "trading_pair": "BTC/USDT",
        "timeframe": "1h"
    }
}

// 接收K线数据
{
    "type": "kline_data",
    "trading_pair": "BTC/USDT",
    "timeframe": "1h",
    "timestamp": "2025-01-02T12:00:00",
    "data": {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "timestamp": 1735814400000,
        "open": 50000,
        "high": 50500,
        "low": 49800,
        "close": 50200,
        "volume": 1250.5
    }
}
```

**支持的时间周期**:
- `1m` - 1分钟
- `5m` - 5分钟
- `15m` - 15分钟
- `1h` - 1小时
- `4h` - 4小时
- `1d` - 1天

---

### 3. 订阅深度数据

```javascript
// 订阅BTC/USDT的深度数据（20档）
ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'order_book',
    params: {
        trading_pair: 'BTC/USDT',
        limit: 20
    }
}));

// 接收深度数据
{
    "type": "order_book",
    "trading_pair": "BTC/USDT",
    "limit": 20,
    "timestamp": "2025-01-02T12:00:00",
    "data": {
        "symbol": "BTC/USDT",
        "bids": [
            {
                "price": 50000,
                "amount": 0.5,
                "total": 0.5,
                "total_percent": 10.0
            },
            // ... 更多买单
        ],
        "asks": [
            {
                "price": 50010,
                "amount": 0.3,
                "total": 0.3,
                "total_percent": 6.0
            },
            // ... 更多卖单
        ],
        "timestamp": 1735814400000
    }
}
```

---

### 4. 订阅成交明细

```javascript
// 订阅BTC/USDT的成交记录（最近50条）
ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'trades',
    params: {
        trading_pair: 'BTC/USDT',
        limit: 50
    }
}));

// 接收成交数据
{
    "type": "trades",
    "trading_pair": "BTC/USDT",
    "timestamp": "2025-01-02T12:00:00",
    "data": [
        {
            "id": "1735814400000",
            "timestamp": 1735814400000,
            "datetime": "2025-01-02T12:00:00",
            "symbol": "BTC/USDT",
            "side": "buy",
            "price": 50000,
            "amount": 0.5,
            "cost": 25000,
            "fee": {
                "cost": 25,
                "currency": "USDT"
            }
        },
        // ... 更多成交记录
    ]
}
```

---

### 5. 订阅市场数据

```javascript
// 订阅BTC/USDT的市场数据
ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'market_data',
    params: {
        trading_pair: 'BTC/USDT'
    }
}));

// 接收市场数据
{
    "type": "market_data",
    "trading_pair": "BTC/USDT",
    "timestamp": "2025-01-02T12:00:00",
    "data": {
        "price": 50000,
        "high": 50500,
        "low": 49800,
        "volume": 1250.5,
        "change": 200,
        "percentage": 0.4
    }
}
```

---

### 6. 订阅机器人状态

```javascript
// 订阅机器人ID为1的状态
ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'bot_status',
    params: {
        bot_id: 1
    }
}));

// 接收机器人状态
{
    "type": "bot_status",
    "bot_id": 1,
    "timestamp": "2025-01-02T12:00:00",
    "data": {
        "status": "running",
        "total_orders": 120,
        "completed_orders": 85,
        "pending_orders": 35,
        "total_profit": 1250.5,
        "total_loss": -320.2,
        "net_profit": 930.3,
        "win_rate": 70.5,
        "current_price": 50000,
        "position": {
            "amount": 2.5,
            "avg_price": 49800,
            "unrealized_pnl": 500
        }
    }
}
```

---

### 7. 订阅市场概览

```javascript
// 订阅市场概览（主要交易对的涨跌幅和成交量）
ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'market_overview',
    params: {}
}));

// 接收市场概览
{
    "type": "market_overview",
    "timestamp": "2025-01-02T12:00:00",
    "data": {
        "market_data": [
            {
                "symbol": "BTC/USDT",
                "price": 50000,
                "change": 200,
                "percentage": 0.4,
                "volume": 1250.5,
                "quoteVolume": 62525000,
                "high": 50500,
                "low": 49800
            },
            {
                "symbol": "ETH/USDT",
                "price": 3000,
                "change": -50,
                "percentage": -1.67,
                "volume": 5000,
                "quoteVolume": 15000000,
                "high": 3100,
                "low": 2950
            },
            // ... 更多交易对
        ],
        "summary": {
            "total_pairs": 5,
            "gainers": 3,
            "losers": 2,
            "avg_change": -0.5,
            "total_volume": 85000000
        }
    }
}
```

---

## ❌ 取消订阅

### 8. 取消订阅频道

```javascript
// 取消订阅K线数据
ws.send(JSON.stringify({
    action: 'unsubscribe',
    channel: 'kline_data',
    params: {
        trading_pair: 'BTC/USDT',
        timeframe: '1h'
    }
}));

// 服务器响应
{
    "type": "unsubscribe_success",
    "channel": "kline_data",
    "params": {
        "trading_pair": "BTC/USDT",
        "timeframe": "1h"
    }
}

// 取消订阅深度数据
ws.send(JSON.stringify({
    action: 'unsubscribe',
    channel: 'order_book',
    params: {
        trading_pair: 'BTC/USDT'
    }
}));

// 取消订阅成交明细
ws.send(JSON.stringify({
    action: 'unsubscribe',
    channel: 'trades',
    params: {
        trading_pair: 'BTC/USDT'
    }
}));

// 取消订阅市场数据
ws.send(JSON.stringify({
    action: 'unsubscribe',
    channel: 'market_data',
    params: {
        trading_pair: 'BTC/USDT'
    }
}));

// 取消订阅市场概览
ws.send(JSON.stringify({
    action: 'unsubscribe',
    channel: 'market_overview',
    params: {}
}));
```

---

## 💓 心跳检测

### 9. 心跳ping/pong

```javascript
// 发送心跳ping
ws.send(JSON.stringify({
    action: 'ping'
}));

// 服务器响应pong
{
    "type": "pong",
    "timestamp": "2025-01-02T12:00:00"
}
```

**建议**: 每30秒发送一次心跳，保持连接活跃。

---

## 🎯 完整示例

### 10. 前端完整示例

```javascript
class WebSocketManager {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.subscriptions = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
    }

    connect() {
        const token = localStorage.getItem('token');
        this.ws = new WebSocket(`${this.url}?token=${token}`);

        this.ws.onopen = () => {
            console.log('WebSocket连接成功');
            this.reconnectAttempts = 0;

            // 重新订阅之前的频道
            this.resubscribeAll();
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onclose = () => {
            console.log('WebSocket连接关闭');
            this.reconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
        };
    }

    handleMessage(message) {
        switch(message.type) {
            case 'kline_data':
                this.onKlineData(message);
                break;
            case 'order_book':
                this.onOrderBook(message);
                break;
            case 'trades':
                this.onTrades(message);
                break;
            case 'market_data':
                this.onMarketData(message);
                break;
            case 'bot_status':
                this.onBotStatus(message);
                break;
            case 'market_overview':
                this.onMarketOverview(message);
                break;
            case 'subscription_success':
                console.log('订阅成功:', message.channel);
                break;
            case 'unsubscribe_success':
                console.log('取消订阅成功:', message.channel);
                break;
            case 'pong':
                // 心跳响应
                break;
            default:
                console.warn('未知消息类型:', message.type);
        }
    }

    subscribe(channel, params) {
        const key = `${channel}:${JSON.stringify(params)}`;
        this.subscriptions[key] = { channel, params };

        this.ws.send(JSON.stringify({
            action: 'subscribe',
            channel,
            params
        }));
    }

    unsubscribe(channel, params) {
        const key = `${channel}:${JSON.stringify(params)}`;
        delete this.subscriptions[key];

        this.ws.send(JSON.stringify({
            action: 'unsubscribe',
            channel,
            params
        }));
    }

    resubscribeAll() {
        for (const key in this.subscriptions) {
            const { channel, params } = this.subscriptions[key];
            this.subscribe(channel, params);
        }
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`尝试重新连接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay);
        } else {
            console.error('达到最大重连次数，放弃重连');
        }
    }

    // 回调函数（可自定义）
    onKlineData(message) {}
    onOrderBook(message) {}
    onTrades(message) {}
    onMarketData(message) {}
    onBotStatus(message) {}
    onMarketOverview(message) {}
}

// 使用示例
const wsManager = new WebSocketManager('ws://localhost:8000/ws');
wsManager.connect();

// 自定义回调
wsManager.onKlineData = (message) => {
    console.log('K线数据:', message.data);
    // 更新K线图表
};

wsManager.onOrderBook = (message) => {
    console.log('深度数据:', message.data);
    // 更新深度图表
};

// 订阅频道
wsManager.subscribe('kline_data', {
    trading_pair: 'BTC/USDT',
    timeframe: '1h'
});

wsManager.subscribe('order_book', {
    trading_pair: 'BTC/USDT',
    limit: 20
});

wsManager.subscribe('trades', {
    trading_pair: 'BTC/USDT',
    limit: 50
});

wsManager.subscribe('market_overview', {});

// 心跳检测
setInterval(() => {
    wsManager.ws.send(JSON.stringify({ action: 'ping' }));
}, 30000);
```

---

## 🔍 推送频率

| 数据类型 | 推送频率 | 说明 |
|---------|---------|------|
| K线数据 | 每5秒 | 仅当K线更新时推送 |
| 深度数据 | 每2秒 | 始终推送最新深度 |
| 成交明细 | 每3秒 | 仅推送新的成交记录 |
| 市场数据 | 每1秒 | 实时价格更新 |
| 机器人状态 | 每2秒 | 机器人运行状态 |
| 市场概览 | 每3秒 | 主要交易对概览 |

---

## ⚠️ 注意事项

### 1. 连接管理
- 保持WebSocket连接活跃，定期发送心跳（建议30秒一次）
- 实现自动重连机制，提高连接稳定性
- 妥善处理连接断开和错误情况

### 2. 订阅管理
- 不要重复订阅同一频道
- 及时取消不需要的订阅，减少服务器负担
- 记录已订阅的频道，断线重连后自动重新订阅

### 3. 性能优化
- 对于高频数据（如深度、K线），考虑使用节流或防抖
- 大量数据建议使用分页或限制数量
- 合理选择时间周期和数据量，避免数据过多

### 4. 错误处理
- 处理网络错误和连接断开
- 处理数据格式错误
- 实现降级机制（WebSocket失败时使用轮询）

---

## 📚 相关文档

- [API文档](./API_DOCUMENTATION.md)
- [Redis缓存优化](./CACHE_OPTIMIZATION.md)
- [交易所API集成](./REAL_EXCHANGE_INTEGRATION.md)

---

## 🎉 总结

✅ **支持多种数据类型** - K线、深度、成交、市场数据、机器人状态、市场概览
✅ **灵活的订阅机制** - 按需订阅，支持动态订阅和取消订阅
✅ **高效的推送频率** - 根据数据类型设置合理的推送频率
✅ **完整的前端示例** - 提供完整的JavaScript使用示例
✅ **生产就绪** - 支持自动重连、心跳检测、错误处理

开始使用WebSocket，体验实时数据推送！ 🚀
