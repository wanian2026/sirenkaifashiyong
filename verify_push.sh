#!/bin/bash
# 推送后验证脚本

echo "✅ 推送后验证"
echo "=============="

# 1. 检查本地与远程是否同步
echo "1️⃣ 检查本地与远程同步状态..."
git fetch origin
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✅ 本地与远程已同步"
else
    echo "❌ 本地与远程不同步"
fi

# 2. 显示最新的3个提交
echo ""
echo "2️⃣ 最新的3个提交："
git log --oneline -3

# 3. 统计总提交数
echo ""
echo "3️⃣ 项目统计："
echo "总提交数: $(git rev-list --count HEAD)"
echo "分支数: $(git branch -a | wc -l)"
echo "作者数: $(git shortlog -sn | wc -l)"

echo ""
echo "=============="
echo "✅ 验证完成"
