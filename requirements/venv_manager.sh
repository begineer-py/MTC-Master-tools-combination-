#!/bin/bash

# C2 虛擬環境管理器
# 解決Cursor AppImage污染問題的完整解決方案

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 項目配置
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"
SITE_PACKAGES="$VENV_DIR/lib/python3.12/site-packages"
SYSTEM_PYTHON="/usr/bin/python3"

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查系統Python
check_system_python() {
    if [ ! -f "$SYSTEM_PYTHON" ]; then
        log_error "系統Python不存在: $SYSTEM_PYTHON"
        log_info "請安裝Python3: sudo apt install python3"
        exit 1
    fi
    log_success "系統Python檢查通過: $SYSTEM_PYTHON"
}

# 創建乾淨的虛擬環境
create_clean_venv() {
    log_info "創建乾淨的虛擬環境..."
    
    # 刪除舊的虛擬環境
    if [ -d "$VENV_DIR" ]; then
        log_warning "刪除舊的虛擬環境..."
        rm -rf "$VENV_DIR"
    fi
    
    # 創建新的虛擬環境（不包含pip，避免Cursor干擾）
    log_info "使用系統Python創建虛擬環境..."
    "$SYSTEM_PYTHON" -m venv "$VENV_DIR" --without-pip
    
    # 修復Python符號連結（避免指向Cursor AppImage）
    log_info "修復Python符號連結..."
    rm -f "$VENV_DIR/bin/python" "$VENV_DIR/bin/python3" "$VENV_DIR/bin/python3.12"
    cp "$SYSTEM_PYTHON" "$VENV_DIR/bin/python3"
    ln -s python3 "$VENV_DIR/bin/python"
    ln -s python3 "$VENV_DIR/bin/python3.12"
    
    # 手動安裝pip
    log_info "安裝pip到虛擬環境..."
    if ! curl -s https://bootstrap.pypa.io/get-pip.py | "$SYSTEM_PYTHON" - --prefix="$VENV_DIR" --force-reinstall; then
        log_warning "pip安裝失敗，嘗試替代方法..."
        # 使用系統pip直接安裝到虛擬環境
        "$SYSTEM_PYTHON" -m pip install --target="$SITE_PACKAGES" --upgrade pip
    fi
    
    log_success "虛擬環境創建完成: $VENV_DIR"
}

# 安裝包的函數
install_package() {
    local packages="$1"
    log_info "安裝包: $packages"
    
    # 設置環境變數並安裝
    PYTHONPATH="$SITE_PACKAGES" "$SYSTEM_PYTHON" -m pip install \
        --target="$SITE_PACKAGES" \
        --upgrade \
        $packages
    
    log_success "包安裝完成: $packages"
}

# 安裝requirements文件
install_requirements() {
    local req_file="$1"
    if [ ! -f "$req_file" ]; then
        log_error "Requirements文件不存在: $req_file"
        return 1
    fi
    
    log_info "從文件安裝依賴: $req_file"
    
    # 逐行讀取並安裝（跳過註釋和空行）
    while IFS= read -r line; do
        # 跳過註釋和空行
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
            continue
        fi
        
        # 移除行尾註釋
        package=$(echo "$line" | sed 's/#.*//' | xargs)
        
        if [ -n "$package" ]; then
            log_info "安裝: $package"
            install_package "$package"
        fi
    done < "$req_file"
    
    log_success "Requirements安裝完成"
}

# 列出已安裝的包
list_packages() {
    log_info "已安裝的包:"
    PYTHONPATH="$SITE_PACKAGES" "$SYSTEM_PYTHON" -m pip list --path="$SITE_PACKAGES"
}

# 測試虛擬環境
test_venv() {
    log_info "測試虛擬環境..."
    
    # 測試Python路徑
    local python_path=$(PYTHONPATH="$SITE_PACKAGES" "$VENV_DIR/bin/python3" -c "import sys; print(sys.executable)")
    log_info "Python執行檔: $python_path"
    
    # 測試包導入
    log_info "測試核心包導入..."
    PYTHONPATH="$SITE_PACKAGES" "$VENV_DIR/bin/python3" -c "
try:
    import flask
    import sqlalchemy
    print('✅ Flask和SQLAlchemy導入成功')
except ImportError as e:
    print(f'❌ 導入失敗: {e}')
    exit(1)
"
    
    log_success "虛擬環境測試通過"
}

# 創建激活腳本
create_activate_script() {
    log_info "創建激活腳本..."
    
    cat > "$PROJECT_ROOT/activate_venv.sh" << 'EOF'
#!/bin/bash
# C2項目虛擬環境激活腳本

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$PROJECT_ROOT/venv/lib/python3.12/site-packages"
export VIRTUAL_ENV="$PROJECT_ROOT/venv"
export PATH="$PROJECT_ROOT/venv/bin:$PATH"

echo "🐍 虛擬環境已激活"
echo "📦 PYTHONPATH: $PYTHONPATH"
echo "💡 使用 'deactivate' 退出虛擬環境"

# 創建deactivate函數
deactivate() {
    unset PYTHONPATH
    unset VIRTUAL_ENV
    export PATH=$(echo $PATH | sed "s|$PROJECT_ROOT/venv/bin:||")
    unset -f deactivate
    echo "🚪 虛擬環境已退出"
}

# 啟動新的shell
exec bash --rcfile <(echo "PS1='(venv) \u@\h:\w\$ '")
EOF
    
    chmod +x "$PROJECT_ROOT/activate_venv.sh"
    log_success "激活腳本創建完成: activate_venv.sh"
}

# 顯示幫助信息
show_help() {
    echo "C2 虛擬環境管理器"
    echo "=================="
    echo ""
    echo "用法: $0 [命令] [參數]"
    echo ""
    echo "命令:"
    echo "  init                     初始化虛擬環境"
    echo "  install <packages>       安裝包"
    echo "  install-req <file>       從requirements文件安裝"
    echo "  list                     列出已安裝的包"
    echo "  test                     測試虛擬環境"
    echo "  clean                    清理並重建虛擬環境"
    echo "  help                     顯示此幫助信息"
    echo ""
    echo "示例:"
    echo "  $0 init                                    # 初始化環境"
    echo "  $0 install flask sqlalchemy               # 安裝包"
    echo "  $0 install-req requirements/requirements.txt  # 安裝requirements"
    echo "  $0 list                                    # 列出包"
    echo ""
}

# 主函數
main() {
    case "$1" in
        "init")
            check_system_python
            create_clean_venv
            create_activate_script
            log_success "虛擬環境初始化完成！"
            log_info "使用 './venv_manager.sh install <package>' 安裝包"
            log_info "使用 'source activate_venv.sh' 激活環境"
            ;;
        "install")
            if [ -z "$2" ]; then
                log_error "請指定要安裝的包"
                exit 1
            fi
            shift
            install_package "$*"
            ;;
        "install-req")
            if [ -z "$2" ]; then
                log_error "請指定requirements文件路徑"
                exit 1
            fi
            install_requirements "$2"
            ;;
        "list")
            list_packages
            ;;
        "test")
            test_venv
            ;;
        "clean")
            log_warning "這將刪除現有的虛擬環境並重建"
            read -p "確定要繼續嗎？(y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                check_system_python
                create_clean_venv
                create_activate_script
                log_success "虛擬環境重建完成！"
            else
                log_info "操作已取消"
            fi
            ;;
        "help"|"--help"|"-h"|"")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@" 