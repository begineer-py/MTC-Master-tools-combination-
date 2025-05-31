# C2項目 Linux 安裝指南

## 系統要求

- **操作系統**: Linux (Ubuntu 18.04+, CentOS 7+, Fedora 30+, Arch Linux)
- **Python版本**: Python 3.8 或更高版本
- **內存**: 建議 8GB 以上 (機器學習功能需要更多內存)
- **存儲空間**: 至少 10GB 可用空間
- **網絡**: 需要互聯網連接以下載依賴

## 快速安裝

### 方法一：使用自動安裝腳本（推薦）

```bash
# 1. 進入項目目錄
cd /home/hacker/Desktop/C2

# 2. 運行安裝腳本
./install_dependencies.sh
```

### 方法二：手動安裝

#### 1. 安裝系統依賴

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip build-essential \
    libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev \
    libjpeg-dev libpng-dev libmagic1 libmagic-dev nmap masscan \
    git curl wget docker.io docker-compose postgresql-client \
    mysql-client sqlite3 libpq-dev libmysqlclient-dev libsqlite3-dev
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3-devel python3-pip gcc gcc-c++ make \
    openssl-devel libffi-devel libxml2-devel libxslt-devel \
    zlib-devel libjpeg-devel libpng-devel file-devel nmap \
    git curl wget docker docker-compose postgresql mysql sqlite \
    postgresql-devel mysql-devel sqlite-devel
```

**Fedora:**
```bash
sudo dnf install -y python3-devel python3-pip gcc gcc-c++ make \
    openssl-devel libffi-devel libxml2-devel libxslt-devel \
    zlib-devel libjpeg-devel libpng-devel file-devel nmap \
    git curl wget docker docker-compose postgresql mysql sqlite \
    postgresql-devel mysql-devel sqlite-devel
```

#### 2. 升級pip並安裝Python依賴

```bash
# 升級pip
python3 -m pip install --upgrade pip setuptools wheel

# 安裝Python依賴
python3 -m pip install -r requirements/requirements.txt

# 安裝playwright瀏覽器
python3 -m playwright install
```

#### 3. 配置Docker（可選）

```bash
# 啟動Docker服務
sudo systemctl start docker
sudo systemctl enable docker

# 將當前用戶添加到docker組
sudo usermod -aG docker $USER

# 重新登錄以使權限生效
```

#### 4. 創建必要目錄

```bash
mkdir -p instance/backups instance/tools logs flask_session output temp
chmod 755 instance logs flask_session output temp
```

## 驗證安裝

運行以下命令檢查關鍵依賴是否正確安裝：

```bash
python3 -c "
import flask, sqlalchemy, requests, beautifulsoup4, nmap, scapy
import torch, transformers, numpy, pandas, matplotlib, aiohttp, playwright
print('所有關鍵依賴安裝成功！')
"
```

## 運行項目

```bash
# 基本運行
python3 run.py

# 重置數據庫後運行
python3 run.py --reset-db

# 僅重置數據庫
python3 run.py --reset-db --reset-only

# 數據庫遷移
python3 run.py --migrate
```

## 常見問題解決

### 1. 權限問題

如果遇到權限錯誤：
```bash
# 確保目錄權限正確
sudo chown -R $USER:$USER /home/hacker/Desktop/C2
chmod -R 755 /home/hacker/Desktop/C2
```

### 2. Python包安裝失敗

如果某些包安裝失敗，嘗試：
```bash
# 使用用戶安裝模式
python3 -m pip install --user -r requirements/requirements.txt

# 或者使用虛擬環境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/requirements.txt
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
./db_unlock.sh

# 或者重置數據庫
python3 run.py --reset-db
```

### 5. Docker相關問題

```bash
# 檢查Docker狀態
sudo systemctl status docker

# 重啟Docker服務
sudo systemctl restart docker

# 檢查用戶是否在docker組中
groups $USER
```

## 性能優化建議

1. **內存優化**: 如果內存不足，可以在配置中禁用某些機器學習功能
2. **存儲優化**: 定期清理logs和temp目錄
3. **網絡優化**: 配置代理以加速包下載

## 安全注意事項

1. 確保防火牆配置正確
2. 定期更新依賴包
3. 不要在生產環境中使用DEBUG模式
4. 定期備份數據庫

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
- ✅ 容器化支持 (Docker)

如果您在安裝過程中遇到任何問題，請檢查日誌文件或聯繫技術支持。 