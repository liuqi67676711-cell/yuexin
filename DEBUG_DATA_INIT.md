# 调试数据初始化问题

## 🔍 问题：显示"完成！共保存 0 本书籍"

我已经改进了脚本，添加了更详细的日志。现在请按以下步骤操作：

## 📝 步骤 1：测试网络连接

首先测试是否能访问 Open Library API：

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
source venv/bin/activate
python test_api.py
```

**如果测试失败**：
- 检查网络连接
- 如果在中国大陆，可能需要配置代理
- 或者使用 VPN

**如果测试成功**：
- 继续下一步

## 📝 步骤 2：重新运行初始化脚本

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
source venv/bin/activate
python scripts/init_books.py
```

现在脚本会显示更详细的信息：
- 每个搜索查询的结果数量
- 去重前后的书籍数量
- 每本书的保存状态
- 详细的错误信息

## 🔍 可能的原因和解决方案

### 原因 1：网络连接问题

**症状**：看到 "搜索 xxx 失败" 或 "HTTP 错误"

**解决**：
1. 检查网络连接
2. 测试是否能访问 https://openlibrary.org
3. 如果在中国大陆，可能需要代理

### 原因 2：API 返回空数据

**症状**：看到 "API 返回 0 条结果"

**解决**：
- 可能是 API 临时问题，稍后重试
- 或者尝试不同的搜索关键词

### 原因 3：数据解析失败

**症状**：看到 "解析失败" 或 "缺少书名"

**解决**：
- 我已经改进了数据解析逻辑
- 现在即使没有 ISBN 也能保存

### 原因 4：数据库保存失败

**症状**：看到 "保存失败" 错误

**解决**：
- 检查数据库文件权限
- 确保没有其他程序在使用数据库

## 📊 查看详细日志

运行脚本后，请查看完整的输出，特别是：
1. 每个搜索查询的结果
2. 去重前后的数量
3. 任何错误信息

把完整的输出发给我，我会帮你分析问题。

## 🚀 快速测试

运行测试脚本：
```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
source venv/bin/activate
python test_api.py
```

如果测试成功，再运行初始化脚本。
