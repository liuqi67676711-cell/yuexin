# 故障排除指南

## 网站显示空白页面

### 检查步骤：

1. **打开浏览器开发者工具**
   - 按 `F12` 或 `Cmd+Option+I` (Mac)
   - 查看 Console（控制台）标签页
   - 查看是否有红色错误信息

2. **检查后端是否运行**
   - 打开 http://localhost:8000/docs
   - 如果能看到 API 文档页面，说明后端正常运行
   - 如果无法访问，后端可能没有启动

3. **检查网络请求**
   - 在开发者工具的 Network（网络）标签页
   - 刷新页面
   - 查看是否有请求失败（红色）

### 常见问题及解决方案：

#### 问题1：后端未启动
**症状**：前端页面空白，控制台显示连接错误

**解决**：
```bash
# 确保后端正在运行
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
./start.sh
```

#### 问题2：CORS 错误
**症状**：控制台显示 "CORS policy" 相关错误

**解决**：
- 检查 `backend/.env` 文件中的 `FRONTEND_URL` 是否正确
- 确保值为 `http://localhost:5173`

#### 问题3：JavaScript 错误
**症状**：控制台显示具体的错误信息

**解决**：
- 查看错误信息的具体内容
- 检查是否缺少依赖：`cd frontend && npm install`
- 尝试清除缓存：`rm -rf node_modules && npm install`

#### 问题4：CSS 未加载
**症状**：页面有内容但样式错乱

**解决**：
- 检查 Tailwind CSS 是否正确编译
- 重新启动前端：`cd frontend && npm run dev`

### 快速诊断命令：

```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查前端依赖
cd frontend && npm list --depth=0

# 检查后端依赖
cd backend && pip list | grep fastapi
```

### 如果以上都不行：

1. **完全重启服务**：
   - 停止所有终端中的服务（Ctrl+C）
   - 重新启动后端和前端

2. **清除缓存**：
   ```bash
   # 前端
   cd frontend
   rm -rf node_modules dist
   npm install
   
   # 后端
   cd backend
   rm -rf venv chroma_db yuexin.db
   # 然后重新运行 start.sh
   ```

3. **检查端口占用**：
   ```bash
   # 检查 8000 端口
   lsof -i :8000
   
   # 检查 5173 端口
   lsof -i :5173
   ```

### 获取帮助：

如果问题仍然存在，请提供以下信息：
1. 浏览器控制台的错误信息（截图或复制文本）
2. 后端终端的输出信息
3. 前端终端的输出信息
