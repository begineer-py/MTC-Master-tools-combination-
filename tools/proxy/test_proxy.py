#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理測試腳本
用於測試HTTP代理攔截器功能
"""

import requests
import time
import json


def test_basic_get():
    """測試基本GET請求"""
    print("測試1: 基本GET請求")
    try:
        proxies = {
            'http': 'http://127.0.0.1:9487',
            'https': 'http://127.0.0.1:9487'
        }
        
        response = requests.get(
            'http://httpbin.org/get',
            proxies=proxies,
            timeout=10
        )
        
        print(f"狀態碼: {response.status_code}")
        print(f"響應內容: {response.text[:200]}...")
        print("✓ GET請求測試成功\n")
        
    except Exception as e:
        print(f"✗ GET請求測試失敗: {e}\n")


def test_post_with_data():
    """測試POST請求（帶數據）"""
    print("測試2: POST請求（帶JSON數據）")
    try:
        proxies = {
            'http': 'http://127.0.0.1:9487',
            'https': 'http://127.0.0.1:9487'
        }
        
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'email': 'test@example.com'
        }
        
        response = requests.post(
            'http://httpbin.org/post',
            json=data,
            proxies=proxies,
            timeout=10
        )
        
        print(f"狀態碼: {response.status_code}")
        print(f"響應內容: {response.text[:200]}...")
        print("✓ POST請求測試成功\n")
        
    except Exception as e:
        print(f"✗ POST請求測試失敗: {e}\n")


def test_headers():
    """測試自定義Headers"""
    print("測試3: 帶自定義Headers的請求")
    try:
        proxies = {
            'http': 'http://127.0.0.1:9487',
            'https': 'http://127.0.0.1:9487'
        }
        
        headers = {
            'User-Agent': 'ProxyTester/1.0',
            'X-Custom-Header': 'Test-Value',
            'Authorization': 'Bearer test-token-123'
        }
        
        response = requests.get(
            'http://httpbin.org/headers',
            headers=headers,
            proxies=proxies,
            timeout=10
        )
        
        print(f"狀態碼: {response.status_code}")
        print(f"響應內容: {response.text[:200]}...")
        print("✓ Headers測試成功\n")
        
    except Exception as e:
        print(f"✗ Headers測試失敗: {e}\n")


def test_form_data():
    """測試表單數據"""
    print("測試4: 表單數據提交")
    try:
        proxies = {
            'http': 'http://127.0.0.1:9487',
            'https': 'http://127.0.0.1:9487'
        }
        
        form_data = {
            'name': '張三',
            'age': '25',
            'city': '台北'
        }
        
        response = requests.post(
            'http://httpbin.org/post',
            data=form_data,
            proxies=proxies,
            timeout=10
        )
        
        print(f"狀態碼: {response.status_code}")
        print(f"響應內容: {response.text[:200]}...")
        print("✓ 表單數據測試成功\n")
        
    except Exception as e:
        print(f"✗ 表單數據測試失敗: {e}\n")


def test_multiple_requests():
    """測試多個連續請求"""
    print("測試5: 多個連續請求")
    try:
        proxies = {
            'http': 'http://127.0.0.1:9487',
            'https': 'http://127.0.0.1:9487'
        }
        
        urls = [
            'http://httpbin.org/json',
            'http://httpbin.org/uuid',
            'http://httpbin.org/user-agent',
        ]
        
        for i, url in enumerate(urls, 1):
            print(f"  發送請求 {i}/3: {url}")
            response = requests.get(url, proxies=proxies, timeout=10)
            print(f"  響應狀態碼: {response.status_code}")
            time.sleep(0.5)  # 間隔0.5秒
        
        print("✓ 多請求測試成功\n")
        
    except Exception as e:
        print(f"✗ 多請求測試失敗: {e}\n")


def main():
    """主測試函數"""
    print("=" * 50)
    print("HTTP代理攔截器 - 功能測試")
    print("=" * 50)
    print("測試目標: 127.0.0.1:9487")
    print("請確保代理服務器已啟動！")
    print("=" * 50)
    print()
    
    try:
        # 檢查代理是否可用
        print("檢查代理服務器連接...")
        proxies = {'http': 'http://127.0.0.1:9487'}
        test_response = requests.get(
            'http://httpbin.org/ip', 
            proxies=proxies, 
            timeout=5
        )
        print("✓ 代理服務器連接正常\n")
        
        # 運行所有測試
        test_basic_get()
        test_post_with_data()
        test_headers()
        test_form_data()
        test_multiple_requests()
        
        print("=" * 50)
        print("所有測試完成！請檢查代理攔截器界面中的請求記錄。")
        print("=" * 50)
        
    except requests.exceptions.ProxyError:
        print("✗ 無法連接到代理服務器 (127.0.0.1:9487)")
        print("請確保代理服務器已啟動！")
    except Exception as e:
        print(f"✗ 測試過程中出現錯誤: {e}")


if __name__ == "__main__":
    main() 