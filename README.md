# 🔐 C2 安全測試平台

> 一個功能強大的本地 C2（Command & Control）網絡安全測試平台，專為安全研究人員和滲透測試人員設計。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange.svg)](https://www.linux.org/)

## 📋 目錄

- [✨ 特色功能](#-特色功能)
- [🏗️ 系統架構](#️-系統架構)
- [🚀 快速開始](#-快速開始)
- [📦 虛擬環境管理](#-虛擬環境管理)
- [🔧 使用說明](#-使用說明)
- [📊 支持的掃描工具](#-支持的掃描工具)
- [🛠️ 開發指南](#️-開發指南)
- [🔒 安全注意事項](#-安全注意事項)
- [📁 項目結構](#-項目結構)
- [🤝 貢獻指南](#-貢獻指南)

## ✨ 特色功能

### 🔍 網絡偵察模塊
- **Nmap** - 高性能端口掃描和服務檢測
- **WebTech** - Web 技術棧識別和版本檢測
- **Gau** - URL 參數收集和路徑發現
- **CrtSH** - 證書透明度日誌查詢和子域名發現
- **FlareSolverr** - Cloudflare 繞過和 JavaScript 渲染

### 🛡️ 漏洞掃描引擎
- **XSS 檢測** - 跨站腳本漏洞自動化檢測
- **SQL 注入** - SQLMap 集成，支持多種注入類型
- **目錄遍歷** - 敏感文件和目錄發現
- **表單注入** - 智能表單字段注入測試
- **NoSQL 注入** - MongoDB、CouchDB、Redis 等 NoSQL 數據庫漏洞檢測

### 🎯 C2 控制功能
- **遠程代碼執行** - 基於 XSS 的客戶端代碼執行
- **信息收集** - 瀏覽器指紋、系統信息收集
- **會話劫持** - Cookie 和 Session 竊取
- **網絡代理** - HTTP 請求攔截和修改

### 🌐 現代化 Web 界面
- **響應式設計** - 支持桌面和移動設備
- **實時更新** - WebSocket 實時掃描狀態
- **數據可視化** - 掃描結果圖表和統計
- **專業界面** - 每個工具獨立的現代化界面

## 🏗️ 系統架構

```
┌─────────────────┬─────────────────┬─────────────────┐
│   前端界面      │    業務邏輯     │    數據存儲     │
├─────────────────┼─────────────────┼─────────────────┤
│ • React 組件    │ • Flask 路由    │ • SQLite 數據庫 │
│ • 現代化 UI     │ • 藍圖架構      │ • 掃描結果存儲  │
│ • 實時更新      │ • 異步任務      │ • 日誌記錄      │
│ • 響應式設計    │ • API 接口      │ • 會話管理      │
└─────────────────┴─────────────────┴─────────────────┘
```

## 🚀 快速開始

### 系統要求

- **操作系統**: Ubuntu 24.04+ / Debian 10+
- **Python**: 3.8 或更高版本
- **內存**: 8GB+ (推薦 16GB)
- **存儲**: 10GB+ 可用空間
- **網絡**: 互聯網連接

### 一鍵安裝

```bash
# 克隆項目
git clone https://github.com/begineer-py/MTC-Master-tools-combination-
cd C2

# 自動安裝所有依賴
chmod +x requirements/install_dependencies.sh
./requirements/install_dependencies.sh

# 啟動應用
python3 run.py --no-sudo
```

### 手動安裝

```bash
# 1. 安裝系統依賴
sudo apt update && sudo apt install -y \
    python3-dev python3-pip python3-venv python3-full \
    nmap masscan git curl wget \
    build-essential libssl-dev libffi-dev

# 2. 創建虛擬環境
python3 -m venv venv
source venv/bin/activate

# 3. 安裝 Python 依賴
pip install -r requirements/requirements.txt
# 4. 啟動應用
python3 run.py --no-sudo
# apt 自己想辦法 如果你要手動安裝的話 
```

## 📦 虛擬環境管理

本項目提供了完善的虛擬環境管理系統：

### 一鍵管理

```bash
# 激活虛擬環境
source .vscode/activate_c2_venv.sh

# 退出虛擬環境
deactivate
# 或使用強制退出
source .vscode/deactivate_c2_venv.sh
```

### 包管理工具

```bash
# 使用虛擬環境管理器
./requirements/install_dependencies.sh
```

## 🔧 使用說明

### 啟動應用

```bash
# 基本啟動
python3 run.py --no-sudo

# 使用 sudo 權限（推薦，性能更好）
python3 run.py

# 重置數據庫
python3 run.py --reset-db

# 僅重置數據庫（不啟動應用）
python3 run.py --reset-db --reset-only
```

### 訪問應用

- **主界面**: http://127.0.0.1:1337
- **掃描界面**: http://127.0.0.1:1337/attack/1

### 核心工作流程

1. **添加目標**: 在主界面添加掃描目標
2. **選擇工具**: 進入 Attack 頁面選擇掃描工具
3. **執行掃描**: 啟動相應的掃描模塊
4. **查看結果**: 實時查看掃描進度和結果
5. **生成報告**: 導出詳細的掃描報告

## 📊 支持的掃描工具

| 工具 | 功能 | 狀態 | 獨立界面 |
|------|------|------|----------|
| **Nmap** | 端口掃描 | ✅ 完成 | ✅ 專業界面 |
| **WebTech** | 技術識別 | ✅ 完成 | ✅ 專業界面 |
| **Gau** | URL 收集 | ✅ 完成 | ✅ 專業界面 |
| **CrtSH** | 子域名發現 | ✅ 完成 | ✅ 專業界面 |
| **SQLMap** | SQL 注入 | 🚧 開發中 | 🚧 開發中 |
| **NoSQLMap** | NoSQL 注入 | 🚧 開發中 | 🚧 開發中 |
| **Nuclei** | 漏洞掃描 | 📋 計劃中 | 📋 計劃中 |

## 🛠️ 開發指南

### 開發環境設置

```bash
# 克隆並進入項目
git clone <repository-url>
cd C2

# 激活虛擬環境
source .vscode/activate_c2_venv.sh

# 安裝開發依賴
pip install -r requirements/requirements.txt

# 啟動開發服務器
python3 run.py --no-sudo
```

### 項目結構

```
C2/
├── 📂 app/                   # Flask 應用核心
│   ├── __init__.py
│   ├── app.py               # Flask 應用工廠
│   └── blueprint_set.py     # 藍圖註冊
├── 📂 routes/               # 路由定義
│   ├── index_routes.py      # 主頁路由
│   ├── result_route.py      # 結果頁面路由
│   ├── zombie_routes.py     # 殭屍網絡路由
│   ├── reconnaissance_route/ # 偵察工具路由
│   │   ├── attack_route.py
│   │   ├── crtsh_route.py
│   │   ├── flaresolverr_route.py
│   │   ├── gau_route.py
│   │   ├── nmap_route.py
│   │   └── webtech_route.py
│   ├── attack_vulnerability_route/ # 攻擊模塊路由
│   │   └── attack_vulnerability_route.py
│   ├── C2_control/          # C2 控制路由
│   │   └── control_route.py
│   └── config_route/        # 配置路由
│       └── target_config_route.py
├── 📂 templates/            # HTML 模板
│   ├── base.html
│   ├── attack.html
│   ├── add_target.html
│   ├── layouts/
│   ├── crtsh_htmls/
│   ├── gau_htmls/
│   ├── nmap_htmls/
│   ├── flaresolverr_htmls/
│   └── C2_control/
├── 📂 static/               # 靜態資源
│   ├── css/                 # 樣式文件
│   ├── js/                  # JavaScript 文件
│   │   ├── components/      # React 組件
│   │   ├── pages/
│   │   ├── utils/
│   │   └── dist/            # 構建輸出
│   ├── images/              # 圖片資源
│   └── logo/
├── 📂 reconnaissance/       # 偵察模塊
│   ├── security_scanning/
│   │   ├── crtsh.py
│   │   ├── Scanner.py
│   │   └── web_tech/
│   ├── scanner_flaresolverr/
│   └── threads/
├── 📂 vulnerability_scanning/ # 漏洞掃描模塊
│   ├── sql_injection.py
│   ├── xss_game/
│   ├── blueprint_/
│   └── threads/
├── 📂 tools/                # 外部工具集成
│   ├── nuclei/              # Nuclei 漏洞掃描器
│   ├── sqlmap/              # SQLMap SQL 注入工具
│   ├── gau_linux/           # Gau URL 收集工具
│   ├── FlareSolverr/        # Cloudflare 繞過工具
│   ├── proxy/               # HTTP 代理工具
│   └── hack_the_box_tool/   # HTB 相關工具
├── 📂 payloads/             # 攻擊載荷庫
│   ├── Discovery/           # 發現類載荷
│   ├── Fuzzing/             # 模糊測試載荷
│   ├── Passwords/           # 密碼字典
│   └── Payloads/            # 通用載荷
├── 📂 config/               # 配置文件
├── 📂 instance/             # 實例文件
│   ├── models.py            # 數據庫模型
│   ├── db_tools.py          # 數據庫工具
│   └── tools/               # 數據庫管理工具
├── 📂 requirements/         # 依賴管理
│   ├── requirements.txt     # Python 依賴列表
│   ├── install_dependencies.sh # 自動安裝腳本
│   ├── venv_manager.sh      # 虛擬環境管理器
│   └── README.md
├── 📂 .vscode/              # 開發環境配置
│   ├── settings.json        # VSCode 設置
│   ├── tasks.json           # 任務配置
│   ├── launch.json          # 調試配置
│   ├── activate_c2_venv.sh  # 虛擬環境激活腳本
│   └── deactivate_c2_venv.sh # 虛擬環境退出腳本
├── 📂 docs/                 # 項目文檔
│   ├── PROJECT_STRUCTURE.md
│   └── developers/
├── 📂 scripts/              # 實用腳本
│   └── database/            # 數據庫管理腳本
├── 📂 test/                 # 測試文件
├── 📂 logs/                 # 日誌文件
├── 📂 output/               # 輸出文件
└── 📂 temp/                 # 臨時文件
```

</details>

## 🤝 貢獻指南

我們歡迎所有形式的貢獻！

### 貢獻方式

1. **報告 Bug**: 在 Issues 中報告問題
2. **功能建議**: 提出新功能想法
3. **代碼貢獻**: 提交 Pull Request
4. **文檔改進**: 完善文檔和教程

### 開發流程

1. Fork 本項目
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 代碼規範

- 使用 Python 3.8+ 語法
- 遵循 PEP 8 代碼風格
- 添加適當的註釋和文檔
- 編寫測試用例

## 📄 許可證

本項目採用 MIT 許可證 - 查看 [LICENSE.md](LICENSE.md) 文件了解詳情。

## 🙏 致謝

感謝以下開源項目的支持：

- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - 數據庫 ORM
- [Nmap](https://nmap.org/) - 網絡掃描工具
- [SQLMap](http://sqlmap.org/) - SQL 注入工具
- [React](https://reactjs.org/) - 前端框架

## 📞 聯繫我們

- **GitHub Issues**: [提交問題](https://github.com/begineer-py/MTC-Master-tools-combination-/issues)
- **Email**: [聯繫郵箱]
- **文檔**: [在線文檔](https://github.com/begineer-py/MTC-Master-tools-combination-/wiki)

---

<div align="center">

**⭐ 如果這個項目對你有幫助，請給我們一個 Star！**

Made with ❤️ by Security Researchers

</div>