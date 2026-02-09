#!/bin/bash

# 修复 embedding 依赖问题

echo "=========================================="
echo "修复 sentence-transformers 版本问题"
echo "=========================================="

cd "/Users/sixsevensconsubine/Desktop/阅心/backend"

# 激活虚拟环境
source venv/bin/activate

# 升级 sentence-transformers
echo "升级 sentence-transformers..."
pip install --upgrade sentence-transformers

# 确保 huggingface_hub 版本兼容
echo "检查 huggingface_hub 版本..."
pip install "huggingface_hub>=0.20.0"

echo ""
echo "✅ 修复完成！"
echo ""
echo "现在可以运行："
echo "  python test_save_one.py"
echo "  或"
echo "  python scripts/init_books.py"
