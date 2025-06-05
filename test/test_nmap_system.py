#!/usr/bin/env python3
"""
Nmap 掃描系統測試腳本
測試前端界面和後端 API 的完整功能
"""

import requests
import time
import sys
import argparse
from urllib.parse import urljoin

class NmapSystemTester:
    def __init__(self, base_url="http://localhost:8964"):
        self.base_url = base_url
        self.api_base = urljoin(base_url, "/api/nmap/")
        
    def test_api_endpoints(self):
        """測試所有 API 端點"""
        print("🔍 測試 API 端點...")
        
        endpoints = [
            ("help", "GET", "幫助信息"),
            ("dashboard", "GET", "界面載入"),
        ]
        
        for endpoint, method, description in endpoints:
            try:
                url = urljoin(self.api_base, endpoint)
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ {description}: {url} - 正常")
                else:
                    print(f"❌ {description}: {url} - 錯誤 {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {description}: {url} - 異常 {str(e)}")
    
    def test_dashboard_ui(self):
        """測試前端界面"""
        print("\n🌐 測試前端界面...")
        
        try:
            url = urljoin(self.api_base, "dashboard")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # 檢查關鍵元素
                checks = [
                    ("<!DOCTYPE html>", "HTML 文檔類型"),
                    ("Nmap 掃描器", "頁面標題"),
                    ("target-id", "目標 ID 輸入框"),
                    ("start-scan-btn", "開始掃描按鈕"),
                    ("nmap_dashboard.js", "JavaScript 文件"),
                ]
                
                for check, description in checks:
                    if check in content:
                        print(f"✅ {description}: 存在")
                    else:
                        print(f"❌ {description}: 缺失")
                        
            else:
                print(f"❌ 界面載入失敗: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 界面測試異常: {str(e)}")
    
    def test_scan_workflow(self, target_id=1):
        """測試掃描工作流程"""
        print(f"\n🎯 測試掃描工作流程 (目標 ID: {target_id})...")
        
        # 1. 檢查狀態
        try:
            status_url = urljoin(self.api_base, f"status/{target_id}")
            response = requests.get(status_url, params={"scan_type": "common"})
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 狀態查詢: {data.get('status', 'unknown')}")
            else:
                print(f"❌ 狀態查詢失敗: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 狀態查詢異常: {str(e)}")
        
        # 2. 檢查歷史記錄
        try:
            history_url = urljoin(self.api_base, f"history/{target_id}")
            response = requests.get(history_url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    history_count = len(data.get('history', []))
                    print(f"✅ 歷史記錄查詢: {history_count} 條記錄")
                else:
                    print(f"⚠️  歷史記錄查詢: 無記錄")
            else:
                print(f"❌ 歷史記錄查詢失敗: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 歷史記錄查詢異常: {str(e)}")
        
        # 3. 檢查結果
        try:
            result_url = urljoin(self.api_base, f"result/{target_id}")
            response = requests.get(result_url, params={"scan_type": "common"})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = data.get('result', {})
                    port_count = len(result.get('ports', []))
                    print(f"✅ 結果查詢: 找到 {port_count} 個端口")
                else:
                    print(f"⚠️  結果查詢: 無結果")
            elif response.status_code == 404:
                print(f"⚠️  結果查詢: 尚無掃描結果")
            else:
                print(f"❌ 結果查詢失敗: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 結果查詢異常: {str(e)}")
    
    def test_static_files(self):
        """測試靜態文件"""
        print("\n📁 測試靜態文件...")
        
        static_files = [
            "/static/js/nmap_dashboard.js",
        ]
        
        for file_path in static_files:
            try:
                url = urljoin(self.base_url, file_path)
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ 靜態文件: {file_path} - 正常")
                else:
                    print(f"❌ 靜態文件: {file_path} - 錯誤 {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 靜態文件: {file_path} - 異常 {str(e)}")
    
    def run_full_test(self, target_id=1):
        """運行完整測試"""
        print("🚀 開始 Nmap 掃描系統完整測試")
        print("=" * 50)
        
        # 檢查服務是否可用
        try:
            response = requests.get(self.base_url, timeout=5)
            print(f"✅ 服務連接: {self.base_url} - 正常")
        except Exception as e:
            print(f"❌ 服務連接失敗: {str(e)}")
            return False
        
        # 運行各項測試
        self.test_api_endpoints()
        self.test_dashboard_ui()
        self.test_static_files()
        self.test_scan_workflow(target_id)
        
        print("\n" + "=" * 50)
        print("✅ 測試完成！")
        print("\n📋 使用說明:")
        print(f"1. 訪問: {urljoin(self.api_base, 'dashboard')}")
        print("2. 輸入目標 ID 並開始掃描")
        print("3. 查看實時結果和歷史記錄")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Nmap 掃描系統測試工具")
    parser.add_argument("--url", default="http://localhost:8964", 
                       help="服務器 URL (默認: http://localhost:8964)")
    parser.add_argument("--target-id", type=int, default=1,
                       help="測試用目標 ID (默認: 1)")
    
    args = parser.parse_args()
    
    tester = NmapSystemTester(args.url)
    success = tester.run_full_test(args.target_id)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 