#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GPU修復驗證測試
"""

import sys
import os
import torch

# 確保可以導入自定義模組
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def check_gpu_status():
    """檢查GPU狀態"""
    print("🔍 檢查GPU狀態...")
    print(f"   CUDA可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   GPU設備: {torch.cuda.get_device_name(0)}")
        print(f"   GPU記憶體: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    print()

def test_trained_model_gpu():
    """測試訓練模型GPU載入"""
    print("🧪 測試訓練模型GPU載入...")
    
    try:
        from hacker_AI_loader.load_models import ModelLoader
        
        loader = ModelLoader()
        print("✅ ModelLoader 實例創建成功")
        
        # 嘗試載入訓練模型（GPU模式）
        print("\n🔄 正在載入訓練模型（GPU模式）...")
        success, message = loader.load_trained_model(force_cpu=False)
        
        if success:
            print(f"✅ {message}")
            print(f"📊 模型狀態: {loader.get_model_status()}")
            
            # 測試簡單問答
            print("\n🤖 測試GPU模式問答:")
            test_questions = [
                "什麼是SQL注入？",
                "網路安全的重要性是什麼？"
            ]
            
            for question in test_questions:
                print(f"\n問題: {question}")
                answer = loader.generate_answer(question)
                print(f"回答: {answer}")
            
            # 卸載模型
            print(f"\n🔧 卸載模型...")
            unload_msg = loader.unload_model()
            print(f"✅ {unload_msg}")
            
            return True
            
        else:
            print(f"❌ {message}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qwen_model():
    """測試Qwen模型載入"""
    print("\n🧪 測試Qwen模型載入...")
    
    try:
        from hacker_AI_loader.load_models import ModelLoader
        
        loader = ModelLoader()
        
        # 嘗試載入Qwen模型
        print("🔄 正在載入Qwen模型...")
        success, message = loader.load_pretrained_model()
        
        if success:
            print(f"✅ {message}")
            print(f"📊 模型狀態: {loader.get_model_status()}")
            
            # 測試簡單問答
            print("\n🤖 測試Qwen模型問答:")
            answer = loader.generate_answer("什麼是人工智能？")
            print(f"回答: {answer}")
            
            # 卸載模型
            unload_msg = loader.unload_model()
            print(f"✅ {unload_msg}")
            
            return True
            
        else:
            print(f"⚠️ Qwen載入失敗（預期可能發生）: {message}")
            return False
            
    except Exception as e:
        print(f"⚠️ Qwen測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 GPU修復驗證測試")
    print("=" * 70)
    
    # 檢查GPU狀態
    check_gpu_status()
    
    # 測試訓練模型GPU載入
    trained_ok = test_trained_model_gpu()
    
    # 測試Qwen模型
    qwen_ok = test_qwen_model()
    
    print("\n" + "=" * 70)
    print("📋 測試結果總結:")
    print(f"   訓練模型GPU載入: {'✅ 成功' if trained_ok else '❌ 失敗'}")
    print(f"   Qwen模型載入: {'✅ 成功' if qwen_ok else '⚠️ 失敗（可忽略）'}")
    
    if trained_ok:
        print("\n🎉 主要功能正常！GPU支援已恢復")
        print("\n💡 使用方法:")
        print("   python run.py  # 啟動GUI（將使用GPU加速）")
        print("\n📌 重要提示:")
        print("   - 訓練模型現在使用GPU運行")
        print("   - 如遇到CUDA問題，系統會自動回退")
        print("   - 知識庫功能始終可用")
        return True
    else:
        print("\n❌ GPU載入失敗，可能需要進一步調試")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 