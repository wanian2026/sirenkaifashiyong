# Mac本地部署完整指南

## 📋 前置条件检查

在开始部署之前，请确保你的Mac已安装：

### 1. 检查Python版本

打开**终端**（Terminal），执行：

```bash
python3 --version
```

**要求**: Python 3.8 或更高版本

**如果未安装**:
- 访问 https://www.python.org/downloads/
- 下载并安装最新版Python

### 2. 检查Git版本

```bash
git --version
```

**如果未安装**:
```bash
# 使用Homebrew安装
brew install git
```

---

## 🚀 完整部署步骤

### 步骤1: 进入项目目录

```bash
cd sirenkaifashiyong
```

**验证项目**:
```bash
ls -la
```

你应该看到以下文件：
```
.env.example
.gitignore
README.md
QUICKSTART.md
requirements.txt
start.sh
app/
workflow/
static/
```

---

### 步骤2: 创建Python虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

**验证激活成功**:
终端提示符前面会显示 `(venv)`

---

### 步骤3: 升级pip并安装依赖

```bash
# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

⏳ **等待安装完成**（约2-5分钟，取决于网速）

**常见问题**:

如果安装失败，尝试：
```bash
# 单独安装每个包
pip install fastapi uvicorn langgraph langchain
pip install ccxt sqlalchemy alembic psycopg2-binary
pip install python-jose passlib bcrypt
pip install python-multipart websockets
pip install pydantic pydantic-settings
pip install python-dotenv aiohttp pandas numpy jinja2
```

---

### 步骤4: 配置环境变量

```bash
# 复制环境配置文件
cp .env.example .env
```

**编辑环境配置文件**:

```bash
nano .env
```

**必须修改的配置**:

```env
# 数据库配置（默认使用SQLite）
DATABASE_URL=sqlite:///./crypto_bot.db

# JWT密钥（必须修改！生成一个随机字符串）
SECRET_KEY=your-super-secret-key-change-this-to-random-string

# JWT配置
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API服务配置
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# 交易所API配置（用于实盘交易，模拟模式留空）
EXCHANGE_ID=binance
API_KEY=
API_SECRET=

# 策略配置
GRID_LEVELS=10
GRID_SPACING=0.02
INVESTMENT_AMOUNT=1000

# 日志配置
LOG_LEVEL=INFO
```

**生成随机SECRET_KEY的方法**:

在**另一个终端窗口**执行：
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

复制生成的随机字符串（类似：`8dFh5_sN9xPq2vL4_mR7tZ1wY3cKj6bGhV`）

粘贴到 `.env` 文件的 `SECRET_KEY=` 后面。

**nano编辑器操作**:
- `Ctrl + O` 保存
- `Enter` 确认
- `Ctrl + X` 退出

---

### 步骤5: 初始化数据库

```bash
python init_db.py
```

✅ **成功输出**:
```
创建数据库表...
数据库表创建完成!
默认管理员用户已创建:
用户名: admin
密码: admin123
请登录后立即修改密码!
```

⚠️ **首次登录后立即修改默认密码！**

---

### 步骤6: 启动服务

#### 方法A: 使用启动脚本（推荐）

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 运行启动脚本
./start.sh
```

#### 方法B: 手动启动

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 启动FastAPI服务（开发模式，支持热重载）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 方法C: 生产模式启动

```bash
# 多worker模式（性能更好）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**启动成功输出**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

### 步骤7: 访问Web界面

在浏览器中打开以下地址：

#### 主界面
📱 **http://localhost:8000/static/index.html**

#### API文档（Swagger UI）
📚 **http://localhost:8000/docs**

#### 健康检查
🏥 **http://localhost:8000/health**

---

## 🔐 首次登录

### 登录信息

- **用户名**: `admin`
- **密码**: `admin123`

### 修改默认密码

登录后立即修改密码（安全最佳实践）：

1. 打开数据库管理工具或命令行
2. 更新密码（需要重新哈希）
3. 或者在代码中实现修改密码功能

---

## 🎯 使用流程

### 1. 创建交易机器人

1. 点击"机器人管理" → "创建机器人"
2. 填写配置：
   - **机器人名称**: 例如 "BTC网格交易机器人"
   - **交易所**: Binance（默认）
   - **交易对**: BTC/USDT
   - **策略**: 对冲网格策略
   - **投资金额**: 1000 USDT（建议从小金额开始）
   - **网格层数**: 10-20（建议10）
   - **网格间距**: 1-3%（建议2%）

3. 点击"创建"

### 2. 启动机器人

在机器人卡片上点击"启动"按钮

### 3. 监控运行

- **仪表盘**: 查看市场数据和统计数据
- **机器人状态**: 点击"状态"按钮查看详细信息
- **交易记录**: 查看所有交易历史

### 4. 停止机器人

点击机器人卡片上的"停止"按钮

---

## 🛠️ 常见问题排查

### Q1: 端口8000被占用

**错误信息**:
```
[Errno 48] Address already in use
```

**解决方法1**: 修改端口
```bash
# 编辑.env文件
nano .env
# 修改: API_PORT=8001
```

**解决方法2**: 杀死占用进程
```bash
# 查找占用进程
lsof -i :8000

# 杀死进程
kill -9 <PID>
```

### Q2: 数据库初始化失败

**错误信息**:
```
sqlite3.OperationalError: database is locked
```

**解决方法**:
```bash
# 删除旧数据库
rm crypto_bot.db

# 重新初始化
python init_db.py
```

### Q3: 依赖安装失败

**解决方法**:
```bash
# 升级pip
pip install --upgrade pip

# 清理缓存
pip cache purge

# 重新安装
pip install -r requirements.txt
```

### Q4: WebSocket连接失败

**解决方法**:
1. 确保服务正在运行
2. 检查浏览器控制台错误（F12）
3. 尝试访问 http://localhost:8000/health

### Q5: 虚拟环境激活失败

**解决方法**:
```bash
# 确保Python3路径正确
which python3

# 重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### Q6: 权限问题

**错误信息**:
```
Permission denied: './start.sh'
```

**解决方法**:
```bash
chmod +x start.sh
./start.sh
```

---

## 🔄 停止服务

在终端按 `Ctrl + C` 停止服务

---

## 🚀 后台运行（可选）

如果想在后台运行服务，使用nohup：

```bash
# 后台运行并记录日志
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# 查看日志
tail -f server.log

# 停止后台服务
ps aux | grep uvicorn
kill -9 <PID>
```

---

## 📱 使用Screen运行（推荐）

```bash
# 创建screen会话
screen -S cryptobot

# 在screen中启动服务
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 分离screen会话（Ctrl + A, 然后按D）

# 重新连接screen会话
screen -r cryptobot

# 查看所有screen会话
screen -ls
```

---

## 🔧 配置PostgreSQL（可选，生产环境推荐）

如果使用PostgreSQL替代SQLite：

### 安装PostgreSQL

```bash
# 使用Homebrew安装
brew install postgresql@14

# 启动PostgreSQL
brew services start postgresql@14

# 创建数据库
createdb cryptobot
```

### 修改.env配置

```env
DATABASE_URL=postgresql://username:password@localhost/cryptobot
```

### 重新初始化数据库

```bash
rm crypto_bot.db
python init_db.py
```

---

## 📊 性能优化

### 1. 使用Gunicorn（生产环境）

```bash
pip install gunicorn

gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### 2. 启用缓存（Redis）

```bash
# 安装Redis
brew install redis

# 启动Redis
brew services start redis
```

---

## 🔒 安全加固

### 1. 使用HTTPS

配置Nginx反向代理并启用SSL证书。

### 2. 防火墙配置

```bash
# 配置macOS防火墙
系统设置 -> 安全性与隐私 -> 防火墙 -> 防火墙选项
```

### 3. 限制访问

修改.env配置：
```env
API_HOST=127.0.0.1  # 只允许本地访问
```

---

## 📝 快速命令参考

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务
uvicorn app.main:app --reload

# 查看日志
tail -f server.log

# 停止服务
Ctrl + C

# 重新初始化数据库
rm crypto_bot.db
python init_db.py

# 查看进程
ps aux | grep uvicorn

# 杀死进程
kill -9 <PID>

# 清理虚拟环境
deactivate
rm -rf venv
```

---

## 🎉 部署完成！

现在你的加密货币交易系统已经成功部署在Mac本地！

### 下一步

1. 访问 http://localhost:8000/static/index.html
2. 使用 admin / admin123 登录
3. 创建你的第一个交易机器人
4. 开始自动化交易之旅！

### 技术支持

遇到问题？查看以下文档：
- 完整文档: [README.md](README.md)
- 快速指南: [QUICKSTART.md](QUICKSTART.md)
- GitHub仓库: https://github.com/wanian2026/sirenkaifashiyong
