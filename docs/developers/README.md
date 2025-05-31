# 開發者文檔

歡迎來到 C2 項目的開發者文檔區域！這裡包含了所有開發相關的技術文檔、設計說明和開發指南。

## 📁 文檔結構

### 核心文檔
- **[API_REFERENCE.md](API_REFERENCE.md)** - API 接口參考文檔
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - 開發環境設置和開發指南
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - 系統架構設計文檔
- **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** - 數據庫結構說明

### 設計文檔
- **[design_document.md](design_document.md)** - 系統設計文檔
- **[SECURITY_DESIGN.md](SECURITY_DESIGN.md)** - 安全設計和考慮

### 開發記錄
- **[開發日誌.txt](開發日誌.txt)** - 開發過程記錄
- **[CHANGELOG.md](CHANGELOG.md)** - 版本更新記錄
- **[TODO.md](TODO.md)** - 待辦事項和功能規劃

### 測試文檔
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - 測試指南和測試用例

## 🚀 快速開始

### 新開發者入門
1. 閱讀 [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) 設置開發環境
2. 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解系統架構
3. 參考 [API_REFERENCE.md](API_REFERENCE.md) 了解 API 接口
4. 查看 [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) 了解數據結構

### 貢獻代碼
1. Fork 項目倉庫
2. 創建功能分支
3. 按照開發指南進行開發
4. 運行測試確保代碼質量
5. 提交 Pull Request

## 🛠️ 開發工具

### 推薦 IDE 配置
- **VS Code**: 推薦安裝 Python、Flask 擴展
- **PyCharm**: 專業版支持 Flask 項目
- **Vim/Neovim**: 配置 Python LSP

### 代碼規範
- 使用 **Black** 進行代碼格式化
- 使用 **Flake8** 進行代碼檢查
- 使用 **MyPy** 進行類型檢查
- 遵循 **PEP 8** 編碼規範

### 測試工具
- **pytest**: 單元測試和集成測試
- **coverage**: 代碼覆蓋率檢查
- **tox**: 多環境測試

## 📋 開發流程

### 功能開發流程
1. **需求分析**: 明確功能需求和技術要求
2. **設計階段**: 更新設計文檔，確定技術方案
3. **編碼實現**: 按照代碼規範進行開發
4. **測試驗證**: 編寫和運行測試用例
5. **文檔更新**: 更新相關文檔和 API 說明
6. **代碼審查**: 提交 PR 進行代碼審查

### 版本發布流程
1. **功能凍結**: 確定發布功能範圍
2. **測試階段**: 全面測試和 bug 修復
3. **文檔更新**: 更新用戶文檔和 CHANGELOG
4. **版本標記**: 創建 Git 標籤
5. **發布部署**: 發布新版本

## 🔧 技術棧

### 後端技術
- **Flask**: Web 框架
- **SQLAlchemy**: ORM 數據庫操作
- **Celery**: 異步任務處理
- **Redis**: 緩存和消息隊列

### 前端技術
- **HTML5/CSS3**: 基礎前端技術
- **JavaScript**: 前端交互邏輯
- **Bootstrap**: UI 框架
- **WebSocket**: 實時通信

### 安全工具集成
- **nmap**: 網絡掃描
- **scapy**: 網絡包處理
- **paramspider**: 參數爬取
- **FlareSolverr**: Cloudflare 繞過

## 📞 聯繫方式

### 獲取幫助
- **GitHub Issues**: 報告 bug 和功能請求
- **討論區**: 技術討論和問題解答
- **開發者群組**: 加入開發者交流群

### 貢獻指南
- 歡迎提交 bug 報告和功能建議
- 歡迎貢獻代碼和文檔
- 歡迎參與代碼審查和測試

## 📚 相關資源

### 學習資源
- [Flask 官方文檔](https://flask.palletsprojects.com/)
- [SQLAlchemy 文檔](https://docs.sqlalchemy.org/)
- [Python 安全編程指南](https://python-security.readthedocs.io/)

### 工具文檔
- [nmap 使用指南](https://nmap.org/book/)
- [scapy 文檔](https://scapy.readthedocs.io/)
- [Docker 文檔](https://docs.docker.com/)

---

**注意**: 本項目僅用於合法的安全測試和教育目的。開發者有責任確保代碼的安全性和合規性。 