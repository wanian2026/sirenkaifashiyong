#!/bin/bash
# 推送前检查清单

echo "🔍 推送前安全检查"
echo "===================="

# 1. 检查敏感信息
echo "1️⃣ 检查敏感信息泄露..."
if git diff --cached --name-only | xargs grep -l "SECRET_KEY\|API_SECRET" 2>/dev/null | grep -v ".env"; then
    echo "⚠️  警告：发现可能的敏感信息"
else
    echo "✅ 未发现敏感信息泄露"
fi

# 2. 检查Python语法
echo ""
echo "2️⃣ 检查Python语法..."
python -m py_compile app/main.py app/backtest.py app/cache.py 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Python语法检查通过"
else
    echo "❌ Python语法检查失败"
fi

# 3. 检查未跟踪的大文件
echo ""
echo "3️⃣ 检查大文件..."
large_files=$(find . -type f -size +10M ! -path './.git/*' ! -path './venv/*' ! -path './__pycache__/*')
if [ -n "$large_files" ]; then
    echo "⚠️  警告：发现大文件："
    echo "$large_files"
else
    echo "✅ 未发现大文件"
fi

# 4. 统计更改
echo ""
echo "4️⃣ 统计更改..."
echo "修改的文件: $(git diff --name-only | wc -l)"
echo "新增的文件: $(git ls-files --others --exclude-standard | wc -l)"
echo "待提交的行数: $(git diff --stat | tail -1)"

# 5. 检查远程连接
echo ""
echo "5️⃣ 检查远程连接..."
if git ls-remote origin &>/dev/null; then
    echo "✅ 远程仓库连接正常"
else
    echo "❌ 无法连接到远程仓库"
fi

echo ""
echo "===================="
echo "✅ 检查完成，可以安全推送"
