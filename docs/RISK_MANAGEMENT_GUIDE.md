# 风险管理系统使用指南

> 版本：1.0.0
> 更新时间：2025年1月2日

---

## 📋 目录

1. [功能概述](#功能概述)
2. [风险管理配置](#风险管理配置)
3. [API 接口说明](#api-接口说明)
4. [使用示例](#使用示例)
5. [风险级别说明](#风险级别说明)
6. [最佳实践](#最佳实践)

---

## 功能概述

风险管理系统提供以下核心功能：

### 1. 风险限制检查
- **持仓限制**：控制最大持仓金额
- **单日亏损限制**：控制单日最大亏损金额
- **总亏损限制**：控制总最大亏损金额
- **订单数限制**：控制每日最大订单数
- **单笔订单限制**：控制单笔订单最大金额

### 2. 自动止损/止盈
- 基于百分比自动触发止损
- 基于百分比自动触发止盈
- 可配置是否启用自动执行

### 3. 风险等级评估
- LOW（低风险）
- MEDIUM（中等风险）
- HIGH（高风险）
- CRITICAL（极高风险）

### 4. 仓位计算
- 基于账户余额和风险百分比计算安全仓位
- 基于止损价格计算合理仓位大小

### 5. 风险收益比计算
- 计算交易的潜在风险和收益比
- 提供交易建议

---

## 风险管理配置

### 1. 创建机器人时配置风险管理参数

在创建或编辑机器人时，可以在 `config` 字段中配置风险管理参数：

```json
{
  "grid_levels": 10,
  "grid_spacing": 0.02,
  "investment_amount": 1000,
  "max_position": 10000,
  "max_daily_loss": 1000,
  "max_total_loss": 5000,
  "max_orders": 50,
  "max_single_order": 1000,
  "stop_loss_threshold": 0.05,
  "take_profit_threshold": 0.10,
  "enable_auto_stop": true
}
```

### 2. 风险管理参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_position` | float | 10000 | 最大持仓金额（USDT） |
| `max_daily_loss` | float | 1000 | 单日最大亏损（USDT） |
| `max_total_loss` | float | 5000 | 总最大亏损（USDT） |
| `max_orders` | int | 50 | 每日最大订单数 |
| `max_single_order` | float | 1000 | 单笔订单最大金额（USDT） |
| `stop_loss_threshold` | float | 0.05 | 止损阈值（5%） |
| `take_profit_threshold` | float | 0.10 | 止盈阈值（10%） |
| `enable_auto_stop` | bool | true | 是否启用自动止损 |

---

## API 接口说明

### 1. 检查机器人风险

**接口**: `POST /api/bots/{bot_id}/check-risk`

**请求参数**:
```json
{
  "position_value": 5000,
  "order_value": 1000
}
```

**响应示例**:
```json
{
  "passed": true,
  "errors": [],
  "risk_report": {
    "timestamp": "2025-01-02T10:00:00",
    "current_position": 5000,
    "max_position": 10000,
    "position_usage_ratio": 0.5,
    "daily_pnl": 200,
    "total_pnl": 1200,
    "daily_loss_limit": 1000,
    "total_loss_limit": 5000,
    "order_count": 15,
    "max_orders": 50,
    "daily_trades": 10,
    "limits_status": {
      "position": true,
      "daily_loss": true,
      "total_loss": true,
      "orders": true
    }
  },
  "risk_level": "medium",
  "recommendation": "可以继续交易"
}
```

### 2. 获取风险报告

**接口**: `GET /api/bots/{bot_id}/risk-report`

**响应示例**:
```json
{
  "timestamp": "2025-01-02T10:00:00",
  "current_position": 5000,
  "max_position": 10000,
  "position_usage_ratio": 0.5,
  "daily_pnl": 200,
  "total_pnl": 1200,
  "daily_loss_limit": 1000,
  "total_loss_limit": 5000,
  "order_count": 15,
  "max_orders": 50,
  "daily_trades": 10,
  "limits_status": {
    "position": true,
    "daily_loss": true,
    "total_loss": true,
    "orders": true
  }
}
```

### 3. 计算安全仓位大小

**接口**: `POST /api/risk/calculate/position-size`

**请求参数**:
```json
{
  "account_balance": 10000,
  "entry_price": 50000,
  "stop_loss_price": 49000,
  "risk_percent": 0.02
}
```

**响应示例**:
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

### 4. 计算风险收益比

**接口**: `POST /api/risk/calculate/risk-reward-ratio`

**请求参数**:
```json
{
  "entry_price": 50000,
  "stop_loss_price": 49000,
  "take_profit_price": 52000
}
```

**响应示例**:
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

---

## 使用示例

### 示例 1: 创建带风险管理的机器人

```bash
curl -X POST "http://localhost:8000/api/bots/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "BTC网格机器人",
    "exchange": "binance",
    "trading_pair": "BTC/USDT",
    "strategy": "hedge_grid",
    "config": {
      "grid_levels": 10,
      "grid_spacing": 0.02,
      "investment_amount": 1000,
      "max_position": 5000,
      "max_daily_loss": 500,
      "stop_loss_threshold": 0.03,
      "take_profit_threshold": 0.08
    }
  }'
```

### 示例 2: 在交易前检查风险

```bash
curl -X POST "http://localhost:8000/api/bots/1/check-risk" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "position_value": 3000,
    "order_value": 500
  }'
```

### 示例 3: 获取实时风险报告

```bash
curl -X GET "http://localhost:8000/api/bots/1/risk-report" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 示例 4: 计算建议仓位

```bash
curl -X POST "http://localhost:8000/api/risk/calculate/position-size" \
  -H "Content-Type: application/json" \
  -d '{
    "account_balance": 10000,
    "entry_price": 50000,
    "stop_loss_price": 49000,
    "risk_percent": 0.02
  }'
```

---

## 风险级别说明

### 1. LOW（低风险）
- **评分范围**: 0-30
- **特征**: 持仓、亏损、波动率都处于低水平
- **建议**: 可以正常交易

### 2. MEDIUM（中等风险）
- **评分范围**: 30-60
- **特征**: 持仓或亏损处于中等水平
- **建议**: 可以继续交易，但需要关注市场变化

### 3. HIGH（高风险）
- **评分范围**: 60-85
- **特征**: 持仓较高或亏损较大
- **建议**: 建议降低仓位或暂停交易

### 4. CRITICAL（极高风险）
- **评分范围**: 85-100
- **特征**: 持仓、亏损或波动率都非常高
- **建议**: 强烈建议立即停止交易

### 风险评分计算

风险总分 = 持仓风险评分 + 亏损风险评分 + 波动率风险评分

- **持仓风险评分**: `(当前持仓 / 最大持仓) * 30` （最高30分）
- **亏损风险评分**: `(亏损 / 单日最大亏损) * 40` （最高40分）
- **波动率风险评分**: `min(波动率 / 0.1, 1) * 30` （最高30分）

---

## 最佳实践

### 1. 风险参数配置建议

#### 保守型投资者
```json
{
  "max_position": 5000,
  "max_daily_loss": 500,
  "max_total_loss": 2000,
  "stop_loss_threshold": 0.03,
  "take_profit_threshold": 0.08,
  "enable_auto_stop": true
}
```

#### 稳健型投资者
```json
{
  "max_position": 10000,
  "max_daily_loss": 1000,
  "max_total_loss": 5000,
  "stop_loss_threshold": 0.05,
  "take_profit_threshold": 0.10,
  "enable_auto_stop": true
}
```

#### 激进型投资者
```json
{
  "max_position": 20000,
  "max_daily_loss": 2000,
  "max_total_loss": 10000,
  "stop_loss_threshold": 0.08,
  "take_profit_threshold": 0.15,
  "enable_auto_stop": true
}
```

### 2. 交易前必做的风险检查

在每次交易前，都应该调用风险检查接口：

```python
# 示例代码
async def execute_trade_with_risk_check(bot_id, position_value, order_value):
    # 1. 检查风险
    risk_response = await check_bot_risk(
        bot_id=bot_id,
        request=RiskCheckRequest(
            position_value=position_value,
            order_value=order_value
        )
    )

    # 2. 如果风险检查未通过，取消交易
    if not risk_response.passed:
        logger.warning(f"风险检查未通过: {risk_response.errors}")
        return False

    # 3. 如果风险等级过高，发送警告
    if risk_response.risk_level in ["high", "critical"]:
        send_risk_alert(risk_response)

    # 4. 执行交易
    await execute_trade(bot_id, position_value, order_value)

    return True
```

### 3. 定期监控风险等级

建议每隔一段时间检查一次机器人的风险等级：

```python
# 每小时检查一次
@repeat_every(seconds=3600)
async def monitor_risk_levels():
    for bot_id in running_bots:
        risk_report = await get_bot_risk_report(bot_id)

        if risk_report['risk_level'] == 'critical':
            # 发送紧急通知
            send_critical_alert(bot_id, risk_report)
            # 考虑自动停止机器人
            await stop_bot(bot_id)
```

### 4. 使用止损保护

虽然机器人有内置的策略，但额外的止损保护非常重要：

1. **设置合理的止损阈值**：建议在 3%-5% 之间
2. **启用自动止损**：确保 `enable_auto_stop` 为 `true`
3. **监控止损触发**：设置止损触发时的通知

### 5. 资金管理建议

- **不要投入全部资金**：建议只用账户资金的 20%-30% 进行交易
- **分散投资**：不要将所有资金投入到一个交易对
- **定期止盈**：达到盈利目标后，考虑部分平仓
- **保留备用资金**：应对极端市场情况

---

## 注意事项

1. **风险管理器生命周期**
   - 风险管理器在机器人启动时初始化
   - 风险管理器在机器人停止时销毁
   - 停止机器人时会生成最终风险报告

2. **每日限制自动重置**
   - 每日亏损限制和订单数限制会在每天自动重置
   - 重置时间根据服务器时区确定（通常是 UTC 00:00）

3. **风险报告的准确性**
   - 风险报告基于机器人的交易记录计算
   - 确保机器人正常运行才能获取准确的风险报告

4. **异常情况处理**
   - 如果市场价格剧烈波动，可能会触发多个止损
   - 建议设置合理的止损阈值，避免过度频繁止损
   - 在极端市场情况下，建议手动停止机器人

---

## 总结

风险管理系统为您的交易提供了多层次的保护：

1. ✅ **事前预防**：在交易前检查所有风险限制
2. ✅ **事中控制**：实时监控风险等级和持仓情况
3. ✅ **事后分析**：提供详细的风险报告和统计信息

合理使用风险管理系统，可以有效降低交易风险，保护您的资金安全！
