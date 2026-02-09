#!/bin/bash

# 阅心前端启动脚本

echo "=========================================="
echo "阅心 - 前端服务启动"
echo "=========================================="

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 Node.js，请先安装 Node.js 18+"
    exit 1
fi

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到 npm，请先安装 npm"
    exit 1
fi

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "安装依赖包（这可能需要几分钟）..."
    npm install
fi

# 启动服务
echo "启动前端服务..."
echo "网站将在 http://localhost:5173 运行"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="

npm run dev
