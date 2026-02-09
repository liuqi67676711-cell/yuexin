# 重启服务指南

## 🔄 快速重启步骤

### 1. 重启后端服务

```bash
# 进入后端目录
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"

# 如果后端正在运行，先停止（在运行后端的终端按 Ctrl+C）

# 重新启动
bash start.sh
```

**验证后端是否启动成功**：
- 看到 `INFO:     Uvicorn running on http://0.0.0.0:8000` 表示成功
- 浏览器访问 http://localhost:8000/health 应该返回 `{"status":"healthy"}`

### 2. 重启前端服务

```bash
# 进入前端目录
cd "/Users/sixsevensconsubine/Desktop/阅心/frontend"

# 如果前端正在运行，先停止（在运行前端的终端按 Ctrl+C）

# 重新启动
npm run dev
```

**验证前端是否启动成功**：
- 看到 `Local: http://localhost:5173` 表示成功
- 浏览器访问 http://localhost:5173 应该看到页面

## 🐛 如果页面是黑色的，可能的原因和解决方法

### 原因1：CSS样式没有加载
**解决方法**：
1. 检查浏览器控制台（F12）是否有CSS加载错误
2. 清除浏览器缓存并刷新（Ctrl+Shift+R 或 Cmd+Shift+R）
3. 确认 `frontend/src/index.css` 文件存在且内容正确

### 原因2：JavaScript错误
**解决方法**：
1. 打开浏览器开发者工具（F12）
2. 查看 Console 标签中的错误信息
3. 查看 Network 标签，确认所有资源都加载成功

### 原因3：后端服务未运行
**解决方法**：
1. 确认后端服务正在运行（访问 http://localhost:8000/health）
2. 如果后端未运行，按照上面的步骤重启后端

### 原因4：端口被占用
**解决方法**：
```bash
# 检查端口占用
lsof -i :8000  # 后端端口
lsof -i :5173  # 前端端口

# 如果被占用，杀死进程或使用备用端口
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
bash kill_port.sh  # 杀死占用8000端口的进程
```

## 📋 完整重启流程

```bash
# 1. 停止所有服务（在各自的终端按 Ctrl+C）

# 2. 重启后端
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
bash start.sh

# 3. 打开新终端，重启前端
cd "/Users/sixsevensconsubine/Desktop/阅心/frontend"
npm run dev

# 4. 浏览器访问 http://localhost:5173
```

## ✅ 验证步骤

1. **后端健康检查**：
   ```bash
   curl http://localhost:8000/health
   ```
   应该返回：`{"status":"healthy"}`

2. **前端页面检查**：
   - 访问 http://localhost:5173
   - 应该看到"阅心"标题和搜索框
   - 页面应该是深色主题（黑色背景）

3. **浏览器控制台检查**：
   - 按 F12 打开开发者工具
   - 查看 Console 是否有错误
   - 查看 Network 是否所有请求都成功

## 🔧 如果问题仍然存在

1. **清除浏览器缓存**：
   - Chrome/Edge: Ctrl+Shift+Delete (Windows) 或 Cmd+Shift+Delete (Mac)
   - 选择"缓存的图片和文件"，清除

2. **检查文件完整性**：
   ```bash
   # 检查前端依赖
   cd "/Users/sixsevensconsubine/Desktop/阅心/frontend"
   npm install
   
   # 检查后端依赖
   cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **查看详细错误信息**：
   - 浏览器控制台（F12 > Console）
   - 后端终端输出
   - 前端终端输出

## 💡 提示

- 如果页面是**纯黑色**（没有任何内容），可能是JavaScript错误
- 如果页面有内容但**背景是黑色**，这是正常的（深色主题）
- 如果页面**完全空白**，检查浏览器控制台的错误信息
