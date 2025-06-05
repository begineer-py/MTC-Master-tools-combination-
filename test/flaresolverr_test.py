import requests
import json
import time

def test_flaresolverr():
    """
    測試 FlareSolverr 服務並實際發送 Google 請求
    """
    # FlareSolverr 服務地址（現在只監聽本地）
    url = "http://127.0.0.1:8191/v1"
    headers = {"Content-Type": "application/json"}
    
    # 測試數據 - 請求 Google
    data = {
        "cmd": "request.get",
        "url": "https://www.google.com/",
        "maxTimeout": 60000
    }
    
    print("🚀 開始測試 FlareSolverr...")
    print(f"📡 目標 URL: {data['url']}")
    print(f"⏱️  最大超時時間: {data['maxTimeout']}ms")
    print("-" * 50)
    
    try:
        # 記錄開始時間
        start_time = time.time()
        
        # 發送請求
        print("📤 正在發送請求到 FlareSolverr...")
        response = requests.post(url, headers=headers, json=data, timeout=70)
        
        # 計算耗時
        elapsed_time = time.time() - start_time
        
        # 檢查 HTTP 狀態碼
        if response.status_code == 200:
            print(f"✅ HTTP 狀態碼: {response.status_code}")
        else:
            print(f"❌ HTTP 狀態碼: {response.status_code}")
            print(f"錯誤內容: {response.text}")
            return
        
        # 解析 JSON 回應
        try:
            result = response.json()
        except json.JSONDecodeError:
            print("❌ 無法解析 JSON 回應")
            print(f"原始回應: {response.text}")
            return
        
        print(f"⏱️  總耗時: {elapsed_time:.2f} 秒")
        print("-" * 50)
        
        # 顯示 FlareSolverr 回應狀態
        if result.get("status") == "ok":
            print("✅ FlareSolverr 狀態: 成功")
            
            solution = result.get("solution", {})
            
            # 顯示解決方案詳情
            print(f"🌐 最終 URL: {solution.get('url', 'N/A')}")
            print(f"📊 HTTP 狀態: {solution.get('status', 'N/A')}")
            print(f"🔧 User-Agent: {solution.get('userAgent', 'N/A')[:100]}...")
            
            # 顯示 Cookies 信息
            cookies = solution.get("cookies", [])
            print(f"🍪 Cookies 數量: {len(cookies)}")
            if cookies:
                print("🍪 Cookies 詳情:")
                for cookie in cookies[:3]:  # 只顯示前3個
                    print(f"   - {cookie.get('name')}: {cookie.get('value')[:50]}...")
            
            # 顯示回應標頭
            headers_info = solution.get("headers", {})
            print(f"📋 回應標頭數量: {len(headers_info)}")
            if headers_info:
                print("📋 主要標頭:")
                important_headers = ['content-type', 'server', 'date', 'cache-control']
                for header in important_headers:
                    if header in headers_info:
                        print(f"   - {header}: {headers_info[header]}")
            
            # 顯示 HTML 內容長度
            html_content = solution.get("response", "")
            print(f"📄 HTML 內容長度: {len(html_content)} 字符")
            
            # 檢查是否包含 Google 特徵
            if "google" in html_content.lower():
                print("✅ 確認收到 Google 頁面內容")
            else:
                print("⚠️  未檢測到 Google 頁面特徵")
            
            # 顯示時間戳
            start_ts = result.get("startTimestamp", 0)
            end_ts = result.get("endTimestamp", 0)
            if start_ts and end_ts:
                processing_time = (end_ts - start_ts) / 1000
                print(f"⚡ FlareSolverr 處理時間: {processing_time:.2f} 秒")
            
        else:
            print(f"❌ FlareSolverr 狀態: {result.get('status', 'unknown')}")
            print(f"錯誤訊息: {result.get('message', 'N/A')}")
        
        print("-" * 50)
        print("📝 完整回應 (JSON):")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except requests.exceptions.ConnectionError:
        print("❌ 連接錯誤: 無法連接到 FlareSolverr 服務")
        print("請確認 FlareSolverr 正在運行並監聽 127.0.0.1:8191")
    except requests.exceptions.Timeout:
        print("❌ 請求超時: FlareSolverr 處理時間過長")
    except Exception as e:
        print(f"❌ 未預期的錯誤: {str(e)}")

def test_health_check():
    """
    測試 FlareSolverr 健康檢查端點
    """
    print("\n🏥 測試健康檢查端點...")
    try:
        response = requests.get("http://127.0.0.1:8191/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ 健康檢查通過")
            print(f"版本: {result.get('version', 'N/A')}")
            print(f"狀態: {result.get('status', 'N/A')}")
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康檢查錯誤: {str(e)}")

if __name__ == "__main__":
    # 執行健康檢查
    test_health_check()
    
    # 執行主要測試
    test_flaresolverr()