import os # 導入 os 模塊，用於與操作系統交互，例如獲取環境變量、路徑操作
import logging # 導入 logging 模塊，用於日誌記錄
import sys # 導入 sys 模塊，用於訪問與 Python 解釋器緊密相關的變量和函數，例如標準輸出/錯誤流
from datetime import datetime # 從 datetime 模塊導入 datetime 類，用於處理日期和時間 (雖然在此文件中未直接使用，但日誌中常用)

class Config: # 定義基礎配置類
    """基本配置類""" # 類文檔字符串
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_secret_key'  # 機密金鑰，首先嘗試從環境變量獲取，否則使用默認值 (用於 Flask 等框架的 session 加密等)
    
    # 數據庫配置
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) # 獲取項目根目錄的絕對路徑 (假設此文件在項目根目錄的下一級目錄中)
    DB_PATH = os.path.join(BASE_DIR, 'instance', 'c2.db') # 構建 SQLite 數據庫文件的絕對路徑，位於 instance 文件夾下，名為 c2.db
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}?check_same_thread=False'  # SQLAlchemy 數據庫連接 URI，使用 SQLite，並允許不同線程訪問 (通過 check_same_thread=False)
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 禁用 Flask-SQLAlchemy 對模型修改的追蹤，以節省資源
    SQLALCHEMY_POOL_SIZE = 20  # SQLAlchemy 連接池的大小，即同時可以保持的數據庫連接數
    SQLALCHEMY_MAX_OVERFLOW = 10  # 超出連接池大小後，允許額外創建的最大連接數
    SQLALCHEMY_POOL_TIMEOUT = 30  # 從連接池獲取連接的超時時間（秒）
    SQLALCHEMY_POOL_RECYCLE = 3600  # 連接在連接池中的最大存活時間（秒），到期後會被回收（例如 1 小時）
    
    # 數據庫自動解鎖 (可能是針對特定數據庫鎖定問題的自定義配置)
    DB_AUTO_UNLOCK = True  # 啟用數據庫自動解鎖功能，默認為 True
    DB_MAX_RETRIES = 5  # 數據庫操作（例如解鎖）的最大重試次數
    DB_RETRY_DELAY = 2  # 每次重試之間的延遲時間（秒）
    
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'  # 調試模式，首先嘗試從環境變量獲取 DEBUG 值，如果為 'True' 字符串則設為 True，否則為 False
    
    # 文件路径配置
    # BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) # 重複定義了 BASE_DIR，通常只需定義一次
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER') or os.path.join(BASE_DIR, 'output') # 輸出文件夾路徑，優先從環境變量獲取，否則使用項目根目錄下的 output 文件夾
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER') or os.path.join(BASE_DIR, 'temp') # 臨時文件夾路徑，優先從環境變量獲取，否則使用項目根目錄下的 temp 文件夾
    TOOLS_FOLDER = os.environ.get('TOOLS_FOLDER') or os.path.join(BASE_DIR, 'tools') # 工具文件夾路徑，優先從環境變量獲取，否則使用項目根目錄下的 tools 文件夾
    
    # Session 配置 (通常用於 Web 應用，如 Flask)
    PERMANENT_SESSION_LIFETIME = 86400  # session 持續時間（秒），設置為 24 小時 (24*60*60)
    SESSION_PERMANENT = True  # 設置 session 為永久性 (其生命週期由 PERMANENT_SESSION_LIFETIME 控制)
    SESSION_TYPE = 'filesystem'  # session 存儲類型，這裡設置為使用文件系統存儲
    
    # FlareSolverr 配置
    FLARESOLVERR_AUTO_START = os.environ.get('FLARESOLVERR_AUTO_START', 'True') == 'True'  # 是否自動啟動 FlareSolverr，優先從環境變量獲取
    FLARESOLVERR_HOST = os.environ.get('FLARESOLVERR_HOST', 'localhost')  # FlareSolverr 監聽的主機，優先從環境變量獲取
    FLARESOLVERR_PORT = int(os.environ.get('FLARESOLVERR_PORT', '8191'))  # FlareSolverr 監聽的端口，優先從環境變量獲取，並轉為整型
    FLARESOLVERR_AUTO_RESTART = os.environ.get('FLARESOLVERR_AUTO_RESTART', 'True') == 'True'  # FlareSolverr 是否自動重啟，優先從環境變量獲取
    FLARESOLVERR_MAX_RESTART_ATTEMPTS = int(os.environ.get('FLARESOLVERR_MAX_RESTART_ATTEMPTS', '5'))  # FlareSolverr 最大自動重啟次數，優先從環境變量獲取
    

class DevelopmentConfig(Config): # 定義開發環境配置類，繼承自 Config 基礎配置類
    """開發環境配置""" # 類文檔字符串
    DEBUG = True # 在開發環境中，明確將 DEBUG 設置為 True
    
class ProductionConfig(Config): # 定義生產環境配置類，繼承自 Config 基礎配置類
    """生產環境配置""" # 類文檔字符串
    DEBUG = False # 在生產環境中，明確將 DEBUG 設置為 False
    # 生產環境可能還會有其他特定配置，例如更嚴格的日誌級別、不同的數據庫地址等

class TestingConfig(Config): # 定義測試環境配置類，繼承自 Config 基礎配置類
    """測試環境配置""" # 類文檔字符串
    TESTING = True # Flask 等框架中用於開啟測試模式的標誌
    DEBUG = True # 測試環境通常也開啟 DEBUG 以便於調試
    # 測試環境可能使用內存數據庫或其他特定於測試的配置
    
# 配置字典，用于通过名称字符串（例如 'development', 'production'）访问对应的配置類
Config_dict = { # 注意這裡的變量名，原代碼中將 Config 類名覆蓋了，這裡改為 Config_dict 以避免衝突
    'development': DevelopmentConfig, # 'development' 字符串對應 DevelopmentConfig 類
    'production': ProductionConfig, # 'production' 字符串對應 ProductionConfig 類
    'testing': TestingConfig, # 'testing' 字符串對應 TestingConfig 類
    'default': DevelopmentConfig # 默認配置使用 DevelopmentConfig 類
}


class EnhancedFormatter(logging.Formatter): # 定義一個增強的日誌格式化器，繼承自 logging.Formatter
    """增強格式器，自動添加來源信息和顏色""" # 類文檔字符串
    
    def format(self, record): # 重寫 format 方法，自定義日誌記錄的格式
        # 自動添加文件名、行號、函數名信息到 record 對象中，方便後續在格式字符串中使用
        record.filename_short = os.path.basename(record.pathname) # 獲取日誌發生的文件名（不含路徑）
        record.funcname_info = f"{record.funcName}()" if record.funcName != '<module>' else 'module' # 獲取函數名，如果是模塊級別則顯示 'module'
        
        # 為不同日誌級別添加 ANSI 轉義序列顏色 (僅在支持顏色的終端中有效)
        color_codes = { # 定義不同日誌級別對應的顏色代碼
            'DEBUG': '\033[36m',    # 青色 (Cyan)
            'INFO': '\033[32m',     # 綠色 (Green)
            'WARNING': '\033[33m',  # 黃色 (Yellow)
            'ERROR': '\033[31m',    # 紅色 (Red)
            'CRITICAL': '\033[35m', # 紫色 (Magenta)
        }
        reset_code = '\033[0m' # ANSI 轉義序列，用於重置顏色
        
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty(): # 檢查標準錯誤輸出是否連接到一個 TTY (終端)
            # 控制台輸出添加顏色
            color = color_codes.get(record.levelname, '') # 獲取當前日誌級別對應的顏色，如果沒有則為空字符串
            record.levelname_colored = f"{color}{record.levelname}{reset_code}" # 格式化帶有顏色的日誌級別名稱
        else: # 如果不是輸出到終端 (例如輸出到文件)
            record.levelname_colored = record.levelname # 日誌級別名稱不添加顏色
            
        return super().format(record) # 調用父類的 format 方法，使用更新後的 record 對象和配置的格式字符串來格式化日誌消息

class LogConfig: # 定義增強的日誌配置類
    """增強的日誌配置類""" # 類文檔字符串
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG') # 日誌級別，優先從環境變量獲取，默認為 DEBUG
    
    # 增強的日誌格式 - 包含來源信息和顏色 (用於控制台)
    LOG_FORMAT_DETAILED = ( # 定義詳細的日誌格式字符串
        '%(asctime)s | %(levelname_colored)-8s | ' # 時間 | 帶顏色的級別 (左對齊，佔8位) |
        '%(filename_short)s:%(lineno)d | %(funcname_info)s | ' # 短文件名:行號 | 函數信息 |
        '%(message)s' # 日誌消息本身
    )
    
    # 文件日誌格式 (不包含顏色，但包含來源信息)
    LOG_FORMAT_FILE = ( # 定義用於文件輸出的日誌格式字符串
        '%(asctime)s | %(levelname)-8s | ' # 時間 | 級別 (左對齊，佔8位) |
        '%(filename_short)s:%(lineno)d | %(funcname_info)s | ' # 短文件名:行號 | 函數信息 |
        '%(message)s' # 日誌消息本身
    )
    
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S' # 日誌中時間戳的格式
    
    @classmethod # 定義一個類方法，可以通過類名直接調用
    def setup_enhanced_logging(cls, app=None): # 設置增強的日誌配置，可選傳入 Flask app 對象
        """設置增強的日誌配置""" # 方法文檔字符串
        # 創建日誌目錄
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs') # 構建日誌文件夾路徑，位於項目根目錄下的 logs 文件夾
        os.makedirs(log_dir, exist_ok=True) # 創建日誌文件夾，如果已存在則不報錯
        
        # 獲取或創建日誌器
        if app: # 如果傳入了 Flask app 對象
            logger = app.logger # 使用 Flask app 自帶的 logger
            # 移除現有的處理器，避免重複日誌
            for handler in logger.handlers[:]: # 遍歷 logger 的處理器列表副本
                logger.removeHandler(handler) # 移除每個處理器
        else: # 如果沒有傳入 Flask app 對象
            logger = logging.getLogger('C2_application') # 獲取一個名為 'C2_application' 的日誌器實例 (如果不存在則創建)
        
        logger.setLevel(logging.getLevelName(cls.LOG_LEVEL)) # 設置日誌器的最低日誌級別 (從字符串轉換為 logging 模塊的級別常量)
        
        # 控制台處理器 (帶顏色和來源信息)
        console_handler = logging.StreamHandler(sys.stdout) # 創建一個將日誌輸出到標準輸出的處理器
        console_handler.setLevel(logging.INFO) # 設置控制台處理器的最低日誌級別為 INFO (可以與 logger 級別不同)
        console_formatter = EnhancedFormatter(cls.LOG_FORMAT_DETAILED, datefmt=cls.LOG_DATE_FORMAT) # 創建一個 EnhancedFormatter 實例，使用詳細格式和日期格式
        console_handler.setFormatter(console_formatter) # 為控制台處理器設置格式化器
        logger.addHandler(console_handler) # 將控制台處理器添加到日誌器
        
        # 文件處理器 - 所有日誌 (固定文件名 app.txt)
        file_handler = logging.FileHandler( # 創建一個將日誌輸出到文件的處理器
            os.path.join(log_dir, 'app.txt'), # 日誌文件名為 app.txt
            encoding='utf-8' # 使用 utf-8 編碼
        )
        file_handler.setLevel(logging.DEBUG) # 設置文件處理器的最低日誌級別為 DEBUG (記錄所有級別的日誌)
        file_formatter = EnhancedFormatter(cls.LOG_FORMAT_FILE, datefmt=cls.LOG_DATE_FORMAT) # 創建一個 EnhancedFormatter 實例，使用文件格式和日期格式
        file_handler.setFormatter(file_formatter) # 為文件處理器設置格式化器
        logger.addHandler(file_handler) # 將文件處理器添加到日誌器
        
        # 錯誤日誌處理器 - 只記錄ERROR和CRITICAL (固定文件名 errors.txt)
        error_handler = logging.FileHandler( # 創建一個專門記錄錯誤日誌的文件處理器
            os.path.join(log_dir, 'errors.txt'), # 日誌文件名為 errors.txt
            encoding='utf-8' # 使用 utf-8 編碼
        )
        error_handler.setLevel(logging.ERROR) # 設置錯誤日誌處理器的最低日誌級別為 ERROR (只記錄 ERROR 和 CRITICAL)
        error_handler.setFormatter(file_formatter) # 使用與普通文件日誌相同的格式化器
        logger.addHandler(error_handler) # 將錯誤日誌處理器添加到日誌器
        
        # 為根日誌器 (root logger) 設置相同的處理器，以捕獲未使用特定 logger 的庫或模塊的日誌
        root_logger = logging.getLogger() # 獲取根日誌器
        root_logger.handlers = []  # 清除根日誌器可能存在的默認處理器（例如，有些環境下 logging.basicConfig() 會添加）
        root_logger.addHandler(console_handler) # 為根日誌器添加控制台處理器
        root_logger.addHandler(file_handler) # 為根日誌器添加文件處理器
        root_logger.setLevel(logging.INFO) # 設置根日誌器的最低日誌級別為 INFO (可以根據需要調整)
        
        logger.info("🚀 增強日誌系統已啟動") # 記錄一條信息，表明日誌系統初始化完成
        logger.debug("調試級別日誌已啟用") # 記錄一條調試信息，如果日誌級別允許則會輸出
        
        return logger # 返回配置好的 logger 實例
    
    # 配置并初始化日誌記錄器 (保持向後兼容，或作為模塊級別的默認 logger)
    # logger = logging.getLogger('C2_application') # 這行如果放在這裡，會在類定義時就執行，可能不是預期的行為。通常在 setup_enhanced_logging 中獲取或創建。
    # 如果希望有一個類級別的 logger 屬性，可以這樣：
    # logger = setup_enhanced_logging.__func__(LogConfig) # 直接調用類方法來初始化，但更常見的是在應用程序啟動時調用 setup_enhanced_logging

    @classmethod 
    def get_context_logger(cls, name=None): # 定義一個獲取帶上下文信息的日誌器的類方法
        """獲取帶上下文信息的日誌器""" # 方法文檔字符串
        if name is None: # 如果沒有提供日誌器名稱
            # 自動獲取調用者信息作為日誌器名稱
            import inspect # 導入 inspect 模塊，用於獲取運行時信息
            frame = inspect.currentframe().f_back # 獲取調用 get_context_logger 的上一級棧幀
            name = f"{os.path.basename(frame.f_code.co_filename)}:{frame.f_lineno}" # 將調用者的文件名和行號作為日誌器名稱
        
        return logging.getLogger(name) # 獲取或創建具有該上下文名稱的日誌器

# 裝飾器：自動記錄函數調用
def log_function_call(logger=None): # 定義一個日誌裝飾器工廠函數，可選傳入 logger 實例
    """裝飾器：自動記錄函數調用和執行時間""" # 函數文檔字符串
    def decorator(func): # 實際的裝飾器函數，接收被裝飾的函數 func 作為參數
        import functools # 導入 functools 模塊，用於保留被裝飾函數的元信息 (如名稱、文檔字符串)
        import time # 導入 time 模塊，用於計算函數執行時間
        
        @functools.wraps(func) # 使用 functools.wraps 保留 func 的元信息
        def wrapper(*args, **kwargs): # 裝飾器返回的包裝函數，接收任意位置參數和關鍵字參數
            nonlocal logger # 聲明 logger 不是局部變量，而是來自外部作用域 (log_function_call 函數的作用域)
            if logger is None: # 如果在創建裝飾器時沒有傳入 logger
                logger = logging.getLogger(func.__module__) # 則使用被裝飾函數所在模塊的名稱作為 logger 名稱
            
            start_time = time.time() # 記錄函數開始執行的時間
            arg_names = list(kwargs.keys()) # 獲取關鍵字參數的名稱列表
            arg_count = len(args) # 獲取位置參數的數量
            logger.info(f"📞 調用函數 {func.__name__} (位置參數個數: {arg_count}, 關鍵字參數: {arg_names})") # 記錄函數調用信息
            
            try: # 嘗試執行被裝飾的函數
                result = func(*args, **kwargs) # 調用原始函數並獲取結果
                execution_time = time.time() - start_time # 計算函數執行耗時
                logger.info(f"✅ 函數 {func.__name__} 執行成功 (耗時: {execution_time:.3f}s)") # 記錄函數成功執行的信息和耗時
                return result # 返回原始函數的執行結果
            except Exception as e: # 如果函數執行過程中發生異常
                execution_time = time.time() - start_time # 同樣計算耗時
                logger.error(f"❌ 函數 {func.__name__} 執行失敗 (耗時: {execution_time:.3f}s): {str(e)}") # 記錄函數執行失敗的信息、耗時和異常信息
                raise # 重新拋出異常，以便上層代碼能捕獲和處理
                
        return wrapper # 返回包裝好的函數
    return decorator # 返回實際的裝飾器