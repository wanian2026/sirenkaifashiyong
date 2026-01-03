#!/bin/bash

echo "🧪 部署测试脚本"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0

# 测试函数
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo "🔍 测试: $test_name"

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "================================================"
echo "📋 步骤 1: 环境检查"
echo "================================================"
echo ""

run_test "Python 已安装" "command -v python3"
run_test "Pip 已安装" "command -v pip3"
run_test "PostgreSQL 已安装" "command -v psql"
run_test "Redis 已安装" "command -v redis-cli"
run_test "虚拟环境存在" "[ -d venv ]"

echo ""

echo "================================================"
echo "📋 步骤 2: 服务状态检查"
echo "================================================"
echo ""

run_test "PostgreSQL 服务运行中" "brew services list | grep postgresql | grep -q started"
run_test "Redis 服务运行中" "redis-cli ping"

echo ""

echo "================================================"
echo "📋 步骤 3: 数据库检查"
echo "================================================"
echo ""

run_test "数据库 trading_db 存在" "psql -lqt | cut -d \| -f 1 | grep -qw trading_db"

echo ""

echo "================================================"
echo "📋 步骤 4: Python 依赖检查"
echo "================================================"
echo ""

if [ -d "venv" ]; then
    source venv/bin/activate

    run_test "FastAPI 已安装" "python -c 'import fastapi'"
    run_test "SQLAlchemy 已安装" "python -c 'import sqlalchemy'"
    run_test "Pydantic 已安装" "python -c 'import pydantic'"
    run_test "ccxt 已安装" "python -c 'import ccxt'"
    run_test "pandas 已安装" "python -c 'import pandas'"
    run_test "CodeAStrategy 可导入" "python -c 'from app.code_a_strategy import CodeAStrategy'"
else
    echo -e "${RED}❌ 虚拟环境不存在${NC}"
    ((TESTS_FAILED++))
fi

echo ""

echo "================================================"
echo "📋 步骤 5: 配置文件检查"
echo "================================================"
echo ""

run_test ".env 文件存在" "[ -f .env ]"
run_test "requirements.txt 存在" "[ -f requirements.txt ]"
run_test "main.py 存在" "[ -f app/main.py ]"
run_test "database.py 存在" "[ -f app/database.py ]"
run_test "models.py 存在" "[ -f app/models.py ]"

echo ""

echo "================================================"
echo "📋 步骤 6: 数据库表检查"
echo "================================================"
echo ""

if [ -f "app/models.py" ] && [ -d "venv" ]; then
    source venv/bin/activate > /dev/null 2>&1
    run_test "数据库表已创建" "python -c 'from app.database import engine; from app.models import Base; Base.metadata.reflect(bind=engine)'"
fi

echo ""

echo "================================================"
echo "📋 步骤 7: 默认用户检查"
echo "================================================"
echo ""

if [ -f "app/models.py" ] && [ -d "venv" ]; then
    source venv/bin/activate > /dev/null 2>&1
    USER_EXISTS=$(python -c "
from app.database import SessionLocal
from app.models import User
db = SessionLocal()
try:
    user = db.query(User).filter(User.username == 'admin').first()
    print(1 if user else 0)
finally:
    db.close()
" 2>/dev/null)

    if [ "$USER_EXISTS" = "1" ]; then
        echo -e "${GREEN}✅ 默认用户 admin 存在${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ 默认用户 admin 不存在${NC}"
        ((TESTS_FAILED++))
    fi
fi

echo ""

echo "================================================"
echo "📋 步骤 8: API 端点检查（服务需先启动）"
echo "================================================"
echo ""

run_test "API 健康检查" "curl -s http://localhost:8000/api/v1/health > /dev/null"
run_test "API 文档可访问" "curl -s http://localhost:8000/docs > /dev/null"

echo ""

echo "================================================"
echo "📊 测试结果"
echo "================================================"
echo ""
echo -e "${GREEN}✅ 通过: $TESTS_PASSED${NC}"
echo -e "${RED}❌ 失败: $TESTS_FAILED${NC}"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$(python -c "print(f'{(100 * $TESTS_PASSED / $TOTAL_TESTS):.1f}')" 2>/dev/null || echo "N/A")
echo "成功率: $SUCCESS_RATE%"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！部署成功！${NC}"
    echo ""
    echo "下一步:"
    echo "  1. 启动服务: ./start.sh"
    echo "  2. 访问界面: http://localhost:8000/static/ultra_minimal.html"
    echo "  3. 登录账号: admin / admin123"
    exit 0
else
    echo -e "${YELLOW}⚠️  有 $TESTS_FAILED 个测试失败${NC}"
    echo ""
    echo "建议:"
    echo "  1. 重新运行部署: ./deploy.sh"
    echo "  2. 检查错误日志: logs/app.log"
    echo "  3. 查看 PostgreSQL: psql -d trading_db"
    exit 1
fi
