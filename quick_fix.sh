#!/bin/bash
# 快速修复数据库初始化问题

echo "====================================="
echo "数据库初始化修复脚本"
echo "====================================="
echo ""

# 清理 Python 缓存
echo "1/3 清理 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo "✅ 缓存清理完成"
echo ""

# 删除旧数据库
echo "2/3 删除旧数据库..."
if [ -f "crypto_bot.db" ]; then
    rm crypto_bot.db
    echo "✅ 已删除旧数据库"
else
    echo "ℹ️  未找到旧数据库文件"
fi
echo ""

# 初始化数据库
echo "3/3 初始化数据库..."
python init_db.py

echo ""
echo "====================================="
echo "完成！"
echo "====================================="
echo ""
echo "下一步："
echo "1. 配置环境变量: cp .env.example .env && nano .env"
echo "2. 启动服务: ./start.sh"
echo "3. 访问界面: http://localhost:8000/static/index.html"
echo ""
