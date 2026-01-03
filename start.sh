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

# 检查 PostgreSQL
echo "🔍 检查 PostgreSQL..."
if ! brew services list | grep postgresql | grep -q started; then
    echo "⚠️  PostgreSQL 未运行，正在启动..."
    brew services start postgresql@14
    sleep 3
fi

# 检查 Redis
echo "🔍 检查 Redis..."
if ! redis-cli ping &> /dev/null; then
    echo "⚠️  Redis 未运行，正在启动..."
    brew services start redis
    sleep 3
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
