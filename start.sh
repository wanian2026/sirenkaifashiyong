#!/bin/bash

echo "🚀 启动加密货币交易系统"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 ./deploy.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
echo "🔍 检查依赖..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "❌ 依赖未安装，请先运行 ./deploy.sh"
    exit 1
fi

# 检查数据库
echo "🔍 检查数据库..."
if grep -q "sqlite://" .env 2>/dev/null; then
    echo "✅ 使用 SQLite 数据库"
elif grep -q "postgresql" .env 2>/dev/null; then
    if ! brew services list | grep postgresql | grep -q started 2>/dev/null; then
        echo "⚠️  PostgreSQL 未运行，正在启动..."
        brew services start postgresql@14 2>/dev/null || echo "   注意: 请确保已安装 PostgreSQL"
        sleep 3
    else
        echo "✅ PostgreSQL 正在运行"
    fi
fi

# 检查 Redis（可选）
echo "🔍 检查 Redis..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis 正在运行"
    else
        echo "⚠️  Redis 未运行（可选服务）"
        echo "   如需使用 Redis，请运行: brew services start redis"
    fi
else
    echo "⚠️  Redis 未安装（可选服务）"
    echo "   如需使用 Redis，请运行: brew install redis"
fi

# 创建日志目录
mkdir -p logs

echo "✅ 所有检查通过"
echo ""
echo "================================================"
echo "🚀 启动服务"
echo "================================================"
echo ""

# 启动服务
echo "服务地址:"
echo "  - API 文档: http://localhost:8000/docs"
echo "  - 极简界面: http://localhost:8000/static/ultra_minimal.html"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 使用 reload 模式启动（开发环境）
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
