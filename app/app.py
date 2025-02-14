import logging
from flask import Flask
from instance.models import db, migrate
from routes.zombie_routes import zombie_bp
from routes.user_dashboard_routes import user_bp
from routes.index_routes import index_bp
from routes.admin_routes import admin_bp
from routes.reconnaissance_route.attack_route import attack_bp
from routes.result_route import result_bp
from routes.attack_vulnerability_route import attack_vulnerability_route   
from routes.api_setting.API_ROUTE import api_route

import secrets
from datetime import timedelta
from flask_session import Session
import time
from sqlalchemy.exc import OperationalError
from flask_login import LoginManager
from reconnaissance.scanner_flaresolverr.start_flaresolverr import start_flaresolverr
import sys
import waitress
import os


def create_app():
    start_flaresolverr()
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
                static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))
    
    # 基本配置
    app.config['SECRET_KEY'] = secrets.token_hex(16)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'c2.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # SQLite 配置
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'connect_args': {
            'check_same_thread': False,
            'timeout': 30,
            'isolation_level': None  # 允許手動控制事務
        }
    }
    
    # Session 配置
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_FILE_DIR'] = 'flask_session'
    app.config['SESSION_FILE_THRESHOLD'] = 500
    app.config['SESSION_FILE_MODE'] = 0o600
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_NAME'] = 'c2_session'
    
    # 初始化 Flask-Session
    Session(app)
    
    # 初始化數據庫
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 配置 SQLite，添加重试机制
    with app.app_context():
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text("PRAGMA journal_mode=WAL"))
                    conn.execute(db.text("PRAGMA busy_timeout=10000"))  # 增加超时时间到10秒
                    conn.commit()
                break  # 如果成功，跳出循环
            except OperationalError as e:
                if attempt < max_retries - 1:  # 如果还有重试机会
                    app.logger.warning(f"数据库锁定，尝试重试 {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)  # 等待一段时间后重试
                else:
                    app.logger.error("无法配置数据库设置，已达到最大重试次数")
                    raise  # 重试耗尽，抛出异常
    
    # 初始化 Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'index.login'  # 設置登入頁面的端點
    
    @login_manager.user_loader
    def load_user(user_id):
        from instance.models import User
        return db.session.get(User, int(user_id))
    
    # 註冊藍圖
    app.register_blueprint(zombie_bp, url_prefix='/api/zombie')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(index_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(attack_bp)
    app.register_blueprint(result_bp, url_prefix='/result')
    app.register_blueprint(attack_vulnerability_route, url_prefix='/attack/vulnerability')
    app.register_blueprint(api_route, url_prefix='/api')
    # 設置日誌配置
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 確保日誌目錄存在
    os.makedirs('logs', exist_ok=True)
    
    file_handler = logging.FileHandler('logs/app.txt', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    app.logger.addHandler(stream_handler)
    
    app.logger.setLevel(logging.DEBUG)
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(port=5000,debug=True)