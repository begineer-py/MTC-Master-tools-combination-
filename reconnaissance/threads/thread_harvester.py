import threading
import json
import logging
from datetime import datetime
from flask import current_app
from instance.models import db, HarvesterResult
import queue
from reconnaissance.theHarvester.harvester import HarvesterScanner

class HarvesterScanThread(threading.Thread):
    """theHarvester 掃描線程類"""
    
    def __init__(self, target_domain, target_id, app, limit=None, sources='all'):
        """初始化掃描線程
        
        Args:
            target_domain: 目標域名
            target_id: 目標ID
            app: Flask應用實例
            limit: 結果限制數（默認None）
            sources: 數據源（默認'all'）
        """
        threading.Thread.__init__(self)
        self.target_domain = target_domain
        self.target_id = target_id
        self.app = app._get_current_object()  # 獲取真實的應用實例
        self.limit = limit
        self.sources = sources
        self.result_queue = queue.Queue()
        self.daemon = True  # 設置為守護線程
        self._setup_logger()
        
    def _setup_logger(self):
        """設置日志記錄器"""
        self.logger = logging.getLogger('HarvesterThread')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _clean_data(self, data):
        """清理掃描結果數據
        
        Args:
            data: 原始數據
            
        Returns:
            清理後的數據
        """
        if isinstance(data, str):
            # 移除分隔線
            if '---' in data:
                return ''
            # 移除空行
            return data.strip()
        elif isinstance(data, list):
            # 清理列表中的每個元素
            cleaned = []
            for item in data:
                if isinstance(item, str):
                    item = item.strip()
                    # 跳過分隔線和空行
                    if item and '---' not in item and '[*]' not in item:
                        cleaned.append(item)
                else:
                    cleaned.append(item)
            return cleaned
        elif isinstance(data, dict):
            # 清理字典中的每個值
            return {k: self._clean_data(v) for k, v in data.items()}
        return data

    def run(self):
        try:
            # 創建應用上下文
            with self.app.app_context():
                scanner = HarvesterScanner()
                success, result = scanner.run_harvester(
                    self.target_domain,
                    self.target_id,
                    self.limit,
                    self.sources
                )
                
                if success:
                    self.result_queue.put((result, True, 200))
                else:
                    self.result_queue.put(({"error": result}, False, 500))
                    
        except Exception as e:
            self.result_queue.put(({"error": str(e)}, False, 500))
    
    def get_result(self, timeout=None):
        """獲取掃描結果，帶超時機制"""
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return {"error": "掃描超時"}, False, 408

def run_harvester_scan(target_domain, target_id, app, limit=100, sources='all', timeout=600):
    """運行 theHarvester 掃描（便捷函數）
    
    Args:
        target_domain: 目標域名
        target_id: 目標ID
        app: Flask應用實例
        limit: 結果限制數
        sources: 數據源
        timeout: 超時時間（秒）
        
    Returns:
        tuple: (result_dict, success, status_code)
    """
    scanner = HarvesterScanThread(target_domain, target_id, app, limit, sources)
    scanner.start()
    return scanner.get_result(timeout=timeout) 