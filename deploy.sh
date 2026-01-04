#!/bin/bash

echo "🚀 加密货币交易系统 - 一键部署脚本"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查函数
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 未安装${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $1 已安装${NC}"
        return 0
    fi
}

# 步骤 1: 环境检查
echo "================================================"
echo "📋 步骤 1: 环境检查"
echo "================================================"
echo ""

echo "检查必需的软件..."
check_command python3 || exit 1
check_command pip3 || exit 1
check_command brew || {
    echo -e "${YELLOW}⚠️  Homebrew 未安装，请先安装 Homebrew${NC}"
    exit 1
}
echo ""

# 步骤 2: 检查虚拟环境
echo "================================================"
echo "📋 步骤 2: 检查虚拟环境"
echo "================================================"
echo ""

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  虚拟环境不存在，正在创建...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}✅ 虚拟环境已创建${NC}"
else
    echo -e "${GREEN}✅ 虚拟环境已存在${NC}"
    source venv/bin/activate
fi

echo "当前 Python: $(python --version)"
echo "当前 Pip: $(pip --version)"
echo ""

# 步骤 3: 安装依赖
echo "================================================"
echo "📋 步骤 3: 安装 Python 依赖"
echo "================================================"
echo ""

echo -e "${YELLOW}⏳ 正在安装依赖...${NC}"
if [ -f "requirements_mac_compatible.txt" ]; then
    pip install -r requirements_mac_compatible.txt --no-cache-dir
elif [ -f "requirements_no_coincurve.txt" ]; then
    pip install -r requirements_no_coincurve.txt --no-cache-dir
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --no-cache-dir
else
    echo -e "${RED}❌ 找不到 requirements.txt${NC}"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 依赖安装成功${NC}"
else
    echo -e "${RED}❌ 依赖安装失败${NC}"
    exit 1
fi
echo ""

# 步骤 4: 安装 PostgreSQL
echo "================================================"
echo "📋 步骤 4: 检查 PostgreSQL"
echo "================================================"
echo ""

if check_command psql; then
    echo -e "${GREEN}✅ PostgreSQL 已安装${NC}"
else
    echo -e "${YELLOW}⚠️  正在安装 PostgreSQL...${NC}"
    brew install postgresql@14
    brew services start postgresql@14
    sleep 3
    echo -e "${GREEN}✅ PostgreSQL 安装完成${NC}"
fi

# 检查 PostgreSQL 服务状态
if brew services list | grep postgresql | grep -q started; then
    echo -e "${GREEN}✅ PostgreSQL 服务已启动${NC}"
else
    echo -e "${YELLOW}⏳ 正在启动 PostgreSQL 服务...${NC}"
    brew services start postgresql@14
    sleep 3
fi
echo ""

# 步骤 5: 安装 Redis
echo "================================================"
echo "📋 步骤 5: 检查 Redis"
echo "================================================"
echo ""

if check_command redis-cli; then
    echo -e "${GREEN}✅ Redis 已安装${NC}"
else
    echo -e "${YELLOW}⚠️  正在安装 Redis...${NC}"
    brew install redis
    brew services start redis
    sleep 3
    echo -e "${GREEN}✅ Redis 安装完成${NC}"
fi

# 检查 Redis 服务状态
if brew services list | grep redis | grep -q started; then
    echo -e "${GREEN}✅ Redis 服务已启动${NC}"
else
    echo -e "${YELLOW}⏳ 正在启动 Redis 服务...${NC}"
    brew services start redis
    sleep 3
fi

# 测试 Redis 连接
if redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ Redis 连接正常${NC}"
else
    echo -e "${RED}❌ Redis 连接失败${NC}"
    exit 1
fi
echo ""

# 步骤 6: 配置环境变量
echo "================================================"
echo "📋 步骤 6: 配置环境变量"
echo "================================================"
echo ""

if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    cat > .env << EOF
# 数据库配置（使用 psycopg3 驱动）
DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/trading_db

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
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
EOF
    echo -e "${GREEN}✅ .env 文件已创建${NC}"
else
    echo -e "${GREEN}✅ .env 文件已存在${NC}"
fi
echo ""

# 步骤 7: 创建数据库
echo "================================================"
echo "📋 步骤 7: 创建数据库"
echo "================================================"
echo ""

# 检查数据库是否存在
if psql -lqt | cut -d \| -f 1 | grep -qw trading_db; then
    echo -e "${GREEN}✅ 数据库 trading_db 已存在${NC}"
else
    echo "创建数据库 trading_db..."
    createdb trading_db
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 数据库创建成功${NC}"
    else
        echo -e "${RED}❌ 数据库创建失败${NC}"
        exit 1
    fi
fi
echo ""

# 步骤 8: 初始化数据库
echo "================================================"
echo "📋 步骤 8: 初始化数据库表"
echo "================================================"
echo ""

echo "创建数据库表..."
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 数据库表创建成功${NC}"
else
    echo -e "${RED}❌ 数据库表创建失败${NC}"
    exit 1
fi
echo ""

# 步骤 9: 创建默认用户
echo "================================================"
echo "📋 步骤 9: 创建默认用户"
echo "================================================"
echo ""

echo "创建默认用户 (admin / admin123)..."
python -c "
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

db = SessionLocal()
try:
    # 检查是否已存在 admin 用户
    existing_user = db.query(User).filter(User.username == 'admin').first()
    if existing_user:
        print('Admin 用户已存在，跳过创建')
    else:
        # 创建 admin 用户
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
echo ""

# 步骤 10: 创建日志目录
echo "================================================"
echo "📋 步骤 10: 创建日志目录"
echo "================================================"
echo ""

mkdir -p logs
echo -e "${GREEN}✅ 日志目录已创建${NC}"
echo ""

# 步骤 11: 启动服务
echo "================================================"
echo "📋 步骤 11: 启动服务"
echo "================================================"
echo ""

echo -e "${GREEN}🎉 部署准备完成！${NC}"
echo ""
echo "================================================"
echo "📝 部署完成信息"
echo "================================================"
echo ""
echo -e "${GREEN}✅ 虚拟环境${NC}: venv/"
echo -e "${GREEN}✅ Python 版本${NC}: $(python --version)"
echo -e "${GREEN}✅ PostgreSQL${NC}: 已安装并启动 (数据库: trading_db)"
echo -e "${GREEN}✅ Redis${NC}: 已安装并启动"
echo -e "${GREEN}✅ 数据库表${NC}: 已初始化"
echo -e "${GREEN}✅ 默认用户${NC}: admin / admin123"
echo ""
echo "================================================"
echo "🚀 启动服务"
echo "================================================"
echo ""
echo "运行以下命令启动服务："
echo ""
echo -e "${YELLOW}source venv/bin/activate${NC}"
echo -e "${YELLOW}python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000${NC}"
echo ""
echo "或使用生产模式："
echo ""
echo -e "${YELLOW}python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4${NC}"
echo ""
echo "================================================"
echo "📱 访问地址"
echo "================================================"
echo ""
echo -e "${GREEN}✅ API 文档 (Swagger)${NC}: http://localhost:8000/docs"
echo -e "${GREEN}✅ API 文档 (ReDoc)${NC}: http://localhost:8000/redoc"
echo -e "${GREEN}✅ 极简界面${NC}: http://localhost:8000/static/ultra_minimal.html"
echo -e "${GREEN}✅ 默认账号${NC}: admin / admin123"
echo ""
echo "================================================"
echo "🛑 停止服务"
echo "================================================"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""
