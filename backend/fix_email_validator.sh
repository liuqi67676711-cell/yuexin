#!/bin/bash

# 修复 email-validator 缺失问题

echo "=========================================="
echo "安装 email-validator"
echo "=========================================="

cd "/Users/sixsevensconsubine/Desktop/阅心/backend"

# 激活虚拟环境
source venv/bin/activate

# 安装 email-validator
echo "安装 email-validator..."
pip install email-validator>=2.0.0

# 或者安装 pydantic[email]
echo "安装 pydantic[email]..."
pip install "pydantic[email]"

echo ""
echo "✅ 修复完成！"
echo ""
echo "现在可以启动后端服务了："
echo "  uvicorn main:app --reload"
