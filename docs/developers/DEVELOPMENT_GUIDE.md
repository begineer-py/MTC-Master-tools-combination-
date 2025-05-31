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
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
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

## 🧪 測試

### 運行測試
```bash
# 運行所有測試
pytest

# 運行特定測試文件
pytest test/test_api_auth.py

# 運行測試並生成覆蓋率報告
pytest --cov=app --cov-report=html

# 運行特定標記的測試
pytest -m "not slow"
```

### 編寫測試
```python
# test/test_example.py
import pytest
from app.app import create_app
from instance.models import db

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
```

## 🐛 調試

### Flask 調試模式
```bash
# 設置環境變量
export FLASK_ENV=development
export FLASK_DEBUG=1

# 運行應用
python run.py
```

### 日誌配置
```python
# 在代碼中添加日誌
import logging

logger = logging.getLogger(__name__)
logger.info("這是一條信息日誌")
logger.error("這是一條錯誤日誌")
```

### 常用調試技巧
```python
# 使用 pdb 調試器
import pdb; pdb.set_trace()

# 使用 print 調試（開發階段）
print(f"變量值: {variable}")

# 使用 Flask 的 current_app
from flask import current_app
current_app.logger.info("應用日誌")
```

## 📦 依賴管理

### 添加新依賴
```bash
# 安裝新包
pip install package-name

# 更新 requirements.txt
pip freeze > requirements/requirements.txt

# 或手動編輯 requirements.txt
vim requirements/requirements.txt
```

### 依賴版本管理
- 使用具體版本號：`Flask==3.0.2`
- 使用兼容版本：`Flask>=3.0.0,<4.0.0`
- 定期更新依賴並測試兼容性

## 🚀 部署準備

### 生產環境配置
```python
# config/config.py
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # 其他生產環境配置
```

### 性能優化
- 使用 Gunicorn 作為 WSGI 服務器
- 配置 Nginx 作為反向代理
- 使用 Redis 進行緩存
- 優化數據庫查詢

## 📋 開發工作流

### 功能開發流程
1. **創建分支**: `git checkout -b feature/new-feature`
2. **開發功能**: 編寫代碼和測試
3. **運行測試**: 確保所有測試通過
4. **代碼檢查**: 運行 linting 工具
5. **提交代碼**: 使用規範的提交消息
6. **推送分支**: `git push origin feature/new-feature`
7. **創建 PR**: 在 GitHub 上創建 Pull Request

### 代碼審查清單
- [ ] 代碼符合項目規範
- [ ] 所有測試通過
- [ ] 新功能有對應測試
- [ ] 文檔已更新
- [ ] 沒有安全漏洞
- [ ] 性能影響可接受

## 🔍 常見問題

### Q: 虛擬環境激活失敗
```bash
# 確保 Python 版本正確
python3 --version

# 重新創建虛擬環境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### Q: 依賴安裝失敗
```bash
# 升級 pip
pip install --upgrade pip

# 使用國內鏡像
pip install -r requirements/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### Q: 數據庫連接問題
```bash
# 檢查數據庫文件權限
ls -la instance/

# 重置數據庫
python run.py --reset-db --reset-only
```

## 📚 學習資源

### Flask 相關
- [Flask 官方文檔](https://flask.palletsprojects.com/)
- [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)

### 安全開發
- [OWASP Python Security](https://owasp.org/www-project-python-security/)
- [Python Security Best Practices](https://python-security.readthedocs.io/)

### 測試
- [pytest 文檔](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)

---

如有問題，請查看項目 Issues 或聯繫開發團隊。 