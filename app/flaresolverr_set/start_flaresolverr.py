import subprocess # 導入 subprocess 模塊，用於創建和管理子進程
import os # 導入 os 模塊，用於與操作系統交互，例如路徑操作
import time # 導入 time 模塊，用於時間相關操作，例如延遲
import requests # 導入 requests 模塊，用於發送 HTTP 請求，檢查 FlareSolverr 健康狀態
import logging # 導入 logging 模塊，用於記錄日誌信息
import threading # 導入 threading 模塊，用於創建和管理線程，例如後台監控
import signal # 導入 signal 模塊，用於處理操作系統信號 (儘管在此代碼中未直接使用，但通常與進程管理相關)
import psutil # 導入 psutil 模塊，用於獲取系統和進程信息，例如查找正在運行的 FlareSolverr 進程
from typing import Optional, Dict, Any # 導入類型提示，增強代碼可讀性和健壯性

class FlareSolverrManager: # 定義 FlareSolverr 自動管理器類
    """FlareSolverr 自動管理器""" # 類文檔字符串，描述其功能
    
    def __init__(self): # 類的構造函數，初始化實例屬性
        self.flaresolverr_host = 'localhost' # FlareSolverr 監聽的主機名，默認為本地
        self.flaresolverr_port = 8191 # FlareSolverr 監聽的端口號，默認為 8191
        self.flaresolverr_url = f'http://{self.flaresolverr_host}:{self.flaresolverr_port}' # 構建完整的 FlareSolverr URL 地址
        self.process: Optional[subprocess.Popen] = None # 用於存儲 FlareSolverr 子進程對象，初始為 None
        self.auto_restart = True # 是否啟用自動重啟功能，默認為 True
        self.max_restart_attempts = 5 # 最大自動重啟嘗試次數
        self.restart_delay = 10  # 秒，每次重啟失敗後的等待延遲時間
        self.health_check_interval = 30  # 秒，健康檢查的間隔時間
        self.monitor_thread: Optional[threading.Thread] = None # 用於存儲監控線程對象，初始為 None
        self.is_monitoring = False # 標記是否正在進行監控，初始為 False
        
        # 設置日誌
        self.logger = logging.getLogger(__name__) # 獲取一個日誌記錄器實例，名稱為當前模塊名
        
        # FlareSolverr 執行文件路徑
        self.flaresolverr_script = os.path.join( # 構建 FlareSolverr 主腳本 flaresolverr.py 的絕對路徑
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), # 從當前文件向上回溯三級目錄
            "tools", "FlareSolverr", "src", "flaresolverr.py" # 拼接後續的路徑組件
        ) # 這個路徑假設您的項目結構是 tools/FlareSolverr/src/flaresolverr.py
        
    def is_flaresolverr_running(self) -> bool: # 定義檢查 FlareSolverr 是否正在運行的方法
        """檢查 FlareSolverr 是否正在運行""" # 方法文檔字符串
        try: # 嘗試執行以下代碼塊
            response = requests.get(f'{self.flaresolverr_url}/health', timeout=5) # 向 FlareSolverr 的 /health 端點發送 GET 請求，設置超時為 5 秒
            return response.status_code == 200 # 如果響應狀態碼為 200，則返回 True，表示正在運行
        except requests.RequestException: # 如果發生請求異常（例如連接不上、超時）
            return False # 返回 False，表示未運行或無法訪問
    
    def get_flaresolverr_process(self) -> Optional[psutil.Process]: # 定義獲取 FlareSolverr 進程對象的方法
        """獲取 FlareSolverr 進程""" # 方法文檔字符串
        try: # 嘗試執行以下代碼塊
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']): # 遍歷系統中所有正在運行的進程，並獲取其 pid、name 和 cmdline 屬性
                cmdline = proc.info.get('cmdline', []) # 獲取進程的命令行參數列表，如果沒有則返回空列表
                if any('flaresolverr.py' in str(cmd) for cmd in cmdline): # 檢查命令行參數中是否包含 'flaresolverr.py' 字符串
                    return proc # 如果找到，返回該 psutil.Process 對象
        except (psutil.NoSuchProcess, psutil.AccessDenied): # 如果在遍歷過程中發生進程不存在或訪問被拒絕的異常
            pass # 忽略這些異常
        return None # 如果沒有找到匹配的進程，返回 None
    
    def start_flaresolverr(self) -> Dict[str, Any]: # 定義啟動 FlareSolverr 的方法
        """啟動 FlareSolverr""" # 方法文檔字符串
        try: # 嘗試執行以下代碼塊
            # 檢查是否已經在運行
            if self.is_flaresolverr_running(): # 調用 is_flaresolverr_running 方法檢查服務狀態
                self.logger.info("FlareSolverr 已經在運行") # 記錄日誌
                return { # 返回成功信息，表明已在運行
                    'success': True,
                    'message': 'FlareSolverr 已經在運行',
                    'status': 'already_running'
                }
            
            # 檢查腳本文件是否存在
            if not os.path.exists(self.flaresolverr_script): # 檢查 FlareSolverr 腳本文件是否存在
                error_msg = f"FlareSolverr 腳本不存在: {self.flaresolverr_script}" # 構建錯誤信息
                self.logger.error(error_msg) # 記錄錯誤日誌
                return { # 返回失敗信息，表明腳本未找到
                    'success': False,
                    'message': error_msg,
                    'status': 'script_not_found'
                }
            
            # 啟動 FlareSolverr
            self.logger.info(f"正在啟動 FlareSolverr: {self.flaresolverr_script}") # 記錄啟動日誌
            
            # 設置環境變量
            env = os.environ.copy() # 複製當前的環境變量
            env.update({ # 更新 FlareSolverr 運行所需的環境變量
                'HOST': self.flaresolverr_host, # 設置 FlareSolverr 監聽的主機
                'PORT': str(self.flaresolverr_port), # 設置 FlareSolverr 監聽的端口（轉為字符串）
                'LOG_LEVEL': 'INFO', # 設置 FlareSolverr 的日誌級別
                'HEADLESS': 'true' # 設置 FlareSolverr 以無頭模式運行瀏覽器
            })
            
            # 啟動進程
            self.process = subprocess.Popen( # 使用 subprocess.Popen 啟動 FlareSolverr 腳本
                ['python3', self.flaresolverr_script], # 要執行的命令和參數 (假設使用 python3)
                stdout=subprocess.PIPE, # 將子進程的標準輸出重定向到管道
                stderr=subprocess.PIPE, # 將子進程的標準錯誤重定向到管道
                env=env, # 傳遞設置好的環境變量
                cwd=os.path.dirname(self.flaresolverr_script) # 設置子進程的工作目錄為腳本所在目錄
            )
            
            # 等待服務啟動
            max_wait_time = 30  # 最大等待時間（秒）
            wait_interval = 2   # 檢查間隔（秒）
            waited_time = 0 # 已等待時間初始化
            
            while waited_time < max_wait_time: # 循環檢查，直到超過最大等待時間
                if self.is_flaresolverr_running(): # 檢查 FlareSolverr 是否已成功運行
                    self.logger.info(f"FlareSolverr 啟動成功，運行在 {self.flaresolverr_url}") # 記錄成功日誌
                    
                    # 啟動監控線程
                    if self.auto_restart: # 如果啟用了自動重啟
                        self.start_monitoring() # 啟動後台監控線程
                    
                    return { # 返回成功信息
                        'success': True,
                        'message': f'FlareSolverr 啟動成功，運行在 {self.flaresolverr_url}',
                        'status': 'started',
                        'url': self.flaresolverr_url,
                        'pid': self.process.pid # 返回子進程的 PID
                    }
                
                time.sleep(wait_interval) # 等待指定間隔
                waited_time += wait_interval # 累加已等待時間
            
            # 啟動超時
            self.logger.error("FlareSolverr 啟動超時") # 記錄超時錯誤日誌
            self.stop_flaresolverr() # 嘗試停止可能部分啟動的進程
            return { # 返回失敗信息，表明啟動超時
                'success': False,
                'message': 'FlareSolverr 啟動超時',
                'status': 'timeout'
            }
            
        except Exception as e: # 如果在啟動過程中發生任何其他異常
            error_msg = f"啟動 FlareSolverr 時出錯: {str(e)}" # 構建錯誤信息
            self.logger.error(error_msg) # 記錄錯誤日誌
            return { # 返回失敗信息
                'success': False,
                'message': error_msg,
                'status': 'error'
            }
    
    def stop_flaresolverr(self) -> Dict[str, Any]: # 定義停止 FlareSolverr 的方法
        """停止 FlareSolverr""" # 方法文檔字符串
        try: # 嘗試執行以下代碼塊
            # 停止監控
            self.stop_monitoring() # 調用 stop_monitoring 方法停止後台監控線程
            
            # 查找並終止進程
            proc = self.get_flaresolverr_process() # 獲取 FlareSolverr 的進程對象
            if proc: # 如果找到了進程
                self.logger.info(f"正在停止 FlareSolverr 進程 (PID: {proc.pid})") # 記錄停止日誌
                proc.terminate() # 發送終止信號 (SIGTERM) 給進程，請求其正常退出
                
                # 等待進程結束
                try: # 嘗試等待進程結束
                    proc.wait(timeout=10) # 等待最多 10 秒讓進程結束
                except psutil.TimeoutExpired: # 如果 10 秒後進程仍未結束
                    self.logger.warning("進程未在規定時間內結束，強制終止") # 記錄警告日誌
                    proc.kill() # 發送強制終止信號 (SIGKILL)
                
                self.logger.info("FlareSolverr 已停止") # 記錄已停止日誌
                return { # 返回成功信息
                    'success': True,
                    'message': 'FlareSolverr 已停止',
                    'status': 'stopped'
                }
            else: # 如果沒有找到正在運行的 FlareSolverr 進程
                return { # 返回信息，表明服務未在運行
                    'success': True,
                    'message': 'FlareSolverr 未在運行',
                    'status': 'not_running'
                }
                
        except Exception as e: # 如果在停止過程中發生任何異常
            error_msg = f"停止 FlareSolverr 時出錯: {str(e)}" # 構建錯誤信息
            self.logger.error(error_msg) # 記錄錯誤日誌
            return { # 返回失敗信息
                'success': False,
                'message': error_msg,
                'status': 'error'
            }
    
    def restart_flaresolverr(self) -> Dict[str, Any]: # 定義重啟 FlareSolverr 的方法
        """重啟 FlareSolverr""" # 方法文檔字符串
        self.logger.info("正在重啟 FlareSolverr") # 記錄重啟日誌
        
        # 停止服務
        stop_result = self.stop_flaresolverr() # 調用停止方法
        if not stop_result['success']: # 如果停止失敗
            return stop_result # 直接返回停止失敗的結果
        
        # 等待一段時間
        time.sleep(2) # 短暫等待，確保端口釋放等
        
        # 啟動服務
        return self.start_flaresolverr() # 調用啟動方法
    
    def get_status(self) -> Dict[str, Any]: # 定義獲取 FlareSolverr 狀態的方法
        """獲取 FlareSolverr 狀態""" # 方法文檔字符串
        try: # 嘗試執行以下代碼塊
            is_running = self.is_flaresolverr_running() # 檢查服務是否正在運行 (通過 HTTP health check)
            proc = self.get_flaresolverr_process() # 獲取進程對象 (通過 psutil)
            
            status = { # 初始化狀態字典
                'running': is_running, # 是否運行
                'url': self.flaresolverr_url if is_running else None, # 如果運行則返回 URL
                'monitoring': self.is_monitoring, # 是否正在監控
                'auto_restart': self.auto_restart # 是否啟用自動重啟
            }
            
            if proc: # 如果找到了進程對象
                status.update({ # 更新狀態字典，加入進程相關信息
                    'pid': proc.pid, # 進程 ID
                    'memory_usage': proc.memory_info().rss / 1024 / 1024,  # MB，獲取進程的 RSS 內存使用量並轉為 MB
                    'cpu_percent': proc.cpu_percent(), # 獲取進程的 CPU 使用率
                    'create_time': proc.create_time() # 獲取進程的創建時間 (時間戳)
                })
            
            # 測試健康狀態
            if is_running: # 如果服務正在運行 (基於 is_flaresolverr_running 的 HTTP health check 結果)
                try: # 嘗試向 FlareSolverr 的根路徑 / 發送請求
                    response = requests.get(f'{self.flaresolverr_url}/', timeout=5) # 獲取響應
                    status['health'] = 'healthy' if response.status_code == 200 else 'unhealthy' # 根據響應碼判斷健康狀態
                    status['version'] = response.json().get('version', 'unknown') # 嘗試從 JSON 響應中獲取版本號
                except: # 如果請求失敗
                    status['health'] = 'unhealthy' # 標記為不健康
            
            return { # 返回包含狀態信息的成功結果
                'success': True,
                'status': status
            }
            
        except Exception as e: # 如果在獲取狀態過程中發生任何異常
            return { # 返回失敗信息
                'success': False,
                'message': f"獲取狀態時出錯: {str(e)}"
            }
    
    def start_monitoring(self): # 定義啟動監控線程的方法
        """啟動監控線程""" # 方法文檔字符串
        if not self.is_monitoring: # 如果當前未在監控
            self.is_monitoring = True # 設置監控標誌為 True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True) # 創建一個新的線程，目標函數為 _monitor_loop，設置為守護線程 (主線程退出時該線程也退出)
            self.monitor_thread.start() # 啟動線程
            self.logger.info("FlareSolverr 監控已啟動") # 記錄日誌
    
    def stop_monitoring(self): # 定義停止監控線程的方法
        """停止監控線程""" # 方法文檔字符串
        self.is_monitoring = False # 設置監控標誌為 False，這會讓 _monitor_loop 中的循環停止
        if self.monitor_thread and self.monitor_thread.is_alive(): # 如果監控線程存在且仍在運行
            self.monitor_thread.join(timeout=5) # 等待監控線程結束，最多等待 5 秒
        self.logger.info("FlareSolverr 監控已停止") # 記錄日誌
    
    def _monitor_loop(self): # 定義私有的監控循環方法 (通常以下劃線開頭表示內部使用)
        """監控循環""" # 方法文檔字符串
        restart_attempts = 0 # 初始化重啟嘗試次數
        
        while self.is_monitoring: # 只要監控標誌為 True，就持續循環
            try: # 嘗試執行以下代碼塊
                if not self.is_flaresolverr_running(): # 檢查 FlareSolverr 是否正在運行
                    if restart_attempts < self.max_restart_attempts: # 如果未達到最大重啟次數
                        restart_attempts += 1 # 重啟次數加 1
                        self.logger.warning(f"FlareSolverr 已停止，嘗試重啟 (第 {restart_attempts} 次)") # 記錄警告日誌
                        
                        result = self.start_flaresolverr() # 嘗試啟動 FlareSolverr
                        if result['success']: # 如果啟動成功
                            restart_attempts = 0  # 重置重啟計數
                            self.logger.info("FlareSolverr 自動重啟成功") # 記錄成功日誌
                        else: # 如果啟動失敗
                            self.logger.error(f"FlareSolverr 自動重啟失敗: {result['message']}") # 記錄錯誤日誌
                            time.sleep(self.restart_delay) # 等待指定的延遲時間後再嘗試
                    else: # 如果已達到最大重啟次數
                        self.logger.error(f"FlareSolverr 重啟次數已達上限 ({self.max_restart_attempts})，停止自動重啟") # 記錄錯誤日誌
                        self.is_monitoring = False # 設置監控標誌為 False，停止監控循環
                        break # 跳出循環
                else: # 如果 FlareSolverr 正在運行
                    restart_attempts = 0  # 重置重啟計數 (因為服務正常)
                
                time.sleep(self.health_check_interval) # 等待指定的健康檢查間隔時間
                
            except Exception as e: # 如果在監控循環中發生任何異常
                self.logger.error(f"監控循環出錯: {str(e)}") # 記錄錯誤日誌
                time.sleep(self.health_check_interval) # 即使出錯，也等待一段時間再繼續，避免CPU佔用過高

# 向後兼容的類名
class start_flaresolverr(FlareSolverrManager): # 定義一個名為 start_flaresolverr 的類，它繼承自 FlareSolverrManager
    """向後兼容的類名""" # 類文檔字符串
    pass # 這個類是空的，僅用於保持與舊代碼的兼容性 (如果舊代碼直接使用 start_flaresolverr() 作為類名來實例化)

# 全局實例
flaresolverr_manager = FlareSolverrManager() # 創建 FlareSolverrManager 類的一個全局實例

def auto_start_flaresolverr(): # 定義一個自動啟動 FlareSolverr 的函數
    """自動啟動 FlareSolverr（用於應用初始化）""" # 函數文檔字符串
    return flaresolverr_manager.start_flaresolverr() # 調用全局實例的 start_flaresolverr 方法

def get_flaresolverr_status(): # 定義一個獲取 FlareSolverr 狀態的函數
    """獲取 FlareSolverr 狀態""" # 函數文檔字符串
    return flaresolverr_manager.get_status() # 調用全局實例的 get_status 方法