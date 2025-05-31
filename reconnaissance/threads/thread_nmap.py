import threading
import queue
from reconnaissance.security_scanning.Scanner import nmap_scan_target
from flask import current_app

class nmap_ScanThread(threading.Thread):
    def __init__(self, target_ip, target_id, app, scan_type='common'):
        super().__init__()
        self.target_ip = target_ip
        self.target_id = target_id
        self.app = app
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

# 存储活动扫描的字典
active_scans = {}

def start_nmap_scan(target_id, target_data, app):
    """
    启动NMAP扫描
    
    参数:
        target_id: 目标ID
        target_data: 包含target_ip, target_port, scan_type等信息的字典
        app: Flask应用实例
    
    返回:
        target_id: 目标ID
    """
    # 提取目标信息
    target_ip = target_data.get('target_ip')
    scan_type = target_data.get('scan_type', 'common')
    
    # 检查是否已有该目标的扫描正在进行
    scan_key = f"{target_id}_{scan_type}"
    if scan_key in active_scans and active_scans[scan_key].is_alive():
        current_app.logger.info(f"已有NMAP扫描正在进行，目标ID: {target_id}，扫描类型: {scan_type}")
        return target_id
    
    # 创建并启动新的扫描线程
    scan_thread = nmap_ScanThread(
        target_ip=target_ip,
        target_id=target_id,
        app=app,
        scan_type=scan_type
    )
    scan_thread.start()
    
    # 记录活动扫描
    active_scans[scan_key] = scan_thread
    
    current_app.logger.info(f"已启动NMAP扫描，目标ID: {target_id}，扫描类型: {scan_type}")
    return target_id