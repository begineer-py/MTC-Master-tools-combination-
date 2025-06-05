# C2 安全測試平台 - 快速開始

## 🚀 快速啟動

### 1. 初始化環境
```bash
# 初始化虛擬環境
./requirements/venv_manager.sh clean

# 安裝核心依賴
./requirements/venv_manager.sh install-req requirements/requirements.txt
```

### 2. 運行應用
```bash
# 設置環境變數並運行
PYTHONPATH=./venv/lib/python3.12/site-packages python3 run.py --no-sudo
```

### 3. 在Cursor中開發

1. 打開 `C2.code-workspace` 文件
2. 點擊 "Open Workspace"
3. 按 F5 調試或 Ctrl+Shift+P → "Tasks: Run Task" → "Run Flask App"

## 📦 包管理

```bash
# 安裝新包
./requirements/venv_manager.sh install "package_name"

# 列出已安裝的包
./requirements/venv_manager.sh list

# 測試環境
./requirements/venv_manager.sh test
```

## 🌐 訪問應用

應用啟動後訪問: http://127.0.0.1:8964

## 🔧 故障排除

- 如果端口被占用，修改 `run.py` 中的端口號
- 如果包導入失敗，檢查 PYTHONPATH 設置
- 使用 `./requirements/venv_manager.sh test` 診斷問題 