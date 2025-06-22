import subprocess
import sys
import os

def create_and_setup_venv(venv_name="venv"):
    """
    創建一個新的虛擬環境並安裝 requirements.txt 中的依賴。
    """
    print(f"[*] 正在創建虛擬環境: {venv_name}")
    try:
        # 創建虛擬環境
        subprocess.run(["python3", "-m", "venv", venv_name], check=True)
        print(f"[+] 虛擬環境 '{venv_name}' 創建成功！")

        # 激活虛擬環境並安裝 requirements.txt
        requirements_path = os.path.join(os.getcwd(), "requirements.txt")
        if os.path.exists(requirements_path):
            print(f"[*] 找到 requirements.txt，正在安裝依賴...")
            # 構建虛擬環境中 pip 的路徑
            pip_path = os.path.join(os.getcwd(), venv_name, "bin", "pip")
            if not os.path.exists(pip_path):
                # Fallback for Windows or other systems where pip might be in Scripts
                pip_path = os.path.join(os.getcwd(), venv_name, "Scripts", "pip")

            if os.path.exists(pip_path):
                subprocess.run([pip_path, "install", "-r", requirements_path], check=True)
                print(f"[+] 依賴安裝成功！")
            else:
                print(f"[!] 警告：無法找到虛擬環境中的 pip。請手動激活虛擬環境並安裝依賴。")
        else:
            print("[*] 未找到 requirements.txt 文件，跳過依賴安裝。")

    except subprocess.CalledProcessError as e:
        print(f"[!] 錯誤：創建虛擬環境或安裝依賴失敗：{e}")
    except Exception as e:
        print(f"[!] 發生意外錯誤：{e}")

if __name__ == "__main__":
    # 這裡可以根據需要添加參數解析，讓用戶可以自定義虛擬環境名稱
    # 比如：python create_venv.py my_custom_venv
    if len(sys.argv) > 1:
        venv_dir_name = sys.argv[1]
        create_and_setup_venv(venv_dir_name)
    else:
        create_and_setup_venv() # 使用默認名稱 'venv' 