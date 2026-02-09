#!/bin/bash

# 阅心后端启动脚本

echo "=========================================="
echo "阅心 - 后端服务启动"
echo "=========================================="

# 检查是否在正确的目录
if [ ! -f "main.py" ]; then
    echo "❌ 错误: 请在 backend 目录下运行此脚本"
    echo "   当前目录: $(pwd)"
    exit 1
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python 3.9+"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 创建虚拟环境失败"
        exit 1
    fi
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ 激活虚拟环境失败"
    exit 1
fi

# 检查关键依赖
echo "📋 检查依赖..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠️  缺少依赖，正在安装..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 安装依赖失败"
        exit 1
    fi
else
    echo "✅ 依赖已安装"
fi

# 检查 email-validator
if ! python -c "import email_validator" 2>/dev/null; then
    echo "⚠️  安装 email-validator..."
    pip install email-validator>=2.0.0
fi

# 检查数据库文件
if [ ! -f "yuexin.db" ]; then
    echo "⚠️  数据库文件不存在，将创建空数据库"
    echo "   如需初始化书籍数据，请运行: python scripts/init_books.py"
fi

# 启动服务
echo ""
echo "=========================================="
echo "🚀 启动后端服务..."
echo "=========================================="
echo "📍 服务地址: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo "💡 健康检查: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

# 启动 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 如果启动失败，显示错误
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 服务启动失败！"
    echo ""
    echo "请检查："
    echo "1. 端口 8000 是否被占用: lsof -i :8000"
    echo "2. 查看上方的错误信息"
    echo "3. 尝试手动启动: python -m uvicorn main:app --reload"
    exit 1
fi
