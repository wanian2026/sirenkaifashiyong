#!/bin/bash

# 从GitHub同步最新进度到本地

echo "======================================"
echo "  同步GitHub最新进度"
echo "======================================"
echo ""

# 1. 拉取最新代码
echo "【步骤1】拉取最新代码..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ 拉取失败，请检查网络连接"
    exit 1
fi

echo "✅ 代码拉取成功"
echo ""

# 2. 显示更新内容
echo "【步骤2】最新提交记录..."
git log --oneline -5
echo ""

# 3. 显示更新的文件
echo "【步骤3】更新的文件..."
git diff HEAD@{1} HEAD --stat 2>/dev/null || echo "（首次更新或无差异）"
echo ""

# 4. 检查关键文件
echo "【步骤4】检查关键文件..."
if [ -f "static/ultra_minimal.html" ]; then
    lines=$(wc -l < "static/ultra_minimal.html")
    echo "✅ static/ultra_minimal.html ($lines 行)"
else
    echo "❌ static/ultra_minimal.html 不存在"
fi

if [ -f "ULTRA_MINIMAL_USER_GUIDE.md" ]; then
    lines=$(wc -l < "ULTRA_MINIMAL_USER_GUIDE.md")
    echo "✅ ULTRA_MINIMAL_USER_GUIDE.md ($lines 行)"
else
    echo "❌ ULTRA_MINIMAL_USER_GUIDE.md 不存在"
fi
echo ""

# 5. 检查服务器状态
echo "【步骤5】服务器状态..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ 服务器正在运行"
    echo "   提示: 如需重启服务，请先按 Ctrl+C 停止当前服务"
else
    echo "⚠️  服务器未运行"
    echo ""
    echo "启动命令："
    echo "  source venv/bin/activate"
    echo "  python -m uvicorn app.main:app --reload"
fi
echo ""

# 6. 完成
echo "======================================"
echo "  同步完成！"
echo "======================================"
echo ""
echo "访问界面: http://localhost:8000/static/ultra_minimal.html"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "如需验证更新，请运行："
echo "  ./verify_update.sh"
echo ""
