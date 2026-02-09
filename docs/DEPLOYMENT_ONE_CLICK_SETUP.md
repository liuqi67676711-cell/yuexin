# 一鍵部署 — 一次性設定說明

完成下面**一次性設定**後，之後你只要：

- **推送到 `main` 分支**，或  
- 到 GitHub 倉庫的 **Actions** 頁面點 **Run workflow**  

就會自動把後端部署到 Railway、前端部署到 Vercel，不用再手動到兩個平台點部署。

---

## 前提：已經用「手動」方式部署過一次

一鍵部署的流程是**沿用你已經建好的 Railway 專案和 Vercel 專案**，所以請先照 **[方案一詳細步驟](./DEPLOYMENT_CLOUD_STEP_BY_STEP.md)** 做完一遍，確認：

- Railway 上有一個「阅心」後端專案，且能正常運行、已產生網址（例如 `https://xxx.up.railway.app`）。
- Vercel 上有一個「阅心」前端專案，且已設定 Root Directory = `frontend`、環境變數 `VITE_API_BASE_URL` = 後端網址、能正常打開。
- Railway 的 `FRONTEND_URL` 已設成你的 Vercel 網址。

做完這些之後，再來做下面「取得 Token / ID 並填到 GitHub」即可啟用一鍵部署。

---

## 一、取得 Railway 的 Project Token

1. 打開 **https://railway.app** 並登入，進入你的「阅心」**專案**（不是某一個 Service，是整個專案）。
2. 點左側或上方的 **Settings**（專案設定），找到 **Tokens** 或 **Project Tokens**。
3. 點 **Create Token** 或 **New Token**，名稱可填 `github-actions`。
4. 建立後會顯示一組 **Token**（只會顯示一次），**立刻複製**下來，等一下要貼到 GitHub Secrets。
5. 在 GitHub 倉庫使用方式：
   - 打開你的 **阅心** 倉庫 → **Settings** → **Secrets and variables** → **Actions**。
   - 點 **New repository secret**，名稱填 **`RAILWAY_TOKEN`**，值貼上剛複製的 Token，儲存。

> 若畫面上只有「Deploy」或「API」相關的 Token，請選**專案層級**的 Token（Project Token），不要用個人帳號的 API Token，否則可能出現 "Project Token Not Found"。

---

## 二、取得 Vercel 的 Token、Org ID、Project ID

### 2.1 Access Token（VERCEL_TOKEN）

1. 打開 **https://vercel.com/account/tokens** 並登入。
2. 點 **Create Token**，名稱可填 `github-actions`，權限用預設即可。
3. 建立後複製 Token，只會顯示一次。
4. 在 GitHub 倉庫：**Settings** → **Secrets and variables** → **Actions** → **New repository secret**，名稱 **`VERCEL_TOKEN`**，值貼上 Token。

### 2.2 Org ID 與 Project ID（VERCEL_ORG_ID、VERCEL_PROJECT_ID）

1. 打開 **https://vercel.com**，進入你的「阅心」**前端專案**（不是團隊列表）。
2. 點上方 **Settings**。
3. 在 **General** 頁面下方可看到 **Project ID**（一組字串），複製下來。
4. **Org ID** 取得方式之一：
   - 在 Vercel 儀表板左側選你的 **Team / 個人帳號**，打開 **Settings**，在 **General** 裡可看到 **Team ID** 或 **Organization ID**，即為 Org ID。  
   - 或：在專案目錄本機執行一次 `vercel link` 後，打開 `frontend/.vercel/project.json`，裡面的 `orgId` 就是 **VERCEL_ORG_ID**，`projectId` 就是 **VERCEL_PROJECT_ID**。
5. 在 GitHub 倉庫新增兩個 Secrets：
   - 名稱 **`VERCEL_ORG_ID`**，值貼上 Org ID（或 Team ID）。
   - 名稱 **`VERCEL_PROJECT_ID`**，值貼上 Project ID。

---

## 三、確認 GitHub Secrets 清單

在 **Settings** → **Secrets and variables** → **Actions** 裡，應至少有以下三個（一鍵部署只會用這三個）：

| Secret 名稱        | 說明           | 從哪裡取得 |
|--------------------|----------------|------------|
| `RAILWAY_TOKEN`    | Railway 專案 Token | Railway 專案 → Settings → Tokens → Create |
| `VERCEL_TOKEN`     | Vercel 帳號 Token  | https://vercel.com/account/tokens |
| `VERCEL_ORG_ID`    | Vercel 團隊/帳號 ID | Team/Account Settings 或 `.vercel/project.json` 的 `orgId` |
| `VERCEL_PROJECT_ID`| Vercel 前端專案 ID | 該專案 Settings → General → Project ID |

儲存後，**不要**再從介面編輯 Secret 看內容（會看不到），只要確認名稱正確即可。

---

## 四、之後怎麼「一鍵」部署

- **方式一**：在本地改完程式後執行  
  `git add . && git commit -m "更新說明" && git push origin main`  
  推送到 `main` 後，GitHub Actions 會自動跑「Deploy 阅心」工作流，部署後端與前端。

- **方式二**：不推程式碼，只想重新部署一次時——  
  打開倉庫的 **Actions** 分頁 → 左側選 **Deploy 阅心** → 右側點 **Run workflow** → 選分支 **main** → **Run workflow**。  
  跑完後就會是最新一次從 `main` 建置的結果。

---

## 五、若部署失敗

- 到 GitHub 倉庫 **Actions** 頁面，點進最近一次 **Deploy 阅心** 的執行，看是哪一個 **Job** 失敗（部署後端 / 部署前端）。
- 點進該 Job 看 **Log**：
  - **Railway**：若出現 "Project Token Not Found" 或權限錯誤，多半是用了個人 API Token 而不是專案 Token；請回 Railway 專案 **Settings → Tokens** 重新建立 **Project Token**，並更新 GitHub Secret `RAILWAY_TOKEN`。
  - **Vercel**：若出現 org/project 錯誤，請確認 `VERCEL_ORG_ID`、`VERCEL_PROJECT_ID` 是從「該前端專案」與其團隊/帳號取得的；若你曾刪除專案重建，需要重新複製 Project ID 並更新 Secret。
- 若前端建置時報錯缺少 `VITE_API_BASE_URL`，請在 **Vercel 專案**的 **Settings → Environment Variables** 裡加上 `VITE_API_BASE_URL` = 你的後端網址（與手動部署時相同），然後在 GitHub 再跑一次 workflow（或推一次程式碼）。

完成以上設定後，一鍵部署就會生效；之後只要 push 或手動 Run workflow 即可自動部署。
