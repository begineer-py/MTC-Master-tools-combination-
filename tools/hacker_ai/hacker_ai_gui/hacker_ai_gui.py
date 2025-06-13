#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import datetime
import sys
import os

# 添加父目錄到路徑以便導入模型載入器
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hacker_AI_loader.load_models import ModelLoader

class HackerAIGUI:
    def __init__(self):
        """初始化GUI界面"""
        self.root = tk.Tk()
        self.root.title("🤖 HackerAI 問答系統")
        self.root.geometry("900x700")
        
        # 初始化模型載入器
        self.model_loader = ModelLoader()
        
        # 設置樣式
        self.setup_styles()
        
        # 創建界面元素
        self.create_widgets()
        
        # 初始化對話歷史
        self.conversation_history = []
        
        # 歡迎訊息
        self.add_message("系統", "歡迎使用 HackerAI 問答系統！🚀\n您可以詢問關於網路安全、滲透測試、編程等問題。\n點擊「載入模型」按鈕來啟用AI功能。")

    def setup_styles(self):
        """設置界面樣式"""
        self.root.configure(bg='#2b2b2b')
        
        # 創建樣式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 自定義樣式
        self.style.configure('Title.TLabel',
                           font=('Arial', 16, 'bold'),
                           background='#2b2b2b',
                           foreground='#00ff00')
        
        self.style.configure('Chat.TFrame',
                           background='#2b2b2b')
        
        self.style.configure('Send.TButton',
                           font=('Arial', 10, 'bold'),
                           background='#00ff00',
                           foreground='#000000')
        
        self.style.configure('Load.TButton',
                           font=('Arial', 9, 'bold'),
                           background='#ff6b6b',
                           foreground='#ffffff')

    def create_widgets(self):
        """創建界面組件"""
        # 主框架
        main_frame = ttk.Frame(self.root, style='Chat.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 標題
        title_label = ttk.Label(main_frame,
                               text="🤖 HackerAI 問答系統",
                               style='Title.TLabel')
        title_label.pack(pady=(0, 10))
        
        # 模型狀態框架
        status_frame = ttk.Frame(main_frame, style='Chat.TFrame')
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 模型狀態標籤
        self.model_status_label = ttk.Label(
            status_frame,
            text="模型狀態: 未載入",
            foreground='#ff6b6b',
            background='#2b2b2b',
            font=('Arial', 10, 'bold')
        )
        self.model_status_label.pack(side=tk.LEFT)
        
        # 對話顯示區域
        self.chat_display = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=90,
            height=28,
            font=('Consolas', 11),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='#00ff00',
            selectbackground='#404040'
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 輸入區域框架
        input_frame = ttk.Frame(main_frame, style='Chat.TFrame')
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 問題輸入框
        self.question_entry = tk.Text(
            input_frame,
            height=3,
            font=('Arial', 11),
            bg='#404040',
            fg='#ffffff',
            insertbackground='#00ff00',
            wrap=tk.WORD
        )
        self.question_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 發送按鈕
        self.send_button = ttk.Button(
            input_frame,
            text="發送 ➤",
            command=self.send_question,
            style='Send.TButton'
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # 綁定Enter鍵
        self.question_entry.bind('<Control-Return>', lambda e: self.send_question())
        
        # 底部按鈕框架
        button_frame = ttk.Frame(main_frame, style='Chat.TFrame')
        button_frame.pack(fill=tk.X)
        
        # 載入模型按鈕
        self.load_model_button = ttk.Button(
            button_frame,
            text="載入訓練模型",
            command=self.load_trained_model,
            style='Load.TButton'
        )
        self.load_model_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 載入Qwen模型按鈕
        self.load_pretrained_button = ttk.Button(
            button_frame,
            text="載入Qwen模型",
            command=self.load_pretrained_model
        )
        self.load_pretrained_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 卸載模型按鈕
        self.unload_button = ttk.Button(
            button_frame,
            text="卸載模型",
            command=self.unload_model
        )
        self.unload_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清除對話按鈕
        clear_button = ttk.Button(
            button_frame,
            text="清除對話",
            command=self.clear_chat
        )
        clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存對話按鈕
        save_button = ttk.Button(
            button_frame,
            text="保存對話",
            command=self.save_conversation
        )
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 狀態標籤
        self.status_label = ttk.Label(
            button_frame,
            text="狀態: 就緒",
            foreground='#00ff00',
            background='#2b2b2b'
        )
        self.status_label.pack(side=tk.RIGHT)

    def add_message(self, sender, message):
        """添加訊息到對話顯示區"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        self.chat_display.config(state=tk.NORMAL)
        
        # 根據發送者設置顏色
        if sender == "您":
            self.chat_display.insert(tk.END, f"[{timestamp}] 🧑‍💻 {sender}: ", "user_tag")
        elif sender == "HackerAI":
            self.chat_display.insert(tk.END, f"[{timestamp}] 🤖 {sender}: ", "ai_tag")
        else:
            self.chat_display.insert(tk.END, f"[{timestamp}] ⚙️ {sender}: ", "system_tag")
        
        self.chat_display.insert(tk.END, f"{message}\n\n")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
        # 配置標籤樣式
        self.chat_display.tag_configure("user_tag", foreground="#00ff00", font=('Consolas', 11, 'bold'))
        self.chat_display.tag_configure("ai_tag", foreground="#ff6b6b", font=('Consolas', 11, 'bold'))
        self.chat_display.tag_configure("system_tag", foreground="#ffd93d", font=('Consolas', 11, 'bold'))

    def send_question(self):
        """處理用戶問題"""
        question = self.question_entry.get("1.0", tk.END).strip()
        
        if not question:
            messagebox.showwarning("警告", "請輸入問題！")
            return
        
        # 添加用戶問題到對話
        self.add_message("您", question)
        
        # 清空輸入框
        self.question_entry.delete("1.0", tk.END)
        
        # 更新狀態
        self.status_label.config(text="狀態: 處理中...")
        self.send_button.config(state=tk.DISABLED)
        
        # 在新線程中處理問題
        thread = threading.Thread(target=self.process_question, args=(question,))
        thread.daemon = True
        thread.start()

    def process_question(self, question):
        """處理問題並生成回答"""
        try:
            # 使用模型載入器生成回答
            answer = self.model_loader.generate_answer(question)
            
            # 在主線程中更新UI
            self.root.after(0, lambda: self.display_answer(answer))
            
        except Exception as e:
            error_msg = f"處理問題時發生錯誤: {str(e)}"
            self.root.after(0, lambda: self.display_answer(error_msg))

    def display_answer(self, answer):
        """顯示AI回答"""
        self.add_message("HackerAI", answer)
        
        # 恢復按鈕狀態
        self.send_button.config(state=tk.NORMAL)
        self.status_label.config(text="狀態: 就緒")
        
        # 聚焦輸入框
        self.question_entry.focus()

    def load_trained_model(self):
        """載入訓練好的模型"""
        self.status_label.config(text="狀態: 載入訓練模型中...")
        self.load_model_button.config(state=tk.DISABLED)
        
        def load_process():
            success, message = self.model_loader.load_trained_model()
            self.root.after(0, lambda: self.model_load_complete(success, message, "trained"))
        
        thread = threading.Thread(target=load_process)
        thread.daemon = True
        thread.start()

    def load_pretrained_model(self):
        """載入Qwen模型"""
        self.status_label.config(text="狀態: 載入Qwen模型中...")
        self.load_pretrained_button.config(state=tk.DISABLED)
        
        def load_process():
            success, message = self.model_loader.load_pretrained_model()
            self.root.after(0, lambda: self.model_load_complete(success, message, "qwen"))
        
        thread = threading.Thread(target=load_process)
        thread.daemon = True
        thread.start()

    def model_load_complete(self, success, message, model_type):
        """模型載入完成"""
        if success:
            self.model_status_label.config(
                text=f"模型狀態: {self.model_loader.get_model_status()}",
                foreground='#00ff00'
            )
            self.status_label.config(text="狀態: 模型已載入")
            self.add_message("系統", f"✅ {message}")
        else:
            self.model_status_label.config(
                text="模型狀態: 載入失敗",
                foreground='#ff6b6b'
            )
            self.status_label.config(text="狀態: 載入失敗")
            self.add_message("系統", f"❌ {message}")
        
        # 重新啟用按鈕
        self.load_model_button.config(state=tk.NORMAL)
        self.load_pretrained_button.config(state=tk.NORMAL)

    def unload_model(self):
        """卸載模型"""
        if self.model_loader.is_loaded:
            message = self.model_loader.unload_model()
            self.model_status_label.config(
                text="模型狀態: 未載入",
                foreground='#ff6b6b'
            )
            self.add_message("系統", f"🔄 {message}")
        else:
            self.add_message("系統", "沒有載入的模型需要卸載。")

    def clear_chat(self):
        """清除對話記錄"""
        if messagebox.askyesno("確認", "確定要清除所有對話記錄嗎？"):
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.conversation_history.clear()
            self.add_message("系統", "對話記錄已清除。")

    def save_conversation(self):
        """保存對話記錄"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.txt"
            
            content = self.chat_display.get(1.0, tk.END)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.add_message("系統", f"對話記錄已保存到: {filename}")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"保存失敗: {str(e)}")

    def run(self):
        """運行GUI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()

if __name__ == "__main__":
    print("🤖 啟動 HackerAI GUI...")
    app = HackerAIGUI()
    app.run()
