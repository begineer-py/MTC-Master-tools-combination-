#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import threading
import importlib.util
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

class StdoutRedirector:
    """重定向標準輸出到Text控件"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        
    def write(self, string):
        self.buffer += string
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        
    def flush(self):
        self.text_widget.insert(tk.END, self.buffer)
        self.text_widget.see(tk.END)
        self.buffer = ""

def load_db_manager():
    """動態加載數據庫管理模塊"""
    db_manager_path = os.path.join(project_root, 'instance', 'tools', 'db_manager.py')
    
    # 如果文件不存在，返回None
    if not os.path.exists(db_manager_path):
        return None
        
    # 動態加載模塊
    spec = importlib.util.spec_from_file_location("db_manager", db_manager_path)
    db_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_manager)
    
    return db_manager

class DbManagerGUI:
    """數據庫管理GUI"""
    def __init__(self, root):
        self.root = root
        self.root.title("C2 數據庫管理工具")
        self.root.geometry("700x500")
        self.root.minsize(600, 400)
        
        # 嘗試加載數據庫管理模塊
        self.db_manager = load_db_manager()
        if not self.db_manager:
            messagebox.showerror("錯誤", "無法加載數據庫管理模塊！")
            self.root.destroy()
            return
        
        # 數據庫路徑
        self.db_path = os.path.join(project_root, 'instance', 'c2.db')
        
        # 創建UI
        self._setup_ui()
    
    def _setup_ui(self):
        """設置界面"""
        # 頂部的工具欄
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 數據庫路徑顯示
        ttk.Label(toolbar_frame, text="數據庫路徑:").pack(side=tk.LEFT, padx=5)
        ttk.Label(toolbar_frame, text=self.db_path).pack(side=tk.LEFT, padx=5)
        
        # 按鈕框架
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 解鎖按鈕
        ttk.Button(btn_frame, text="解鎖數據庫", command=self._unlock_db).pack(side=tk.LEFT, padx=5)
        
        # 檢查按鈕
        ttk.Button(btn_frame, text="檢查完整性", command=self._check_db).pack(side=tk.LEFT, padx=5)
        
        # 優化按鈕
        ttk.Button(btn_frame, text="優化數據庫", command=self._optimize_db).pack(side=tk.LEFT, padx=5)
        
        # 修復按鈕
        ttk.Button(btn_frame, text="修復數據庫", command=self._repair_db).pack(side=tk.LEFT, padx=5)
        
        # 備份按鈕
        ttk.Button(btn_frame, text="備份數據庫", command=self._backup_db).pack(side=tk.LEFT, padx=5)
        
        # 清空日誌按鈕
        ttk.Button(btn_frame, text="清空日誌", command=self._clear_log).pack(side=tk.RIGHT, padx=5)
        
        # 狀態欄
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="就緒")
        self.status_label.pack(side=tk.LEFT)
        
        # 日誌區域
        log_frame = ttk.LabelFrame(self.root, text="操作日誌")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 重定向標準輸出到日誌區域
        self.stdout_redirector = StdoutRedirector(self.log_text)
    
    def _update_status(self, text):
        """更新狀態欄"""
        self.status_label.config(text=text)
    
    def _clear_log(self):
        """清空日誌"""
        self.log_text.delete(1.0, tk.END)
    
    def _run_in_thread(self, func, status_text):
        """在線程中運行函數，避免UI阻塞"""
        def wrapper():
            try:
                # 重定向標準輸出
                old_stdout = sys.stdout
                sys.stdout = self.stdout_redirector
                
                # 更新狀態
                self._update_status(f"正在{status_text}...")
                
                # 執行函數
                result = func()
                
                # 恢復標準輸出
                sys.stdout = old_stdout
                
                # 更新狀態
                if result:
                    self._update_status(f"{status_text}完成")
                else:
                    self._update_status(f"{status_text}失敗")
                    
            except Exception as e:
                # 恢復標準輸出
                sys.stdout = old_stdout
                
                # 顯示錯誤
                error_msg = f"{status_text}時出錯: {str(e)}"
                self.log_text.insert(tk.END, f"\n錯誤: {error_msg}\n")
                self._update_status(error_msg)
        
        # 建立並啟動線程
        thread = threading.Thread(target=wrapper)
        thread.daemon = True
        thread.start()
    
    def _unlock_db(self):
        """解鎖數據庫"""
        self._run_in_thread(
            lambda: self.db_manager.unlock_database(self.db_path),
            "解鎖數據庫"
        )
    
    def _check_db(self):
        """檢查數據庫完整性"""
        self._run_in_thread(
            lambda: self.db_manager.check_database(self.db_path),
            "檢查數據庫完整性"
        )
    
    def _optimize_db(self):
        """優化數據庫"""
        self._run_in_thread(
            lambda: self.db_manager.optimize_database(self.db_path),
            "優化數據庫"
        )
    
    def _repair_db(self):
        """修復數據庫"""
        self._run_in_thread(
            lambda: self.db_manager.repair_database(self.db_path),
            "修復數據庫"
        )
    
    def _backup_db(self):
        """備份數據庫"""
        self._run_in_thread(
            lambda: self.db_manager.backup_database(self.db_path),
            "備份數據庫"
        )

def main():
    # 確保必要的目錄存在
    os.makedirs(os.path.join(project_root, "instance"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "instance/backups"), exist_ok=True)
    
    # 創建Tkinter根窗口
    root = tk.Tk()
    
    # 設置主題
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    
    # 創建GUI應用
    app = DbManagerGUI(root)
    
    # 啟動主循環
    root.mainloop()

if __name__ == "__main__":
    main() 