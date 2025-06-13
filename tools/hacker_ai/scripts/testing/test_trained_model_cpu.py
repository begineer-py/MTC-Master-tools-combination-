#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
測試訓練模型CPU模式
專門檢查HackerAI訓練模型的問題
"""

import sys
import os

# 確保可以導入自定義模組
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_trained_model_cpu():
    """測試訓練模型CPU模式"""
    print("🧪 測試訓練模型 - CPU模式")
    print("=" * 50)
    
    try:
        from hacker_AI_loader.load_models import ModelLoader
        
        loader = ModelLoader()
        print("✅ ModelLoader實例創建成功")
        
        # 強制使用CPU避開CUDA問題
        print("\n🔄 載入訓練模型（CPU模式）...")
        success, message = loader.load_trained_model(force_cpu=True)
        
        if success:
            print(f"✅ {message}")
            print(f"📊 模型狀態: {loader.get_model_status()}")
            
            # 測試問答
            test_questions = [
                "什麼是SQL注入？",
                "解釋一下XSS攻擊",
                "你好"
            ]
            
            for question in test_questions:
                print(f"\n問題: {question}")
                try:
                    answer = loader.generate_answer(question)
                    print(f"回答: {answer}")
                except Exception as e:
                    print(f"❌ 生成錯誤: {e}")
            
            # 卸載模型
            print(f"\n🔧 卸載模型...")
            unload_msg = loader.unload_model()
            print(f"✅ {unload_msg}")
            
            return True
            
        else:
            print(f"❌ 載入失敗: {message}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_trained_model_cpu()
    print(f"\n結果: {'成功' if success else '失敗'}") 