# 開發指南

本文檔將指導你如何設置 C2 項目的開發環境並開始開發。

## 🛠️ 開發環境設置

### 系統要求
- **Python**: 3.8 或更高版本
- **Git**: 版本控制
- **Docker**: 容器化服務（可選）
- **Node.js**: 前端構建（可選）

### 1. 克隆項目
```bash
git clone <repository-url>
cd C2
```

### 2. 設置 Python 虛擬環境
```bash
# 創建虛擬環境
python3 -m venv venv

# 激活虛擬環境
source venv/bin/activate
```

### 3. 安裝依賴
```bash
# 安裝完整依賴（推薦開發環境）
pip install -r requirements/requirements.txt

# 或使用自動安裝腳本（Linux）
chmod +x requirements/install_dependencies.sh
./requirements/install_dependencies.sh
```

### 4. 數據庫設置
```bash
# 初始化數據庫
python run.py --reset-db --reset-only

# 或手動創建數據庫
python -c "from app.app import create_app; from instance.models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 5. 配置開發環境
```bash
# 複製配置文件模板
cp config/config.py.example config/config.py

# 編輯配置文件
vim config/config.py
```

## 🔧 IDE 配置

### VS Code 配置
創建 `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/venv": true,
        "**/node_modules": true
    }
}
```

創建 `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Flask App",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/run.py",
            "env": {
                "FLASK_ENV": "development",
                "FLASK_DEBUG": "1"
            },
            "console": "integratedTerminal"
        }
    ]
}
```

### PyCharm 配置
1. 打開項目目錄
2. 設置 Python 解釋器為 `venv/bin/python`
3. 配置運行配置：
   - Script path: `run.py`
   - Environment variables: `FLASK_ENV=development;FLASK_DEBUG=1`

## 📝 代碼規範

### Python 代碼風格
```bash
# 安裝開發工具
pip install black flake8 mypy isort

# 格式化代碼
black .

# 檢查代碼風格
flake8 .

# 類型檢查
mypy .

# 排序導入
isort .
```

### 代碼規範要求
- 使用 **Black** 格式化，行長度 88 字符
- 遵循 **PEP 8** 編碼規範
- 使用類型提示（Type Hints）
- 編寫清晰的文檔字符串
- 變量和函數使用描述性命名

### Git 提交規範
```bash
# 提交消息格式
<type>(<scope>): <description>

# 類型說明
feat: 新功能
fix: bug 修復
docs: 文檔更新
style: 代碼格式化
refactor: 代碼重構
test: 測試相關
chore: 構建過程或輔助工具的變動

# 示例
feat(scanner): 添加新的漏洞掃描模塊
fix(database): 修復數據庫連接問題
docs(api): 更新 API 文檔
```