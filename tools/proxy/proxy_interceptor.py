#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP代理攔截器 - 類似Burp Suite的功能
監聽9487端口，攔截並記錄HTTP請求
"""

import socket
import threading
import time
import re
import urllib.parse
from datetime import datetime


class HTTPRequest:
    """HTTP請求數據結構"""
    def __init__(self, raw_data, client_addr):
        self.raw_data = raw_data
        self.client_addr = client_addr
        self.timestamp = datetime.now()
        self.method = ""
        self.url = ""
        self.path = ""
        self.headers = {}
        self.body = ""
        self.host = ""
        self.port = 80
        self._parse_request()
    
    def _parse_request(self):
        """解析HTTP請求"""
        try:
            lines = self.raw_data.decode('utf-8', errors='ignore').split('\r\n')
            if lines:
                # 解析請求行
                request_line = lines[0]
                parts = request_line.split(' ')
                if len(parts) >= 2:
                    self.method = parts[0]
                    self.url = parts[1]
                    
                    # 解析URL
                    if self.url.startswith('http://') or self.url.startswith('https://'):
                        parsed = urllib.parse.urlparse(self.url)
                        self.host = parsed.hostname or ''
                        self.port = parsed.port or (443 if parsed.scheme == 'https' else 80)
                        self.path = parsed.path + ('?' + parsed.query if parsed.query else '')
                    else:
                        self.path = self.url
                
                # 解析headers
                header_end = -1
                for i, line in enumerate(lines[1:], 1):
                    if line == '':
                        header_end = i
                        break
                    if ':' in line:
                        key, value = line.split(':', 1)
                        self.headers[key.strip().lower()] = value.strip()
                
                # 獲取Host
                if 'host' in self.headers:
                    host_header = self.headers['host']
                    if ':' in host_header:
                        self.host, port_str = host_header.split(':', 1)
                        try:
                            self.port = int(port_str)
                        except ValueError:
                            self.port = 80
                    else:
                        self.host = host_header
                
                # 解析body
                if header_end > 0 and header_end < len(lines):
                    self.body = '\r\n'.join(lines[header_end + 1:])
        
        except Exception as e:
            print(f"解析請求時出錯: {e}")
    
    def to_string(self):
        """將請求轉換為字符串格式"""
        headers_str = '\n'.join([f"{k}: {v}" for k, v in self.headers.items()])
        return f"""時間: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
客戶端: {self.client_addr[0]}:{self.client_addr[1]}
方法: {self.method}
URL: {self.url}
主機: {self.host}:{self.port}
路徑: {self.path}

Headers:
{headers_str}

Body:
{self.body}
"""


class ProxyInterceptor:
    """HTTP代理攔截器"""
    
    def __init__(self, port=9487):
        self.port = port
        self.running = False
        self.server_socket = None
        self.requests = []  # 存儲捕捉到的請求
        self.callbacks = []  # 新請求回調函數
    
    def add_request_callback(self, callback):
        """添加新請求的回調函數"""
        self.callbacks.append(callback)
    
    def start(self):
        """啟動代理服務器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(10)
            self.running = True
            
            print(f"代理服務器已啟動，監聽端口 {self.port}")
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    # 為每個客戶端連接創建新線程
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_addr),
                        daemon=True
                    )
                    client_thread.start()
                except socket.error:
                    if self.running:
                        print("接受連接時出錯")
                    break
        
        except Exception as e:
            print(f"啟動代理服務器時出錯: {e}")
    
    def stop(self):
        """停止代理服務器"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("代理服務器已停止")
    
    def _handle_client(self, client_socket, client_addr):
        """處理客戶端連接"""
        try:
            # 接收客戶端請求
            request_data = b""
            client_socket.settimeout(10)  # 設置超時
            
            while True:
                try:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    request_data += chunk
                    
                    # 檢查是否接收完整的HTTP請求
                    if b'\r\n\r\n' in request_data:
                        # 檢查是否有Content-Length
                        header_end = request_data.find(b'\r\n\r\n')
                        headers = request_data[:header_end].decode('utf-8', errors='ignore')
                        
                        content_length = 0
                        for line in headers.split('\r\n'):
                            if line.lower().startswith('content-length:'):
                                try:
                                    content_length = int(line.split(':', 1)[1].strip())
                                except:
                                    content_length = 0
                                break
                        
                        body_received = len(request_data) - header_end - 4
                        if body_received >= content_length:
                            break
                except socket.timeout:
                    break
                except:
                    break
            
            if request_data:
                # 創建HTTPRequest對象
                http_request = HTTPRequest(request_data, client_addr)
                self.requests.append(http_request)
                
                # 通知所有回調函數
                for callback in self.callbacks:
                    try:
                        callback(http_request)
                    except Exception as e:
                        print(f"回調函數執行出錯: {e}")
                
                # 轉發請求到目標服務器
                response = self._forward_request(http_request)
                
                # 返回響應給客戶端
                if response:
                    client_socket.send(response)
        
        except Exception as e:
            print(f"處理客戶端請求時出錯: {e}")
        
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _forward_request(self, http_request):
        """轉發請求到目標服務器"""
        try:
            if not http_request.host:
                # 返回錯誤響應
                return b"HTTP/1.1 400 Bad Request\r\n\r\nInvalid host"
            
            # 連接到目標服務器
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.settimeout(10)
            target_socket.connect((http_request.host, http_request.port))
            
            # 發送原始請求
            target_socket.send(http_request.raw_data)
            
            # 接收響應
            response_data = b""
            while True:
                try:
                    chunk = target_socket.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk
                except socket.timeout:
                    break
                except:
                    break
            
            target_socket.close()
            return response_data
        
        except Exception as e:
            print(f"轉發請求時出錯: {e}")
            error_response = f"HTTP/1.1 502 Bad Gateway\r\n\r\nProxy Error: {str(e)}"
            return error_response.encode('utf-8')
    
    def get_requests(self):
        """獲取所有捕捉到的請求"""
        return self.requests.copy()
    
    def clear_requests(self):
        """清空請求列表"""
        self.requests.clear() 