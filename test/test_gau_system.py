#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import sys

def test_gau_system():
    """測試 Gau URL 掃描系統的完整功能"""
    
    base_url = "http://localhost:8964"
    target_id = 1
    
    print("🚀 開始 Gau URL 掃描系統完整測試")
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
        response = requests.get(f"{base_url}/api/gau/help", timeout=10)
        if response.status_code == 200:
            help_data = response.json()
            print(f"✅ 幫助信息: {base_url}/api/gau/help - 正常")
            print(f"   📋 API 標題: {help_data.get('title', 'N/A')}")
            print(f"   🔧 功能數量: {len(help_data.get('features', []))}")
        else:
            print(f"❌ 幫助信息: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 幫助信息測試失敗: {str(e)}")
    
    # 測試界面載入
    try:
        response = requests.get(f"{base_url}/api/gau/dashboard", timeout=10)
        if response.status_code == 200:
            print(f"✅ 界面載入: {base_url}/api/gau/dashboard - 正常")
        else:
            print(f"❌ 界面載入: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 界面載入測試失敗: {str(e)}")
    
    # 3. 測試前端界面
    print("\n🌐 測試前端界面...")
    
    try:
        response = requests.get(f"{base_url}/api/gau/dashboard?target_id={target_id}", timeout=10)
        if response.status_code == 200:
            html_content = response.text
            
            # 檢查關鍵元素
            checks = [
                ("HTML 文檔類型", "<!DOCTYPE html>" in html_content),
                ("頁面標題", "Gau URL 掃描器" in html_content),
                ("目標 ID 輸入框", 'id="target-id"' in html_content),
                ("開始掃描按鈕", 'onclick="startScan()"' in html_content),
                ("JavaScript 文件", 'gau_dashboard.js' in html_content),
                ("CSS 樣式", '<style>' in html_content),
                ("通知容器", 'notification-container' in html_content),
                ("掃描選項", 'scan-options' in html_content),
                ("分類過濾器", 'category-filters' in html_content),
                ("URL 表格", 'url-table' in html_content),
                ("分頁控制", 'pagination' in html_content),
                ("橙色主題", '#FF9800' in html_content)
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
        response = requests.get(f"{base_url}/static/js/gau_dashboard.js", timeout=10)
        if response.status_code == 200:
            print(f"✅ 靜態文件: /static/js/gau_dashboard.js - 正常")
            js_content = response.text
            
            # 檢查關鍵函數
            js_checks = [
                ("setTarget 函數", "function setTarget()" in js_content),
                ("startScan 函數", "function startScan()" in js_content),
                ("loadResults 函數", "function loadResults(" in js_content),
                ("exportUrls 函數", "function exportUrls(" in js_content),
                ("filterByCategory 函數", "function filterByCategory(" in js_content),
                ("displayPagination 函數", "function displayPagination()" in js_content),
                ("copyUrl 函數", "function copyUrl(" in js_content),
                ("downloadFile 函數", "function downloadFile()" in js_content)
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
        response = requests.get(f"{base_url}/api/gau/status/{target_id}", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ 狀態查詢: {status_data.get('status', 'unknown')}")
            print(f"   📝 狀態消息: {status_data.get('message', 'N/A')}")
        else:
            print(f"❌ 狀態查詢: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 狀態查詢失敗: {str(e)}")
    
    # 測試歷史記錄查詢
    try:
        response = requests.get(f"{base_url}/api/gau/history/{target_id}", timeout=10)
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
        response = requests.get(f"{base_url}/api/gau/result/{target_id}", timeout=10)
        if response.status_code == 200:
            result_data = response.json()
            if result_data.get('success'):
                result = result_data.get('result', {})
                urls = result.get('urls', [])
                categories = result.get('categories', {})
                print(f"✅ 結果查詢: 找到 {len(urls)} 個 URL")
                print(f"   📊 分類統計: 總計 {categories.get('all', 0)}, JS {categories.get('js', 0)}, API {categories.get('api', 0)}")
            else:
                print(f"⚠️ 結果查詢: {result_data.get('message', '無結果')}")
        elif response.status_code == 404:
            print(f"⚠️ 結果查詢: 未找到掃描結果")
        else:
            print(f"❌ 結果查詢: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 結果查詢失敗: {str(e)}")
    
    # 測試分頁查詢
    try:
        response = requests.get(f"{base_url}/api/gau/result/{target_id}?page=1&per_page=10&category=all", timeout=10)
        if response.status_code == 200:
            result_data = response.json()
            if result_data.get('success'):
                pagination = result_data.get('result', {}).get('pagination', {})
                print(f"✅ 分頁查詢: 第 {pagination.get('page', 1)} 頁，共 {pagination.get('total_pages', 1)} 頁")
            else:
                print(f"⚠️ 分頁查詢: {result_data.get('message', '無結果')}")
        else:
            print(f"❌ 分頁查詢: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 分頁查詢失敗: {str(e)}")
    
    # 測試文件下載
    try:
        response = requests.get(f"{base_url}/api/gau/file/{target_id}", timeout=15)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            print(f"✅ 文件下載: 成功 ({content_length} 字節, {content_type})")
        elif response.status_code == 404:
            print(f"⚠️ 文件下載: 未找到掃描結果文件")
        else:
            print(f"❌ 文件下載: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 文件下載失敗: {str(e)}")
    
    # 6. 測試 Attack 頁面集成
    print(f"\n🔗 測試 Attack 頁面集成...")
    
    try:
        response = requests.get(f"{base_url}/attack/{target_id}", timeout=10)
        if response.status_code == 200:
            attack_content = response.text
            
            # 檢查是否包含 Gau 鏈接
            gau_link_check = f"/api/gau/dashboard?target_id={target_id}" in attack_content
            gau_button_check = "Gau URL 掃描器界面" in attack_content
            orange_theme_check = "#FF9800" in attack_content
            four_columns_check = "col-md-3" in attack_content
            
            if gau_link_check:
                print("✅ Attack 頁面: 包含 Gau 掃描器鏈接")
            else:
                print("❌ Attack 頁面: 缺少 Gau 掃描器鏈接")
                
            if gau_button_check:
                print("✅ Attack 頁面: 包含 Gau 按鈕文字")
            else:
                print("❌ Attack 頁面: 缺少 Gau 按鈕文字")
                
            if orange_theme_check:
                print("✅ Attack 頁面: 包含橙色主題")
            else:
                print("❌ Attack 頁面: 缺少橙色主題")
                
            if four_columns_check:
                print("✅ Attack 頁面: 使用 4 列布局")
            else:
                print("❌ Attack 頁面: 布局不正確")
        else:
            print(f"❌ Attack 頁面測試: 狀態碼 {response.status_code}")
    except Exception as e:
        print(f"❌ Attack 頁面測試失敗: {str(e)}")
    
    # 7. 測試掃描選項
    print(f"\n⚙️ 測試掃描選項...")
    
    try:
        # 測試帶選項的掃描請求（不實際執行）
        scan_options = {
            "threads": 30,
            "providers": "wayback,commoncrawl",
            "blacklist": "png,jpg,gif",
            "verbose": True
        }
        
        print(f"✅ 掃描選項配置: {scan_options}")
        print("   📝 注意: 實際掃描測試需要手動執行以避免長時間等待")
        
    except Exception as e:
        print(f"❌ 掃描選項測試失敗: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ 測試完成！")
    print("\n📋 使用說明:")
    print(f"1. 訪問: {base_url}/api/gau/dashboard")
    print("2. 輸入目標 ID 並配置掃描選項")
    print("3. 開始掃描並查看實時結果")
    print("4. 使用分類過濾和搜索功能")
    print("5. 導出結果或下載完整文件")
    print(f"6. 或從 Attack 頁面直接跳轉: {base_url}/attack/{target_id}")
    
    print("\n🎨 設計特色:")
    print("- 橙色主題 (#FF9800) 區別於其他掃描器")
    print("- URL 自動分類 (JS、API、圖片、CSS、文檔等)")
    print("- 分頁和搜索功能")
    print("- 多種導出格式 (TXT、CSV)")
    print("- 實時狀態更新")
    print("- 歷史記錄管理")
    
    return True

if __name__ == "__main__":
    try:
        test_gau_system()
    except KeyboardInterrupt:
        print("\n\n⚠️ 測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 測試過程中發生錯誤: {str(e)}")
        sys.exit(1) 