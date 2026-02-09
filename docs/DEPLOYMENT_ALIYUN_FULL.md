# 阅心 — 全部用阿里雲部署（ECS + OSS）完整步驟

本指南說明如何把「阅心」**後端**放在阿里雲 **ECS**（雲伺服器）、**前端**放在阿里雲 **OSS**（對象存儲），整站都跑在阿里雲上。

**架構：**

- **後端**：ECS 上一台 Linux 主機跑 FastAPI（uvicorn），用 Nginx 把 80 端口的 `/api` 轉發到後端。
- **前端**：本機建置出 `dist/`，上傳到 OSS Bucket 的靜態網站托管，用戶透過 OSS 的網址訪問。
- **前後端連線**：前端建置時填後端地址（ECS 公網 IP 或域名）；後端 CORS 填前端地址（OSS 靜態網站網址）。

建議順序：**先做後端 ECS → 再做 OSS 前端 → 最後把兩邊地址互相填好**。

---

## 一、部署前準備（本機）

- 已註冊 [阿里雲](https://www.aliyun.com)，並完成實名認證。
- 本機能 SSH（終端或 PuTTY），且專案程式碼已能正常跑（可選，但建議先在本機跑通）。
- 準備好 **DeepSeek API Key**（後端要填），見 [方案一詳細步驟](./DEPLOYMENT_CLOUD_STEP_BY_STEP.md) 裡的「取得 DeepSeek API Key」。
- 想好一組 **JWT 密鑰**（隨機英文+數字，至少約 20 字），例如：`my_yuexin_secret_2024_xyz`。

---

## 二、購買並初始化 ECS（後端用）

### 2.1 創建 ECS 實例

1. 登入 [阿里雲 ECS 控制台](https://ecs.console.aliyun.com)。
2. 點 **創建實例**（或 **實例與鏡像 → 實例** 再創建）。
3. 主要選項建議：
   - **付費模式**：按量付費 或 包年包月（依你需求）。
   - **地域**：選離你用戶近的（如華東1）。
   - **鏡像**：**Ubuntu 22.04 64位**。
   - **規格**：入門可用 **1 核 2 GiB**（如 ecs.t6-c1m2.large），之後可升配。
   - **儲存**：系統盤 40GB 一般夠用。
   - **網路**：分配公網 IP（方便用 IP 訪問後端；若之後綁域名可再改）。
   - **登錄憑證**：選 **密鑰對** 並新建或選擇已有密鑰（建議），或選密碼登錄。
4. **安全組**：新建或選已有，**入方向** 要放行：
   - **22**（SSH）
   - **80**（HTTP，給 Nginx 用）
   - 若之後用 HTTPS，再放行 **443**。
5. 完成創建，記下 **公網 IP**（後面當作後端地址用）。

### 2.2 登錄 ECS

在終端（密鑰登錄，把 `你的密鑰.pem` 和 `公網IP` 換成實際值）：

```bash
chmod 400 你的密鑰.pem
ssh -i 你的密鑰.pem root@公網IP
```

密碼登錄則：`ssh root@公網IP`，輸入密碼。

---

## 三、在 ECS 上部署後端

以下命令都在 **ECS 上** 執行（已 SSH 登入）。

### 3.1 安裝 Python 3.10+ 與 Nginx

```bash
apt update && apt install -y python3 python3-pip python3-venv nginx git
```

確認版本：

```bash
python3 --version   # 建議 3.10 或以上
```

### 3.2 上傳或克隆專案到 ECS

**方式 A：用 Git（推薦，倉庫在 GitHub 等）**

```bash
cd /opt
git clone https://github.com/你的用戶名/阅心倉庫名.git yuexin
# 若倉庫是私有的，需在 ECS 上配置 SSH key 或 token
```

**方式 B：本機用 scp 上傳**

在本機執行（在專案根目錄）：

```bash
scp -i 你的密鑰.pem -r /Users/sixsevensconsubine/Desktop/阅心 root@公網IP:/opt/yuexin
```

然後在 ECS 上確認目錄存在：`ls /opt/yuexin`，應有 `backend`、`frontend` 等。

### 3.3 後端虛擬環境與依賴

```bash
cd /opt/yuexin/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3.4 後端環境變數 .env

```bash
cp .env.example .env
nano .env
```

在 `.env` 裡填寫或修改（把下面值換成你的）：

```env
# 大模型（必填一組，建議 DeepSeek）
DEEPSEEK_API_KEY=你的DeepSeek的Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 安全（必改）
JWT_SECRET_KEY=你準備好的隨機長字串

# 資料庫與向量庫（用預設即可）
DATABASE_URL=sqlite:///./yuexin.db
CHROMA_PERSIST_DIR=./chroma_db

# CORS：先填 OSS 靜態網站地址（見第五步），例如：
# FRONTEND_URL=http://你的Bucket名稱.oss-地域.aliyuncs.com
# 若 OSS 是 https，就寫 https://...
FRONTEND_URL=http://placeholder.oss-cn-hangzhou.aliyuncs.com
```

**先隨便寫一個 FRONTEND_URL**（如上面 placeholder），等 OSS 建好後再回來改成真實 OSS 地址並重啟後端。儲存退出（nano：Ctrl+O 回車，Ctrl+X）。

### 3.5 用 systemd 常駐後端

```bash
sudo nano /etc/systemd/system/yuexin-api.service
```

寫入（路徑若是別處請改 `/opt/yuexin/backend`）：

```ini
[Unit]
Description=Yuexin FastAPI Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/yuexin/backend
Environment="PATH=/opt/yuexin/backend/venv/bin"
ExecStart=/opt/yuexin/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

啟用並啟動：

```bash
sudo systemctl daemon-reload
sudo systemctl enable yuexin-api
sudo systemctl start yuexin-api
sudo systemctl status yuexin-api
```

看到 `active (running)` 即可。本機測一下：

```bash
curl http://127.0.0.1:8000/health
```

應返回 `{"status":"healthy"}`。

### 3.6 Nginx 反代：80 端口轉到後端 8000

只暴露 80，把 `/api` 轉給後端：

```bash
sudo nano /etc/nginx/sites-available/yuexin-api
```

寫入（`server_name` 可先寫 ECS 公網 IP 或 `_`）：

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
```

啟用並重載：

```bash
sudo ln -sf /etc/nginx/sites-available/yuexin-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

在**本機**瀏覽器或終端測試（把 `ECS公網IP` 換成實際 IP）：

```text
http://ECS公網IP/api/health
```

應返回 `{"status":"healthy"}`。**後端地址**就是：`http://ECS公網IP`（不要加 `/api`，前端會自己加路徑）。

---

## 四、初始化後端資料（可選，若需要書目與向量）

若專案需要預先導入書籍、向量庫，在 ECS 上：

```bash
cd /opt/yuexin/backend
source venv/bin/activate
# 若有 init_books 等腳本，依專案說明執行，例如：
# python scripts/init_books.py
```

沒有腳本可略過，後端 API 能跑即可。

---

## 五、建立 OSS Bucket 並開靜態網站（前端）

### 5.1 創建 Bucket

1. 打開 [OSS 控制台](https://oss.console.aliyun.com)。
2. **創建 Bucket**：
   - **Bucket 名稱**：自訂（如 `yuexin-web`），全域唯一。
   - **地域**：建議與 ECS 同地域（如華東1）。
   - **存儲類型**：標準。
   - **讀寫權限**：**公共讀**（靜態網站要對外讀）。
3. 創建完成後記住 **Bucket 名稱** 和 **地域**（如 `oss-cn-hangzhou`）。

### 5.2 開啟靜態網站托管

1. 點進該 Bucket → **基礎設置**。
2. 找到 **靜態頁面** / **靜態網站托管**，點 **設置**：
   - **托管類型**：靜態網站托管。
   - **默認首頁**：`index.html`。
   - **默認 404 頁**：`index.html`（方便前端路由）。
3. 保存。

### 5.3 記下靜態網站訪問地址

在 **基礎設置** 或 **概覽** 裡會有一項 **靜態網站訪問** 或 **Bucket 外網訪問** 地址，形如：

- `http://你的Bucket名稱.oss-地域.aliyuncs.com`  
或  
- `https://你的Bucket名稱.oss-地域.aliyuncs.com`

**把這個地址完整記下來**，後面要填到後端 `FRONTEND_URL`，以及建置前端時若需 CORS 會用到。

### 5.4 設置 CORS（前後端不同域必做）

1. 在該 Bucket → **權限管理** → **跨域設置**。
2. **創建規則**：
   - **來源**：`*` 或填 `http://你的Bucket名.oss-地域.aliyuncs.com`、`https://...`（與上面靜態網站地址一致）。
   - **允許 Methods**：GET, POST, PUT, DELETE, HEAD。
   - **允許 Headers**：`*`。
   - **暴露 Headers**：可留空或 `*`。
3. 保存。

---

## 六、本機建置前端並上傳到 OSS

在**你本機**（Mac/Windows）專案目錄操作。

### 6.1 建置前端

把 `後端地址` 換成 ECS 的訪問地址（即 `http://ECS公網IP`，不要加 `/api`）：

```bash
cd frontend
export VITE_API_BASE_URL=http://你的ECS公網IP
npm ci
npm run build
```

會生成 `frontend/dist/`。

### 6.2 上傳 dist 到 OSS

**方式 A：控制台上傳**

1. OSS 控制台 → 你的 Bucket → **文件管理**。
2. 進入根目錄（或你要放的目錄）。
3. **上傳文件**，選擇 `dist` 目錄下的**所有檔案**（含 `index.html` 和 `assets/` 裡的全部），上傳。

**方式 B：ossutil 命令行**

1. 下載並配置 [ossutil](https://help.aliyun.com/document_detail/120075.html)。
2. 在專案目錄執行（把 `你的Bucket名`、`地域` 換成實際值）：

```bash
ossutil cp -r frontend/dist/ oss://你的Bucket名/ --update
```

### 6.3 驗證前端

用瀏覽器打開你在 5.3 記下的 **靜態網站訪問地址**，應能看到阅心首頁。若打不開，檢查 Bucket 是否為「公共讀」、靜態網站是否啟用、默認首頁是否為 `index.html`。

---

## 七、把前後端連起來（CORS）

1. 回到 **ECS**，編輯後端 `.env`：
   ```bash
   nano /opt/yuexin/backend/.env
   ```
2. 把 **FRONTEND_URL** 改成你在 5.3 記下的 **OSS 靜態網站訪問地址**（與瀏覽器打開前端的網址完全一致，含 `http://` 或 `https://`，結尾不要斜線），例如：
   ```env
   FRONTEND_URL=http://yuexin-web.oss-cn-hangzhou.aliyuncs.com
   ```
3. 儲存後重啟後端：
   ```bash
   sudo systemctl restart yuexin-api
   ```

再從瀏覽器打開 OSS 前端地址，試試搜尋、推薦、AI 書童等功能；若之前有 CORS 錯誤，此時應消失。

---

## 八、可選：自訂域名與 HTTPS

- **ECS 後端**：若有域名，可在 ECS 綁定域名，並在 Nginx 裡配 `server_name 你的域名`；HTTPS 可用阿里雲免費 SSL 證書 + Nginx 配置 `listen 443 ssl`。
- **OSS 前端**：在 Bucket **傳輸管理** 裡綁定自訂域名（域名需備案），並在 OSS 或 CDN 開啟 HTTPS。

改完域名後，記得：
- 前端重新建置時把 `VITE_API_BASE_URL` 改成後端域名（如 `https://api.你的域名.com`）。
- 後端 `.env` 的 `FRONTEND_URL` 改成前端域名（如 `https://www.你的域名.com`），並重啟 `yuexin-api`。

---

## 九、流程與檢查清單速覽

| 步驟 | 做什麼 |
|------|--------|
| 1 | 買 ECS（Ubuntu 22.04），安全組放行 22、80 |
| 2 | SSH 登入 ECS，裝 Python3、Nginx，上傳/克隆專案到 `/opt/yuexin` |
| 3 | `backend` 下建 venv、裝依賴、配 `.env`（含 DEEPSEEK、JWT、暫時的 FRONTEND_URL） |
| 4 | systemd 跑 uvicorn（127.0.0.1:8000），Nginx 把 80 的 `/api` 反代到 8000 |
| 5 | 建 OSS Bucket，開靜態網站托管，設 CORS，記下靜態網站訪問地址 |
| 6 | 本機建置前端（VITE_API_BASE_URL=http://ECS公網IP），上傳 dist 到 OSS |
| 7 | 把後端 `.env` 的 FRONTEND_URL 改成 OSS 地址，重啟後端 |

完成後：用戶訪問 **OSS 靜態網站地址** 使用前端，前端會請求 **http://ECS公網IP/api/...** 作為後端 API。

若某一步報錯，可根據錯誤信息對照：後端看 `sudo journalctl -u yuexin-api -f`，Nginx 看 `sudo nginx -t` 和 `/var/log/nginx/error.log`，前端看瀏覽器開發者工具 Network 與 Console。
