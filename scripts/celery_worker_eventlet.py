#!/usr/bin/env python3
"""
Start Celery worker with Eventlet monkey patching applied BEFORE Celery bootstraps.
Usage:
    python scripts/celery_worker_eventlet.py -A c2_core.celery:app worker -P eventlet -c 100 -l info
"""
import sys

# Patch as early as possible
import eventlet
eventlet.monkey_patch()

from celery.__main__ import main as celery_main

if __name__ == "__main__":
    # Delegate to Celery's CLI entrypoint
    sys.exit(celery_main())
