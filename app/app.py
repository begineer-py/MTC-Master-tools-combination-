import logging
from flask import Flask, request
from instance.models import db, migrate, Target
import secrets
from datetime import timedelta
from flask_session import Session
import time
from sqlalchemy.exc import OperationalError
from flask_login import LoginManager
from reconnaissance.scanner_flaresolverr.start_flaresolverr import start_flaresolverr
import sys
import os
from app.blueprint_set import register_blueprints
from flask_cors import CORS
import requests
from requests.exceptions import RequestException

def check_harvester_environment():
    """檢查 theHarvester 環境"""
    harvester_path = os.path.join(os.getcwd(), 'tools', 'theHarvester')
    
    # 檢查 theHarvester 目錄是否存在
    if not os.path.exists(harvester_path):
        try:
            # 如果不存在，克隆倉庫
            import subprocess
            clone_cmd = f"git clone https://github.com/laramies/theHarvester.git {harvester_path}"
            subprocess.run(clone_cmd, shell=True, check=True)
            
            # 安裝依賴
            install_cmd = f"pip install -r {os.path.join(harvester_path, 'requirements.txt')}"
            subprocess.run(install_cmd, shell=True, check=True)
            
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"安裝 theHarvester 失敗: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"設置 theHarvester 環境時出錯: {str(e)}")
    
    return True

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

def create_app():
    try:
        # 檢查 theHarvester 環境
        check_harvester_environment()
        
        # 檢查並啟動 FlareSolverr
        if not check_flaresolverr():
            print("正在啟動 FlareSolverr 服務...")
            start_flaresolverr()
            # 等待服務啟動
            max_retries = 5
            for i in range(max_retries):
                if check_flaresolverr():
                    print("FlareSolverr 服務已啟動")
                    break
                if i < max_retries - 1:
                    print(f"等待 FlareSolverr 服務啟動 ({i+1}/{max_retries})...")
                    time.sleep(3)
            else:
                print("警告: FlareSolverr 服務可能未正確啟動")
    except Exception as e:
        print(f"環境檢查失敗: {str(e)}")
        sys.exit(1)
    
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
                static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))
    
    # 启用 CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
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
            'isolation_level': None  # 允许手动控制事务
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
    
    # 初始化数据库
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
    login_manager.login_view = 'index.login'  # 设置登入页面的端点
    
    @login_manager.request_loader
    def load_user_from_request(request):
        from instance.models import User
        
        # 首先，尝试从 Authorization header 中获取 API Key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # 查找具有此 API Key 的目标
            target = Target.query.filter_by(api_key=api_key).first()
            if target:
                # 返回目标关联的用户
                user = User.query.get(target.user_id)
                if user:
                    # 设置 API 认证状态
                    user.set_api_auth(api_key)
                    # 将用户保存到 session 中
                    from flask_login import login_user
                    login_user(user)
                    return user
        
        # 如果没有 API Key 或验证失败，返回 None
        return None

    @login_manager.user_loader
    def load_user(user_id):
        from instance.models import User
        return db.session.get(User, int(user_id))
    
    # 注册蓝图
    register_blueprints(app)
    
    # 设置日志配置
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 确保日志目录存在
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
    app.run(port=5000, debug=True, use_reloader=False)  # 禁用重載器