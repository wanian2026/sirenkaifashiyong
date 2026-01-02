#!/bin/bash
# 使用 Conda 安装依赖的快速脚本

set -e  # 遇到错误立即退出

echo "====================================="
echo "加密货币交易系统 - Conda 安装脚本"
echo "====================================="
echo ""

# 检查是否安装了 conda
if ! command -v conda &> /dev/null; then
    echo "❌ 未检测到 conda"
    echo ""
    echo "请先安装 Miniforge："
    echo ""
    echo "Apple Silicon (M1/M2/M3):"
    echo "  curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh"
    echo "  bash Miniforge3-MacOSX-arm64.sh"
    echo ""
    echo "Intel Mac:"
    echo "  curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh"
    echo "  bash Miniforge3-MacOSX-x86_64.sh"
    echo ""
    echo "安装完成后重启终端，然后重新运行此脚本"
    exit 1
fi

echo "✅ 检测到 conda: $(conda --version)"
echo ""

# 检查 Python 版本
echo "📋 当前 Python 版本:"
python --version
echo ""

# 步骤1: 使用 conda 安装 pandas 和 numpy
echo "====================================="
echo "步骤 1/5: 使用 Conda 安装 pandas 和 numpy"
echo "====================================="
conda install pandas numpy -y

# 步骤2: 升级 pip
echo ""
echo "====================================="
echo "步骤 2/5: 升级 pip"
echo "====================================="
pip install --upgrade pip

# 步骤3: 安装核心依赖
echo ""
echo "====================================="
echo "步骤 3/5: 安装核心依赖"
echo "====================================="
pip install fastapi uvicorn langgraph langchain ccxt

# 步骤4: 安装数据库和认证依赖
echo ""
echo "====================================="
echo "步骤 4/5: 安装数据库和认证依赖"
echo "====================================="
pip install sqlalchemy alembic python-jose passlib bcrypt

# 步骤5: 安装其他依赖
echo ""
echo "====================================="
echo "步骤 5/5: 安装其他依赖"
echo "====================================="
pip install python-multipart websockets pydantic pydantic-settings python-dotenv aiohttp jinja2

# 验证安装
echo ""
echo "====================================="
echo "验证安装"
echo "====================================="
echo ""

echo "✅ pandas 版本:"
python -c "import pandas; print(pandas.__version__)"

echo ""
echo "✅ numpy 版本:"
python -c "import numpy; print(numpy.__version__)"

echo ""
echo "✅ fastapi 版本:"
python -c "import fastapi; print(fastapi.__version__)"

echo ""
echo "====================================="
echo "🎉 依赖安装完成！"
echo "====================================="
echo ""
echo "下一步："
echo "1. 配置环境变量: cp .env.example .env && nano .env"
echo "2. 初始化数据库: python init_db.py"
echo "3. 启动服务: ./start.sh"
echo ""
echo "详细说明请查看: FIX_PANDAS_INSTALL.md"
