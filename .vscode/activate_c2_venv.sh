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
# 調試信息（可選）
# echo "DEBUG: VIRTUAL_ENV='$VIRTUAL_ENV', VENV_PATH='$VENV_PATH'"
# echo "DEBUG: PATH contains venv/bin: $(echo $PATH | grep -q "$VENV_PATH/bin" && echo 'yes' || echo 'no')"

if [ "$VIRTUAL_ENV" = "$VENV_PATH" ] && [[ "$PATH" == *"$VENV_PATH/bin"* ]]; then
    echo "✅ 虛擬環境已經正確激活: $VENV_PATH"
    ALREADY_ACTIVATED=true
else
    ALREADY_ACTIVATED=false
fi

# 如果還沒激活，則進行激活
if [ "$ALREADY_ACTIVATED" = false ]; then
    # 保存原始PATH（如果還沒保存的話）
    if [ -z "$_OLD_VIRTUAL_PATH" ]; then
        export _OLD_VIRTUAL_PATH="$PATH"
    fi

    # 設置環境變數
    export VIRTUAL_ENV="$VENV_PATH"
    export PATH="$VENV_PATH/bin:$PATH"
    export PYTHONPATH="$VENV_PATH/lib/python3.12/site-packages"

    # 設置提示符（避免重複添加）
    if [[ "$PS1" != *"(C2-venv)"* ]]; then
        export PS1="(C2-venv) $PS1"
    fi
fi

# 顯示激活信息
if [ "$ALREADY_ACTIVATED" = true ]; then
    echo "🔄 重新顯示虛擬環境信息"
else
    echo "🐍 C2虛擬環境已激活"
fi
echo "🔧 Python: $(which python3)"
echo "📦 Pip: $(which pip)"
echo "📁 項目目錄: $PROJECT_ROOT"
echo ""


# 確保 deactivate 函數在當前 shell 中可用
export -f deactivate 2>/dev/null || true

# 創建退出別名作為備用方法
alias exit_venv='deactivate'
alias quit_venv='deactivate'

# 顯示可用命令
echo "💡 可用命令:"
echo "  python3 run.py --no-sudo    # 運行應用"
echo "  pip install package_name    # 安裝包"
echo "  pip list                    # 列出已安裝的包"
echo "  deactivate                  # 退出虛擬環境"
echo "  exit_venv                   # 退出虛擬環境（備用）"
echo "  source .vscode/deactivate_c2_venv.sh  # 強制退出虛擬環境"
echo "  source .vscode/activate_c2_venv.sh    # 重新激活"
echo ""

# 驗證虛擬環境是否正確激活
echo "🔍 驗證虛擬環境:"
echo "  Virtual Env: $VIRTUAL_ENV"
echo "  Python 路徑: $(which python3)"
echo "  Pip 路徑: $(which pip)" 