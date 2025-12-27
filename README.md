```markdown
第一部分：核心免責聲明 (中文版)
【法律免責聲明與使用條約】
授權與合法性：本工具僅限於「受控環境下的安全研究」與「獲得明確書面授權的滲透測試」。使用者在對任何目標執行掃描、分析或打擊任務前，必須確保擁有該目標的所有權或合法授權。
刑事責任自負：未經授權的掃描與滲透可能違反《中華民國刑法》第 358 條至第 362 條（妨害電腦使用罪）或其他國家/地區的網路安全法律（如美國 CFAA）。開發者對於使用者之任何違法行為不負任何連帶責任。
無擔保聲明：本平台「按原樣（As-Is）」提供。開發者不保證工具的穩定性、準確性，亦不對因使用本工具造成的任何直接或間接損失（包括但不限於系統崩潰、數據丟失、業務中斷或法律追訴）承擔責任。
情報準確性：AI 分析與自動化工具可能存在「誤報（False Positive）」或「漏報（False Negative）」。所有情報僅供參考，使用者應在決策前自行複核。
使用者承諾：一旦下載、編譯或運行本專案代碼，即代表您已閱讀、理解並完全同意本聲明的所有條款。

LEGAL DISCLAIMER
FOR EDUCATIONAL AND ETHICAL TESTING PURPOSES ONLY.
Usage of MTC (Master Tools Combination) for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws.
Developers assume no liability and are not responsible for any misuse or damage caused by this program.
By using this software, you agree that you are solely responsible for your own actions.
The software is provided "as is", without warranty of any kind, express or implied.
# C2 Django AI - 全方位網路安全掃描平台

## 項目概述

C2 Django AI是一個全方位的網路安全掃描和滲透測試平台，集成了現代化的AI分析能力。該系統採用Django後端框架，結合React前端界面，提供從資產發現、端口掃描到深度AI分析的完整工作流程。

## 架構總覽

### 核心技術棧
- **後端框架**: Django 5.2.9 + Django REST Framework
- **數據庫**: PostgreSQL (通過Docker容器運行)
- **任務隊列**: Redis + Celery
- **前端**: React 18 + TypeScript + Vite
- **容器化**: Docker Compose
- **API代理**: 自定義代理服務支持多個AI API (Gemini, Mistral等)

## 主要功能模組

### 1. 核心數據模型 (core app)
負責管理所有安全掃描相關的數據實體：

#### 資產管理
- **Target**: 專案目標 (如 google.com)
- **Seed**: 種子資產 (域名、IP範圍、URL)
- **IP**: IP地址及其端口信息
- **Port**: 開放端口及服務信息
- **Subdomain**: 子域名及其屬性
- **URLResult**: URL掃描結果及分析數據

#### 掃描記錄
- **SubfinderScan**: 子域名發現任務
- **NmapScan**: 端口掃描任務
- **URLScan**: URL深度掃描任務

#### AI分析模型
- **IPAIAnalysis**: IP地址AI分析
- **SubdomainAIAnalysis**: 子域名AI分析
- **URLAIAnalysis**: URL內容AI分析

### 2. AI分析系統 (analyze_ai app)
集成多個AI服務提供商進行智能分析：

#### 支持的AI服務
- Google Gemini 2.5 Flash
- Mistral AI
- 自定義代理服務

#### 分析功能
- IP地址風險評估和漏洞分析
- 子域名業務重要性和技術棧分析
- URL內容分析和敏感信息提取

#### 技術特點
- 動態AI服務切換和負載均衡
- GraphQL數據查詢優化
- Token使用量控制和錯誤處理
- 批量處理和重試機制

### 3. 掃描工具集成

#### Nmap掃描器 (nmap_scanner)
- 異步端口掃描任務
- XML結果解析和數據庫存儲
- 掃描狀態追蹤和錯誤處理

#### 子域名發現 (subfinder)
- 多來源子域名枚舉
- DNS解析和CDN/WAF檢測
- 資產生命週期管理

#### 網路爬蟲 (flaresolverr)
- 反爬蟲保護繞過
- 技術棧檢測 (Wappalyzer集成)
- 動態內容渲染支持

### 4. 前端界面 (frontend)
現代化的React應用：

#### 主要頁面
- 目標管理儀表板
- 掃描結果展示
- 子域名詳情頁面
- 種子資產管理

#### 技術特點
- TypeScript類型安全
- React Router導航
- 響應式設計
- RESTful API集成

## 外部依賴和服務

### 容器化服務 (Docker Compose)
- **PostgreSQL**: 主數據庫
- **Redis**: 任務隊列和緩存
- **Hasura**: GraphQL API層
- **NocoDB**: 管理員後台界面
- **FlareSolverr**: 反爬蟲代理
- **FlareProxyGo**: 代理管理工具
- **NyaProxy**: API均勻負載
### Python依賴 (requirements.txt)
- **Web框架**: Django, DRF, django-ninja
- **數據庫**: psycopg2-binary, redis
- **任務處理**: celery, eventlet, kombu
- **網路請求**: requests, httpx, curl_cffi
- **解析工具**: beautifulsoup4, gql (GraphQL)
- **安全工具**: python-nmap, wafw00f, python-Wappalyzer
- **工具**: pydantic, PyYAML, loguru

### 外部工具集成
- **Nmap**: 端口掃描
- **Subfinder**: 子域名發現
- **dnsx**: DNS解析
- **cdncheck**: CDN/WAF檢測

---

## 🛠 MTC (Master Tools Combination) 部署手冊

### 0. 戰前準備 (System Requirements)
- **OS**: Linux (Ubuntu 22.04+ 最佳)
- **工具**: Docker, Docker Compose V2, Miniconda/Anaconda
- **硬體**: 建議 2 vCPU / 4GB RAM 以上 (因掃描任務較吃記憶體)

### 1. 基礎設施啟動 (The Support)
這一步啟動資料庫、快取、代理中心與 WAF 繞過服務。

```bash
git clone https://github.com/begineer-py/MTC-Master-tools-combination-.git
cd MTC-Master-tools-combination-

# 建立並配置你的 AI 代理 (這是系統啟動的門票)
# 如果沒有，至少要建一個空的，否則 Django 啟動會報錯
mkdir -p docker
proxies:
  - name: "gemini_json_ai"
    url: "http://localhost:8502/api/gemini_json_ai/"
EOF

# 一鍵啟動後勤部隊
# 包括: Postgres, Redis, Hasura, NocoDB, FlareSolverr, NyaProxy
docker compose up -d
```

### 2. 邏輯大腦配置 (The Brain)
我們使用 Conda 跑 Django 與 Celery，這樣 Nmap 可以直接讀取網卡，不需要搞複雜的 Docker 網路穿透。

#### A. 環境建立
```bash
# 建立 Python 3.10 環境
conda create -n mtc_env python=3.10 -y
conda activate mtc_env

# 安裝依賴 (使用我們精簡後的清單)
pip install -r requirements.txt
```

#### B. 環境變數 (.env)
*(請根據你的環境配置相應的環境變數)*

### 3. 初始化戰場 (The Initialization)
```bash
# 1. 執行資料庫遷移
python manage.py migrate

# 2. 建立管理員 (用來進 Django Admin)
python manage.py createsuperuser

# 3. 檢查系統狀態
python manage.py check
```

### 4. 全力運作 (The Execution)
你需要開啟三個 screen 或 tmux 視窗，讓系統持久運行：

#### 視窗 1: Django API Server
```bash
conda activate mtc_env
uvicorn c2_core.asgi:application --host 0.0.0.0 --port 8000 --workers 9 --loop uvloop --http httptools --backlog 2048 --limit-concurrency 1000 --reload
```

#### 視窗 2: Celery Worker (任務處理中心)
```bash
conda activate mtc_env
python scripts/celery_worker_eventlet.py -A c2_core.celery:app worker -P eventlet -c 100 -l info
```

#### 視窗 3: Celery Beat (定期掃描調度)
```bash
conda activate mtc_env
celery -A c2_core beat -l info
```

### 5. 驗收成果 (The Triage)
- **Web API**: http://127.0.0.1:8000
- **Hasura Console**: http://127.0.0.1:8085 (用來進行複雜的圖譜查詢)
- **NocoDB**: http://127.0.0.1:8081 (用來像看 Excel 一樣看你的掃描結果)
- **Django Admin**: http://127.0.0.1:8000/admin (手動管理 Seed 與 Target)

## 💡 運維細節 (Ops Notes)

### Nmap 執行
因為 Python 跑在宿主機 (Conda)，當 Celery 觸發 Nmap 任務時，它會直接在宿主機執行或透過宿主機 Docker 啟動。確保宿主機已安裝 nmap (`sudo apt install nmap`)。

### 檔案權限
如果使用 subprocess 保存掃描結果到本地，請確保 mtc_env 運行的用戶有讀寫 `./scans` 資料夾的權限。

### Hasura 歷史記錄
首次部署後，請登入 Hasura Console，「Track」所有的 `core_historical*` 表，並建立 Relationship，這樣前端才能看到情報變更時間軸。
```
