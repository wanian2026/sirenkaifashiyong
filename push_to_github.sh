#!/bin/bash

# GitHub推送脚本
# 使用方法: 在本地Mac终端执行此脚本

echo "=========================================="
echo "    GitHub 仓库推送脚本"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# 检查是否在正确的目录
if [ ! -f "app/main.py" ]; then
    echo "错误: 请在项目根目录执行此脚本"
    exit 1
fi

# 显示当前状态
echo "[1] 当前Git状态:"
git status
echo ""

# 显示即将推送的文件
echo "[2] 即将推送的文件:"
echo "总文件数: $(git ls-files | wc -l)"
echo "总代码行数: $(git ls-files | xargs cat | wc -l)"
echo ""

# 确认推送
read -p "是否确认推送到GitHub? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消推送"
    exit 0
fi

echo ""
echo "[3] 正在推送到GitHub..."
echo ""

# 推送到GitHub
if git push origin main; then
    echo ""
    echo "=========================================="
    echo "✅ 推送成功!"
    echo "=========================================="
    echo ""
    echo "现在可以在GitHub网页端查看:"
    echo "  📁 https://github.com/wanian2026/sirenkaifashiyong"
    echo ""
    echo "包含文件:"
    echo "  - 25个文件"
    echo "  - 2620+ 行代码"
    echo "  - 完整的加密货币交易系统"
    echo ""
else
    echo ""
    echo "❌ 推送失败!"
    echo ""
    echo "可能的原因:"
    echo "  1. 身份验证失败"
    echo "  2. 网络连接问题"
    echo "  3. 仓库权限问题"
    echo ""
    echo "解决方法:"
    echo "  方法1 - 使用GitHub CLI:"
    echo "    gh auth login"
    echo "    git push origin main"
    echo ""
    echo "  方法2 - 使用Personal Access Token:"
    echo "    git remote set-url origin https://TOKEN@github.com/wanian2026/sirenkaifashiyong.git"
    echo "    git push origin main"
    echo ""
    exit 1
fi
