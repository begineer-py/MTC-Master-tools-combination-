#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP代理攔截器功能演示腳本
展示工具的主要功能，包括內建瀏覽器
"""

import sys
import os
import threading
import time

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui_interface import ProxyGUI


def print_demo_info():
    """打印演示信息"""
    print("=" * 60)
    print("🎯 HTTP代理攔截器 - 功能演示")
    print("=" * 60)
    print()
    print("🚀 主要功能演示:")
    print("  • HTTP代理服務器（監聽9487端口）")
    print("  • 🌐 內建瀏覽器（類似Burp Suite）")
    print("  • 請求攔截和詳情顯示")
    print("  • 請求編輯和重放功能")
    print("  • 🧪 快速測試工具")
    print("  • 日誌導出功能")
    print()
    print("📖 使用演示步驟:")
    print("  1. 啟動程序後，點擊'啟動代理'按鈕")
    print("  2. 切換到'🌐 內建瀏覽器'標籤頁")
    print("  3. 在地址欄輸入 http://httpbin.org 並訪問")
    print("  4. 切換回'🔍 代理攔截'標籤頁查看攔截的請求")
    print("  5. 點擊請求項查看詳情，可編輯並重放")
    print("  6. 使用'🧪 快速測試'按鈕進行多種測試")
    print()
    print("🎉 特色功能:")
    print("  • 所有通過內建瀏覽器的請求都會被自動攔截")
    print("  • 支持查看原始HTML源碼")
    print("  • 可以開啟外部瀏覽器並自動配置代理")
    print("  • 一鍵測試多種HTTP請求類型")
    print()
    print("正在啟動GUI演示...")
    print("=" * 60)


def demo_auto_test():
    """自動演示測試（可選）"""
    print("\n🤖 自動演示功能已準備就緒")
    print("啟動代理後，可以使用以下自動化測試:")
    
    auto_test_urls = [
        "http://httpbin.org/get",
        "http://httpbin.org/json", 
        "http://httpbin.org/headers",
        "http://example.com"
    ]
    
    print("可測試的URL:")
    for i, url in enumerate(auto_test_urls, 1):
        print(f"  {i}. {url}")


def main():
    """主演示函數"""
    try:
        # 顯示演示信息
        print_demo_info()
        
        # 演示自動測試功能
        demo_auto_test()
        
        # 創建並運行GUI應用
        app = ProxyGUI()
        
        # 啟動GUI
        app.run()
    
    except KeyboardInterrupt:
        print("\n\n⛔ 用戶中斷演示")
    except Exception as e:
        print(f"\n\n❌ 演示過程中出錯: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n🎊 感謝體驗HTTP代理攔截器演示！")
        print("GitHub: https://github.com/your-repo/proxy-interceptor")


if __name__ == "__main__":
    main() 