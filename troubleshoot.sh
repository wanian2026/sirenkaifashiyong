#!/bin/bash

echo "🔍 诊断安装问题..."

echo "1️⃣ 检查 Python 版本..."
python --version

echo "2️⃣ 检查 pip 版本..."
pip --version

echo "3️⃣ 检查虚拟环境..."
echo "VIRTUAL_ENV: $VIRTUAL_ENV"

echo "4️⃣ 检查系统架构..."
uname -m

echo "5️⃣ 检查 Homebrew 状态..."
if command -v brew &> /dev/null; then
    brew --version
else
    echo "⚠️  Homebrew 未安装"
fi

echo "6️⃣ 检查编译工具..."
if command -v gcc &> /dev/null; then
    gcc --version | head -1
else
    echo "⚠️  gcc 未安装"
fi

echo "7️⃣ 检查已安装的包数量..."
pip list | wc -l

echo "8️⃣ 尝试查找 coincurve 的预编译包..."
pip install --dry-run --ignore-installed coincurve 2>&1 | grep -A5 coincurve

echo "✅ 诊断完成！"
