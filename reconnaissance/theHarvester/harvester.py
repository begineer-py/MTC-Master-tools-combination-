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

class HarvesterScanner:
    """theHarvester 掃描器"""
    
    def __init__(self):
        self._setup_logger()
        self.harvester_path = os.path.join(os.getcwd(), 'tools', 'theHarvester', 'theHarvester.py')
        
    def _setup_logger(self):
        """設置日志記錄器"""
        self.logger = logging.getLogger('HarvesterScanner')
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 添加控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
    def _run_single_source(self, domain, source, limit=None):
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
                '-n',  # DNS 查詢
                '-c'   # DNS 暴力破解
            ]
            
            if limit is not None:
                cmd.extend(['-l', str(limit)])
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if process.returncode != 0:
                self.logger.warning(f"數據源 {source} 掃描失敗: {process.stderr}")
                return None
                
            return process.stdout
            
        except Exception as e:
            self.logger.error(f"數據源 {source} 掃描出錯: {str(e)}")
            return None
            
    def _parse_output(self, output):
        """解析掃描輸出
        
        Args:
            output: 掃描輸出文本
            
        Returns:
            dict: 解析後的結果
        """
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
        
        current_section = None
        for line in output.split('\n'):
            line = line.strip()
            
            if not line:
                continue
                
            if '[*] Emails found:' in line:
                current_section = 'emails'
            elif '[*] Hosts found:' in line:
                current_section = 'hosts'
            elif '[*] URLs found:' in line:
                current_section = 'urls'
            elif '[*] IPs found:' in line:
                current_section = 'ips'
            elif '[*] ASNs found:' in line:
                current_section = 'asns'
            elif '[*] LinkedIn employees found:' in line:
                current_section = 'linkedin'
            elif '[*] DNS Records found:' in line:
                current_section = 'dns_records'
            elif '[*] IP Ranges found:' in line:
                current_section = 'ip_ranges'
            elif '[*] Reverse DNS records found:' in line:
                current_section = 'reverse_dns'
            elif current_section and line.startswith('[-]'):
                current_section = None
            elif current_section and not line.startswith('['):
                result[current_section].append(line)
                
        return result
        
    def _merge_results(self, results):
        """合併多個掃描結果
        
        Args:
            results: 掃描結果列表
            
        Returns:
            dict: 合併後的結果
        """
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
        
        return {k: list(v) for k, v in merged.items()}
        
    def run_harvester(self, domain, target_id, limit=None, sources='all'):
        """運行 theHarvester 掃描
        
        Args:
            domain: 目標域名
            target_id: 目標ID
            limit: 結果限制數
            sources: 數據源（逗號分隔的字符串或'all'）
            
        Returns:
            tuple: (success, result)
        """
        try:
            self.logger.info(f"開始掃描目標: {domain}")
            
            # 確定要使用的數據源
            if sources == 'all':
                source_list = ['baidu', 'bing', 'google', 'yahoo', 'duckduckgo']
            else:
                source_list = sources.split(',')
            
            # 創建線程池
            results = []
            with ThreadPoolExecutor(max_workers=min(len(source_list), 5)) as executor:
                future_to_source = {
                    executor.submit(self._run_single_source, domain, source, limit): source
                    for source in source_list
                }
                
                for future in as_completed(future_to_source):
                    source = future_to_source[future]
                    try:
                        output = future.result()
                        if output:
                            result = self._parse_output(output)
                            results.append(result)
                            self.logger.info(f"數據源 {source} 掃描完成")
                        else:
                            self.logger.warning(f"數據源 {source} 返回空結果")
                    except Exception as e:
                        self.logger.error(f"處理數據源 {source} 結果時出錯: {str(e)}")
            
            # 合併結果
            merged_result = self._merge_results(results)
            
            # 更新數據庫
            self._update_db_result(target_id, merged_result)
            
            return True, merged_result
            
        except Exception as e:
            error_msg = f"掃描過程出錯: {str(e)}"
            self.logger.error(error_msg)
            self._update_db_result(target_id, None, error_msg)
            return False, error_msg
            
    def _update_db_result(self, target_id, scan_data=None, error=None):
        """更新數據庫中的掃描結果
        
        Args:
            target_id: 目標ID
            scan_data: 掃描結果數據（可選）
            error: 錯誤信息（可選）
        """
        try:
            # 查找現有結果或創建新結果
            result = HarvesterResult.query.filter_by(target_id=target_id).first()
            if not result:
                result = HarvesterResult(target_id=target_id)
                db.session.add(result)
            
            # 更新結果
            result.scan_time = datetime.now()
            
            if scan_data is not None:
                result.status = 'completed'
                result.urls = scan_data['urls']
                result.emails = scan_data['emails']
                result.hosts = scan_data['hosts']
                result.direct_ips = scan_data['ips']
                result.asn_info = scan_data['asns']
                result.social_media = scan_data.get('linkedin', [])
                result.dns_records = scan_data['dns_records']
                result.ip_ranges = scan_data['ip_ranges']
                result.reverse_dns = scan_data['reverse_dns']
                result.error = None
            else:
                result.status = 'error'
                result.error = error
            
            db.session.commit()
            self.logger.info(f"成功更新數據庫結果 (target_id: {target_id})")
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"更新數據庫結果失敗: {str(e)}")
            raise
            
if __name__ == '__main__':
    # 测试代码
    scanner = HarvesterScanner()
    result = scanner.run_harvester('example.com', target_id=1, limit=100, sources='all')
    print(json.dumps(result, indent=2, ensure_ascii=False)) 