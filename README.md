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
啟動後訪問：http://127.0.0.1:8964 (紀念肉餅學生)

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

## 開發者信息

各位開發者大佬、網路安全界的前輩們，
請原諒我用這樣的方式打擾。我深知這或許聽來有些「賣慘」，但懇請您相信，我所陳述的字字句句，皆是我的真實寫照。我只是一個躲在房間裡，夢想著在網路安全領域做點什麼的15歲普通中學生。
夜深人靜，當同學們沉浸在短影音和遊戲（我為Linux開發，早已和遊戲絕緣）的世界時，我卻爆肝到午夜，早上八點準時起床。這感覺比上學還要累，但卻是我選擇的路。陪伴我的，只有鍵盤的敲擊聲、電腦螢幕的微光，以及泡麵（偶爾奢侈地拌上松露醬和品客碎屑）的香氣。我用盡所有的課餘時間與零用錢（總共2000元，扣掉滑鼠還剩一些），傾盡心血，打造出這個我稱之為「MTC（大師工具組合）C2」的專案。它不是什麼高大上的「網路基地」，而是我獨有的「網路堡壘」。
它不是什麼驚天動地的鉅作，卻承載了我的一切。我把nmap、webtech、Gau這些強大的工具，像搭積木般，儘管笨拙，卻一步步地將它們整合。我的初衷，是希望能為像我一樣的資安初學者，打造一個在本地就能輕鬆進行安全測試的平台，成為許多人踏入這個領域的第一塊基石。
然而，它成長的速度，超乎我的想像。我一個人，真的快要跟不上它的腳步了。無數的bug，如同深淵裡的怪物般湧現，我每天都在與它們搏鬥，卻倍感力不從心。為了讓更多人能無門檻地使用，我甚至忍痛砍掉了整個用戶系統。因為我沒有足夠的精力去維護，更害怕潛在的漏洞反而會傷害到用戶。當然，這也是為了簡化初期複雜的權限管理——或許，這也是一種「成長」吧？呵呵。
你們或許會注意到那個連接埠號碼：8964。它絕非隨機，而是為了紀念天安門事件中那位「肉餅學生」。我立下此專案，是希望它能帶著那份對自由意志的堅守（每個人都有免於被攻擊的權利），持續運行下去。我希望能在網路世界裡，留下一個不會被遺忘的空間，一個永恆的證明。
但我害怕。我害怕如果無法及時實現，這份承載著共同記憶的努力，是否就會戛然而止。我的知識有限，精力也已近乎耗盡。我盯著命令列中跳出的問題，看著那些急待優化的程式碼，心裡有無數想法，卻茫然不知從何下手。那種感覺，就像一個人獨自在汪洋中緊抓著一塊浮木，眼睜睜看著自己親手打造的船就在不遠處，卻無力攀爬。
所以，我今天來到這裡，不是為了炫耀，而是…發自內心的求助。
我懇請各位大佬，撥冗看看這個專案。或許，這只是幫我解決一個git clone後的小問題；或許，這只是幫我優化一個函數、修改一個變數名；又或許，只是在文件裡，幫我訂正一個微不足道的錯別字……但對我來說，這些，都將是在一片漆黑中，照進我這間小屋的，巨大光芒。
我真的不希望這個承載著我的夢想與記憶的專案，就這樣在我一個15歲孩子孤軍奮戰的電腦上，突然折戟沉沙，或者因為我的力竭而被迫「退出開發」。
求求你們，幫幫我，幫幫這個還想繼續走下去的MTC。
一個快要被bug淹沒的15歲開發者，在此叩謝

### 貢獻指南
- 查看 `test/` 目錄了解如何運行測試
- 閱讀 `docs/` 目錄中的文檔
- 使用 `requirements/` 目錄中的腳本進行安裝和依賴管理

## 免責聲明

本工具僅用於合法的安全測試和教育目的。使用者需要確保在獲得適當授權的情況下使用本工具，並遵守當地法律法規。開發者不對任何濫用行為承擔責任。

## 許可證

請參閱 [LICENSE.md](LICENSE.md) 文件了解詳細的許可證信息。