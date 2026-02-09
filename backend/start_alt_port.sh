#!/bin/bash

# 使用备用端口启动（8001）

cd "/Users/sixsevensconsubine/Desktop/阅心/backend"

echo "=========================================="
echo "阅心 - 后端服务启动（端口 8001）"
echo "=========================================="

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 检查 email-validator
if ! python -c "import email_validator" 2>/dev/null; then
    echo "安装 email-validator..."
    pip install email-validator>=2.0.0
fi

echo ""
echo "🚀 启动服务（端口 8001）..."
echo "📍 服务地址: http://localhost:8001"
echo "📚 API 文档: http://localhost:8001/docs"
echo ""
echo "⚠️  注意：前端需要更新 API 地址为 http://localhost:8001"
echo "   或者编辑 frontend/vite.config.ts 中的 proxy target"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8001
