# C2 網絡安全測試平台

## 項目簡介

這是一個功能強大的本地C2（Command & Control）網絡安全測試平台，專為安全研究人員和滲透測試人員設計。平台提供了完整的網絡偵察、漏洞掃描和安全測試功能，讓任何想要進行安全測試的人都能輕鬆上手。

## 主要功能

### 🔍 前端偵察功能
- **nmap**: 網絡端口掃描
- **webtech**: Web技術識別
- **Gau**: 參數爬取
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

## 系統要求

- **操作系統**: Ubuntu/Debian Linux (18.04+)
- **Python版本**: Python 3.8 或更高版本
- **內存**: 建議 8GB 以上 (機器學習功能需要更多內存)
- **存儲空間**: 至少 10GB 可用空間
- **網絡**: 需要互聯網連接以下載依賴

## 快速開始

### 方法一：使用自動安裝腳本（推薦）

```bash
# 克隆項目
git clone https://github.com/begineer-py/MTC-Master-tools-combination-
cd C2

# 運行自動安裝腳本
chmod +x requirements/install_dependencies.sh
./requirements/install_dependencies.sh

# 啟動應用
python run.py
```

### 方法二：手動安裝

#### 1. 安裝系統依賴

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip python3-venv python3-full \
    build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev \
    zlib1g-dev libjpeg-dev libpng-dev libmagic1 libmagic-dev \
    nmap masscan git curl wget postgresql-client mysql-client \
    sqlite3 libpq-dev libmysqlclient-dev libsqlite3-dev
```

#### 2. 創建虛擬環境並安裝Python依賴

```bash
# 創建虛擬環境
python3 -m venv venv
source venv/bin/activate

# 升級pip
python -m pip install --upgrade pip setuptools wheel

# 安裝Python依賴
pip install -r requirements/requirements.txt

# 安裝playwright瀏覽器
python -m playwright install
```

#### 3. 創建必要目錄

```bash
mkdir -p instance/backups instance/tools logs flask_session output temp
chmod 755 instance logs flask_session output temp
```

## 驗證安裝

運行以下命令檢查關鍵依賴是否正確安裝：

```bash
python -c "
import flask, sqlalchemy, requests, beautifulsoup4, nmap, scapy
import torch, transformers, numpy, pandas, matplotlib, aiohttp, playwright
print('所有關鍵依賴安裝成功！')
"
```

## 運行項目

```bash
# 基本運行
python run.py

# 重置數據庫後運行
python run.py --reset-db

# 僅重置數據庫
python run.py --reset-db --reset-only

# 數據庫遷移
python run.py --migrate
```

### 訪問應用
啟動後訪問：http://127.0.0.1:6666

## 常見問題解決

### 1. 權限問題

如果遇到權限錯誤：
```bash
# 確保目錄權限正確
sudo chown -R $USER:$USER /path/to/C2
chmod -R 755 /path/to/C2
```

### 2. Python包安裝失敗

如果某些包安裝失敗，嘗試：
```bash
# 使用虛擬環境（推薦）
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/requirements.txt

# 或者使用用戶安裝模式
python3 -m pip install --user -r requirements/requirements.txt
```

### 3. 機器學習依賴問題

對於PyTorch等大型包：
```bash
# 如果沒有CUDA，安裝CPU版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 如果有CUDA，安裝GPU版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4. 數據庫鎖定問題

如果遇到數據庫鎖定：
```bash
# 解鎖數據庫
./scripts/database/db_unlock.sh

# 或者重置數據庫
python run.py --reset-db
```

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
│   ├── install_dependencies.sh # 自動安裝腳本
│   ├── apt_install.txt     # Ubuntu/Debian包列表
│   └── requirements.txt    # Python依賴
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

## 支持的功能

安裝完成後，您將可以使用以下功能：

- ✅ Web應用框架 (Flask)
- ✅ 數據庫操作 (SQLAlchemy)
- ✅ 網絡掃描 (nmap, masscan)
- ✅ 漏洞掃描 (SQL注入, XSS等)
- ✅ 網絡包分析 (scapy)
- ✅ 機器學習 (PyTorch, Transformers)
- ✅ 異步處理 (aiohttp)
- ✅ 瀏覽器自動化 (Playwright)

## 性能優化建議

1. **內存優化**: 如果內存不足，可以在配置中禁用某些機器學習功能
2. **存儲優化**: 定期清理logs和temp目錄
3. **網絡優化**: 配置代理以加速包下載

## 安全注意事項

1. 確保防火牆配置正確
2. 定期更新依賴包
3. 不要在生產環境中使用DEBUG模式
4. 定期備份數據庫

## 系統更新記錄

### 用戶模型移除
為了簡化系統架構，我們移除了所有與用戶相關的模型和功能：

1. **模型更改**：
   - 從數據庫中刪除了`User`模型
   - 刪除了`ZOMBIE`模型和相關的`Command_ZOMBIE`模型
   - 刪除了`Command_User`模型
   - 修改了`Target`模型，移除了對`User`的引用

2. **權限檢查**：
   - 簡化了權限系統，只檢查目標是否存在，不再驗證用戶權限

### 系統簡化 (最新)
為了提高穩定性和維護性：

1. **移除多發行版支持**: 專注於Ubuntu/Debian系統
2. **移除Docker依賴**: 簡化安裝流程
3. **強制虛擬環境**: 確保環境隔離和穩定性
4. **模組化包管理**: 使用獨立的apt_install.txt管理系統依賴

## 使用指南

1. **添加目標**: 通過首頁的"添加目標"按鈕添加新的掃描目標
2. **執行掃描**: 選擇目標後，可以執行各種掃描和測試
3. **管理數據**: 使用`scripts/database/`中的工具管理數據庫

### 貢獻指南
- `test/` 目錄有一些如何運行測試
- 閱讀 `docs/` 目錄中的文檔
- 使用 `requirements/` 目錄中的腳本進行安裝和依賴管理

## 免責聲明

# MTC - 免責聲明與使用準則

## ⚠️ 重要警告 (IMPORTANT WARNING)

本工具 (`MTC`) 被設計為一個強大的安全研究和滲透測試框架。與任何強大的工具一樣，它可能被用於惡意目的。本聲明的目的，是明確劃清合法使用與非法濫用之間的界線。

### 1. 授權用途 (Authorized Use)

`MTC` 僅限於以下兩種情況使用：

*   **學術研究與安全教育：** 在隔離的、您自己擁有完全控制權的實驗室環境中，學習和理解Web攻擊與防禦技術。
*   **授權的滲透測試：** 在獲得目標系統所有者 **明確、書面授權** 的前提下，對目標系統進行安全性評估。

### 2. 禁止的行為 (Prohibited Actions)

嚴格禁止使用 `MTC` 進行任何未經授權的計算機入侵或數據竊取活動。這包括但不限於：

*   對任何不屬於您或未經您授權的網站植入鉤子。
*   竊取、篡改或洩露任何您無權訪問的數據。
*   對任何系統造成服務中斷或破壞。

### 3. 無擔保聲明 (AS-IS Warranty)

本工具按「現狀」提供，不附帶任何明示或暗示的擔保。作者不對本工具的性能、穩定性或適用性作任何保證。

### 4. 責任限制 (Limitation of Liability)

在任何情況下，對於因使用或無法使用本工具而導致的任何直接、間接、附帶、特殊、懲戒性或後果性的損害（包括但不限於數據丟失、利潤損失或業務中斷），無論是基於何種責任理論（合同、嚴格責任或侵權），本項目的作者、貢獻者及維護者均不承擔任何責任。

**您對本工具的任何使用，都代表您已經閱讀、理解並同意遵守上述所有條款，並願意為您的所有行為獨立承擔全部法律責任。**

---

## 許可證

請參閱 [LICENSE.md](LICENSE.md) 文件了解詳細的許可證信息。