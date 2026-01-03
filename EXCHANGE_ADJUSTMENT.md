# 交易所调整说明

## 修改内容

根据用户要求，已将交易所选项精简，只保留 **币安（Binance）** 和 **欧易（OKX）** 两个交易所，删除了其他所有交易所。

## 修改的文件

### 1. app/exchange_manager.py
- 修改 `SUPPORTED_EXCHANGES` 字典
- 删除：huobi, bybit, gate, kucoin, bitget
- 保留：binance, okx

```python
SUPPORTED_EXCHANGES = {
    'binance': '币安',
    'okx': '欧易',
}
```

### 2. static/ultra_minimal.html
修改了两处交易所选择下拉框：

- **机器人创建表单**（行601）
- **添加交易所模态框**（行690）

修改前：
```html
<select id="botExchange">
    <option value="binance">Binance</option>
    <option value="okx">OKX</option>
    <option value="huobi">Huobi</option>
</select>
```

修改后：
```html
<select id="botExchange">
    <option value="binance">Binance</option>
    <option value="okx">OKX</option>
</select>
```

### 3. quick_setup.py
- 删除交易所选项中的 "huobi"
- 修改输入提示从 "请选择交易所 (1-3)" 改为 "请选择交易所 (1-2)"

修改前：
```python
exchange_map = {"1": "binance", "2": "okx", "3": "huobi"}
exchange_choice = input("请选择交易所 (1-3) [默认: 1]: ").strip() or "1"
```

修改后：
```python
exchange_map = {"1": "binance", "2": "okx"}
exchange_choice = input("请选择交易所 (1-2) [默认: 1]: ").strip() or "1"
```

### 4. app/main.py
- 添加 `exchanges` 路由导入
- 注册 exchanges.router 路由

```python
from app.routers import (
    auth, bots, trades, orders, risk, backtest,
    notifications, rbac, optimization, exchange, exchanges, analytics, strategies, websocket, audit_log, log_manager, database_manager, performance_monitor, bot_performance, risk_enhanced
)

app.include_router(exchanges.router, prefix="/api/exchanges", tags=["交易所配置"])
```

## 验证结果

### 后端API测试
```bash
curl http://localhost:8000/api/exchanges/supported
```

返回结果：
```json
{
    "success": true,
    "exchanges": {
        "binance": "币安",
        "okx": "欧易"
    }
}
```

### Python模块测试
```python
from app.exchange_manager import ExchangeManager
print('支持的交易所:', ExchangeManager.get_supported_exchanges())
```

输出：
```
支持的交易所: {'binance': '币安', 'okx': '欧易'}
```

### 前端界面检查
- ✅ 机器人创建表单：只显示 Binance 和 OKX
- ✅ 添加交易所模态框：只显示 Binance 和 OKX

## 影响范围

- ✅ 不影响现有数据库
- ✅ 不影响已配置的交易所
- ✅ 前端和后端保持一致
- ✅ API正常工作

## 使用方法

### 通过Web界面
1. 访问 http://localhost:8000/static/ultra_minimal.html
2. 登录系统
3. 点击「交易所配置」
4. 添加交易所时，下拉框只显示 Binance 和 OKX

### 通过快速配置脚本
```bash
python quick_setup.py
```

按照提示选择交易所（1: Binance, 2: OKX）

### 通过API调用
```bash
curl http://localhost:8000/api/exchanges/supported
```

## 注意事项

1. **已配置的交易所不受影响**：如果之前配置了其他交易所，数据库中的配置仍然存在，但系统将不再支持这些交易所的新配置
2. **测试功能正常**：交易所连接测试、余额查询等功能仅在支持的交易所（binance、okx）上可用
3. **前端和后端同步**：前端选项和后端支持列表已完全同步

## 后续优化建议

如果需要进一步优化：
1. 可以清理数据库中已删除的交易所配置
2. 可以在启动时自动检测并提示不支持的交易所配置
3. 可以添加自定义交易所支持功能
