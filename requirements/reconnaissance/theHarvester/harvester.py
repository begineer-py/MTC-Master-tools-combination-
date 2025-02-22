import subprocess
import json
import logging
from datetime import datetime
from instance.models import db, HarvesterResult
import os
import sys
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re
from bs4 import BeautifulSoup

class Harvester:
    def __init__(self, domain, limit=100):
        self.domain = domain
        self.limit = limit
        self.results = []
        self.source_mapping = {
            'all': [
                'anubis', 'baidu', 'bevigil', 'binaryedge', 'bing', 'bingapi',
                'bufferoverun', 'censys', 'certspotter', 'criminalip', 'crtsh',
                'duckduckgo', 'fullhunt', 'github-code', 'google', 'hackertarget',
                'hunter', 'hunterhow', 'intelx', 'netlas', 'onyphe', 'otx',
                'pentesttools', 'projectdiscovery', 'rapiddns', 'rocketreach',
                'securitytrails', 'shodan', 'sitedossier', 'subdomaincenter',
                'subdomainfinderc99', 'threatminer', 'tomba', 'urlscan',
                'virustotal', 'yahoo', 'zoomeye'
            ],
            'baidu': 'baidu',
            'bing': 'bing',
            'google': 'google',
            'yahoo': 'yahoo',
            'duckduckgo': 'duckduckgo'
        }

    def _get_mapped_source(self, source):
        if source == 'all':
            return self.source_mapping['all']
        return self.source_mapping.get(source, source)

    def _run_single_source(self, source):
        try:
            cmd = [
                sys.executable,
                self.harvester_path,
                '-d', self.domain,
                '-b', source,
                '-l', str(self.limit),
                '-u',  # 啟用 URL 搜索
                '-f', f'output_{source}.html'  # 為每個源使用不同的輸出文件
            ]
            
            logging.info(f'運行 theHarvester，數據源: {source}')
            logging.debug(f'命令: {" ".join(cmd)}')
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            # 讀取輸出文件
            output_file = f'output_{source}.html'
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                process.stdout += content
                # 刪除臨時文件
                os.remove(output_file)
            
            if process.stdout:
                logging.info(f'命令輸出 (數據源 {source}): {process.stdout}')
            
            if process.stderr:
                logging.warning(f'命令錯誤輸出 (數據源 {source}): {process.stderr}')
                
            if process.returncode != 0:
                error_msg = process.stderr if process.stderr else process.stdout
                if 'FlareSolverr' in error_msg:
                    logging.error('FlareSolverr 服務錯誤 - 請檢查服務是否運行')
                elif '403 Forbidden' in error_msg:
                    logging.error('搜索被阻止 - 收到 403 錯誤')
                else:
                    logging.error(f'命令失敗 (數據源 {source}): {error_msg}')
                return False
                
            return bool(process.stdout.strip())
            
        except Exception as e:
            logging.error(f'運行 theHarvester 時出錯，數據源 {source}: {str(e)}')
            return False

    def run_harvester(self, source='all'):
        success = False
        sources = self._get_mapped_source(source)
        
        if isinstance(sources, list):
            for s in sources:
                if self._run_single_source(s):
                    success = True
        else:
            success = self._run_single_source(sources)
            
        return success

class HarvesterScanner:
    """theHarvester 掃描器類"""
    
    def __init__(self):
        # 線程控制
        self.max_workers = 8  # 限制最大線程數
        self.min_workers = 2
        self.active_tasks = 0
        self.executor = None
        
        # 隊列和鎖
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # 各種鎖機制
        self.thread_lock = threading.Lock()
        self.db_lock = threading.Lock()
        self.result_lock = threading.Lock()
        self.scan_lock = threading.Lock()
        self.queue_lock = threading.Lock()
        
        # 條件變量
        self.task_cv = threading.Condition(self.thread_lock)
        self.result_cv = threading.Condition(self.result_lock)
        
        # 掃描狀態
        self.scanning = False
        self.scan_complete = threading.Event()
        
        # 消息回調
        self.message_callback = None
        
        self._setup_logger()
        
        # 更新為確實可用的搜索源
        self.valid_sources = [
            'all'   
        ]
        
        # 設置 theHarvester 路徑
        self.harvester_path = os.path.join(os.getcwd(), 'tools', 'theHarvester', 'theHarvester.py')
        if not os.path.exists(self.harvester_path):
            raise FileNotFoundError(f"找不到 theHarvester 腳本: {self.harvester_path}")
            
    def __del__(self):
        """確保資源被正確釋放"""
        self.stop_scan()
        
    def stop_scan(self):
        """停止掃描並清理資源"""
        with self.scan_lock:
            if not self.scanning:
                return
            self.scanning = False
            
        # 等待所有任務完成
        with self.task_cv:
            while self.active_tasks > 0:
                self.task_cv.wait(timeout=1.0)  # 設置超時以避免死鎖
                
        # 關閉線程池
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None
            
        # 清空隊列
        with self.queue_lock:
            while not self.task_queue.empty():
                try:
                    self.task_queue.get_nowait()
                except queue.Empty:
                    break
                    
        self.logger.info("掃描已停止，資源已清理")
        
    def set_message_callback(self, callback):
        """設置消息回調函數"""
        self.message_callback = callback
        
    def _send_message(self, message, msg_type='info'):
        """發送消息到回調函數"""
        if self.message_callback:
            self.message_callback(message, msg_type)
            
    def run_harvester(self, domain, target_id, sources='all'):
        """運行 theHarvester 掃描"""
        try:
            with self.scan_lock:
                if self.scanning:
                    raise RuntimeError("掃描已在進行中")
                self.scanning = True
                self.scan_complete.clear()
            
            # 使用單一命令執行所有搜索源
            cmd = [
                sys.executable,
                self.harvester_path,
                '-d', domain,
                '-b', sources,  # 使用傳入的sources參數
                '-t'  # 只執行基本搜索
            ]
            
            print(f"\n[*] 執行命令: {' '.join(cmd)}\n")
            
            # 使用 Popen 實時獲取輸出
            startupinfo = None
            if os.name == 'nt':  # Windows系統
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
                # 創建臨時文件來存儲輸出
            output_file = os.path.join(os.getcwd(), 'harvester_output.txt')
            error_file = os.path.join(os.getcwd(), 'harvester_error.txt')
            
            try:
                with open(output_file, 'w', encoding='utf-8') as out, \
                     open(error_file, 'w', encoding='utf-8') as err:
                    
                    process = subprocess.Popen(
                        cmd,
                        stdout=out,
                        stderr=err,
                        text=True,
                        encoding='utf-8',
                        errors='ignore',
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    
                    # 設置超時時間
                    start_time = time.time()
                    timeout = 600  # 10分鐘超時
                    
                    # 等待進程完成或超時
                    while process.poll() is None:
                        if time.time() - start_time > timeout:
                            process.kill()
                            print(f"\n[!] 掃描超時（{timeout}秒）")
                            return False, "掃描超時"
                        time.sleep(0.1)
                    
                    # 讀取輸出文件
                    with open(output_file, 'r', encoding='utf-8') as f:
                        output = f.read()
                    with open(error_file, 'r', encoding='utf-8') as f:
                        error_output = f.read()
                    
                    # 打印輸出
                    if output:
                        print(output)
                    if error_output:
                        print(error_output, file=sys.stderr)
                    
                    # 解析結果並更新數據庫
                    if output.strip():
                        parsed_result = self._parse_output(output)
                        if parsed_result:
                            self._update_db_result(target_id, parsed_result)
                            return True, parsed_result
                        else:
                            error_msg = "掃描完成但未找到有效數據"
                            self._update_db_result(target_id, None, error_msg)
                            return False, error_msg
                    else:
                        error_msg = "掃描返回空結果"
                        self._update_db_result(target_id, None, error_msg)
                        return False, error_msg
                    
            except Exception as e:
                error_msg = f"掃描過程出錯: {str(e)}"
                print(f"\n[!] {error_msg}")
                self._update_db_result(target_id, None, error_msg)
                return False, error_msg
            finally:
                # 清理臨時文件
                try:
                    if os.path.exists(output_file):
                        os.remove(output_file)
                    if os.path.exists(error_file):
                        os.remove(error_file)
                except Exception as e:
                    print(f"清理臨時文件時出錯: {str(e)}")
                
        except Exception as e:
            error_msg = f"掃描過程出錯: {str(e)}"
            print(f"\n[!] {error_msg}")
            self._update_db_result(target_id, None, error_msg)
            return False, error_msg
        finally:
            self.stop_scan()

    def _setup_logger(self):
        """設置日志記錄器"""
        self.logger = logging.getLogger('HarvesterScanner')
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 添加控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
    def _get_mapped_source(self, source):
        """始終返回所有搜索源"""
        return self.valid_sources
        
    def _run_single_source(self, domain, source, limit=None):
        """使用單個數據源運行掃描"""
        try:
            self.logger.info(f"\n{'='*50}\n開始掃描數據源: {source}\n{'='*50}")
            
            cmd = [
                sys.executable,
                self.harvester_path,
                '-d', domain,
                '-b', source,
                '-t'   # 只執行基本搜索
            ]
            
            if limit is not None:
                cmd.extend(['-l', str(limit)])
            
            self.logger.info(f"執行命令: {' '.join(cmd)}")
            
            # 使用 Popen 而不是 run，這樣我們可以實時獲取輸出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            # 設置超時時間
            start_time = time.time()
            timeout = 60  # 1分鐘超時
            output = []
            error_output = []
            
            while True:
                # 檢查是否超時
                if time.time() - start_time > timeout:
                    process.kill()
                    self.logger.error(f"數據源 {source} 掃描超時（1分鐘）")
                    return None
                    
                # 檢查是否已經找到足夠的URL
                if output and len(output) >= limit:
                    process.kill()
                    self.logger.info(f"已找到足夠的URL ({limit}個)，停止掃描")
                    break
                    
                # 讀取輸出
                output_line = process.stdout.readline()
                error_line = process.stderr.readline()
                
                if output_line:
                    output.append(output_line)
                    self.logger.info(f"[{source}] {output_line.strip()}")
                if error_line:
                    error_output.append(error_line)
                    self.logger.warning(f"[{source}] Error: {error_line.strip()}")
                
                # 檢查進程是否結束
                if process.poll() is not None:
                    break
                    
                # 短暫休眠以減少CPU使用
                time.sleep(0.1)
            
            # 獲取剩餘輸出
            remaining_output, remaining_error = process.communicate()
            if remaining_output:
                output.append(remaining_output)
            if remaining_error:
                error_output.append(remaining_error)
            
            if process.returncode != 0 and not output:  # 如果有輸出，即使返回碼非0也繼續處理
                error_msg = ''.join(error_output).strip()
                self.logger.error(f"數據源 {source} 掃描失敗: {error_msg}")
                return None
            
            result = ''.join(output)
            
            # 檢查輸出是否為空
            if not result.strip():
                self.logger.warning(f"數據源 {source} 返回空結果")
                return None
            
            self.logger.info(f"\n{'='*50}\n數據源 {source} 掃描成功\n{'='*50}")
            return result
            
        except Exception as e:
            self.logger.error(f"數據源 {source} 掃描出錯: {str(e)}")
            self.logger.exception("詳細錯誤堆棧:")
            return None

    def _adjust_thread_count(self, queue_size):
        """動態調整線程數
        
        Args:
            queue_size: 當前隊列大小
        
        Returns:
            int: 建議的線程數
        """
        with self.thread_lock:
            # 根據隊列大小動態調整線程數
            if queue_size > 20:
                return min(self.max_workers, 20)
            elif queue_size > 10:
                return min(self.max_workers, 15)
            elif queue_size > 5:
                return min(self.max_workers, 10)
            else:
                return self.min_workers

    def _execute_task(self, domain, source, limit, results):
        """執行單個掃描任務"""
        try:
            with self.scan_lock:
                if not self.scanning:
                    return
                
            with self.thread_lock:
                self.active_tasks += 1
            
            self.logger.info(f"開始執行任務: {source}")
            
            output = self._run_single_source(domain, source, limit)
            if output:
                result = self._parse_output(output)
                
                with self.result_lock:
                    results.append(result)
                    self.result_cv.notify()  # 通知有新結果
                
                self.logger.info(f"數據源 {source} 掃描完成")
            else:
                self.logger.warning(f"數據源 {source} 返回空結果")
                
        except Exception as e:
            self.logger.error(f"處理數據源 {source} 時出錯: {str(e)}")
            self.logger.exception("詳細錯誤堆棧:")
        finally:
            with self.thread_lock:
                self.active_tasks -= 1
                if self.active_tasks == 0:
                    self.task_cv.notify_all()  # 通知所有任務完成

    def _parse_output(self, output):
        if not output:
            return {}
        
        result = {
            'urls': [],
            'emails': [],
            'hosts': [],
            'ips': [],
            'asns': [],
            'linkedin': [],
            'dns_records': [],
            'ip_ranges': [],
            'reverse_dns': []
        }
        
        def is_valid_domain(domain):
            """驗證域名格式"""
            pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
            return bool(re.match(pattern, domain))
        
        def process_url(url):
            """處理和清理URL"""
            url = url.strip('"\'<>[]{}()')
            if url.startswith('www.'):
                url = 'http://' + url
            return url
        
        def extract_domain_from_url(url):
            """從URL中提取域名"""
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                return parsed.netloc.split(':')[0]  # 移除端口號
            except:
                return None
        
        # 解析HTML內容
        if '<html' in output:
            soup = BeautifulSoup(output, 'html.parser')
            for a in soup.find_all('a', href=True):
                url = process_url(a['href'])
                if url.startswith(('http://', 'https://')):
                    if url not in result['urls']:
                        result['urls'].append(url)
                        print(f"\033[92m[+] 發現URL: {url}\033[0m")
                        # 從URL提取域名作為主機
                        domain = extract_domain_from_url(url)
                        if domain and is_valid_domain(domain) and domain not in result['hosts']:
                            result['hosts'].append(domain)
                            print(f"\033[96m[+] 從URL提取主機: {domain}\033[0m")
        
        # 解析文本內容
        current_section = None
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 檢測當前部分
            if '[*]' in line:
                if 'Emails found:' in line:
                    current_section = 'emails'
                    print(f"\n\033[94m[*] 開始解析郵箱...\033[0m")
                elif 'Hosts found:' in line:
                    current_section = 'hosts'
                    print(f"\n\033[94m[*] 開始解析主機...\033[0m")
                elif 'URLs found:' in line or 'Links found:' in line:
                    current_section = 'urls'
                    print(f"\n\033[94m[*] 開始解析URL...\033[0m")
                elif 'IPs found:' in line:
                    current_section = 'ips'
                    print(f"\n\033[94m[*] 開始解析IP...\033[0m")
                continue
            
            # 處理URL部分
            if current_section == 'urls':
                if line.startswith(('http://', 'https://', 'www.')):
                    url = process_url(line)
                    if url not in result['urls']:
                        result['urls'].append(url)
                        print(f"\033[92m[+] 發現URL: {url}\033[0m")
                        # 從URL提取域名作為主機
                        domain = extract_domain_from_url(url)
                        if domain and is_valid_domain(domain) and domain not in result['hosts']:
                            result['hosts'].append(domain)
                            print(f"\033[96m[+] 從URL提取主機: {domain}\033[0m")
            
            # 處理主機部分
            elif current_section == 'hosts':
                if is_valid_domain(line) and line not in result['hosts']:
                    result['hosts'].append(line)
                    print(f"\033[96m[+] 發現主機: {line}\033[0m")
                    # 如果主機名不是完整URL，創建一個
                    if not line.startswith(('http://', 'https://')):
                        url = f"http://{line}"
                        if url not in result['urls']:
                            result['urls'].append(url)
                            print(f"\033[92m[+] 從主機創建URL: {url}\033[0m")
            
            # 處理其他部分
            elif current_section and not line.startswith('['):
                if current_section == 'emails' and '@' in line:
                    if line not in result['emails']:
                        result['emails'].append(line)
                        print(f"\033[93m[+] 發現郵箱: {line}\033[0m")
                elif current_section == 'ips' and re.match(r'^\d{1,3}(\.\d{1,3}){3}$', line):
                    if line not in result['ips']:
                        result['ips'].append(line)
                        print(f"\033[95m[+] 發現IP: {line}\033[0m")
        
        # 額外處理：從整個輸出中提取URL
        url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+'
        additional_urls = re.findall(url_pattern, output)
        if additional_urls:
            print(f"\n\033[94m[*] 從文本中提取額外URL...\033[0m")
        for url in additional_urls:
            url = process_url(url)
            if url not in result['urls']:
                result['urls'].append(url)
                print(f"\033[92m[+] 發現額外URL: {url}\033[0m")
                # 從URL提取域名作為主機
                domain = extract_domain_from_url(url)
                if domain and is_valid_domain(domain) and domain not in result['hosts']:
                    result['hosts'].append(domain)
                    print(f"\033[96m[+] 從URL提取主機: {domain}\033[0m")
        
        # 清理結果
        for key in result:
            result[key] = list(set(filter(None, result[key])))
            result[key].sort()
        
        # 打印統計信息
        print(f"\n\033[1m[*] 掃描結果統計:\033[0m")
        print(f"\033[92m[+] URLs: {len(result['urls'])} 個\033[0m")
        print(f"\033[93m[+] Emails: {len(result['emails'])} 個\033[0m")
        print(f"\033[96m[+] Hosts: {len(result['hosts'])} 個\033[0m")
        print(f"\033[95m[+] IPs: {len(result['ips'])} 個\033[0m")
        
        return result
        
    def _merge_results(self, results):
        """合併多個掃描結果"""
        with self.result_lock:
            merged = {
                'urls': set(),
                'emails': set(),
                'hosts': set(),
                'ips': set(),
                'asns': set(),
                'linkedin': set(),
                'dns_records': set(),
                'ip_ranges': set(),
                'reverse_dns': set()
            }
            
            for result in results:
                if not result:
                    continue
                for key in merged:
                    merged[key].update(result.get(key, []))
            
            return {k: sorted(list(v)) for k, v in merged.items()}
        
    def _update_db_result(self, target_id, scan_data=None, error=None):
        """更新數據庫中的掃描結果"""
        try:
            # 在事務中執行所有數據庫操作
            with db.session.begin():
                # 基本驗證
                if not target_id:
                    raise ValueError("目標ID不能為空")
                
                # 查找或創建結果記錄
                result = db.session.query(HarvesterResult).filter_by(
                    target_id=target_id
                ).first()
                
                if not result:
                    result = HarvesterResult(target_id=target_id)
                    db.session.add(result)
                    self.logger.info(f"創建新的掃描結果記錄 (target_id: {target_id})")
                
                # 更新掃描時間
                result.scan_time = datetime.now()
                
                if scan_data is not None:
                    # 驗證數據格式
                    if not isinstance(scan_data, dict):
                        raise ValueError("掃描數據必須是字典格式")
                    
                    # 設置狀態為完成
                    result.status = 'completed'
                    
                    # 處理新數據
                    result.urls = sorted(list(set(scan_data.get('urls', []))))
                    result.emails = sorted(list(set(scan_data.get('emails', []))))
                    result.hosts = sorted(list(set(scan_data.get('hosts', []))))
                    result.direct_ips = sorted(list(set(scan_data.get('ips', []))))
                    result.asn_info = sorted(list(set(scan_data.get('asns', []))))
                    result.social_media = sorted(list(set(scan_data.get('linkedin', []))))
                    result.dns_records = sorted(list(set(scan_data.get('dns_records', []))))
                    result.ip_ranges = sorted(list(set(scan_data.get('ip_ranges', []))))
                    result.reverse_dns = sorted(list(set(scan_data.get('reverse_dns', []))))
                    
                    # 添加元數據
                    result.scan_sources = json.dumps(self.valid_sources)
                    result.error = None
                    
                    # 記錄更新統計
                    self.logger.info("數據更新統計:")
                    self.logger.info(f"- URLs: {len(result.urls)} 個")
                    self.logger.info(f"- Emails: {len(result.emails)} 個")
                    self.logger.info(f"- Hosts: {len(result.hosts)} 個")
                    self.logger.info(f"- IPs: {len(result.direct_ips)} 個")
                    
                else:
                    # 處理錯誤情況
                    result.status = 'error'
                    result.error = error if error else "未知錯誤"
                    self.logger.error(f"掃描失敗: {result.error}")
                
                # 提交更改
                db.session.commit()
                self.logger.info(f"成功保存掃描結果到數據庫 (target_id: {target_id})")
                
        except Exception as e:
            db.session.rollback()
            error_msg = f"保存掃描結果到數據庫失敗: {str(e)}"
            self.logger.error(error_msg)
            self.logger.exception("詳細錯誤堆棧:")
            raise

    @staticmethod
    def _clean_and_validate_data(data_list, data_type):
        """線程安全的數據清理和驗證方法"""
        if not isinstance(data_list, list):
            return []
        
        cleaned_data = set()
        for item in data_list:
            if not item or not isinstance(item, (str, int, float)):
                continue
                
            item = str(item).strip()
            
            # 根據數據類型進行驗證
            if data_type == 'url':
                if item.startswith(('http://', 'https://')):
                    cleaned_data.add(item)
            elif data_type == 'email':
                if '@' in item and '.' in item.split('@')[1]:
                    cleaned_data.add(item)
            elif data_type == 'host':
                if '.' in item and not item.startswith(('http://', 'https://')):
                    cleaned_data.add(item)
            elif data_type == 'ip':
                if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', item):
                    cleaned_data.add(item)
            else:
                cleaned_data.add(item)
        
        return sorted(list(cleaned_data))

if __name__ == '__main__':
    # 测试代码
    scanner = HarvesterScanner()
    result = scanner.run_harvester('example.com', target_id=1, limit=100, sources='all')
    print(json.dumps(result, indent=2, ensure_ascii=False)) 