#!/bin/bash

echo "🐍 Python 版本清理工具"
echo "⚠️  警告：此脚本仅删除通过 Homebrew 安装的 Python，不会删除系统自带的 Python"
echo ""
echo "================================================"
echo "📋 步骤 1: 检查所有已安装的 Python 版本"
echo "================================================"
echo ""

# 检查系统自带 Python
echo "🔹 系统自带 Python:"
echo "  - $(python3 --version 2>/dev/null || echo '未找到')"
echo "  - 位置: $(which python3 2>/dev/null || echo '未找到')"
echo ""

# 检查 Homebrew 安装的 Python
echo "🔹 Homebrew 安装的 Python:"
brew list | grep python
echo ""

# 列出所有 Python 版本
echo "🔹 所有 Python 版本:"
ls -la /usr/local/bin/python* 2>/dev/null
ls -la /opt/homebrew/bin/python* 2>/dev/null
echo ""

echo "================================================"
echo "📋 步骤 2: 检查 Python 路径和版本"
echo "================================================"
echo ""

echo "当前使用的 Python:"
python3 --version
which python3
echo ""

echo "所有 Python 3.x 版本:"
for py in /opt/homebrew/bin/python3.* /usr/local/bin/python3.*; do
    if [ -f "$py" ]; then
        echo "  - $py -> $($py --version 2>/dev/null | head -1)"
    fi
done
echo ""

echo "================================================"
echo "📋 步骤 3: 检查虚拟环境"
echo "================================================"
echo ""

if [ -d "venv" ]; then
    echo "当前目录的虚拟环境:"
    echo "  - venv/"
    echo "  - Python 版本: $(venv/bin/python --version 2>/dev/null || echo '未知')"
else
    echo "未找到当前目录的虚拟环境"
fi
echo ""

echo "================================================"
echo "📋 步骤 4: 检查 pip 缓存"
echo "================================================"
echo ""

echo "pip 缓存大小:"
du -sh ~/.cache/pip 2>/dev/null || echo "未找到 pip 缓存"
echo ""

echo "================================================"
echo "⚠️  重要提醒"
echo "================================================"
echo ""
echo "1. macOS 系统自带 Python，不要删除"
echo "2. 只能删除通过 Homebrew 安装的 Python"
echo "3. 删除前请确认不再使用该版本"
echo "4. 建议保留当前项目使用的 Python 版本"
echo ""

echo "================================================"
echo "📋 推荐清理步骤"
echo "================================================"
echo ""
echo "1. 删除不需要的 Python 版本（Homebrew 安装）:"
echo "   brew uninstall python@3.13"
echo "   brew uninstall python@3.11"
echo ""
echo "2. 清理 pip 缓存:"
echo "   pip cache purge"
echo ""
echo "3. 删除不需要的虚拟环境:"
echo "   rm -rf venv_old"
echo ""
echo "4. 清理 Homebrew 旧版本:"
echo "   brew cleanup --prune=all"
echo ""

echo "================================================"
echo "📋 查看依赖关系"
echo "================================================"
echo ""

echo "查看哪些包依赖了特定 Python 版本:"
brew deps --installed | grep python
echo ""

echo "✅ 检查完成！"
echo ""
echo "💡 提示：运行 'brew list | grep python' 查看所有 Homebrew 安装的 Python"
echo "💡 提示：运行 'ls -la /opt/homebrew/bin/python*' 查看所有 Python 二进制文件"
