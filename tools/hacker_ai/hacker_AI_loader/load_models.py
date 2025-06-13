#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI模型載入器模組
=================

此模組負責載入和管理AI模型，支持以下功能：
- 載入訓練好的HackerAI模型
- 載入Qwen預訓練模型作為備用
- GPU/CPU自動選擇和管理
- 文本生成和問答處理
- 模型記憶體管理

主要類別：
- ModelLoader: 模型載入和管理的核心類

作者: HackerAI團隊
版本: 2.0 (GPU優化版)
"""

import os
import sys
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, AutoProcessor
import torch
import json
from pathlib import Path
import warnings

# 抑制transformers警告信息以保持輸出清潔
warnings.filterwarnings("ignore")

class ModelLoader:
    """
    AI模型載入器
    
    負責管理AI模型的載入、卸載和文本生成功能。
    支持GPU加速和CPU備用模式。
    """
    
    def __init__(self):
        """
        初始化模型載入器
        
        設置模型路徑和初始狀態變數
        """
        # 模型文件夾路徑（相對於當前文件的上級目錄）
        self.models_path = os.path.join(os.path.dirname(__file__), "..", "models")
        
        # 模型組件
        self.tokenizer = None      # 分詞器
        self.model = None          # 模型主體
        self.pipeline = None       # 文本生成管道
        self.processor = None      # VL模型處理器（針對Qwen2.5-VL）
        
        # 狀態標誌
        self.is_loaded = False     # 模型是否已載入
        self.use_cpu = False       # 是否強制使用CPU

        
    def load_trained_model(self, force_cpu=False):
        """
        載入訓練好的HackerAI模型
        
        會自動檢查並嘗試載入修復後的模型
        
        Args:
            force_cpu (bool): 是否強制使用CPU，默認False
            
        Returns:
            tuple: (成功標誌, 狀態信息)
        """
        # 優先檢查修復後的模型
        fixed_model_path = os.path.join(self.models_path, "hacker_ai_fixed")
        trained_model_path = os.path.join(self.models_path, "hacker_ai_trained")
        
        model_path = None
        model_type = ""
        
        if os.path.exists(fixed_model_path):
            model_path = fixed_model_path
            model_type = "修復後的"
            print("🔧 發現修復後的模型，將使用修復版本")
        elif os.path.exists(trained_model_path):
            model_path = trained_model_path
            model_type = "原始"
            print("⚠️ 使用原始訓練模型（可能存在NaN問題）")
        else:
            return False, f"找不到訓練好的模型: {trained_model_path} 或 {fixed_model_path}"
        
        try:
            print(f"📥 載入{model_type}HackerAI模型: {model_path}")
            
            # 載入分詞器
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 檢查是否強制使用CPU
            use_cuda = torch.cuda.is_available() and not force_cpu
            self.use_cpu = not use_cuda
            
            print(f"使用設備: {'CUDA' if use_cuda else 'CPU'}")
            
            # 載入模型
            if use_cuda:
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float32,
                    device_map=None
                ).to('cpu')
            
            # 檢查模型權重是否正常
            nan_count = 0
            for name, param in self.model.named_parameters():
                if torch.isnan(param).any():
                    nan_count += 1
                    break  # 只檢查第一個就夠了
            
            if nan_count > 0:
                warning_msg = (
                    "⚠️ 警告: 模型仍存在NaN權重問題。\n"
                    "建議使用修復腳本: python fix_nan_model.py\n"
                    "或使用Qwen1.5-1.8B-Chat模型作為替代方案。"
                )
                print(warning_msg)
                return False, warning_msg
            
            # 創建生成管道
            from transformers import pipeline
            
            if use_cuda:
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    max_length=512,
                    do_sample=True,
                    temperature=0.8,
                    top_p=0.95,
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    return_full_text=False
                )
            else:
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=-1,  # CPU
                    max_length=512,
                    do_sample=True,
                    temperature=0.8,
                    top_p=0.95,
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    return_full_text=False
                )
            
            self.is_loaded = True
            success_msg = f"✅ {model_type}HackerAI模型載入成功！(使用{'GPU' if use_cuda else 'CPU'})"
            print(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"載入{model_type}模型失敗: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def load_pretrained_model(self, model_path=None):
        """
        載入Qwen2.5-VL預訓練模型作為備用
        
        注意：Qwen2.5-VL是視覺語言模型，需要特殊的載入和處理流程
        
        Args:
            model_path (str, optional): 自定義模型路徑，默認使用內建Qwen路徑
            
        Returns:
            tuple: (成功標誌, 狀態信息)
        """
        try:
            # 構建Qwen模型路徑（默認使用本地Qwen1.5-1.8B-Chat）
            if model_path is None:
                model_path = os.path.join(self.models_path, "Qwen1.5-1.8B-Chat")
            
            # 檢查模型文件夾是否存在
            if not os.path.exists(model_path):
                return False, f"找不到Qwen模型: {model_path}"
            
            print(f"正在載入Qwen預訓練模型: {model_path}")
            
            # 自動檢測CUDA可用性
            use_cuda = torch.cuda.is_available()
            self.use_cpu = not use_cuda
            
            print(f"使用設備: {'CUDA' if use_cuda else 'CPU'}")
            
            # Qwen1.5-1.8B-Chat是純文本模型，使用標準載入流程
            print("🔄 載入Qwen1.5-1.8B-Chat純文本模型...")
            
            # 載入分詞器
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            
            # 根據設備載入模型
            if use_cuda:
                # GPU模式：使用float16和自動設備映射
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,    # GPU使用float16節省顯存
                    device_map="auto",            # 自動分配GPU
                    trust_remote_code=True        # 允許執行自定義代碼
                )
                
                # GPU模式的pipeline（不指定device）
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    max_length=512,                           # 適當增加生成長度
                    do_sample=True,                           # 啟用採樣
                    temperature=0.8,                          # 控制隨機性
                    top_p=0.95,                               # 核心採樣
                    repetition_penalty=1.1,                   # 重複懲罰
                    pad_token_id=self.tokenizer.eos_token_id, # 填充token
                    eos_token_id=self.tokenizer.eos_token_id, # 結束token
                    return_full_text=False                    # 只返回新生成文本
                )
            else:
                # CPU模式：使用float32確保精度
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float32,    # CPU使用float32
                    device_map=None,              # 不使用設備映射
                    trust_remote_code=True
                ).to('cpu')                       # 明確移到CPU
                
                # CPU模式的pipeline（指定device）
                device = -1  # CPU設備ID
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=device,                            # 指定CPU設備
                    max_length=512,
                    do_sample=True,
                    temperature=0.8,
                    top_p=0.95,
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    return_full_text=False
                )
            
            # 設置pad_token（如果不存在）
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            print("✅ 載入為Qwen1.5-1.8B-Chat純文本模型")
            
            # 設置載入狀態
            self.is_loaded = True
            return True, f"Qwen1.5-1.8B-Chat模型載入成功！(使用{'GPU' if use_cuda else 'CPU'})"
            
        except Exception as e:
            error_msg = str(e)
            print(f"詳細錯誤: {error_msg}")
            # 提供用戶友好的錯誤信息和建議
            return False, f"Qwen模型載入失敗: {error_msg}\n建議：使用純文本版本的Qwen2模型或其他文本生成模型"

    def generate_answer(self, question):
        """
        使用AI模型生成問題的回答
        
        Args:
            question (str): 用戶輸入的問題
            
        Returns:
            str: AI生成的回答或錯誤提示
        """
        # 直接使用AI模型生成回答，不使用知識庫
        # 如果模型已載入，使用AI生成回答
        if self.is_loaded and (self.pipeline or self.model):
            try:
                # 構建問答提示語
                prompt = f"問題: {question}\n回答:"
                
                # 使用pipeline進行文本生成（適用於所有模型）
                if self.pipeline:
                    # 數值穩定性優化的生成參數（避免inf/nan錯誤）
                    generation_kwargs = {
                        "max_new_tokens": 200,                       # 適中的生成長度
                        "num_return_sequences": 1,                   # 生成序列數量
                        "temperature": 0.6,                          # 較低的隨機性
                        "do_sample": True,                           # 啟用採樣生成
                        "top_p": 0.85,                               # 保守的核心採樣
                        "top_k": 40,                                 # 限制候選詞彙
                        "repetition_penalty": 1.02,                  # 輕微的重複懲罰
                        "no_repeat_ngram_size": 2,                   # 避免重複n-gram
                        "pad_token_id": self.tokenizer.eos_token_id, # 填充token ID
                        "eos_token_id": self.tokenizer.eos_token_id, # 結束token ID
                        "return_full_text": False,                   # 只返回新生成部分
                        "clean_up_tokenization_spaces": True        # 清理token化空格
                    }
                    
                    # 使用pipeline生成回答
                    response = self.pipeline(prompt, **generation_kwargs)
                    
                    # 解析pipeline返回結果
                    if response and len(response) > 0:
                        generated_text = response[0].get('generated_text', '')
                        # 清理prompt殘留（防止return_full_text=False失效）
                        answer = generated_text.replace(prompt, "").strip()
                        
                        # 檢查回答質量
                        if answer and len(answer) > 5:
                            return f"🤖 AI回答: {answer}"
                        else:
                            return self.get_fallback_answer(question)
                    else:
                        return self.get_fallback_answer(question)
                        
                else:
                    # 模型已載入但沒有可用的生成器
                    return self.get_fallback_answer(question)
                    
            except Exception as e:
                # 捕獲所有生成過程中的錯誤
                error_msg = str(e)
                print(f"AI生成錯誤: {error_msg}")
                return f"AI暫時無法回答: {self.get_fallback_answer(question)}"
        else:
            # 模型未載入
            return self.get_fallback_answer(question)

    def get_fallback_answer(self, question):
        """
        獲取備用回答（當AI模型無法正常生成時使用）
        
        Args:
            question (str): 用戶問題
            
        Returns:
            str: 備用回答信息
        """
        return "很抱歉，AI模型暫時無法處理您的問題。請嘗試重新表述或檢查模型狀態。"

    def get_model_status(self):
        """
        獲取當前模型的載入狀態和基本信息
        
        Returns:
            str: 模型狀態描述字符串
        """
        if self.is_loaded and self.model:
            try:
                # 嘗試獲取模型類型信息
                if hasattr(self.model, 'config') and hasattr(self.model.config, '_name_or_path'):
                    model_path = str(self.model.config._name_or_path)
                    
                    # 根據路徑判斷模型類型
                    if "hacker_ai_trained" in model_path:
                        model_type = "訓練模型"
                    elif "Qwen" in model_path:
                        model_type = "Qwen模型"
                    else:
                        model_type = "預訓練模型"
                else:
                    model_type = "未知模型"
                
                # 檢測運行設備
                device_info = "GPU" if hasattr(self.model, 'device') and 'cuda' in str(self.model.device) else "CPU"
                return f"已載入 - {model_type} ({device_info})"
                
            except Exception:
                # 狀態檢查出錯時的備用信息
                return "已載入 - 模型狀態未知"
        else:
            return "未載入"

    def unload_model(self):
        """
        卸載當前載入的模型並釋放記憶體
        
        清理步驟：
        1. 清空模型組件引用
        2. 清理GPU記憶體緩存
        3. 強制垃圾回收
        
        Returns:
            str: 卸載狀態信息
        """
        try:
            # 清空所有模型組件的引用
            self.tokenizer = None        # 分詞器
            self.model = None           # 模型主體
            self.pipeline = None        # 生成管道
            if hasattr(self, 'processor'):
                self.processor = None   # VL模型處理器
            self.is_loaded = False      # 重置載入狀態
            
            # 清理GPU記憶體緩存（如果可用）
            if torch.cuda.is_available():
                try:
                    torch.cuda.empty_cache()     # 清空GPU緩存
                    print("🔧 GPU記憶體已清理")
                except Exception as e:
                    # GPU清理錯誤不應影響主要流程
                    print(f"清理GPU記憶體時出現錯誤（忽略）: {e}")
            
            # 強制Python垃圾回收
            import gc
            gc.collect()
            
            return "模型已卸載，記憶體已釋放"
            
        except Exception as e:
            return f"卸載模型時發生錯誤: {str(e)}"
        
