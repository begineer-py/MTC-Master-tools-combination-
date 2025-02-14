import os

class Config:
    """基本配置類"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_secret_key'  # 機密金鑰
    
    # 數據庫配置
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(os.path.dirname(__file__), "instance", "C2.db")}?check_same_thread=False'  # 允許多線程訪問
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 禁用對修改的追蹤
    SQLALCHEMY_POOL_SIZE = 20  # 連接池大小
    SQLALCHEMY_MAX_OVERFLOW = 10  # 超出連接池大小後的最大連接數
    SQLALCHEMY_POOL_TIMEOUT = 30  # 連接池超時時間（秒）
    SQLALCHEMY_POOL_RECYCLE = 3600  # 連接回收時間（秒）
    
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'  # 調試模式   
    
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

