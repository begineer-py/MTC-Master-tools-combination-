# C2 網絡安全測試平台

## 項目簡介

這是一個功能強大的本地C2（Command & Control）網絡安全測試平台，專為安全研究人員和滲透測試人員設計。平台提供了完整的網絡偵察、漏洞掃描和安全測試功能，讓任何想要進行安全測試的人都能輕鬆上手。

## 主要功能

### 🔍 前端偵察功能
- **nmap**: 網絡端口掃描
- **webtech**: Web技術識別
- **paramspider**: 參數爬取
- **crtsh**: 證書透明度日誌查詢
- **cloudflare_pass**: Cloudflare繞過（基於paramspider）

### 🛡️ 安全掃描模塊
- 漏洞掃描和檢測
- 網絡服務識別
- 安全配置檢查
- 自動化滲透測試

### 🎯 目標管理
- 簡化的目標添加和管理
- 無需用戶認證，直接訪問
- 掃描結果統一管理

## 快速開始

### 系統要求
- Python 3.8+
- Docker（可選，用於某些功能）
- Linux/Windows/macOS

### 安裝步驟

#### Linux 系統
```bash
# 克隆項目
git clone <repository-url>
cd C2

# 運行自動安裝腳本
chmod +x requirements/install_dependencies.sh
./requirements/install_dependencies.sh

# 激活虛擬環境（如果創建了的話）
source venv/bin/activate

# 啟動應用
python run.py
```

#### Windows 系統
```bash
# 安裝依賴
pip install -r requirements/requirements.txt

# 啟動應用
python run.py
```

### 訪問應用
啟動後訪問：http://127.0.0.1:5000

## 項目結構

```
C2/
├── app/                    # Flask 應用核心代碼
├── routes/                 # 路由定義
├── templates/              # HTML 模板
├── static/                 # 靜態資源
├── config/                 # 配置文件
├── instance/               # 數據庫和模型
├── requirements/           # 依賴管理和安裝文件
├── scripts/                # 工具腳本
│   └── database/          # 數據庫管理腳本
├── test/                   # 測試文件
├── docs/                   # 項目文檔
├── frontend/               # 前端構建配置
├── vulnerability_scanning/ # 漏洞掃描模塊
├── reconnaissance/         # 偵察模塊
├── back_door/             # 後門模塊
├── DDOS_DAY/              # DDoS 模塊
└── run.py                 # 應用入口點
```

詳細結構說明請參考：[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

## 系統更新記錄

### 用戶模型移除
為了簡化系統架構，我們移除了所有與用戶相關的模型和功能：

1. **模型更改**：
   - 從數據庫中刪除了`User`模型
   - 刪除了`ZOMBIE`模型和相關的`Command_ZOMBIE`模型
   - 刪除了`Command_User`模型
   - 修改了`Target`模型，移除了對`User`的引用

2. **身份驗證改變**：
   - 移除了Flask-Login依賴
   - `login_required`裝飾器已變為空裝飾器
   - 移除了登錄、註冊和註銷功能

3. **權限檢查**：
   - 簡化了權限系統，只檢查目標是否存在，不再驗證用戶權限

## 使用指南

1. **添加目標**: 通過首頁的"添加目標"按鈕添加新的掃描目標
2. **執行掃描**: 選擇目標後，可以執行各種掃描和測試
3. **查看結果**: 所有掃描結果都會保存在`output/`目錄中
4. **管理數據**: 使用`scripts/database/`中的工具管理數據庫

## 重置數據庫

如果需要重置數據庫：

```bash
# 重置數據庫並啟動應用
python run.py --reset-db

# 只重置數據庫，不啟動應用
python run.py --reset-db --reset-only
```

## 開發者信息

這個項目由一位15歲的學生開發，旨在降低網絡安全測試的門檻。我們歡迎更多開發者加入這個項目，共同完善這個平台。

### 貢獻指南
- 查看 `test/` 目錄了解如何運行測試
- 閱讀 `docs/` 目錄中的文檔
- 使用 `requirements/` 目錄中的腳本進行安裝和依賴管理

## 免責聲明

本工具僅用於合法的安全測試和教育目的。使用者需要確保在獲得適當授權的情況下使用本工具，並遵守當地法律法規。開發者不對任何濫用行為承擔責任。

## 許可證

請參閱 [LICENSE.md](LICENSE.md) 文件了解詳細的許可證信息。