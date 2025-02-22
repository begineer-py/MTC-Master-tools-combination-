import threading
import json
import logging
from datetime import datetime
from flask import current_app
from instance.models import db, HarvesterResult
import queue
from reconnaissance.theHarvester.harvester import HarvesterScanner
import sys

class HarvesterScanThread(threading.Thread):
    """theHarvester 掃描線程類"""
    
    def __init__(self, target_domain, target_id, app, sources='all'):
        """初始化掃描線程
        
        Args:
            target_domain: 目標域名
            target_id: 目標ID
            app: Flask應用實例
            sources: 數據源（默認'all'）
        """
        threading.Thread.__init__(self)
        self.target_domain = target_domain
        self.target_id = target_id
        self.app = app._get_current_object()  # 獲取真實的應用實例
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
        """清理掃描結果數據"""
        if not isinstance(data, dict):
            return {}
            
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, list):
                # 移除空值和重複項
                cleaned_list = list(filter(None, set(value)))
                if cleaned_list:
                    cleaned[key] = sorted(cleaned_list)
            elif value:
                cleaned[key] = value
                
        return cleaned
    
    def run(self):
        """執行掃描線程"""
        try:
            with self.app.app_context():
                self.logger.info(f"開始掃描目標: {self.target_domain}")
                
                scanner = HarvesterScanner()
                success, result = scanner.run_harvester(
                    self.target_domain,
                    self.target_id,
                    sources=self.sources
                )
                
                if success and isinstance(result, dict):
                    # 清理和驗證結果數據
                    cleaned_result = self._clean_data(result)
                    
                    # 檢查是否有任何有效數據
                    has_data = any([
                        cleaned_result.get('urls', []),
                        cleaned_result.get('emails', []),
                        cleaned_result.get('hosts', []),
                        cleaned_result.get('ips', []),
                        cleaned_result.get('asns', []),
                        cleaned_result.get('linkedin', []),
                        cleaned_result.get('dns_records', []),
                        cleaned_result.get('ip_ranges', []),
                        cleaned_result.get('reverse_dns', [])
                    ])
                    
                    if has_data:
                        self.result_queue.put((cleaned_result, True, 200))
                    else:
                        self.result_queue.put(({"error": "掃描完成但未找到任何有效數據"}, False, 404))
                else:
                    self.result_queue.put(({"error": str(result)}, False, 500))
                    
        except Exception as e:
            error_msg = f"掃描過程發生錯誤: {str(e)}"
            print(f"\n[!] {error_msg}", file=sys.stderr)
            self.result_queue.put(({"error": error_msg}, False, 500))
    
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
    scanner = HarvesterScanThread(target_domain, target_id, app, sources)
    scanner.start()
    return scanner.get_result(timeout=timeout) 