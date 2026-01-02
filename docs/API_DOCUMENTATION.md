# 加密货币交易系统 - API文档

> 基于LangGraph工作流的加密货币合约交易系统 API 完整文档

---

## 📚 目录

- [认证接口](#认证接口)
- [机器人管理](#机器人管理)
- [订单管理](#订单管理)
- [交易记录](#交易记录)
- [风险管理](#风险管理)
- [WebSocket实时推送](#websocket实时推送)

---

## 🔐 认证接口

### 用户注册

```http
POST /api/auth/register
Content-Type: application/json
```

**请求体：**
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "SecurePassword123"
}
```

**响应：**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 用户登录

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded
```

**请求参数：**
- `username`: 用户名
- `password`: 密码

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 获取当前用户信息

```http
GET /api/auth/me
Authorization: Bearer {token}
```

**响应：**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 修改密码

```http
PUT /api/auth/change-password
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体：**
```json
{
  "old_password": "OldPassword123",
  "new_password": "NewPassword456"
}
```

**响应：**
```json
{
  "message": "密码修改成功"
}
```

### 更新用户信息

```http
PUT /api/auth/me
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体：**
```json
{
  "email": "newemail@example.com"
}
```

**响应：**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "newemail@example.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## 🤖 机器人管理

### 创建机器人

```http
POST /api/bots
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体：**
```json
{
  "name": "BTC网格交易机器人",
  "exchange": "binance",
  "trading_pair": "BTC/USDT",
  "strategy": "hedge_grid",
  "config": {
    "grid_levels": 10,
    "grid_spacing": 0.02,
    "investment_amount": 1000,
    "dynamic_grid": true,
    "batch_build": true,
    "batch_count": 3,
    "stop_loss_threshold": 0.05,
    "take_profit_threshold": 0.10
  }
}
```

**响应：**
```json
{
  "id": 1,
  "name": "BTC网格交易机器人",
  "exchange": "binance",
  "trading_pair": "BTC/USDT",
  "strategy": "hedge_grid",
  "status": "stopped",
  "config": {...},
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 获取机器人列表

```http
GET /api/bots
Authorization: Bearer {token}
```

**响应：**
```json
[
  {
    "id": 1,
    "name": "BTC网格交易机器人",
    "exchange": "binance",
    "trading_pair": "BTC/USDT",
    "strategy": "hedge_grid",
    "status": "running",
    "config": {...},
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### 获取机器人详情

```http
GET /api/bots/{bot_id}
Authorization: Bearer {token}
```

**响应：** 同创建响应

### 更新机器人配置

```http
PUT /api/bots/{bot_id}
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体：**
```json
{
  "name": "新的机器人名称",
  "config": {
    "grid_levels": 20,
    "grid_spacing": 0.015
  }
}
```

**响应：** 同创建响应

### 启动机器人

```http
POST /api/bots/{bot_id}/start
Authorization: Bearer {token}
```

**响应：**
```json
{
  "message": "机器人已启动",
  "bot_id": 1
}
```

### 停止机器人

```http
POST /api/bots/{bot_id}/stop
Authorization: Bearer {token}
```

**响应：**
```json
{
  "message": "机器人已停止",
  "bot_id": 1
}
```

### 获取机器人状态

```http
GET /api/bots/{bot_id}/status
Authorization: Bearer {token}
```

**响应：**
```json
{
  "current_price": 50000,
  "total_invested": 1000,
  "realized_profit": 50.5,
  "pending_orders": 5,
  "filled_orders": 10
}
```

### 删除机器人

```http
DELETE /api/bots/{bot_id}
Authorization: Bearer {token}
```

**响应：**
```json
{
  "message": "机器人已删除"
}
```

---

## 📋 订单管理

### 创建订单

```http
POST /api/orders
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体：**
```json
{
  "bot_id": 1,
  "order_type": "buy",
  "price": 49000,
  "amount": 0.01,
  "level": 1
}
```

**响应：**
```json
{
  "id": 1,
  "bot_id": 1,
  "level": 1,
  "order_type": "buy",
  "price": 49000,
  "amount": 0.01,
  "status": "pending",
  "order_id": null,
  "filled_amount": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "filled_at": null
}
```

### 获取订单列表

```http
GET /api/orders?bot_id=1&status_filter=pending&limit=100&offset=0
Authorization: Bearer {token}
```

**查询参数：**
- `bot_id`: 机器人ID（可选）
- `status_filter`: 状态筛选（可选）
- `order_type`: 订单类型（可选）
- `limit`: 数量限制（默认100）
- `offset`: 偏移量（默认0）

**响应：** 订单对象数组

### 获取订单统计

```http
GET /api/orders/stats/summary?bot_id=1
Authorization: Bearer {token}
```

**响应：**
```json
{
  "total_orders": 15,
  "pending_count": 5,
  "filled_count": 8,
  "cancelled_count": 2,
  "failed_count": 0,
  "total_filled_amount": 95000
}
```

### 取消单个订单

```http
POST /api/orders/{order_id}/cancel
Authorization: Bearer {token}
```

**响应：**
```json
{
  "message": "订单已取消",
  "order_id": 1
}
```

### 批量取消订单

```http
POST /api/orders/batch/cancel?bot_id=1&status_filter=pending
Authorization: Bearer {token}
```

**响应：**
```json
{
  "message": "批量撤单完成",
  "total": 5,
  "cancelled": 5,
  "failed": 0
}
```

### 更新订单状态

```http
PATCH /api/orders/{order_id}/status?new_status=filled&filled_amount=0.01
Authorization: Bearer {token}
```

**响应：**
```json
{
  "message": "订单状态已更新",
  "order_id": 1,
  "status": "filled"
}
```

### 获取订单详情

```http
GET /api/orders/{order_id}
Authorization: Bearer {token}
```

**响应：** 订单对象

---

## 💰 交易记录

### 获取机器人交易记录

```http
GET /api/trades/bot/{bot_id}?limit=100&offset=0
Authorization: Bearer {token}
```

**响应：** 交易对象数组

### 获取最近交易记录

```http
GET /api/trades/recent?limit=50
Authorization: Bearer {token}
```

**响应：** 交易对象数组

### 获取交易统计

```http
GET /api/trades/stats?bot_id=1&start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer {token}
```

**响应：**
```json
{
  "total_trades": 50,
  "total_profit": 500.50,
  "average_profit": 10.01,
  "win_rate": 65.5,
  "profit_factor": 2.5,
  "max_profit": 100.0,
  "max_loss": -50.0,
  "gross_profit": 800.0,
  "gross_loss": 300.0
}
```

### 获取每日统计

```http
GET /api/trades/stats/daily?bot_id=1&days=30
Authorization: Bearer {token}
```

**响应：**
```json
{
  "data": [
    {
      "date": "2024-01-01",
      "trades_count": 10,
      "total_profit": 50.5,
      "winning_trades": 7,
      "losing_trades": 3,
      "win_rate": 70.0
    }
  ]
}
```

### 按交易对统计

```http
GET /api/trades/stats/by-pair
Authorization: Bearer {token}
```

**响应：**
```json
{
  "data": [
    {
      "trading_pair": "BTC/USDT",
      "trades_count": 30,
      "total_profit": 300.0,
      "average_profit": 10.0
    }
  ]
}
```

### 高级筛选交易记录

```http
GET /api/trades/filter?bot_id=1&trading_pair=BTC/USDT&side=buy&start_date=2024-01-01&min_profit=0&sort_by=created_at&sort_order=desc&limit=100
Authorization: Bearer {token}
```

**查询参数：**
- `bot_id`: 机器人ID
- `trading_pair`: 交易对
- `side`: 买卖方向
- `start_date`: 开始日期
- `end_date`: 结束日期
- `min_profit`: 最小盈利
- `max_profit`: 最大盈利
- `sort_by`: 排序字段（created_at, price, amount, profit）
- `sort_order`: 排序方向（asc, desc）
- `limit`: 数量限制
- `offset`: 偏移量

**响应：** 交易对象数组

### 导出交易记录

```http
GET /api/trades/export?format=csv&bot_id=1&start_date=2024-01-01
Authorization: Bearer {token}
```

**查询参数：**
- `format`: 导出格式（csv, json）
- `bot_id`: 机器人ID
- `trading_pair`: 交易对
- `start_date`: 开始日期
- `end_date`: 结束日期

**响应（CSV）：** CSV文件流

**响应（JSON）：**
```json
{
  "export_time": "2024-01-01T00:00:00Z",
  "total_records": 50,
  "data": [...]
}
```

---

## ⚠️ 风险管理

### 检查风险限制

```http
POST /api/risk/bot/{bot_id}/check?position_value=5000&order_value=100
Authorization: Bearer {token}
```

**响应：**
```json
{
  "passed": true,
  "errors": [],
  "risk_report": {
    "timestamp": "2024-01-01T00:00:00Z",
    "current_position": 5000,
    "max_position": 10000,
    "position_usage_ratio": 0.5,
    "daily_pnl": 100.5,
    "total_pnl": 500.5,
    "daily_loss_limit": 1000,
    "total_loss_limit": 5000,
    "order_count": 10,
    "max_orders": 50,
    "daily_trades": 10,
    "limits_status": {
      "position": true,
      "daily_loss": true,
      "total_loss": true,
      "orders": true
    }
  }
}
```

### 获取风险报告

```http
GET /api/risk/bot/{bot_id}/report
Authorization: Bearer {token}
```

**响应：** 风险报告对象

### 重置每日限制

```http
POST /api/risk/bot/{bot_id}/reset
Authorization: Bearer {token}
```

**响应：**
```json
{
  "message": "每日风险限制已重置"
}
```

### 计算仓位大小

```http
POST /api/risk/calculate/position-size?account_balance=10000&risk_percent=0.02&entry_price=50000&stop_loss_price=49000
Authorization: Bearer {token}
```

**响应：**
```json
{
  "account_balance": 10000,
  "risk_percent": 0.02,
  "risk_amount": 200,
  "entry_price": 50000,
  "stop_loss_price": 49000,
  "position_size": 0.02,
  "position_value": 1000,
  "loss_per_unit": 1000,
  "risk_reward_ratio_warning": false
}
```

### 计算风险收益比

```http
POST /api/risk/calculate/risk-reward-ratio?entry_price=50000&stop_loss_price=49000&take_profit_price=52000
Authorization: Bearer {token}
```

**响应：**
```json
{
  "entry_price": 50000,
  "stop_loss_price": 49000,
  "take_profit_price": 52000,
  "risk": 1000,
  "reward": 2000,
  "risk_reward_ratio": 2.0,
  "suggestion": "风险收益比优秀"
}
```

### 评估风险等级

```http
POST /api/risk/bot/{bot_id}/evaluate-risk?position_value=5000&unrealized_pnl=100&volatility=0.02
Authorization: Bearer {token}
```

**响应：**
```json
{
  "risk_level": "medium",
  "advice": "当前风险中等，建议谨慎操作",
  "position_value": 5000,
  "unrealized_pnl": 100,
  "volatility": 0.02
}
```

### 删除风险管理器

```http
DELETE /api/risk/bot/{bot_id}
Authorization: Bearer {token}
```

**响应：**
```json
{
  "message": "风险管理器已删除"
}
```

---

## 📡 WebSocket实时推送

### 连接WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?token=YOUR_TOKEN');
```

### 机器人状态推送

**订阅频道：** `bot_status`

```json
{
  "type": "bot_status",
  "bot_id": 1,
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "trading_pair": "BTC/USDT",
    "current_price": 50000,
    "base_price": 50000,
    "total_invested": 1000,
    "realized_profit": 50.5,
    "unrealized_pnl": 25.0,
    "total_pnl": 75.5,
    "current_position": 0.02,
    "avg_buy_price": 49500,
    "pending_orders": 5,
    "filled_orders": 10,
    "grid_levels": 10,
    "grid_spacing": 0.02,
    "is_mock_mode": false,
    "dynamic_grid": true,
    "batch_build": true,
    "volatility": 0.02
  }
}
```

### 市场数据推送

**订阅频道：** `market_data`

```json
{
  "type": "market_data",
  "trading_pair": "BTC/USDT",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "price": 50000,
    "high": 50500,
    "low": 49500,
    "volume": 5000.5,
    "change": 100,
    "percentage": 0.2
  }
}
```

### K线数据推送

**订阅频道：** `kline_data`

```json
{
  "type": "kline_data",
  "trading_pair": "BTC/USDT",
  "timeframe": "1h",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": [
    [
      1704067200000,
      49900,
      50100,
      49800,
      50000,
      100.5
    ]
  ]
}
```

K线数据格式：`[timestamp, open, high, low, close, volume]`

### 深度数据推送

**订阅频道：** `order_book`

```json
{
  "type": "order_book",
  "trading_pair": "BTC/USDT",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "bids": [
      [49999, 0.5],
      [49998, 1.0]
    ],
    "asks": [
      [50001, 0.5],
      [50002, 1.0]
    ],
    "timestamp": 1704067200000
  }
}
```

深度数据格式：`[price, amount]`

### 交易通知推送

**订阅频道：** `trade_notification`

```json
{
  "type": "trade_notification",
  "bot_id": 1,
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "trade_id": 100,
    "side": "buy",
    "price": 49900,
    "amount": 0.01,
    "profit": 0,
    "trading_pair": "BTC/USDT"
  }
}
```

---

## 🔧 使用示例

### 完整交易流程

```python
import requests
import websocket
import json

# 1. 登录获取token
response = requests.post(
    'http://localhost:8000/api/auth/login',
    data={'username': 'admin', 'password': 'admin123'}
)
token = response.json()['access_token']

# 设置认证头
headers = {'Authorization': f'Bearer {token}'}

# 2. 创建机器人
bot_data = {
    "name": "BTC网格交易",
    "exchange": "binance",
    "trading_pair": "BTC/USDT",
    "strategy": "hedge_grid",
    "config": {
        "grid_levels": 10,
        "grid_spacing": 0.02,
        "investment_amount": 1000
    }
}
response = requests.post(
    'http://localhost:8000/api/bots',
    json=bot_data,
    headers=headers
)
bot_id = response.json()['id']

# 3. 检查风险限制
response = requests.post(
    f'http://localhost:8000/api/risk/bot/{bot_id}/check',
    params={'position_value': 1000, 'order_value': 100},
    headers=headers
)
print(response.json())

# 4. 启动机器人
response = requests.post(
    f'http://localhost:8000/api/bots/{bot_id}/start',
    headers=headers
)
print(response.json())

# 5. 连接WebSocket获取实时数据
def on_message(ws, message):
    data = json.loads(message)
    print(f"收到消息: {data['type']}")

ws = websocket.WebSocketApp(
    f'ws://localhost:8000/ws?token={token}',
    on_message=on_message
)
ws.run_forever()

# 6. 停止机器人
response = requests.post(
    f'http://localhost:8000/api/bots/{bot_id}/stop',
    headers=headers
)
print(response.json())

# 7. 导出交易记录
response = requests.get(
    'http://localhost:8000/api/trades/export',
    params={'format': 'csv', 'bot_id': bot_id},
    headers=headers
)
with open('trades.csv', 'wb') as f:
    f.write(response.content)
```

### WebSocket订阅示例

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8000/ws?token=YOUR_TOKEN');

// 处理消息
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch(data.type) {
        case 'bot_status':
            console.log('机器人状态:', data.data);
            break;
        case 'market_data':
            console.log('市场数据:', data.data);
            updatePrice(data.data.price);
            break;
        case 'kline_data':
            console.log('K线数据:', data.data);
            updateChart(data.data.data);
            break;
        case 'order_book':
            console.log('深度数据:', data.data);
            updateOrderBook(data.data);
            break;
        case 'trade_notification':
            console.log('交易通知:', data.data);
            showNotification(data.data);
            break;
    }
};

// 错误处理
ws.onerror = (error) => {
    console.error('WebSocket错误:', error);
};

// 连接关闭
ws.onclose = () => {
    console.log('WebSocket连接已关闭');
};
```

---

## 📝 注意事项

1. **认证**: 所有需要认证的接口都需要在请求头中携带JWT Token
2. **错误处理**: 所有API错误都返回标准错误格式
3. **分页**: 列表接口支持分页，默认每页100条
4. **实时数据**: 建议使用WebSocket获取实时数据，轮询方式效率较低
5. **风险控制**: 强烈建议使用风险管理功能，避免过度交易

---

## 🔗 相关文档

- [系统README](../README.md)
- [功能列表](../FEATURES.md)
- [快速开始](../QUICKSTART.md)
