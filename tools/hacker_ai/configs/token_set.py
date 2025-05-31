#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

# API令牌 (請設置環境變量 HF_API_TOKEN)
HF_API_TOKEN = None  # 不再硬編碼令牌

def get_token():
    """獲取Hugging Face API令牌
    優先級: 環境變量
    """
    # 檢查環境變量
    env_token = os.environ.get("HF_API_TOKEN")
    if env_token:
        return env_token
    
    # 如果沒有環境變量，返回 None 並提示用戶設置
    print("警告: 未找到 HF_API_TOKEN 環境變量")
    print("請設置環境變量: export HF_API_TOKEN=your_token_here")
    return None

def set_token_from_file(token_file_path):
    """從文件中讀取令牌（可選功能）
    
    Args:
        token_file_path (str): 令牌文件路徑
        
    Returns:
        str: API令牌，如果文件不存在則返回None
    """
    try:
        if os.path.exists(token_file_path):
            with open(token_file_path, 'r', encoding='utf-8') as f:
                token = f.read().strip()
                return token if token else None
    except Exception as e:
        print(f"讀取令牌文件失敗: {e}")
    return None

if __name__ == "__main__":
    # 測試獲取令牌
    token = get_token()
    if token:
        print(f"當前使用的API令牌: {token[:5]}...{token[-4:]}")
    else:
        print("未設置API令牌")
        print("使用方法:")
        print("1. 設置環境變量: export HF_API_TOKEN=your_token_here")
        print("2. 或在代碼中調用 set_token_from_file('/path/to/token/file')")
