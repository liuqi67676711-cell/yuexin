# 阅心 — 方案一：雲端部署詳細步驟（第一次部署版）

本指南假設你是**第一次**把網站部署到雲端，會盡量寫清每一步在什麼畫面、點哪裡、填什麼。

整體流程：**先部署後端（Railway）→ 拿到後端網址 → 部署前端（Vercel）→ 把前端網址填回後端 → 完成**。

---

## 一、部署前準備（在電腦上先做完）

### 1.1 程式碼已在 GitHub 上

- 若專案還沒推上 GitHub：
  1. 到 [GitHub](https://github.com) 登入，點 **New repository** 新建一個倉庫（例如取名 `yuexin`）。
  2. 在本機專案目錄打開終端，執行（把 `你的用戶名`、`yuexin` 換成你的）：
     ```bash
     git init
     git add .
     git commit -m "Initial commit"
     git branch -M main
     git remote add origin https://github.com/你的用戶名/yuexin.git
     git push -u origin main
     ```
- 若已經有倉庫，只要確認最新程式碼已 `git push` 上去即可。

### 1.2 準備後端要用的「環境變數」內容（稍後會貼到 Railway）

建議先開一個記事本，把下面要填的記下來，部署時直接複製貼上。

| 變數名 | 要填的值 | 說明 |
|--------|----------|------|
| `FRONTEND_URL` | **先留空**，等前端部署好再回來填 | 例如：`https://yuexin-xxx.vercel.app` |
| `JWT_SECRET_KEY` | 一串隨機英文+數字（至少 20 字） | 可自己亂打，例如：`my_yuexin_secret_2024_abc123xyz` |
| `DATABASE_URL` | `sqlite:///./yuexin.db` | 先用 SQLite，之後可加 Railway Volume 做持久化 |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | 向量庫目錄 |
| `DEEPSEEK_API_KEY` | 你的 DeepSeek API Key | 到 https://platform.deepseek.com 註冊並建立 API Key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | 通常不用改 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 通常不用改 |

**如何取得 DeepSeek API Key：**

1. 打開 https://platform.deepseek.com ，用手機或郵箱註冊/登入。
2. 進入控制台後，找到「API Key」或「金鑰管理」。
3. 點「創建新 Key」，複製產生的 Key（形如 `sk-xxxx...`），貼到上面的 `DEEPSEEK_API_KEY`。

**重要：** 不要把 API Key 寫進程式碼或提交到 GitHub，只填在 Railway 的環境變數裡。

### 1.3 本機先確認能跑起來（可選但建議）

在專案根目錄：

- 後端：`cd backend && pip install -r requirements.txt && 設定好 .env 後 uvicorn main:app --port 8000`
- 前端：`cd frontend && npm install && npm run build`

若本機能正常建置、後端能啟動，再部署到雲端會比較安心。

---

## 二、後端部署：Railway（第一步）

### 2.1 註冊並登入 Railway

1. 打開瀏覽器，前往 **https://railway.app**
2. 點右上角 **Login**，選擇 **Login with GitHub**
3. 授權 Railway 讀取你的 GitHub 帳號（必要，才能選倉庫部署）

### 2.2 建立新專案並從 GitHub 選倉庫

1. 登入後若在 Dashboard，點 **New Project**（或 **Create Project**）。
2. 在「如何建立專案」的選項裡，選 **Deploy from GitHub repo**（從 GitHub 倉庫部署）。
3. 若第一次使用，會要你授權 Railway 存取 GitHub 倉庫，點 **Configure GitHub App**，選擇要授權的帳號或組織，並勾選「授權存取你的 xxx 倉庫」或 **All repositories**（或至少選包含「阅心」的那個倉庫），然後 **Save**。
4. 回到 Railway，重新選 **Deploy from GitHub repo**，在列表裡選你的「阅心」專案倉庫（例如 `yuexin`），點選它。

### 2.3 把「根目錄」指到 backend

Railway 預設會用「整個倉庫根目錄」建置，但我們的後端在 `backend` 資料夾裡，所以要改根目錄：

1. 部署開始後，會出現一個 **Service**（一個方塊）。點進這個 Service。
2. 點上方的 **Settings**（設定）。
3. 在設定頁面找到 **Root Directory** 或 **Source** 區塊：
   - 若有 **Root Directory** 欄位，填：`backend`
   - 若沒有，找 **Build** 或 **Deploy** 相關設定，看是否有「Monorepo」或「Subfolder」可填 `backend`。
4. 儲存（Save）。

### 2.4 設定「建置」與「啟動」指令

仍在該 Service 的 **Settings** 裡：

1. **Build Command**（建置指令）：  
   填：`pip install -r requirements.txt`  
   （若平台有預設偵測 Python 並自動 `pip install`，可留空試試，失敗再填。）

2. **Start Command**（啟動指令）：  
   **一定要填**：  
   `uvicorn main:app --host 0.0.0.0 --port $PORT`  
   （Railway 會把 `$PORT` 換成實際的 port。）

3. **Watch Paths**（可選）：  
   若有這個欄位，可填 `backend/**`，這樣只有 `backend` 底下變動時才重新部署。

儲存。

### 2.5 新增環境變數

1. 在同一個 Service 裡，點 **Variables**（變數）分頁（或 **Environment**）。
2. 點 **New Variable** 或 **Add Variable**，一個一個加入下面這些（名稱與值照表填，不要有多餘空格）：

   | Variable Name | Value |
   |---------------|--------|
   | `FRONTEND_URL` | `https://placeholder.vercel.app`（暫時佔位，後面會改） |
   | `JWT_SECRET_KEY` | 你準備好的隨機字串 |
   | `DATABASE_URL` | `sqlite:///./yuexin.db` |
   | `CHROMA_PERSIST_DIR` | `./chroma_db` |
   | `DEEPSEEK_API_KEY` | 你的 DeepSeek Key（sk-開頭） |
   | `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` |
   | `DEEPSEEK_MODEL` | `deepseek-chat` |

3. **可選**：若希望正式環境不開 debug，可加一條：  
   - 名稱：`RUN_ENV`  
   - 值：`production`

4. 儲存。Railway 通常會自動觸發一次重新部署。

### 2.6 取得後端的「公開網址」

1. 在該 Service 的 **Settings** 裡，找到 **Networking** 或 **Domains**。
2. 點 **Generate Domain** 或 **Add Domain**，讓 Railway 產生一個網址，形如：  
   `https://xxxxxx.up.railway.app`
3. **把這個網址複製下來**，後面部署前端時會用到。  
   - 注意：網址**不要**在結尾加 `/api`，只要到 `.app` 為止，例如：`https://yuexin-api.up.railway.app`。

### 2.7 確認後端有跑起來

1. 在 Railway 的 **Deployments** 分頁看最新一次部署是否 **Success**（綠色）。
2. 用瀏覽器打開你剛複製的網址，後面加 `/health`，例如：  
   `https://xxxxxx.up.railway.app/health`  
   若看到 `{"status":"healthy"}` 或類似 JSON，代表後端已成功上線。

若部署失敗，點進該次 Deployment 看 **Logs**，常見問題：Root Directory 沒設成 `backend`、Start Command 打錯、或缺少某個環境變數。

---

## 三、前端部署：Vercel（第二步）

### 3.1 註冊並登入 Vercel

1. 打開 **https://vercel.com**
2. 點 **Sign Up** 或 **Login**，選擇 **Continue with GitHub**
3. 授權 Vercel 存取你的 GitHub

### 3.2 匯入「阅心」倉庫

1. 登入後在 Dashboard 點 **Add New…** → **Project**（或 **Import Project**）。
2. 在「Import Git Repository」列表裡選你的「阅心」倉庫（若沒出現，點 **Adjust GitHub App Permissions** 授權對應倉庫）。
3. 點倉庫右側 **Import**。

### 3.3 設定專案（建置用）

在 **Configure Project** 頁面：

1. **Project Name**：可保持預設（例如 `yuexin`）或改成你喜歡的名字。
2. **Framework Preset**：選 **Vite**（若沒自動偵測到）。
3. **Root Directory**：  
   點 **Edit**，改為 **frontend**（只部署前端的資料夾）。
4. **Build Command**：  
   填：`npm run build`（或保持預設，若預設已是 `npm run build` 就不用改）。
5. **Output Directory**：  
   填：`dist`（Vite 預設輸出目錄）。
6. **Environment Variables**（環境變數）：  
   - 名稱：`VITE_API_BASE_URL`  
   - 值：**你從 Railway 複製的後端網址**，例如 `https://xxxxxx.up.railway.app`  
   - **注意**：不要加 `/api`，不要結尾斜線，例如：✅ `https://yuexin-api.up.railway.app`，❌ `https://yuexin-api.up.railway.app/api`。

然後點 **Deploy**，等一兩分鐘。

### 3.4 取得前端的公開網址

1. 部署完成後，會顯示 **Congratulations** 或專案首頁。
2. 畫面上會有一個 **Visit** 或網址，形如：  
   `https://yuexin-xxx.vercel.app`  
   或 `https://yuexin-xxx-你的用戶名.vercel.app`。
3. **把這個網址完整複製下來**（含 `https://`），下一步要填回 Railway。

---

## 四、把前後端連起來（CORS）

後端只允許「你設定的前端網址」跨域請求，所以要把 Railway 的 `FRONTEND_URL` 改成 Vercel 的真實網址。

1. 回到 **Railway** → 你的專案 → 點進**後端那個 Service**。
2. 打開 **Variables**。
3. 找到 `FRONTEND_URL`，把值改成**你從 Vercel 複製的前端網址**，例如：  
   `https://yuexin-xxx.vercel.app`  
   結尾不要加斜線。
4. 儲存。Railway 通常會自動再部署一次；若沒有，到 **Deployments** 手動點 **Redeploy**。

等部署完成後，用瀏覽器打開**前端網址**，試試搜尋、推薦、AI 書童等功能，若都能正常發請求且沒有 CORS 錯誤，就代表前後端已正確連線。

---

## 五、部署後檢查與常見問題

### 5.1 前端能開，但搜尋/推薦/書童沒反應

- **可能原因一**：前端的 `VITE_API_BASE_URL` 填錯或沒填。  
  - **處理**：Vercel 專案 → **Settings** → **Environment Variables**，確認 `VITE_API_BASE_URL` 是後端網址（無 `/api`），改完後到 **Deployments** 點 **Redeploy**（因為 Vite 變數是建置時寫進去的，必須重新建置）。
- **可能原因二**：後端 `FRONTEND_URL` 與你實際打開的前端網址不一致（例如多了 `www`、或 http/https 不同）。  
  - **處理**：Railway 的 `FRONTEND_URL` 必須和瀏覽器網址列上的**完全一致**（含 `https://`）。

### 5.2 瀏覽器出現 CORS 錯誤

- 代表後端不允許這個「來源」跨域。  
- 確認 Railway 的 `FRONTEND_URL` 就是你打開網站時網址列上的那個網址（含 `https://`，無結尾斜線），然後在 Railway 重新部署一次。

### 5.3 Railway 部署失敗、Build 或 Start 錯誤

- 點進該次 **Deployment** → **View Logs**：
  - 若找不到 `main.py` 或 `requirements.txt`，多半是 **Root Directory** 沒設成 `backend`。
  - 若寫 `ModuleNotFoundError`，多半是依賴沒裝好，確認 **Build Command** 有 `pip install -r requirements.txt`。
  - 若寫 port 或 bind 錯誤，確認 **Start Command** 是：  
    `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 5.4 Vercel 建置失敗

- 點進該次 **Deployment** → **Building** 的 Log：
  - 若是 `npm install` 或 `npm run build` 報錯，多半是 Node 版本或依賴問題；可在專案 **Settings** → **General** 裡指定 **Node.js Version** 為 18 或 20 再重試。
  - 確認 **Root Directory** 是 `frontend`，這樣 `package.json` 才會在正確位置。

### 5.5 資料重啟後不見（Railway）

- Railway 免費方案重啟後，沒有掛 Volume 的磁碟會被清空，所以 SQLite 的 `yuexin.db` 和 `chroma_db` 可能會消失。
- 若需要持久化：
  1. 在該 Service 的 **Settings** 裡找 **Volumes**，新增一個 Volume，並掛到某個路徑，例如 `/data`。
  2. 把環境變數改成：  
     `DATABASE_URL=sqlite:////data/yuexin.db`  
     `CHROMA_PERSIST_DIR=/data/chroma_db`  
  並在應用啟動時確保 `/data` 目錄存在（或程式會自動建立）。  
  這樣重啟後資料會保留在 Volume 裡。

---

## 六、之後更新網站怎麼做

- **後端**：只要把程式碼 `git push` 到 GitHub，Railway 會自動重新部署（若已連到該倉庫）。
- **前端**：同樣 `git push` 後，Vercel 會自動重新建置並上線。  
  若你改了 **環境變數**（例如 `VITE_API_BASE_URL`），在 Vercel 改完後要到 **Deployments** 手動 **Redeploy** 一次，新的變數才會進到新建置裡。

---

## 七、快速對照表

| 步驟 | 平台 | 要做的事 |
|------|------|----------|
| 1 | GitHub | 程式碼已 push，倉庫可被 Railway / Vercel 存取 |
| 2 | Railway | New Project → Deploy from GitHub → 選 repo → Root Directory = `backend`，Start = `uvicorn main:app --host 0.0.0.0 --port $PORT`，填環境變數，Generate Domain，複製後端網址 |
| 3 | Vercel | Import 同一個 repo → Root = `frontend`，Build = `npm run build`，Output = `dist`，`VITE_API_BASE_URL` = 後端網址，Deploy，複製前端網址 |
| 4 | Railway | 把 `FRONTEND_URL` 改成前端網址，儲存並等重新部署 |
| 5 | 瀏覽器 | 打開前端網址，測試搜尋、推薦、書童 |

若某一步的畫面與上述不同（例如 Railway / Vercel 改版），以該平台當前的選項為準；關鍵是：**後端根目錄 = backend、啟動用 $PORT**，**前端根目錄 = frontend、建置時帶入 VITE_API_BASE_URL**，以及 **FRONTEND_URL 與實際前端網址一致**。

---

## 八、做完一次手動部署後，想改成一鍵部署？

專案裡已內建 **GitHub Actions** 工作流，推送到 `main` 或手動執行就會自動部署後端與前端。你只需要做**一次性設定**：把 Railway 與 Vercel 的 Token / 專案 ID 填到 GitHub 倉庫的 Secrets。  
詳細步驟請看：**[一鍵部署一次性設定](./DEPLOYMENT_ONE_CLICK_SETUP.md)**。
