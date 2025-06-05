#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import sys

def test_attack_page():
    """測試 Attack 頁面的基本功能"""
    base_url = "http://localhost:8964"
    
    print("🔍 測試 Attack 頁面集成...")
    
    try:
        # 測試 Attack 頁面載入
        response = requests.get(f"{base_url}/attack/1", timeout=10)
        if response.status_code != 200:
            print(f"❌ Attack 頁面無法訪問: {response.status_code}")
            return False
            
        content = response.text
        
        # 檢查基本 HTML 結構
        checks = [
            ("HTML 文檔類型", "<!DOCTYPE html>" in content),
            ("React 掛載點", 'id="attack-root"' in content),
            ("初始數據", "window.INITIAL_DATA" in content),
            ("Bundle.js 引用", "/static/js/dist/bundle.js" in content),
            ("目標 ID", 'targetId: "1"' in content),
            ("目標數據", 'target_ip:' in content and 'domain:' in content),
            ("用戶數據", 'currentUser:' in content),
        ]
        
        all_passed = True
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}: {'通過' if result else '失敗'}")
            if not result:
                all_passed = False
        
        # 測試 bundle.js 是否可訪問
        bundle_response = requests.get(f"{base_url}/static/js/dist/bundle.js", timeout=5)
        bundle_ok = bundle_response.status_code == 200
        print(f"   {'✅' if bundle_ok else '❌'} Bundle.js 可訪問: {'是' if bundle_ok else '否'}")
        
        if bundle_ok:
            # 檢查 bundle.js 中是否包含 Gau 相關內容
            bundle_content = bundle_response.text
            gau_checks = [
                ("Gau 按鈕文字", "進入 Gau URL 掃描器界面" in bundle_content),
                ("橙色主題", "#FF9800" in bundle_content),
                ("Gau 鏈接", "/api/gau/dashboard" in bundle_content),
                ("四列布局", "col-md-3" in bundle_content),
            ]
            
            print("   📦 Bundle.js 內容檢查:")
            for check_name, result in gau_checks:
                status = "✅" if result else "❌"
                print(f"      {status} {check_name}: {'包含' if result else '缺少'}")
                if not result:
                    all_passed = False
        else:
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 測試過程中出錯: {str(e)}")
        return False

def main():
    print("🚀 Attack 頁面集成測試")
    print("=" * 50)
    
    success = test_attack_page()
    
    print("=" * 50)
    if success:
        print("✅ 所有測試通過！Attack 頁面集成正常")
        print("\n📋 使用說明:")
        print("1. 訪問: http://localhost:8964/attack/1")
        print("2. 點擊 'Gau URL 掃描器界面' 按鈕")
        print("3. 自動跳轉到 Gau 掃描器並傳遞 target_id=1")
    else:
        print("❌ 部分測試失敗，請檢查上述錯誤")
        sys.exit(1)

if __name__ == "__main__":
    main() 