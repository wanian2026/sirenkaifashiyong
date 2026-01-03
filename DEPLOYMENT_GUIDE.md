# 完整部署指南

## 📋 目录

1. [系统要求](#系统要求)
2. [一键部署](#一键部署推荐)
3. [手动部署](#手动部署)
4. [启动服务](#启动服务)
5. [测试部署](#测试部署)
6. [常见问题](#常见问题)
7. [生产环境部署](#生产环境部署)

---

## 系统要求

### 硬件要求
- **CPU**: 至少 2 核
- **内存**: 至少 4GB RAM（推荐 8GB）
- **磁盘**: 至少 10GB 可用空间

### 软件要求
- **操作系统**: macOS 12+ / Linux (Ubuntu 20.04+)
- **Python**: 3.12+ (推荐 3.14)
- **PostgreSQL**: 14+
- **Redis**: 6+
- **Homebrew**: (macOS)

### 网络要求
- 互联网连接（用于安装依赖和访问交易所 API）
- 防火墙开放端口 8000（或自定义端口）

---

## 一键部署（推荐）

### 步骤 1: 克隆项目

```bash
# 克隆仓库
git clone https://github.com/wanian2026/sirenkaifashiyong.git
cd sirenkaifashiyong
```

### 步骤 2: 运行部署脚本

```bash
# 给脚本添加执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

### 步骤 3: 启动服务

```bash
# 给启动脚本添加执行权限
chmod +x start.sh

# 启动服务
./start.sh
```

### 步骤 4: 访问界面

- **API 文档**: http://localhost:8000/docs
- **极简界面**: http://localhost:8000/static/ultra_minimal.html
- **默认账号**: admin / admin123

---

## 手动部署

### 步骤 1: 安装系统依赖

#### macOS

```bash
# 安装 Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 PostgreSQL
brew install postgresql@14
brew services start postgresql@14

# 安装 Redis
brew install redis
brew services start redis
```

#### Linux (Ubuntu)

```bash
# 更新包列表
sudo apt update

# 安装 PostgreSQL
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# 安装 Redis
sudo apt install redis-server
sudo systemctl start redis
```

### 步骤 2: 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 步骤 3: 安装 Python 依赖

```bash
# 如果遇到 coincurve 问题，使用修复版本
pip install -r requirements_no_coincurve.txt --no-cache-dir

# 或尝试使用更新版本
pip install coincurve --upgrade --no-cache-dir
pip install -r requirements.txt --no-cache-dir
```

### 步骤 4: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env
```

#### .env 文件内容

```env
# 数据库配置
DATABASE_URL=postgresql://postgres@localhost:5432/trading_db

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 交易所配置（可选）
BINANCE_API_KEY=
BINANCE_API_SECRET=
OKX_API_KEY=
OKX_API_SECRET=

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 步骤 5: 创建数据库

#### macOS

```bash
# 创建数据库
createdb trading_db

# 验证数据库
psql -d trading_db -c "SELECT version();"
```

#### Linux

```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 在 PostgreSQL 命令行中
CREATE DATABASE trading_db;
\q
```

### 步骤 6: 初始化数据库表

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 创建数据库表
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
```

### 步骤 7: 创建默认用户

```bash
# 创建管理员用户
python -c "
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

db = SessionLocal()
try:
    admin_user = User(
        username='admin',
        email='admin@example.com',
        hashed_password=get_password_hash('admin123'),
        is_active=True,
        is_superuser=True
    )
    db.add(admin_user)
    db.commit()
    print('Admin 用户创建成功')
except Exception as e:
    print(f'创建用户失败: {e}')
finally:
    db.close()
"
```

### 步骤 8: 创建日志目录

```bash
mkdir -p logs
```

---

## 启动服务

### 开发模式（推荐用于测试）

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务（自动重载）
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产模式

```bash
# 使用多个工作进程
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 或使用 systemd/launchd（见生产环境部署）
```

### 使用启动脚本

```bash
# 给脚本添加执行权限
chmod +x start.sh stop.sh

# 启动服务
./start.sh

# 停止服务
./stop.sh
```

---

## 测试部署

### 自动测试

```bash
# 运行测试脚本
chmod +x test_deployment.sh
./test_deployment.sh
```

测试内容：
- ✅ 环境检查
- ✅ 服务状态检查
- ✅ 数据库检查
- ✅ Python 依赖检查
- ✅ 配置文件检查
- ✅ 数据库表检查
- ✅ 默认用户检查
- ✅ API 端点检查

### 手动测试

#### 1. 测试 API 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

预期输出：
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

#### 2. 测试用户登录

```bash
# 登录获取 Token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

#### 3. 测试策略 API

```bash
# 获取策略类型
TOKEN="your_access_token"
curl http://localhost:8000/api/v1/strategies/types \
  -H "Authorization: Bearer $TOKEN"
```

#### 4. 测试数据库连接

```bash
# 连接数据库
psql -d trading_db

# 查看表
\dt

# 查看用户
SELECT * FROM users;

# 退出
\q
```

#### 5. 测试 Redis 连接

```bash
# 测试连接
redis-cli ping

# 应该返回: PONG

# 查看键
redis-cli KEYS "*"
```

---

## 常见问题

### Q1: PostgreSQL 连接失败

**问题**: `could not connect to server: Connection refused`

**解决方案**:

```bash
# 检查 PostgreSQL 服务状态
brew services list | grep postgresql

# 启动服务
brew services start postgresql@14

# 检查端口占用
lsof -i :5432

# 查看日志
tail -f /opt/homebrew/var/log/postgresql@14.log
```

### Q2: Redis 连接失败

**问题**: `Error connecting to Redis`

**解决方案**:

```bash
# 检查 Redis 服务状态
brew services list | grep redis

# 启动服务
brew services start redis

# 测试连接
redis-cli ping

# 查看日志
tail -f /opt/homebrew/var/log/redis.log
```

### Q3: 端口已被占用

**问题**: `Address already in use: 8000`

**解决方案**:

```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或更换端口
python -m uvicorn app.main:app --port 8001
```

### Q4: 数据库表不存在

**问题**: `relation "users" does not exist`

**解决方案**:

```bash
# 重新创建表
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"

# 或删除数据库重新创建
dropdb trading_db
createdb trading_db
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
```

### Q5: 虚拟环境激活失败

**问题**: `venv/bin/activate: No such file or directory`

**解决方案**:

```bash
# 重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Q6: 依赖安装失败

**问题**: `coincurve` 安装错误

**解决方案**:

```bash
# 清理缓存
pip cache purge

# 使用修复版本
pip install -r requirements_no_coincurve.txt

# 或先安装 coincurve
pip install coincurve --upgrade
pip install -r requirements.txt
```

### Q7: 权限错误

**问题**: `Permission denied`

**解决方案**:

```bash
# 给脚本添加执行权限
chmod +x deploy.sh start.sh stop.sh test_deployment.sh

# 或使用 sudo（不推荐）
sudo ./deploy.sh
```

---

## 生产环境部署

### 使用 Gunicorn + Uvicorn

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

### 使用 Systemd (Linux)

创建 `/etc/systemd/system/trading-bot.service`:

```ini
[Unit]
Description=Trading Bot API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=your_user
WorkingDirectory=/path/to/sirenkaifashiyong
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start trading-bot

# 查看状态
sudo systemctl status trading-bot

# 开机自启
sudo systemctl enable trading-bot
```

### 使用 Nginx 反向代理

创建 `/etc/nginx/sites-available/trading-bot`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/sirenkaifashiyong/static/;
    }
}
```

启用配置：

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/trading-bot /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 使用 Docker (可选)

创建 `Dockerfile`:

```dockerfile
FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：

```bash
# 构建镜像
docker build -t trading-bot .

# 运行容器
docker run -d \
  --name trading-bot \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/trading_db \
  -e REDIS_URL=redis://redis:6379/0 \
  trading-bot
```

### SSL/TLS 配置 (Let's Encrypt)

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 安全建议

1. **修改默认密码**
   ```python
   # 修改 admin 密码
   from app.database import SessionLocal
   from app.models import User
   from app.auth import get_password_hash

   db = SessionLocal()
   user = db.query(User).filter(User.username == 'admin').first()
   user.hashed_password = get_password_hash('new_strong_password')
   db.commit()
   ```

2. **配置防火墙**
   ```bash
   # 只允许特定 IP 访问
   sudo ufw allow from your_ip to any port 8000
   ```

3. **使用环境变量**
   ```bash
   # 不要在代码中硬编码敏感信息
   # 使用 .env 文件或环境变量
   ```

4. **定期更新依赖**
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

5. **备份数据库**
   ```bash
   # 定期备份
   pg_dump trading_db > backup_$(date +%Y%m%d).sql
   ```

---

## 监控和日志

### 查看日志

```bash
# 应用日志
tail -f logs/app.log

# 访问日志
tail -f logs/access.log

# 错误日志
tail -f logs/error.log

# PostgreSQL 日志
tail -f /opt/homebrew/var/log/postgresql@14.log

# Redis 日志
tail -f /opt/homebrew/var/log/redis.log
```

### 性能监控

```bash
# 查看系统资源
htop

# 查看 Python 进程
ps aux | grep python

# 查看数据库连接
psql -d trading_db -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## 更新和维护

### 更新代码

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
./stop.sh
./start.sh
```

### 数据库迁移

```bash
# 使用 Alembic（如果配置了）
alembic upgrade head

# 或手动执行 SQL
psql -d trading_db < migrations/migration.sql
```

---

## 支持和帮助

- **文档**: 查看项目 README.md
- **日志**: logs/app.log
- **GitHub Issues**: https://github.com/wanian2026/sirenkaifashiyong/issues

---

## 快速命令参考

```bash
# 部署
./deploy.sh

# 启动
./start.sh

# 停止
./stop.sh

# 测试
./test_deployment.sh

# 查看日志
tail -f logs/app.log

# 数据库
psql -d trading_db

# Redis
redis-cli
```

---

**祝部署顺利！** 🚀
