#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import shutil # 用於檢查 docker 命令是否存在

# --- 常量定義 ---
# 要安裝（拉取）的 ZAP Docker 鏡像名稱 (穩定版)
ZAP_DOCKER_IMAGE = "ghcr.io/zaproxy/zaproxy:stable"

# --- 核心功能函數 ---

def check_docker_command():
    """
    檢查系統環境中 'docker' 命令是否可用。
    """
    if shutil.which("docker") is None:
        print("[!] 錯誤：未在系統路徑中找到 'docker' 命令。", file=sys.stderr)
        print("   請確保 Docker 已經正確安裝，並且 Docker 的執行路徑已添加到系統的 PATH 環境變量中。", file=sys.stderr)
        print("   您可以從 Docker 官網獲取安裝指南：https://docs.docker.com/engine/install/", file=sys.stderr)
        return False
    print("[*] 檢測到 'docker' 命令。")
    # 注意：這裡僅檢查命令是否存在，不保證 Docker 守護進程正在運行。
    # 可以在這裡添加更複雜的檢查，例如運行 'docker info'，但會增加複雜性。
    return True

def pull_zap_docker_image(image_name: str):
    """
    使用 subprocess 調用 'docker pull' 命令來拉取指定的 Docker 鏡像。

    Args:
        image_name (str): 要拉取的 Docker 鏡像的名稱。

    Returns:
        bool: 如果成功拉取或鏡像已是最新版本，則返回 True，否則返回 False。
    """
    print(f"\n[*] 準備開始拉取 Docker 鏡像：{image_name}")
    print("    這可能需要一些時間，具體取決於您的網絡速度。")
    print("-" * 40)

    # 構建 docker pull 命令列表
    command = ["docker", "pull", image_name]

    try:
        # 執行 docker pull 命令
        # check=True: 如果命令返回非零退出碼（表示錯誤），則會引發 CalledProcessError
        # text=True: 使 stdout 和 stderr 作為字符串處理（如果需要捕獲的話）
        # capture_output=False (默認): 讓 docker pull 的輸出（例如下載進度）直接顯示在控制台上
        # stderr=subprocess.PIPE: 捕獲標準錯誤輸出，以便在出錯時顯示詳細信息
        process = subprocess.run(command, check=True, text=True, stderr=subprocess.PIPE)

        print("-" * 40)
        print(f"[+] 成功！Docker 鏡像 '{image_name}' 已成功拉取或已是最新版本。")
        return True

    except FileNotFoundError:
        # 這個錯誤理論上會被 check_docker_command 提前捕捉，但作為後備保留
        print("[!] 致命錯誤：執行 'docker' 命令失敗，似乎未找到該命令。", file=sys.stderr)
        print("   請再次確認 Docker 是否已正確安裝並配置好環境變量。", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        # docker pull 命令執行失敗（例如網絡問題、鏡像名稱錯誤、權限不足等）
        print("-" * 40, file=sys.stderr)
        print(f"[!] 錯誤：拉取 Docker 鏡像 '{image_name}' 失敗。", file=sys.stderr)
        print(f"   執行的命令: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"   Docker 返回錯誤碼: {e.returncode}", file=sys.stderr)
        if e.stderr:
            print(f"   詳細錯誤輸出:\n{e.stderr.strip()}", file=sys.stderr)
        else:
            print("   (未能捕獲到 Docker 的具體錯誤輸出)", file=sys.stderr)
        print("\n   可能的原因包括：", file=sys.stderr)
        print("     - 網絡連接問題（無法訪問 Docker Hub）", file=sys.stderr)
        print("     - Docker 守護進程未運行", file=sys.stderr)
        print("     - 鏡像名稱拼寫錯誤", file=sys.stderr)
        print("     - 磁盤空間不足", file=sys.stderr)
        print("     - (如果需要登錄私有倉庫) 未正確登錄 Docker", file=sys.stderr)
        return False
    except Exception as e:
        # 捕獲其他意想不到的異常
        print("-" * 40, file=sys.stderr)
        print(f"[!] 發生了意料之外的錯誤：{e}", file=sys.stderr)
        print("   腳本執行被中斷。", file=sys.stderr)
        return False

# --- 主程序入口 ---
if __name__ == "__main__":
    print("--- OWASP ZAP Docker 鏡像安裝腳本 ---")

    # 1. 檢查 Docker 命令是否可用
    if not check_docker_command():
        print("\n腳本因無法找到 Docker 命令而提前終止。", file=sys.stderr)
        sys.exit(1) # 以錯誤碼退出

    # 2. 執行鏡像拉取
    success = pull_zap_docker_image(ZAP_DOCKER_IMAGE)

    # 3. 根據結果退出
    if success:
        print("\n鏡像安裝（拉取）過程已完成。")
        sys.exit(0) # 成功退出
    else:
        print("\n鏡像安裝（拉取）過程中遇到錯誤。", file=sys.stderr)
        sys.exit(1) # 失敗退出