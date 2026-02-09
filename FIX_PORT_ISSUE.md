# 解决端口占用问题

## 🔍 问题

端口 8000 已被占用，无法启动后端服务。

## ✅ 解决方法

### 方法一：杀死占用端口的进程（推荐）

我已经创建了自动脚本：

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
./kill_port.sh
```

这个脚本会：
1. 查找占用 8000 端口的进程
2. 显示进程信息
3. 询问是否杀死进程
4. 如果确认，自动杀死进程

### 方法二：手动查找并杀死进程

```bash
# 1. 查找占用端口的进程
lsof -i :8000

# 2. 杀死进程（替换 PID 为实际进程号）
kill -9 <PID>

# 或者一行命令
lsof -ti:8000 | xargs kill -9
```

### 方法三：使用其他端口（临时方案）

如果不想杀死现有进程，可以使用其他端口：

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
./start_alt_port.sh
```

这会使用端口 8001 启动服务。

**注意**：如果使用 8001 端口，需要更新前端配置：
- 编辑 `frontend/vite.config.ts`
- 将 proxy target 改为 `http://localhost:8001`

## 🚀 推荐操作流程

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"

# 1. 杀死占用端口的进程
./kill_port.sh
# 输入 y 确认

# 2. 启动服务
./start.sh
```

## 📝 检查端口占用

随时可以检查端口是否被占用：

```bash
lsof -i :8000
```

如果没有输出，说明端口未被占用。
