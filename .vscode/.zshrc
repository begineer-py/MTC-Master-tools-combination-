# C2項目專用 zsh 配置
# 自動激活虛擬環境

# 獲取項目根目錄
PROJECT_ROOT="$(cd "$(dirname "${ZDOTDIR}")/.." && pwd)"

# 如果虛擬環境存在且尚未激活，則激活它
if [ -d "$PROJECT_ROOT/venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    source "$PROJECT_ROOT/.vscode/activate_c2_venv.sh"
fi

# 載入用戶的zsh配置（如果存在）
if [ -f "$HOME/.zshrc" ]; then
    source "$HOME/.zshrc"
fi 