#!/bin/bash

# 加密货币交易系统 - 停止脚本

echo "=========================================="
echo "  加密货币交易系统 - 停止中..."
echo "=========================================="
echo ""

# 读取配置文件中的端口
API_PORT=8000
if [ -f ".env" ]; then
    API_PORT=$(grep API_PORT .env | cut -d '=' -f2)
    API_PORT=${API_PORT:-8000}
fi

# 查找占用端口的进程
PID=$(lsof -ti :$API_PORT)

if [ -z "$PID" ]; then
    echo "没有找到运行在端口 $API_PORT 的服务"
    echo "服务可能已经停止"
    exit 0
fi

echo "找到进程 PID: $PID"

# 尝试优雅关闭
echo "正在停止服务..."
kill $PID

# 等待进程结束
sleep 2

# 检查进程是否还在运行
if ps -p $PID > /dev/null; then
    echo "进程未响应，强制关闭..."
    kill -9 $PID
    sleep 1
fi

# 再次检查
if ps -p $PID > /dev/null; then
    echo "错误: 无法停止进程 PID: $PID"
    echo "请手动执行: kill -9 $PID"
    exit 1
else
    echo "=========================================="
    echo "  服务已停止"
    echo "=========================================="
    exit 0
fi
