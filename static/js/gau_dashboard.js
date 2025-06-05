// 全局變量
let currentTargetId = null;
let scanInterval = null;
let allUrls = [];
let currentPage = 1;
let totalPages = 1;
let currentCategory = 'all';
let currentSearch = '';
let urlCategories = {};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 隱藏載入畫面
    document.getElementById('loading').style.display = 'none';
    document.getElementById('gau-app').style.display = 'block';
    
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
    
    // 獲取掃描選項
    const options = {
        threads: parseInt(document.getElementById('threads').value) || 50,
        providers: document.getElementById('providers').value,
        blacklist: document.getElementById('blacklist').value,
        verbose: document.getElementById('verbose').checked
    };
    
    try {
        const response = await fetch(`/api/gau/scan/${currentTargetId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(options)
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateScanStatus('scanning', '掃描正在進行中...');
            document.getElementById('start-scan-btn').disabled = true;
            document.getElementById('scan-progress').classList.remove('hidden');
            
            // 開始輪詢狀態
            startStatusPolling();
            
            showNotification('掃描已開始', `正在對目標 ${currentTargetId} 執行 Gau URL 掃描`, 'success');
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
            const response = await fetch(`/api/gau/status/${currentTargetId}`);
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
        const response = await fetch(`/api/gau/status/${currentTargetId}`);
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
async function loadResults(page = 1, category = 'all', search = '') {
    if (!currentTargetId) return;
    
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: 50,
            category: category,
            search: search
        });
        
        const response = await fetch(`/api/gau/result/${currentTargetId}?${params}`);
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
    allUrls = result.urls || [];
    urlCategories = result.categories || {};
    currentPage = result.pagination?.page || 1;
    totalPages = result.pagination?.total_pages || 1;
    
    // 顯示統計信息
    displayStatistics(result);
    
    // 顯示分類過濾器
    displayCategoryFilters();
    
    // 顯示 URL 表格
    displayUrlTable(allUrls);
    
    // 顯示分頁控制
    displayPagination();
}

// 顯示統計信息
function displayStatistics(result) {
    const statsContainer = document.getElementById('url-statistics');
    const categories = result.categories || {};
    
    statsContainer.innerHTML = `
        <div class="stat-card">
            <div class="stat-number">${categories.all || 0}</div>
            <div class="stat-label">總 URL 數</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${categories.js || 0}</div>
            <div class="stat-label">JavaScript</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${categories.api || 0}</div>
            <div class="stat-label">API 端點</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${categories.image || 0}</div>
            <div class="stat-label">圖片文件</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${categories.css || 0}</div>
            <div class="stat-label">CSS 文件</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${categories.doc || 0}</div>
            <div class="stat-label">文檔文件</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${categories.other || 0}</div>
            <div class="stat-label">其他</div>
        </div>
    `;
}

// 顯示分類過濾器
function displayCategoryFilters() {
    const filtersContainer = document.getElementById('category-filters');
    const categories = [
        { key: 'all', label: '全部', icon: '🔗' },
        { key: 'js', label: 'JavaScript', icon: '📜' },
        { key: 'api', label: 'API', icon: '🔌' },
        { key: 'image', label: '圖片', icon: '🖼️' },
        { key: 'css', label: 'CSS', icon: '🎨' },
        { key: 'doc', label: '文檔', icon: '📄' },
        { key: 'other', label: '其他', icon: '📦' }
    ];
    
    filtersContainer.innerHTML = categories.map(cat => `
        <button class="category-btn ${currentCategory === cat.key ? 'active' : ''}" 
                onclick="filterByCategory('${cat.key}')">
            ${cat.icon} ${cat.label} (${urlCategories[cat.key] || 0})
        </button>
    `).join('');
}

// 按分類過濾
function filterByCategory(category) {
    currentCategory = category;
    currentPage = 1;
    loadResults(currentPage, currentCategory, currentSearch);
}

// 顯示 URL 表格
function displayUrlTable(urls) {
    const tbody = document.getElementById('url-table-body');
    tbody.innerHTML = '';
    
    if (!urls || urls.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #666;">未找到 URL</td></tr>';
        return;
    }
    
    urls.forEach((url, index) => {
        const row = document.createElement('tr');
        
        // 判斷 URL 類型
        let urlType = '其他';
        const urlLower = url.toLowerCase();
        if (urlLower.includes('.js') || urlLower.includes('javascript')) {
            urlType = 'JavaScript';
        } else if (urlLower.includes('/api/') || urlLower.includes('.json') || urlLower.includes('.xml')) {
            urlType = 'API';
        } else if (urlLower.includes('.png') || urlLower.includes('.jpg') || urlLower.includes('.gif')) {
            urlType = '圖片';
        } else if (urlLower.includes('.css')) {
            urlType = 'CSS';
        } else if (urlLower.includes('.pdf') || urlLower.includes('.doc')) {
            urlType = '文檔';
        }
        
        const startIndex = (currentPage - 1) * 50;
        
        row.innerHTML = `
            <td>${startIndex + index + 1}</td>
            <td class="url-cell" title="${url}">${url}</td>
            <td>${urlType}</td>
            <td>
                <button class="copy-button" onclick="copyUrl('${url.replace(/'/g, "\\'")}', this)">複製</button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// 顯示分頁控制
function displayPagination() {
    const paginationContainer = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }
    
    let paginationHtml = '';
    
    // 上一頁按鈕
    paginationHtml += `
        <button onclick="changePage(${currentPage - 1})" ${currentPage <= 1 ? 'disabled' : ''}>
            ← 上一頁
        </button>
    `;
    
    // 頁碼按鈕
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        paginationHtml += `<button onclick="changePage(1)">1</button>`;
        if (startPage > 2) {
            paginationHtml += `<span>...</span>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <button onclick="changePage(${i})" ${i === currentPage ? 'class="current-page"' : ''}>
                ${i}
            </button>
        `;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHtml += `<span>...</span>`;
        }
        paginationHtml += `<button onclick="changePage(${totalPages})">${totalPages}</button>`;
    }
    
    // 下一頁按鈕
    paginationHtml += `
        <button onclick="changePage(${currentPage + 1})" ${currentPage >= totalPages ? 'disabled' : ''}>
            下一頁 →
        </button>
    `;
    
    paginationContainer.innerHTML = paginationHtml;
}

// 切換頁面
function changePage(page) {
    if (page < 1 || page > totalPages || page === currentPage) return;
    
    currentPage = page;
    loadResults(currentPage, currentCategory, currentSearch);
}

// 過濾 URL
function filterUrls() {
    const searchTerm = document.getElementById('url-search').value;
    currentSearch = searchTerm;
    currentPage = 1;
    loadResults(currentPage, currentCategory, currentSearch);
}

// 複製 URL
function copyUrl(url, button) {
    navigator.clipboard.writeText(url).then(() => {
        const originalText = button.textContent;
        button.textContent = '已複製';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
        
        showNotification('複製成功', `已複製 URL: ${url.substring(0, 50)}...`, 'success');
    }).catch(err => {
        showNotification('複製失敗', '無法複製到剪貼板', 'error');
    });
}

// 導出 URL
function exportUrls(format) {
    if (!allUrls || allUrls.length === 0) {
        showNotification('導出失敗', '沒有可導出的 URL', 'error');
        return;
    }
    
    let content = '';
    let filename = '';
    let mimeType = '';
    
    if (format === 'txt') {
        content = allUrls.join('\n');
        filename = `gau_urls_${currentTargetId}_${Date.now()}.txt`;
        mimeType = 'text/plain';
    } else if (format === 'csv') {
        content = 'Index,URL,Type\n';
        allUrls.forEach((url, index) => {
            let urlType = '其他';
            const urlLower = url.toLowerCase();
            if (urlLower.includes('.js') || urlLower.includes('javascript')) {
                urlType = 'JavaScript';
            } else if (urlLower.includes('/api/') || urlLower.includes('.json')) {
                urlType = 'API';
            } else if (urlLower.includes('.png') || urlLower.includes('.jpg')) {
                urlType = '圖片';
            } else if (urlLower.includes('.css')) {
                urlType = 'CSS';
            } else if (urlLower.includes('.pdf') || urlLower.includes('.doc')) {
                urlType = '文檔';
            }
            content += `${index + 1},"${url}","${urlType}"\n`;
        });
        filename = `gau_urls_${currentTargetId}_${Date.now()}.csv`;
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
    
    showNotification('導出成功', `已導出 ${allUrls.length} 個 URL`, 'success');
}

// 複製所有 URL
function copyAllUrls() {
    if (!allUrls || allUrls.length === 0) {
        showNotification('複製失敗', '沒有可複製的 URL', 'error');
        return;
    }
    
    const content = allUrls.join('\n');
    navigator.clipboard.writeText(content).then(() => {
        showNotification('複製成功', `已複製 ${allUrls.length} 個 URL 到剪貼板`, 'success');
    }).catch(err => {
        showNotification('複製失敗', '無法複製到剪貼板', 'error');
    });
}

// 下載完整文件
function downloadFile() {
    if (!currentTargetId) {
        showNotification('下載失敗', '請先設置目標 ID', 'error');
        return;
    }
    
    const downloadUrl = `/api/gau/file/${currentTargetId}`;
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `gau_results_${currentTargetId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    showNotification('下載開始', '正在下載完整的掃描結果文件', 'success');
}

// 載入歷史記錄
async function loadHistory() {
    if (!currentTargetId) return;
    
    try {
        const response = await fetch(`/api/gau/history/${currentTargetId}`);
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
        const scanTime = record.scan_time ? new Date(record.scan_time * 1000).toLocaleString() : '-';
        const statusText = record.status === 'completed' ? '成功' : 
                          record.status === 'failed' ? '失敗' : 
                          record.status === 'scanning' ? '進行中' : '未知';
        const errorMsg = record.error_message || '-';
        
        row.innerHTML = `
            <td>${scanTime}</td>
            <td>${statusText}</td>
            <td>${record.url_count || 0}</td>
            <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${errorMsg}</td>
        `;
        
        tbody.appendChild(row);
    });
} 