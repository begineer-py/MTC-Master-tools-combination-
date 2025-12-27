"""
ASGI config for c2_core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os  # 導入os模塊，用於與操作系統交互，例如訪問環境變量

from django.core.asgi import (
    get_asgi_application,
)  # 從Django的ASGI模塊導入獲取ASGI應用實例的函數

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "c2_core.settings"
)  # 設置Django應用的默認設置模塊路徑

application = (
    get_asgi_application()
)  # 調用函數獲取Django的ASGI應用實例，作為ASGI服務器的入口點
