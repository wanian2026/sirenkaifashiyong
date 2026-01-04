#!/bin/bash

echo "🚀 加密货币交易系统 - 快速启动（SQLite 版本）"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 步骤 1: 检查 Python
echo "================================================"
echo "📋 步骤 1: 检查 Python 环境"
echo "================================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ python3 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 版本: $(python3 --version)${NC}"
echo ""

# 步骤 2: 创建虚拟环境（如果不存在）
echo "================================================"
echo "📋 步骤 2: 检查虚拟环境"
echo "================================================"
echo ""

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  虚拟环境不存在，正在创建...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ 虚拟环境已创建${NC}"
fi

source venv/bin/activate
echo -e "${GREEN}✅ 虚拟环境已激活${NC}"
echo ""

# 步骤 3: 升级 pip
echo "================================================"
echo "📋 步骤 3: 升级 pip"
echo "================================================"
echo ""

pip install --upgrade pip
echo -e "${GREEN}✅ pip 已升级${NC}"
echo ""

# 步骤 4: 安装依赖
echo "================================================"
echo "📋 步骤 4: 安装依赖"
echo "================================================"
echo ""

echo -e "${YELLOW}⏳ 正在安装依赖...${NC}"
if [ -f "requirements_mac_compatible.txt" ]; then
    pip install -r requirements_mac_compatible.txt --no-cache-dir
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

# 步骤 5: 配置环境变量
echo "================================================"
echo "📋 步骤 5: 配置环境变量"
echo "================================================"
echo ""

if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    cat > .env << EOF
# 数据库配置（使用 SQLite）
DATABASE_URL=sqlite:///./trading.db

# Redis 配置（可选，如果未安装 Redis，可以禁用）
REDIS_ENABLED=false

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

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

# 步骤 6: 创建数据库表
echo "================================================"
echo "📋 步骤 6: 创建数据库表"
echo "================================================"
echo ""

python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 数据库表创建成功${NC}"
else
    echo -e "${RED}❌ 数据库表创建失败${NC}"
    exit 1
fi
echo ""

# 步骤 7: 创建日志目录
echo "================================================"
echo "📋 步骤 7: 创建日志目录"
echo "================================================"
echo ""

mkdir -p logs
echo -e "${GREEN}✅ 日志目录已创建${NC}"
echo ""

# 完成
echo "================================================"
echo "✅ 部署完成！"
echo "================================================"
echo ""
echo -e "${GREEN}🎉 加密货币交易系统已成功部署！${NC}"
echo ""
echo "📝 下一步："
echo "   1. 启动服务："
echo "      ${YELLOW}./start.sh${NC}"
echo ""
echo "   2. 访问界面："
echo "      ${YELLOW}http://localhost:8000/static/ultra_minimal.html${NC}"
echo ""
echo "   3. 默认登录账号："
echo "      用户名：${YELLOW}admin${NC}"
echo "      密码：${YELLOW}admin123${NC}"
echo ""
echo "💡 提示："
echo "   - 使用 SQLite 数据库（文件位于项目根目录）"
echo "   - 如需使用 PostgreSQL，请修改 .env 中的 DATABASE_URL"
echo "   - 如需使用 Redis，请先安装 Redis 并修改 .env 中的配置"
echo ""
