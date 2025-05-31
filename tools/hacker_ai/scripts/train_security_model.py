import os
import torch
import argparse
import json
import logging
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer,
    Trainer, 
    TrainingArguments,
    DataCollatorForLanguageModeling,
    set_seed
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training
)
from datasets import Dataset, load_dataset
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="安全知识模型训练脚本")
    parser.add_argument("--base_model_path", type=str, required=True, 
                        help="基础模型路径 (deepseek-coder-1.3b)")
    parser.add_argument("--security_model_path", type=str, required=False,
                        help="安全知识模型路径 (deepseek-r1-abliterated-8b)")
    parser.add_argument("--data_path", type=str, required=True,
                        help="安全数据集路径")
    parser.add_argument("--output_dir", type=str, required=True,
                        help="输出目录")
    parser.add_argument("--learning_rate", type=float, default=2e-5,
                        help="学习率")
    parser.add_argument("--num_train_epochs", type=int, default=3,
                        help="训练轮数")
    parser.add_argument("--per_device_train_batch_size", type=int, default=4,
                        help="每个设备的训练批次大小")
    parser.add_argument("--lora_rank", type=int, default=8,
                        help="LoRA适配器的秩")
    parser.add_argument("--lora_alpha", type=int, default=16,
                        help="LoRA alpha参数")
    parser.add_argument("--seed", type=int, default=42,
                        help="随机种子")
    parser.add_argument("--use_4bit", action="store_true",
                        help="是否使用4位量化")
    parser.add_argument("--merge_models", action="store_true",
                        help="是否合并安全知识从大模型到小模型")
    return parser.parse_args()

def load_security_dataset(data_path):
    """
    加载安全数据集
    
    参数:
    data_path (str): 安全数据集路径
    
    返回:
    Dataset: 处理后的数据集
    """
    logger.info(f"加载安全数据集: {data_path}")
    
    all_data = []
    
    # 加载CVE数据
    cve_path = os.path.join(data_path, "cve_data", "cve_data.json")
    if os.path.exists(cve_path):
        with open(cve_path, "r", encoding="utf-8") as f:
            cve_data = json.load(f)
            logger.info(f"加载了 {len(cve_data)} 条CVE数据")
            
            for item in cve_data:
                all_data.append({
                    "text": f"问题: {item['prompt']}\n回答: {item['description']}\n\n"
                })
    
    # 加载CTF数据
    ctf_path = os.path.join(data_path, "ctf_data", "ctf_data.json")
    if os.path.exists(ctf_path):
        with open(ctf_path, "r", encoding="utf-8") as f:
            ctf_data = json.load(f)
            logger.info(f"加载了 {len(ctf_data)} 条CTF数据")
            
            for item in ctf_data:
                all_data.append({
                    "text": f"问题: {item['prompt']}\n回答: {item['solution']}\n\n"
                })
    
    # 加载渗透测试数据
    pentest_path = os.path.join(data_path, "pentest_data", "pentest_data.json")
    if os.path.exists(pentest_path):
        with open(pentest_path, "r", encoding="utf-8") as f:
            pentest_data = json.load(f)
            logger.info(f"加载了 {len(pentest_data)} 条渗透测试数据")
            
            for item in pentest_data:
                prompt = f"如何使用{item['name']}技术进行{item['category']}?"
                response = f"{item['detail']}"
                all_data.append({
                    "text": f"问题: {prompt}\n回答: {response}\n\n"
                })
    
    logger.info(f"总共加载了 {len(all_data)} 条训练数据")
    return Dataset.from_list(all_data)

def prepare_model_for_training(args):
    """
    准备模型用于训练
    
    参数:
    args: 命令行参数
    
    返回:
    model: 准备好用于训练的模型
    tokenizer: 分词器
    """
    logger.info(f"加载基础模型: {args.base_model_path}")
    
    # 量化配置
    if args.use_4bit:
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model_path,
            quantization_config=bnb_config,
            device_map="auto",
        )
        model = prepare_model_for_kbit_training(model)
    else:
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model_path,
            torch_dtype=torch.float16,
            device_map="auto",
        )
    
    tokenizer = AutoTokenizer.from_pretrained(args.base_model_path)
    
    # 确保分词器有填充标记
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # 配置LoRA
    lora_config = LoraConfig(
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        target_modules=["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    logger.info("应用LoRA适配器...")
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model, tokenizer

def merge_security_knowledge(base_model, security_model, tokenizer, output_dir):
    """
    合并安全知识从大模型到小模型
    
    参数:
    base_model: 基础小模型
    security_model: 安全知识大模型
    tokenizer: 分词器
    output_dir: 输出目录
    """
    logger.info("开始合并安全知识...")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 选择一些安全相关提示
    security_prompts = [
        "什么是SQL注入攻击？",
        "如何执行一次基本的渗透测试？",
        "解释XSS漏洞的工作原理。",
        "如何使用nmap扫描网络？",
        "常见的密码破解技术有哪些？"
    ]
    
    # 获取安全模型的知识
    security_knowledge = {}
    logger.info("从安全模型中提取知识...")
    
    with torch.no_grad():
        for prompt in tqdm(security_prompts):
            inputs = tokenizer(prompt, return_tensors="pt").to(security_model.device)
            outputs = security_model.generate(
                inputs["input_ids"],
                max_length=512,
                num_return_sequences=1,
            )
            security_knowledge[prompt] = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # 创建一个知识注入数据集
    knowledge_data = [{"text": f"问题: {prompt}\n回答: {response}\n\n"} 
                      for prompt, response in security_knowledge.items()]
    
    knowledge_dataset = Dataset.from_list(knowledge_data)
    
    # 使用知识蒸馏方法将安全知识注入基础模型
    logger.info("将安全知识注入基础模型...")
    
    # 这里简化为直接微调
    # 实际中可能需要更复杂的知识蒸馏技术
    
    # 保存合并后的模型
    merged_model_dir = os.path.join(output_dir, "merged_model")
    os.makedirs(merged_model_dir, exist_ok=True)
    
    base_model.save_pretrained(merged_model_dir)
    tokenizer.save_pretrained(merged_model_dir)
    
    with open(os.path.join(merged_model_dir, "security_knowledge.json"), "w") as f:
        json.dump(security_knowledge, f, ensure_ascii=False, indent=2)
    
    logger.info(f"合并完成，模型已保存到: {merged_model_dir}")
    
    return merged_model_dir

def main():
    args = parse_args()
    set_seed(args.seed)
    
    # 加载和准备模型
    model, tokenizer = prepare_model_for_training(args)
    
    if args.merge_models and args.security_model_path:
        # 加载安全知识模型
        logger.info(f"加载安全知识模型: {args.security_model_path}")
        security_model = AutoModelForCausalLM.from_pretrained(
            args.security_model_path,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        
        # 合并安全知识
        merge_security_knowledge(model, security_model, tokenizer, args.output_dir)
    else:
        # 常规微调流程
        # 加载数据集
        train_dataset = load_security_dataset(args.data_path)
        
        # 定义训练参数
        training_args = TrainingArguments(
            output_dir=args.output_dir,
            learning_rate=args.learning_rate,
            num_train_epochs=args.num_train_epochs,
            per_device_train_batch_size=args.per_device_train_batch_size,
            save_steps=100,
            save_total_limit=3,
            logging_steps=10,
            gradient_accumulation_steps=8,
            fp16=True,
            optim="adamw_torch",
            lr_scheduler_type="cosine",
            warmup_ratio=0.05,
            weight_decay=0.01,
            report_to="none",
            remove_unused_columns=False,
        )
        
        # 配置数据收集器
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer, 
            mlm=False
        )
        
        # 初始化训练器
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=data_collator,
            tokenizer=tokenizer,
        )
        
        # 开始训练
        logger.info("开始训练...")
        trainer.train()
        
        # 保存最终模型
        final_model_dir = os.path.join(args.output_dir, "final_model")
        os.makedirs(final_model_dir, exist_ok=True)
        trainer.save_model(final_model_dir)
        tokenizer.save_pretrained(final_model_dir)
        
        logger.info(f"训练完成，模型已保存到: {final_model_dir}")

if __name__ == "__main__":
    main() 