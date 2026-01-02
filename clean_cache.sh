#!/bin/bash
# Python 缓存清理脚本

echo "====================================="
echo "Python 缓存清理工具"
echo "====================================="
echo ""

# 当前目录
CURRENT_DIR=$(pwd)
echo "清理目录: $CURRENT_DIR"
echo ""

# 统计清理前的文件数量
PYC_COUNT=$(find . -name "*.pyc" 2>/dev/null | wc -l)
PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)

echo "发现文件:"
echo "  - .pyc 文件: $PYC_COUNT"
echo "  - __pycache__ 目录: $PYCACHE_COUNT"
echo ""

# 清理 .pyc 文件
echo "1/2 清理 .pyc 文件..."
find . -name "*.pyc" -delete 2>/dev/null
PYC_DELETED=$(find . -name "*.pyc" 2>/dev/null | wc -l)
echo "✅ 已清理 .pyc 文件"
echo ""

# 清理 __pycache__ 目录
echo "2/2 清理 __pycache__ 目录..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
PYCACHE_DELETED=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
echo "✅ 已清理 __pycache__ 目录"
echo ""

# 最终统计
FINAL_PYC=$(find . -name "*.pyc" 2>/dev/null | wc -l)
FINAL_PYCACHE=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)

echo "====================================="
echo "清理完成！"
echo "====================================="
echo "剩余文件:"
echo "  - .pyc 文件: $FINAL_PYC"
echo "  - __pycache__ 目录: $FINAL_PYCACHE"
echo ""
echo "已清理:"
echo "  - .pyc 文件: $((PYC_COUNT - FINAL_PYC))"
echo "  - __pycache__ 目录: $((PYCACHE_COUNT - FINAL_PYCACHE))"
echo ""
