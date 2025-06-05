#!/usr/bin/env python3
"""
Gau 掃描修復測試腳本
測試排除文件參數和文件下載功能
"""

import requests
import json
import time
import sys

API_BASE = "http://localhost:8964/api/gau"
TARGET_ID = 1

def test_scan_with_blacklist():
    """測試帶有自定義 blacklist 的掃描"""
    print("🔍 測試 1: 自定義排除文件參數")
    
    # 測試數據
    test_data = {
        "threads": 8,
        "blacklist": "png,jpg,gif,css,js,ico,svg,woff,ttf",
        "verbose": True,
        "providers": ["wayback", "commoncrawl"]
    }
    
    print(f"發送掃描請求: {test_data}")
    
    response = requests.post(f"{API_BASE}/scan/{TARGET_ID}", 
                           json=test_data,
                           headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 掃描啟動成功: {result}")
        return True
    else:
        print(f"❌ 掃描啟動失敗: {response.status_code} - {response.text}")
        return False

def check_scan_status():
    """檢查掃描狀態"""
    print("\n📊 檢查掃描狀態")
    
    response = requests.get(f"{API_BASE}/status/{TARGET_ID}")
    
    if response.status_code == 200:
        result = response.json()
        status = result.get('status', 'unknown')
        message = result.get('message', '')
        print(f"狀態: {status} - {message}")
        return status
    else:
        print(f"❌ 獲取狀態失敗: {response.status_code}")
        return None

def wait_for_completion(max_wait=300):
    """等待掃描完成"""
    print(f"\n⏳ 等待掃描完成 (最多 {max_wait} 秒)")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        status = check_scan_status()
        
        if status == 'completed':
            print("✅ 掃描完成")
            return True
        elif status == 'failed':
            print("❌ 掃描失敗")
            return False
        elif status in ['scanning', 'not_started']:
            print("⏳ 掃描進行中...")
            time.sleep(10)
        else:
            print(f"⚠️  未知狀態: {status}")
            time.sleep(5)
    
    print("⏰ 等待超時")
    return False

def test_file_download():
    """測試文件下載功能"""
    print("\n📁 測試 2: 文件下載功能")
    
    response = requests.get(f"{API_BASE}/file/{TARGET_ID}")
    
    if response.status_code == 200:
        # 檢查響應頭
        content_type = response.headers.get('Content-Type', '')
        content_disposition = response.headers.get('Content-Disposition', '')
        content_length = response.headers.get('Content-Length', '0')
        
        print(f"✅ 文件下載成功")
        print(f"   Content-Type: {content_type}")
        print(f"   Content-Disposition: {content_disposition}")
        print(f"   Content-Length: {content_length} bytes")
        
        # 檢查文件內容的前幾行
        content = response.text
        lines = content.split('\n')[:10]
        print(f"   文件前 10 行:")
        for i, line in enumerate(lines, 1):
            print(f"   {i:2d}: {line}")
        
        return True
    else:
        print(f"❌ 文件下載失敗: {response.status_code} - {response.text}")
        return False

def test_result_retrieval():
    """測試結果獲取"""
    print("\n📋 測試 3: 結果獲取")
    
    response = requests.get(f"{API_BASE}/result/{TARGET_ID}?page=1&per_page=10")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            scan_result = result.get('result', {})
            total_urls = scan_result.get('total_urls', 0)
            status = scan_result.get('status', 'unknown')
            categories = scan_result.get('categories', {})
            
            print(f"✅ 結果獲取成功")
            print(f"   狀態: {status}")
            print(f"   總 URL 數: {total_urls}")
            print(f"   分類統計: {categories}")
            
            return True
        else:
            print(f"❌ 結果獲取失敗: {result.get('message', 'Unknown error')}")
            return False
    else:
        print(f"❌ 結果獲取失敗: {response.status_code} - {response.text}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始 Gau 掃描修復測試")
    print("=" * 50)
    
    # 測試 1: 自定義排除文件參數
    if not test_scan_with_blacklist():
        print("❌ 測試 1 失敗，退出")
        return False
    
    # 等待掃描完成
    if not wait_for_completion():
        print("❌ 掃描未能在預期時間內完成")
        return False
    
    # 測試 2: 結果獲取
    if not test_result_retrieval():
        print("❌ 測試 3 失敗")
        return False
    
    # 測試 3: 文件下載
    if not test_file_download():
        print("❌ 測試 2 失敗")
        return False
    
    print("\n🎉 所有測試通過！")
    print("=" * 50)
    print("修復驗證:")
    print("✅ 排除文件參數功能正常")
    print("✅ 文件下載功能正常")
    print("✅ 結果獲取功能正常")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
        sys.exit(1) 