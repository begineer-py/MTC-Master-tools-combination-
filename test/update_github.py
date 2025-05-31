import os
import sys
import subprocess
from pathlib import Path

def run_command(command, error_message):
    """執行命令並處理錯誤"""
    try:
        subprocess.run(command, check=True, shell=True, encoding='utf-8')
        return True
    except subprocess.CalledProcessError:
        print(f"\033[91m錯誤: {error_message}\033[0m")  # 紅色錯誤信息
        return False

def main():
    # 設置控制台編碼為 UTF-8
    if sys.platform == 'win32':
        os.system('chcp 65001')
    
    # 獲取提交信息
    commit_message = input("\033[93m請輸入提交信息: \033[0m")  # 黃色提示
    
    # 檢查提交信息是否為空
    if not commit_message.strip():
        print("\033[93m警告: 提交信息不能為空，腳本終止。\033[0m")  # 黃色警告
        return
    
    # 設置倉庫路徑
    repo_path = Path(os.getcwd())

    # 檢查倉庫目錄是否存在
    if not repo_path.exists():
        print(f"\033[91m錯誤: 倉庫目錄 {repo_path} 不存在！\033[0m")
        return
    
    # 切換到倉庫根目錄
    os.chdir(repo_path)
    
    # 設置 Git 中文路徑支持
    run_command("git config --global core.quotepath false", "設置 Git 編碼失敗")
    
    # 執行 Git 操作
    print("\033[92m正在添加更改...\033[0m")  # 綠色信息
    if not run_command("git add .", "git add 失敗，可能是權限不足或 Git 未正確安裝"):
        return
    
    print(f"\033[92m正在提交更改，提交信息為: '{commit_message}'\033[0m")
    if not run_command(f'git commit -m "{commit_message}"', "git commit 失敗，請檢查是否有需要提交的更改"):
        return
    
    print("\033[92m正在推送更改...\033[0m")
    if not run_command("git push origin main --force", "git push 失敗，請檢查遠程倉庫配置或網絡連接"):
        return
    
    print("\033[92m正在檢查 Git 狀態...\033[0m")
    run_command("git status", "無法獲取 Git 狀態")
    
    print("\033[92m腳本執行完畢。\033[0m")

if __name__ == "__main__":
    main() 