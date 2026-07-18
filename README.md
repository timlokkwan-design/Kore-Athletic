# 田徑隊訓練管理 App

以 Python + Streamlit 建立的田徑隊訓練管理網頁，支援學生記錄訓練數據與教練查看總覽圖表。

## 正式上線

1. 關閉 Streamlit 後，雙擊 **`正式上線重置.bat`**
2. 輸入 `YES` 確認 — 會自動備份 `data/` 至 `data/backups/`，並清除測試資料
3. 雙擊 **`start.bat`** 啟動，用教練帳號登入並修改密碼
4. 在教練平台建立新賽季課表；於「系統設定 → 網站內容」確認訪客專區文案

正式模式會建立 `data/.production` 標記，不再自動產生測試學員及假課表。

教練忘記密碼：雙擊 **`重設教練密碼.bat`**

## 免費放上線（給學生固定網址）

使用 **Streamlit Community Cloud**（完全免費）→ 詳見 **[上線指南.md](上線指南.md)**

簡述：GitHub 上傳程式 → share.streamlit.io 部署 → 得到 `https://你的名稱.streamlit.app`

**建議：** 再加 [Supabase 免費雲端資料庫](設定Supabase.md)，重新部署時資料不會遺失。

## 測試帳號（僅開發模式，未執行正式重置時）

| 角色 | 帳號 | 密碼 |
|------|------|------|
| 教練 | ktll | 170330 |
| 學生 | student1 | 123 |
| 家長 | parent1 | 123 |

## 功能

### 登入與三角色
- 教練 / 學生 / 家長分開介面
- 登入前顯示 KORE ATHLETIC 歡迎頁

### 訓練看板（全角色共用）
- 今日課表、訓練階段、週主題、校際賽倒數
- 教練提示、訓練規格、回報完成率

### 學生端
- 訓練日誌（趟數、秒數、RPE、時長、Foster 負荷）
- 健康問卷（睡眠 / 酸痛 / 心情）
- 個人 ACWR 狀態與休息建議

### 教練端
- 週期化課表編輯（類型、組數、距離、複製日期）
- 全局階段 / 週主題 / 比賽倒數日
- WhatsApp 課表複製
- 數據總覽圖表
- 團隊 ACWR + 健康預警儀表板

### 家長端
- 唯讀查看子女訓練摘要、ACWR、近期記錄

## 專案結構

```
track-training-app/
├── app.py                  # 主程式入口
├── requirements.txt
├── data/                   # CSV 數據（自動產生）
│   ├── training_logs.csv
│   └── training_menus.csv
├── utils/
│   ├── config.py           # 品牌、訓練類型、設定
│   ├── data_store.py       # CSV 讀寫
│   ├── auth.py             # 登入驗證
│   └── acwr.py             # ACWR / Foster 負荷
└── views/
    ├── auth_view.py        # 登入頁
    ├── student_view.py     # 學生端
    ├── coach_view.py       # 教練端
    ├── parent_view.py      # 家長端
    └── components/
        └── board.py        # 訓練看板
```

## 安裝與執行

```bash
cd track-training-app
pip install -r requirements.txt
streamlit run app.py
```

瀏覽器會自動開啟 `http://localhost:8501`。

## 數據存儲

- 所有資料存於 `data/` 目錄（CSV + 頭像 + 網站文案）
- **開發模式**：首次啟動會自動建立範例數據
- **正式模式**（`data/.production` 存在）：只保留教練帳號，不建立測試資料
