import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------- 配置區 (CONFIGURATION) -------------------

# 1. 從Burp Suite的請求中，複製出完整的Cookie和Headers
#    確保移除 "Content-Length" 這個頭，requests會自動計算
HEADERS = {
    'Host': 'www.etsy.com',
    'Cookie': 'uaid=VUudhUHvgd_XW9qGDV7TRvI-FcljZACCDB_H1TC6Wqk0MTNFyUopPjHNNdAvrLA0sKLUPym3sDDQyNWg2CvEPT3DUqmWAQA.; user_prefs=1PskVgakrgK2uh6xV6AuE7WSYndjZACCDB_H1TA6Wikk3EVJJ680J0dHKTVPNzRYSQcoBBUxglC4iFgGAA..; fve=1749828011.0; exp_ebid=m=c8x4uF1v7SbtMMT18DOOq5Y%2FBTW5JX40VV0ums5JmV0%3D,v=uj24Mszn-PPz1GYu8NtrLlvpLQeb2NNL; _fbp=fb.1.1749828015990.6567792664097912; ua=531227642bc86f3b5fd7103a0c0b4fd6; _gcl_au=1.1.1139366786.1749828017; _ga=GA1.1.1400917634.1749828017; lantern=d03c8639-afd5-4b1b-b777-81dcd442d494; session-key-www=1100298062-1386333409753-610ef54c524a32637c0eb29f069b278ab7663e379e512971da537458|1757604262; session-key-apex=1100298062-1386333409753-4485ac62b8d1857d7a24e1d90fbf2557d5d4135147a670ee4ed7987c|1757604262; LD=1; et-v1-1-1-_etsy_com=2%3A5d3854dd6dc76693239ca98bec7b6cdffd9333b9%3A1749828261%3A1749828261%3A__athena_compat-1100298062-1386333409753-e022879b35696f8f7dd471f5f821716cd94fca8a41d989cf012ab15e96be22470d3e80cf789eb3b2; _pin_unauth=dWlkPVltVTFNMlExWW1NdE1HVmtNeTAwWldNeUxUbGtZbVl0TVdJNU0yTXpPRGcyWlRneQ; _ga_KR3J610VYM=GS2.1.s1749867132$o3$g1$t1749867797$j46$l0$h0; _uetsid=e9551440486911f0825dc59ac4002dbc; _uetvid=e954f710486911f0a59a9394bac689b8; datadome=qUwi380D0vvM~nYqaEWUr98TxH69QEHPZupyWUwd~wJWmT6ToMxOU0GiXmdwXu6twUgz~ptIcFm_2_xFWHPzPIf5eMAXF_Z~OAq_hTEjisD6Uw78XXGC7z5xGQ6Ndv80',
    'X-Csrf-Token': '3:1749867796:iv6TVmRJY5Dgoy9MNfMSWWj7Mub-:8dea5394d50cf77bf60f679c1b5da500d988eedb3e6f8496d851d6c2de3a7727',
    # ... 其他所有Header都複製過來 ...
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
}

# 2. 目標URL，將shop_id替換為你實際攔截到的有效ID
TARGET_URL = 'https://www.etsy.com/api/v3/ajax/bespoke/shop/60258308/onboarding/preferences'

# 2. 核心變更：我們的Payload不再是數字，而是一個貨幣代碼列表
#    這裡我為你準備了一份包含常見及部分冷門貨幣的列表
CURRENCY_CODES = [
    # 主要貨幣
    "USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "CNY", "HKD", "SGD", "TWD",
    # 亞洲貨幣
    "KRW", "INR", "THB", "MYR", "PHP", "IDR", "VND",
    # 歐洲貨幣
    "SEK", "NOK", "DKK", "PLN", "RUB", "TRY",
    # 美洲貨幣
    "MXN", "BRL",
    # 中東與非洲貨幣
    "AED", "SAR", "ZAR",
    # 測試用/特殊/已失效貨幣 (尋找異常的關鍵)
    "BTC", "XBT", "ETH", # 加密貨幣
    "XAU", "XAG", # 貴金属
    "XYZ", "ABC", "AAA", # 虛構代碼
    "ITL", "DEM", "FRF"  # 已被歐元取代的舊貨幣
    "KPW",  # 朝鮮圓
    "IRR",  # 伊朗里亞爾
    "SYP",  # 敘利亞鎊
    "CUP",  # 古巴比索

    # 2. 匯率極低的罕見貨幣 (Low Value / High Precision Currencies)
    "VND",  # 越南盾 (~25,000 to 1 USD)
    "IDR",  # 印尼盾 (~16,000 to 1 USD)
    "UZS",  # 烏茲別克斯坦索姆 (~12,000 to 1 USD)
    "LAK",  # 寮國基普 (~21,000 to 1 USD)

    # 3. 不存在的/已失效的貨幣 (測試錯誤處理)
    "XYZ", "ABC", "AAA",  # 虛構代碼
    "ITL", "DEM", "FRF",  # 舊歐洲貨幣

    # 4. 加密貨幣 (測試是否意外接受)
    "BTC", "ETH"

]

# 3. 掃描設置
MAX_WORKERS = 3     # 降低並發，因為測試總量不大，且需要更精準
REQUEST_DELAY = 0.2 # 稍微增加延遲，模仿人類行為

# ------------------- 核心邏輯 (CORE LOGIC) -------------------

def check_currency_code(currency_code):
    """發送一個請求來測試指定的currency_code"""
    payload = {
        'country_id': 209, # 使用一個已知的、有效的國家ID，如美國
        'currency_code': currency_code,
        'name': 'initial_seller_type',
        'value': 0,
        'language_code': 'en-US'
    }
    
    try:
        response = requests.put(TARGET_URL, headers=HEADERS, data=payload, timeout=10)
        
        # 這次，我們不僅關心200 OK，還要關心不同的錯誤信息
        # 一個好的策略是記錄下所有非400（由WAF觸發的請求格式錯誤）的響應
        if response.status_code != 400:
             # 返回狀態碼和響應體，以便後續分析
            return currency_code, response.status_code, response.text
        else:
            return currency_code, response.status_code, None
            
    except requests.exceptions.RequestException as e:
        return currency_code, -1, str(e) # -1 代表網路錯誤

# ------------------- 執行與輸出 (EXECUTION & OUTPUT) -------------------

if __name__ == "__main__":
    print(f"[*] 開始掃描貨幣代碼...")
    results = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_currency_code, code): code for code in CURRENCY_CODES}
        
        for future in as_completed(futures):
            code = futures[future]
            try:
                cc, status, body = future.result()
                if body is not None:
                    # 打印出所有「有意義」的響應
                    print(f"[+] 測試代碼: {cc} | 狀態碼: {status} | 響應體: {body[:100]}...") # 只打印前100個字符
                results[cc] = status

            except Exception as e:
                print(f"[!] 代碼 {code} 執行時發生未知錯誤: {e}")
            
            time.sleep(REQUEST_DELAY)

    print("\n[*] 掃描完成！")
    print("[*] 以下是不同貨幣代碼的響應狀態碼總結:")
    
    # 分類匯總結果
    successful_codes = [code for code, status in results.items() if status == 200]
    not_found_codes = [code for code, status in results.items() if status == 404]
    error_codes = {code: status for code, status in results.items() if status not in [200, 404, 400, -1]}

    print(f"\n[SUCCESS] 接受的貨幣代碼 (200 OK): {successful_codes}")
    print(f"[NOT FOUND] 未找到或無效的代碼 (404 Not Found): {not_found_codes}")
    print(f"[OTHER ERRORS] 其他值得關注的錯誤響應: {error_codes}")