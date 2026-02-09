# 阅心 — 用阿里雲對象存儲（OSS）部署說明

網上說的「用阿里雲對象存儲部署」通常是指：把**靜態網站**（HTML / JS / CSS）放到 OSS 的「靜態網站托管」上，透過網址訪問。

---

## 咱們這個項目可以這麼部署嗎？

**可以，但只能部署「前端」那一部分。**

| 部分 | 能否用 OSS 部署 | 說明 |
|------|------------------|------|
| **前端**（Vite 打包後的 `dist/`） | ✅ **可以** | 就是靜態檔案，適合放 OSS 靜態網站托管。 |
| **後端**（FastAPI + 資料庫 + 向量庫） | ❌ **不行** | OSS 只能存檔、不能跑程式。後端必須放在「能跑 Python 的環境」（如 ECS、函數計算、或繼續用 Railway）。 |

所以：

- **整站都用阿里雲**：前端 → OSS；後端 → 阿里雲 ECS（雲伺服器）。**完整步驟見：[全部用阿里雲部署（ECS + OSS）](./DEPLOYMENT_ALIYUN_FULL.md)**。
- **只把前端遷到 OSS**：前端 → OSS；後端維持在 Railway / Render 或你現在用的任何主機。

下面只講「**前端**如何部署到阿里雲 OSS」，後端你照現有方式跑（或改用 ECS），並把前端的 API 地址指到後端即可。

---

## 前端部署到 OSS 的步驟概要

### 1. 建 OSS Bucket 並開靜態網站

1. 登入 [阿里雲 OSS 控制台](https://oss.console.aliyun.com)。
2. 新建 **Bucket**（例如華東 1、外網讀寫），記住 **Bucket 名稱** 和 **地域**。
3. 在該 Bucket 的 **基礎設置** 裡，找到 **靜態頁面** / **靜態網站托管**：
   - 設為 **啟用**。
   - **默認首頁**：`index.html`。
   - **默認 404 頁**：可填 `index.html`（讓前端路由如 `/search` 由 React 處理）。

### 2. 設定 CORS（若前後端不同域）

若前端在 OSS（如 `https://xxx.oss.aliyuncs.com`），後端在別處（如 Railway），需要給該 Bucket 配 **CORS 規則**，否則瀏覽器會擋跨域請求。

在 Bucket **權限管理** → **跨域設置** 新增規則，例如：

- **來源**：`*` 或你的前端訪問地址（如 `https://你的桶.oss-region.aliyuncs.com`）。
- **允許 Methods**：`GET, POST, PUT, DELETE, HEAD`。
- **允許 Headers**：`*`。
- **暴露 Headers**：可留空或填 `*`。

（後端那邊的 CORS 也要允許這個 OSS 前端網址，例如在 Railway 的 `FRONTEND_URL` 填 OSS 靜態網站訪問地址。）

### 3. 本機建置前端並上傳 dist

在專案目錄：

```bash
cd frontend
# 把後端地址換成你實際的後端網址（不要結尾 /api）
export VITE_API_BASE_URL=https://你的後端地址
npm ci
npm run build
```

會得到 `frontend/dist/` 目錄。把 **dist 目錄裡的所有檔案**（含 `index.html`、`assets/` 等）上傳到 OSS Bucket **根目錄**（或你指定的前綴目錄）。

上傳方式任選其一：

- **控制台**：OSS 控制台 → 該 Bucket → **文件管理** → **上傳文件**，選 dist 內所有檔案。
- **命令行工具 ossutil**：  
  `ossutil cp -r dist/ oss://你的Bucket名稱/`  
  （需先配置 ossutil 的 endpoint、AccessKey。）

### 4. 訪問地址

- 若開了靜態網站托管，訪問地址一般是：  
  `https://你的Bucket名稱.oss-地域.aliyuncs.com`  
  或你在 Bucket 裡看到的「靜態網站訪問」地址。
- 也可在 **傳輸管理** 裡綁定**自訂域名**（需備案），用你自己的域名訪問。

### 5. 前端要改的配置

- **建置時**：`VITE_API_BASE_URL` 設成你的**後端對外地址**（例如 `https://xxx.up.railway.app` 或 `https://api.你的域名.com`），**不要**加 `/api`。
- **後端**：把 CORS 的 `FRONTEND_URL` 設成你的 **OSS 靜態網站訪問地址**（或自訂域名），和瀏覽器實際打開的網址一致。

---

## 後端放哪裡？

OSS 不能跑後端，可以選：

| 方式 | 說明 |
|------|------|
| **繼續用 Railway / Render** | 不改後端部署，只把前端遷到 OSS；前端的 `VITE_API_BASE_URL` 指到現有後端，後端 `FRONTEND_URL` 改為 OSS 地址。 |
| **阿里雲 ECS** | 買一臺雲主機，裝 Python、跑 uvicorn，用 Nginx 反代；和現有「自備伺服器」部署方式一樣，見 [DEPLOYMENT.md 方案二](./DEPLOYMENT.md)。 |
| **阿里雲函數計算 FC** | 把 FastAPI 包成 HTTP 函數跑在 FC 上，需要改一點部署方式，相對進階。 |

---

## 小結

- **可以**用阿里雲對象存儲部署「阅心」的**前端**：建 Bucket、開靜態網站托管、上傳 `frontend/dist/`、設 CORS、建置時填好 `VITE_API_BASE_URL`。
- **後端**不能放 OSS，要放在能執行 Python 的服務（如 Railway、ECS、FC 等）。
- 若你希望，我可以再寫一版「僅前端 OSS + 後端 Railway」的逐步清單（含 ossutil 或控制台上傳的具體步驟）。
