"""
WSGI config for c2_core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os # 導入Python的os模塊，用於操作系統相關功能

from django.core.wsgi import get_wsgi_application # 從Django核心的wsgi模塊導入get_wsgi_application函數

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'c2_core.settings') # 設定DJANGO_SETTINGS_MODULE環境變數，指向專案的設定檔

application = get_wsgi_application() # 獲取WSGI應用程式，供Web伺服器調用