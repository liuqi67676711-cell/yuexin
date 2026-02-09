# 重启后端服务指南

## 方法一：使用启动脚本（推荐）

```bash
# 1. 进入后端目录
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"

# 2. 如果服务正在运行，先停止它
# 在运行服务的终端窗口按 Ctrl+C

# 3. 运行启动脚本
bash start.sh
```

## 方法二：手动启动

```bash
# 1. 进入后端目录
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 方法三：如果端口被占用

如果显示 `Address already in use`，可以使用以下方法：

### 选项A：杀死占用端口的进程

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
bash kill_port.sh
```

然后重新启动：
```bash
bash start.sh
```

### 选项B：使用备用端口

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
bash start_alt_port.sh
```

**注意**：如果使用备用端口（8001），需要修改前端配置：
编辑 `frontend/vite.config.ts`，将代理地址改为：
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8001',
    changeOrigin: true,
  },
}
```

## 验证服务是否启动成功

启动成功后，你应该看到类似这样的输出：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 检查服务状态

在浏览器中访问：
- http://localhost:8000/health
- 应该返回：`{"status":"healthy"}`

## 常见问题

### 1. 找不到 venv
如果提示找不到虚拟环境，先创建：
```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 依赖缺失
如果提示缺少模块，安装依赖：
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 数据库迁移
首次启动或更新后，确保数据库表已创建：
```bash
source venv/bin/activate
python migrate_db.py
```
