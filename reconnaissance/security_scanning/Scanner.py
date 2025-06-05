import nmap
import json
from instance.models import nmap_Result, db
from flask import current_app
from datetime import datetime
import time
from sqlalchemy.exc import OperationalError
import os

class NmapConfig:
    """Nmap 掃描配置類 - 管理掃描參數和選項"""
    
    def __init__(self):
        # 檢查當前用戶權限
        self.has_root_privileges = os.geteuid() == 0 if hasattr(os, 'geteuid') else False
        
        # 掃描參數配置
        self.scan_types = {
            'basic': {
                'name': '基本掃描',
                'args': '-T4 --max-rtt-timeout 30s',
                'requires_root': False
            },
            'connect': {
                'name': 'TCP Connect 掃描',
                'args': '-sT -sV -T4 --version-intensity 5 --max-rtt-timeout 30s',
                'requires_root': False
            },
            'syn': {
                'name': 'TCP SYN 掃描',
                'args': '-sS -sV -T4 --version-intensity 9 --version-all --max-rtt-timeout 30s --min-rtt-timeout 10s --initial-rtt-timeout 10s',
                'requires_root': True
            },
            'comprehensive': {
                'name': '綜合掃描',
                'args': '-sS -sV -sC -T4 --version-intensity 9 --version-all --script=default,safe --max-rtt-timeout 30s',
                'requires_root': True
            }
        }
        
        # 端口配置
        self.port_sets = {
            'common': [
                21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 
                443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080
            ],
            'extended': [  # 114個擴展端口（原名 top100，實際包含114個端口）
                7, 20, 21, 22, 23, 25, 43, 53, 69, 80, 88, 102, 110, 111, 119, 123,
                135, 137, 138, 139, 143, 161, 162, 177, 179, 194, 201, 264, 389, 443,
                445, 464, 465, 497, 500, 502, 512, 513, 514, 515, 520, 521, 540, 554,
                587, 593, 623, 626, 631, 636, 666, 771, 789, 873, 902, 993, 995, 1025,
                1026, 1027, 1028, 1029, 1080, 1099, 1177, 1194, 1234, 1433, 1434, 1521,
                1604, 1723, 1725, 1741, 1812, 1813, 1883, 1900, 2000, 2049, 2082, 2083,
                2086, 2087, 2096, 2181, 2222, 2375, 2376, 3128, 3306, 3389, 3690, 4333,
                4444, 4899, 5000, 5432, 5900, 5938, 6379, 7001, 8000, 8080, 8443, 8888,
                9000, 9090, 9200, 9418, 9999, 10000, 27017, 28017
            ],
            # 保持向後相容性的別名
            'top100': [  # 別名，實際包含114個端口
                7, 20, 21, 22, 23, 25, 43, 53, 69, 80, 88, 102, 110, 111, 119, 123,
                135, 137, 138, 139, 143, 161, 162, 177, 179, 194, 201, 264, 389, 443,
                445, 464, 465, 497, 500, 502, 512, 513, 514, 515, 520, 521, 540, 554,
                587, 593, 623, 626, 631, 636, 666, 771, 789, 873, 902, 993, 995, 1025,
                1026, 1027, 1028, 1029, 1080, 1099, 1177, 1194, 1234, 1433, 1434, 1521,
                1604, 1723, 1725, 1741, 1812, 1813, 1883, 1900, 2000, 2049, 2082, 2083,
                2086, 2087, 2096, 2181, 2222, 2375, 2376, 3128, 3306, 3389, 3690, 4333,
                4444, 4899, 5000, 5432, 5900, 5938, 6379, 7001, 8000, 8080, 8443, 8888,
                9000, 9090, 9200, 9418, 9999, 10000, 27017, 28017
            ]
        }
    
    def get_scan_args(self, scan_type='auto'):
        """獲取掃描參數"""
        if scan_type == 'auto':
            # 自動選擇最佳掃描類型
            if self.has_root_privileges:
                return self.scan_types['syn']['args']
            else:
                return self.scan_types['connect']['args']
        elif scan_type in self.scan_types:
            config = self.scan_types[scan_type]
            if config['requires_root'] and not self.has_root_privileges:
                current_app.logger.warning(f"掃描類型 {scan_type} 需要 root 權限，降級為 connect 掃描")
                return self.scan_types['connect']['args']
            return config['args']
        else:
            return self.scan_types['basic']['args']
    
    def get_ports_string(self, port_set='common'):
        """獲取端口字符串"""
        if port_set in self.port_sets:
            return ','.join(map(str, self.port_sets[port_set]))
        return ','.join(map(str, self.port_sets['common']))

# 創建全局配置實例
nmap_config = NmapConfig()

def format_scan_result(scan_result, scan_time):
    try:
        # 檢查掃描結果
        if not scan_result or 'scan' not in scan_result or not scan_result['scan']:
            current_app.logger.error("Invalid scan result format")
            return {
                "host": "未知",
                "hostname": "未知",
                "state": "未知",
                "ports": {},
                "scan_time": scan_time
            }
        
        # 獲取主機信息
        host = list(scan_result['scan'].keys())[0]
        host_info = scan_result['scan'][host]
        
        # 獲取主機名
        hostname = "未知"
        if 'hostnames' in host_info and host_info['hostnames']:
            if isinstance(host_info['hostnames'], list):
                hostname = host_info['hostnames'][0].get('name', '未知')
            elif isinstance(host_info['hostnames'], dict):
                hostname = host_info['hostnames'].get('name', '未知')
        
        # 獲取主機狀態
        state = "未知"
        if 'status' in host_info:
            state = host_info['status'].get('state', '未知')
        
        # 格式化端口信息
        ports = {}
        if 'tcp' in host_info:
            for port_number, port_info in host_info['tcp'].items():
                ports[str(port_number)] = {
                    "state": port_info.get('state', 'unknown'),
                    "name": port_info.get('name', 'unknown'),
                    "product": port_info.get('product', ''),
                    "version": port_info.get('version', '')
                }
        
        # 構建結果字典
        result = {
            "host": host,
            "hostname": hostname,
            "state": state,
            "ports": ports,
            "scan_time": scan_time
        }
        
        current_app.logger.debug(f"Formatted scan result: {json.dumps(result)}")
        return result
        
    except Exception as e:
        current_app.logger.error(f"Error formatting scan result: {str(e)}")
        return {
            "host": "未知",
            "hostname": "未知",
            "state": "error",
            "ports": {},
            "scan_time": scan_time
        }

def nmap_scan_target(target_ip, target_id, scan_type='common'):
    try:
        # 移除 http:// 或 https:// 前綴，以及路徑和查詢參數
        target_ip_no_https = target_ip.replace('https://', '').replace('http://', '').split('/')[0].split('?')[0]
        
        # 記錄處理後的目標IP
        current_app.logger.debug(f"Processing target IP: {target_ip_no_https}, Scan Type: {scan_type}")
        
        # 創建 nmap 掃描器實例
        nm = nmap.PortScanner()
        
        # 根據掃描類型選擇端口範圍和掃描參數
        if scan_type == 'full':
            ports_str = nmap_config.get_ports_string('top100')
            scan_args = nmap_config.get_scan_args('auto')
            current_app.logger.info("執行擴展端口掃描（114個端口）")
        else:
            ports_str = nmap_config.get_ports_string('common')
            scan_args = nmap_config.get_scan_args('auto')
            current_app.logger.info("執行常見端口掃描（19個端口）")
        
        # 組合完整的掃描參數
        full_args = f"{scan_args} -p{ports_str}"
        
        # 記錄掃描信息
        current_app.logger.info(f"執行掃描: nmap {full_args} {target_ip_no_https}")
        if not nmap_config.has_root_privileges:
            current_app.logger.info("當前以非 root 用戶運行，使用 TCP Connect 掃描")
        
        # 執行掃描
        try:
            scan_result = nm.scan(target_ip_no_https, arguments=full_args)
        except Exception as e:
            if "requires root privileges" in str(e) or "Permission denied" in str(e):
                # 如果仍然需要權限，使用最基本的掃描
                current_app.logger.warning("權限不足，降級為基本掃描模式")
                basic_args = f"{nmap_config.get_scan_args('basic')} -p{ports_str}"
                scan_result = nm.scan(target_ip_no_https, arguments=basic_args)
            else:
                raise e
        
        # 獲取當前時間
        scan_time = datetime.now()
        
        # 格式化掃描結果
        formatted_result = format_scan_result(scan_result, scan_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        # 確保所有掃描的端口都在結果中
        if 'ports' not in formatted_result:
            formatted_result['ports'] = {}
            
        # 根據掃描類型填充端口結果
        port_list = nmap_config.port_sets['top100'] if scan_type == 'full' else nmap_config.port_sets['common']
        for port in port_list:
            port_str = str(port)
            if port_str not in formatted_result['ports']:
                formatted_result['ports'][port_str] = {
                    "state": "filtered",
                    "name": "unknown",
                    "product": "",
                    "version": ""
                }
        
        # 使用重試機制更新數據庫
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            try:
                # 更新或創建數據庫記錄
                existing_result = nmap_Result.query.filter_by(target_id=target_id).first()
                
                if existing_result:
                    existing_result.scan_result = json.dumps(formatted_result)
                    existing_result.scan_time = scan_time
                    existing_result.scan_type = scan_type
                else:
                    new_result = nmap_Result(
                        target_id=target_id,
                        scan_result=json.dumps(formatted_result),
                        scan_time=scan_time,
                        scan_type=scan_type
                    )
                    db.session.add(new_result)
                
                db.session.commit()
                break  # 成功後跳出循環
                
            except OperationalError as e:
                if "database is locked" in str(e):
                    if attempt < max_retries - 1:
                        current_app.logger.warning(f"Database is locked, retrying... (attempt {attempt + 1}/{max_retries})")
                        db.session.rollback()
                        time.sleep(retry_delay)
                    else:
                        current_app.logger.error("Failed to update database after max retries")
                        raise
                else:
                    raise
            except Exception as e:
                db.session.rollback()
                raise
        
        return formatted_result, True, 200
        
    except Exception as e:
        current_app.logger.error(f"Nmap scan error: {str(e)}")
        error_result = {
            "host": target_ip_no_https,
            "hostname": "未知",
            "state": "error",
            "ports": {},
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scan_type": scan_type,
            "error": str(e)
        }
        return error_result, False, 500
