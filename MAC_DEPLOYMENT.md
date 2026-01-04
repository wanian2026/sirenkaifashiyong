# Mac 本地部署指南

## 方案一：快速部署（推荐）- 使用 SQLite

### 步骤 1: 进入项目目录
```bash
cd /Users/macbook/Desktop/sirenkaifashiyong
```

### 步骤 2: 运行快速启动脚本
```bash
chmod +x quickstart_sqlite.sh
./quickstart_sqlite.sh
```

这个脚本会自动完成：
- ✅ 检查 Python 环境
- ✅ 创建/激活虚拟环境
- ✅ 安装所有依赖
- ✅ 配置环境变量（使用 SQLite）
- ✅ 创建数据库表
- ✅ 创建日志目录

### 步骤 3: 启动服务
```bash
chmod +x start.sh
./start.sh
```

### 步骤 4: 访问系统
在浏览器中打开：
```
http://localhost:8000/static/ultra_minimal.html
```

### 默认登录账号
- 用户名：`admin`
- 密码：`admin123`

---

## 方案二：完整部署 - 使用 PostgreSQL + Redis

### 步骤 1: 安装 Homebrew（如果未安装）
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 步骤 2: 安装 PostgreSQL
```bash
brew install postgresql@14
brew services start postgresql@14
```

### 步骤 3: 安装 Redis
```bash
brew install redis
brew services start redis
```

### 步骤 4: 运行部署脚本
```bash
chmod +x deploy.sh
./deploy.sh
```

### 步骤 5: 启动服务
```bash
./start.sh
```

### 步骤 6: 访问系统
同方案一，访问：`http://localhost:8000/static/ultra_minimal.html`

---

## 手动部署（如果脚本失败）

### 1. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. 升级 pip
```bash
pip install --upgrade pip
```

### 3. 安装依赖
```bash
pip install -r requirements_mac_compatible.txt
```

### 4. 配置环境变量
```bash
# 创建 .env 文件
cp .env.example .env

# 编辑 .env 文件，设置数据库配置
# SQLite 版本（推荐）:
# DATABASE_URL=sqlite:///./trading.db

# PostgreSQL 版本:
# DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/trading_db
```

### 5. 创建数据库表
```bash
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
```

### 6. 创建日志目录
```bash
mkdir -p logs
```

### 7. 启动服务
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 常见问题解决

### 问题 1: 虚拟环境激活失败
```bash
# 如果提示找不到 venv，重新创建
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### 问题 2: 依赖安装失败
```bash
# 清理缓存后重新安装
pip cache purge
pip install -r requirements_mac_compatible.txt --no-cache-dir
```

### 问题 3: 端口 8000 被占用
```bash
# 修改 .env 文件中的端口
API_PORT=8001

# 或使用其他端口启动
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 问题 4: 数据库连接失败
```bash
# 使用 SQLite（无需安装数据库）
# 编辑 .env 文件：
DATABASE_URL=sqlite:///./trading.db

# 重新创建数据库表
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
```

### 问题 5: 权限错误
```bash
# 给脚本添加执行权限
chmod +x *.sh

# 如果需要管理员权限
sudo ./deploy.sh
```

---

## 验证部署

### 检查服务状态
```bash
# 检查服务是否运行
curl http://localhost:8000/health

# 应该返回: {"status":"healthy"}
```

### 查看日志
```bash
# 实时查看日志
tail -f logs/app.log
```

### 测试数据库连接
```bash
python -c "from app.database import engine; conn = engine.connect(); print('✅ 数据库连接成功'); conn.close()"
```

---

## 停止服务

```bash
./stop.sh
```

或手动停止：
```bash
# 查找进程
ps aux | grep uvicorn

# 停止进程
kill <PID>
```

---

## 更新代码

```bash
# 拉取最新代码
git pull origin main

# 如果有新的依赖
pip install -r requirements_mac_compatible.txt

# 重启服务
./stop.sh
./start.sh
```

---

## 数据备份（SQLite）

```bash
# 备份数据库
cp trading.db trading.db.backup.$(date +%Y%m%d_%H%M%S)

# 恢复数据库
cp trading.db.backup.20250120_120000 trading.db
```

---

## 系统要求

- **Python**: 3.12 或 3.14（推荐 3.14）
- **操作系统**: macOS 11.0+
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 500MB 可用空间

---

## 下一步

部署成功后，你可以：

1. **创建交易策略**
   - 访问策略管理页面
   - 创建新的交易机器人
   - 配置交易参数

2. **连接交易所**
   - 在设置中添加交易所 API
   - 测试连接
   - 开始模拟或真实交易

3. **监控交易**
   - 查看实时交易记录
   - 查看收益统计
   - 查看策略表现

---

## 获取帮助

如果遇到问题：

1. 查看日志文件：`logs/app.log`
2. 检查环境变量：`cat .env`
3. 运行测试脚本：`./test_deployment.sh`
4. 查看故障排查指南：`troubleshoot.sh`

---

## 开发模式

如果需要开发调试：

```bash
# 启用热重载
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启用详细日志
export LOG_LEVEL=DEBUG
./start.sh
```

---

祝部署顺利！🚀
