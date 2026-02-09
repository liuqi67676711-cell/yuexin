# 快速修复指南

如果遇到以下问题：
1. 搜索显示500错误
2. AI书童显示"请先登录"
3. 功能无法使用

## 立即执行的步骤

### 1. 运行数据库修复脚本

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
bash fix_database.sh
```

### 2. 如果数据库中没有书籍，初始化数据

```bash
bash init_data.sh
```

### 3. 测试后端API

```bash
source venv/bin/activate
python test_backend.py
```

这会显示：
- 数据库连接状态
- 表是否存在
- 书籍数量
- API是否正常工作

### 4. 重启后端服务

```bash
# 停止当前服务（Ctrl+C）
bash start.sh
```

### 5. 检查前端

刷新浏览器，打开开发者工具（F12）：
- Console标签：查看是否有错误
- Network标签：查看API请求状态

## 常见问题

### 问题1: 搜索返回500错误

**原因**：可能是数据库表不存在或数据库中没有书籍

**解决**：
1. 运行 `bash fix_database.sh`
2. 运行 `bash init_data.sh` 初始化书籍数据
3. 重启后端

### 问题2: AI书童显示"请先登录"

**原因**：访客登录没有自动执行

**解决**：
1. 刷新浏览器页面（这会触发自动登录）
2. 检查浏览器控制台是否有登录错误
3. 检查后端是否正常运行

### 问题3: 所有功能都无法使用

**原因**：可能是数据库表没有创建

**解决**：
1. 运行 `bash fix_database.sh`
2. 检查输出，确认所有表都已创建
3. 如果表缺失，运行 `python migrate_db.py`
4. 重启后端

## 验证修复

修复后，检查：

1. ✅ 后端终端没有错误信息
2. ✅ `python test_backend.py` 显示所有测试通过
3. ✅ 浏览器可以正常访问页面
4. ✅ 搜索功能可以返回结果（即使为空）
5. ✅ AI书童可以打开并创建对话

## 如果问题仍然存在

请提供以下信息：

1. `bash fix_database.sh` 的完整输出
2. `python test_backend.py` 的完整输出
3. 后端终端的错误信息
4. 浏览器控制台的错误信息（F12 -> Console）
