#!/bin/zsh
# C2項目虛擬環境退出腳本

echo "🚪 正在退出 C2 虛擬環境..."

# 清理環境變數
unset VIRTUAL_ENV
unset PYTHONPATH  
unset ALREADY_ACTIVATED

# 恢復 PATH
if [ -n "$_OLD_VIRTUAL_PATH" ]; then
    export PATH="$_OLD_VIRTUAL_PATH"
    unset _OLD_VIRTUAL_PATH
else
    # 手動清理 PATH 中的 venv 路徑
    export PATH=$(echo "$PATH" | sed 's|[^:]*venv[^:]*:||g' | sed 's|:[^:]*venv[^:]*||g')
fi

# 清理提示符
if [[ "$PS1" == *"(venv)"* ]] || [[ "$PS1" == *"(C2-venv)"* ]]; then
    export PS1=$(echo "$PS1" | sed 's/(venv) //g' | sed 's/(C2-venv) //g')
fi

# 移除別名
unalias exit_venv 2>/dev/null || true
unalias quit_venv 2>/dev/null || true

# 移除函數
unset -f deactivate 2>/dev/null || true

echo "✅ C2虛擬環境已退出"
echo "🔧 當前 Python: $(which python3)"
echo "📁 當前目錄: $(pwd)" 