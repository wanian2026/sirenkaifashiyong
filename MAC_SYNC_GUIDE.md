# Mac 本地开发环境同步指南

## 🚀 快速同步步骤（推荐）

### 1. 克隆项目到 Mac

```bash
# 在 Mac 终端执行
git clone https://github.com/wanian2026/sirenkaifashiyong.git
cd sirenkaifashiyong
```

### 2. 安装依赖

```bash
# 确保已安装 Python 3.10+
python3 --version

# 安装项目依赖
pip3 install -r requirements.txt

# 如果某些包安装失败，单独安装
pip3 install fastapi uvicorn[standard] sqlalchemy redis aioredis ccxt websockets
```

### 3. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env  # 或使用你喜欢的编辑器
```

`.env` 文件配置示例：

```env
# 数据库配置
DATABASE_URL=sqlite:///./crypto_trading.db

# Redis 配置（可选）
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API 密钥配置
EXCHANGE_API_KEY=your_binance_api_key
EXCHANGE_API_SECRET=your_binance_api_secret

# JWT 配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 审计日志
AUDIT_LOG_ENABLED=true
```

### 4. 初始化数据库

```bash
# SQLite 会自动创建数据库文件
python3 -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine); print('数据库初始化完成')"
```

### 5. 启动服务

```bash
# 开发模式（带热重载）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. 访问 Web 界面

打开浏览器访问：

- **主页**: http://localhost:8000/
- **极简管理界面**: http://localhost:8000/static/simple.html
- **完整管理界面**: http://localhost:8000/static/management.html
- **主仪表盘**: http://localhost:8000/static/index.html
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

---

## 🔄 保持同步

### 拉取最新代码

```bash
cd /path/to/sirenkaifashiyong
git pull origin main
```

### 推送本地修改到云端（如果有）

```bash
git add .
git commit -m "your commit message"
git push origin main
```

---

## 📦 安装 Redis（可选）

如果需要使用 Redis 缓存功能：

```bash
# macOS 使用 Homebrew 安装
brew install redis

# 启动 Redis
brew services start redis

# 验证 Redis 运行
redis-cli ping
# 应返回: PONG
```

---

## 🔧 常见问题排查

### 问题 1: 端口被占用

```bash
# 查看 8000 端口占用情况
lsof -i :8000

# 终止进程
kill -9 <PID>

# 或使用其他端口
uvicorn app.main:app --port 8080
```

### 问题 2: Python 版本不兼容

```bash
# 安装 pyenv 管理多版本 Python
brew install pyenv

# 安装 Python 3.10
pyenv install 3.10.0
pyenv global 3.10.0

# 验证版本
python --version
```

### 问题 3: 依赖包安装失败

```bash
# 升级 pip
pip3 install --upgrade pip

# 使用国内镜像源加速
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 4: 静态文件 404

确认当前目录是项目根目录，然后启动服务：

```bash
cd /path/to/sirenkaifashiyong
pwd  # 应该显示项目路径
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧪 测试功能

### 测试 API 端点

```bash
# 健康检查
curl http://localhost:8000/health

# 系统信息
curl http://localhost:8000/api/system/info

# 获取机器人列表
curl http://localhost:8000/api/bots/
```

### 测试 WebSocket 连接

```bash
# 使用 wscat 工具测试
npm install -g wscat
wscat -c ws://localhost:8000/ws/bots
```

---

## 📝 项目结构

```
sirenkaifashiyong/
├── app/                    # 应用主目录
│   ├── main.py            # FastAPI 主程序
│   ├── config.py          # 配置文件
│   ├── database.py        # 数据库连接
│   ├── models.py          # 数据模型
│   ├── routers/           # API 路由
│   ├── services/          # 业务逻辑
│   └── websocket/         # WebSocket 处理
├── static/                # 静态文件（HTML/CSS/JS）
├── templates/             # 模板文件
├── tests/                 # 测试文件
├── requirements.txt       # Python 依赖
├── .env                   # 环境变量（不提交到 Git）
├── .gitignore            # Git 忽略规则
└── README.md             # 项目说明
```

---

## 🎯 核心功能模块

- ✅ **对冲网格策略** - 自动化对冲交易
- ✅ **均值回归策略** - 基于统计均值回归
- ✅ **动量策略** - 捕捉价格动量
- ✅ **回测引擎** - 策略回测和优化
- ✅ **风险管理** - 实时风险监控
- ✅ **WebSocket 实时推送** - 市场数据实时更新
- ✅ **RBAC 权限管理** - 基于角色的访问控制
- ✅ **Redis 缓存** - 提升性能
- ✅ **数据分析仪表盘** - 可视化数据展示
- ✅ **日志管理** - 系统日志查询
- ✅ **性能监控** - 实时性能指标

---

## 💡 下一步建议

1. **配置交易所 API**：在 `.env` 中填写真实的 Binance API 密钥
2. **测试策略**：先在模拟环境测试策略逻辑
3. **监控运行**：使用管理界面监控机器人状态
4. **风险控制**：合理设置止损止盈参数

---

## 📞 获取帮助

遇到问题时：
1. 检查日志：`tail -f logs/app.log`
2. 查看错误信息：浏览器控制台 (F12)
3. 查看 API 文档：http://localhost:8000/docs
4. 提交 Issue：https://github.com/wanian2026/sirenkaifashiyong/issues

---

**更新时间**: 2025-01-03  
**当前版本**: v1.0.0
