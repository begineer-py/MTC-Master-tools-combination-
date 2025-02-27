import os
import sys
import subprocess
import threading
import queue
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

class SearchSourceThread(threading.Thread):
    """搜索源執行線程"""
    
    def __init__(self, domain, source, harvester_path, result_queue, logger):
        threading.Thread.__init__(self)
        self.domain = domain
        self.source = source
        self.harvester_path = harvester_path
        self.result_queue = result_queue
        self.logger = logger
        self.daemon = True
    
    def run(self):
        start_time = time.time()
        try:
            cmd = [
                sys.executable,
                self.harvester_path,
                '-d', self.domain,
                '-b', self.source,
                '-l', '1000'  # 只保留搜索深度限制
            ]
            
            print(f"\n[*] 線程 {self.source} 開始執行: {' '.join(cmd)}\n")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore',
                bufsize=1,
                universal_newlines=True
            )
            
            # 實時讀取並打印輸出
            while True:
                output_line = process.stdout.readline()
                error_line = process.stderr.readline()
                
                if output_line:
                    print(f"[{self.source}] {output_line.strip()}")
                if error_line:
                    print(f"[{self.source}] Error: {error_line.strip()}", file=sys.stderr)
                
                # 檢查進程是否結束
                if process.poll() is not None:
                    # 讀取剩餘輸出
                    remaining_out, remaining_err = process.communicate()
                    if remaining_out:
                        print(f"[{self.source}] {remaining_out.strip()}")
                    if remaining_err:
                        print(f"[{self.source}] Error: {remaining_err.strip()}", file=sys.stderr)
                    break
                
            if process.returncode == 0:
                self.logger.info(f"搜索源 {self.source} 執行成功")
                self.result_queue.put((self.source, True, remaining_out if 'remaining_out' in locals() else ''))
            else:
                error_msg = remaining_err if 'remaining_err' in locals() else '未知錯誤'
                self.logger.warning(f"搜索源 {self.source} 執行失敗: {error_msg}")
                self.result_queue.put((self.source, False, error_msg))
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"搜索源 {self.source} 執行超時")
            self.result_queue.put((self.source, False, "執行超時"))
        except Exception as e:
            self.logger.error(f"搜索源 {self.source} 執行出錯: {str(e)}")
            self.result_queue.put((self.source, False, str(e)))

class CommandRunner:
    """命令執行器"""
    
    def __init__(self):
        self.logger = logging.getLogger('CommandRunner')
        self.logger.setLevel(logging.INFO)
        self.harvester_path = os.path.join(os.getcwd(), 'tools', 'theHarvester', 'theHarvester.py')
        
    def run_single_source(self, domain, source, limit=None):
        """使用單個數據源運行掃描
        
        Args:
            domain: 目標域名
            source: 數據源
            limit: 結果限制數
            
        Returns:
            dict: 掃描結果
        """
        try:
            cmd = [
                sys.executable,
                self.harvester_path,
                '-d', domain,
                '-b', source,
                '-l', '1000'  # 增加搜索深度
            ]
            
            if limit is not None:
                cmd.extend(['-l', str(limit)])
            
            self.logger.info(f"執行命令: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=300  # 5分鐘超時
            )
            
            if process.returncode != 0:
                self.logger.warning(f"搜索源 {source} 掃描失敗: {process.stderr}")
                return None
                
            return process.stdout
            
        except Exception as e:
            self.logger.error(f"搜索源 {source} 掃描出錯: {str(e)}")
            return None
            
    def run_multiple_sources(self, domain, sources):
        """運行多個搜索源的掃描
        
        Args:
            domain: 目標域名
            sources: 搜索源列表
            
        Returns:
            dict: 合併後的結果
        """
        result_queue = queue.Queue()
        threads = []
        
        # 創建並啟動線程
        for source in sources:
            thread = SearchSourceThread(
                domain=domain,
                source=source,
                harvester_path=self.harvester_path,
                result_queue=result_queue,
                logger=self.logger
            )
            threads.append(thread)
            thread.start()
            time.sleep(1)
        
        # 等待所有線程完成
        for thread in threads:
            thread.join(timeout=360)
            
        # 收集結果
        results = []
        while not result_queue.empty():
            source, success, output = result_queue.get()
            if success:
                results.append(output)
                
        return results