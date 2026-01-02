# 数据分析系统使用指南

> 版本：1.0.0
> 更新时间：2025年1月2日

---

## 📋 目录

1. [功能概述](#功能概述)
2. [API 接口说明](#api-接口说明)
3. [使用示例](#使用示例)
4. [数据解读](#数据解读)
5. [最佳实践](#最佳实践)

---

## 功能概述

数据分析系统提供以下核心功能：

### 1. 仪表盘总览
- 机器人统计（总数、运行中、已停止）
- 交易统计（总次数、盈利/亏损交易）
- 盈亏统计（总盈亏、今日盈亏、最大盈利/亏损）
- 性能指标（胜率、投资回报率）
- 最近交易记录

### 2. 收益曲线
- 累计收益曲线
- 每日盈亏
- 回撤分析
- 支持多时间周期（1d、7d、30d、90d、all）

### 3. 交易统计
- 胜率
- 盈利因子
- 平均盈利/亏损
- 最大盈利/亏损
- 按交易对统计

### 4. 机器人性能
- 机器人基本信息
- 交易统计
- 订单统计
- 性能指标
- 运行时间

### 5. 交易热力图
- 每小时交易统计
- 交易活跃时段分析
- 盈利时段分析

---

## API 接口说明

### 1. 获取仪表盘总览

**接口**: `GET /api/analytics/dashboard`

**说明**: 获取用户的仪表盘总览数据，包括所有机器人和交易的汇总统计。

**响应示例**:
```json
{
  "bots": {
    "total": 5,
    "running": 3,
    "stopped": 2
  },
  "trades": {
    "total": 150,
    "winning_trades": 90,
    "losing_trades": 60
  },
  "pnl": {
    "total": 1250.50,
    "today": 85.20,
    "average": 8.34,
    "max_profit": 150.00,
    "max_loss": -45.00
  },
  "performance": {
    "win_rate": 60.0,
    "total_investment": 5000,
    "roi": 25.01
  },
  "recent_trades": [
    {
      "id": 150,
      "bot_id": 1,
      "trading_pair": "BTC/USDT",
      "side": "sell",
      "price": 50500,
      "amount": 0.01,
      "profit": 25.50,
      "created_at": "2025-01-02T10:30:00"
    }
  ],
  "timestamp": "2025-01-02T10:30:00"
}
```

### 2. 获取收益曲线

**接口**: `GET /api/analytics/profit-curve`

**查询参数**:
- `bot_id` (可选): 机器人ID，不指定则查询全部机器人
- `period` (可选): 时间周期，默认 `7d`
  - `1d`: 1天
  - `7d`: 7天
  - `30d`: 30天
  - `90d`: 90天
  - `all`: 全部

**响应示例**:
```json
{
  "period": "7d",
  "dates": ["2025-01-01", "2025-01-02", "2025-01-03"],
  "profit_curve": [0, 100, 250, 300],
  "daily_pnls": [0, 100, 150, 50],
  "cumulative_pnl": 300,
  "max_drawdown": -15.5,
  "drawdowns": [0, 0, -5.2, -15.5],
  "data_points": 4
}
```

### 3. 获取交易统计

**接口**: `GET /api/analytics/trade-statistics`

**查询参数**:
- `bot_id` (可选): 机器人ID，不指定则查询全部机器人

**响应示例**:
```json
{
  "total_trades": 150,
  "winning_trades": 90,
  "losing_trades": 60,
  "win_rate": 60.0,
  "profit_factor": 1.85,
  "average_win": 15.50,
  "average_loss": -8.33,
  "largest_win": 150.00,
  "largest_loss": -45.00,
  "average_trade": 8.34,
  "total_profit": 1395.00,
  "total_loss": -752.00,
  "net_profit": 643.00,
  "pair_statistics": {
    "BTC/USDT": {
      "trades": 80,
      "profit": 450.00,
      "winning": 50,
      "win_rate": 62.5
    },
    "ETH/USDT": {
      "trades": 70,
      "profit": 193.00,
      "winning": 40,
      "win_rate": 57.14
    }
  },
  "timestamp": "2025-01-02T10:30:00"
}
```

### 4. 获取机器人性能

**接口**: `GET /api/analytics/bot/{bot_id}/performance`

**路径参数**:
- `bot_id`: 机器人ID

**响应示例**:
```json
{
  "bot_id": 1,
  "bot_name": "BTC网格机器人",
  "trading_pair": "BTC/USDT",
  "strategy": "hedge_grid",
  "status": "running",
  "trades": {
    "total": 80,
    "total_profit": 820.00,
    "total_loss": -370.00,
    "net_profit": 450.00
  },
  "orders": {
    "total": 200,
    "pending": 10,
    "filled": 190
  }
}
```

### 5. 获取每小时交易统计

**接口**: `GET /api/analytics/hourly-trades`

**查询参数**:
- `bot_id` (可选): 机器人ID，不指定则查询全部机器人
- `days` (可选): 统计天数，默认 7，范围 1-90

**响应示例**:
```json
{
  "period": "7d",
  "heatmap_data": [
    {
      "day": 1,
      "hour": 9,
      "trades": 15,
      "profit": 120.50
    },
    {
      "day": 1,
      "hour": 10,
      "trades": 20,
      "profit": 85.30
    }
  ],
  "timestamp": "2025-01-02T10:30:00"
}
```

### 6. 获取分析总览

**接口**: `GET /api/analytics/overview`

**说明**: 一次性获取多个关键指标，用于仪表盘快速加载

**响应示例**:
```json
{
  "dashboard": { /* 仪表盘数据 */ },
  "profit_curve": { /* 收益曲线数据 */ },
  "trade_statistics": { /* 交易统计数据 */ },
  "timestamp": "2025-01-02T10:30:00"
}
```

---

## 使用示例

### 示例 1: 获取仪表盘数据

```bash
curl -X GET "http://localhost:8000/api/analytics/dashboard" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 示例 2: 获取过去7天的收益曲线

```bash
curl -X GET "http://localhost:8000/api/analytics/profit-curve?period=7d" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 示例 3: 获取指定机器人的收益曲线

```bash
curl -X GET "http://localhost:8000/api/analytics/profit-curve?bot_id=1&period=30d" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 示例 4: 获取交易统计

```bash
curl -X GET "http://localhost:8000/api/analytics/trade-statistics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 示例 5: 获取机器人性能

```bash
curl -X GET "http://localhost:8000/api/analytics/bot/1/performance" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 示例 6: 获取每小时交易统计

```bash
curl -X GET "http://localhost:8000/api/analytics/hourly-trades?days=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 数据解读

### 1. 胜率 (Win Rate)

**定义**: 盈利交易次数 / 总交易次数 × 100%

**解读**:
- **> 60%**: 优秀
- **50% - 60%**: 良好
- **40% - 50%**: 一般
- **< 40%**: 需要改进

### 2. 盈利因子 (Profit Factor)

**定义**: 总盈利 / 总亏损

**解读**:
- **> 2.0**: 优秀
- **1.5 - 2.0**: 良好
- **1.0 - 1.5**: 一般
- **< 1.0**: 需要改进

### 3. 最大回撤 (Max Drawdown)

**定义**: 从历史最高点到最低点的最大跌幅

**解读**:
- **< 10%**: 优秀
- **10% - 20%**: 良好
- **20% - 30%**: 需要注意
- **> 30%**: 风险过高

### 4. 投资回报率 (ROI)

**定义**: (总盈亏 / 总投资金额) × 100%

**解读**:
- **> 50%**: 优秀
- **20% - 50%**: 良好
- **0% - 20%**: 一般
- **< 0%**: 亏损

---

## 最佳实践

### 1. 定期查看仪表盘

建议每天或每周查看一次仪表盘，了解：
- 总体盈亏情况
- 机器人运行状态
- 最近交易记录

### 2. 分析收益曲线

关注：
- 收益曲线是否稳定上升
- 回撤是否在可接受范围内
- 是否有明显的亏损期

### 3. 监控交易统计

定期检查：
- 胜率是否稳定
- 盈利因子是否健康
- 平均盈利和平均亏损的比例

### 4. 优化交易策略

根据数据分析结果：
- 胜率低 → 调整入场条件或止损设置
- 盈利因子低 → 提高止盈目标或降低止损
- 回撤过大 → 降低仓位或增加止损保护

### 5. 机器人对比分析

使用机器人性能接口对比不同机器人的表现：
- 哪个机器人盈利最高
- 哪个机器人风险控制最好
- 哪个机器人最适合当前市场环境

---

## 前端集成示例

### 1. 仪表盘页面

```javascript
// 获取仪表盘数据
async function loadDashboard() {
  const response = await fetch('/api/analytics/dashboard', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const data = await response.json();

  // 显示机器人统计
  document.getElementById('total-bots').textContent = data.bots.total;
  document.getElementById('running-bots').textContent = data.bots.running;

  // 显示盈亏统计
  document.getElementById('total-pnl').textContent = data.pnl.total.toFixed(2);
  document.getElementById('today-pnl').textContent = data.pnl.today.toFixed(2);

  // 显示性能指标
  document.getElementById('win-rate').textContent = data.performance.win_rate.toFixed(1) + '%';
  document.getElementById('roi').textContent = data.performance.roi.toFixed(1) + '%';

  // 显示最近交易
  renderRecentTrades(data.recent_trades);
}
```

### 2. 收益曲线图表

```javascript
// 使用 Chart.js 绘制收益曲线
async function loadProfitChart(period = '7d') {
  const response = await fetch(`/api/analytics/profit-curve?period=${period}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const data = await response.json();

  const ctx = document.getElementById('profit-chart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.dates,
      datasets: [{
        label: '累计收益',
        data: data.profit_curve,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: `收益曲线 (${data.period})`
        }
      }
    }
  });
}
```

### 3. 交易热力图

```javascript
// 绘制交易热力图
async function loadHeatmap(days = 7) {
  const response = await fetch(`/api/analytics/hourly-trades?days=${days}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const data = await response.json();

  // 构建热力图矩阵 (7天 x 24小时)
  const heatmap = new Array(7).fill(0).map(() => new Array(24).fill(0));

  data.heatmap_data.forEach(item => {
    heatmap[item.day][item.hour] = item.trades;
  });

  // 使用热力图库绘制
  drawHeatmap(heatmap);
}
```

---

## 注意事项

1. **数据延迟**
   - 仪表盘数据可能有轻微延迟（通常在几秒内）
   - 建议在前端实现自动刷新（每30秒或1分钟）

2. **数据准确性**
   - 确保机器人正常运行才能获取准确的数据
   - 停止的机器人仍然有历史数据

3. **性能考虑**
   - 获取大量历史数据可能需要较长时间
   - 建议使用适当的时间周期参数

4. **数据隐私**
   - 所有数据都是用户特定的，不会泄露给其他用户
   - 使用 JWT Token 进行身份验证

---

## 总结

数据分析系统为您的交易提供了全面的分析工具：

1. ✅ **实时监控**：通过仪表盘实时了解整体情况
2. ✅ **趋势分析**：通过收益曲线分析长期趋势
3. ✅ **性能评估**：通过交易统计评估策略表现
4. ✅ **对比分析**：对比不同机器人和交易对的表现
5. ✅ **时段分析**：通过热力图找出最佳交易时段

合理使用数据分析工具，可以帮助您：
- 优化交易策略
- 降低交易风险
- 提高盈利能力
- 做出更明智的交易决策
