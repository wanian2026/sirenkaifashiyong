#!/bin/bash

# 加密货币交易系统启动脚本

echo "=========================================="
echo "    加密货币交易系统启动脚本"
echo "=========================================="

# 检查Python版本
echo ""
echo "[1/5] 检查Python版本..."
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3未安装，请先安装Python3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Python版本: $PYTHON_VERSION"

# 检查虚拟环境
echo ""
echo "[2/5] 检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "虚拟环境创建成功"
else
    echo "虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "[3/5] 激活虚拟环境..."
source venv/bin/activate

# 检查依赖
echo ""
echo "[4/5] 检查依赖包..."
pip install -q -r requirements.txt
echo "依赖包安装完成"

# 检查环境配置
echo ""
echo "[5/5] 检查环境配置..."
if [ ! -f ".env" ]; then
    echo "警告: .env文件不存在，正在从.env.example创建..."
    cp .env.example .env
    echo "请编辑.env文件配置必要参数，特别是SECRET_KEY"
    echo ""
    read -p "是否现在编辑.env文件? (y/n): " edit_env
    if [ "$edit_env" = "y" ] || [ "$edit_env" = "Y" ]; then
        nano .env
    fi
fi

# 检查数据库
echo ""
echo "[6/6] 检查数据库..."
if [ ! -f "crypto_bot.db" ]; then
    echo "数据库不存在，正在初始化..."
    python init_db.py
else
    echo "数据库已存在"
fi

# 启动服务
echo ""
echo "=========================================="
echo "启动服务..."
echo "=========================================="
echo ""
echo "服务地址:"
echo "  - Web界面: http://localhost:8000/static/index.html"
echo "  - API文档: http://localhost:8000/docs"
echo ""
echo "默认管理员账户:"
echo "  - 用户名: admin"
echo "  - 密码: admin123"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动FastAPI服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
