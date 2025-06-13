#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
診斷訓練模型問題
檢查模型權重和輸出數值
"""

import sys
import os
import torch
import numpy as np

# 確保可以導入自定義模組
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def diagnose_model():
    """診斷訓練模型的問題"""
    print("🔍 診斷訓練模型")
    print("=" * 50)
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        model_path = "models/hacker_ai_trained"
        
        print("📥 載入模型和分詞器...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32,
            device_map=None
        )
        
        print("✅ 模型載入成功")
        
        # 檢查模型權重
        print("\n🔬 檢查模型權重...")
        for name, param in model.named_parameters():
            if torch.isnan(param).any():
                print(f"❌ NaN檢測到在 {name}")
            elif torch.isinf(param).any():
                print(f"❌ Inf檢測到在 {name}")
            else:
                print(f"✅ {name}: 正常")
            break  # 只檢查第一個參數作為示例
        
        # 測試簡單輸入
        print("\n🧪 測試簡單輸入...")
        test_text = "Hello"
        inputs = tokenizer(test_text, return_tensors="pt")
        
        print(f"輸入token: {inputs['input_ids']}")
        
        with torch.no_grad():
            try:
                # 只做前向傳播，不生成
                outputs = model(**inputs)
                logits = outputs.logits
                
                print(f"Logits形狀: {logits.shape}")
                print(f"Logits數值範圍: {logits.min().item():.4f} 到 {logits.max().item():.4f}")
                
                # 檢查是否有NaN或Inf
                if torch.isnan(logits).any():
                    print("❌ Logits包含NaN")
                elif torch.isinf(logits).any():
                    print("❌ Logits包含Inf")
                else:
                    print("✅ Logits正常")
                    
                    # 嘗試計算概率
                    probs = torch.softmax(logits, dim=-1)
                    if torch.isnan(probs).any():
                        print("❌ 概率計算產生NaN")
                    elif torch.isinf(probs).any():
                        print("❌ 概率計算產生Inf")
                    elif (probs < 0).any():
                        print("❌ 概率包含負值")
                    else:
                        print("✅ 概率計算正常")
                        
                        # 嘗試簡單生成
                        print("\n🎯 嘗試最小生成...")
                        try:
                            gen_outputs = model.generate(
                                inputs['input_ids'],
                                max_new_tokens=5,
                                do_sample=False,  # 使用貪心解碼避免採樣問題
                                pad_token_id=tokenizer.eos_token_id
                            )
                            generated_text = tokenizer.decode(gen_outputs[0], skip_special_tokens=True)
                            print(f"✅ 生成成功: {generated_text}")
                        except Exception as e:
                            print(f"❌ 生成失敗: {e}")
                            
            except Exception as e:
                print(f"❌ 前向傳播失敗: {e}")
                
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_model() 