# 阅心 — 公網部署指南

讓大家透過網址訪問你的「阅心」網站，大致有兩種做法：**雲端平台部署**（免伺服器）和 **自備伺服器部署**（VPS）。

---

## 架構說明

- **前端**：Vite + React，打包後為靜態檔案（`dist/`），需放在靜態託管或 Nginx 下。
- **後端**：FastAPI（uvicorn），需常駐運行，並提供 SQLite 資料庫與 Chroma 向量庫的持久化儲存。

因此部署時需要：
1. 一個地方跑**後端**（並能持久化資料）。
2. 一個地方放**前端靜態檔**，且前端的 API 請求要指到後端網址。

---

## 方案一：雲端平台部署（推薦入門）

適合不想自己管伺服器的人。常見組合：**前端 Vercel + 後端 Railway 或 Render**。

> **第一次部署？** 請直接看 **[方案一詳細步驟（第一次部署版）](./DEPLOYMENT_CLOUD_STEP_BY_STEP.md)**，從準備 GitHub、取得 API Key，到 Railway / Vercel 每一步點哪裡、填什麼都有說明。  
> **已手動部署過，想改成一推程式碼就自動部署？** 見 **[一鍵部署一次性設定](./DEPLOYMENT_ONE_CLICK_SETUP.md)**。

### 1. 後端部署（以 Railway 為例）

1. 註冊 [Railway](https://railway.app)，用 GitHub 登入。
2. 新建專案 → **Deploy from GitHub**，選擇你的「阅心」倉庫。
3. 在專案裡新增 **Service**，選擇 **GitHub Repo**，設定：
   - **Root Directory**：`backend`
   - **Build Command**：可留空或 `pip install -r requirements.txt`
   - **Start Command**：`uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Watch Paths**：`backend/**`
4. 在該 Service 的 **Variables** 裡設定環境變數（見下方「環境變數清單」），其中：
   - `FRONTEND_URL` = 你即將部署的前端網址（例如 `https://yuexin.vercel.app`）
   - `DATABASE_URL`：Railway 可選用內建 PostgreSQL，若沿用 SQLite 需注意磁碟持久化（Railway 有 Volume 可掛載目錄）
   - 若用 SQLite，可設 `DATABASE_URL=sqlite:///./yuexin.db`，並把 `yuexin.db` 和 `chroma_db` 放在同一持久化 Volume
5. 部署完成後，記下後端的公開網址，例如：`https://xxx.up.railway.app`。

> **Render** 做法類似：New → Web Service → 連 GitHub，Root 設為 `backend`，Build: `pip install -r requirements.txt`，Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`，並在 Environment 填寫相同環境變數。

### 2. 前端部署（Vercel）

1. 註冊 [Vercel](https://vercel.com)，用 GitHub 登入。
2. **Import** 你的「阅心」倉庫。
3. 設定：
   - **Framework Preset**：Vite
   - **Root Directory**：`frontend`
   - **Build Command**：`npm run build`
   - **Output Directory**：`dist`
   - **Environment Variables** 新增：
     - `VITE_API_BASE_URL` = 你的後端網址（例如 `https://xxx.up.railway.app`），**不要**在結尾加 `/api`
4. 部署完成後會得到一個網址，例如 `https://yuexin-xxx.vercel.app`。
5. 回到後端（Railway/Render）的環境變數，把 `FRONTEND_URL` 設成這個 Vercel 網址（含 `https://`），重新部署後端一次。

### 3. 後端需支援動態 Port

雲端平台會注入 `PORT`。請確認後端啟動方式使用該 port：

在 `backend/main.py` 最後若用 uvicorn 直接跑，可改為：

```python
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
```

這樣在 Railway/Render 上會自動使用正確的 port。

---

## 方案二：自備伺服器（VPS）部署

你有一台有公網 IP 的 Linux 主機（阿里雲、騰訊雲、DigitalOcean、Vultr 等）時，可以前後端都放在同一台機器上。

### 1. 環境準備

- 安裝：Python 3.10+、Node 18+、Nginx、SQLite（一般系統自帶）。
- 專案放在例如：`/var/www/yuexin`（或你家目錄），包含 `frontend` 與 `backend`。

### 2. 後端

```bash
cd /var/www/yuexin/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 編輯 .env：FRONTEND_URL=https://你的域名，JWT_SECRET_KEY 改成隨機長字串
# 若用 systemd 常駐（推薦）：
# sudo nano /etc/systemd/system/yuexin-api.service
```

`yuexin-api.service` 範例：

```ini
[Unit]
Description=Yuexin FastAPI
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/yuexin/backend
Environment="PATH=/var/www/yuexin/backend/venv/bin"
ExecStart=/var/www/yuexin/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

然後：

```bash
sudo systemctl daemon-reload
sudo systemctl enable yuexin-api
sudo systemctl start yuexin-api
```

### 3. 前端建置

在**你本機**或伺服器上：

```bash
cd /var/www/yuexin/frontend
# 建置時把 API 指到後端（替換成你的後端網址或域名）
export VITE_API_BASE_URL=https://你的域名或IP
npm ci
npm run build
```

把 `dist/` 內容放到 Nginx 要提供靜態檔的目錄，例如 `/var/www/yuexin/dist`（可把 `frontend/dist` 複製過去）。

### 4. Nginx 設定

例如站點配置 `/etc/nginx/sites-available/yuexin`：

```nginx
server {
    listen 80;
    server_name 你的域名或IP;

    root /var/www/yuexin/dist;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

啟用並重載 Nginx：

```bash
sudo ln -s /etc/nginx/sites-available/yuexin /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

若用域名，建議用 Let’s Encrypt 上 HTTPS（`certbot`），並在 Nginx 裡把 `listen 80` 改為 `listen 443 ssl` 等。

---

## 環境變數清單

### 後端（backend）

| 變數 | 說明 | 部署時注意 |
|------|------|------------|
| `FRONTEND_URL` | 前端完整網址 | 必須設成你對外的前端網址，否則 CORS 會擋 |
| `JWT_SECRET_KEY` | JWT 簽名密鑰 | **務必**改成隨機長字串，勿用預設值 |
| `DATABASE_URL` | 資料庫連線 | 雲端可沿用 `sqlite:///./yuexin.db`（需持久化目錄）或改用 PostgreSQL |
| `DEEPSEEK_API_KEY` / `OPENAI_*` | 大模型 API | 依你使用的服務填寫 |
| `CHROMA_PERSIST_DIR` | Chroma 向量庫目錄 | 需在持久化磁碟上（如 Volume 或 VPS 本機路徑） |

### 前端（frontend）

| 變數 | 說明 |
|------|------|
| `VITE_API_BASE_URL` | 後端 API 的完整網址（例如 `https://api.yourdomain.com` 或 Railway/Render 給的網址），**不要**加結尾 `/api`，前端會自己加路徑。 |

---

## 部署後檢查

1. **前端**：用瀏覽器打開網站，能正常看到首頁、搜尋等畫面。
2. **API**：在瀏覽器開發者工具 Network 裡，看請求是否都打到 `VITE_API_BASE_URL` 對應的網址，且沒有 CORS 錯誤。
3. **後端**：確認 `FRONTEND_URL` 與你實際訪問的前端網址一致（含 `https://`）。
4. **安全**：確認未把 `.env` 或 API Key 提交到公開倉庫；生產環境一定要改 `JWT_SECRET_KEY`。

---

## 其他：全部用阿里雲（ECS + OSS）

若你想**整站都放在阿里雲**：後端用 **ECS**（雲伺服器）、前端用 **OSS**（靜態網站托管）。  
**完整一步步做法**（從買 ECS、裝後端、建 OSS、上傳前端到互相填地址）：**[全部用阿里雲部署（ECS + OSS）](./DEPLOYMENT_ALIYUN_FULL.md)**。

僅前端用 OSS、後端用別家：見 **[用阿里雲 OSS 部署（前端）](./DEPLOYMENT_ALIYUN_OSS.md)**。

---

## 簡短對照

| 項目 | 方案一（雲端） | 方案二（VPS） | 前端用 OSS |
|------|----------------|----------------|
| 前端 | Vercel / Netlify / Cloudflare Pages | Nginx 託管 `dist/` | 阿里雲 OSS 靜態網站托管 |
| 後端 | Railway / Render / Fly.io | systemd + uvicorn，Nginx 反代 `/api` | 需另用 ECS / Railway 等（OSS 不能跑後端） |
| 網址 | 平台提供的子網域或自訂域名 | 自己的域名或 IP | OSS 訪問地址或自訂域名 |
| 難度 | 較低，註冊與設定環境變數即可 | 需會一點 Linux 與 Nginx | 建 Bucket、上傳、設 CORS |

若你告訴我打算用「雲端」還是「自己的 VPS」，我可以按你選的方案寫成一步步的檢查清單（含你專案裡的實際路徑與檔名）。
