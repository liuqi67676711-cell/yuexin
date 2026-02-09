# 数据初始化指南

## 📚 如何重新运行数据初始化

### 方法一：使用 Python 直接运行（推荐）

1. **打开终端**，进入后端目录：
```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
```

2. **确保后端依赖已安装**（如果还没安装）：
```bash
pip install -r requirements.txt
```

3. **运行初始化脚本**：
```bash
python scripts/init_books.py
```

或者使用 Python3：
```bash
python3 scripts/init_books.py
```

### 方法二：如果使用虚拟环境

如果你使用了虚拟环境（venv）：

1. **激活虚拟环境**：
```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

2. **运行脚本**：
```bash
python scripts/init_books.py
```

## 📊 初始化过程说明

脚本运行时会：

1. **创建数据库表**（如果不存在）
2. **从 Open Library API 获取书籍数据**
   - 搜索多个热门关键词
   - 获取约 100+ 本书籍
3. **去重处理**
   - 基于 ISBN 或 title+author
4. **保存到数据库**
   - 保存到 SQLite 数据库
   - 生成向量并保存到 Chroma 向量数据库

## ⏱️ 预计时间

- **网络良好**：2-5 分钟
- **网络较慢**：5-10 分钟

## 📝 运行示例输出

正常运行时，你会看到类似这样的输出：

```
开始获取书籍数据...
搜索: science fiction
搜索: romance
...
共获取 120 本书籍
去重后: 95 本书籍
已保存: The Hitchhiker's Guide to the Galaxy (ID: 1)
已保存: Pride and Prejudice (ID: 2)
...
进度: 10 本书籍已处理
进度: 20 本书籍已处理
...
完成！共保存 95 本书籍
```

## ⚠️ 常见问题

### Q1: 提示 "ModuleNotFoundError: No module named 'app'"
**解决**：确保在 `backend` 目录下运行脚本，不要进入 `scripts` 目录

### Q2: 提示网络错误
**解决**：
- 检查网络连接
- 确保可以访问 `openlibrary.org`
- 如果在中国大陆，可能需要代理

### Q3: 显示 "共保存 0 本书籍"
**解决**：
- 检查网络连接
- 查看是否有错误信息
- 确保数据库文件有写入权限

### Q4: 提示数据库锁定错误
**解决**：
- 确保后端服务已停止（按 Ctrl+C）
- 关闭可能正在使用数据库的程序
- 重新运行脚本

## 🔄 重新初始化

如果你想清空现有数据并重新初始化：

1. **停止后端服务**（如果正在运行）

2. **删除数据库文件**（可选）：
```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
rm yuexin.db  # 删除 SQLite 数据库
rm -rf chroma_db  # 删除向量数据库
```

3. **重新运行初始化脚本**：
```bash
python scripts/init_books.py
```

## ✅ 验证数据是否成功初始化

初始化完成后，你可以：

1. **检查数据库文件**：
```bash
ls -lh yuexin.db  # 应该能看到数据库文件
```

2. **启动后端服务**，访问 API 文档：
   - 打开 http://localhost:8000/docs
   - 测试 `/api/books/` 接口，应该能看到书籍列表

3. **在前端测试**：
   - 刷新浏览器页面
   - 尝试语义搜索
   - 应该能看到推荐结果

## 📞 需要帮助？

如果遇到问题，请提供：
1. 完整的错误信息
2. 运行脚本时的输出
3. 你的 Python 版本（运行 `python --version`）
