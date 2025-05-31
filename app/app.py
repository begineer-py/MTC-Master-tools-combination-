import logging
from flask import Flask, request, jsonify
from instance.models import db, migrate
from datetime import timedelta
from flask_session import Session
import time
import sys
import os
import shutil
from sqlalchemy.exc import OperationalError
# 修復導入路徑 - 註釋掉有問題的導入
# from requirements.reconnaissance.scanner_flaresolverr.start_flaresolverr import start_flaresolverr
from app.blueprint_set import register_blueprints
from flask_cors import CORS
import requests
from requests.exceptions import RequestException
from config.config import Config, LogConfig, FlaresolverrConfig
import importlib.util

def check_flaresolverr():
    """檢查 FlareSolverr 服務是否正在運行"""
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
    """啟動 FlareSolverr 服務的替代實現"""
    try:
        # 檢查是否已經運行
        if check_flaresolverr():
            return True
        
        # 嘗試啟動 FlareSolverr（如果安裝了的話）
        # 這裡可以添加啟動邏輯，暫時返回 False
        return False
    except Exception as e:
        print(f"啟動 FlareSolverr 時出錯: {e}")
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
    db_manager_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'tools', 'db_manager.py')
    
    # 如果文件不存在，返回None
    if not os.path.exists(db_manager_path):
        return None
        
    # 動態加載模塊
    spec = importlib.util.spec_from_file_location("db_manager", db_manager_path)
    db_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_manager)
    
    return db_manager

def unlock_database(app):
    """檢查並解鎖數據庫文件"""
    # 嘗試使用數據庫管理模塊
    db_manager = load_db_manager()
    
    if db_manager:
        db_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'c2.db'))
        app.logger.info(f"使用數據庫管理模塊解鎖數據庫: {db_path}")
        
        # 調用數據庫管理模塊的解鎖函數
        db_manager.unlock_database(db_path)
        return True
    
    # 如果無法加載模塊，使用內置的解鎖方法
    db_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'c2.db'))
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
    """配置应用日志"""
    # 设置日志配置
    formatter = logging.Formatter(LogConfig.LOG_FORMAT, LogConfig.LOG_DATE_FORMAT)
    
    # 添加文件日志处理器
    if os.path.exists('logs'):
        file_handler = logging.FileHandler('logs/app.txt', encoding='utf-8')
        file_handler.setLevel(logging.getLevelName(LogConfig.LOG_LEVEL))
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
    
    # 添加控制台日志处理器
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.getLevelName(LogConfig.LOG_LEVEL))
    stream_handler.setFormatter(formatter)
    app.logger.addHandler(stream_handler)
    
    # 设置应用日志级别
    app.logger.setLevel(logging.getLevelName(LogConfig.LOG_LEVEL))

def create_app(config_name="default"):
    """創建 Flask 應用程序實例"""
    # 確保所需目錄存在
    ensure_directories_exist()
    
    # 創建應用實例
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # 配置應用
    app.config.from_object(Config[config_name])
    app.permanent_session_lifetime = timedelta(minutes=30)
    
    # 配置静态文件
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 禁用静态文件缓存
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # 启用模板自动重载
    
    # 初始化數據庫
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 初始化 Session
    Session(app)
    CORS(app)
    
    # 配置日誌
    setup_logging(app)
    
    try:
        # 嘗試啟動 FlareSolverr 服務
        print("正在啟動 FlareSolverr 服務...")
        flaresolverr_success = start_flaresolverr()
        if flaresolverr_success:
            print("FlareSolverr 服務已啟動")
        else:
            print("FlareSolverr 服務啟動失敗，但應用將繼續運行")
    except Exception as e:
        print(f"FlareSolverr 服務啟動時發生錯誤：{str(e)}，但應用將繼續運行")
    
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
    app.run(port=5000, debug=Config.DEBUG, use_reloader=False)  # 禁用重載器