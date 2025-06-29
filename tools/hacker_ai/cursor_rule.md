# HackerAI 項目結構規範

## 資料夾結構說明

### 核心資料夾
- **models/** -- 存放所有AI模型檔案（訓練完成的模型、修復後的模型等）
- **datasets/** -- 存放訓練數據和測試數據集
- **configs/** -- 存放配置檔案（訓練參數、模型配置等）
- **hacker_AI_loader/** -- 模型載入器和相關工具類

### 腳本資料夾
- **scripts/training/** -- 訓練相關腳本（安全訓練、原始訓練等）
- **scripts/testing/** -- 測試相關腳本（模型測試、功能驗證等）
- **scripts/diagnosis/** -- 診斷相關腳本（NaN檢測、模型修復等）
- **scripts/utils/** -- 工具腳本（清理、轉換、輔助功能等）

### 文檔資料夾
- **docs/** -- 項目文檔和說明
- **docs/reports/** -- 修復報告、測試報告等技術文檔

### 系統資料夾
- **logs/** -- 日誌檔案（訓練日誌、錯誤日誌等）
- **venv/** -- Python虛擬環境
- **__pycache__/** -- Python快取檔案
- **.vscode/** -- VSCode配置檔案
- **.cursor/** -- Cursor編輯器配置檔案
- **requirements/** -- 依賴管理檔案

### GUI相關
- **hacker_ai_gui/** -- 圖形使用者介面相關檔案

## 檔案放置規則

### ✅ 正確放置
- 訓練腳本 → `scripts/training/`
- 測試腳本 → `scripts/testing/`
- 修復工具 → `scripts/diagnosis/`
- 配置檔案 → `configs/`
- 模型檔案 → `models/`
- 數據集 → `datasets/`
- 報告文檔 → `docs/reports/`

### ❌ 避免放置
- 不要在根目錄放置功能性腳本
- 不要在根目錄放置報告文檔
- 不要混合不同類型的檔案在同一資料夾

## 命名規範

### 腳本命名
- 訓練腳本：`train_*.py` 或 `*_train.py`
- 測試腳本：`test_*.py`
- 修復工具：`fix_*.py`
- 診斷工具：`diagnose_*.py`

### 模型命名
- 原始模型：`hacker_ai_trained/`
- 修復模型：`hacker_ai_fixed/`
- 重訓模型：`hacker_ai_retrained/`

### 配置檔案
- 安全配置：`*_safe.json`
- 一般配置：`*.json`

## 維護原則

1. **單一職責**：每個資料夾只存放特定類型的檔案
2. **清晰分類**：按功能而非時間順序組織檔案
3. **易於查找**：使用描述性的資料夾和檔案名稱
4. **版本控制**：重要檔案使用版本後綴（如 `_v1`, `_v2`）

## 新增檔案指南

在添加新檔案時，請參考以下決策樹：

```
新檔案 → 
├── 是腳本？ → 
│   ├── 訓練相關？ → scripts/training/
│   ├── 測試相關？ → scripts/testing/
│   ├── 診斷相關？ → scripts/diagnosis/
│   └── 工具相關？ → scripts/utils/
├── 是模型？ → models/
├── 是數據？ → datasets/
├── 是配置？ → configs/
├── 是文檔？ → docs/ 或 docs/reports/
└── 是日誌？ → logs/
```

