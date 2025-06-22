#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP代理GUI界面 - 類似Burp Suite的界面
提供請求攔截、查看、編輯和重放功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import json
from datetime import datetime
from proxy_interceptor import ProxyInterceptor, HTTPRequest
from request_replayer import ReplayResultWindow
from browser_widget import ProxyBrowser


class ProxyGUI:
    """代理GUI主界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HTTP代理攔截器 - 類似Burp Suite")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        # 代理攔截器實例
        self.proxy = ProxyInterceptor(port=9487)
        self.proxy.add_request_callback(self.on_new_request)
        
        # 當前選中的請求
        self.current_request = None
        
        # 代理服務器線程
        self.proxy_thread = None
        
        # 內建瀏覽器
        self.browser = None
        
        # 創建界面
        self._create_widgets()
        
        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _create_widgets(self):
        """創建界面組件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 工具欄
        self._create_toolbar(main_frame)
        
        # 主要內容區域 - 使用Notebook來管理不同功能標籤頁
        self.main_notebook = ttk.Notebook(main_frame)
        self.main_notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 代理攔截標籤頁
        proxy_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(proxy_frame, text="🔍 代理攔截")
        
        # 在代理攔截標籤頁中創建原有的分割面板
        paned_window = ttk.PanedWindow(proxy_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左側面板 - 請求列表
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=1)
        
        # 右側面板 - 請求詳情
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=2)
        
        # 創建請求列表
        self._create_request_list(left_frame)
        
        # 創建請求詳情
        self._create_request_details(right_frame)
        
        # 創建內建瀏覽器標籤頁
        self._create_browser_tab()
    
    def _create_toolbar(self, parent):
        """創建工具欄"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # 代理控制按鈕
        self.start_btn = ttk.Button(
            toolbar, 
            text="啟動代理 (9487)", 
            command=self.start_proxy,
            style="Accent.TButton"
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(
            toolbar, 
            text="停止代理", 
            command=self.stop_proxy,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 分隔線
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 清空按鈕
        ttk.Button(
            toolbar, 
            text="清空請求", 
            command=self.clear_requests
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # 導出按鈕
        ttk.Button(
            toolbar, 
            text="導出日誌", 
            command=self.export_logs
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # 分隔線
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 瀏覽器快速導航
        ttk.Button(
            toolbar, 
            text="🌐 瀏覽器", 
            command=self.switch_to_browser
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # 快速測試按鈕
        ttk.Button(
            toolbar, 
            text="🧪 快速測試", 
            command=self.quick_test
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # 狀態標籤
        self.status_label = ttk.Label(toolbar, text="代理已停止", foreground="red")
        self.status_label.pack(side=tk.RIGHT, padx=(5, 0))
    
    def _create_request_list(self, parent):
        """創建請求列表"""
        list_frame = ttk.LabelFrame(parent, text="攔截的請求")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 創建Treeview
        columns = ("時間", "方法", "主機", "路徑", "狀態")
        self.request_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings")
        
        # 設置列寬
        self.request_tree.column("#0", width=50, minwidth=50)
        self.request_tree.column("時間", width=120, minwidth=120)
        self.request_tree.column("方法", width=60, minwidth=60)
        self.request_tree.column("主機", width=150, minwidth=100)
        self.request_tree.column("路徑", width=200, minwidth=150)
        self.request_tree.column("狀態", width=80, minwidth=80)
        
        # 設置列標題
        self.request_tree.heading("#0", text="ID")
        self.request_tree.heading("時間", text="時間")
        self.request_tree.heading("方法", text="方法")
        self.request_tree.heading("主機", text="主機")
        self.request_tree.heading("路徑", text="路徑")
        self.request_tree.heading("狀態", text="狀態")
        
        # 滾動條
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.request_tree.yview)
        self.request_tree.configure(yscrollcommand=tree_scroll.set)
        
        # 打包
        self.request_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 綁定選擇事件
        self.request_tree.bind("<<TreeviewSelect>>", self.on_request_select)
    
    def _create_request_details(self, parent):
        """創建請求詳情面板"""
        details_frame = ttk.LabelFrame(parent, text="請求詳情")
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # 創建Notebook（標籤頁）
        notebook = ttk.Notebook(details_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 原始請求標籤頁
        raw_frame = ttk.Frame(notebook)
        notebook.add(raw_frame, text="原始請求")
        
        self.raw_text = scrolledtext.ScrolledText(
            raw_frame, 
            wrap=tk.WORD, 
            height=20,
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="#ffffff"
        )
        self.raw_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 格式化請求標籤頁
        formatted_frame = ttk.Frame(notebook)
        notebook.add(formatted_frame, text="格式化請求")
        
        # 基本信息框架
        info_frame = ttk.LabelFrame(formatted_frame, text="基本信息")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 創建信息標籤
        self.info_labels = {}
        info_fields = [
            ("時間", "timestamp"),
            ("客戶端", "client"),
            ("方法", "method"),
            ("URL", "url"),
            ("主機", "host"),
            ("路徑", "path")
        ]
        
        for i, (label_text, field_name) in enumerate(info_fields):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(info_frame, text=f"{label_text}:").grid(
                row=row, column=col, sticky=tk.W, padx=5, pady=2
            )
            
            label = ttk.Label(info_frame, text="", foreground="blue")
            label.grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=2)
            self.info_labels[field_name] = label
        
        # Headers框架
        headers_frame = ttk.LabelFrame(formatted_frame, text="請求頭")
        headers_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.headers_text = scrolledtext.ScrolledText(
            headers_frame, 
            wrap=tk.NONE, 
            height=8,
            bg="#f8f8f8"
        )
        self.headers_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Body框架
        body_frame = ttk.LabelFrame(formatted_frame, text="請求體")
        body_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.body_text = scrolledtext.ScrolledText(
            body_frame, 
            wrap=tk.WORD, 
            height=8,
            bg="#f8f8f8"
        )
        self.body_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 編輯和重放標籤頁
        edit_frame = ttk.Frame(notebook)
        notebook.add(edit_frame, text="編輯與重放")
        
        # 編輯區域
        edit_label = ttk.Label(edit_frame, text="編輯請求內容（修改後可重放）:")
        edit_label.pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        self.edit_text = scrolledtext.ScrolledText(
            edit_frame, 
            wrap=tk.WORD, 
            height=20,
            bg="#f0f0f0"
        )
        self.edit_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 按鈕框架
        button_frame = ttk.Frame(edit_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            button_frame, 
            text="重放請求", 
            command=self.replay_request
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame, 
            text="重置編輯", 
            command=self.reset_edit
        ).pack(side=tk.LEFT)
    
    def _create_browser_tab(self):
        """創建內建瀏覽器標籤頁"""
        try:
            # 創建瀏覽器實例
            self.browser = ProxyBrowser(self.main_notebook, proxy_port=9487)
        except Exception as e:
            print(f"創建瀏覽器標籤頁時出錯: {e}")
            # 如果創建失敗，添加一個錯誤提示標籤頁
            error_frame = ttk.Frame(self.main_notebook)
            self.main_notebook.add(error_frame, text="❌ 瀏覽器")
            
            error_label = ttk.Label(
                error_frame, 
                text=f"內建瀏覽器載入失敗:\n{str(e)}\n\n請使用外部瀏覽器並配置代理：127.0.0.1:9487",
                justify=tk.CENTER
            )
            error_label.pack(expand=True)
    
    def start_proxy(self):
        """啟動代理服務器"""
        try:
            self.proxy_thread = threading.Thread(target=self.proxy.start, daemon=True)
            self.proxy_thread.start()
            
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="代理運行中 - 端口 9487", foreground="green")
            
            messagebox.showinfo("成功", "代理服務器已啟動!\n監聽端口: 9487")
        
        except Exception as e:
            messagebox.showerror("錯誤", f"啟動代理服務器失敗:\n{str(e)}")
    
    def stop_proxy(self):
        """停止代理服務器"""
        try:
            self.proxy.stop()
            
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="代理已停止", foreground="red")
            
            messagebox.showinfo("成功", "代理服務器已停止!")
        
        except Exception as e:
            messagebox.showerror("錯誤", f"停止代理服務器失敗:\n{str(e)}")
    
    def on_new_request(self, request):
        """處理新請求回調"""
        def update_ui():
            # 添加到請求列表
            request_id = len(self.proxy.get_requests())
            time_str = request.timestamp.strftime('%H:%M:%S')
            
            self.request_tree.insert(
                "", "end",
                text=str(request_id),
                values=(
                    time_str,
                    request.method,
                    f"{request.host}:{request.port}",
                    request.path[:50] + "..." if len(request.path) > 50 else request.path,
                    "已攔截"
                )
            )
            
            # 自動滾動到底部
            items = self.request_tree.get_children()
            if items:
                self.request_tree.see(items[-1])
        
        # 在主線程中更新UI
        self.root.after(0, update_ui)
    
    def on_request_select(self, event):
        """處理請求選擇事件"""
        selection = self.request_tree.selection()
        if not selection:
            return
        
        try:
            # 獲取選中項目的ID
            item = self.request_tree.item(selection[0])
            request_id = int(item['text']) - 1  # 轉換為0基索引
            
            # 獲取對應的請求
            requests = self.proxy.get_requests()
            if 0 <= request_id < len(requests):
                self.current_request = requests[request_id]
                self.display_request_details(self.current_request)
        
        except (ValueError, IndexError) as e:
            print(f"選擇請求時出錯: {e}")
    
    def display_request_details(self, request):
        """顯示請求詳情"""
        # 顯示原始請求
        self.raw_text.delete(1.0, tk.END)
        self.raw_text.insert(1.0, request.raw_data.decode('utf-8', errors='ignore'))
        
        # 顯示基本信息
        self.info_labels['timestamp'].config(text=request.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
        self.info_labels['client'].config(text=f"{request.client_addr[0]}:{request.client_addr[1]}")
        self.info_labels['method'].config(text=request.method)
        self.info_labels['url'].config(text=request.url)
        self.info_labels['host'].config(text=f"{request.host}:{request.port}")
        self.info_labels['path'].config(text=request.path)
        
        # 顯示Headers
        self.headers_text.delete(1.0, tk.END)
        headers_str = '\n'.join([f"{k}: {v}" for k, v in request.headers.items()])
        self.headers_text.insert(1.0, headers_str)
        
        # 顯示Body
        self.body_text.delete(1.0, tk.END)
        self.body_text.insert(1.0, request.body)
        
        # 在編輯區域顯示原始請求
        self.edit_text.delete(1.0, tk.END)
        self.edit_text.insert(1.0, request.raw_data.decode('utf-8', errors='ignore'))
    
    def clear_requests(self):
        """清空請求列表"""
        if messagebox.askyesno("確認", "確定要清空所有請求嗎？"):
            self.proxy.clear_requests()
            self.request_tree.delete(*self.request_tree.get_children())
            self.current_request = None
            
            # 清空詳情面板
            self.raw_text.delete(1.0, tk.END)
            self.headers_text.delete(1.0, tk.END)
            self.body_text.delete(1.0, tk.END)
            self.edit_text.delete(1.0, tk.END)
            
            for label in self.info_labels.values():
                label.config(text="")
    
    def export_logs(self):
        """導出日誌"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
                title="保存日誌文件"
            )
            
            if filename:
                requests = self.proxy.get_requests()
                
                if filename.endswith('.json'):
                    # 導出為JSON格式
                    export_data = []
                    for i, req in enumerate(requests):
                        export_data.append({
                            'id': i + 1,
                            'timestamp': req.timestamp.isoformat(),
                            'client_addr': f"{req.client_addr[0]}:{req.client_addr[1]}",
                            'method': req.method,
                            'url': req.url,
                            'host': req.host,
                            'port': req.port,
                            'path': req.path,
                            'headers': req.headers,
                            'body': req.body,
                            'raw_data': req.raw_data.decode('utf-8', errors='ignore')
                        })
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, ensure_ascii=False, indent=2)
                else:
                    # 導出為文本格式
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write("HTTP代理攔截日誌\n")
                        f.write("=" * 50 + "\n\n")
                        
                        for i, req in enumerate(requests):
                            f.write(f"請求 #{i + 1}\n")
                            f.write("-" * 30 + "\n")
                            f.write(req.to_string())
                            f.write("\n" + "=" * 50 + "\n\n")
                
                messagebox.showinfo("成功", f"日誌已導出到: {filename}")
        
        except Exception as e:
            messagebox.showerror("錯誤", f"導出日誌失敗:\n{str(e)}")
    
    def replay_request(self):
        """重放請求"""
        try:
            if not self.current_request:
                messagebox.showwarning("警告", "請先選擇一個請求")
                return
            
            # 獲取編輯後的請求內容
            edited_request = self.edit_text.get(1.0, tk.END).strip()
            if not edited_request:
                messagebox.showwarning("警告", "請求內容不能為空")
                return
            
            # 打開重放結果窗口
            ReplayResultWindow(self.root, edited_request)
        
        except Exception as e:
            messagebox.showerror("錯誤", f"重放請求失敗:\n{str(e)}")
    
    def reset_edit(self):
        """重置編輯內容"""
        if self.current_request:
            self.edit_text.delete(1.0, tk.END)
            self.edit_text.insert(1.0, self.current_request.raw_data.decode('utf-8', errors='ignore'))
    
    def on_closing(self):
        """處理窗口關閉事件"""
        if self.proxy.running:
            if messagebox.askyesno("確認退出", "代理服務器仍在運行，確定要退出嗎？"):
                self.proxy.stop()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def switch_to_browser(self):
        """切換到瀏覽器標籤頁"""
        try:
            # 查找瀏覽器標籤頁
            for i in range(self.main_notebook.index("end")):
                tab_text = self.main_notebook.tab(i, "text")
                if "瀏覽器" in tab_text:
                    self.main_notebook.select(i)
                    return
        except Exception as e:
            print(f"切換到瀏覽器標籤頁時出錯: {e}")
    
    def quick_test(self):
        """快速測試功能"""
        if not self.proxy.running:
            messagebox.showwarning("警告", "請先啟動代理服務器")
            return
        
        # 提供快速測試選項
        test_urls = [
            ("HTTP測試工具", "http://httpbin.org"),
            ("簡單測試頁面", "http://example.com"),
            ("JSON API測試", "http://httpbin.org/json"),
            ("獲取IP信息", "http://httpbin.org/ip"),
            ("User-Agent測試", "http://httpbin.org/user-agent")
        ]
        
        # 創建選擇對話框
        test_window = tk.Toplevel(self.root)
        test_window.title("快速測試")
        test_window.geometry("400x300")
        test_window.transient(self.root)
        test_window.grab_set()
        
        ttk.Label(test_window, text="選擇測試網站:", font=("Arial", 12, "bold")).pack(pady=10)
        
        # 創建測試按鈕
        for name, url in test_urls:
            btn_frame = ttk.Frame(test_window)
            btn_frame.pack(fill=tk.X, padx=20, pady=5)
            
            ttk.Button(
                btn_frame,
                text=f"{name}",
                command=lambda u=url: self._test_url(u, test_window)
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            ttk.Label(btn_frame, text=url, foreground="gray").pack(side=tk.RIGHT)
        
        # 自定義URL測試
        custom_frame = ttk.LabelFrame(test_window, text="自定義URL測試")
        custom_frame.pack(fill=tk.X, padx=20, pady=10)
        
        url_var = tk.StringVar()
        url_entry = ttk.Entry(custom_frame, textvariable=url_var)
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        ttk.Button(
            custom_frame,
            text="測試",
            command=lambda: self._test_url(url_var.get(), test_window)
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        
        ttk.Button(test_window, text="關閉", command=test_window.destroy).pack(pady=10)
    
    def _test_url(self, url, window):
        """測試指定URL"""
        if not url.strip():
            messagebox.showwarning("警告", "請輸入有效的URL")
            return
        
        try:
            # 關閉測試窗口
            window.destroy()
            
            # 切換到瀏覽器並導航
            self.switch_to_browser()
            
            if self.browser and self.browser.browser:
                self.browser.navigate_to(url)
            else:
                messagebox.showinfo("測試", f"將測試URL: {url}\n請手動在瀏覽器中訪問")
        
        except Exception as e:
            messagebox.showerror("錯誤", f"測試失敗: {str(e)}")
    
    def run(self):
        """運行GUI"""
        # 設置主題
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定義樣式
        style.configure('Accent.TButton', foreground='white', background='#0078d4')
        
        self.root.mainloop()


if __name__ == "__main__":
    app = ProxyGUI()
    app.run() 