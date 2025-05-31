#!/bin/bash

# C2項目依賴安裝腳本 - Linux版本
# 此腳本將安裝項目所需的所有Python包和系統依賴

set -e  # 遇到錯誤時退出

echo "=== C2項目依賴安裝腳本 ==="
echo "正在為Linux系統安裝依賴..."

# 檢查Python版本
echo "檢查Python版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "錯誤：需要Python 3.8或更高版本，當前版本：$python_version"
    exit 1
fi

echo "Python版本檢查通過：$python_version"

# 檢查pip是否安裝
if ! command -v pip3 &> /dev/null; then
    echo "錯誤：pip3未安裝，請先安裝pip3"
    exit 1
fi

# 更新系統包管理器
echo "更新系統包管理器..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
elif command -v yum &> /dev/null; then
    sudo yum update -y
elif command -v dnf &> /dev/null; then
    sudo dnf update -y
elif command -v pacman &> /dev/null; then
    sudo pacman -Sy
else
    echo "警告：無法識別的包管理器，請手動安裝系統依賴"
fi

# 安裝系統依賴
echo "安裝系統依賴..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    sudo apt-get install -y \
        python3-dev \
        python3-pip \
        python3-venv \
        python3-full \
        build-essential \
        libssl-dev \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
        libjpeg-dev \
        libpng-dev \
        libmagic1 \
        libmagic-dev \
        nmap \
        masscan \
        git \
        curl \
        wget \
        docker.io \
        docker-compose \
        postgresql-client \
        mysql-client \
        sqlite3 \
        libpq-dev \
        libmysqlclient-dev \
        libsqlite3-dev
        
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y \
        python3-devel \
        python3-pip \
        gcc \
        gcc-c++ \
        make \
        openssl-devel \
        libffi-devel \
        libxml2-devel \
        libxslt-devel \
        zlib-devel \
        libjpeg-devel \
        libpng-devel \
        file-devel \
        nmap \
        git \
        curl \
        wget \
        docker \
        docker-compose \
        postgresql \
        mysql \
        sqlite \
        postgresql-devel \
        mysql-devel \
        sqlite-devel
        
elif command -v dnf &> /dev/null; then
    # Fedora
    sudo dnf install -y \
        python3-devel \
        python3-pip \
        gcc \
        gcc-c++ \
        make \
        openssl-devel \
        libffi-devel \
        libxml2-devel \
        libxslt-devel \
        zlib-devel \
        libjpeg-devel \
        libpng-devel \
        file-devel \
        nmap \
        git \
        curl \
        wget \
        docker \
        docker-compose \
        postgresql \
        mysql \
        sqlite \
        postgresql-devel \
        mysql-devel \
        sqlite-devel
        
elif command -v pacman &> /dev/null; then
    # Arch Linux
    sudo pacman -S --noconfirm \
        python \
        python-pip \
        base-devel \
        openssl \
        libffi \
        libxml2 \
        libxslt \
        zlib \
        libjpeg \
        libpng \
        file \
        nmap \
        masscan \
        git \
        curl \
        wget \
        docker \
        docker-compose \
        postgresql \
        mysql \
        sqlite \
        postgresql-libs \
        mysql-clients \
        sqlite
fi

# 檢查是否需要使用虛擬環境
echo "檢查Python環境管理..."
USE_VENV=false

# 檢查是否是externally-managed環境
if python3 -m pip install --help 2>&1 | grep -q "externally-managed-environment" || \
   [ -f "/usr/lib/python3.*/EXTERNALLY-MANAGED" ] 2>/dev/null; then
    echo "檢測到externally-managed環境，將創建虛擬環境..."
    USE_VENV=true
fi

# 創建並激活虛擬環境（如果需要）
if [ "$USE_VENV" = true ]; then
    echo "創建虛擬環境..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    echo "激活虛擬環境..."
    source venv/bin/activate
    
    # 升級虛擬環境中的pip
    echo "升級虛擬環境中的pip..."
    python -m pip install --upgrade pip setuptools wheel
    
    PIP_CMD="python -m pip"
    PYTHON_CMD="python"
else
    # 升級系統pip
    echo "升級pip..."
    python3 -m pip install --upgrade pip setuptools wheel --break-system-packages
    
    PIP_CMD="python3 -m pip"
    PYTHON_CMD="python3"
fi

# 安裝Python依賴
echo "安裝Python依賴..."
if [ -f "requirements/requirements.txt" ]; then
    echo "從requirements/requirements.txt安裝依賴..."
    if [ "$USE_VENV" = true ]; then
        $PIP_CMD install -r requirements/requirements.txt
    else
        $PIP_CMD install -r requirements/requirements.txt --break-system-packages
    fi
else
    echo "錯誤：找不到requirements/requirements.txt文件"
    exit 1
fi

# 安裝playwright瀏覽器
echo "安裝playwright瀏覽器..."
$PYTHON_CMD -m playwright install

# 檢查Docker是否運行
echo "檢查Docker服務..."
if command -v docker &> /dev/null; then
    if ! sudo systemctl is-active --quiet docker; then
        echo "啟動Docker服務..."
        sudo systemctl start docker
        sudo systemctl enable docker
    fi
    
    # 將當前用戶添加到docker組
    sudo usermod -aG docker $USER
    echo "已將用戶 $USER 添加到docker組，請重新登錄以生效"
else
    echo "警告：Docker未安裝，某些功能可能無法使用"
fi

# 創建必要的目錄
echo "創建必要的目錄..."
mkdir -p instance/backups
mkdir -p instance/tools
mkdir -p logs
mkdir -p flask_session
mkdir -p output
mkdir -p temp

# 設置權限
echo "設置目錄權限..."
chmod 755 instance
chmod 755 logs
chmod 755 flask_session
chmod 755 output
chmod 755 temp

# 檢查安裝結果
echo "檢查關鍵依賴安裝狀態..."
$PYTHON_CMD -c "
import sys
packages = [
    'flask', 'sqlalchemy', 'requests', 'beautifulsoup4', 
    'nmap', 'scapy', 'torch', 'transformers', 'numpy', 
    'pandas', 'matplotlib', 'aiohttp', 'playwright'
]

failed = []
for package in packages:
    try:
        __import__(package)
        print(f'✓ {package}')
    except ImportError:
        print(f'✗ {package}')
        failed.append(package)

if failed:
    print(f'\n警告：以下包安裝失敗：{failed}')
    sys.exit(1)
else:
    print('\n所有關鍵依賴安裝成功！')
"

echo ""
echo "=== 安裝完成 ==="
echo "所有依賴已安裝完成！"
echo ""

if [ "$USE_VENV" = true ]; then
    echo "注意：已創建虛擬環境，運行項目前請先激活："
    echo "source venv/bin/activate"
    echo ""
fi

echo "注意事項："
echo "1. 如果您使用了Docker相關功能，請重新登錄以使docker組權限生效"
echo "2. 某些機器學習功能可能需要CUDA支持，請根據需要安裝NVIDIA驅動和CUDA"
echo "3. 如果遇到權限問題，請確保當前用戶有足夠的權限"
echo ""

if [ "$USE_VENV" = true ]; then
    echo "現在您可以運行項目："
    echo "source venv/bin/activate"
    echo "python run.py"
else
    echo "現在您可以運行項目："
    echo "python3 run.py"
fi 