# API 參考文檔

C2 平台提供了豐富的 RESTful API 接口，支持各種安全測試和管理功能。

## 🔗 基礎信息

### 基礎 URL
```
http://localhost:5000/api/v1
```

### 認證方式
目前系統已簡化，無需用戶認證即可訪問所有 API。

### 響應格式
所有 API 響應均為 JSON 格式：
```json
{
    "success": true,
    "data": {},
    "message": "操作成功",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### 錯誤響應
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "錯誤描述"
    },
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## 📋 目標管理 API

### 獲取目標列表
```http
GET /api/v1/targets
```

**響應示例:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "url": "https://example.com",
            "name": "測試目標",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z",
            "last_scan": "2024-01-01T12:00:00Z"
        }
    ]
}
```

### 添加新目標
```http
POST /api/v1/targets
Content-Type: application/json

{
    "url": "https://example.com",
    "name": "目標名稱",
    "description": "目標描述"
}
```

### 獲取目標詳情
```http
GET /api/v1/targets/{target_id}
```

### 更新目標
```http
PUT /api/v1/targets/{target_id}
Content-Type: application/json

{
    "name": "新名稱",
    "description": "新描述"
}
```

### 刪除目標
```http
DELETE /api/v1/targets/{target_id}
```

## 🔍 掃描 API

### 啟動 Nmap 掃描
```http
POST /api/v1/scan/nmap
Content-Type: application/json

{
    "target_id": 1,
    "scan_type": "tcp_syn",
    "ports": "1-1000",
    "options": ["-sV", "-O"]
}
```

**響應示例:**
```json
{
    "success": true,
    "data": {
        "scan_id": "scan_123456",
        "status": "running",
        "target": "https://example.com"
    }
}
```

### 獲取掃描狀態
```http
GET /api/v1/scan/{scan_id}/status
```

### 獲取掃描結果
```http
GET /api/v1/scan/{scan_id}/results
```

### Web 技術識別
```http
POST /api/v1/scan/webtech
Content-Type: application/json

{
    "target_id": 1,
    "deep_scan": true
}
```

### 參數爬取 (ParamSpider)
```http
POST /api/v1/scan/paramspider
Content-Type: application/json

{
    "target_id": 1,
    "depth": 3,
    "exclude_extensions": [".jpg", ".png", ".css"]
}
```

### 證書透明度查詢
```http
POST /api/v1/scan/crtsh
Content-Type: application/json

{
    "domain": "example.com",
    "include_subdomains": true
}
```

## 🛡️ 漏洞掃描 API

### 啟動漏洞掃描
```http
POST /api/v1/vulnerability/scan
Content-Type: application/json

{
    "target_id": 1,
    "scan_types": ["xss", "sql_injection", "directory_traversal"],
    "intensity": "medium"
}
```

### 獲取漏洞報告
```http
GET /api/v1/vulnerability/report/{target_id}
```

**響應示例:**
```json
{
    "success": true,
    "data": {
        "target_id": 1,
        "vulnerabilities": [
            {
                "type": "xss",
                "severity": "high",
                "url": "https://example.com/search",
                "parameter": "q",
                "payload": "<script>alert(1)</script>",
                "description": "反射型 XSS 漏洞"
            }
        ],
        "summary": {
            "total": 5,
            "high": 1,
            "medium": 2,
            "low": 2
        }
    }
}
```

## 📊 數據分析 API

### 獲取掃描統計
```http
GET /api/v1/analytics/scan-stats
```

### 獲取漏洞趨勢
```http
GET /api/v1/analytics/vulnerability-trends?days=30
```

### 生成報告
```http
POST /api/v1/reports/generate
Content-Type: application/json

{
    "target_id": 1,
    "report_type": "comprehensive",
    "format": "pdf"
}
```

## 🔧 系統管理 API

### 獲取系統狀態
```http
GET /api/v1/system/status
```

**響應示例:**
```json
{
    "success": true,
    "data": {
        "version": "1.0.0",
        "uptime": 3600,
        "active_scans": 2,
        "database_status": "healthy",
        "services": {
            "flaresolverr": "running",
            "docker": "available"
        }
    }
}
```

### 獲取系統配置
```http
GET /api/v1/system/config
```

### 更新系統配置
```http
PUT /api/v1/system/config
Content-Type: application/json

{
    "max_concurrent_scans": 5,
    "scan_timeout": 3600,
    "enable_notifications": true
}
```

## 📁 文件管理 API

### 上傳文件
```http
POST /api/v1/files/upload
Content-Type: multipart/form-data

file: [binary data]
target_id: 1
file_type: wordlist
```

### 下載掃描結果
```http
GET /api/v1/files/download/{file_id}
```

### 獲取文件列表
```http
GET /api/v1/files?target_id=1&file_type=results
```

## 🔄 WebSocket API

### 實時掃描狀態
```javascript
// 連接 WebSocket
const ws = new WebSocket('ws://localhost:5000/ws/scan-status');

// 監聽掃描狀態更新
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('掃描狀態:', data);
};

// 訂閱特定掃描
ws.send(JSON.stringify({
    action: 'subscribe',
    scan_id: 'scan_123456'
}));
```

### 實時日誌
```javascript
const ws = new WebSocket('ws://localhost:5000/ws/logs');

ws.onmessage = function(event) {
    const logEntry = JSON.parse(event.data);
    console.log('日誌:', logEntry);
};
```

## 📝 API 使用示例

### Python 示例
```python
import requests
import json

# 基礎配置
BASE_URL = "http://localhost:5000/api/v1"
headers = {"Content-Type": "application/json"}

# 添加目標
target_data = {
    "url": "https://example.com",
    "name": "測試目標"
}
response = requests.post(f"{BASE_URL}/targets", 
                        json=target_data, 
                        headers=headers)
target = response.json()["data"]

# 啟動掃描
scan_data = {
    "target_id": target["id"],
    "scan_type": "tcp_syn"
}
response = requests.post(f"{BASE_URL}/scan/nmap", 
                        json=scan_data, 
                        headers=headers)
scan = response.json()["data"]

# 檢查掃描狀態
response = requests.get(f"{BASE_URL}/scan/{scan['scan_id']}/status")
status = response.json()["data"]
print(f"掃描狀態: {status['status']}")
```

### JavaScript 示例
```javascript
// 使用 fetch API
async function addTarget(url, name) {
    const response = await fetch('/api/v1/targets', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url, name })
    });
    
    const result = await response.json();
    return result.data;
}

// 啟動掃描
async function startScan(targetId) {
    const response = await fetch('/api/v1/scan/nmap', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            target_id: targetId,
            scan_type: 'tcp_syn'
        })
    });
    
    return await response.json();
}
```

### cURL 示例
```bash
# 添加目標
curl -X POST http://localhost:5000/api/v1/targets \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "name": "測試目標"}'

# 啟動掃描
curl -X POST http://localhost:5000/api/v1/scan/nmap \
  -H "Content-Type: application/json" \
  -d '{"target_id": 1, "scan_type": "tcp_syn"}'

# 獲取掃描結果
curl http://localhost:5000/api/v1/scan/scan_123456/results
```

## 🚨 錯誤代碼

| 錯誤代碼 | HTTP 狀態 | 描述 |
|---------|----------|------|
| `TARGET_NOT_FOUND` | 404 | 目標不存在 |
| `SCAN_IN_PROGRESS` | 409 | 掃描正在進行中 |
| `INVALID_URL` | 400 | 無效的 URL 格式 |
| `SCAN_FAILED` | 500 | 掃描執行失敗 |
| `RATE_LIMIT_EXCEEDED` | 429 | 請求頻率超限 |
| `INSUFFICIENT_RESOURCES` | 503 | 系統資源不足 |

## 📈 API 限制

- **請求頻率**: 每分鐘最多 100 次請求
- **並發掃描**: 最多同時進行 5 個掃描任務
- **文件上傳**: 單個文件最大 100MB
- **響應超時**: 30 秒

## 🔄 版本控制

API 使用語義化版本控制，當前版本為 `v1`。

### 版本兼容性
- **向後兼容**: 小版本更新保持向後兼容
- **重大變更**: 大版本更新可能包含破壞性變更
- **廢棄通知**: 廢棄的 API 會提前 6 個月通知

---

如需更多信息或遇到問題，請查看項目文檔或提交 Issue。 