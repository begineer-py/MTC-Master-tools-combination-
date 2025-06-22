#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
內建瀏覽器組件 - 類似Burp Suite的內建瀏覽器
支持自動代理配置、頁面導航、HTML渲染等功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import urllib.parse
import html
import re
import threading
import subprocess
import sys
import webbrowser
from datetime import datetime


class SimpleBrowser:
    """簡單的瀏覽器組件"""
    
    def __init__(self, parent_frame, proxy_port=9487):
        self.parent_frame = parent_frame
        self.proxy_port = proxy_port
        self.current_url = ""
        self.history = []
        self.history_index = -1
        
        # 代理配置
        self.proxies = {
            'http': f'http://127.0.0.1:{proxy_port}',
            'https': f'http://127.0.0.1:{proxy_port}'
        }
        
        self._create_browser_ui()
    
    def _create_browser_ui(self):
        """創建瀏覽器UI界面"""
        # 瀏覽器工具欄
        toolbar = ttk.Frame(self.parent_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # 導航按鈕
        self.back_btn = ttk.Button(
            toolbar, 
            text="◀", 
            width=3,
            command=self.go_back,
            state=tk.DISABLED
        )
        self.back_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.forward_btn = ttk.Button(
            toolbar, 
            text="▶", 
            width=3,
            command=self.go_forward,
            state=tk.DISABLED
        )
        self.forward_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 重新整理按鈕
        ttk.Button(
            toolbar, 
            text="↻", 
            width=3,
            command=self.refresh
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # 地址欄
        ttk.Label(toolbar, text="網址:").pack(side=tk.LEFT, padx=(5, 2))
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(
            toolbar, 
            textvariable=self.url_var,
            font=("Consolas", 10)
        )
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.url_entry.bind('<Return>', self.navigate_to_url)
        
        # 訪問按鈕
        ttk.Button(
            toolbar, 
            text="訪問", 
            command=self.navigate_to_url
        ).pack(side=tk.RIGHT)
        
        # 開啟外部瀏覽器按鈕
        ttk.Button(
            toolbar, 
            text="外部瀏覽器", 
            command=self.open_external_browser
        ).pack(side=tk.RIGHT, padx=(0, 5))
        
        # 內容區域
        content_frame = ttk.Frame(self.parent_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # 創建Notebook用於顯示不同類型的內容
        self.content_notebook = ttk.Notebook(content_frame)
        self.content_notebook.pack(fill=tk.BOTH, expand=True)
        
        # HTML渲染標籤頁
        html_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(html_frame, text="頁面內容")
        
        self.html_display = scrolledtext.ScrolledText(
            html_frame,
            wrap=tk.WORD,
            bg="#ffffff",
            fg="#000000",
            font=("Arial", 10)
        )
        self.html_display.pack(fill=tk.BOTH, expand=True)
        
        # 原始HTML標籤頁
        raw_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(raw_frame, text="原始HTML")
        
        self.raw_html = scrolledtext.ScrolledText(
            raw_frame,
            wrap=tk.WORD,
            bg="#f8f8f8",
            fg="#333333",
            font=("Consolas", 9)
        )
        self.raw_html.pack(fill=tk.BOTH, expand=True)
        
        # 狀態欄
        self.status_frame = ttk.Frame(self.parent_frame)
        self.status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.status_label = ttk.Label(
            self.status_frame, 
            text="就緒 - 通過代理端口 9487 瀏覽網頁",
            foreground="green"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # 預設顯示歡迎頁面
        self._show_welcome_page()
    
    def _show_welcome_page(self):
        """顯示歡迎頁面"""
        welcome_html = """
        <h1>🌐 內建代理瀏覽器</h1>
        <hr>
        <h2>歡迎使用HTTP代理攔截器的內建瀏覽器！</h2>
        
        <h3>功能特點：</h3>
        <ul>
            <li>✅ 自動通過代理端口 9487 發送請求</li>
            <li>✅ 所有請求都會被攔截並記錄</li>
            <li>✅ 支持HTTP和HTTPS網站</li>
            <li>✅ 可以查看原始HTML源碼</li>
            <li>✅ 支持開啟外部瀏覽器</li>
        </ul>
        
        <h3>使用說明：</h3>
        <ol>
            <li>在上方地址欄輸入網址（如：http://example.com）</li>
            <li>點擊"訪問"按鈕或按Enter鍵</li>
            <li>頁面內容會顯示在下方</li>
            <li>所有請求會自動在主界面中顯示</li>
        </ol>
        
        <h3>推薦測試網站：</h3>
        <ul>
            <li><a href="http://httpbin.org">http://httpbin.org</a> - HTTP測試工具</li>
            <li><a href="http://example.com">http://example.com</a> - 簡單測試頁面</li>
            <li><a href="http://www.baidu.com">http://www.baidu.com</a> - 百度搜索</li>
        </ul>
        
        <hr>
        <p><em>提示：所有通過此瀏覽器的請求都會被代理攔截器記錄，方便進行安全測試和分析。</em></p>
        """
        
        self._render_simple_html(welcome_html)
        self.status_label.config(text="就緒 - 請在地址欄輸入網址開始瀏覽", foreground="blue")
    
    def navigate_to_url(self, event=None):
        """導航到指定URL"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("錯誤", "請輸入有效的網址")
            return
        
        # 自動添加http://前綴
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            self.url_var.set(url)
        
        self._load_page(url)
    
    def _load_page(self, url):
        """載入網頁"""
        self.status_label.config(text=f"正在載入 {url}...", foreground="orange")
        
        # 在新線程中載入頁面
        thread = threading.Thread(target=self._load_page_worker, args=(url,), daemon=True)
        thread.start()
    
    def _load_page_worker(self, url):
        """在背景線程中載入頁面"""
        try:
            # 使用代理發送請求
            response = requests.get(
                url, 
                proxies=self.proxies, 
                timeout=15,
                headers={
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            
            # 在主線程中更新UI
            self.parent_frame.after(0, self._update_page_content, url, response)
            
        except requests.exceptions.ProxyError:
            self.parent_frame.after(0, self._show_error, "代理連接失敗", "無法連接到代理服務器，請確保代理已啟動")
        except requests.exceptions.Timeout:
            self.parent_frame.after(0, self._show_error, "載入超時", f"載入 {url} 超時")
        except requests.exceptions.RequestException as e:
            self.parent_frame.after(0, self._show_error, "載入失敗", f"載入 {url} 失敗：{str(e)}")
        except Exception as e:
            self.parent_frame.after(0, self._show_error, "未知錯誤", f"發生未知錯誤：{str(e)}")
    
    def _update_page_content(self, url, response):
        """更新頁面內容"""
        self.current_url = url
        
        # 更新歷史記錄
        if self.history_index == -1 or self.history[self.history_index] != url:
            # 如果不在歷史末尾，移除後面的記錄
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            
            self.history.append(url)
            self.history_index = len(self.history) - 1
        
        # 更新導航按鈕狀態
        self.back_btn.config(state=tk.NORMAL if self.history_index > 0 else tk.DISABLED)
        self.forward_btn.config(state=tk.NORMAL if self.history_index < len(self.history) - 1 else tk.DISABLED)
        
        # 顯示頁面內容
        content_type = response.headers.get('content-type', '').lower()
        
        if 'text/html' in content_type:
            # HTML內容
            self._render_simple_html(response.text)
            self.raw_html.delete(1.0, tk.END)
            self.raw_html.insert(1.0, response.text)
        elif 'application/json' in content_type:
            # JSON內容
            try:
                import json
                formatted_json = json.dumps(response.json(), indent=2, ensure_ascii=False)
                self._render_simple_html(f"<h3>JSON Response</h3><pre>{html.escape(formatted_json)}</pre>")
                self.raw_html.delete(1.0, tk.END)
                self.raw_html.insert(1.0, response.text)
            except:
                self._render_simple_html(f"<h3>JSON Response</h3><pre>{html.escape(response.text)}</pre>")
        else:
            # 其他內容類型
            self._render_simple_html(f"<h3>內容類型: {content_type}</h3><pre>{html.escape(response.text[:5000])}</pre>")
            self.raw_html.delete(1.0, tk.END)
            self.raw_html.insert(1.0, response.text)
        
        # 更新狀態
        self.status_label.config(
            text=f"已載入 {url} - 狀態碼: {response.status_code} - 大小: {len(response.content)} bytes",
            foreground="green"
        )
    
    def _render_simple_html(self, html_content):
        """簡單的HTML渲染"""
        self.html_display.delete(1.0, tk.END)
        
        # 移除HTML標籤並保留文本內容
        text_content = self._html_to_text(html_content)
        
        self.html_display.insert(1.0, text_content)
    
    def _html_to_text(self, html_content):
        """將HTML轉換為簡單文本"""
        # 基本的HTML標籤處理
        text = html_content
        
        # 處理標題
        text = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n\1\n' + '='*50 + '\n', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 處理段落
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 處理換行
        text = re.sub(r'<br[^>]*/?>', '\n', text, flags=re.IGNORECASE)
        
        # 處理列表
        text = re.sub(r'<li[^>]*>(.*?)</li>', r'• \1\n', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<ul[^>]*>|</ul>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<ol[^>]*>|</ol>', '\n', text, flags=re.IGNORECASE)
        
        # 處理鏈接
        text = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'\2 [\1]', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 處理粗體和斜體
        text = re.sub(r'<(b|strong)[^>]*>(.*?)</\1>', r'**\2**', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<(i|em)[^>]*>(.*?)</\1>', r'*\2*', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 處理水平線
        text = re.sub(r'<hr[^>]*/?>', '\n' + '-'*50 + '\n', text, flags=re.IGNORECASE)
        
        # 移除所有剩餘的HTML標籤
        text = re.sub(r'<[^>]+>', '', text)
        
        # 解碼HTML實體
        text = html.unescape(text)
        
        # 清理多餘的空行
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def _show_error(self, title, message):
        """顯示錯誤信息"""
        error_html = f"""
        <h2>❌ {title}</h2>
        <hr>
        <p>{message}</p>
        <h3>可能的解決方案：</h3>
        <ul>
            <li>確保代理服務器已啟動（端口 {self.proxy_port}）</li>
            <li>檢查網址是否正確</li>
            <li>檢查網絡連接</li>
            <li>嘗試使用外部瀏覽器</li>
        </ul>
        """
        self._render_simple_html(error_html)
        self.status_label.config(text=f"錯誤: {message}", foreground="red")
    
    def go_back(self):
        """後退"""
        if self.history_index > 0:
            self.history_index -= 1
            url = self.history[self.history_index]
            self.url_var.set(url)
            self._load_page(url)
    
    def go_forward(self):
        """前進"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            url = self.history[self.history_index]
            self.url_var.set(url)
            self._load_page(url)
    
    def refresh(self):
        """重新整理"""
        if self.current_url:
            self._load_page(self.current_url)
    
    def open_external_browser(self):
        """開啟外部瀏覽器並配置代理"""
        url = self.url_var.get().strip()
        if not url:
            url = "http://httpbin.org"
        
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        try:
            # 嘗試使用不同的瀏覽器並配置代理
            if sys.platform.startswith('linux'):
                # Linux系統
                browsers = [
                    ['google-chrome', f'--proxy-server=http://127.0.0.1:{self.proxy_port}'],
                    ['chromium-browser', f'--proxy-server=http://127.0.0.1:{self.proxy_port}'],
                    ['firefox', '-private-window']  # Firefox需要手動配置代理
                ]
                
                for browser_cmd in browsers:
                    try:
                        cmd = browser_cmd + [url]
                        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        messagebox.showinfo(
                            "瀏覽器已開啟", 
                            f"已使用外部瀏覽器開啟 {url}\n\n"
                            f"瀏覽器已配置代理: 127.0.0.1:{self.proxy_port}\n"
                            "如使用Firefox，請手動配置HTTP代理"
                        )
                        return
                    except FileNotFoundError:
                        continue
                
                # 如果沒有找到支持的瀏覽器，使用默認方式
                webbrowser.open(url)
                messagebox.showinfo(
                    "瀏覽器已開啟", 
                    f"已開啟默認瀏覽器訪問 {url}\n\n"
                    "請手動配置瀏覽器代理設置:\n"
                    f"HTTP代理: 127.0.0.1:{self.proxy_port}"
                )
            
            elif sys.platform == 'darwin':
                # macOS系統
                try:
                    subprocess.Popen([
                        'open', '-a', 'Google Chrome', 
                        '--args', f'--proxy-server=http://127.0.0.1:{self.proxy_port}',
                        url
                    ])
                    messagebox.showinfo(
                        "瀏覽器已開啟", 
                        f"已使用Chrome開啟 {url}\n代理已配置: 127.0.0.1:{self.proxy_port}"
                    )
                except:
                    webbrowser.open(url)
                    messagebox.showinfo(
                        "瀏覽器已開啟", 
                        f"已開啟默認瀏覽器\n請手動配置代理: 127.0.0.1:{self.proxy_port}"
                    )
            
            elif sys.platform.startswith('win'):
                # Windows系統
                try:
                    subprocess.Popen([
                        'start', 'chrome', 
                        f'--proxy-server=http://127.0.0.1:{self.proxy_port}',
                        url
                    ], shell=True)
                    messagebox.showinfo(
                        "瀏覽器已開啟", 
                        f"已使用Chrome開啟 {url}\n代理已配置: 127.0.0.1:{self.proxy_port}"
                    )
                except:
                    webbrowser.open(url)
                    messagebox.showinfo(
                        "瀏覽器已開啟", 
                        f"已開啟默認瀏覽器\n請手動配置代理: 127.0.0.1:{self.proxy_port}"
                    )
        
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟外部瀏覽器失敗: {str(e)}")


class ProxyBrowser:
    """代理瀏覽器管理器"""
    
    def __init__(self, parent_notebook, proxy_port=9487):
        self.parent_notebook = parent_notebook
        self.proxy_port = proxy_port
        self.browser_frame = None
        self.browser = None
        
        self._create_browser_tab()
    
    def _create_browser_tab(self):
        """創建瀏覽器標籤頁"""
        self.browser_frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.browser_frame, text="🌐 內建瀏覽器")
        
        # 創建瀏覽器實例
        self.browser = SimpleBrowser(self.browser_frame, self.proxy_port)
    
    def navigate_to(self, url):
        """導航到指定URL"""
        if self.browser:
            self.browser.url_var.set(url)
            self.browser.navigate_to_url()
    
    def get_current_url(self):
        """獲取當前URL"""
        if self.browser:
            return self.browser.current_url
        return "" 