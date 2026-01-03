#!/bin/bash

echo "🛑 停止加密货币交易系统"
echo ""

# 查找并停止 uvicorn 进程
PIDS=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "✅ 没有运行中的服务"
else
    echo "正在停止服务 (PID: $PIDS)..."
    kill $PIDS

    # 等待进程结束
    for i in {1..10}; do
        if ! ps -p $PIDS > /dev/null; then
            echo "✅ 服务已停止"
            break
        fi
        echo "等待中... ($i/10)"
        sleep 1
    done

    # 如果进程仍在运行，强制终止
    if ps -p $PIDS > /dev/null; then
        echo "⚠️  强制终止服务"
        kill -9 $PIDS
    fi
fi

echo "✅ 完成"
