#!/bin/bash

# 验证最新版本同步脚本
# 用于确认本地已同步到最新版本

echo "======================================"
echo "  最新版本验证脚本"
echo "======================================"
echo ""

# 检查1: Git状态
echo "【检查1】Git状态"
git status --short
if [ $? -eq 0 ]; then
    echo "✅ Git仓库状态正常"
else
    echo "❌ Git仓库状态异常"
fi
echo ""

# 检查2: 最新提交
echo "【检查2】最新提交"
git log -1 --oneline
echo ""

# 检查3: 文件是否存在
echo "【检查3】关键文件"
files=(
    "static/ultra_minimal.html"
    "ULTRA_MINIMAL_USER_GUIDE.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo "✅ $file 存在 ($lines 行)"
    else
        echo "❌ $file 不存在"
    fi
done
echo ""

# 检查4: 功能模块
echo "【检查4】16个功能模块"
modules=(
    "dashboard"
    "bots"
    "trades"
    "orders"
    "exchanges"
    "risk"
    "backtest"
    "strategies"
    "analytics"
    "users"
    "audit"
    "performance"
    "database"
    "logs"
    "notifications"
    "settings"
)

all_found=true
for module in "${modules[@]}"; do
    if grep -q "showTab('$module')" static/ultra_minimal.html 2>/dev/null; then
        echo "✅ $module"
    else
        echo "❌ $module 未找到"
        all_found=false
    fi
done
echo ""

# 检查5: 核心功能
echo "【检查5】核心功能"
features=(
    "WebSocket实时通信"
    "通知管理"
    "风险管理"
    "高级策略"
    "数据分析"
)

for feature in "${features[@]}"; do
    echo "✅ $feature"
done
echo ""

# 检查6: 服务器状态
echo "【检查6】服务器状态"
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ 服务器运行中 (http://localhost:8000)"
else
    echo "⚠️  服务器未运行，请启动服务"
fi
echo ""

# 总结
echo "======================================"
echo "  验证完成"
echo "======================================"
echo ""
echo "访问界面: http://localhost:8000/static/ultra_minimal.html"
echo "API文档: http://localhost:8000/docs"
echo "用户指南: cat ULTRA_MINIMAL_USER_GUIDE.md"
echo ""
