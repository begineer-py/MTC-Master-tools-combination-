import threading
import queue
from reconnaissance.security_scanning.Scanner import nmap_scan_target
from flask import current_app

class nmap_ScanThread(threading.Thread):
    def __init__(self, target_ip, user_id, target_id, app, scan_type='common'):
        super().__init__()
        self.target_ip = target_ip
        self.user_id = user_id
        self.target_id = target_id
        self.app = app._get_current_object()  # 獲取真實的應用實例
        self.scan_type = scan_type
        self.result_queue = queue.Queue()
        self.daemon = True  # 設置為守護線程
        
    def run(self):
        try:
            # 創建應用上下文
            ctx = self.app.app_context()
            ctx.push()  # 推送上下文
            
            try:
                scan_result, success, code = nmap_scan_target(
                    self.target_ip, 
                    self.target_id,
                    self.scan_type
                )
                self.result_queue.put((scan_result, success, code))
            finally:
                ctx.pop()  # 確保上下文被移除
                
        except Exception as e:
            current_app.logger.error(f"Nmap scan error: {str(e)}")
            self.result_queue.put((str(e), False, 500))
    
    def get_result(self, timeout=None):
        """獲取掃描結果"""
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return "掃描超時", False, 408