# 田徑隊訓練管理 App

以 Python + Streamlit 建立的田徑隊訓練管理網頁，支援學生記錄訓練數據與教練查看總覽圖表。

## 功能

### 學生端
- 查看今日訓練菜單（項目、趟數、目標秒數）
- 提交每趟的實際秒數、RPE 自覺強度（1–10）、傷病不適部位
- 查看自己的今日記錄

### 教練端
- 所有學生數據總覽（人數、趟數、平均差距、不適回報）
- 目標 vs 實際秒數圖表（依學生平均、依趟數、RPE 分布）
- 完整記錄表與傷病提醒

## 專案結構

```
track-training-app/
├── app.py                  # 主程式入口
├── requirements.txt
├── data/                   # CSV 數據（自動產生）
│   ├── training_logs.csv
│   └── training_menus.csv
├── utils/
│   ├── config.py           # 訓練菜單與設定
│   └── data_store.py       # CSV 讀寫
└── views/
    ├── student_view.py     # 學生端介面
    └── coach_view.py       # 教練端介面
```

## 安裝與執行

```bash
cd track-training-app
pip install -r requirements.txt
streamlit run app.py
```

瀏覽器會自動開啟 `http://localhost:8501`。

## 數據存儲

- 所有訓練記錄存於 `data/training_logs.csv`
- 訓練菜單存於 `data/training_menus.csv`
- 首次啟動會自動建立範例數據，方便測試教練端圖表

若要修改今日菜單，可編輯 `utils/config.py` 中的 `DEFAULT_MENU`，或直接修改 `data/training_menus.csv`。
