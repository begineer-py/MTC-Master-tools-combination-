#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import sys

def test_crtsh_system():
    """測試 crt.sh 掃描系統的完整功能"""
    
    base_url = "http://localhost:8964"
    target_id = 1
    
    print("🚀 開始 crt.sh 掃描系統完整測試")
    print("=" * 50)
    
    # 1. 測試服務連接
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ 服務連接: {base_url} - 正常")
        else:
            print(f"❌ 服務連接: {base_url} - 異常 (狀態碼: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ 服務連接失敗: {str(e)}")
        return False
    
    # 2. 測試 API 端點
    print("🔍 測試 API 端點...")
    
    # 測試幫助信息
    try:
        response = requests.get(f"{base_url}/api/crtsh/help", timeout=10)
        if response.status_code == 200:
            help_data = response.json()
            print(f"✅ 幫助信息: {base_url}/api/crtsh/help - 正常")
            print(f"   📋 API 標題: {help_data.get('title', 'N/A')}")
        else:
            print(f"❌ 幫助信息: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 幫助信息測試失敗: {str(e)}")
    
    # 測試界面載入
    try:
        response = requests.get(f"{base_url}/api/crtsh/dashboard", timeout=10)
        if response.status_code == 200:
            print(f"✅ 界面載入: {base_url}/api/crtsh/dashboard - 正常")
        else:
            print(f"❌ 界面載入: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 界面載入測試失敗: {str(e)}")
    
    # 3. 測試前端界面
    print("\n🌐 測試前端界面...")
    
    try:
        response = requests.get(f"{base_url}/api/crtsh/dashboard?target_id={target_id}", timeout=10)
        if response.status_code == 200:
            html_content = response.text
            
            # 檢查關鍵元素
            checks = [
                ("HTML 文檔類型", "<!DOCTYPE html>" in html_content),
                ("頁面標題", "crt.sh 子域名掃描器" in html_content),
                ("目標 ID 輸入框", 'id="target-id"' in html_content),
                ("開始掃描按鈕", 'onclick="startScan()"' in html_content),
                ("JavaScript 文件", 'crtsh_dashboard.js' in html_content),
                ("CSS 樣式", '<style>' in html_content),
                ("通知容器", 'notification-container' in html_content)
            ]
            
            for check_name, check_result in checks:
                status = "✅" if check_result else "❌"
                print(f"{status} {check_name}: {'存在' if check_result else '缺失'}")
        else:
            print(f"❌ 前端界面測試失敗: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 前端界面測試失敗: {str(e)}")
    
    # 4. 測試靜態文件
    print("\n📁 測試靜態文件...")
    
    try:
        response = requests.get(f"{base_url}/static/js/crtsh_dashboard.js", timeout=10)
        if response.status_code == 200:
            print(f"✅ 靜態文件: /static/js/crtsh_dashboard.js - 正常")
            js_content = response.text
            
            # 檢查關鍵函數
            js_checks = [
                ("setTarget 函數", "function setTarget()" in js_content),
                ("startScan 函數", "function startScan()" in js_content),
                ("loadResults 函數", "function loadResults()" in js_content),
                ("exportDomains 函數", "function exportDomains(" in js_content)
            ]
            
            for check_name, check_result in js_checks:
                status = "✅" if check_result else "❌"
                print(f"   {status} {check_name}: {'存在' if check_result else '缺失'}")
        else:
            print(f"❌ 靜態文件: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 靜態文件測試失敗: {str(e)}")
    
    # 5. 測試掃描工作流程
    print(f"\n🎯 測試掃描工作流程 (目標 ID: {target_id})...")
    
    # 測試狀態查詢
    try:
        response = requests.get(f"{base_url}/api/crtsh/status/{target_id}", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ 狀態查詢: {status_data.get('status', 'unknown')}")
        else:
            print(f"❌ 狀態查詢: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 狀態查詢失敗: {str(e)}")
    
    # 測試歷史記錄查詢
    try:
        response = requests.get(f"{base_url}/api/crtsh/history/{target_id}", timeout=10)
        if response.status_code == 200:
            history_data = response.json()
            if history_data.get('success'):
                history_count = len(history_data.get('history', []))
                print(f"✅ 歷史記錄查詢: {history_count} 條記錄")
            else:
                print(f"⚠️ 歷史記錄查詢: {history_data.get('message', '無數據')}")
        else:
            print(f"❌ 歷史記錄查詢: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 歷史記錄查詢失敗: {str(e)}")
    
    # 測試結果查詢
    try:
        response = requests.get(f"{base_url}/api/crtsh/result/{target_id}", timeout=10)
        if response.status_code == 200:
            result_data = response.json()
            if result_data.get('success'):
                domains = result_data.get('result', {}).get('domains', [])
                print(f"✅ 結果查詢: 找到 {len(domains)} 個域名")
            else:
                print(f"⚠️ 結果查詢: {result_data.get('message', '無結果')}")
        elif response.status_code == 404:
            print(f"⚠️ 結果查詢: 未找到掃描結果")
        else:
            print(f"❌ 結果查詢: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 結果查詢失敗: {str(e)}")
    
    # 6. 測試 Attack 頁面集成
    print(f"\n🔗 測試 Attack 頁面集成...")
    
    try:
        response = requests.get(f"{base_url}/attack/{target_id}", timeout=10)
        if response.status_code == 200:
            attack_content = response.text
            
            # 檢查是否包含 crtsh 鏈接
            crtsh_link_check = f"/api/crtsh/dashboard?target_id={target_id}" in attack_content
            if crtsh_link_check:
                print("✅ Attack 頁面: 包含 crt.sh 掃描器鏈接")
            else:
                print("❌ Attack 頁面: 缺少 crt.sh 掃描器鏈接")
        else:
            print(f"❌ Attack 頁面測試: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ Attack 頁面測試失敗: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ 測試完成！")
    print("\n📋 使用說明:")
    print(f"1. 訪問: {base_url}/api/crtsh/dashboard")
    print("2. 輸入目標 ID 並開始掃描")
    print("3. 查看實時結果和歷史記錄")
    print(f"4. 或從 Attack 頁面直接跳轉: {base_url}/attack/{target_id}")
    
    return True

if __name__ == "__main__":
    try:
        test_crtsh_system()
    except KeyboardInterrupt:
        print("\n\n⚠️ 測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 測試過程中發生錯誤: {str(e)}")
        sys.exit(1) 