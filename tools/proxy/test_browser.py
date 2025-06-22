#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
內建瀏覽器功能測試腳本
用於驗證瀏覽器組件是否正常工作
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from browser_widget import ProxyBrowser, SimpleBrowser


def test_browser_widget():
    """測試瀏覽器組件"""
    print("測試內建瀏覽器組件...")
    
    # 創建測試窗口
    root = tk.Tk()
    root.title("瀏覽器組件測試")
    root.geometry("800x600")
    
    # 創建Notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    try:
        # 創建瀏覽器實例
        browser = ProxyBrowser(notebook, proxy_port=9487)
        
        print("✓ 瀏覽器組件創建成功")
        
        # 添加測試按鈕
        test_frame = ttk.Frame(root)
        test_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def test_navigation():
            browser.navigate_to("http://example.com")
            print("✓ 執行導航測試")
        
        ttk.Button(
            test_frame, 
            text="測試導航到 example.com", 
            command=test_navigation
        ).pack(side=tk.LEFT, padx=5)
        
        def test_httpbin():
            browser.navigate_to("http://httpbin.org/json")
            print("✓ 執行JSON API測試")
        
        ttk.Button(
            test_frame, 
            text="測試 httpbin.org JSON", 
            command=test_httpbin
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            test_frame, 
            text="注意：需要代理服務器運行在9487端口", 
            foreground="red"
        ).pack(side=tk.RIGHT, padx=5)
        
        print("瀏覽器測試界面已啟動")
        print("請手動測試以下功能：")
        print("1. 在地址欄輸入URL並訪問")
        print("2. 使用前進後退按鈕")
        print("3. 查看頁面內容和原始HTML")
        print("4. 嘗試開啟外部瀏覽器")
        
        root.mainloop()
        
    except Exception as e:
        print(f"✗ 瀏覽器組件測試失敗: {e}")
        import traceback
        traceback.print_exc()


def test_simple_browser():
    """測試簡單瀏覽器"""
    print("測試簡單瀏覽器組件...")
    
    root = tk.Tk()
    root.title("簡單瀏覽器測試")
    root.geometry("1000x700")
    
    try:
        # 創建簡單瀏覽器
        browser = SimpleBrowser(root, proxy_port=9487)
        
        print("✓ 簡單瀏覽器創建成功")
        print("瀏覽器界面已啟動，可以直接使用")
        
        root.mainloop()
        
    except Exception as e:
        print(f"✗ 簡單瀏覽器測試失敗: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主測試函數"""
    print("=" * 50)
    print("內建瀏覽器功能測試")
    print("=" * 50)
    print()
    
    choice = input("選擇測試模式:\n1. 完整瀏覽器組件測試\n2. 簡單瀏覽器測試\n請輸入選擇 (1/2): ")
    
    if choice == "1":
        test_browser_widget()
    elif choice == "2":
        test_simple_browser()
    else:
        print("無效選擇，執行簡單瀏覽器測試...")
        test_simple_browser()


if __name__ == "__main__":
    main() 