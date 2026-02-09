#!/bin/bash

# 手动启动脚本（更详细的错误信息）

cd "/Users/sixsevensconsubine/Desktop/阅心/backend"

echo "当前目录: $(pwd)"
echo ""

# 激活虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
else
    echo "❌ 虚拟环境不存在，请先运行: python3 -m venv venv"
    exit 1
fi

# 检查 Python
echo "Python 路径: $(which python)"
echo "Python 版本: $(python --version)"
echo ""

# 检查关键模块
echo "检查关键模块..."
python -c "import fastapi; print('✅ fastapi')" || echo "❌ fastapi 未安装"
python -c "import uvicorn; print('✅ uvicorn')" || echo "❌ uvicorn 未安装"
python -c "import sqlalchemy; print('✅ sqlalchemy')" || echo "❌ sqlalchemy 未安装"
python -c "import email_validator; print('✅ email-validator')" || echo "❌ email-validator 未安装"
echo ""

# 尝试导入主模块
echo "测试导入主模块..."
python -c "from main import app; print('✅ main.py 导入成功')" || {
    echo "❌ main.py 导入失败"
    echo "详细错误："
    python -c "from main import app" 2>&1
    exit 1
}

echo ""
echo "启动服务..."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
