// 全局變量
let currentTargetId = null;
let currentScanType = 'common';
let scanInterval = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 隱藏載入畫面
    document.getElementById('loading').style.display = 'none';
    document.getElementById('nmap-app').style.display = 'block';
    
    // 如果 URL 中有 target_id，自動設置
    const urlParams = new URLSearchParams(window.location.search);
    const targetId = urlParams.get('target_id');
    if (targetId && targetId !== '') {
        document.getElementById('target-id').value = targetId;
        setTarget();
    }
});

// 顯示通知
function showNotification(title, message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-title">${title}</div>
        <div class="notification-message">${message}</div>
    `;
    
    container.appendChild(notification);
    
    // 3秒後自動移除
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// 設置目標
function setTarget() {
    const targetId = document.getElementById('target-id').value;
    if (!targetId || isNaN(targetId) || parseInt(targetId) <= 0) {
        showNotification('錯誤', '請輸入有效的目標 ID', 'error');
        return;
    }
    
    currentTargetId = parseInt(targetId);
    
    // 顯示掃描控制面板
    document.getElementById('target-selection').classList.add('hidden');
    document.getElementById('scan-control').classList.remove('hidden');
    
    // 更新 URL
    const newUrl = new URL(window.location);
    newUrl.searchParams.set('target_id', currentTargetId);
    window.history.pushState({}, '', newUrl);
    
    // 獲取初始狀態
    refreshStatus();
    loadHistory();
    
    showNotification('成功', `已設置目標 ID: ${currentTargetId}`, 'success');
}

// 選擇掃描類型
function selectScanType(type) {
    currentScanType = type;
    
    // 更新 UI
    document.querySelectorAll('.scan-type-chip').forEach(chip => {
        chip.classList.remove('active');
    });
    document.querySelector(`[data-type="${type}"]`).classList.add('active');
    
    // 更新預計時間
    const estimatedTime = type === 'common' ? '30-120秒' : '2-5分鐘';
    document.getElementById('estimated-time').textContent = estimatedTime;
}

// 開始掃描
async function startScan() {
    if (!currentTargetId) {
        showNotification('錯誤', '請先設置目標 ID', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/nmap/scan/${currentTargetId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ scan_type: currentScanType }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateScanStatus('scanning', '掃描正在進行中...');
            document.getElementById('start-scan-btn').disabled = true;
            document.getElementById('scan-progress').classList.remove('hidden');
            
            // 開始輪詢狀態
            startStatusPolling();
            
            showNotification('掃描已開始', `正在對目標 ${currentTargetId} 執行${currentScanType === 'common' ? '常用端口' : '完整'}掃描`, 'success');
        } else {
            showNotification('掃描失敗', data.message, 'error');
        }
    } catch (error) {
        showNotification('掃描失敗', '啟動掃描時發生錯誤', 'error');
        console.error('掃描錯誤:', error);
    }
}

// 更新掃描狀態
function updateScanStatus(status, message) {
    const statusElement = document.getElementById('scan-status');
    const messageElement = document.getElementById('scan-message');
    
    statusElement.className = 'status-chip';
    
    switch (status) {
        case 'scanning':
            statusElement.classList.add('status-scanning');
            statusElement.textContent = '掃描中';
            break;
        case 'completed':
            statusElement.classList.add('status-completed');
            statusElement.textContent = '已完成';
            break;
        case 'error':
            statusElement.classList.add('status-error');
            statusElement.textContent = '錯誤';
            break;
        default:
            statusElement.textContent = '未開始';
    }
    
    messageElement.textContent = message || '';
}

// 開始狀態輪詢
function startStatusPolling() {
    if (scanInterval) {
        clearInterval(scanInterval);
    }
    
    scanInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/nmap/status/${currentTargetId}?scan_type=${currentScanType}`);
            const data = await response.json();
            
            if (data.success) {
                updateScanStatus(data.status, data.message);
                
                if (data.status === 'completed') {
                    // 掃描完成
                    clearInterval(scanInterval);
                    document.getElementById('start-scan-btn').disabled = false;
                    document.getElementById('scan-progress').classList.add('hidden');
                    
                    // 載入結果
                    loadResults();
                    loadHistory();
                    
                    showNotification('掃描完成', '掃描已成功完成，正在載入結果', 'success');
                } else if (data.status === 'error') {
                    // 掃描錯誤
                    clearInterval(scanInterval);
                    document.getElementById('start-scan-btn').disabled = false;
                    document.getElementById('scan-progress').classList.add('hidden');
                    
                    showNotification('掃描失敗', '掃描過程中發生錯誤', 'error');
                }
            }
        } catch (error) {
            console.error('狀態查詢錯誤:', error);
        }
    }, 3000);
}

// 刷新狀態
async function refreshStatus() {
    if (!currentTargetId) return;
    
    try {
        const response = await fetch(`/api/nmap/status/${currentTargetId}?scan_type=${currentScanType}`);
        const data = await response.json();
        
        if (data.success) {
            updateScanStatus(data.status, data.message);
            
            if (data.status === 'completed') {
                loadResults();
            }
        }
    } catch (error) {
        console.error('狀態刷新錯誤:', error);
    }
}

// 載入掃描結果
async function loadResults() {
    if (!currentTargetId) return;
    
    try {
        const response = await fetch(`/api/nmap/result/${currentTargetId}?scan_type=${currentScanType}`);
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success) {
                displayResults(data.result);
                document.getElementById('scan-results').classList.remove('hidden');
            }
        } else if (response.status === 404) {
            // 結果尚未準備好
            console.log('掃描結果尚未準備好');
        }
    } catch (error) {
        console.error('載入結果錯誤:', error);
    }
}

// 顯示掃描結果
function displayResults(result) {
    // 顯示統計信息
    if (result.port_statistics) {
        const stats = result.port_statistics;
        const statsContainer = document.getElementById('port-statistics');
        
        statsContainer.innerHTML = `
            <div class="card stat-card">
                <div class="stat-number stat-open">${stats.open}</div>
                <div class="stat-label">開放端口</div>
            </div>
            <div class="card stat-card">
                <div class="stat-number stat-filtered">${stats.filtered}</div>
                <div class="stat-label">過濾端口</div>
            </div>
            <div class="card stat-card">
                <div class="stat-number stat-closed">${stats.closed}</div>
                <div class="stat-label">關閉端口</div>
            </div>
            <div class="card stat-card">
                <div class="stat-number stat-total">${stats.total}</div>
                <div class="stat-label">總端口數</div>
            </div>
        `;
    }
    
    // 顯示端口詳情
    if (result.ports) {
        const tableBody = document.getElementById('port-table-body');
        
        // 按狀態排序：開放 > 過濾 > 關閉
        const sortedPorts = result.ports.sort((a, b) => {
            const order = { 'open': 0, 'filtered': 1, 'closed': 2 };
            return order[a.state] - order[b.state];
        });
        
        tableBody.innerHTML = sortedPorts.map(port => `
            <tr>
                <td><strong>${port.port}</strong></td>
                <td><span class="port-state port-state-${port.state}">${port.state}</span></td>
                <td>${port.service || '未知'}</td>
                <td>${port.version || '-'}</td>
                <td>${port.protocol || 'tcp'}</td>
            </tr>
        `).join('');
    }
}

// 載入掃描歷史
async function loadHistory() {
    if (!currentTargetId) return;
    
    try {
        const response = await fetch(`/api/nmap/history/${currentTargetId}`);
        const data = await response.json();
        
        if (data.success && data.history.length > 0) {
            displayHistory(data.history);
            document.getElementById('scan-history').classList.remove('hidden');
        }
    } catch (error) {
        console.error('載入歷史錯誤:', error);
    }
}

// 顯示掃描歷史
function displayHistory(history) {
    const tableBody = document.getElementById('history-table-body');
    
    tableBody.innerHTML = history.map(record => `
        <tr>
            <td>${record.scan_time}</td>
            <td><span class="scan-type-chip">${record.scan_type === 'common' ? '常用端口' : '完整掃描'}</span></td>
            <td><span class="port-state port-state-${record.host_status === 'up' ? 'open' : 'closed'}">${record.host_status}</span></td>
            <td>${record.port_count}</td>
            <td><strong style="color: #4caf50;">${record.open_ports}</strong></td>
        </tr>
    `).join('');
}

// 頁面卸載時清理
window.addEventListener('beforeunload', function() {
    if (scanInterval) {
        clearInterval(scanInterval);
    }
}); 