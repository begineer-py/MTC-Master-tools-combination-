# 數據庫結構說明

C2 項目使用 SQLite 作為默認數據庫，支持 PostgreSQL 和 MySQL。本文檔詳細說明了數據庫的表結構和關係。

## 📊 數據庫概覽

### 數據庫配置
- **默認數據庫**: SQLite (`instance/c2.db`)
- **支持數據庫**: PostgreSQL, MySQL, SQLite
- **ORM**: SQLAlchemy
- **遷移工具**: Flask-Migrate

### 表結構總覽
```
C2 Database
├── targets (目標管理)
├── scans (掃描記錄)
├── scan_results (掃描結果)
├── vulnerabilities (漏洞記錄)
├── crawler (爬蟲任務)
├── crawler_links (爬取的鏈接)
├── crawler_forms (表單數據)
├── crawler_images (圖片資源)
├── crawler_resources (其他資源)
├── system_logs (系統日誌)
└── configurations (系統配置)
```

## 🎯 核心表結構

### targets (目標管理表)
存儲掃描目標的基本信息。

```sql
CREATE TABLE targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url VARCHAR(500) NOT NULL,
    name VARCHAR(200),
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_scan_at DATETIME,
    scan_count INTEGER DEFAULT 0,
    vulnerability_count INTEGER DEFAULT 0
);
```

**字段說明:**
- `id`: 主鍵，自增
- `url`: 目標 URL，必填
- `name`: 目標名稱
- `description`: 目標描述
- `status`: 狀態 (active, inactive, archived)
- `created_at`: 創建時間
- `updated_at`: 更新時間
- `last_scan_at`: 最後掃描時間
- `scan_count`: 掃描次數統計
- `vulnerability_count`: 漏洞數量統計

### scans (掃描記錄表)
記錄所有掃描任務的信息。

```sql
CREATE TABLE scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id INTEGER NOT NULL,
    scan_type VARCHAR(100) NOT NULL,
    scan_id VARCHAR(200) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    duration INTEGER,
    command TEXT,
    options JSON,
    error_message TEXT,
    FOREIGN KEY (target_id) REFERENCES targets (id) ON DELETE CASCADE
);
```

**字段說明:**
- `id`: 主鍵，自增
- `target_id`: 關聯的目標 ID
- `scan_type`: 掃描類型 (nmap, webtech, paramspider, etc.)
- `scan_id`: 唯一掃描標識符
- `status`: 掃描狀態 (pending, running, completed, failed)
- `started_at`: 開始時間
- `completed_at`: 完成時間
- `duration`: 掃描耗時（秒）
- `command`: 執行的命令
- `options`: 掃描選項（JSON 格式）
- `error_message`: 錯誤信息

### scan_results (掃描結果表)
存儲掃描的詳細結果。

```sql
CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    result_type VARCHAR(100),
    data JSON NOT NULL,
    raw_output TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_id) REFERENCES scans (id) ON DELETE CASCADE
);
```

**字段說明:**
- `id`: 主鍵，自增
- `scan_id`: 關聯的掃描 ID
- `result_type`: 結果類型 (port, service, technology, etc.)
- `data`: 結構化結果數據（JSON 格式）
- `raw_output`: 原始輸出
- `created_at`: 創建時間

## 🛡️ 漏洞管理表

### vulnerabilities (漏洞記錄表)
記錄發現的安全漏洞。

```sql
CREATE TABLE vulnerabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id INTEGER NOT NULL,
    scan_id INTEGER,
    vulnerability_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(500),
    description TEXT,
    url VARCHAR(1000),
    parameter VARCHAR(200),
    payload TEXT,
    evidence TEXT,
    remediation TEXT,
    cvss_score DECIMAL(3,1),
    cve_id VARCHAR(50),
    status VARCHAR(50) DEFAULT 'open',
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    verified_at DATETIME,
    fixed_at DATETIME,
    FOREIGN KEY (target_id) REFERENCES targets (id) ON DELETE CASCADE,
    FOREIGN KEY (scan_id) REFERENCES scans (id) ON DELETE SET NULL
);
```

**字段說明:**
- `vulnerability_type`: 漏洞類型 (xss, sql_injection, etc.)
- `severity`: 嚴重程度 (critical, high, medium, low, info)
- `cvss_score`: CVSS 評分
- `cve_id`: CVE 編號
- `status`: 狀態 (open, verified, fixed, false_positive)

## 🕷️ 爬蟲相關表

### crawler (爬蟲任務表)
```sql
CREATE TABLE crawler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id INTEGER NOT NULL,
    task_id VARCHAR(200) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    depth INTEGER DEFAULT 3,
    max_pages INTEGER DEFAULT 100,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    pages_crawled INTEGER DEFAULT 0,
    links_found INTEGER DEFAULT 0,
    forms_found INTEGER DEFAULT 0,
    images_found INTEGER DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY (target_id) REFERENCES targets (id) ON DELETE CASCADE
);
```

### crawler_links (爬取鏈接表)
```sql
CREATE TABLE crawler_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawler_id INTEGER NOT NULL,
    url VARCHAR(1000) NOT NULL,
    title VARCHAR(500),
    status_code INTEGER,
    content_type VARCHAR(100),
    content_length INTEGER,
    response_time DECIMAL(10,3),
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crawler_id) REFERENCES crawler (id) ON DELETE CASCADE
);
```

### crawler_forms (表單數據表)
```sql
CREATE TABLE crawler_forms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawler_id INTEGER NOT NULL,
    url VARCHAR(1000) NOT NULL,
    method VARCHAR(10),
    action VARCHAR(1000),
    fields JSON,
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crawler_id) REFERENCES crawler (id) ON DELETE CASCADE
);
```

### crawler_images (圖片資源表)
```sql
CREATE TABLE crawler_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawler_id INTEGER NOT NULL,
    url VARCHAR(1000) NOT NULL,
    src VARCHAR(1000),
    alt VARCHAR(500),
    size_bytes INTEGER,
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crawler_id) REFERENCES crawler (id) ON DELETE CASCADE
);
```

### crawler_resources (其他資源表)
```sql
CREATE TABLE crawler_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawler_id INTEGER NOT NULL,
    url VARCHAR(1000) NOT NULL,
    resource_type VARCHAR(100),
    src VARCHAR(1000),
    size_bytes INTEGER,
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crawler_id) REFERENCES crawler (id) ON DELETE CASCADE
);
```

## 📋 系統管理表

### system_logs (系統日誌表)
```sql
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level VARCHAR(20) NOT NULL,
    logger VARCHAR(100),
    message TEXT NOT NULL,
    module VARCHAR(100),
    function VARCHAR(100),
    line_number INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    extra_data JSON
);
```

### configurations (系統配置表)
```sql
CREATE TABLE configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(200) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    category VARCHAR(100),
    data_type VARCHAR(50) DEFAULT 'string',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🔗 表關係圖

```
targets (1) ──────── (N) scans
   │                    │
   │                    └── (N) scan_results
   │
   ├── (N) vulnerabilities
   │
   └── (N) crawler
           ├── (N) crawler_links
           ├── (N) crawler_forms
           ├── (N) crawler_images
           └── (N) crawler_resources
```

## 📝 索引設計

### 性能優化索引
```sql
-- 目標表索引
CREATE INDEX idx_targets_url ON targets(url);
CREATE INDEX idx_targets_status ON targets(status);
CREATE INDEX idx_targets_created_at ON targets(created_at);

-- 掃描表索引
CREATE INDEX idx_scans_target_id ON scans(target_id);
CREATE INDEX idx_scans_scan_type ON scans(scan_type);
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_scans_started_at ON scans(started_at);

-- 掃描結果表索引
CREATE INDEX idx_scan_results_scan_id ON scan_results(scan_id);
CREATE INDEX idx_scan_results_result_type ON scan_results(result_type);

-- 漏洞表索引
CREATE INDEX idx_vulnerabilities_target_id ON vulnerabilities(target_id);
CREATE INDEX idx_vulnerabilities_severity ON vulnerabilities(severity);
CREATE INDEX idx_vulnerabilities_type ON vulnerabilities(vulnerability_type);
CREATE INDEX idx_vulnerabilities_status ON vulnerabilities(status);

-- 爬蟲表索引
CREATE INDEX idx_crawler_target_id ON crawler(target_id);
CREATE INDEX idx_crawler_status ON crawler(status);
CREATE INDEX idx_crawler_links_crawler_id ON crawler_links(crawler_id);
CREATE INDEX idx_crawler_links_url ON crawler_links(url);
```

## 🔧 數據庫操作

### 常用查詢示例

#### 獲取目標的最新掃描
```sql
SELECT s.*, t.name as target_name
FROM scans s
JOIN targets t ON s.target_id = t.id
WHERE s.target_id = ?
ORDER BY s.started_at DESC
LIMIT 1;
```

#### 統計漏洞分佈
```sql
SELECT 
    severity,
    COUNT(*) as count
FROM vulnerabilities
WHERE target_id = ? AND status = 'open'
GROUP BY severity
ORDER BY 
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        WHEN 'info' THEN 5
    END;
```

#### 獲取掃描統計
```sql
SELECT 
    scan_type,
    COUNT(*) as total_scans,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_scans,
    AVG(duration) as avg_duration
FROM scans
WHERE target_id = ?
GROUP BY scan_type;
```

## 🛠️ 數據庫維護

### 備份策略
```bash
# SQLite 備份
cp instance/c2.db instance/backups/c2_$(date +%Y%m%d_%H%M%S).db

# PostgreSQL 備份
pg_dump c2_database > backup_$(date +%Y%m%d_%H%M%S).sql

# MySQL 備份
mysqldump c2_database > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 數據清理
```sql
-- 清理舊的掃描記錄（保留最近 30 天）
DELETE FROM scans 
WHERE started_at < datetime('now', '-30 days');

-- 清理已修復的漏洞（保留最近 90 天）
DELETE FROM vulnerabilities 
WHERE status = 'fixed' AND fixed_at < datetime('now', '-90 days');

-- 清理系統日誌（保留最近 7 天）
DELETE FROM system_logs 
WHERE timestamp < datetime('now', '-7 days');
```

### 性能監控
```sql
-- 檢查表大小
SELECT 
    name,
    COUNT(*) as row_count
FROM sqlite_master 
WHERE type = 'table'
GROUP BY name;

-- 檢查索引使用情況
EXPLAIN QUERY PLAN 
SELECT * FROM scans WHERE target_id = 1;
```

## 🔄 數據遷移

### Flask-Migrate 命令
```bash
# 初始化遷移
flask db init

# 創建遷移文件
flask db migrate -m "描述變更"

# 應用遷移
flask db upgrade

# 回滾遷移
flask db downgrade
```

### 自定義遷移腳本示例
```python
"""添加新字段

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 添加新字段
    op.add_column('targets', sa.Column('priority', sa.Integer(), default=1))
    
    # 創建新索引
    op.create_index('idx_targets_priority', 'targets', ['priority'])

def downgrade():
    # 刪除索引
    op.drop_index('idx_targets_priority', 'targets')
    
    # 刪除字段
    op.drop_column('targets', 'priority')
```

---

如需更多數據庫相關信息，請參考 SQLAlchemy 官方文檔或聯繫開發團隊。 