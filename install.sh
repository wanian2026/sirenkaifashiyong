#!/bin/bash

# 加密货币交易系统 - Mac本地部署脚本
# 使用方法: bash install.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  加密货币交易系统 - Mac本地部署"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 检查系统环境
echo -e "${YELLOW}[1/7] 检查系统环境...${NC}"

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3，请先安装Python 3.8+${NC}"
    echo "推荐使用 Homebrew 安装: brew install python"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Python版本: $PYTHON_VERSION${NC}"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}错误: 未找到pip3${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pip3已安装${NC}"

echo ""

# 2. 创建虚拟环境
echo -e "${YELLOW}[2/7] 创建Python虚拟环境...${NC}"

if [ -d "venv" ]; then
    echo -e "${YELLOW}虚拟环境已存在，跳过创建${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
fi

# 激活虚拟环境
source venv/bin/activate
echo -e "${GREEN}✓ 虚拟环境已激活${NC}"

echo ""

# 3. 升级pip和安装基础工具
echo -e "${YELLOW}[3/7] 升级pip和安装基础工具...${NC}"

pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✓ pip已升级${NC}"

echo ""

# 4. 安装项目依赖
echo -e "${YELLOW}[4/7] 安装项目依赖包...${NC}"

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ 依赖包安装完成${NC}"
else
    echo -e "${RED}错误: 未找到requirements.txt文件${NC}"
    exit 1
fi

echo ""

# 5. 配置环境变量
echo -e "${YELLOW}[5/7] 配置环境变量...${NC}"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ 已创建.env配置文件${NC}"
    else
        # 创建默认.env文件
        cat > .env << 'EOF'
# 数据库配置
DATABASE_URL=sqlite:///./crypto_bot.db

# JWT密钥 (生产环境请修改为随机字符串!)
SECRET_KEY=dev-secret-key-change-in-production-$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API服务配置
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# 交易所配置 (可选)
EXCHANGE_ID=binance
API_KEY=
API_SECRET=

# 网格策略默认参数
GRID_LEVELS=10
GRID_SPACING=0.02
INVESTMENT_AMOUNT=1000

# 日志配置
LOG_LEVEL=INFO

# Redis配置 (可选，用于缓存)
REDIS_ENABLED=False
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 安全配置
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
AUDIT_LOG_ENABLED=True
AUDIT_LOG_RETENTION_DAYS=90
SENSITIVE_OPERATIONS_VERIFY=True
MAX_LOGIN_ATTEMPTS=5
LOGIN_LOCKOUT_DURATION=1800

# 邮箱配置 (可选)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_USE_TLS=True

# 前端URL
FRONTEND_URL=http://localhost:3000
EOF
        echo -e "${GREEN}✓ 已创建.env配置文件${NC}"
    fi
    
    echo -e "${YELLOW}重要提示: 请根据需要修改.env文件中的配置${NC}"
else
    echo -e "${YELLOW}.env文件已存在，跳过创建${NC}"
fi

echo ""

# 6. 初始化数据库
echo -e "${YELLOW}[6/7] 初始化数据库...${NC}"

if [ -f "init_db.py" ]; then
    python3 init_db.py
    echo -e "${GREEN}✓ 数据库初始化完成${NC}"
else
    echo -e "${YELLOW}警告: 未找到init_db.py，请手动初始化数据库${NC}"
fi

echo ""

# 7. 创建启动脚本
echo -e "${YELLOW}[7/7] 创建启动脚本...${NC}"

if [ ! -f "start.sh" ]; then
    cat > start.sh << 'EOF'
#!/bin/bash

# 激活虚拟环境
source venv/bin/activate

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EOF
    chmod +x start.sh
    echo -e "${GREEN}✓ 启动脚本创建成功${NC}"
else
    echo -e "${YELLOW}启动脚本已存在，跳过创建${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  部署完成！${NC}"
echo "=========================================="
echo ""
echo "接下来请执行以下步骤:"
echo ""
echo -e "${YELLOW}1. 激活虚拟环境:${NC}"
echo "   source venv/bin/activate"
echo ""
echo -e "${YELLOW}2. (可选) 修改配置文件:${NC}"
echo "   nano .env"
echo ""
echo -e "${YELLOW}3. 启动服务:${NC}"
echo "   bash start.sh"
echo ""
echo -e "${YELLOW}4. 访问Web界面:${NC}"
echo "   http://localhost:8000/static/index.html"
echo ""
echo -e "${YELLOW}5. 默认登录账户:${NC}"
echo "   用户名: admin"
echo "   密码: admin123"
echo ""
echo -e "${RED}⚠️  安全提示: 登录后请立即修改默认密码！${NC}"
echo ""
echo "=========================================="
