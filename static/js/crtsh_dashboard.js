// 全局變量
let currentTargetId = null;
let scanInterval = null;
let allDomains = [];

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 隱藏載入畫面
    document.getElementById('loading').style.display = 'none';
    document.getElementById('crtsh-app').style.display = 'block';
    
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

// 開始掃描
async function startScan() {
    if (!currentTargetId) {
        showNotification('錯誤', '請先設置目標 ID', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/crtsh/scan/${currentTargetId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateScanStatus('scanning', '掃描正在進行中...');
            document.getElementById('start-scan-btn').disabled = true;
            document.getElementById('scan-progress').classList.remove('hidden');
            
            // 開始輪詢狀態
            startStatusPolling();
            
            showNotification('掃描已開始', `正在對目標 ${currentTargetId} 執行 crt.sh 子域名掃描`, 'success');
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
            const response = await fetch(`/api/crtsh/status/${currentTargetId}`);
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
        const response = await fetch(`/api/crtsh/status/${currentTargetId}`);
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

// 載入結果
async function loadResults() {
    if (!currentTargetId) return;
    
    try {
        const response = await fetch(`/api/crtsh/result/${currentTargetId}`);
        const data = await response.json();
        
        if (data.success && data.result) {
            displayResults(data.result);
            document.getElementById('scan-results').classList.remove('hidden');
        } else {
            showNotification('載入失敗', '無法載入掃描結果', 'error');
        }
    } catch (error) {
        console.error('載入結果錯誤:', error);
        showNotification('載入失敗', '載入結果時發生錯誤', 'error');
    }
}

// 顯示結果
function displayResults(result) {
    allDomains = result.domains || [];
    
    // 顯示統計信息
    const statsContainer = document.getElementById('domain-statistics');
    const stats = result.domain_statistics || {
        total: allDomains.length,
        unique_subdomains: allDomains.length,
        wildcard_domains: 0,
        main_domain_count: allDomains.length
    };
    
    statsContainer.innerHTML = `
        <div class="stat-card">
            <div class="stat-number">${stats.total}</div>
            <div class="stat-label">總域名數</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${stats.unique_subdomains}</div>
            <div class="stat-label">唯一子域名</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${stats.wildcard_domains}</div>
            <div class="stat-label">通配符域名</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${stats.main_domain_count}</div>
            <div class="stat-label">主域名</div>
        </div>
    `;
    
    // 顯示域名列表
    displayDomainTable(allDomains);
}

// 顯示域名表格
function displayDomainTable(domains) {
    const tbody = document.getElementById('domain-table-body');
    tbody.innerHTML = '';
    
    if (!domains || domains.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #666;">未找到域名</td></tr>';
        return;
    }
    
    domains.forEach((domain, index) => {
        const row = document.createElement('tr');
        
        // 判斷域名類型
        let domainType = '主域名';
        if (domain.startsWith('*.')) {
            domainType = '通配符';
        } else if (domain.includes('.') && domain.split('.').length > 2) {
            domainType = '子域名';
        }
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td class="domain-cell">${domain}</td>
            <td>${domainType}</td>
            <td>
                <button class="copy-button" onclick="copyDomain('${domain}', this)">複製</button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// 複製域名
function copyDomain(domain, button) {
    navigator.clipboard.writeText(domain).then(() => {
        const originalText = button.textContent;
        button.textContent = '已複製';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
        
        showNotification('複製成功', `已複製域名: ${domain}`, 'success');
    }).catch(err => {
        showNotification('複製失敗', '無法複製到剪貼板', 'error');
    });
}

// 過濾域名
function filterDomains() {
    const searchTerm = document.getElementById('domain-search').value.toLowerCase();
    const filteredDomains = allDomains.filter(domain => 
        domain.toLowerCase().includes(searchTerm)
    );
    displayDomainTable(filteredDomains);
}

// 導出域名
function exportDomains(format) {
    if (!allDomains || allDomains.length === 0) {
        showNotification('導出失敗', '沒有可導出的域名', 'error');
        return;
    }
    
    let content = '';
    let filename = '';
    let mimeType = '';
    
    if (format === 'txt') {
        content = allDomains.join('\n');
        filename = `crtsh_domains_${currentTargetId}_${Date.now()}.txt`;
        mimeType = 'text/plain';
    } else if (format === 'csv') {
        content = 'Index,Domain,Type\n';
        allDomains.forEach((domain, index) => {
            let domainType = '主域名';
            if (domain.startsWith('*.')) {
                domainType = '通配符';
            } else if (domain.includes('.') && domain.split('.').length > 2) {
                domainType = '子域名';
            }
            content += `${index + 1},"${domain}","${domainType}"\n`;
        });
        filename = `crtsh_domains_${currentTargetId}_${Date.now()}.csv`;
        mimeType = 'text/csv';
    }
    
    // 創建下載鏈接
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    showNotification('導出成功', `已導出 ${allDomains.length} 個域名`, 'success');
}

// 複製所有域名
function copyAllDomains() {
    if (!allDomains || allDomains.length === 0) {
        showNotification('複製失敗', '沒有可複製的域名', 'error');
        return;
    }
    
    const content = allDomains.join('\n');
    navigator.clipboard.writeText(content).then(() => {
        showNotification('複製成功', `已複製 ${allDomains.length} 個域名到剪貼板`, 'success');
    }).catch(err => {
        showNotification('複製失敗', '無法複製到剪貼板', 'error');
    });
}

// 載入歷史記錄
async function loadHistory() {
    if (!currentTargetId) return;
    
    try {
        const response = await fetch(`/api/crtsh/history/${currentTargetId}`);
        const data = await response.json();
        
        if (data.success) {
            displayHistory(data.history);
            document.getElementById('scan-history').classList.remove('hidden');
        }
    } catch (error) {
        console.error('載入歷史錯誤:', error);
    }
}

// 顯示歷史記錄
function displayHistory(history) {
    const tbody = document.getElementById('history-table-body');
    tbody.innerHTML = '';
    
    if (!history || history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #666;">暫無歷史記錄</td></tr>';
        return;
    }
    
    history.forEach(record => {
        const row = document.createElement('tr');
        const scanTime = new Date(record.scan_time * 1000).toLocaleString();
        const statusText = record.status === 'success' ? '成功' : 
                          record.status === 'failed' ? '失敗' : '進行中';
        const errorMsg = record.error_message || '-';
        
        row.innerHTML = `
            <td>${scanTime}</td>
            <td>${statusText}</td>
            <td>${record.domain_count}</td>
            <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${errorMsg}</td>
        `;
        
        tbody.appendChild(row);
    });
} 