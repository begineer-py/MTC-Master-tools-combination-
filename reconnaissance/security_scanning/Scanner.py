import nmap
import json
from instance.models import nmap_Result, db
from flask import current_app
from datetime import datetime
import time
from sqlalchemy.exc import OperationalError

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
        
        # 根據掃描類型選擇端口範圍
        if scan_type == 'full':
            # 常見100端口掃描
            common_100_ports = [
                7,     # Echo
                20,    # FTP-DATA
                21,    # FTP
                22,    # SSH
                23,    # Telnet
                25,    # SMTP
                43,    # WHOIS
                53,    # DNS
                69,    # TFTP
                80,    # HTTP
                88,    # Kerberos
                102,   # MS Exchange
                110,   # POP3
                111,   # RPC
                119,   # NNTP
                123,   # NTP
                135,   # MSRPC
                137,   # NetBIOS
                138,   # NetBIOS
                139,   # NetBIOS
                143,   # IMAP
                161,   # SNMP
                162,   # SNMP Trap
                177,   # XDMCP
                179,   # BGP
                194,   # IRC
                201,   # AppleTalk
                264,   # BGMP
                389,   # LDAP
                443,   # HTTPS
                445,   # SMB
                464,   # Kerberos
                465,   # SMTPS
                497,   # Dantz
                500,   # ISAKMP
                502,   # Modbus
                512,   # rexec
                513,   # rlogin
                514,   # Syslog
                515,   # LPD/LPR
                520,   # RIP
                521,   # RIPng
                540,   # UUCP
                554,   # RTSP
                587,   # SMTP
                593,   # HTTP RPC
                623,   # IPMI
                626,   # OS Services
                631,   # IPP
                636,   # LDAPS
                666,   # Doom
                771,   # RealSecure
                789,   # RedLion
                873,   # rsync
                902,   # VMware
                993,   # IMAPS
                995,   # POP3S
                1025,  # NFS
                1026,  # Windows
                1027,  # Windows
                1028,  # Windows
                1029,  # Windows
                1080,  # SOCKS
                1099,  # RMI Registry
                1177,  # Windows
                1194,  # OpenVPN
                1234,  # VLC
                1433,  # MSSQL
                1434,  # MSSQL
                1521,  # Oracle
                1604,  # Citrix
                1723,  # PPTP
                1725,  # Steam
                1741,  # CiscoWorks
                1812,  # RADIUS
                1813,  # RADIUS
                1883,  # MQTT
                1900,  # UPnP
                2000,  # Cisco SCCP
                2049,  # NFS
                2082,  # cPanel
                2083,  # cPanel SSL
                2086,  # WHM
                2087,  # WHM SSL
                2096,  # cPanel Webmail
                2181,  # Zookeeper
                2222,  # DirectAdmin
                2375,  # Docker
                2376,  # Docker SSL
                3128,  # Squid
                3306,  # MySQL
                3389,  # RDP
                3690,  # SVN
                4333,  # mSQL
                4444,  # Metasploit
                4899,  # Radmin
                5000,  # Python
                5432,  # PostgreSQL
                5900,  # VNC
                5938,  # TeamViewer
                6379,  # Redis
                7001,  # Weblogic
                8000,  # HTTP Alt
                8080,  # HTTP Proxy
                8443,  # HTTPS Alt
                8888,  # HTTP Alt
                9000,  # Jenkins
                9090,  # HTTP Alt
                9200,  # Elasticsearch
                9418,  # Git
                9999,  # HTTP Alt
                10000, # Webmin
                27017, # MongoDB
                28017  # MongoDB Web
            ]
            ports_str = ','.join(map(str, common_100_ports))
            current_app.logger.info("執行常見100端口掃描")
        else:
            # 常見端口掃描
            common_ports = [
                21,    # FTP
                22,    # SSH
                23,    # Telnet
                25,    # SMTP
                53,    # DNS
                80,    # HTTP
                110,   # POP3
                135,   # MSRPC
                139,   # NetBIOS
                143,   # IMAP
                443,   # HTTPS
                445,   # SMB
                993,   # IMAPS
                995,   # POP3S
                1723,  # PPTP
                3306,  # MySQL
                3389,  # RDP
                5900,  # VNC
                8080   # HTTP Proxy
            ]
            ports_str = ','.join(map(str, common_ports))
            current_app.logger.info("執行常見端口掃描")
        
        # 執行掃描
        scan_result = nm.scan(
            target_ip_no_https, 
            arguments=f'-sS -sV -T4 -p{ports_str} --version-intensity 9 --version-all --max-rtt-timeout 30s --min-rtt-timeout 10s --initial-rtt-timeout 10s'
        )
        
        # 獲取當前時間
        scan_time = datetime.now()
        
        # 格式化掃描結果
        formatted_result = format_scan_result(scan_result, scan_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        # 確保所有掃描的端口都在結果中
        if 'ports' not in formatted_result:
            formatted_result['ports'] = {}
            
        # 如果是常見端口掃描，確保所有常見端口都在結果中
        if scan_type == 'common':
            for port in common_ports:
                port_str = str(port)
                if port_str not in formatted_result['ports']:
                    formatted_result['ports'][port_str] = {
                        "state": "filtered",
                        "name": "unknown",
                        "product": "",
                        "version": ""
                    }
        elif scan_type == 'full':
            for port in common_100_ports:
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
                    existing_result.scan_type = scan_type  # 添加掃描類型
                else:
                    new_result = nmap_Result(
                        target_id=target_id,
                        scan_result=json.dumps(formatted_result),
                        scan_time=scan_time,
                        scan_type=scan_type  # 添加掃描類型
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
            "scan_type": scan_type  # 添加掃描類型
        }
        return error_result, False, 500
