#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP代理攔截器 - 類似Burp Suite
主程序入口

使用方法:
1. 運行本程序
2. 點擊"啟動代理"按鈕，程序將監聽9487端口
3. 配置目標應用或瀏覽器使用 127.0.0.1:9487 作為HTTP代理
4. 在目標應用中發送HTTP請求，本工具將攔截並顯示請求詳情
5. 可以編輯請求內容並重放

作者：AI助手
版本：1.0
"""

import sys
import os

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui_interface import ProxyGUI


def print_welcome():
    """顯示歡迎信息"""
    print("=" * 60)
    print("     HTTP代理攔截器 - 類似Burp Suite")
    print("=" * 60)
    print()
    print("功能特點:")
    print("  • 監聽9487端口，攔截HTTP請求")
    print("  • 實時顯示請求詳情（方法、URL、Headers、Body等）")
    print("  • 支持請求編輯和重放")
    print("  • 導出請求日誌（JSON/TXT格式）")
    print("  • 美觀的GUI界面，類似專業工具")
    print()
    print("使用步驟:")
    print("  1. 點擊'啟動代理'按鈕")
    print("  2. 配置目標應用使用 127.0.0.1:9487 作為HTTP代理")
    print("  3. 發送請求，在左側列表中查看攔截的請求")
    print("  4. 點擊請求項查看詳情，可編輯並重放")
    print()
    print("代理配置示例:")
    print("  • curl: curl -x 127.0.0.1:9487 http://example.com")
    print("  • 瀏覽器: 設置HTTP代理為 127.0.0.1:9487")
    print("  • Python requests: proxies={'http': 'http://127.0.0.1:9487'}")
    print()
    print("正在啟動GUI界面...")
    print("=" * 60)


def main():
    """主函數"""
    try:
        # 顯示歡迎信息
        print_welcome()
        
        # 創建並運行GUI應用
        app = ProxyGUI()
        app.run()
    
    except KeyboardInterrupt:
        print("\n\n用戶中斷，程序退出")
    except Exception as e:
        print(f"\n\n程序運行出錯: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("感謝使用HTTP代理攔截器！")


if __name__ == "__main__":
    main() 