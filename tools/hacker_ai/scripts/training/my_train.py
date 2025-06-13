#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os  # 作業系統相關功能，如檔案路徑操作
import sys  # Python系統相關功能，如程式退出
import json  # 處理JSON格式的配置檔案
import logging  # 記錄程式運行日誌
from pathlib import Path  # 更現代的檔案路徑處理方式
import torch  # PyTorch深度學習框架
import shutil  # 檔案和目錄操作工具
import glob  # 檔案路徑模式匹配工具
from torch.utils.data import Dataset, DataLoader  # PyTorch的資料載入工具
from transformers import (  # Hugging Face的預訓練模型庫
    AutoTokenizer,  # 自動選擇合適的文字分詞器
    AutoModelForCausalLM,  # 自動選擇合適的語言生成模型
    TrainingArguments,  # 訓練參數配置類
    Trainer,  # 模型訓練器
    DataCollatorForLanguageModeling  # 語言模型的資料整理器
)

class HackerAITrainer:  # 定義HackerAI訓練器類別
    def __init__(self):  # 初始化方法，建立訓練器實例時自動執行
        """初始化訓練器，從零開始訓練"""
        self._setup_logging()  # 設定日誌記錄系統
        self.logger = logging.getLogger(__name__)  # 建立日誌記錄器
        self.logger.info("初始化 HackerAI 從零訓練器...")  # 記錄初始化開始

        self.config = self._load_config()  # 載入配置檔案
        self._load_parameters()  # 載入訓練參數
        self._check_dependencies()  # 檢查必要的軟體依賴
        self._ensure_output_dir()  # 確保輸出目錄存在
        
        self.logger.info("HackerAI 訓練器初始化完成.")  # 記錄初始化完成

    def _setup_logging(self):  # 設定日誌記錄系統
        """配置日誌記錄器"""
        log_dir = Path("./logs")  # 建立日誌目錄路徑
        log_dir.mkdir(exist_ok=True)  # 建立日誌目錄（如果不存在）
        log_file = log_dir / "hacker_ai_train.log"  # 設定日誌檔案路徑

        logging.basicConfig(  # 配置日誌記錄的基本設定
            level=logging.INFO,  # 設定日誌等級為INFO
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 設定日誌格式
            handlers=[  # 設定日誌輸出處理器
                logging.FileHandler(log_file, encoding='utf-8'),  # 輸出到檔案
                logging.StreamHandler(sys.stdout)  # 輸出到控制台
            ]
        )

    def _load_config(self):  # 載入配置檔案
        """從配置文件加載訓練參數"""
        config_path = Path("configs/training_config.json")  # 配置檔案路徑
        try:
            with open(config_path, 'r', encoding='utf-8') as f:  # 開啟配置檔案
                config = json.load(f)  # 解析JSON格式的配置
            self.logger.info(f"已成功加載配置文件: {config_path}")  # 記錄載入成功
            return config  # 回傳配置內容
        except FileNotFoundError:  # 如果檔案不存在
            self.logger.warning(f"配置文件未找到: {config_path}，使用默認參數")  # 記錄警告
            return {}  # 回傳空字典，使用預設參數
        except json.JSONDecodeError as e:  # 如果JSON格式錯誤
            self.logger.error(f"解析配置文件失敗: {e}，使用默認參數")  # 記錄錯誤
            return {}  # 回傳空字典，使用預設參數

    def _get_param(self, param_path, default_value=None):  # 從配置中取得參數
        """從配置中獲取參數"""
        parts = param_path.split('.')  # 將參數路徑分割成部分（如"model.base_model"分割成["model", "base_model"]）
        value = self.config  # 從配置開始
        try:
            for part in parts:  # 逐層深入配置結構
                value = value[part]  # 取得下一層的值
            return value  # 回傳找到的參數值
        except (KeyError, TypeError):  # 如果參數不存在或類型錯誤
            return default_value  # 回傳預設值

    def _load_parameters(self):  # 載入所有訓練參數
        """加載訓練參數"""
        self.logger.info("加載訓練參數...")  # 記錄開始載入參數
        
        # 基礎模型配置
        self.model_name = self._get_param("model.base_model", "gpt2")  # 使用的基礎模型名稱，預設為GPT-2
        self.vocab_size = self._get_param("model.vocab_size", 50257)  # 詞彙表大小
        self.max_length = self._get_param("model.max_length", 512)  # 最大文字長度
        
        # 訓練數據
        self.data_path = self._get_param("data.path", "./datasets/hacker_data.txt")  # 訓練資料檔案路徑
        
        # 訓練參數
        self.output_dir = self._get_param("training.output_dir", "./models/hacker_ai_from_scratch")  # 模型輸出目錄
        self.batch_size = self._get_param("training.batch_size", 4)  # 批次大小（一次處理多少個樣本）
        self.epochs = self._get_param("training.epochs", 3)  # 訓練輪數（整個資料集要訓練幾遍）
        self.learning_rate = self._get_param("training.learning_rate", 5e-5)  # 學習率（模型學習的速度）
        self.warmup_steps = self._get_param("training.warmup_steps", 100)  # 暖身步數（逐漸增加學習率的步數）
        self.save_steps = self._get_param("training.save_steps", 500)  # 每多少步保存一次模型
        self.auto_cleanup_checkpoints = self._get_param("training.auto_cleanup_checkpoints", True)  # 是否自動清理檢查點
        self.keep_best_checkpoint = self._get_param("training.keep_best_checkpoint", False)  # 是否保留最佳檢查點
        
        self.logger.info("訓練參數加載完成:")  # 記錄參數載入完成
        self.logger.info(f"  基礎模型: {self.model_name}")  # 顯示使用的基礎模型
        self.logger.info(f"  數據路徑: {self.data_path}")  # 顯示資料路徑
        self.logger.info(f"  輸出目錄: {self.output_dir}")  # 顯示輸出目錄

    def _check_dependencies(self):  # 檢查軟體依賴
        """檢查依賴"""
        self.logger.info("檢查依賴...")  # 記錄開始檢查依賴
        try:
            import transformers  # 嘗試匯入transformers庫
            self.logger.info(f"  torch version: {torch.__version__}")  # 顯示PyTorch版本
            self.logger.info(f"  transformers version: {transformers.__version__}")  # 顯示Transformers版本
            
            if torch.cuda.is_available():  # 檢查是否有GPU可用
                self.logger.info(f"  CUDA可用: {torch.cuda.get_device_name(0)}")  # 顯示GPU名稱
            else:
                self.logger.warning("  CUDA不可用，將使用CPU訓練")  # 警告只能使用CPU訓練
            
            return True  # 依賴檢查通過
        except ImportError as e:  # 如果缺少必要的庫
            self.logger.error(f"缺少關鍵依賴: {e}")  # 記錄錯誤
            return False  # 依賴檢查失敗

    def _ensure_output_dir(self):  # 確保輸出目錄存在
        """確保輸出目錄存在"""
        output_path = Path(self.output_dir)  # 建立輸出路徑物件
        output_path.mkdir(parents=True, exist_ok=True)  # 建立目錄（包括父目錄，如果已存在則不報錯）
        self.logger.info(f"輸出目錄: {self.output_dir}")  # 記錄輸出目錄

    def _load_data(self):  # 載入訓練資料
        """加載訓練數據"""
        self.logger.info("加載訓練數據...")  # 記錄開始載入資料
        data_path = Path(self.data_path)  # 建立資料路徑物件
        
        if not data_path.exists():  # 如果資料檔案不存在
            self.logger.error(f"數據文件不存在: {self.data_path}")  # 記錄錯誤
            sys.exit(1)  # 退出程式
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:  # 開啟資料檔案
                text_data = f.read()  # 讀取所有文字內容
            
            self.logger.info(f"成功加載數據，字符數: {len(text_data)}")  # 記錄載入成功和字符數
            return text_data  # 回傳文字資料
        except Exception as e:  # 如果載入失敗
            self.logger.error(f"加載數據失敗: {e}")  # 記錄錯誤
            sys.exit(1)  # 退出程式

    def _prepare_model_and_tokenizer(self):  # 準備模型和分詞器
        """準備模型和分詞器"""
        self.logger.info("初始化模型和分詞器...")  # 記錄開始初始化
        
        try:
            # 加載分詞器（將文字轉換成數字的工具）
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)  # 載入預訓練的分詞器
            if self.tokenizer.pad_token is None:  # 如果沒有填充符號
                self.tokenizer.pad_token = self.tokenizer.eos_token  # 使用結束符號作為填充符號
            
            # 加載模型配置並創建新模型
            self.model = AutoModelForCausalLM.from_pretrained(  # 載入預訓練的語言生成模型
                self.model_name,  # 模型名稱
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32  # 根據是否有GPU選擇數據類型
            )
            
            self.logger.info("模型和分詞器初始化完成")  # 記錄初始化完成
            return True  # 初始化成功
        except Exception as e:  # 如果初始化失敗
            self.logger.error(f"初始化模型失敗: {e}")  # 記錄錯誤
            return False  # 初始化失敗

    def _create_dataset(self, text_data):  # 建立訓練資料集
        """創建訓練數據集"""
        self.logger.info("創建訓練數據集...")  # 記錄開始建立資料集
        
        # 將文本分割成塊（因為模型有最大長度限制）
        chunks = []  # 儲存文字塊的列表
        chunk_size = self.max_length - 2  # 每塊的大小（留空間給特殊符號）
        
        for i in range(0, len(text_data), chunk_size):  # 按塊大小分割文字
            chunk = text_data[i:i + chunk_size]  # 取得一塊文字
            if len(chunk.strip()) > 0:  # 如果這塊文字不是空的
                chunks.append(chunk)  # 加入到列表中
        
        self.logger.info(f"創建了 {len(chunks)} 個訓練樣本")  # 記錄建立的樣本數量
        return HackerDataset(chunks, self.tokenizer, self.max_length)  # 回傳資料集物件

    def _cleanup_checkpoints(self):  # 清理訓練檢查點
        """清理訓練檢查點"""
        if not self.auto_cleanup_checkpoints:  # 如果沒有啟用自動清理
            self.logger.info("跳過檢查點清理（已禁用）")  # 記錄跳過清理
            return
        
        self.logger.info("開始清理訓練檢查點...")  # 記錄開始清理
        
        # 查找所有檢查點目錄（訓練過程中保存的中間狀態）
        checkpoint_pattern = os.path.join(self.output_dir, "checkpoint-*")  # 檢查點目錄的模式
        checkpoint_dirs = glob.glob(checkpoint_pattern)  # 找到所有符合模式的目錄
        
        if not checkpoint_dirs:  # 如果沒有找到檢查點
            self.logger.info("未找到檢查點目錄")  # 記錄沒有找到
            return
        
        total_size_before = 0  # 清理前的總大小
        for checkpoint_dir in checkpoint_dirs:  # 遍歷所有檢查點目錄
            # 計算檢查點大小
            for root, dirs, files in os.walk(checkpoint_dir):  # 遍歷目錄中的所有檔案
                for file in files:  # 遍歷每個檔案
                    file_path = os.path.join(root, file)  # 建立完整檔案路徑
                    if os.path.exists(file_path):  # 如果檔案存在
                        total_size_before += os.path.getsize(file_path)  # 累加檔案大小
        
        if self.keep_best_checkpoint and checkpoint_dirs:  # 如果要保留最佳檢查點
            # 保留最後一個（通常是最好的）檢查點
            checkpoint_dirs.sort(key=lambda x: int(x.split('-')[-1]))  # 按檢查點編號排序
            best_checkpoint = checkpoint_dirs[-1]  # 取得最後一個（最新的）檢查點
            
            self.logger.info(f"保留最佳檢查點: {best_checkpoint}")  # 記錄保留的檢查點
            
            # 刪除其他檢查點
            for checkpoint_dir in checkpoint_dirs[:-1]:  # 遍歷除了最後一個之外的所有檢查點
                try:
                    shutil.rmtree(checkpoint_dir)  # 刪除整個目錄
                    self.logger.info(f"已刪除檢查點: {checkpoint_dir}")  # 記錄刪除成功
                except Exception as e:  # 如果刪除失敗
                    self.logger.warning(f"刪除檢查點失敗 {checkpoint_dir}: {e}")  # 記錄警告
        else:
            # 刪除所有檢查點
            for checkpoint_dir in checkpoint_dirs:  # 遍歷所有檢查點
                try:
                    shutil.rmtree(checkpoint_dir)  # 刪除整個目錄
                    self.logger.info(f"已刪除檢查點: {checkpoint_dir}")  # 記錄刪除成功
                except Exception as e:  # 如果刪除失敗
                    self.logger.warning(f"刪除檢查點失敗 {checkpoint_dir}: {e}")  # 記錄警告
        
        # 顯示節省的空間
        total_size_mb = total_size_before / (1024 * 1024)  # 轉換為MB
        if not self.keep_best_checkpoint:  # 如果刪除了所有檢查點
            self.logger.info(f"檢查點清理完成，節省空間: {total_size_mb:.2f} MB")  # 記錄節省的空間
        else:
            # 重新計算剩餘大小
            remaining_size = 0  # 剩餘大小
            remaining_checkpoints = glob.glob(checkpoint_pattern)  # 找到剩餘的檢查點
            for checkpoint_dir in remaining_checkpoints:  # 遍歷剩餘檢查點
                for root, dirs, files in os.walk(checkpoint_dir):  # 遍歷目錄
                    for file in files:  # 遍歷檔案
                        file_path = os.path.join(root, file)  # 建立檔案路徑
                        if os.path.exists(file_path):  # 如果檔案存在
                            remaining_size += os.path.getsize(file_path)  # 累加檔案大小
                            self.logger.info(f"保留檢查點: {file_path} ({os.path.getsize(file_path)/1024:.1f} KB)")  # 記錄保留的檢查點
            
            saved_size_mb = (total_size_before - remaining_size) / (1024 * 1024)  # 計算節省的空間
            remaining_size_mb = remaining_size / (1024 * 1024)  # 計算剩餘空間
            self.logger.info(f"檢查點清理完成，節省空間: {saved_size_mb:.2f} MB，剩餘: {remaining_size_mb:.2f} MB")  # 記錄詳細資訊

    def _cleanup_unnecessary_files(self):  # 清理推理不需要的文件
        """清理推理時不需要的文件"""
        self.logger.info("清理推理不需要的文件...")
        
        # 推理時不需要的文件列表
        unnecessary_files = [
            "training_args.bin",  # 訓練參數，推理時不需要
        ]
        
        # 可選清理的目錄
        unnecessary_dirs = [
            "logs",  # 訓練日誌，推理時不需要
        ]
        
        total_saved = 0
        
        # 刪除不必要的文件
        for filename in unnecessary_files:
            file_path = os.path.join(self.output_dir, filename)
            if os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    total_saved += file_size
                    self.logger.info(f"已刪除文件: {filename} ({file_size/1024:.1f} KB)")
                except Exception as e:
                    self.logger.warning(f"刪除文件失敗 {filename}: {e}")
        
        # 刪除不必要的目錄
        for dirname in unnecessary_dirs:
            dir_path = os.path.join(self.output_dir, dirname)
            if os.path.exists(dir_path):
                try:
                    # 計算目錄大小
                    dir_size = 0
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if os.path.exists(file_path):
                                dir_size += os.path.getsize(file_path)
                    
                    shutil.rmtree(dir_path)
                    total_saved += dir_size
                    self.logger.info(f"已刪除目錄: {dirname} ({dir_size/1024:.1f} KB)")
                except Exception as e:
                    self.logger.warning(f"刪除目錄失敗 {dirname}: {e}")
        
        if total_saved > 0:
            self.logger.info(f"文件清理完成，額外節省: {total_saved/1024/1024:.2f} MB")
        else:
            self.logger.info("沒有找到需要清理的額外文件")

    def run_training(self):  # 執行訓練
        """運行訓練"""
        self.logger.info("=== 開始從零訓練 HackerAI 模型 ===")  # 記錄訓練開始
        
        # 加載數據
        text_data = self._load_data()  # 載入訓練文字資料
        
        # 準備模型和分詞器
        if not self._prepare_model_and_tokenizer():  # 如果模型和分詞器準備失敗
            sys.exit(1)  # 退出程式
        
        # 創建數據集
        dataset = self._create_dataset(text_data)  # 建立訓練資料集
        
        # 計算訓練步數
        total_samples = len(dataset)  # 總樣本數
        steps_per_epoch = max(1, total_samples // self.batch_size)  # 每個epoch的步數
        max_steps = steps_per_epoch * self.epochs  # 最大訓練步數
        
        # 確保至少有一些訓練步數
        if max_steps < 10:  # 如果步數太少
            max_steps = 50  # 設定最小步數
        
        self.logger.info(f"總樣本數: {total_samples}")  # 記錄總樣本數
        self.logger.info(f"每個epoch步數: {steps_per_epoch}")  # 記錄每個epoch的步數
        self.logger.info(f"最大訓練步數: {max_steps}")  # 記錄最大訓練步數
        
        # 設置訓練參數
        training_args = TrainingArguments(  # 建立訓練參數物件
            output_dir=self.output_dir,  # 輸出目錄
            overwrite_output_dir=True,  # 覆蓋輸出目錄
            max_steps=max_steps,  # 最大訓練步數
            per_device_train_batch_size=self.batch_size,  # 每個設備的批次大小
            learning_rate=self.learning_rate,  # 學習率
            warmup_steps=min(self.warmup_steps, max_steps // 4),  # 暖身步數
            save_steps=max(10, max_steps // 5),  # 保存步數間隔
            save_total_limit=3,  # 最多保存3個檢查點
            logging_steps=max(1, max_steps // 10),  # 日誌記錄步數間隔
            logging_dir=f"{self.output_dir}/logs",  # 日誌目錄
            dataloader_drop_last=False,  # 不丟棄最後一個不完整的批次
            fp16=False,  # 禁用混合精度以避免FP16問題
            eval_strategy="no",  # 不進行評估
            remove_unused_columns=False,  # 不移除未使用的欄位
            report_to=[],  # 禁用所有報告工具包括wandb
            disable_tqdm=False,  # 啟用進度條
        )
        
        # 數據整理器（將資料整理成模型可以處理的格式）
        data_collator = DataCollatorForLanguageModeling(  # 建立語言模型資料整理器
            tokenizer=self.tokenizer,  # 使用的分詞器
            mlm=False,  # 不使用遮蔽語言模型（因為我們做的是生成任務）
        )
        
        # 創建訓練器
        trainer = Trainer(  # 建立訓練器物件
            model=self.model,  # 要訓練的模型
            args=training_args,  # 訓練參數
            train_dataset=dataset,  # 訓練資料集
            data_collator=data_collator,  # 資料整理器
        )
        
        # 開始訓練
        self.logger.info("開始訓練...")  # 記錄訓練開始
        try:
            trainer.train()  # 執行訓練
            
            # 保存模型
            trainer.save_model()  # 保存訓練好的模型
            self.tokenizer.save_pretrained(self.output_dir)  # 保存分詞器
            
            self.logger.info(f"訓練完成！模型已保存到 {self.output_dir}")  # 記錄訓練完成
            
            # 自動清理檢查點
            self._cleanup_checkpoints()  # 清理不需要的檢查點檔案
            
            # 清理推理不需要的文件
            self._cleanup_unnecessary_files()  # 清理推理時不需要的額外文件
            
        except Exception as e:  # 如果訓練過程中出錯
            self.logger.error(f"訓練過程中出錯: {e}")  # 記錄錯誤
            sys.exit(1)  # 退出程式


class HackerDataset(Dataset):  # 定義資料集類別
    """黑客AI數據集"""
    
    def __init__(self, texts, tokenizer, max_length):  # 初始化資料集
        self.texts = texts  # 儲存文字資料
        self.tokenizer = tokenizer  # 儲存分詞器
        self.max_length = max_length  # 儲存最大長度
    
    def __len__(self):  # 回傳資料集大小
        return len(self.texts)  # 回傳文字數量
    
    def __getitem__(self, idx):  # 取得指定索引的資料項目
        text = self.texts[idx]  # 取得指定索引的文字
        
        # 編碼文本（將文字轉換成數字）
        encoded = self.tokenizer(  # 使用分詞器編碼文字
            text,  # 要編碼的文字
            truncation=True,  # 如果太長就截斷
            padding='max_length',  # 填充到最大長度
            max_length=self.max_length,  # 最大長度
            return_tensors='pt'  # 回傳PyTorch張量格式
        )
        
        # 對於語言模型，標籤就是輸入（模型要學習預測下一個詞）
        return {
            'input_ids': encoded['input_ids'].flatten(),  # 輸入的數字序列
            'attention_mask': encoded['attention_mask'].flatten(),  # 注意力遮罩（告訴模型哪些位置是真實內容）
            'labels': encoded['input_ids'].flatten()  # 標籤（模型要學習預測的目標）
        }


if __name__ == "__main__":  # 如果這個檔案被直接執行（而不是被匯入）
    try:
        trainer = HackerAITrainer()  # 建立訓練器實例
        trainer.run_training()  # 執行訓練
    except Exception as e:  # 如果出現任何錯誤
        logging.critical(f"訓練失敗: {e}", exc_info=True)  # 記錄嚴重錯誤和詳細資訊
        sys.exit(1)  # 退出程式