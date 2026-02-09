# 🚀 阅心 - 启动指南

## 我已经帮你完成了以下工作：

✅ **1. 大模型配置（AI 书童回复质量）**
- 不配置也可运行，AI 书童会使用内置简单回复
- **推荐**：在 `backend/.env` 中配置任一接口，获得更详细、自然的对话：
  - **OpenAI**：`OPENAI_API_KEY=sk-xxx`（可选 `OPENAI_BASE_URL`、`OPENAI_MODEL`）
  - **DeepSeek**：`DEEPSEEK_API_KEY=xxx`（可选 `DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`）
- 优先使用 DeepSeek，未配置时使用 OpenAI，都未配置则使用内置回复

✅ **2. 数据初始化**
- 已创建自动初始化脚本
- 首次运行会自动从 Open Library API 获取书籍数据
- 无需手动操作

✅ **3. 启动脚本**
- 已创建一键启动脚本
- 双击即可运行

## 📋 现在请按以下步骤操作：

### 方法一：使用启动脚本（最简单）

**第一步：启动后端**

1. 打开终端（Terminal）
2. 运行以下命令：
```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
chmod +x start.sh
./start.sh
```

等待看到 "服务将在 http://localhost:8000 运行" 的提示

**第二步：启动前端（新开一个终端窗口）**

1. 打开新的终端窗口
2. 运行以下命令：
```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/frontend"
chmod +x start.sh
./start.sh
```

等待看到 "网站将在 http://localhost:5173 运行" 的提示

**第三步：访问网站**

在浏览器中打开：**http://localhost:5173**

---

### 方法二：手动启动（如果脚本不工作）

**启动后端：**
```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/init_books.py  # 首次运行需要初始化数据
uvicorn main:app --reload
```

**启动前端（新终端）：**
```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/frontend"
npm install
npm run dev
```

---

## ⚠️ 重要提示

1. **首次运行需要时间**：
   - 安装依赖可能需要 5-10 分钟
   - 初始化书籍数据可能需要 2-5 分钟
   - 请耐心等待

2. **需要两个终端窗口**：
   - 一个运行后端（端口 8000）
   - 一个运行前端（端口 5173）

3. **访问地址**：
   - 前端网站：http://localhost:5173
   - 后端 API：http://localhost:8000/docs

4. **如果遇到问题**：
   - 检查 Python 版本（需要 3.9+）
   - 检查 Node.js 版本（需要 18+）
   - 查看终端错误信息

---

## 🎉 启动成功后

1. 在浏览器访问 http://localhost:5173
2. 尝试语义搜索："最近工作压力大，想看点轻松的书"
3. 注册账户体验完整功能
4. 查看推荐结果并添加到书架

祝使用愉快！📚
