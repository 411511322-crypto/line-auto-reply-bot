# LINE Bot 自動回覆程式 (LINE Auto-Reply Bot)

這是一個使用 Python (Flask + official `line-bot-sdk` v3) 打造的 LINE 自動回覆機器人專案。支援關鍵字匹配自動回覆、常見問題選單以及預設提示訊息，結構完整並已配置 `.gitignore`，可安全上傳至 GitHub。

---

## 目錄結構

```text
line-auto-reply-bot/
├── app.py              # 主程式 (處理 Webhook 與自動回覆邏輯)
├── requirements.txt    # 專案相依套件清單
├── .env.example        # 環境變數設定範本
├── .gitignore          # Git 忽略清單 (保護金鑰不上傳)
└── README.md           # 專案說明與部署指南
```

---

## 一、前置作業：申請 LINE Messaging API

1. 前往 [LINE Developers Console](https://developers.line.biz/) 並使用你的 LINE 帳號登入。
2. 建立一個 **Provider**（提供者，例如：你的名字或品牌名）。
3. 在 Provider 底下點擊 **Create a new channel**，選擇 **Messaging API**。
4. 填寫頻道基本資料（Channel name, Channel description, Category 等）並完成建立。
5. 進入該 Channel 頁面，取得以下兩項機密金鑰：
   * **Channel Secret**：位於 `Basic settings` 分頁最下方。
   * **Channel Access Token**：位於 `Messaging API` 分頁最下方，點擊 **Issue** 生成（長期權杖）。
6. 在 `Messaging API` 分頁將 **Auto-reply messages**（自動回應訊息）設定為 **Disabled**（避免 LINE 官方內建的預設罐頭訊息與程式衝突）。

---

## 二、本地執行與測試

### 1. 複製專案並安裝套件
建議使用虛擬環境：
```bash
# 建立虛擬環境
python -m venv .venv

# 啟動虛擬環境 (Windows PowerShell)
.venv\Scripts\Activate.ps1

# 安裝相依套件
pip install -r requirements.txt
```

### 2. 設定環境變數
將 `.env.example` 複製一份並命名為 `.env`：
```bash
cp .env.example .env
```
用文字編輯器開啟 `.env`，填入你的 LINE 金鑰：
```env
LINE_CHANNEL_ACCESS_TOKEN=你的Channel_Access_Token
LINE_CHANNEL_SECRET=你的Channel_Secret
PORT=5000
```

### 3. 啟動伺服器
```bash
python app.py
```
伺服器將在 `http://127.0.0.1:5000` 啟動。

### 4. 使用 ngrok 進行本地測試 (穿透內網)
LINE Webhook 必須使用 HTTPS 網址。你可以使用 [ngrok](https://ngrok.com/) 將本機端口對外公開：
```bash
ngrok http 5000
```
你會得到一個類似 `https://xxxx-xx-xx.ngrok-free.app` 的 HTTPS 網址。

### 5. 設定 LINE Webhook
1. 回到 LINE Developers Console 的 **Messaging API** 分頁。
2. 找到 **Webhook URL**，填入你的 ngrok 網址加上 `/callback`，例如：
   ```text
   https://xxxx-xx-xx.ngrok-free.app/callback
   ```
3. 點擊 **Update**，接著點擊 **Verify** 測試連線（顯示 Success 即代表正常）。
4. 開啟 **Use webhook** 開關。
5. 掃描該頁面的 QR Code 加入好友，開始傳送訊息測試！

---

## 三、部署至免費雲端平台 (例如 Render)

若希望機器人 24 小時不間斷運作，可部署至 [Render](https://render.com/)：

1. 將專案推送到你的 GitHub Repository。
2. 註冊並登入 Render，點擊 **New +** → **Web Service**。
3. 連接剛建立的 GitHub 倉庫。
4. 設定設定值：
   * **Runtime**：`Python 3`
   * **Build Command**：`pip install -r requirements.txt`
   * **Start Command**：`gunicorn app:app`
5. 在 **Environment Variables** 新增兩組環境變數：
   * `LINE_CHANNEL_ACCESS_TOKEN` = 你的 Channel Access Token
   * `LINE_CHANNEL_SECRET` = 你的 Channel Secret
6. 部署完成後，Render 會提供一組網址（如 `https://your-bot.onrender.com`）。
7. 將 LINE Developers 後台的 Webhook URL 修改為：
   `https://your-bot.onrender.com/callback`

---

## 四、上傳至 GitHub 的完整步驟

> ⚠️ **重要提醒**：請務必確認 `.env` 檔案**沒有**被加入 Git。本專案已在 `.gitignore` 中排除 `.env`，切勿將含有真實 Token 的檔案 commit。

在專案目錄下執行以下指令：

```bash
# 1. 初始化 Git 倉庫
git init

# 2. 將所有檔案加入暫存區 (會自動忽略 .env 和 .venv)
git add .

# 3. 檢查加入的檔案（確認沒有 .env）
git status

# 4. 提交第一次 commit
git commit -m "feat: initial commit for LINE auto reply bot"

# 5. 將預設分支命名為 main
git branch -M main

# 6. 關聯到你在 GitHub 建立的遠端倉庫 (請將網址替換為你的倉庫網址)
git remote add origin https://github.com/你的用戶名/你的倉庫名稱.git

# 7. 推送至 GitHub
git push -u origin main
```
