# 🚀 快速开始指南

## ⚡ 3 分钟快速部署

### 1️⃣ 克隆项目

```bash
git clone https://github.com/wanian2026/sirenkaifashiyong.git
cd sirenkaifashiyong
```

### 2️⃣ 一键部署

```bash
chmod +x deploy.sh
./deploy.sh
```

这个脚本会自动完成：
- ✅ 创建虚拟环境
- ✅ 安装所有依赖
- ✅ 安装和配置 PostgreSQL
- ✅ 安装和配置 Redis
- ✅ 创建数据库和表
- ✅ 创建默认用户 (admin / admin123)

### 3️⃣ 启动服务

```bash
chmod +x start.sh
./start.sh
```

### 4️⃣ 访问界面

打开浏览器访问：

- **🎯 极简界面**: http://localhost:8000/static/ultra_minimal.html
- **📚 API 文档**: http://localhost:8000/docs
- **🔑 默认账号**: `admin` / `admin123`

---

## 📝 常用命令

### 启动/停止

```bash
# 启动服务
./start.sh

# 停止服务
./stop.sh

# 或手动启动
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 测试

```bash
# 运行部署测试
./test_deployment.sh

# 测试 API
curl http://localhost:8000/api/v1/health
```

### 查看日志

```bash
# 查看应用日志
tail -f logs/app.log

# 查看 PostgreSQL 日志
tail -f /opt/homebrew/var/log/postgresql@14.log

# 查看 Redis 日志
tail -f /opt/homebrew/var/log/redis.log
```

---

## 🎯 功能清单

### 核心功能
- ✅ 代号A策略（对冲马丁格尔）
- ✅ 实时行情监控
- ✅ 机器人管理
- ✅ 交易记录
- ✅ 订单管理
- ✅ 风险管理
- ✅ 策略回测

### 交易功能
- ✅ 支持多个交易所（Binance, OKX）
- ✅ 多交易对支持
- ✅ 实时价格监控
- ✅ 自动交易执行
- ✅ 止损机制

### 管理功能
- ✅ 用户管理
- ✅ 审计日志
- ✅ 性能监控
- ✅ 数据库管理
- ✅ 系统设置

---

## ⚙️ 代号A策略

### 策略说明

**代号A策略**是一个基于对冲马丁格尔的智能交易策略：

1. **初始设置**: 同时开一个多单和一个空单
2. **上涨触发**: 价格 ≥ 多单成本价 × (1 + 上涨阈值) 时，平多开多
3. **下跌触发**: 价格 ≤ 空单成本价 × (1 - 下跌阈值) 时，平空开空
4. **止损机制**: 多单跌破止损线或空单突破止损线时强制平仓

### 创建机器人

1. 登录系统
2. 进入"机器人管理"标签
3. 点击"创建机器人"
4. 填写配置：
   - 名称: `我的代号A机器人`
   - 交易所: `Binance`
   - 交易对: `BTC/USDT`
   - 策略: `代号A策略`
   - 单边投资金额: `1000`
   - 上涨阈值: `2%`
   - 下跌阈值: `2%`
   - 止损比例: `10%`
5. 点击"创建"
6. 点击"启动"

### 运行回测

1. 进入"回测"标签
2. 点击"新建回测"
3. 填写配置：
   - 策略: `代号A策略`
   - 交易对: `BTC/USDT`
   - 时间范围: 最近30天
   - 参数: 使用默认值
4. 点击"运行回测"
5. 查看回测结果

---

## 🐛 常见问题

### PostgreSQL 连接失败

```bash
# 启动 PostgreSQL
brew services start postgresql@14

# 或检查端口
lsof -i :5432
```

### Redis 连接失败

```bash
# 启动 Redis
brew services start redis

# 测试连接
redis-cli ping
```

### 端口被占用

```bash
# 查找占用进程
lsof -i :8000

# 更换端口
python -m uvicorn app.main:app --port 8001
```

### 虚拟环境问题

```bash
# 重新创建
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📚 详细文档

- **完整部署指南**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Python 清理指南**: [PYTHON_CLEANUP_GUIDE.md](PYTHON_CLEANUP_GUIDE.md)
- **README**: [README.md](README.md)

---

## 🔗 相关链接

- GitHub: https://github.com/wanian2026/sirenkaifashiyong
- API 文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📞 获取帮助

如果遇到问题：

1. 查看 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) 中的常见问题部分
2. 检查日志: `tail -f logs/app.log`
3. 运行测试: `./test_deployment.sh`
4. 提交 Issue: https://github.com/wanian2026/sirenkaifashiyong/issues

---

**开始使用吧！** 🎉
