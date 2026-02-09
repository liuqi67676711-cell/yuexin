# 修复 Embedding 导入错误

## 🔍 问题原因

错误 `cannot import name 'cached_download' from 'huggingface_hub'` 是因为：
- `sentence-transformers==2.2.2` 版本太旧
- 新版本的 `huggingface_hub` 已经移除了 `cached_download` 函数
- 需要升级 `sentence-transformers` 到更新的版本

## ✅ 解决方法

### 方法一：使用自动修复脚本（推荐）

我已经创建了自动修复脚本：

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
./fix_embedding.sh
```

这个脚本会：
1. 激活虚拟环境
2. 升级 sentence-transformers
3. 确保 huggingface_hub 版本兼容

### 方法二：手动修复

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
source venv/bin/activate

# 升级 sentence-transformers
pip install --upgrade sentence-transformers

# 确保 huggingface_hub 版本兼容
pip install "huggingface_hub>=0.20.0"
```

## 🚀 修复后操作

修复完成后：

1. **测试单本书保存**：
```bash
python test_save_one.py
```

2. **如果测试成功，运行完整初始化**：
```bash
python scripts/init_books.py
```

## 📝 我已经做的改进

1. **更新了 requirements.txt**：使用 `sentence-transformers>=2.3.0`
2. **改进了错误处理**：如果导入失败，会使用备用方案
3. **添加了自动修复脚本**：一键修复依赖问题

## ⚠️ 注意事项

- 升级 sentence-transformers 可能需要几分钟
- 首次使用模型时会下载模型文件（可能需要一些时间）
- 如果网络不好，模型下载可能会失败

## 🔍 如果修复后仍有问题

如果修复后仍有问题，请：
1. 运行 `pip list | grep sentence` 查看版本
2. 运行 `pip list | grep huggingface` 查看版本
3. 把输出发给我
