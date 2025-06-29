# C2項目專用 zsh 配置
# 自動激活虛擬環境

# 獲取項目根目錄
PROJECT_ROOT="$(cd "$(dirname "${ZDOTDIR}")/.." && pwd)"

# 自動激活已禁用，請手動執行：
# source .vscode/activate_c2_venv.sh

# 載入用戶的zsh配置（如果存在）
if [ -f "$HOME/.zshrc" ]; then
    source "$HOME/.zshrc"
fi 
function deactivate() {
    # 恢復原始PATH
    if [ -n "$_OLD_VIRTUAL_PATH" ]; then
        export PATH="$_OLD_VIRTUAL_PATH"
        unset _OLD_VIRTUAL_PATH
    fi
    
    # 恢復原始提示符（更安全的方式）
    if [[ "$PS1" == *"(C2-venv)"* ]]; then
        export PS1=$(echo "$PS1" | sed 's/(C2-venv) //')
    fi
    
    # 清理環境變數
    unset PYTHONPATH
    unset VIRTUAL_ENV
    unset ALREADY_ACTIVATED
    unset -f deactivate
    echo "🚪 C2虛擬環境已退出"
}
