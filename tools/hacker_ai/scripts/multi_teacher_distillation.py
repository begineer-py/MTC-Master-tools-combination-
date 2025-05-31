import os
import torch
import argparse
import logging
import json
import random
import numpy as np
from tqdm import tqdm
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
    set_seed
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from huggingface_api_client import HuggingFaceClient
import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "./configs/multi_teacher_config.json"

class MultiTeacherDistiller:
    """多教师模型蒸馏器类"""
    
    def __init__(self, args=None):
        """初始化蒸馏器"""
        self.args = args if args else self.parse_args()
        self.config = None
        self.hf_client = None
        self.model = None
        self.tokenizer = None
        self.training_args = None
        self.train_dataset = None
        self.teacher_models = []
        self.prompts_by_model = []
        
        # 加载配置
        self.load_config()
        
        # 应用配置覆盖
        if args is None:
            self.args = self.apply_config_overrides(self.args)
    
    def load_config(self, config_path=None):
        """加载JSON配置文件"""
        if config_path is None:
            config_path = self.args.config if hasattr(self.args, 'config') else DEFAULT_CONFIG_PATH
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"成功加载配置文件: {config_path}")
            return self.config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def parse_args(self):
        """解析命令行参数"""
        # 加载默认配置
        config = self.load_config(DEFAULT_CONFIG_PATH)
        model_settings = config.get("model_settings", {})
        distillation_settings = config.get("distillation_settings", {})
        training_settings = config.get("training_settings", {})
        domain_settings = config.get("domain_settings", {})
        
        # 从配置中获取默认教师模型
        default_teacher_models = model_settings.get("default_teacher_models", [
            "openchat/openchat-3.5-0106",
            "THUDM/chatglm3-6b",
            "Qwen/Qwen-7B-Chat",
            "01-ai/Yi-6B-Chat",
            "mistralai/Mistral-7B-Instruct-v0.2",
            "meta-llama/Llama-2-7b-chat-hf",
            "google/gemma-7b-it"
        ])
        
        parser = argparse.ArgumentParser(description="从多个Hugging Face免费API进行蒸馏")
        
        # 配置文件设置
        parser.add_argument("--config", type=str, default=DEFAULT_CONFIG_PATH,
                            help="配置文件路径")
        
        # 基础设置
        parser.add_argument("--student_model_path", type=str,
                            default=model_settings.get("default_student_model_path"),
                            help="学生模型路径（如deepseek-coder-1.3b）")
        parser.add_argument("--output_dir", type=str, default="./multi_distilled_model",
                            help="输出目录")
        
        # 教师模型设置
        parser.add_argument("--teacher_models", type=str, nargs="+", default=default_teacher_models,
                            help="教师模型ID列表")
        parser.add_argument("--custom_models", type=str, nargs="+", default=[],
                            help="额外的自定义教师模型ID")
        parser.add_argument("--domain", type=str, 
                            default=domain_settings.get("default_domain", "security"),
                            choices=domain_settings.get("available_domains", ["security", "coding", "general", "combined"]),
                            help="查询的领域类型")
        
        # 蒸馏设置
        parser.add_argument("--samples_per_model", type=int, 
                            default=distillation_settings.get("samples_per_model", 20),
                            help="每个模型的样本数量")
        parser.add_argument("--temperature", type=float, 
                            default=distillation_settings.get("temperature", 0.7),
                            help="教师模型生成时的温度")
        parser.add_argument("--max_length", type=int, 
                            default=distillation_settings.get("max_length", 1024),
                            help="生成回复的最大长度")
        parser.add_argument("--use_cached", action="store_true",
                            default=distillation_settings.get("use_cached", False),
                            help="使用缓存的知识数据（如果存在）")
        
        # 训练设置
        parser.add_argument("--use_4bit", action="store_true",
                            default=training_settings.get("use_4bit", False),
                            help="是否使用4位量化")
        parser.add_argument("--num_train_epochs", type=int, 
                            default=training_settings.get("num_train_epochs", 3),
                            help="训练轮数")
        parser.add_argument("--learning_rate", type=float, 
                            default=training_settings.get("learning_rate", 2e-4),
                            help="学习率")
        parser.add_argument("--per_device_train_batch_size", type=int, 
                            default=training_settings.get("per_device_train_batch_size", 4),
                            help="每设备训练批次大小")
        parser.add_argument("--use_lora", action="store_true", 
                            default=training_settings.get("use_lora", True),
                            help="是否使用LoRA参数高效微调")
        parser.add_argument("--lora_rank", type=int, 
                            default=training_settings.get("lora_rank", 8),
                            help="LoRA秩")
        parser.add_argument("--lora_alpha", type=int, 
                            default=training_settings.get("lora_alpha", 16),
                            help="LoRA alpha参数")
        parser.add_argument("--seed", type=int, 
                            default=training_settings.get("seed", 42),
                            help="随机种子")
        
        # API设置
        parser.add_argument("--hf_token", type=str,
                            help="Hugging Face API令牌")
        parser.add_argument("--retry_count", type=int, 
                            default=distillation_settings.get("retry_count", 3),
                            help="API请求失败后的重试次数")
        parser.add_argument("--timeout", type=int, 
                            default=distillation_settings.get("timeout", 30),
                            help="API请求超时时间（秒）")
        
        # 问题文件设置
        parser.add_argument("--questions_dir", type=str, 
                            default=domain_settings.get("questions_dir", "./scripts/questions"),
                            help="问题文件所在目录")
        
        return parser.parse_args()

    def apply_config_overrides(self, args):
        """根据命令行参数覆盖配置"""
        # 如果使用了非默认配置文件
        if args.config != DEFAULT_CONFIG_PATH:
            logger.info(f"加载自定义配置文件: {args.config}")
            config = self.load_config(args.config)
            # 更新没有在命令行中明确指定的参数
            args_dict = vars(args)
            default_args = vars(self.parse_args())
            
            # 更新模型设置
            model_settings = config.get("model_settings", {})
            if "default_student_model_path" in model_settings and args.student_model_path == default_args["student_model_path"]:
                args.student_model_path = model_settings["default_student_model_path"]
            
            # 更新教师模型设置
            if "default_teacher_models" in model_settings and args.teacher_models == default_args["teacher_models"]:
                args.teacher_models = model_settings["default_teacher_models"]
            
            # 更新蒸馏设置
            distillation_settings = config.get("distillation_settings", {})
            for key in ["samples_per_model", "temperature", "max_length", "use_cached", "retry_count", "timeout"]:
                if key in distillation_settings and key in args_dict and args_dict[key] == default_args[key]:
                    setattr(args, key, distillation_settings[key])
            
            # 更新训练设置
            training_settings = config.get("training_settings", {})
            for key in ["use_4bit", "num_train_epochs", "learning_rate", "per_device_train_batch_size", 
                        "use_lora", "lora_rank", "lora_alpha", "seed"]:
                if key in training_settings and key in args_dict and args_dict[key] == default_args[key]:
                    setattr(args, key, training_settings[key])
            
            # 更新领域设置
            domain_settings = config.get("domain_settings", {})
            if "default_domain" in domain_settings and args.domain == default_args["domain"]:
                args.domain = domain_settings["default_domain"]
            if "questions_dir" in domain_settings and args.questions_dir == default_args["questions_dir"]:
                args.questions_dir = domain_settings["questions_dir"]
        
        return args
    
    def read_questions_from_file(self, file_path, num_samples):
        """从文件中读取问题"""
        if not os.path.exists(file_path):
            logger.error(f"问题文件不存在: {file_path}")
            raise FileNotFoundError(f"无法找到问题文件: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            prompts = [line.strip() for line in f if line.strip()]
        
        if not prompts:
            logger.error(f"问题文件为空: {file_path}")
            raise ValueError(f"问题文件为空: {file_path}")
        
        # 如果问题不够，重复使用
        while len(prompts) < num_samples:
            prompts.append(random.choice(prompts))
        
        # 确保不超过请求的样本数
        random.shuffle(prompts)
        return prompts[:num_samples]

    def get_prompts(self):
        """从文件获取指定领域的问题"""
        domain = self.args.domain
        questions_dir = self.args.questions_dir
        
        # 合并自定义模型
        self.teacher_models = self.args.teacher_models + self.args.custom_models
        
        # 计算所需的总提示数量
        prompts_per_model = self.args.samples_per_model
        total_prompts = prompts_per_model * len(self.teacher_models)
        
        domain_file_map = {
            "security": "security_questions.txt",
            "coding": "coding_questions.txt",
            "general": "general_questions.txt",
            "combined": "combined_questions.txt"
        }
        
        file_path = os.path.join(questions_dir, domain_file_map[domain])
        logger.info(f"从文件 {file_path} 读取 {domain} 领域的问题")
        
        try:
            all_prompts = self.read_questions_from_file(file_path, total_prompts)
            logger.info(f"成功加载 {len(all_prompts)} 个问题")
            
            # 每个模型使用不同的提示集，确保多样性
            chunks = np.array_split(all_prompts, len(self.teacher_models))
            self.prompts_by_model = [chunk.tolist() for chunk in chunks]
            
            return all_prompts
        except Exception as e:
            logger.error(f"读取问题文件时出错: {e}")
            raise
    
    def format_prompt_for_model(self, model_id, prompt):
        """根据不同的模型格式化提示"""
        # 针对不同模型的格式化模板
        if "chatglm" in model_id.lower():
            return f"[Round 1]\n\n问：{prompt}\n\n答："
        elif "qwen" in model_id.lower():
            return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        elif "llama" in model_id.lower() or "mistral" in model_id.lower():
            return f"<s>[INST] {prompt} [/INST]"
        elif "gemma" in model_id.lower():
            return f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        elif "openchat" in model_id.lower():
            return f"Human: {prompt}\n\nAssistant:"
        elif "yi" in model_id.lower():
            return f"<human>: {prompt}\n<assistant>:"
        else:
            # 默认格式
            return f"问题: {prompt}\n回答:"

    def collect_knowledge_from_models(self):
        """从多个教师模型收集知识"""
        dataset = []
        os.makedirs("datasets", exist_ok=True)
        cache_file = f"datasets/multi_teacher_knowledge_{self.args.domain}.json"
        
        # 检查是否有缓存数据
        if self.args.use_cached and os.path.exists(cache_file):
            logger.info(f"使用缓存的知识数据: {cache_file}")
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        
        logger.info(f"从 {len(self.teacher_models)} 个教师模型收集知识...")
        
        for model_id, prompts in zip(self.teacher_models, self.prompts_by_model):
            logger.info(f"查询模型: {model_id}，样本数: {len(prompts)}")
            model_dataset = []
            
            for prompt in tqdm(prompts):
                formatted_prompt = self.format_prompt_for_model(model_id, prompt)
                params = {
                    "temperature": self.args.temperature,
                    "max_length": self.args.max_length,
                    "top_p": 0.95,
                    "return_full_text": False
                }
                
                # 带重试的API请求
                response = None
                retry_count = 0
                while retry_count < self.args.retry_count:
                    try:
                        response = self.hf_client.query_model(model_id, formatted_prompt, params)
                        if "error" not in response:
                            break
                        retry_count += 1
                        logger.warning(f"查询失败 ({retry_count}/{self.args.retry_count}): {response.get('error', '未知错误')}")
                    except Exception as e:
                        retry_count += 1
                        logger.warning(f"查询异常 ({retry_count}/{self.args.retry_count}): {e}")
                
                if not response or "error" in response:
                    logger.warning(f"跳过提示: {prompt} - 请求失败")
                    continue
                
                # 处理响应格式 (因模型而异)
                if isinstance(response, list) and len(response) > 0:
                    if "generated_text" in response[0]:
                        answer = response[0]["generated_text"]
                    else:
                        answer = str(response[0])
                else:
                    answer = str(response)
                
                # 清理可能的模型格式化标记
                answer = answer.replace("<|im_end|>", "").replace("</s>", "").replace("<|endoftext|>", "")
                
                # 创建教师-学生数据对
                item = {
                    "prompt": prompt,
                    "response": answer,
                    "model": model_id,
                    "text": f"问题: {prompt}\n回答: {answer}"
                }
                model_dataset.append(item)
                dataset.append(item)
            
            logger.info(f"从模型 {model_id} 成功收集 {len(model_dataset)} 个知识样本")
        
        logger.info(f"总共收集 {len(dataset)} 个知识样本")
        
        # 保存数据集以便复用
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        
        return dataset

    def prepare_student_model(self):
        """准备学生模型用于训练"""
        model_path = self.args.student_model_path
        use_4bit = self.args.use_4bit
        use_lora = self.args.use_lora
        lora_rank = self.args.lora_rank
        lora_alpha = self.args.lora_alpha
        
        logger.info(f"加载学生模型: {model_path}")
        
        # 量化配置
        if use_4bit:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=bnb_config,
                device_map="auto",
            )
            if use_lora:
                model = prepare_model_for_kbit_training(model)
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
            )
        
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # 确保分词器有填充标记
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # 配置LoRA (如果启用)
        if use_lora:
            logger.info("应用LoRA适配器...")
            
            # 不同架构的目标模块
            architecture = model.config.architectures[0] if hasattr(model.config, 'architectures') and model.config.architectures else ""
            if "Llama" in architecture:
                target_modules = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "down_proj", "up_proj"]
            elif "Mistral" in architecture:
                target_modules = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "down_proj", "up_proj"]
            elif "Gemma" in architecture:
                target_modules = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "down_proj", "up_proj"]
            elif "DeepSeek" in architecture:
                target_modules = ["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"]
            else:
                # 默认适用于大多数模型的目标模块
                target_modules = ["query_key_value", "dense", "q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "down_proj", "up_proj"]
            
            lora_config = LoraConfig(
                r=lora_rank,
                lora_alpha=lora_alpha,
                target_modules=target_modules,
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM"
            )
            
            model = get_peft_model(model, lora_config)
            model.print_trainable_parameters()
        
        self.model = model
        self.tokenizer = tokenizer
        return model, tokenizer

    def setup_training_args(self):
        """设置训练参数"""
        training_settings = self.config.get("training_settings", {})
        
        # 定义训练参数
        self.training_args = TrainingArguments(
            output_dir=self.args.output_dir,
            learning_rate=self.args.learning_rate,
            num_train_epochs=self.args.num_train_epochs,
            per_device_train_batch_size=self.args.per_device_train_batch_size,
            save_steps=training_settings.get("save_steps", 50),
            save_total_limit=training_settings.get("save_total_limit", 3),
            logging_steps=training_settings.get("logging_steps", 10),
            gradient_accumulation_steps=training_settings.get("gradient_accumulation_steps", 4),
            fp16=not self.args.use_4bit and training_settings.get("fp16", True),
            optim=training_settings.get("optim", "adamw_torch"),
            lr_scheduler_type=training_settings.get("lr_scheduler_type", "cosine"),
            warmup_ratio=training_settings.get("warmup_ratio", 0.05),
            weight_decay=training_settings.get("weight_decay", 0.01),
            report_to="none",
            remove_unused_columns=False,
        )
        
        return self.training_args
    
    def save_model(self, output_path=None):
        """保存模型到指定路径"""
        if output_path is None:
            output_path = self.args.output_dir
            
        logger.info(f"保存模型到 {output_path}")
        
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
        
        # 保存模型和分词器
        if self.model and self.tokenizer:
            self.model.save_pretrained(output_path)
            self.tokenizer.save_pretrained(output_path)
            
            # 保存配置信息
            with open(os.path.join(output_path, "distillation_config.json"), "w", encoding="utf-8") as f:
                json.dump({
                    "teacher_models": self.teacher_models,
                    "domain": self.args.domain,
                    "samples_per_model": self.args.samples_per_model,
                    "distillation_date": str(datetime.datetime.now()),
                    "training_args": {
                        "learning_rate": self.args.learning_rate,
                        "num_train_epochs": self.args.num_train_epochs,
                        "per_device_train_batch_size": self.args.per_device_train_batch_size,
                        "use_lora": self.args.use_lora,
                        "lora_rank": self.args.lora_rank,
                        "lora_alpha": self.args.lora_alpha,
                        "use_4bit": self.args.use_4bit
                    }
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"模型已保存到 {output_path}")
            return True
        else:
            logger.error("无法保存模型: 模型或分词器未初始化")
            return False
    
    def load_model(self, model_path=None):
        """从指定路径加载模型"""
        if model_path is None:
            model_path = self.args.output_dir
            
        logger.info(f"从 {model_path} 加载模型")
        
        if not os.path.exists(model_path):
            logger.error(f"模型路径不存在: {model_path}")
            return False
        
        try:
            # 加载模型和分词器
            if self.args.use_4bit:
                from transformers import BitsAndBytesConfig
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    quantization_config=bnb_config,
                    device_map="auto",
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,
                    device_map="auto",
                )
                
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            # 确保分词器有填充标记
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info(f"成功加载模型和分词器")
            return True
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False
    
    def run(self):
        """执行多教师蒸馏流程"""
        # 设置随机种子
        set_seed(self.args.seed)
        
        # 创建Hugging Face客户端
        self.hf_client = HuggingFaceClient(api_token=self.args.hf_token)
        
        # 获取提示
        self.get_prompts()
        
        # 从教师模型收集知识
        knowledge_data = self.collect_knowledge_from_models()
        
        if not knowledge_data:
            logger.error("未能从教师模型收集到知识，退出")
            return
        
        # 创建数据集
        self.train_dataset = Dataset.from_list([{"text": item["text"]} for item in knowledge_data])
        
        # 准备学生模型
        self.prepare_student_model()
        
        # 设置训练参数
        self.setup_training_args()
        
        # 配置数据收集器
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer, 
            mlm=False
        )
        
        # 初始化训练器
        trainer = Trainer(
            model=self.model,
            args=self.training_args,
            train_dataset=self.train_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        # 开始训练
        logger.info("开始训练学生模型...")
        trainer.train()
        
        # 保存模型
        logger.info(f"保存蒸馏后的模型到 {self.args.output_dir}")
        self.save_model()
        
        logger.info("多教师蒸馏完成！")

def main():
    """主函数"""
    distiller = MultiTeacherDistiller()
    distiller.run()

if __name__ == "__main__":
    main() 