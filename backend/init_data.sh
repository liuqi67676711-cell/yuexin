#!/bin/bash

# 阅心 - 数据初始化脚本

echo "=========================================="
echo "阅心 - 数据初始化"
echo "=========================================="

# 检查是否在正确的目录
if [ ! -f "main.py" ]; then
    echo "错误: 请在 backend 目录下运行此脚本"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "检查并安装依赖..."
pip install -r requirements.txt

# 运行初始化脚本
echo "开始初始化书籍数据..."
echo "这可能需要几分钟，请耐心等待..."
echo ""

python scripts/init_books.py

echo ""
echo "=========================================="
echo "数据初始化完成！"
echo "=========================================="
