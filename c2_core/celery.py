# c2_core/celery.py

import os
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "c2_core.settings")

app = Celery("c2_core")

# --- 核心配置 ---
app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
app.conf.task_serializer = settings.CELERY_TASK_SERIALIZER
app.conf.result_serializer = settings.CELERY_RESULT_SERIALIZER
app.conf.accept_content = settings.CELERY_ACCEPT_CONTENT
app.conf.timezone = settings.CELERY_TIMEZONE

# 操！把這行加進來，命令 Celery Beat 去讀取資料庫裡的作戰計劃
app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"

# 這一行會自動發現所有 app 下的 tasks.py 文件
app.autodiscover_tasks()
