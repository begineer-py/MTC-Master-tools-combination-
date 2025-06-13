#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HackerAI 問答系統主程序
功能已拆分到以下模組：
- hacker_ai_gui.hacker_ai_gui: GUI界面邏輯
- hacker_AI_loader.load_models: AI模型載入和處理邏輯
"""

import sys
import os

# 確保可以導入自定義模組
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # 導入GUI模組
    from hacker_ai_gui.hacker_ai_gui import HackerAIGUI
    
    def main():
        """主函數"""
        print("🚀 正在啟動 HackerAI 問答系統...")
        print("📁 模組結構:")
        print("   ├── hacker_ai_gui/hacker_ai_gui.py - GUI界面邏輯")
        print("   ├── hacker_AI_loader/load_models.py - AI模型載入器")
        print("   └── run.py - 主程序入口")
        print()
        
        # 創建並運行GUI應用
        app = HackerAIGUI()
        app.run()

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ 導入模組失敗: {e}")
    print("請確保以下文件存在:")
    print("- hacker_ai_gui/hacker_ai_gui.py")
    print("- hacker_AI_loader/load_models.py")
    sys.exit(1)
except Exception as e:
    print(f"❌ 啟動失敗: {e}")
    sys.exit(1)