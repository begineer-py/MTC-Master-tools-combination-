import os
import logging
import sys
from datetime import datetime
import time  # 解決 'time' 未定義的問題
import functools  # 解決 'functools' 未定義的問題
import asyncio  # 解決 'asyncio' 未定義的問題
from typing import (
    Any,
    Awaitable,  # 新增：代表可等待對象
    Callable,
    Optional,
    TypeVar,
    ParamSpec,  # 新增：用於精確描述參數類型
    overload,  # 新增：用於定義多個類型簽名
)


import os


class Config:  # 定義基礎配置類
    """基本配置類"""
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'a_default_secret_key'

    # 數據庫配置 - 現在連接 PostgreSQL！
    # 注意：這些信息應該從環境變量中獲取，更安全和靈活！
    # 但為了測試，我們先直接寫死
    POSTGRES_USER = os.environ.get('POSTGRES_USER') or 'myuser'  # 數據庫用戶名
    POSTGRES_PASSWORD = os.environ.get(
        'POSTGRES_PASSWORD') or 'secret'  # 數據庫密碼
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST') or 'localhost'  # 數據庫主機
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT') or '5432'  # 數據庫端口
    POSTGRES_DB = os.environ.get('POSTGRES_DB') or 'mydb'  # 數據庫名

    # 修改這裡！連接 PostgreSQL！
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@'
        f'{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_MAX_OVERFLOW = 10
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 3600

    # 你原本的 SQLite 配置可以註釋掉或刪除
    # BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    # DB_PATH = os.path.join(BASE_DIR, 'instance', 'c2.db')
    # SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}?check_same_thread=False'

    # 數據庫自動解鎖 (可能是針對特定數據庫鎖定問題的自定義配置)
    DB_AUTO_UNLOCK = True
    DB_MAX_RETRIES = 5
    DB_RETRY_DELAY = 2

    # 調試模式，首先嘗試從環境變量獲取 DEBUG 值，如果為 'True' 字符串則設為 True，否則為 False
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # 文件路径配置
    # BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) # 重複定義了 BASE_DIR，通常只需定義一次
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER') or os.path.join(
        BASE_DIR, 'output')  # 輸出文件夾路徑，優先從環境變量獲取，否則使用項目根目錄下的 output 文件夾
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER') or os.path.join(
        BASE_DIR, 'temp')  # 臨時文件夾路徑，優先從環境變量獲取，否則使用項目根目錄下的 temp 文件夾
    TOOLS_FOLDER = os.environ.get('TOOLS_FOLDER') or os.path.join(
        BASE_DIR, 'tools')  # 工具文件夾路徑，優先從環境變量獲取，否則使用項目根目錄下的 tools 文件夾

    # Session 配置 (通常用於 Web 應用，如 Flask)
    PERMANENT_SESSION_LIFETIME = 86400  # session 持續時間（秒），設置為 24 小時 (24*60*60)
    # 設置 session 為永久性 (其生命週期由 PERMANENT_SESSION_LIFETIME 控制)
    SESSION_PERMANENT = True
    SESSION_TYPE = 'filesystem'  # session 存儲類型，這裡設置為使用文件系統存儲

    # FlareSolverr 配置
    FLARESOLVERR_AUTO_START = os.environ.get(
        'FLARESOLVERR_AUTO_START', 'True') == 'True'  # 是否自動啟動 FlareSolverr，優先從環境變量獲取
    FLARESOLVERR_HOST = os.environ.get(
        'FLARESOLVERR_HOST', 'localhost')  # FlareSolverr 監聽的主機，優先從環境變量獲取
    # FlareSolverr 監聽的端口，優先從環境變量獲取，並轉為整型
    FLARESOLVERR_PORT = int(os.environ.get('FLARESOLVERR_PORT', '8191'))
    FLARESOLVERR_AUTO_RESTART = os.environ.get(
        'FLARESOLVERR_AUTO_RESTART', 'True') == 'True'  # FlareSolverr 是否自動重啟，優先從環境變量獲取
    FLARESOLVERR_MAX_RESTART_ATTEMPTS = int(os.environ.get(
        'FLARESOLVERR_MAX_RESTART_ATTEMPTS', '5'))  # FlareSolverr 最大自動重啟次數，優先從環境變量獲取


class DevelopmentConfig(Config):  # 定義開發環境配置類，繼承自 Config 基礎配置類
    """開發環境配置"""  # 類文檔字符串
    DEBUG = True  # 在開發環境中，明確將 DEBUG 設置為 True


class ProductionConfig(Config):  # 定義生產環境配置類，繼承自 Config 基礎配置類
    """生產環境配置"""  # 類文檔字符串
    DEBUG = False  # 在生產環境中，明確將 DEBUG 設置為 False
    # 生產環境可能還會有其他特定配置，例如更嚴格的日誌級別、不同的數據庫地址等


class TestingConfig(Config):  # 定義測試環境配置類，繼承自 Config 基礎配置類
    """測試環境配置"""  # 類文檔字符串
    TESTING = True  # Flask 等框架中用於開啟測試模式的標誌
    DEBUG = True  # 測試環境通常也開啟 DEBUG 以便於調試
    # 測試環境可能使用內存數據庫或其他特定於測試的配置


# 配置字典，用于通过名称字符串（例如 'development', 'production'）访问对应的配置類
Config_dict = {  # 注意這裡的變量名，原代碼中將 Config 類名覆蓋了，這裡改為 Config_dict 以避免衝突
    'development': DevelopmentConfig,  # 'development' 字符串對應 DevelopmentConfig 類
    'production': ProductionConfig,  # 'production' 字符串對應 ProductionConfig 類
    'testing': TestingConfig,  # 'testing' 字符串對應 TestingConfig 類
    'default': DevelopmentConfig  # 默認配置使用 DevelopmentConfig 類
}


# 定義一個增強的日誌格式化器，繼承自 logging.Formatter
class EnhancedFormatter(logging.Formatter):
    """增強格式器，自動添加來源信息和顏色"""  # 類文檔字符串

    def format(self, record):  # 重寫 format 方法，自定義日誌記錄的格式
        # 自動添加文件名、行號、函數名信息到 record 對象中，方便後續在格式字符串中使用
        record.filename_short = os.path.basename(
            record.pathname)  # 獲取日誌發生的文件名（不含路徑）
        # 獲取函數名，如果是模塊級別則顯示 'module'
        record.funcname_info = f"{record.funcName}()" if record.funcName != '<module>' else 'module'

        # 為不同日誌級別添加 ANSI 轉義序列顏色 (僅在支持顏色的終端中有效)
        color_codes = {  # 定義不同日誌級別對應的顏色代碼
            'DEBUG': '\033[36m',    # 青色 (Cyan)
            'INFO': '\033[32m',     # 綠色 (Green)
            'WARNING': '\033[33m',  # 黃色 (Yellow)
            'ERROR': '\033[31m',    # 紅色 (Red)
            'CRITICAL': '\033[35m',  # 紫色 (Magenta)
        }
        reset_code = '\033[0m'  # ANSI 轉義序列，用於重置顏色

        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():  # 檢查標準錯誤輸出是否連接到一個 TTY (終端)
            # 控制台輸出添加顏色
            # 獲取當前日誌級別對應的顏色，如果沒有則為空字符串
            color = color_codes.get(record.levelname, '')
            # 格式化帶有顏色的日誌級別名稱
            record.levelname_colored = f"{color}{record.levelname}{reset_code}"
        else:  # 如果不是輸出到終端 (例如輸出到文件)
            record.levelname_colored = record.levelname  # 日誌級別名稱不添加顏色

        return super().format(record)  # 調用父類的 format 方法，使用更新後的 record 對象和配置的格式字符串來格式化日誌消息


class LogConfig:  # 定義增強的日誌配置類
    """增強的日誌配置類"""  # 類文檔字符串
    LOG_LEVEL = os.environ.get(
        'LOG_LEVEL', 'DEBUG')  # 日誌級別，優先從環境變量獲取，默認為 DEBUG

    # 增強的日誌格式 - 包含來源信息和顏色 (用於控制台)
    LOG_FORMAT_DETAILED = (  # 定義詳細的日誌格式字符串
        '%(asctime)s | %(levelname_colored)-8s | '  # 時間 | 帶顏色的級別 (左對齊，佔8位) |
        '%(filename_short)s:%(lineno)d | %(funcname_info)s | '  # 短文件名:行號 | 函數信息 |
        '%(message)s'  # 日誌消息本身
    )

    # 文件日誌格式 (不包含顏色，但包含來源信息)
    LOG_FORMAT_FILE = (  # 定義用於文件輸出的日誌格式字符串
        '%(asctime)s | %(levelname)-8s | '  # 時間 | 級別 (左對齊，佔8位) |
        '%(filename_short)s:%(lineno)d | %(funcname_info)s | '  # 短文件名:行號 | 函數信息 |
        '%(message)s'  # 日誌消息本身
    )

    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  # 日誌中時間戳的格式

    @classmethod  # 定義一個類方法，可以通過類名直接調用
    def setup_enhanced_logging(cls, app=None):  # 設置增強的日誌配置，可選傳入 Flask app 對象
        """設置增強的日誌配置"""  # 方法文檔字符串
        # 創建日誌目錄
        log_dir = os.path.join(os.path.dirname(os.path.dirname(
            __file__)), 'logs')  # 構建日誌文件夾路徑，位於項目根目錄下的 logs 文件夾
        os.makedirs(log_dir, exist_ok=True)  # 創建日誌文件夾，如果已存在則不報錯

        # 獲取或創建日誌器
        if app:  # 如果傳入了 Flask app 對象
            logger = app.logger  # 使用 Flask app 自帶的 logger
            # 移除現有的處理器，避免重複日誌
            for handler in logger.handlers[:]:  # 遍歷 logger 的處理器列表副本
                logger.removeHandler(handler)  # 移除每個處理器
        else:  # 如果沒有傳入 Flask app 對象
            # 獲取一個名為 'C2_application' 的日誌器實例 (如果不存在則創建)
            logger = logging.getLogger('C2_application')

        # 設置日誌器的最低日誌級別 (從字符串轉換為 logging 模塊的級別常量)
        logger.setLevel(logging.getLevelName(cls.LOG_LEVEL))

        # 控制台處理器 (帶顏色和來源信息)
        console_handler = logging.StreamHandler(
            sys.stdout)  # 創建一個將日誌輸出到標準輸出的處理器
        # 設置控制台處理器的最低日誌級別為 INFO (可以與 logger 級別不同)
        console_handler.setLevel(logging.INFO)
        # 創建一個 EnhancedFormatter 實例，使用詳細格式和日期格式
        console_formatter = EnhancedFormatter(
            cls.LOG_FORMAT_DETAILED, datefmt=cls.LOG_DATE_FORMAT)
        console_handler.setFormatter(console_formatter)  # 為控制台處理器設置格式化器
        logger.addHandler(console_handler)  # 將控制台處理器添加到日誌器

        # 文件處理器 - 所有日誌 (固定文件名 app.txt)
        file_handler = logging.FileHandler(  # 創建一個將日誌輸出到文件的處理器
            os.path.join(log_dir, 'app.txt'),  # 日誌文件名為 app.txt
            encoding='utf-8'  # 使用 utf-8 編碼
        )
        # 設置文件處理器的最低日誌級別為 DEBUG (記錄所有級別的日誌)
        file_handler.setLevel(logging.DEBUG)
        # 創建一個 EnhancedFormatter 實例，使用文件格式和日期格式
        file_formatter = EnhancedFormatter(
            cls.LOG_FORMAT_FILE, datefmt=cls.LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)  # 為文件處理器設置格式化器
        logger.addHandler(file_handler)  # 將文件處理器添加到日誌器

        # 錯誤日誌處理器 - 只記錄ERROR和CRITICAL (固定文件名 errors.txt)
        error_handler = logging.FileHandler(  # 創建一個專門記錄錯誤日誌的文件處理器
            os.path.join(log_dir, 'errors.txt'),  # 日誌文件名為 errors.txt
            encoding='utf-8'  # 使用 utf-8 編碼
        )
        # 設置錯誤日誌處理器的最低日誌級別為 ERROR (只記錄 ERROR 和 CRITICAL)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)  # 使用與普通文件日誌相同的格式化器
        logger.addHandler(error_handler)  # 將錯誤日誌處理器添加到日誌器

        # 為根日誌器 (root logger) 設置相同的處理器，以捕獲未使用特定 logger 的庫或模塊的日誌
        root_logger = logging.getLogger()  # 獲取根日誌器
        root_logger.handlers = []  # 清除根日誌器可能存在的默認處理器（例如，有些環境下 logging.basicConfig() 會添加）
        root_logger.addHandler(console_handler)  # 為根日誌器添加控制台處理器
        root_logger.addHandler(file_handler)  # 為根日誌器添加文件處理器
        root_logger.setLevel(logging.INFO)  # 設置根日誌器的最低日誌級別為 INFO (可以根據需要調整)

        logger.info("🚀 增強日誌系統已啟動")  # 記錄一條信息，表明日誌系統初始化完成
        logger.debug("調試級別日誌已啟用")  # 記錄一條調試信息，如果日誌級別允許則會輸出

        return logger  # 返回配置好的 logger 實例

    # 配置并初始化日誌記錄器 (保持向後兼容，或作為模塊級別的默認 logger)
    # logger = logging.getLogger('C2_application') # 這行如果放在這裡，會在類定義時就執行，可能不是預期的行為。通常在 setup_enhanced_logging 中獲取或創建。
    # 如果希望有一個類級別的 logger 屬性，可以這樣：
    # logger = setup_enhanced_logging.__func__(LogConfig) # 直接調用類方法來初始化，但更常見的是在應用程序啟動時調用 setup_enhanced_logging

    @classmethod
    def get_context_logger(cls, name=None):  # 定義一個獲取帶上下文信息的日誌器的類方法
        """獲取帶上下文信息的日誌器"""  # 方法文檔字符串
        if name is None:  # 如果沒有提供日誌器名稱
            # 自動獲取調用者信息作為日誌器名稱
            import inspect  # 導入 inspect 模塊，用於獲取運行時信息
            current_frame = inspect.currentframe()  # 獲取當前棧幀
            if current_frame is not None and current_frame.f_back is not None:  # 檢查棧幀是否存在
                frame = current_frame.f_back  # 獲取調用 get_context_logger 的上一級棧幀
                # 將調用者的文件名和行號作為日誌器名稱
                name = f"{os.path.basename(frame.f_code.co_filename)}:{frame.f_lineno}"
            else:  # 如果無法獲取棧幀信息
                name = 'C2_application_context'  # 使用默認名稱

        return logging.getLogger(name)  # 獲取或創建具有該上下文名稱的日誌器

# 裝飾器：自動記錄函數調用


def log_function_call(logger: Optional[logging.Logger] = None) -> Callable:
    """
    裝飾器：自動記錄函數調用、詳細參數、回傳值和執行時間。
    無縫支援同步與非同步 (async) 函數。
    """
    def decorator(func: Callable) -> Callable:

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 異步版本的邏輯 (幾乎和同步版一樣)
            _logger = logger or logging.getLogger(func.__module__)
            func_name = func.__qualname__

            # 將參數格式化的部分直接放在這裡
            arg_list = [repr(arg) for arg in args]
            kwarg_list = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            call_args_str = ", ".join(arg_list + kwarg_list)

            _logger.info(f"📞 [開始] 調用 (async) {func_name}({call_args_str})")
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)  # 唯一的不同：這裡有 await
                execution_time = time.perf_counter() - start_time
                _logger.info(
                    f"✅ [成功] {func_name} 執行完畢 (耗時: {execution_time:.4f}s) -> 回傳: {repr(result)}")
                return result
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                _logger.exception(
                    f"❌ [失敗] {func_name} 執行時發生錯誤 (耗時: {execution_time:.4f}s): {e}")
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步版本的邏輯
            _logger = logger or logging.getLogger(func.__module__)
            func_name = func.__qualname__

            # 將參數格式化的部分直接放在這裡
            arg_list = [repr(arg) for arg in args]
            kwarg_list = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            call_args_str = ", ".join(arg_list + kwarg_list)

            _logger.info(f"📞 [開始] 調用 {func_name}({call_args_str})")
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)  # 唯一的不同：這裡沒有 await
                execution_time = time.perf_counter() - start_time
                _logger.info(
                    f"✅ [成功] {func_name} 執行完畢 (耗時: {execution_time:.4f}s) -> 回傳: {repr(result)}")
                return result
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                _logger.exception(
                    f"❌ [失敗] {func_name} 執行時發生錯誤 (耗時: {execution_time:.4f}s): {e}")
                raise

        # 判斷並返回對應的包裝器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
