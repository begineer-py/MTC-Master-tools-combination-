import os
import logging

class Config:
    """基本配置類"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_secret_key'  # 機密金鑰
    
    # 數據庫配置
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'instance', 'c2.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}?check_same_thread=False'  # 允許多線程訪問
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 禁用對修改的追蹤
    SQLALCHEMY_POOL_SIZE = 20  # 連接池大小
    SQLALCHEMY_MAX_OVERFLOW = 10  # 超出連接池大小後的最大連接數
    SQLALCHEMY_POOL_TIMEOUT = 30  # 連接池超時時間（秒）
    SQLALCHEMY_POOL_RECYCLE = 3600  # 連接回收時間（秒）
    
    # 數據庫自動解鎖
    DB_AUTO_UNLOCK = True  # 啟用數據庫自動解鎖
    DB_MAX_RETRIES = 5  # 最大重試次數
    DB_RETRY_DELAY = 2  # 重試延遲（秒）
    
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'  # 調試模式   
    
    # 文件路径配置
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER') or os.path.join(BASE_DIR, 'output')
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER') or os.path.join(BASE_DIR, 'temp')
    TOOLS_FOLDER = os.environ.get('TOOLS_FOLDER') or os.path.join(BASE_DIR, 'tools')
    
    # Session 配置
    PERMANENT_SESSION_LIFETIME = 86400  # session 持續時間（秒），設置為 24 小時
    SESSION_PERMANENT = True  # 設置 session 為永久性
    SESSION_TYPE = 'filesystem'  # 使用文件系統存儲 session
    
    # FlareSolverr 配置
    FLARESOLVERR_URL = os.environ.get('FLARESOLVERR_URL', 'http://localhost:8191/v1')
    FLARESOLVERR_TIMEOUT = int(os.environ.get('FLARESOLVERR_TIMEOUT', 60000))  # 毫秒
    FLARESOLVERR_START_TIMEOUT = int(os.environ.get('FLARESOLVERR_START_TIMEOUT', 20))  # 秒
    FLARESOLVERR_CONTAINER_NAME = os.environ.get('FLARESOLVERR_CONTAINER_NAME', 'relaxed_cray')  # Docker 容器名稱
    FLARESOLVERR_AUTO_START = os.environ.get('FLARESOLVERR_AUTO_START', 'True').lower() == 'true'

class DevelopmentConfig(Config):
    """開發環境配置"""
    DEBUG = True
    
class ProductionConfig(Config):
    """生產環境配置"""
    DEBUG = False

class TestingConfig(Config):
    """測試環境配置"""
    TESTING = True
    DEBUG = True
    
# 配置字典，用于通过名称访问配置
Config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

class FlaresolverrConfig:
    """Flaresolverr 配置類"""
    FLARESOLVERR_URL = os.environ.get('FLARESOLVERR_URL', 'http://localhost:8191/v1')
    FLARESOLVERR_TIMEOUT = int(os.environ.get('FLARESOLVERR_TIMEOUT', 60000))  # 毫秒
    FLARESOLVERR_START_TIMEOUT = int(os.environ.get('FLARESOLVERR_START_TIMEOUT', 20))  # 秒
    FLARESOLVERR_CONTAINER_NAME = os.environ.get('FLARESOLVERR_CONTAINER_NAME', 'relaxed_cray')  # Docker 容器名稱
    FLARESOLVERR_AUTO_START = os.environ.get('FLARESOLVERR_AUTO_START', 'True').lower() == 'true'

class TheHarvesterConfig:
    """TheHarvester 配置類"""
    THEHARVESTER_PATH = os.path.join(os.path.dirname(__file__), '..', 'tools', 'theHarvester', 'theHarvester.py')
    THEHARVESTER_TIMEOUT = int(os.environ.get('THEHARVESTER_TIMEOUT', 60000))  # 毫秒
    THEHARVESTER_START_TIMEOUT = int(os.environ.get('THEHARVESTER_START_TIMEOUT', 20))  # 秒

class LogConfig:
    """日誌配置類"""
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # 配置并初始化日志记录器
    logger = logging.getLogger('C2_application')
    logger.setLevel(logging.getLevelName(LOG_LEVEL))
    
    # 如果没有处理器，添加一个控制台处理器
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.getLevelName(LOG_LEVEL))
        
        # 设置格式
        formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(console_handler)
        
        # 设置文件日志（如果需要）
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(os.path.join(log_dir, 'c2_app.log'), encoding='utf-8')
        file_handler.setLevel(logging.getLevelName(LOG_LEVEL))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

class DockerConfig:
    """Docker 配置類"""
    docker_path = os.environ.get('DOCKER_PATH', 'docker')
    docker_compose_path = os.environ.get('DOCKER_COMPOSE_PATH', 'docker-compose')
    docker_start_timeout = int(os.environ.get('DOCKER_START_TIMEOUT', 30))  # 秒
    docker_stop_timeout = int(os.environ.get('DOCKER_STOP_TIMEOUT', 10))  # 秒
    docker_check_interval = int(os.environ.get('DOCKER_CHECK_INTERVAL', 2))  # 秒
    docker_auto_start = os.environ.get('DOCKER_AUTO_START', 'True').lower() == 'true'
    docker_auto_restart = os.environ.get('DOCKER_AUTO_RESTART', 'True').lower() == 'true'




