#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import logging
from pathlib import Path

def cleanup_model_directory(model_dir):
    """清理模型目錄中推理不需要的文件"""
    
    # 設置日誌
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    model_path = Path(model_dir)
    if not model_path.exists():
        logger.error(f"模型目錄不存在: {model_dir}")
        return False
    
    logger.info(f"開始清理模型目錄: {model_dir}")
    
    # 推理時不需要的文件列表
    unnecessary_files = [
        "training_args.bin",  # 訓練參數
    ]
    
    # 推理時不需要的目錄
    unnecessary_dirs = [
        "logs",  # 訓練日誌
    ]
    
    total_saved = 0
    
    # 刪除不必要的文件
    for filename in unnecessary_files:
        file_path = model_path / filename
        if file_path.exists():
            try:
                file_size = file_path.stat().st_size
                file_path.unlink()
                total_saved += file_size
                logger.info(f"已刪除文件: {filename} ({file_size/1024:.1f} KB)")
            except Exception as e:
                logger.warning(f"刪除文件失敗 {filename}: {e}")
    
    # 刪除不必要的目錄
    for dirname in unnecessary_dirs:
        dir_path = model_path / dirname
        if dir_path.exists():
            try:
                # 計算目錄大小
                dir_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                shutil.rmtree(dir_path)
                total_saved += dir_size
                logger.info(f"已刪除目錄: {dirname} ({dir_size/1024:.1f} KB)")
            except Exception as e:
                logger.warning(f"刪除目錄失敗 {dirname}: {e}")
    
    if total_saved > 0:
        logger.info(f"清理完成，節省空間: {total_saved/1024/1024:.2f} MB")
    else:
        logger.info("沒有找到需要清理的文件")
    
    # 顯示最終模型目錄內容
    logger.info("清理後的模型文件:")
    for item in model_path.iterdir():
        if item.is_file():
            size_mb = item.stat().st_size / (1024 * 1024)
            logger.info(f"  {item.name}: {size_mb:.1f} MB")
    
    return True

def analyze_model_files(model_dir):
    """分析模型文件用途"""
    
    essential_files = {
        "model.safetensors": "✅ 必需 - 模型權重",
        "config.json": "✅ 必需 - 模型配置", 
        "tokenizer.json": "✅ 必需 - 分詞器",
        "vocab.json": "✅ 必需 - 詞彙表",
        "merges.txt": "✅ 必需 - 分詞合併規則",
        "special_tokens_map.json": "✅ 必需 - 特殊符號映射",
        "tokenizer_config.json": "✅ 必需 - 分詞器配置",
        "generation_config.json": "⚠️ 可選 - 生成配置（可自定義）",
        "training_args.bin": "❌ 不需要 - 訓練參數",
        "logs/": "❌ 不需要 - 訓練日誌"
    }
    
    print(f"\n📁 模型目錄分析: {model_dir}")
    print("=" * 50)
    
    model_path = Path(model_dir)
    total_size = 0
    
    for item in model_path.rglob('*'):
        if item.is_file():
            size = item.stat().st_size
            total_size += size
            relative_path = item.relative_to(model_path)
            
            # 檢查文件類型
            file_key = str(relative_path)
            if item.is_dir():
                file_key += "/"
            
            status = essential_files.get(file_key, "❓ 未知用途")
            
            print(f"{status}")
            print(f"  📄 {relative_path}: {size/1024/1024:.1f} MB")
    
    print("=" * 50)
    print(f"總大小: {total_size/1024/1024:.1f} MB")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("使用方法: python cleanup_model.py <模型目錄路徑>")
        print("例如: python cleanup_model.py ./models/hacker_ai_trained")
        sys.exit(1)
    
    model_directory = sys.argv[1]
    
    # 先分析文件
    analyze_model_files(model_directory)
    
    # 詢問是否清理
    response = input("\n是否清理不需要的文件? (y/n): ")
    if response.lower() in ['y', 'yes', '是']:
        cleanup_model_directory(model_directory)
    else:
        print("已取消清理操作") 