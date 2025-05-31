# Requirements 目錄說明

這個目錄包含了 C2 項目的所有依賴管理和安裝相關文件。

## 文件說明

### 📦 依賴定義文件

#### `requirements.txt`
- **用途**: 完整的 Python 包依賴列表
- **內容**: 包含項目運行所需的所有 Python 包及其版本
- **使用**: `pip install -r requirements.txt`

#### `requirements-core.txt`
- **用途**: 核心依賴的簡化版本
- **內容**: 只包含最基本的運行依賴，適合快速安裝
- **使用**: `pip install -r requirements-core.txt`

### 🚀 安裝腳本

#### `install_dependencies.sh`
- **用途**: Linux 系統自動安裝腳本
- **功能**:
  - 自動檢測 Linux 發行版
  - 安裝系統依賴包
  - 創建 Python 虛擬環境（如需要）
  - 安裝 Python 依賴
  - 配置 Docker 和權限
  - 驗證安裝結果
- **使用**: `chmod +x install_dependencies.sh && ./install_dependencies.sh`

#### `LINUX_INSTALL_GUIDE.md`
- **用途**: 詳細的 Linux 安裝指南
- **內容**: 
  - 系統要求說明
  - 手動安裝步驟
  - 常見問題解決方案
  - 性能優化建議

## 安裝方式選擇

### 🔧 自動安裝（推薦）
```bash
# Linux 系統
chmod +x requirements/install_dependencies.sh
./requirements/install_dependencies.sh
```

### 📋 手動安裝
```bash
# 安裝完整依賴
pip install -r requirements/requirements.txt

# 或安裝核心依賴
pip install -r requirements/requirements-core.txt
```

### 🐳 虛擬環境安裝
```bash
# 創建虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝依賴
pip install -r requirements/requirements.txt
```

## 依賴分類

### 核心 Web 框架
- Flask 及其擴展
- SQLAlchemy 數據庫 ORM
- 會話和認證管理

### 網絡和安全工具
- nmap, scapy (網絡掃描)
- requests, aiohttp (HTTP 客戶端)
- cryptography (加密功能)

### 數據處理
- pandas, numpy (數據分析)
- beautifulsoup4, lxml (HTML 解析)
- PyYAML (配置文件)

### 機器學習（可選）
- torch, transformers (深度學習)
- scikit-learn (機器學習)

### 開發工具
- pytest (測試框架)
- black, flake8 (代碼格式化)
- playwright (瀏覽器自動化)

## 故障排除

### 常見問題

1. **權限錯誤**
   ```bash
   # 使用虛擬環境
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **包版本衝突**
   ```bash
   # 使用核心依賴
   pip install -r requirements-core.txt
   ```

3. **系統依賴缺失**
   ```bash
   # 運行自動安裝腳本
   ./install_dependencies.sh
   ```

### 獲取幫助

- 查看 `LINUX_INSTALL_GUIDE.md` 獲取詳細安裝說明
- 檢查項目根目錄的 `README.md` 了解項目概況
- 參考 `docs/PROJECT_STRUCTURE.md` 了解項目結構

## 更新依賴

如需更新依賴版本：

1. 編輯 `requirements.txt` 文件
2. 測試新版本的兼容性
3. 更新 `requirements-core.txt`（如果涉及核心依賴）
4. 更新安裝腳本（如果需要新的系統依賴） 