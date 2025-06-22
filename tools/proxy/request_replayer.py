#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP請求重放器
用於重新發送編輯後的HTTP請求並分析響應
"""

import socket
import ssl
import urllib.parse
import threading
import time
from datetime import datetime


class HTTPResponse:
    """HTTP響應數據結構"""
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.status_code = 0
        self.status_message = ""
        self.headers = {}
        self.body = ""
        self.response_time = 0
        self.timestamp = datetime.now()
        self._parse_response()
    
    def _parse_response(self):
        """解析HTTP響應"""
        try:
            response_str = self.raw_data.decode('utf-8', errors='ignore')
            lines = response_str.split('\r\n')
            
            if lines:
                # 解析狀態行
                status_line = lines[0]
                parts = status_line.split(' ', 2)
                if len(parts) >= 2:
                    try:
                        self.status_code = int(parts[1])
                    except ValueError:
                        self.status_code = 0
                    
                    if len(parts) >= 3:
                        self.status_message = parts[2]
                
                # 解析headers
                header_end = -1
                for i, line in enumerate(lines[1:], 1):
                    if line == '':
                        header_end = i
                        break
                    if ':' in line:
                        key, value = line.split(':', 1)
                        self.headers[key.strip().lower()] = value.strip()
                
                # 解析body
                if header_end > 0 and header_end < len(lines):
                    self.body = '\r\n'.join(lines[header_end + 1:])
        
        except Exception as e:
            print(f"解析響應時出錯: {e}")
    
    def to_string(self):
        """將響應轉換為字符串格式"""
        headers_str = '\n'.join([f"{k}: {v}" for k, v in self.headers.items()])
        return f"""時間: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
狀態碼: {self.status_code} {self.status_message}
響應時間: {self.response_time:.3f}秒

Headers:
{headers_str}

Body:
{self.body}
"""


class RequestReplayer:
    """HTTP請求重放器"""
    
    def __init__(self):
        self.timeout = 10  # 超時時間（秒）
    
    def replay_request(self, raw_request, callback=None):
        """
        重放HTTP請求
        
        Args:
            raw_request (str): 原始HTTP請求字符串
            callback (function): 響應回調函數
        
        Returns:
            HTTPResponse: HTTP響應對象
        """
        def replay_worker():
            try:
                response = self._send_request(raw_request)
                if callback:
                    callback(response, None)
                return response
            except Exception as e:
                if callback:
                    callback(None, str(e))
                return None
        
        # 在新線程中執行請求
        thread = threading.Thread(target=replay_worker, daemon=True)
        thread.start()
        
        return thread
    
    def _send_request(self, raw_request):
        """發送HTTP請求"""
        start_time = time.time()
        
        try:
            # 解析請求
            request_info = self._parse_request(raw_request)
            if not request_info:
                raise ValueError("無法解析HTTP請求")
            
            host = request_info['host']
            port = request_info['port']
            is_https = request_info['is_https']
            
            # 創建socket連接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            try:
                # 連接到服務器
                sock.connect((host, port))
                
                # 如果是HTTPS，包裝SSL
                if is_https:
                    context = ssl.create_default_context()
                    sock = context.wrap_socket(sock, server_hostname=host)
                
                # 發送請求
                sock.send(raw_request.encode('utf-8'))
                
                # 接收響應
                response_data = b""
                while True:
                    try:
                        chunk = sock.recv(4096)
                        if not chunk:
                            break
                        response_data += chunk
                        
                        # 檢查是否接收完整（簡單檢查）
                        if b'\r\n\r\n' in response_data:
                            # 檢查Content-Length
                            header_part = response_data.split(b'\r\n\r\n')[0]
                            headers_str = header_part.decode('utf-8', errors='ignore')
                            
                            content_length = 0
                            for line in headers_str.split('\r\n'):
                                if line.lower().startswith('content-length:'):
                                    try:
                                        content_length = int(line.split(':', 1)[1].strip())
                                    except:
                                        content_length = 0
                                    break
                            
                            if content_length > 0:
                                body_start = response_data.find(b'\r\n\r\n') + 4
                                body_received = len(response_data) - body_start
                                if body_received >= content_length:
                                    break
                            else:
                                # 沒有Content-Length，等待一小段時間
                                sock.settimeout(0.5)
                                try:
                                    chunk = sock.recv(4096)
                                    if not chunk:
                                        break
                                    response_data += chunk
                                except socket.timeout:
                                    break
                    
                    except socket.timeout:
                        break
                
                # 計算響應時間
                response_time = time.time() - start_time
                
                # 創建響應對象
                response = HTTPResponse(response_data)
                response.response_time = response_time
                
                return response
            
            finally:
                sock.close()
        
        except Exception as e:
            response_time = time.time() - start_time
            raise Exception(f"發送請求失敗 (耗時 {response_time:.3f}s): {str(e)}")
    
    def _parse_request(self, raw_request):
        """解析HTTP請求，提取主機和端口信息"""
        try:
            lines = raw_request.strip().split('\r\n')
            if not lines:
                return None
            
            # 解析請求行
            request_line = lines[0]
            parts = request_line.split(' ')
            if len(parts) < 2:
                return None
            
            method = parts[0]
            url = parts[1]
            
            # 解析headers以獲取Host
            host = ""
            port = 80
            is_https = False
            
            for line in lines[1:]:
                if line == '':
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'host':
                        if ':' in value:
                            host, port_str = value.split(':', 1)
                            try:
                                port = int(port_str)
                            except ValueError:
                                port = 80
                        else:
                            host = value
                            port = 80
            
            # 檢查URL中是否包含完整的scheme
            if url.startswith('https://'):
                is_https = True
                if port == 80:
                    port = 443
                parsed_url = urllib.parse.urlparse(url)
                if parsed_url.hostname:
                    host = parsed_url.hostname
                if parsed_url.port:
                    port = parsed_url.port
            elif url.startswith('http://'):
                is_https = False
                parsed_url = urllib.parse.urlparse(url)
                if parsed_url.hostname:
                    host = parsed_url.hostname
                if parsed_url.port:
                    port = parsed_url.port
            
            if not host:
                return None
            
            return {
                'host': host,
                'port': port,
                'is_https': is_https,
                'method': method,
                'url': url
            }
        
        except Exception as e:
            print(f"解析請求時出錯: {e}")
            return None


class ReplayResultWindow:
    """重放結果顯示窗口"""
    
    def __init__(self, parent, request_text):
        self.parent = parent
        self.request_text = request_text
        self.window = None
        self.response = None
        self.error = None
        
        self._create_window()
        self._start_replay()
    
    def _create_window(self):
        """創建結果窗口"""
        import tkinter as tk
        from tkinter import ttk, scrolledtext
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("請求重放結果")
        self.window.geometry("800x600")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 狀態框架
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="正在發送請求...", foreground="orange")
        self.status_label.pack(side=tk.LEFT)
        
        # 進度條
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=(10, 0))
        self.progress.start()
        
        # 創建Notebook
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 請求標籤頁
        request_frame = ttk.Frame(notebook)
        notebook.add(request_frame, text="發送的請求")
        
        self.request_display = scrolledtext.ScrolledText(
            request_frame, 
            wrap=tk.WORD,
            bg="#f8f8f8",
            state=tk.DISABLED
        )
        self.request_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 顯示請求內容
        self.request_display.config(state=tk.NORMAL)
        self.request_display.insert(1.0, self.request_text)
        self.request_display.config(state=tk.DISABLED)
        
        # 響應標籤頁
        response_frame = ttk.Frame(notebook)
        notebook.add(response_frame, text="服務器響應")
        
        self.response_display = scrolledtext.ScrolledText(
            response_frame, 
            wrap=tk.WORD,
            bg="#f8f8f8"
        )
        self.response_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 按鈕框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame, 
            text="關閉", 
            command=self.window.destroy
        ).pack(side=tk.RIGHT)
        
        ttk.Button(
            button_frame, 
            text="再次重放", 
            command=self._start_replay
        ).pack(side=tk.RIGHT, padx=(0, 10))
    
    def _start_replay(self):
        """開始重放請求"""
        self.status_label.config(text="正在發送請求...", foreground="orange")
        self.progress.start()
        self.response_display.delete(1.0, 'end')
        
        # 創建重放器並發送請求
        replayer = RequestReplayer()
        replayer.replay_request(self.request_text, self._on_response)
    
    def _on_response(self, response, error):
        """處理響應回調"""
        def update_ui():
            self.progress.stop()
            
            if error:
                self.status_label.config(text=f"請求失敗: {error}", foreground="red")
                self.response_display.insert(1.0, f"錯誤: {error}")
            else:
                self.status_label.config(
                    text=f"請求成功 - 狀態碼: {response.status_code} - 響應時間: {response.response_time:.3f}s", 
                    foreground="green"
                )
                self.response_display.insert(1.0, response.to_string())
        
        # 在主線程中更新UI
        self.window.after(0, update_ui) 