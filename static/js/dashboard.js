document.addEventListener('DOMContentLoaded', function() {
    const targetList = document.getElementById('targetList');
    const userId = targetList.dataset.userId;

    targetList.addEventListener('click', function(event) {
        const targetId = event.target.getAttribute('data-target-id');
        
        if (event.target.classList.contains('select-target')) {
            redirectToAttackPage(userId, targetId);
        } else if (event.target.classList.contains('generate-api')) {
            generateApiKey(userId, targetId, event.target);
        } else if (event.target.classList.contains('delete-api')) {
            deleteApiKey(userId, targetId, event.target);
        } else if (event.target.classList.contains('check-api')) {
            checkApiKey(userId, targetId);
        }
    });

    function redirectToAttackPage(userId, targetId) {
        window.location.href = `/user/${userId}/attack/${targetId}`;
    }

    async function generateApiKey(userId, targetId, button) {
        try {
            const response = await fetch('/api/make_api_key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_id: userId, target_id: targetId })
            });

            const data = await response.json();
            if (data) {
                const targetElement = button.closest('li');
                const apiKeySpan = targetElement.querySelector('.api-key');
                apiKeySpan.textContent = data;
                
                // 更新按鈕顯示狀態
                button.style.display = 'none';
                targetElement.querySelector('.delete-api').style.display = 'inline-block';
                targetElement.querySelector('.check-api').style.display = 'inline-block';
                
                alert('API Key 生成成功！');
            } else {
                alert('生成 API Key 失敗：' + (data.message || '未知錯誤'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('生成 API Key 時發生錯誤');
        }
    }

    async function deleteApiKey(userId, targetId, button) {
        if (!confirm('確定要刪除此 API Key 嗎？')) {
            return;
        }

        try {
            const response = await fetch('/api/delete_api_key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_id: userId, target_id: targetId })
            });

            const data = await response.json();
            if (data) {
                const targetElement = button.closest('li');
                const apiKeySpan = targetElement.querySelector('.api-key');
                apiKeySpan.textContent = '未生成';
                
                // 更新按鈕顯示狀態
                button.style.display = 'none';
                targetElement.querySelector('.generate-api').style.display = 'inline-block';
                targetElement.querySelector('.check-api').style.display = 'none';
                
                alert('API Key 已刪除！');
            } else {
                alert('刪除 API Key 失敗：' + (data.message || '未知錯誤'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('刪除 API Key 時發生錯誤');
        }
    }

    async function checkApiKey(userId, targetId) {
        try {
            const apiKey = document.querySelector(`li[data-target-id="${targetId}"] .api-key`).textContent;
            if (apiKey === '未生成') {
                alert('請先生成 API Key');
                return;
            }
            
            const response = await fetch('/api/check_api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    user_id: userId, 
                    target_id: targetId,
                    api_key: apiKey
                })
            });

            const data = await response.json();
            if (data) {
                alert('API Key 有效！');
            } else {
                alert('API Key 無效：' + (data.message || '驗證失敗'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('檢查 API Key 時發生錯誤');
        }
    }
}); 