# Mac 本地部署 - 逐步指南

> 📅 最后更新：2025年1月2日
> 🎯 适用版本：v1.0

---

## 📋 前置检查

在开始之前，请在终端中执行以下命令检查你的 Mac 环境：

### 检查 1：Python 版本

```bash
python3 --version
```

**要求**: Python 3.8 或更高版本

如果未安装 Python，访问 https://www.python.org/downloads/

---

### 检查 2：Conda 是否已安装

```bash
conda --version
```

**要求**: Conda 或 Miniforge

如果未安装，执行：
```bash
# Apple Silicon (M1/M2/M3)
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh
bash Miniforge3-MacOSX-arm64.sh

# Intel Mac
# curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh
# bash Miniforge3-MacOSX-x86_64.sh
```

安装后**重启终端**。

---

## 🚀 开始部署

### 步骤 1：进入项目目录

**选项 A：从 GitHub 克隆（推荐）**

```bash
cd ~/Desktop
git clone https://github.com/wanian2026/sirenkaifashiyong.git
cd sirenkaifashiyong
```

**选项 B：使用本地已有代码**

```bash
cd ~/Desktop/sirenkaifashiyong
```

**验证**：执行 `ls -la`，应该能看到 `app/`、`workflow/`、`requirements.txt` 等文件。

---

### 步骤 2：创建 Conda 环境

```bash
# 创建名为 cryptobot 的环境，使用 Python 3.12
conda create -n cryptobot python=3.12 -y
```

**激活环境**：
```bash
conda activate cryptobot
```

**验证激活成功**：终端提示符前应该显示 `(cryptobot)`

---

### 步骤 3：安装依赖

使用提供的自动安装脚本（推荐）：

```bash
bash install_with_conda.sh
```

**或者手动安装**：

```bash
# 1. 使用 Conda 安装数据科学包
conda install pandas numpy -y

# 2. 安装核心依赖
pip install fastapi uvicorn langgraph langchain ccxt

# 3. 安装数据库相关
pip install sqlalchemy alembic bcrypt python-jose passlib

# 4. 安装其他依赖
pip install python-multipart websockets pydantic pydantic-settings
pip install python-dotenv aiohttp jinja2
```

**安装时间**：约 3-5 分钟（取决于网速）

---

### 步骤 4：验证依赖安装

执行以下命令确认所有依赖都已正确安装：

```bash
python -c "import fastapi; print('✅ fastapi:', fastapi.__version__)"
python -c "import uvicorn; print('✅ uvicorn:', uvicorn.__version__)"
python -c "import langgraph; print('✅ langgraph:', langgraph.__version__)"
python -c "import langchain; print('✅ langchain:', langchain.__version__)"
python -c "import ccxt; print('✅ ccxt:', ccxt.__version__)"
python -c "import sqlalchemy; print('✅ sqlalchemy:', sqlalchemy.__version__)"
python -c "import bcrypt; print('✅ bcrypt:', bcrypt.__version__)"
python -c "import pandas; print('✅ pandas:', pandas.__version__)"
```

如果所有检查都显示 ✅，说明安装成功！

---

### 步骤 5：配置环境变量

```bash
# 1. 复制环境配置文件
cp .env.example .env

# 2. 生成随机密钥
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

**复制上面生成的 SECRET_KEY**（类似：`SECRET_KEY=8dFh5_sN9xPq2vL4_mR7tZ1wY3cKj6bGhV`）

```bash
# 3. 编辑配置文件
nano .env
```

**修改以下配置**：

```env
# 数据库配置（使用 SQLite，Mac 内置）
DATABASE_URL=sqlite:///./crypto_bot.db

# JWT 密钥（粘贴上面生成的随机字符串）
SECRET_KEY=粘贴-上面生成的-随机-密钥

# 其他配置保持默认即可
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API 服务配置
API_HOST=0.0.0.0
API_PORT=8000

# 交易所 API（用于实盘交易，模拟模式留空即可）
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

**保存并退出**：
- 按 `Ctrl + O` 保存
- 按 `Enter` 确认
- 按 `Ctrl + X` 退出

---

### 步骤 6：初始化数据库

使用一键修复脚本（推荐）：

```bash
bash quick_fix.sh
```

**或手动执行**：

```bash
# 1. 清理缓存（重要！）
bash clean_cache.sh

# 2. 删除旧数据库（如果存在）
rm -f crypto_bot.db

# 3. 初始化数据库
python init_db.py
```

**预期输出**：

```
创建数据库表...
数据库表创建完成!
默认管理员用户已创建:
用户名: admin
密码: admin123
请登录后立即修改密码!
```

✅ 如果看到上面的输出，说明数据库初始化成功！

---

### 步骤 7：启动服务

**方法 A：使用启动脚本（推荐）**

```bash
./start.sh
```

**方法 B：手动启动**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**预期输出**：

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

✅ 如果看到上面的输出，说明服务启动成功！

---

### 步骤 8：访问 Web 界面

在浏览器中打开以下地址：

#### 🖥️ 主界面
```
http://localhost:8000/static/index.html
```

#### 📚 API 文档
```
http://localhost:8000/docs
```

#### 🏥 健康检查
```
http://localhost:8000/health
```

---

## 🔐 首次登录

登录信息：

- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **登录后建议立即修改密码！**

---

## 🎯 使用流程

### 1. 创建交易机器人

1. 登录系统
2. 点击"机器人管理" → "创建机器人"
3. 填写配置：
   - **机器人名称**: 例如 "BTC网格交易机器人"
   - **交易所**: Binance（默认）
   - **交易对**: BTC/USDT
   - **策略**: 对冲网格策略
   - **投资金额**: 1000 USDT（建议从小金额开始）
   - **网格层数**: 10-20（建议 10）
   - **网格间距**: 1-3%（建议 2%）
4. 点击"创建"

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

### Q1: 端口 8000 被占用

**错误信息**:
```
[Errno 48] Address already in use
```

**解决方法**：

```bash
# 查找占用进程
lsof -i :8000

# 杀死进程（替换 <PID> 为实际的进程 ID）
kill -9 <PID>
```

或修改端口：
```bash
# 编辑 .env 文件
nano .env
# 修改 API_PORT=8001
```

---

### Q2: 数据库初始化失败

**错误信息**:
```
ModuleNotFoundError: No module named 'sqlalchemy'
```

**解决方法**：

```bash
# 确保在 cryptobot 环境中
conda activate cryptobot

# 清理缓存并重新安装
bash clean_cache.sh
pip install sqlalchemy

# 重新初始化
python init_db.py
```

---

### Q3: bcrypt 模块错误

**错误信息**:
```
(trapped) error reading bcrypt version
```

**解决方法**：

```bash
# 卸载旧版本
pip uninstall passlib -y

# 安装正确的 bcrypt 版本
pip install bcrypt==4.1.2

# 清理缓存并重新初始化
bash quick_fix.sh
```

---

### Q4: pandas 安装失败

**错误信息**:
```
error: metadata-generation-failed
```

**解决方法**：

```bash
# 使用 Conda 安装 pandas（推荐）
conda install pandas numpy -y

# 如果仍然失败，查看 FIX_PANDAS_INSTALL.md
```

---

### Q5: 服务启动失败

**解决方法**：

```bash
# 1. 检查环境是否激活
conda activate cryptobot

# 2. 检查依赖是否安装
pip list | grep fastapi
pip list | grep uvicorn

# 3. 清理缓存
bash clean_cache.sh

# 4. 重新启动服务
./start.sh
```

---

## 📝 快速命令参考

### 日常使用

```bash
# 激活环境
conda activate cryptobot

# 进入项目目录
cd ~/Desktop/sirenkaifashiyong

# 启动服务
./start.sh

# 停止服务
Ctrl + C
```

### 维护命令

```bash
# 清理缓存
bash clean_cache.sh

# 重新初始化数据库
bash quick_fix.sh

# 查看日志
tail -f logs/app.log

# 查看进程
ps aux | grep uvicorn

# 杀死进程
kill -9 <PID>
```

---

## 🔄 更新代码

从 GitHub 拉取最新代码：

```bash
cd ~/Desktop/sirenkaifashiyong
git pull origin main

# 如果有新的依赖
pip install -r requirements.txt

# 如果数据库有变化
bash quick_fix.sh

# 重启服务
./start.sh
```

---

## 📖 相关文档

| 文档 | 说明 |
|------|------|
| `README.md` | 项目总体介绍 |
| `QUICKSTART.md` | 快速开始指南 |
| `MAC_DEPLOYMENT_GUIDE.md` | 详细部署文档 |
| `FIX_BCRYPT_ERROR.md` | bcrypt 问题修复 |
| `FIX_DATABASE_INSTALL.md` | 数据库安装修复 |
| `FIX_PANDAS_INSTALL.md` | pandas 安装修复 |
| `INIT_DB_FIX.md` | 数据库初始化修复 |

---

## 🎉 部署完成！

恭喜！你的加密货币交易系统已经成功部署在 Mac 本地！

### 下一步

1. ✅ 访问 http://localhost:8000/static/index.html
2. ✅ 使用 `admin` / `admin123` 登录
3. ✅ 创建你的第一个交易机器人
4. ✅ 开始自动化交易之旅！

---

## 📞 获取帮助

遇到问题？

1. 查看本文档的"常见问题排查"部分
2. 查看相关修复文档（FIX_*.md）
3. 检查日志：`tail -f logs/app.log`

---

**祝你使用愉快！** 🚀
