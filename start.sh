#!/bin/bash

# 加密货币交易系统 - 启动脚本

echo "=========================================="
echo "  加密货币交易系统 - 启动中..."
echo "=========================================="
echo ""

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "错误: 虚拟环境不存在"
    echo "请先运行: bash install.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "警告: .env文件不存在"
    echo "将使用默认配置启动"
fi

# 检查数据库是否存在
if [ ! -f "crypto_bot.db" ]; then
    echo "数据库文件不存在，正在初始化..."
    python3 init_db.py
    if [ $? -ne 0 ]; then
        echo "错误: 数据库初始化失败"
        exit 1
    fi
fi

# 启动服务
echo "正在启动服务..."
echo "=========================================="
echo ""

# 读取配置
API_HOST=$(grep API_HOST .env | cut -d '=' -f2)
API_PORT=$(grep API_PORT .env | cut -d '=' -f2)
API_RELOAD=$(grep API_RELOAD .env | cut -d '=' -f2)

# 设置默认值
API_HOST=${API_HOST:-0.0.0.0}
API_PORT=${API_PORT:-8000}
API_RELOAD=${API_RELOAD:-true}

# 启动uvicorn
if [ "$API_RELOAD" = "True" ] || [ "$API_RELOAD" = "true" ]; then
    uvicorn app.main:app --host $API_HOST --port $API_PORT --reload
else
    uvicorn app.main:app --host $API_HOST --port $API_PORT
fi
