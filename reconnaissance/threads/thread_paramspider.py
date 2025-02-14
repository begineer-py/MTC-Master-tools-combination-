import threading
import queue
import logging
from flask import current_app
from instance.models import db, ParamSpiderResult
import os
import sys
from tools.ParamSpider.paramspider.main import fetch_and_clean_urls
from datetime import datetime

def setup_logging():
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

logger = setup_logging()

class ParamSpiderThread(threading.Thread):
    """ParamSpider 多線程處理類"""
    
    def __init__(self, target_url, target_id, app, exclude='', threads=50):
        """
        初始化 ParamSpider 線程
        
        Args:
            target_url: 目標 URL
            target_id: 目標 ID
            app: Flask 應用程序
            exclude: 排除的路徑
            threads: 線程數量
        """
        super().__init__()
        self.target_url = target_url
        self.target_id = target_id
        self.app = app._get_current_object() if hasattr(app, '_get_current_object') else app
        self.exclude = exclude
        self.threads = threads
        self.daemon = True
        self.result_queue = queue.Queue()

    def run(self):
        """線程執行方法"""
        try:
            # 創建應用上下文
            ctx = self.app.app_context()
            ctx.push()
            
            try:
                logger.info(f"開始處理目標: {self.target_url}")
                
                # 提取域名
                domain = self.target_url.replace('https://', '').replace('http://', '').split('/')[0]
                
                # 運行 ParamSpider
                urls = fetch_and_clean_urls(domain)
                
                if urls:
                    # 構建結果
                    result = {
                        'status': 'success',
                        'result': {
                            'result_text': '\n'.join([f'URL: {url}' for url in urls]),
                            'total_urls': len(urls),
                            'unique_parameters': len(set(url.split('?')[1].split('=')[0] for url in urls if '?' in url))
                        }
                    }
                    
                    # 保存到數據庫
                    try:
                        # 先檢查是否存在現有記錄
                        existing_result = ParamSpiderResult.query.filter_by(target_id=self.target_id).first()
                        if existing_result:
                            # 更新現有記錄
                            existing_result.exclude = self.exclude
                            existing_result.threads = self.threads
                            existing_result.status = 'success'
                            existing_result.result_text = result['result']['result_text']
                            existing_result.total_urls = result['result']['total_urls']
                            existing_result.unique_parameters = result['result']['unique_parameters']
                            existing_result.updated_at = datetime.now()
                        else:
                            # 創建新記錄
                            paramspider_result = ParamSpiderResult(
                                target_id=self.target_id,
                                exclude=self.exclude,
                                threads=self.threads,
                                status='success',
                                result_text=result['result']['result_text'],
                                total_urls=result['result']['total_urls'],
                                unique_parameters=result['result']['unique_parameters']
                            )
                            db.session.add(paramspider_result)
                        
                        db.session.commit()
                        self.result_queue.put((result, True, 200))
                        
                    except Exception as e:
                        db.session.rollback()
                        error_msg = f"保存結果時出錯: {str(e)}"
                        logger.error(error_msg)
                        self.result_queue.put(({'message': error_msg}, False, 500))
                        
                else:
                    error_msg = "未找到任何 URL"
                    logger.warning(error_msg)
                    self.result_queue.put(({'message': error_msg}, False, 404))
                    
            finally:
                # 確保在完成後移除上下文
                ctx.pop()
                    
        except Exception as e:
            error_msg = f"執行 ParamSpider 時出錯: {str(e)}"
            logger.error(error_msg)
            self.result_queue.put(({'message': error_msg}, False, 500))

    def get_result(self, timeout=300):
        """
        獲取掃描結果
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            tuple: (result, success, code)
        """
        try:
            result, success, code = self.result_queue.get(timeout=timeout)
            return result, success, code
        except queue.Empty:
            return {'message': '掃描超時'}, False, 408
        except Exception as e:
            return {'message': f'獲取結果時出錯: {str(e)}'}, False, 500

class ParamSpiderThreadPool:
    """ParamSpider 線程池管理類"""
    
    def __init__(self, num_threads: int = 5):
        """
        初始化線程池
        
        Args:
            num_threads: 線程數量
        """
        self.domain_queue = queue.Queue()
        self.num_threads = num_threads
        self.threads = []
        self.app = current_app._get_current_object()
        
    def add_domain(self, domain: str):
        """
        添加域名到處理隊列
        
        Args:
            domain: 要處理的域名
        """
        self.domain_queue.put(domain)
        
    def start_threads(self):
        """啟動所有線程"""
        for _ in range(self.num_threads):
            thread = ParamSpiderThread(
                target_url=self.domain_queue.get(),
                target_id=None,  # 這裡需要從外部傳入
                app=self.app,
                exclude='',
                threads=self.num_threads
            )
            thread.start()
            self.threads.append(thread)
            
    def wait_completion(self):
        """等待所有任務完成並返回結果"""
        # 等待所有線程結束
        for thread in self.threads:
            thread.join()
            
        logger.info("所有線程已完成")
        return self.results
        
    def save_results(self, target_id: int):
        """
        保存掃描結果到數據庫
        
        Args:
            target_id: 目標ID
        """
        with self.app.app_context():
            for thread in self.threads:
                try:
                    result, success, code = thread.get_result(timeout=300)
                    if success and result:
                        paramspider_result = ParamSpiderResult(
                            target_id=target_id,
                            exclude=thread.exclude,
                            threads=thread.threads,
                            status='success',
                            result_text=result.get('result', {}).get('result_text', ''),
                            total_urls=result.get('result', {}).get('total_urls', 0),
                            unique_parameters=result.get('result', {}).get('unique_parameters', 0)
                        )
                        db.session.add(paramspider_result)
                        db.session.commit()
                except Exception as e:
                    logger.error(f"保存 ParamSpider 結果時出錯: {str(e)}")
                    db.session.rollback()
        
        self.threads = [] 