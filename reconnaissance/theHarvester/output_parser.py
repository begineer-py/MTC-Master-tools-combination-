import logging
from typing import Dict, Set, List, Optional
import re
from datetime import datetime
import json

class OutputParser:
    """命令輸出解析器類"""
    
    def __init__(self):
        self._setup_logger()
        
    def _setup_logger(self):
        """設置日誌記錄器"""
        self.logger = logging.getLogger('OutputParser')
        self.logger.setLevel(logging.INFO)
        
        # 創建格式化器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 添加控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
    def _clean_line(self, line: str) -> str:
        """清理輸出行"""
        line = line.strip()
        line = re.sub(r'\s+', ' ', line)
        line = line.replace('*', '').replace('[+]', '').replace('[-]', '')
        return line.strip()
        
    def _is_valid_host(self, host: str) -> bool:
        """驗證主機名是否有效"""
        if not host:
            return False
            
        # 清理主機名
        host = host.lower().strip()
        
        # 排除無效的主機名
        invalid_patterns = [
            r'^\*',              # 通配符
            r'^\[',              # 方括號開頭
            r'^-',               # 破折號開頭
            r'^$',               # 空字符串
            r'^unknown$',        # unknown
            r'^localhost$',      # localhost
            r'^none$',           # none
            r'^example\.',       # example.com 等測試域名
            r'^test\.',          # test.com 等測試域名
            r'^invalid$',        # invalid
            r'^null$',           # null
            r'^undefined$',      # undefined
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, host):
                return False
                
        # 檢查是否包含有效的域名部分
        domain_pattern = r'^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,}$'
        if not re.match(domain_pattern, host):
            # 如果不是標準格式，檢查是否為IP地址
            if self._is_valid_ip(host):
                return False  # IP地址應該放在IPs集合中
            # 檢查是否為CNAME記錄
            if '.amazonaws.com' in host or '.cloudfront.net' in host or '.github.io' in host:
                return True
            return False
            
        return True
        
    def _is_valid_email(self, email: str) -> bool:
        """驗證郵件地址是否有效"""
        if not email:
            return False
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
        
    def _is_valid_ip(self, ip: str) -> bool:
        """驗證IP地址是否有效"""
        if not ip:
            return False
            
        # 清理IP地址
        ip = ip.strip()
        
        # 檢查IPv4
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ipv4_pattern, ip):
            # 驗證每個數字段
            for part in ip.split('.'):
                if not 0 <= int(part) <= 255:
                    return False
            return True
            
        # 檢查IPv6
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|' \
                      r'^([0-9a-fA-F]{1,4}:){1,7}:|' \
                      r'^([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}$|' \
                      r'^([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}$|' \
                      r'^([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}$|' \
                      r'^([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}$|' \
                      r'^([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}$|' \
                      r'^[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})$|' \
                      r'^:((:[0-9a-fA-F]{1,4}){1,7}|:)$|' \
                      r'^fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}$|' \
                      r'^::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])$|' \
                      r'^([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])$'
                      
        return bool(re.match(ipv6_pattern, ip))
        
    def _is_valid_url(self, url: str) -> bool:
        """驗證URL是否有效"""
        if not url:
            return False
        url_pattern = r'^(http|https)://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[a-zA-Z0-9./-]*$'
        return bool(re.match(url_pattern, url))
        
    def parse_output(self, output: str) -> Dict:
        """解析命令輸出"""
        if not output:
            self.logger.warning("收到空輸出")
            return self._create_empty_result()
            
        self.logger.info("開始解析命令輸出")
        
        try:
            # 嘗試解析 JSON 格式
            try:
                json_data = json.loads(output)
                if isinstance(json_data, dict):
                    return self._parse_json_output(json_data)
            except json.JSONDecodeError:
                pass
            
            # 如果不是 JSON，按文本格式解析
            result = {
                'urls': set(),
                'hosts': set(),
                'emails': set(),
                'ips': set(),
                'asns': set()
            }
            
            current_section = None
            source_name = None
            lines = output.split('\n')
            
            for i, line in enumerate(lines):
                line = self._clean_line(line)
                if not line:
                    continue
                    
                # 檢測源名稱
                if line.startswith('[') and ']' in line:
                    source_name = line[1:line.index(']')]
                    self.logger.info(f"處理源: {source_name}")
                    continue
                    
                # 跳過頭部信息
                if any(skip in line for skip in ['*******************', 'theHarvester', 'Coded by', 'Edge-Security']):
                    continue
                    
                # 識別部分
                if '[*] Hosts found:' in line or '[+] Hosts found:' in line:
                    current_section = 'hosts'
                    continue
                elif '[*] Emails found:' in line or '[+] Emails found:' in line:
                    current_section = 'emails'
                    continue
                elif '[*] IPs found:' in line or '[+] IPs found:' in line:
                    current_section = 'ips'
                    continue
                elif '[*] URLs found:' in line or '[+] URLs found:' in line or '[*] Interesting URLs found:' in line:
                    current_section = 'urls'
                    continue
                elif '[*] ASNs found:' in line or '[+] ASNs found:' in line:
                    current_section = 'asns'
                    continue
                elif line.startswith('--------------------'):
                    continue
                elif '[*] Target:' in line or '[*] Searching' in line:
                    continue
                elif line.startswith('[!]'):  # 錯誤信息
                    self.logger.warning(f"源 {source_name} 報告錯誤: {line}")
                    continue
                    
                # 處理數據
                if current_section == 'hosts':
                    parts = line.split(':')
                    host = parts[0].strip()
                    if self._is_valid_host(host):
                        result['hosts'].add(host)
                        if len(parts) > 1:
                            ip_part = parts[1].strip()
                            if self._is_valid_ip(ip_part):
                                result['ips'].add(ip_part)
                        
                elif current_section == 'emails':
                    if self._is_valid_email(line):
                        result['emails'].add(line)
                        domain = line.split('@')[1]
                        if self._is_valid_host(domain):
                            result['hosts'].add(domain)
                        
                elif current_section == 'ips':
                    if ':' in line:  # 可能是IPv6
                        if self._is_valid_ip(line):
                            result['ips'].add(line)
                    else:
                        ip = line.split(':')[0] if ':' in line else line
                        if self._is_valid_ip(ip):
                            result['ips'].add(ip)
                        
                elif current_section == 'urls':
                    if self._is_valid_url(line):
                        result['urls'].add(line)
                        try:
                            from urllib.parse import urlparse
                            parsed = urlparse(line)
                            if self._is_valid_host(parsed.netloc):
                                result['hosts'].add(parsed.netloc)
                        except Exception as e:
                            self.logger.error(f"解析URL時出錯: {str(e)}")
                        
                elif current_section == 'asns':
                    if line and not line.startswith('-'):
                        result['asns'].add(line)
                        
            # 轉換結果為排序後的列表
            final_result = {k: sorted(list(v)) for k, v in result.items()}
            
            # 記錄統計信息
            self._log_statistics(final_result)
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"解析輸出時出錯: {str(e)}")
            return self._create_empty_result()
        
    def _parse_json_output(self, json_data: Dict) -> Dict:
        """解析 JSON 格式的輸出"""
        try:
            result = {
                'urls': set(),
                'hosts': set(),
                'emails': set(),
                'ips': set(),
                'asns': set()
            }
            
            # 處理 JSON 數據
            for key in result:
                if key in json_data:
                    items = json_data[key]
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, str):
                                if key == 'hosts' and self._is_valid_host(item):
                                    result['hosts'].add(item)
                                elif key == 'emails' and self._is_valid_email(item):
                                    result['emails'].add(item)
                                elif key == 'ips' and self._is_valid_ip(item):
                                    result['ips'].add(item)
                                elif key == 'urls' and self._is_valid_url(item):
                                    result['urls'].add(item)
                                elif key == 'asns':
                                    result['asns'].add(item)
                                    
            # 轉換為排序後的列表
            final_result = {k: sorted(list(v)) for k, v in result.items()}
            
            # 記錄統計信息
            self._log_statistics(final_result)
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"解析 JSON 輸出時出錯: {str(e)}")
            return self._create_empty_result()
        
    def _create_empty_result(self) -> Dict:
        """創建空結果字典"""
        return {
            'urls': [],
            'hosts': [],
            'emails': [],
            'ips': [],
            'asns': [],
            'linkedin': [],
            'dns_records': [],
            'ip_ranges': [],
            'reverse_dns': []
        }
        
    def _log_statistics(self, result: Dict):
        """記錄結果統計信息"""
        self.logger.info("\n=== 解析結果統計 ===")
        for key, value in result.items():
            self.logger.info(f"{key}: {len(value)} 個")
        self.logger.info("==================\n")
        
    def save_to_file(self, result: Dict, filename: Optional[str] = None) -> str:
        """將結果保存到文件
        
        Args:
            result: 解析結果
            filename: 可選的文件名
            
        Returns:
            str: 保存的文件路徑
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'harvester_output_{timestamp}.txt'
            
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for key, values in result.items():
                    if values:
                        f.write(f"\n=== {key.upper()} ===\n")
                        for value in values:
                            f.write(f"{value}\n")
                            
            self.logger.info(f"結果已保存到文件: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"保存結果到文件時出錯: {str(e)}")
            return ''

def create_output_parser() -> OutputParser:
    """創建輸出解析器實例"""
    return OutputParser()

if __name__ == '__main__':
    # 設置日誌級別
    logging.basicConfig(level=logging.INFO)
    
    # 測試代碼
    parser = create_output_parser()
    
    test_output = """
    [*] Hosts found:
    example.com
    api.example.com
    
    [*] Emails found:
    test@example.com
    admin@example.com
    
    [*] IPs found:
    192.168.1.1
    10.0.0.1
    
    [*] Interesting Urls found:
    https://example.com/api
    http://api.example.com/docs
    """
    
    result = parser.parse_output(test_output)
    parser.save_to_file(result, 'test_output.txt') 