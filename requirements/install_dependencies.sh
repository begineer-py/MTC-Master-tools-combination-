#!/bin/bash

# C2項目依賴安裝腳本 - Linux版本
# 此腳本將安裝項目所需的所有Python包和系統依賴
# 整合了虛擬環境創建和管理功能

set -e  # 遇到錯誤時退出

# 獲取腳本所在目錄，並切換到作為項目根目錄的上級目錄
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
cd "$PROJECT_ROOT"
echo "工作目錄已切換至項目根目錄：$PROJECT_ROOT"

echo "=== C2項目依賴安裝腳本 ==="
echo "正在為Linux系統安裝依賴..."

#——————————————————————————————————————————————————————————————————————————————————
# 1. Python版本檢查模塊
#——————————————————————————————————————————————————————————————————————————————————

# 檢查Python版本
echo "檢查Python版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "錯誤：需要Python 3.8或更高版本，當前版本：$python_version"
    exit 1
fi

echo "Python版本檢查通過：$python_version"

#——————————————————————————————————————————————————————————————————————————————————
# 2. pip3安裝檢查和自動安裝模塊
#——————————————————————————————————————————————————————————————————————————————————

# 檢查pip是否安裝，如果沒有則嘗試自動安裝
if ! command -v pip3 &> /dev/null; then
    echo "警告：pip3未安裝，正在嘗試自動安裝..."
    
    # 檢查是否為Ubuntu/Debian系統
    if command -v apt-get &> /dev/null; then
        echo "更新apt包管理器..."
        sudo apt-get update
        echo "安裝python3-pip..."
        sudo apt-get install -y python3-pip python3-venv python3-full
    else
        echo "錯誤：此腳本僅支援Ubuntu/Debian系統(apt-get)"
        echo "請手動安裝pip3後重新運行此腳本"
        exit 1
    fi
    
    # 再次檢查pip是否安裝成功
    if ! command -v pip3 &> /dev/null; then
        echo "錯誤：pip3安裝失敗，請手動安裝pip3"
        exit 1
    fi
    
    echo "pip3安裝成功！"
else
    echo "pip3已安裝，版本：$(pip3 --version)"
fi

#——————————————————————————————————————————————————————————————————————————————————
# 3. 系統包管理器更新模塊
#——————————————————————————————————————————————————————————————————————————————————

# 更新系統包管理器
echo "更新系統包管理器..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
else
    echo "錯誤：此腳本僅支援Ubuntu/Debian系統(apt-get)"
    exit 1
fi

#——————————————————————————————————————————————————————————————————————————————————
# 4. 系統依賴安裝模塊
#——————————————————————————————————————————————————————————————————————————————————

# 安裝系統依賴
echo "安裝系統依賴..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    echo "使用apt_install.txt安裝Ubuntu/Debian依賴..."
    if [ -f "requirements/apt_install.txt" ]; then
        # 從apt_install.txt讀取包列表（忽略註釋和空行）
        packages=$(grep -v '^#' requirements/apt_install.txt | grep -v '^$' | tr '\n' ' ')
        sudo apt-get install -y $packages
    else
        echo "警告：未找到requirements/apt_install.txt，使用默認包列表"
        sudo apt-get install -y \
            python3-dev python3-pip python3-venv python3-full \
            build-essential libssl-dev libffi-dev libxml2-dev \
            libxslt1-dev zlib1g-dev libjpeg-dev libpng-dev \
            libmagic1 libmagic-dev nmap masscan git curl wget \
            postgresql-client mysql-client sqlite3 libpq-dev \
            libmysqlclient-dev libsqlite3-dev
    fi
else
    echo "錯誤：此腳本僅支援Ubuntu/Debian系統(apt-get)"
    exit 1
fi


#——————————————————————————————————————————————————————————————————————————————————
# 6. 虛擬環境管理函數模塊
#——————————————————————————————————————————————————————————————————————————————————

# 虛擬環境創建和管理函數
create_virtual_environment() {
    local venv_name="venv"
    local base_dir=$(pwd)
    
    echo "=== 虛擬環境設置 ==="
    echo "創建虛擬環境：$venv_name"
    
    # 如果虛擬環境已存在，詢問是否重新創建
    if [ -d "$venv_name" ]; then
        echo "虛擬環境 '$venv_name' 已存在"
        echo "使用現有虛擬環境..."
    fi
    
    # 創建虛擬環境
    if [ ! -d "$venv_name" ]; then
        echo "正在創建新的虛擬環境..."
        python3 -m venv "$venv_name"
        if [ $? -eq 0 ]; then
            echo "✓ 虛擬環境創建成功"
        else
            echo "✗ 虛擬環境創建失敗"
            exit 1
        fi
    fi
    
    # 激活虛擬環境
    echo "激活虛擬環境..."
    source "$venv_name/bin/activate"
    
    # 驗證虛擬環境激活
    if [ "$VIRTUAL_ENV" != "" ]; then
        echo "✓ 虛擬環境已激活：$VIRTUAL_ENV"
    else
        echo "✗ 虛擬環境激活失敗"
        exit 1
    fi
    
    # 升級虛擬環境中的pip
    echo "升級虛擬環境中的pip..."
    python -m pip install --upgrade pip setuptools wheel
    
    # 設置命令變數
    PIP_CMD="python -m pip"
    PYTHON_CMD="python"
    
    echo "虛擬環境設置完成！"
}

#——————————————————————————————————————————————————————————————————————————————————
# 7. 系統級安裝設置模塊
#——————————————————————————————————————————————————————————————————————————————————
USE_VENV=true
# 系統級安裝設置
setup_system_installation() {
    echo "=== 系統級安裝設置 ==="
    
    # 升級系統pip
    echo "升級系統pip..."
    python3 -m pip install --upgrade pip setuptools wheel --break-system-packages 2>/dev/null || \
    python3 -m pip install --upgrade pip setuptools wheel
    
    # 設置命令變數
    PIP_CMD="python3 -m pip"
    PYTHON_CMD="python3"
    
    echo "系統級安裝設置完成！"
}

#——————————————————————————————————————————————————————————————————————————————————
# 8. 環境設置執行模塊
#——————————————————————————————————————————————————————————————————————————————————

# 執行環境設置
if [ "$USE_VENV" = true ]; then
    create_virtual_environment
else
    setup_system_installation
fi

#——————————————————————————————————————————————————————————————————————————————————
# 9. Python依賴安裝模塊
#——————————————————————————————————————————————————————————————————————————————————

# 安裝Python依賴的函數
install_python_dependencies() {
    echo "=== 安裝Python依賴 ==="
    
    # 檢查requirements.txt文件
    if [ -f "requirements.txt" ]; then
        requirements_file="requirements.txt"
    elif [ -f "requirements/requirements.txt" ]; then
        requirements_file="requirements/requirements.txt"
    else
        echo "錯誤：找不到requirements.txt文件"
        echo "請確保在項目根目錄或requirements/目錄下存在requirements.txt"
        exit 1
    fi
    
    echo "從 $requirements_file 安裝依賴..."
    
    # 根據環境選擇安裝方式
    if [ "$USE_VENV" = true ]; then
        $PIP_CMD install -r "$requirements_file"
    else
        # 嘗試不同的安裝方式
        $PIP_CMD install -r "$requirements_file" --break-system-packages 2>/dev/null || \
        $PIP_CMD install -r "$requirements_file" --user 2>/dev/null || \
        $PIP_CMD install -r "$requirements_file"
    fi
    
    if [ $? -eq 0 ]; then
        echo "✓ Python依賴安裝成功"
    else
        echo "✗ Python依賴安裝失敗"
        exit 1
    fi
}

# 安裝Python依賴
install_python_dependencies

#——————————————————————————————————————————————————————————————————————————————————
# 10. Playwright瀏覽器安裝模塊
#——————————————————————————————————————————————————————————————————————————————————

# 安裝playwright瀏覽器
echo "=== 安裝playwright瀏覽器 ==="
$PYTHON_CMD -m playwright install
if [ $? -eq 0 ]; then
    echo "✓ Playwright瀏覽器安裝成功"
else
    echo "✗ Playwright瀏覽器安裝失敗，但不影響主要功能"
fi



#——————————————————————————————————————————————————————————————————————————————————
# 12. 項目目錄結構創建模塊
#——————————————————————————————————————————————————————————————————————————————————

# 創建必要的目錄
echo "=== 創建項目目錄結構 ==="
directories=(
    "instance/backups"
    "instance/tools"
    "logs"
    "flask_session"
    "output"
    "temp"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "✓ 創建目錄：$dir"
    else
        echo "- 目錄已存在：$dir"
    fi
done

# 設置權限
echo "設置目錄權限..."
chmod 755 instance logs flask_session output temp 2>/dev/null || true

#——————————————————————————————————————————————————————————————————————————————————
# 13. 依賴檢查模塊
#——————————————————————————————————————————————————————————————————————————————————

# 依賴檢查函數
check_dependencies() {
    echo "=== 檢查關鍵依賴安裝狀態 ==="
    
    $PYTHON_CMD -c "
import sys
import importlib

# 關鍵依賴列表
packages = [
    'flask', 'sqlalchemy', 'requests', 'beautifulsoup4', 
    'nmap', 'scapy', 'torch', 'transformers', 'numpy', 
    'pandas', 'matplotlib', 'aiohttp', 'playwright'
]

# 可選依賴列表
optional_packages = [
    'tensorflow', 'opencv', 'pillow'
]

print('檢查必要依賴：')
failed = []
for package in packages:
    try:
        importlib.import_module(package)
        print(f'✓ {package}')
    except ImportError:
        print(f'✗ {package}')
        failed.append(package)

print('\n檢查可選依賴：')
for package in optional_packages:
    try:
        importlib.import_module(package)
        print(f'✓ {package}')
    except ImportError:
        print(f'- {package} (可選)')

if failed:
    print(f'\n⚠ 警告：以下必要包安裝失敗：{failed}')
    print('您可以稍後手動安裝這些包')
else:
    print('\n🎉 所有關鍵依賴安裝成功！')
"
}

# 執行依賴檢查
check_dependencies

#——————————————————————————————————————————————————————————————————————————————————
# 14. 安裝完成信息顯示模塊
#——————————————————————————————————————————————————————————————————————————————————

echo ""
echo "=== 安裝完成 ==="
echo "🎉 所有依賴已安裝完成！"
echo ""

# 顯示使用說明
if [ "$USE_VENV" = true ]; then
    echo "📝 虛擬環境使用說明："
    echo "   激活虛擬環境：source venv/bin/activate"
    echo "   退出虛擬環境：deactivate"
    echo "   運行項目：source venv/bin/activate && python run.py"
    echo ""
fi

echo "📋 注意事項："
echo "   1. 機器學習功能可能需要CUDA支持"
echo "   2. 如遇權限問題，請確保當前用戶有足夠權限"
echo ""

echo "🚀 現在您可以運行項目："
if [ "$USE_VENV" = true ]; then
    echo "   source venv/bin/activate"
    echo "   python run.py"
else
    echo "   python3 run.py"
fi

echo ""
echo "💡 腳本參數："
echo "   --use-venv 或 -v : 強制使用虛擬環境"
echo "   例如：./install_dependencies.sh --use-venv" 