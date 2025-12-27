#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
from pathlib import Path
from urllib.parse import urljoin
import sys

# --- 配置 ---
# 假設此腳本位於 <project_root>/scripts/ 目錄下
# 我們的目標是定位到 <project_root>/docker/docker-compose.yml 和 <project_root>/docker/config.yaml
# 如果你的目錄結構不同，修改下面這兩行
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DOCKER_DIR = PROJECT_ROOT / "docker"
DOCKER_COMPOSE_PATH = DOCKER_DIR / "docker-compose.yml"
NYA_PROXY_CONFIG_PATH = DOCKER_DIR / "config.yaml"

# 目標服務和端口映射關鍵字
TARGET_SERVICE_NAME = "nyaproxy_spider"


def die(message: str):
    """打印錯誤信息並以非零狀態碼退出。"""
    print(f"操，出錯了: {message}", file=sys.stderr)
    sys.exit(1)


def parse_base_url_from_docker_compose(file_path: Path, service_name: str) -> str:
    """
    從 docker-compose.yml 文件中解析指定服務的基礎 URL。
    核心邏輯: 找到服務，抓取 'ports' 列表，解析出主機端口。

    :param file_path: docker-compose.yml 的路徑。
    :param service_name: 目標服務的名稱 (例如 'nyaproxy_spider')。
    :return: 構造好的基礎 URL (例如 'http://127.0.0.1:8502')。
    """
    print(f"[*] 正在解析 Docker Compose 文件: {file_path}")
    if not file_path.is_file():
        die(f"找不到 Docker Compose 文件: {file_path}")

    try:
        with open(file_path, "r") as f:
            compose_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        die(f"解析 YAML 文件失敗: {e}")
    except IOError as e:
        die(f"讀取文件失敗: {e}")

    services = compose_data.get("services", {})
    target_service = services.get(service_name)

    if not target_service:
        die(f"在 {file_path} 中找不到服務 '{service_name}'。")

    ports = target_service.get("ports", [])
    if not ports:
        die(f"服務 '{service_name}' 沒有定義任何 'ports'。")

    # 我們只關心第一個端口映射
    port_mapping = ports[0]
    try:
        # 格式是 "HOST_PORT:CONTAINER_PORT"
        host_port = str(port_mapping).split(":")[0]
        if not host_port.isdigit():
            die(f"端口映射格式無效: '{port_mapping}'。期望 'HOST:CONTAINER'。")
    except (IndexError, AttributeError):
        die(f"端口映射格式無效: '{port_mapping}'。期望 'HOST:CONTAINER'。")

    base_url = f"http://127.0.0.1:{host_port}"
    print(f"[+] 成功解析基礎 URL: {base_url}")
    return base_url


def generate_ai_urls_from_config(base_url: str, config_path: Path) -> dict:
    """
    【硬編碼修正版】解析 Nya Proxy 的配置文件，找出所有以 '_ai' 結尾的 API，
    並強制添加 '/api' 前綴，拼接成完整的內部 URL。

    :param base_url: 從 docker-compose 解析出的基礎 URL。
    :param config_path: Nya Proxy 的 config.yaml 路徑。
    :return: 一個字典，鍵是 API 名稱，值是完整的內部 URL。
    """
    print(f"[*] 正在解析 Nya Proxy 配置文件: {config_path}")
    if not base_url:
        die("基礎 URL (base_url) 為空，無法繼續解析。")
    if not config_path.is_file():
        die(f"找不到 Nya Proxy 配置文件: {config_path}")

    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        die(f"解析 YAML 文件失敗: {e}")
    except IOError as e:
        die(f"讀取文件失敗: {e}")

    apis = config_data.get("apis", {})
    if not apis:
        die("配置文件中找不到 'apis' 部分。")

    ### 修正：硬編碼 API 前綴 ###
    API_PREFIX = "/api"
    print(f"[*] 使用硬編碼的 API 前綴: '{API_PREFIX}'")

    ai_endpoints = {}
    print("[*] 正在掃描後綴為 '_ai' 的 API...")
    for api_name, api_config in apis.items():
        if api_name.endswith("_ai"):
            aliases = api_config.get("aliases")
            if not aliases or not isinstance(aliases, list):
                print(f"[!] 警告: AI 服務 '{api_name}' 沒有定義 'aliases'，已跳過。")
                continue

            # 使用第一個 alias 作為路徑
            api_path_suffix = aliases[0].lstrip("/")  # 確保後綴部分沒有開頭的斜杠

            ### 修正：拼接硬編碼前綴和後綴 ###
            # 確保 base_url 結尾沒有斜杠，API_PREFIX 開頭有斜杠，後綴部分開頭沒有斜杠
            # 這樣可以保證拼接的確定性
            full_url = f"{base_url.rstrip('/')}{API_PREFIX}/{api_path_suffix}"

            ai_endpoints[api_name] = full_url
            print(f"  - 發現: {api_name} -> {full_url}")

    if not ai_endpoints:
        print("[!] 在配置文件中沒有找到任何後綴為 '_ai' 的 API。")

    return ai_endpoints


def main():
    """主執行函數"""
    print("--- 開始自動化生成 AI 服務內部 URL ---")

    # 1. 解析基礎 URL
    base_url = parse_base_url_from_docker_compose(
        file_path=DOCKER_COMPOSE_PATH, service_name=TARGET_SERVICE_NAME
    )

    # 2. 生成 AI 端點
    ai_service_urls = generate_ai_urls_from_config(
        base_url=base_url, config_path=NYA_PROXY_CONFIG_PATH
    )

    print("\n--- 任務完成 ---")
    if ai_service_urls:
        print("生成的 AI 服務內部可訪問 URL 列表:")
        for name, url in ai_service_urls.items():
            print(f"  '{name}': '{url}'")
        print(
            "\n你可以將這些 URL 用於你的 `analyze_ai` 模塊中，通過內部代理調用 AI 服務。"
        )
    else:
        print("未生成任何 URL。請檢查你的配置文件。")
    print(ai_service_urls)


if __name__ == "__main__":
    main()
