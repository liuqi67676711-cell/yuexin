#!/bin/bash

# 杀死占用 8000 端口的进程

PORT=8000

echo "查找占用端口 $PORT 的进程..."

# macOS 使用 lsof
PID=$(lsof -ti:$PORT)

if [ -z "$PID" ]; then
    echo "✅ 端口 $PORT 未被占用"
    exit 0
fi

echo "找到进程: PID=$PID"
echo ""
echo "进程详情:"
lsof -i:$PORT
echo ""

read -p "是否要杀死此进程? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    kill -9 $PID
    echo "✅ 已杀死进程 $PID"
    echo ""
    echo "现在可以启动服务了："
    echo "  ./start.sh"
else
    echo "取消操作"
    echo ""
    echo "你可以："
    echo "1. 手动杀死进程: kill -9 $PID"
    echo "2. 或使用其他端口启动: uvicorn main:app --reload --port 8001"
fi
