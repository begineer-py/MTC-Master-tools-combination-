import logging
from flask import Flask, request, jsonify, make_response
from instance.models import db, migrate
from datetime import timedelta
from flask_session import Session
import time
import sys
import os
import shutil
from sqlalchemy.exc import OperationalError
from app.blueprint_set import register_blueprints
import requests
from requests.exceptions import RequestException
from config.config import Config_dict as ConfigDict, LogConfig
import importlib.util

# 導入 FlareSolverr 管理器
try:
    from app.flaresolverr_set.start_flaresolverr import flaresolverr_manager, auto_start_flaresolverr
    FLARESOLVERR_AVAILABLE = True
except ImportError as e:
    print(f"警告：無法導入 FlareSolverr 管理器: {e}")
    FLARESOLVERR_AVAILABLE = False


def check_flaresolverr():
    """檢查 FlareSolverr 服務是否正在運行"""
    if FLARESOLVERR_AVAILABLE:
        return flaresolverr_manager.is_flaresolverr_running()
    else:
        # 備用檢查方法
        try:
            response = requests.post('http://localhost:8191/v1',
                                     json={
                                         "cmd": "sessions.list"
                                     },
                                     timeout=5)
            return response.status_code == 200
        except RequestException:
            return False


def start_flaresolverr():
    """啟動 FlareSolverr 服務"""
    if FLARESOLVERR_AVAILABLE:
        try:
            result = auto_start_flaresolverr()
            return result.get('success', False)
        except Exception as e:
            print(f"啟動 FlareSolverr 時出錯: {e}")
            return False
    else:
        print("FlareSolverr 管理器不可用，跳過自動啟動")
        return False


def ensure_directories_exist():
    """確保必要的目錄存在"""
    required_dirs = [
        "instance",
        "instance/backups",
        "instance/tools",
        "logs",
        "flask_session"
    ]

    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)


def load_db_manager():
    """動態加載數據庫管理模塊"""
    db_manager_path = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), 'instance', 'tools', 'db_manager.py')

    # 如果文件不存在，返回None
    if not os.path.exists(db_manager_path):
        return None

    # 動態加載模塊
    spec = importlib.util.spec_from_file_location(
        "db_manager", db_manager_path)
    if spec is None or spec.loader is None:
        return None

    db_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_manager)

    return db_manager


def unlock_database(app):
    """檢查並解鎖數據庫文件"""
    # 嘗試使用數據庫管理模塊
    db_manager = load_db_manager()

    if db_manager:
        db_path = os.path.abspath(os.path.join(os.path.dirname(
            os.path.dirname(__file__)), 'instance', 'c2.db'))
        app.logger.info(f"使用數據庫管理模塊解鎖數據庫: {db_path}")

        # 調用數據庫管理模塊的解鎖函數
        db_manager.unlock_database(db_path)
        return True

    # 如果無法加載模塊，使用內置的解鎖方法
    db_path = os.path.abspath(os.path.join(os.path.dirname(
        os.path.dirname(__file__)), 'instance', 'c2.db'))
    db_shm_path = f"{db_path}-shm"
    db_wal_path = f"{db_path}-wal"

    app.logger.info(f"檢查數據庫路徑: {db_path}")

    # 確保數據庫目錄存在
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        app.logger.info(f"創建數據庫目錄: {db_dir}")

    # 檢查是否存在鎖文件
    lock_files = []
    if os.path.exists(db_shm_path):
        lock_files.append(db_shm_path)
    if os.path.exists(db_wal_path):
        lock_files.append(db_wal_path)

    if lock_files:
        # 如果數據庫文件存在，則創建備份
        backup_time = time.strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(db_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        if os.path.exists(db_path):
            backup_path = os.path.join(backup_dir, f"c2_{backup_time}.db")
            try:
                shutil.copy2(db_path, backup_path)
                app.logger.info(f"數據庫備份創建: {backup_path}")
            except Exception as e:
                app.logger.error(f"備份數據庫時出錯: {str(e)}")

        # 嘗試刪除鎖文件
        for lock_file in lock_files:
            try:
                os.remove(lock_file)
                app.logger.info(f"刪除鎖文件: {lock_file}")
            except Exception as e:
                app.logger.error(f"無法刪除鎖文件 {lock_file}: {str(e)}")

    # 確保數據庫文件存在（即使是空的）
    if not os.path.exists(db_path):
        try:
            # 創建空的數據庫文件
            with open(db_path, 'wb') as f:
                pass
            app.logger.info(f"創建新的數據庫文件: {db_path}")
        except Exception as e:
            app.logger.error(f"無法創建數據庫文件: {str(e)}")

    return True


def setup_logging(app):
    """配置应用日志 - 使用增強版本"""
    return LogConfig.setup_enhanced_logging(app)


def create_app(config_name="default"):
    """創建 Flask 應用程序實例"""
    # 確保所需目錄存在
    ensure_directories_exist()

    # 創建應用實例
    app = Flask(__name__, template_folder='../templates',
                static_folder='../static')

    # 配置應用
    app.config.from_object(ConfigDict[config_name])  # type: ignore
    app.permanent_session_lifetime = timedelta(minutes=30)

    # 配置静态文件
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 禁用静态文件缓存
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # 启用模板自动重载

    # 添加全域 CORS 標頭
    @app.after_request
    def after_request(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
        response.headers['Access-Control-Max-Age'] = '86400'  # 24 小時
        return response

    # 處理 OPTIONS 預檢請求
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
            response.headers['Access-Control-Max-Age'] = '86400'
            return response

    # 初始化數據庫
    db.init_app(app)
    migrate.init_app(app, db)

    # 初始化 Session
    Session(app)

    # 配置日誌
    setup_logging(app)

    # 根據配置決定是否自動啟動 FlareSolverr
    if app.config.get('FLARESOLVERR_AUTO_START', True):
        try:
            app.logger.info("正在檢查 FlareSolverr 服務...")

            if FLARESOLVERR_AVAILABLE:
                # 配置 FlareSolverr 管理器
                flaresolverr_manager.flaresolverr_host = app.config.get(
                    'FLARESOLVERR_HOST', 'localhost')
                flaresolverr_manager.flaresolverr_port = app.config.get(
                    'FLARESOLVERR_PORT', 8191)
                flaresolverr_manager.flaresolverr_url = f"http://{flaresolverr_manager.flaresolverr_host}:{flaresolverr_manager.flaresolverr_port}"
                flaresolverr_manager.auto_restart = app.config.get(
                    'FLARESOLVERR_AUTO_RESTART', True)
                flaresolverr_manager.max_restart_attempts = app.config.get(
                    'FLARESOLVERR_MAX_RESTART_ATTEMPTS', 5)

                app.logger.info("正在啟動 FlareSolverr 服務...")
                flaresolverr_success = start_flaresolverr()
                if flaresolverr_success:
                    app.logger.info("✅ FlareSolverr 服務已啟動")
                else:
                    app.logger.warning("⚠️ FlareSolverr 服務啟動失敗，但應用將繼續運行")
            else:
                app.logger.warning("⚠️ FlareSolverr 管理器不可用，跳過自動啟動")
        except Exception as e:
            app.logger.error(f"❌ FlareSolverr 服務啟動時發生錯誤：{str(e)}，但應用將繼續運行")
    else:
        app.logger.info("🔧 FlareSolverr 自動啟動已禁用")

    # 註冊藍圖
    register_blueprints(app)

    # 設置健康檢查路由
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy"})

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    # 禁用重載器
    app.run(port=1337, debug=ConfigDict['default'].DEBUG, use_reloader=False)
