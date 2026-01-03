# 策略调整说明

## 修改内容

根据用户要求，已将交易策略精简，只保留 **Code A策略**，并添加了阈值、止损、止盈等参数的手动输入功能。

## 修改的文件

### 1. static/ultra_minimal.html

#### 1.1 机器人创建表单

**策略选择**（行611）：
```html
<!-- 修改前 -->
<select id="botStrategy">
    <option value="grid">网格策略</option>
    <option value="hedge_grid">对冲网格</option>
    <option value="martingale">马丁格尔</option>
    <option value="mean_reversion">均值回归</option>
    <option value="momentum">动量策略</option>
    <option value="code_a">Code A策略</option>
</select>

<!-- 修改后 -->
<select id="botStrategy">
    <option value="code_a">Code A策略</option>
</select>
```

**新增参数输入框**（行617-634）：
```html
<!-- 新增阈值参数 -->
<div class="form-row">
    <div class="form-group">
        <label>阈值(%)</label>
        <input type="number" id="botThreshold" value="1" step="0.1">
    </div>
    <div class="form-group">
        <label>止损阈值(%)</label>
        <input type="number" id="botStopLoss" value="5" step="0.1">
    </div>
</div>

<!-- 新增止盈和最大仓位参数 -->
<div class="form-row">
    <div class="form-group">
        <label>止盈阈值(%)</label>
        <input type="number" id="botTakeProfit" value="10" step="0.1">
    </div>
    <div class="form-group">
        <label>最大仓位(USDT)</label>
        <input type="number" id="botMaxPosition" value="10000">
    </div>
</div>
```

#### 1.2 回测模态框

**策略选择**（行659）：
```html
<!-- 修改前 -->
<select id="backtestStrategy">
    <option value="grid">网格策略</option>
    <option value="hedge_grid">对冲网格</option>
    <option value="martingale">马丁格尔</option>
    <option value="mean_reversion">均值回归</option>
    <option value="momentum">动量策略</option>
    <option value="code_a">Code A策略</option>
</select>

<!-- 修改后 -->
<select id="backtestStrategy">
    <option value="code_a">Code A策略</option>
</select>
```

#### 1.3 JavaScript代码更新（行1073-1088）

**修改前**：
```javascript
async function createBot() {
    const data = {
        name: document.getElementById('botName').value,
        exchange_id: document.getElementById('botExchange').value,
        symbol: document.getElementById('botSymbol').value,
        strategy_type: document.getElementById('botStrategy').value,
        investment_amount: parseFloat(document.getElementById('botInvestment').value),
        grid_levels: parseInt(document.getElementById('botGridLevels').value),
        grid_spacing: parseFloat(document.getElementById('botGridSpacing').value) / 100
    };
```

**修改后**：
```javascript
async function createBot() {
    const config = {
        investment_amount: parseFloat(document.getElementById('botInvestment').value),
        grid_levels: parseInt(document.getElementById('botGridLevels').value),
        grid_spacing: parseFloat(document.getElementById('botGridSpacing').value) / 100,
        threshold: parseFloat(document.getElementById('botThreshold').value) / 100,
        stop_loss_threshold: parseFloat(document.getElementById('botStopLoss').value) / 100,
        take_profit_threshold: parseFloat(document.getElementById('botTakeProfit').value) / 100,
        max_position: parseFloat(document.getElementById('botMaxPosition').value)
    };

    const data = {
        name: document.getElementById('botName').value,
        exchange: document.getElementById('botExchange').value,
        trading_pair: document.getElementById('botSymbol').value,
        strategy: document.getElementById('botStrategy').value,
        config: config
    };
```

### 2. quick_setup.py

#### 2.1 策略选择（行190-196）

**修改前**：
```python
# 策略选择
print("\n可用策略:")
print("  1. hedge_grid (对冲网格)")
print("  2. mean_reversion (均值回归)")
print("  3. momentum (动量策略)")
strategy_map = {"1": "hedge_grid", "2": "mean_reversion", "3": "momentum"}
strategy_choice = input("请选择策略 (1-3) [默认: 1]: ").strip() or "1"
strategy = strategy_map.get(strategy_choice, "hedge_grid")
```

**修改后**：
```python
# 策略选择
print("\n可用策略:")
print("  1. code_a (Code A策略)")
strategy_map = {"1": "code_a"}
strategy_choice = input("请选择策略 (1-1) [默认: 1]: ").strip() or "1"
strategy = strategy_map.get(strategy_choice, "code_a")
```

#### 2.2 新增阈值参数输入（行203-205）

```python
threshold = float(input("阈值，如 0.01 表示 1% [默认: 0.01]: ").strip() or "0.01")
```

#### 2.3 配置字典更新（行208-218）

**修改前**：
```python
config = {
    "grid_levels": grid_levels,
    "grid_spacing": grid_spacing,
    "investment_amount": investment_amount,
    "max_position": max_position,
    "stop_loss_threshold": stop_loss,
    "take_profit_threshold": take_profit,
    "enable_auto_stop": True,
    "dynamic_grid": False,
    "batch_build": False
}
```

**修改后**：
```python
config = {
    "grid_levels": grid_levels,
    "grid_spacing": grid_spacing,
    "threshold": threshold,
    "investment_amount": investment_amount,
    "max_position": max_position,
    "stop_loss_threshold": stop_loss,
    "take_profit_threshold": take_profit,
    "enable_auto_stop": True,
    "dynamic_grid": False,
    "batch_build": False
}
```

## 新增参数说明

### 参数列表

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| 阈值 (threshold) | 百分比 | 1% | 策略触发阈值 |
| 止损阈值 (stop_loss_threshold) | 百分比 | 5% | 止损触发阈值 |
| 止盈阈值 (take_profit_threshold) | 百分比 | 10% | 止盈触发阈值 |
| 最大仓位 (max_position) | USDT | 10000 | 最大持仓金额 |
| 网格层数 (grid_levels) | 整数 | 10 | 网格数量 |
| 网格间距 (grid_spacing) | 百分比 | 2% | 网格间距 |
| 投资金额 (investment_amount) | USDT | 1000 | 投资金额 |

### 参数配置建议

**保守配置**：
- 阈值：0.5-1%
- 止损：3-5%
- 止盈：8-10%
- 最大仓位：5000-10000 USDT

**激进配置**：
- 阈值：1-2%
- 止损：5-8%
- 止盈：15-20%
- 最大仓位：10000-20000 USDT

## 使用方法

### 通过Web界面

1. 访问 http://localhost:8000/static/ultra_minimal.html
2. 登录系统
3. 点击「机器人管理」→「创建机器人」
4. 选择策略：Code A策略
5. 填写参数：
   - 交易所：Binance或OKX
   - 交易对：如 BTC/USDT
   - 投资金额：如 1000
   - 网格层数：如 10
   - 网格间距：如 2
   - **阈值**：如 1
   - **止损阈值**：如 5
   - **止盈阈值**：如 10
   - **最大仓位**：如 10000
6. 点击「创建」

### 通过快速配置脚本

```bash
python quick_setup.py
```

按照提示输入参数：
- 阈值：输入 0.01 表示 1%
- 止损阈值：输入 0.05 表示 5%
- 止盈阈值：输入 0.10 表示 10%

## 验证结果

### 前端界面 ✅
- 机器人创建表单：只显示 Code A策略
- 回测模态框：只显示 Code A策略
- 参数输入框：阈值、止损、止盈、最大仓位全部可用

### 快速配置脚本 ✅
- 策略选择：只有 Code A策略
- 参数输入：支持阈值、止损、止盈等参数

### 数据提交 ✅
- 前端正确构建 config 对象
- 所有参数正确传递给后端

## 影响范围

- ✅ 只影响创建新机器人
- ✅ 已有机器人不受影响
- ✅ 前端和后端数据格式兼容
- ✅ 所有参数均可手动输入

## 后续优化建议

1. 可以添加参数验证，确保输入值在合理范围内
2. 可以添加参数说明和提示
3. 可以添加参数预设模板（保守、平衡、激进）
4. 可以根据交易对自动推荐参数
