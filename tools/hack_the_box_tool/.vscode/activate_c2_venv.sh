#!/bin/zsh
# C2項目虛擬環境激活腳本 - 專為Cursor設計

# 獲取項目根目錄
PROJECT_ROOT="$(cd "${0:h}/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"

# 檢查虛擬環境是否存在
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ 虛擬環境不存在: $VENV_PATH"
    echo "請先運行: python3 -m venv venv"
    return 1
fi

# 設置環境變數
export VIRTUAL_ENV="$VENV_PATH"
export PATH="$VENV_PATH/bin:$PATH"
export PYTHONPATH="$VENV_PATH/lib/python3.12/site-packages"

# 顯示激活信息
echo "🐍 C2虛擬環境已激活"
echo "-----------------------------------"
echo "👤 當前用戶: $(whoami)"
echo "🏠 當前目錄: $(pwd)"
echo "💻 系統類型: $(uname -s)"
echo "🐚 默認Shell: $SHELL"
echo "🔧 Python: $(which python3)"
echo "📦 Pip: $(which pip)"
echo "🔄 PATH: $PATH"
echo "📁 項目目錄: $PROJECT_ROOT"
echo "-----------------------------------"
echo ""

# 創建deactivate函數
deactivate() {
    export PATH=$(echo $PATH | sed "s|$VENV_PATH/bin:||")
    unset PYTHONPATH
    unset VIRTUAL_ENV
    unset PS1
    unset -f deactivate
    echo "🚪 C2虛擬環境已退出"
}

# 顯示可用命令
echo "💡 可用命令:"
echo "  python3 run.py --no-sudo    # 運行應用"
echo "  pip install package_name    # 安裝包"
echo "  pip list                    # 列出已安裝的包"
echo "  deactivate                  # 退出虛擬環境"
echo "" 

# 列出虛擬環境中的Python包
echo "✨ 虛擬環境中已安裝的Python包:"
pip list
echo "-----------------------------------" 