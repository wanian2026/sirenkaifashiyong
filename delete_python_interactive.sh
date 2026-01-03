#!/bin/bash

echo "🐍 Python 版本删除工具（交互式）"
echo "⚠️  警告：此操作不可逆，请谨慎操作！"
echo ""

# 获取所有 Homebrew 安装的 Python 版本
echo "================================================"
echo "📋 已安装的 Python 版本（Homebrew）"
echo "================================================"
echo ""

PYTHONS=()
INDEX=1

# 检查各种 Python 版本
for version in 3.14 3.13 3.12 3.11 3.10 3.9 3.8; do
    if brew list python@$version &>/dev/null; then
        PY_VERSION=$(python$version --version 2>/dev/null | head -1)
        PY_PATH=$(which python$version 2>/dev/null)
        echo "$INDEX) Python $version"
        echo "   版本: $PY_VERSION"
        echo "   路径: $PY_PATH"
        echo ""

        PYTHONS+=("python@$version")
        INDEX=$((INDEX + 1))
    fi
done

if [ ${#PYTHONS[@]} -eq 0 ]; then
    echo "未找到通过 Homebrew 安装的 Python 版本"
    exit 0
fi

echo "0) 取消操作"
echo ""

# 让用户选择
read -p "请选择要删除的 Python 版本编号 (0-${#PYTHONS[@]}): " choice

if [ "$choice" -eq 0 ] 2>/dev/null; then
    echo "❌ 操作已取消"
    exit 0
fi

# 验证输入
if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#PYTHONS[@]} ]; then
    echo "❌ 无效的选择"
    exit 1
fi

# 获取选中的 Python
SELECTED_PYTHON="${PYTHONS[$((choice-1))]}"

echo ""
echo "================================================"
echo "⚠️  确认删除"
echo "================================================"
echo ""
echo "你即将删除: $SELECTED_PYTHON"
echo ""
read -p "确认删除？请输入 'yes' 继续: " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ 操作已取消"
    exit 0
fi

echo ""
echo "================================================"
echo "🗑️  开始删除"
echo "================================================"
echo ""

# 检查是否有包依赖这个 Python 版本
echo "🔍 检查依赖关系..."
DEPENDENCIES=$(brew deps $SELECTED_PYTHON 2>/dev/null)

if [ -n "$DEPENDENCIES" ]; then
    echo "⚠️  警告：以下包依赖 $SELECTED_PYTHON:"
    echo "$DEPENDENCIES"
    echo ""
    read -p "仍然要删除吗？请输入 'yes' 继续: " force_confirm

    if [ "$force_confirm" != "yes" ]; then
        echo "❌ 操作已取消"
        exit 0
    fi
fi

# 删除 Python
echo "正在删除 $SELECTED_PYTHON..."
brew uninstall $SELECTED_PYTHON

if [ $? -eq 0 ]; then
    echo "✅ $SELECTED_PYTHON 删除成功"
else
    echo "❌ 删除失败"
    exit 1
fi

# 清理缓存
echo ""
echo "🧹 清理 Homebrew 缓存..."
brew cleanup

echo ""
echo "================================================"
echo "✅ 删除完成"
echo "================================================"
echo ""
echo "建议操作:"
echo "1. 检查系统默认 Python: which python3"
echo "2. 更新 PATH 环境变量（如需要）"
echo "3. 重新创建虚拟环境: python3 -m venv venv"
echo ""
