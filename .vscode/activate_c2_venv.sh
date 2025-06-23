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

# 檢查是否已經正確激活（同時檢查VIRTUAL_ENV和PATH）
if [ "$VIRTUAL_ENV" = "$VENV_PATH" ] && [[ "$PATH" == *"$VENV_PATH/bin"* ]]; then
    echo "✅ 虛擬環境已經正確激活: $VENV_PATH"
    return 0
fi

# 保存原始PATH（如果還沒保存的話）
if [ -z "$_OLD_VIRTUAL_PATH" ]; then
    export _OLD_VIRTUAL_PATH="$PATH"
fi

# 設置環境變數
export VIRTUAL_ENV="$VENV_PATH"
export PATH="$VENV_PATH/bin:$PATH"
export PYTHONPATH="$VENV_PATH/lib/python3.12/site-packages"

# 設置提示符
export PS1="(C2-venv) $PS1"

# 顯示激活信息
echo "🐍 C2虛擬環境已激活"
echo "🔧 Python: $(which python3)"
echo "📦 Pip: $(which pip)"
echo "📁 項目目錄: $PROJECT_ROOT"
echo ""

# 創建deactivate函數
deactivate() {
    # 恢復原始PATH
    if [ -n "$_OLD_VIRTUAL_PATH" ]; then
        export PATH="$_OLD_VIRTUAL_PATH"
        unset _OLD_VIRTUAL_PATH
    fi
    
    # 恢復原始提示符
    export PS1=$(echo "$PS1" | sed 's/(C2-venv) //')
    
    # 清理環境變數
    unset PYTHONPATH
    unset VIRTUAL_ENV
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

# 驗證虛擬環境是否正確激活
echo "🔍 驗證虛擬環境:"
echo "  Virtual Env: $VIRTUAL_ENV"
echo "  Python 路徑: $(which python3)"
echo "  Pip 路徑: $(which pip)" 