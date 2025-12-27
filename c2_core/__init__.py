from .celery import (
    app as celery_app,
)  # 從本地的 celery 模組導入 Celery 應用實例，並命名為 celery_app

__all__ = ("celery_app",)  # 定義當此模組被 * 導入時，應公開的名稱列表
default_app_config = "c2_core.apps.C2CoreConfig"  # 指定 Django 應用程式的預設配置類別
