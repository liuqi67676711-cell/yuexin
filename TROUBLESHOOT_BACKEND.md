# 后端启动问题排查

## 🔍 问题排查步骤

### 步骤 1：检查当前目录

确保你在 `backend` 目录下：

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
pwd
# 应该显示: /Users/sixsevensconsubine/Desktop/阅心/backend
```

### 步骤 2：使用手动启动脚本（查看详细错误）

我已经创建了一个更详细的启动脚本：

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
./start_manual.sh
```

这个脚本会：
- 显示详细的检查信息
- 测试每个关键模块
- 显示具体的错误信息

### 步骤 3：手动启动（如果脚本失败）

如果脚本失败，尝试手动启动：

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
source venv/bin/activate

# 检查 Python 和模块
python --version
python -c "import fastapi; print('fastapi OK')"
python -c "import uvicorn; print('uvicorn OK')"

# 尝试启动
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## ⚠️ 常见问题

### 问题 1：端口被占用

**症状**：`Address already in use`

**解决**：
```bash
# 查看占用 8000 端口的进程
lsof -i :8000

# 杀死进程（替换 PID 为实际进程号）
kill -9 <PID>

# 或者使用其他端口
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 问题 2：模块导入错误

**症状**：`ModuleNotFoundError` 或 `ImportError`

**解决**：
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 问题 3：数据库文件权限问题

**症状**：`Permission denied` 或数据库相关错误

**解决**：
```bash
# 检查文件权限
ls -l yuexin.db

# 如果需要，修改权限
chmod 644 yuexin.db
```

### 问题 4：虚拟环境未激活

**症状**：找不到模块或使用系统 Python

**解决**：
```bash
source venv/bin/activate
# 确认看到 (venv) 前缀
```

## 📝 请提供的信息

如果启动失败，请提供：

1. **完整的错误信息**（从终端复制）
2. **运行 `./start_manual.sh` 的输出**
3. **Python 版本**：`python --version`
4. **当前目录**：`pwd`

## 🚀 快速操作

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"

# 方法 1：使用改进的启动脚本
./start.sh

# 方法 2：使用详细诊断脚本
./start_manual.sh

# 方法 3：手动启动
source venv/bin/activate
python -m uvicorn main:app --reload
```

请运行 `./start_manual.sh` 并把输出发给我，我会帮你定位问题！
