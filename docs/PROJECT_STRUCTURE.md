# C2 項目結構說明

## 目錄結構

```
C2/
├── app/                    # Flask 應用核心代碼
├── routes/                 # 路由定義
├── templates/              # HTML 模板
├── static/                 # 靜態資源 (CSS, JS, 圖片)
├── config/                 # 配置文件
├── instance/               # 實例相關文件 (數據庫, 模型)
├── utils/                  # 工具函數
├── requirements/           # Python 依賴管理和安裝文件
│   ├── requirements.txt   # 完整依賴列表
│   ├── requirements-core.txt # 核心依賴
│   ├── install_dependencies.sh # 自動安裝腳本
│   ├── LINUX_INSTALL_GUIDE.md # Linux安裝指南
│   └── README.md          # 依賴管理說明
├── scripts/                # 各種腳本工具
│   ├── database/          # 數據庫相關腳本
│   └── ...                # 其他工具腳本
├── test/                   # 測試文件
├── docs/                   # 項目文檔
│   ├── developers/        # 開發者專用文檔
│   │   ├── README.md      # 開發者文檔總覽
│   │   ├── DEVELOPMENT_GUIDE.md # 開發環境設置指南
│   │   ├── API_REFERENCE.md # API 接口參考
│   │   ├── DATABASE_SCHEMA.md # 數據庫結構說明
│   │   ├── TODO.md        # 待辦事項和功能規劃
│   │   ├── design_document.md # 系統設計文檔
│   │   └── 開發日誌.txt   # 開發過程記錄
│   ├── PROJECT_STRUCTURE.md # 項目結構說明（本文檔）
│   └── remade.md          # 項目原始說明
├── frontend/               # 前端構建配置
├── logs/                   # 日誌文件
├── output/                 # 輸出文件
├── temp/                   # 臨時文件
├── tools/                  # 外部工具
├── vulnerability_scanning/ # 漏洞掃描模塊
├── reconnaissance/         # 偵察模塊
├── back_door/             # 後門模塊
├── DDOS_DAY/              # DDoS 模塊
├── migrations/            # 數據庫遷移文件
├── build/                 # 構建輸出
├── flask_session/         # Flask 會話文件
├── venv/                  # Python 虛擬環境
└── run.py                 # 應用入口點
```

## 目錄說明

### 核心應用目錄
- **app/**: Flask 應用的核心代碼，包含應用工廠和主要邏輯
- **routes/**: 所有路由定義，按功能模塊分組
- **templates/**: Jinja2 HTML 模板文件
- **static/**: 靜態資源文件 (CSS, JavaScript, 圖片等)
- **config/**: 應用配置文件

### 數據和模型
- **instance/**: 實例特定文件，包含數據庫文件和模型定義
- **migrations/**: Flask-Migrate 數據庫遷移文件

### 功能模塊
- **vulnerability_scanning/**: 漏洞掃描相關功能
- **reconnaissance/**: 網絡偵察和信息收集
- **back_door/**: 後門和持久化功能
- **DDOS_DAY/**: DDoS 攻擊模塊
- **tools/**: 各種安全工具集成

### 開發和維護
- **scripts/**: 各種維護和工具腳本
  - **database/**: 數據庫管理腳本
- **test/**: 單元測試和集成測試
- **docs/**: 項目文檔和說明
  - **developers/**: 開發者專用技術文檔
- **frontend/**: 前端構建配置和依賴

### 依賴管理
- **requirements/**: Python 依賴管理和安裝
  - **requirements.txt**: 完整的Python包依賴列表
  - **requirements-core.txt**: 核心依賴的簡化版本
  - **install_dependencies.sh**: Linux系統自動安裝腳本
  - **LINUX_INSTALL_GUIDE.md**: 詳細的Linux安裝指南
  - **README.md**: 依賴管理說明文檔

### 運行時目錄
- **logs/**: 應用日誌文件
- **output/**: 掃描和分析結果輸出
- **temp/**: 臨時文件存儲
- **flask_session/**: Flask 會話數據
- **build/**: 前端構建輸出

### 環境和依賴
- **venv/**: Python 虛擬環境

## 開發者文檔詳解

### docs/developers/ 目錄
專門為開發者提供的技術文檔區域，包含：

#### 核心開發文檔
- **README.md**: 開發者文檔總覽和快速導航
- **DEVELOPMENT_GUIDE.md**: 完整的開發環境設置和開發指南
- **API_REFERENCE.md**: 詳細的 API 接口參考文檔
- **DATABASE_SCHEMA.md**: 數據庫表結構和關係說明

#### 規劃和設計
- **TODO.md**: 待辦事項、功能規劃和開發路線圖
- **design_document.md**: 系統架構和設計文檔
- **開發日誌.txt**: 開發過程記錄和重要變更

#### 文檔使用指南
1. **新開發者**: 從 `developers/README.md` 開始
2. **環境設置**: 參考 `developers/DEVELOPMENT_GUIDE.md`
3. **API 開發**: 查看 `developers/API_REFERENCE.md`
4. **數據庫操作**: 參考 `developers/DATABASE_SCHEMA.md`
5. **功能規劃**: 查看 `developers/TODO.md`

## 重要文件

- **run.py**: 應用程序入口點，用於啟動 Flask 應用
- **README.md**: 項目說明文檔
- **LICENSE.md**: 項目許可證
- **.gitignore**: Git 忽略文件配置

## 使用說明

### 用戶使用
1. **啟動應用**: 從項目根目錄運行 `python run.py`
2. **安裝依賴**: 使用 `requirements/install_dependencies.sh`
3. **查看文檔**: 參考 `docs/` 目錄中的相關文檔

### 開發者使用
1. **開發環境**: 參考 `docs/developers/DEVELOPMENT_GUIDE.md`
2. **API 開發**: 查看 `docs/developers/API_REFERENCE.md`
3. **數據庫**: 參考 `docs/developers/DATABASE_SCHEMA.md`
4. **貢獻代碼**: 查看 `docs/developers/TODO.md` 了解待辦事項

## 文檔維護

### 文檔更新原則
- **用戶文檔**: 隨功能發布同步更新
- **開發者文檔**: 隨代碼變更及時更新
- **API 文檔**: 接口變更時必須更新
- **數據庫文檔**: 結構變更時同步更新

### 文檔質量標準
- 內容準確性和時效性
- 結構清晰，易於導航
- 示例代碼可執行
- 支持多種使用場景

---

如需更多信息，請查看對應目錄中的詳細文檔或聯繫開發團隊。 