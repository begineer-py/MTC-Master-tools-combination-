# c2_core/apps.py

from django.apps import AppConfig
import sys


class C2CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "c2_core"

    def ready(self):
        print("🚀 C2-CORE 應用準備就緒...")

        # --- 初始化日誌系統 ---
        print("  [*] 日誌系統初始化中...")
        from .config.logging import LogConfig

        LogConfig.setup_enhanced_logging()
        print("  [✅] 日誌系統初始化完成。")

        # --- 觸發 AI 服務 URL 的生成 ---
        # Config 類已經在加載時解析了 docker-compose
        # 我們只需要再解析 config.yaml 並填充 AI_SERVICE_URLS
        print("  [*] 動態加載 AI 服務 URL...")
        try:
            from scripts.generate_ai_proxy_urls import (
                generate_ai_urls_from_config,
                NYA_PROXY_CONFIG_PATH,
            )
            from .config.config import Config

            # Config 類已經為我們準備好了 nyaproxy 的基礎 URL
            base_url = Config.NYAPROXY_SPIDER_URL
            if base_url:
                ai_urls = generate_ai_urls_from_config(base_url, NYA_PROXY_CONFIG_PATH)
                Config.AI_SERVICE_URLS = ai_urls  # 填充動態列表
                print(f"  [✅] AI 服務 URL 加載完成: {len(ai_urls)} 個端點已註冊。")
            else:
                print(
                    "  [❌] 警告: 未能從 docker-compose 解析 nyaproxy_spider URL，跳過 AI URL 生成。",
                    file=sys.stderr,
                )

        except Exception as e:
            print(f"  [❌] 警告：動態加載 AI 服務 URL 失敗: {e}", file=sys.stderr)
