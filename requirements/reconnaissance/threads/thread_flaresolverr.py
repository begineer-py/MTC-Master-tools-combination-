import threading
import queue
import logging
from flask import current_app
from reconnaissance.scanner_flaresolverr.cloudflare_bypass import CloudflareBypass
from contextlib import contextmanager
from instance.models import db

@contextmanager
def session_scope():
    """提供事务范围的会话上下文管理器"""
    session = db.session
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

def setup_logging():
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

logger = setup_logging()

class FlareSolverrThread(threading.Thread):
    """FlareSolverr 多線程處理類"""
    
    def __init__(self, url_queue, target_id, app=None, flaresolverr_url="http://localhost:8191/v1"):
        """
        初始化 FlareSolverr 線程
        
        Args:
            url_queue: URL 任務隊列
            target_id: 目標 ID
            app: Flask 應用實例
            flaresolverr_url: FlareSolverr 的 URL
        """
        super().__init__()
        self.url_queue = url_queue
        self.target_id = target_id
        self.flaresolverr_url = flaresolverr_url
        self.app = app._get_current_object() if hasattr(app, '_get_current_object') else app
        self.bypass = CloudflareBypass(flaresolverr_url, app=self.app)
        self.daemon = True  # 設置為守護線程
        
    def run(self):
        """線程執行方法"""
        while True:
            try:
                # 從隊列獲取 URL，如果 1 秒內沒有任務則退出
                url = self.url_queue.get_nowait()
                
                # 處理 URL
                logger.info(f"[*] 處理 URL: {url}")
                try:
                    with self.app.app_context():
                        with session_scope() as session:
                            self.bypass.make_request(url, self.target_id)
                except Exception as e:
                    logger.error(f"處理 URL 時出錯: {str(e)}")
                
                # 標記任務完成
                self.url_queue.task_done()
                
            except queue.Empty:
                logger.info(f"[線程 {self.name}] 沒有更多任務，退出線程")
                break
            except Exception as e:
                logger.error(f"線程執行出錯: {str(e)}")
                break

class FlareSolverrThreadPool:
    """FlareSolverr 線程池管理類"""
    
    def __init__(self, num_threads: int = 5):
        """
        初始化線程池
        
        Args:
            num_threads: 線程數量
        """
        self.url_queue = queue.Queue()
        self.threads = []
        self.num_threads = num_threads
        self.app = current_app._get_current_object()
        
    def add_url(self, url: str):
        """
        添加 URL 到處理隊列
        
        Args:
            url: 要處理的 URL
        """
        self.url_queue.put(url)
        
    def start_threads(self, target_id):
        """
        啟動所有線程
        
        Args:
            target_id: 目標 ID
        """
        for _ in range(self.num_threads):
            thread = FlareSolverrThread(
                url_queue=self.url_queue,
                target_id=target_id,
                app=self.app
            )
            thread.start()
            self.threads.append(thread)
            
    def wait_completion(self):
        """等待所有線程完成"""
        # 等待隊列清空
        self.url_queue.join()
        
        # 等待所有線程結束
        for thread in self.threads:
            thread.join()
            
        logger.info("所有線程已完成")
        self.threads = [] 