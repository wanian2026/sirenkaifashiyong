# 加密货币交易系统 - Mac本地部署指南

## 📋 目录

1. [系统要求](#系统要求)
2. [快速部署](#快速部署)
3. [详细部署步骤](#详细部署步骤)
4. [配置说明](#配置说明)
5. [启动与访问](#启动与访问)
6. [常见问题](#常见问题)
7. [生产环境建议](#生产环境建议)

---

## 系统要求

### 硬件要求
- **CPU**: Intel Core i5 或 Apple Silicon M1/M2/M3
- **内存**: 最低 4GB，推荐 8GB+
- **存储**: 至少 2GB 可用空间

### 软件要求
- **操作系统**: macOS 10.15 (Catalina) 或更高版本
- **Python**: 3.8 或更高版本
- **浏览器**: Chrome、Firefox、Safari 等现代浏览器

---

## 快速部署

### 一键部署（推荐新手）

```bash
# 1. 进入项目目录
cd sirenkaifashiyong

# 2. 执行一键部署脚本
bash install.sh

# 3. 启动服务
bash start.sh
```

### 部署完成后

访问地址: http://localhost:8000/static/index.html

默认账户:
- 用户名: `admin`
- 密码: `admin123`

⚠️ **安全提示**: 登录后请立即修改默认密码！

---

## 详细部署步骤

### 步骤 1: 安装系统依赖

#### 1.1 安装 Homebrew（如未安装）

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 1.2 安装 Python 3.8+

```bash
# 检查Python版本
python3 --version

# 如果版本低于3.8，安装新版本
brew install python@3.11
```

#### 1.3 安装 Git（如未安装）

```bash
brew install git
```

---

### 步骤 2: 获取项目代码

#### 方式一：从GitHub克隆

```bash
git clone https://github.com/wanian2026/sirenkaifashiyong.git
cd sirenkaifashiyong
```

#### 方式二：从本地复制

如果你已经将代码复制到本地，直接进入项目目录:

```bash
cd /path/to/your/project
```

---

### 步骤 3: 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

验证虚拟环境是否激活成功:

```bash
which python  # 应该显示: /path/to/project/venv/bin/python
```

---

### 步骤 4: 安装项目依赖

```bash
# 升级pip
pip install --upgrade pip setuptools wheel

# 安装依赖包
pip install -r requirements.txt
```

这一步可能需要几分钟时间，请耐心等待。

---

### 步骤 5: 配置环境变量

#### 5.1 创建.env文件

```bash
cp .env.example .env
```

#### 5.2 修改配置文件（可选）

```bash
nano .env
```

**最小化配置（仅需修改SECRET_KEY）:**

```env
# 必须修改为随机字符串！
SECRET_KEY=your-super-secret-key-here

# 其他配置可以使用默认值
```

**生成安全的SECRET_KEY:**

```bash
openssl rand -hex 32
```

将生成的值粘贴到`.env`文件的`SECRET_KEY`字段。

---

### 步骤 6: 初始化数据库

```bash
python3 init_db.py
```

初始化成功后，会创建默认管理员账户:
- 用户名: `admin`
- 密码: `admin123`

---

### 步骤 7: 启动服务

#### 方式一：使用启动脚本（推荐）

```bash
bash start.sh
```

#### 方式二：手动启动

```bash
# 激活虚拟环境
source venv/bin/activate

# 开发模式（支持热重载）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 配置说明

### 数据库配置

#### SQLite（默认，无需安装）

```env
DATABASE_URL=sqlite:///./crypto_bot.db
```

**优点**: 无需额外安装，配置简单
**适用场景**: 开发测试、个人使用

#### PostgreSQL（生产环境推荐）

```bash
# 1. 安装PostgreSQL
brew install postgresql

# 2. 启动PostgreSQL服务
brew services start postgresql

# 3. 创建数据库
createdb cryptobot
```

修改`.env`配置:

```env
DATABASE_URL=postgresql://username:password@localhost/cryptobot
```

**优点**: 性能更好，支持并发
**适用场景**: 生产环境、多用户

### Redis缓存配置（可选）

```bash
# 1. 安装Redis
brew install redis

# 2. 启动Redis服务
brew services start redis
```

修改`.env`配置:

```env
REDIS_ENABLED=True
REDIS_HOST=localhost
REDIS_PORT=6379
```

**优点**: 提升性能，减轻数据库压力
**适用场景**: 高并发访问、大量数据缓存

### 交易所API配置（实盘交易需要）

如果需要进行实盘交易，需要配置交易所API:

```env
EXCHANGE_ID=binance
API_KEY=your-api-key
API_SECRET=your-api-secret
```

**获取API密钥:**

1. 登录交易所官网
2. 进入API管理页面
3. 创建新的API密钥
4. 设置权限（通常需要现货交易权限）
5. 复制API Key和Secret到配置文件

⚠️ **安全提示**:
- 建议创建只读或有限权限的API密钥
- 不要将API密钥提交到版本控制系统
- 定期更换API密钥

---

## 启动与访问

### 启动服务

```bash
bash start.sh
```

启动成功后会显示:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 访问Web界面

在浏览器中打开:

- **主界面**: http://localhost:8000/static/index.html
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **系统信息**: http://localhost:8000/api/system/info

### 登录系统

默认账户:
- 用户名: `admin`
- 密码: `admin123`

登录后立即修改密码:
1. 进入"系统设置"
2. 点击"修改密码"
3. 输入新密码并确认

---

## 常见问题

### Q1: 安装依赖时出现错误

**问题**: `pip install -r requirements.txt` 失败

**解决方案**:

```bash
# 1. 升级pip
pip install --upgrade pip

# 2. 清理缓存
pip cache purge

# 3. 重新安装
pip install -r requirements.txt --no-cache-dir
```

### Q2: 虚拟环境激活失败

**问题**: `source venv/bin/activate` 提示找不到文件

**解决方案**:

```bash
# 删除旧的虚拟环境
rm -rf venv

# 重新创建
python3 -m venv venv
source venv/bin/activate
```

### Q3: 端口8000被占用

**问题**: 启动时提示端口已被占用

**解决方案**:

**方案一：修改端口**

编辑`.env`文件:

```env
API_PORT=8001
```

**方案二：关闭占用端口的进程**

```bash
# 查找占用8000端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>
```

### Q4: 数据库初始化失败

**问题**: `python3 init_db.py` 执行失败

**解决方案**:

```bash
# 1. 检查.env配置
cat .env

# 2. 删除旧数据库文件（如果有）
rm -f crypto_bot.db

# 3. 重新初始化
python3 init_db.py
```

### Q5: 无法访问Web界面

**问题**: 浏览器打不开 http://localhost:8000

**解决方案**:

1. 检查服务是否启动:

```bash
curl http://localhost:8000/health
```

2. 检查防火墙设置
3. 尝试使用 `127.0.0.1` 代替 `localhost`

### Q6: 交易所连接失败

**问题**: 提示交易所连接错误

**解决方案**:

1. 检查网络连接
2. 验证API密钥是否正确
3. 检查交易所API是否维护
4. 尝试切换到其他交易所

---

## 生产环境建议

### 1. 安全加固

```env
# 1. 修改SECRET_KEY为强随机字符串
SECRET_KEY=$(openssl rand -hex 32)

# 2. 启用HTTPS（需要配置SSL证书）
# 建议使用Nginx反向代理

# 3. 限制CORS
# 修改app/main.py中的CORS配置

# 4. 启用审计日志
AUDIT_LOG_ENABLED=True
```

### 2. 性能优化

```env
# 1. 使用PostgreSQL替代SQLite
DATABASE_URL=postgresql://user:pass@localhost/cryptobot

# 2. 启用Redis缓存
REDIS_ENABLED=True

# 3. 生产模式启动（多进程）
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000

# 4. 禁用热重载
API_RELOAD=False
```

### 3. 监控与日志

```env
# 1. 日志级别
LOG_LEVEL=INFO  # 生产环境建议使用INFO

# 2. 启用性能监控
# 可配置外部监控系统（如Prometheus、Grafana）

# 3. 日志轮转
# 配置日志轮转策略，避免日志文件过大
```

### 4. 备份策略

```bash
# 1. 数据库备份
# 定期备份数据库文件

# 2. 配置备份
# 备份.env文件

# 3. 代码备份
# 使用Git进行版本控制
```

---

## 部署验证清单

部署完成后，请检查以下项目:

- [ ] 服务启动成功，无错误日志
- [ ] 可以访问Web界面
- [ ] 可以使用admin账户登录
- [ ] 可以创建测试机器人
- [ ] 可以启动机器人
- [ ] 可以查看交易记录
- [ ] WebSocket连接正常
- [ ] API文档可访问
- [ ] 健康检查接口正常

---

## 技术支持

如遇到问题，请:

1. 查看本部署指南的"常见问题"部分
2. 检查服务日志输出
3. 查看GitHub Issues: https://github.com/wanian2026/sirenkaifashiyong/issues

---

## 下一步

部署成功后，你可以:

1. 📖 [阅读用户使用手册](README.md)
2. 🎯 [创建第一个交易机器人](#创建交易机器人)
3. 📊 [查看系统功能特性](README.md#功能特性)
4. 🔧 [配置高级功能](#配置说明)

祝你使用愉快！🚀
