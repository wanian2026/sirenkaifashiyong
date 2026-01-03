#!/bin/bash

echo "🔧 修复 coincurve 兼容性问题..."

# 停止当前安装
echo "⚠️  如果之前的安装卡住了，请按 Ctrl+C 停止，然后运行此脚本"

# 方案 1：先安装编译依赖（可能需要）
echo "📦 安装编译依赖..."
if command -v brew &> /dev/null; then
    brew install libtool automake autoconf pkg-config
else
    echo "⚠️  Homebrew 未安装，跳过编译依赖安装"
fi

# 清理之前的缓存
echo "🧹 清理 pip 缓存..."
pip cache purge

# 方案 2：尝试安装更新的 coincurve
echo "🔄 尝试安装更新的 coincurve..."
pip install --no-cache-dir coincurve --upgrade

# 如果上面成功，继续安装其他依赖
if [ $? -eq 0 ]; then
    echo "✅ coincurve 安装成功，继续安装其他依赖..."
    pip install -r requirements.txt --no-cache-dir
else
    echo "⚠️  coincurve 安装失败，尝试使用修复的 requirements.txt..."
    pip install -r requirements_fixed.txt --no-cache-dir
fi

echo "✅ 完成！"
