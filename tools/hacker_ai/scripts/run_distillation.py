#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import logging
import subprocess
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="AI黑客工具 - 从Hugging Face模型蒸馏知识")
    
    parser.add_argument("--mode", type=str, required=True,
                        choices=["single", "multi", "expert"],
                        help="蒸馏模式: single=单教师模型, multi=多教师模型, expert=专家模型组合")
    
    parser.add_argument("--student_model", type=str, default="./deepseek-coder-1.3b",
                        help="学生模型路径（本地模型）")
    
    parser.add_argument("--domain", type=str, default="combined",
                        choices=["security", "coding", "general", "combined"],
                        help="蒸馏领域")
    
    parser.add_argument("--output_dir", type=str, default="./distilled_hacker_ai",
                        help="输出目录")
    
    parser.add_argument("--use_4bit", action="store_true",
                        help="是否使用4位量化")
    
    parser.add_argument("--use_lora", action="store_true", default=True,
                        help="是否使用LoRA")
    
    parser.add_argument("--hf_token", type=str,
                        help="Hugging Face API令牌")
    
    parser.add_argument("--teacher_model", type=str, 
                        default="mistralai/Mistral-7B-Instruct-v0.2",
                        help="单教师模式下的教师模型")
    
    parser.add_argument("--samples", type=int, default=100,
                        help="收集的样本总数")
    
    parser.add_argument("--use_cached", action="store_true",
                        help="使用缓存的知识数据")
    
    return parser.parse_args()

def check_dependencies():
    """检查必要的依赖"""
    try:
        import torch
        import transformers
        import peft
        from datasets import Dataset
        
        logger.info(f"PyTorch版本: {torch.__version__}")
        logger.info(f"Transformers版本: {transformers.__version__}")
        logger.info(f"PEFT版本: {peft.__version__}")
        
        # 检查CUDA是否可用
        if torch.cuda.is_available():
            logger.info(f"CUDA可用，使用设备: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA版本: {torch.version.cuda}")
        else:
            logger.warning("CUDA不可用，将使用CPU训练（非常慢）")
        
        return True
    
    except ImportError as e:
        logger.error(f"缺少必要的依赖: {e}")
        logger.error("请运行: pip install torch transformers peft datasets")
        return False

def check_model_exists(model_path):
    """检查模型是否存在"""
    if not os.path.exists(model_path):
        logger.error(f"学生模型路径不存在: {model_path}")
        logger.error("请确保已下载模型或提供正确的路径")
        return False
    return True

def run_single_teacher_distillation(args):
    """运行单一教师模型蒸馏"""
    logger.info(f"开始单一教师蒸馏，教师模型: {args.teacher_model}")
    
    cmd = [
        "python", "distill_from_huggingface.py",
        "--student_model_path", args.student_model,
        "--teacher_model_id", args.teacher_model,
        "--output_dir", args.output_dir,
        "--num_samples", str(args.samples),
        "--domain", args.domain
    ]
    
    if args.use_4bit:
        cmd.append("--use_4bit")
    
    if args.use_lora:
        cmd.append("--use_lora")
    
    if args.hf_token:
        cmd.extend(["--hf_token", args.hf_token])
    
    logger.info(f"执行命令: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"蒸馏过程出错: {e}")
        return False

def run_multi_teacher_distillation(args):
    """运行多教师模型蒸馏"""
    logger.info("开始多教师蒸馏")
    
    # 计算每个模型的样本数
    samples_per_model = args.samples // 7  # 默认有7个模型
    
    cmd = [
        "python", "multi_teacher_distillation.py",
        "--student_model_path", args.student_model,
        "--output_dir", args.output_dir,
        "--samples_per_model", str(samples_per_model),
        "--domain", args.domain
    ]
    
    if args.use_4bit:
        cmd.append("--use_4bit")
    
    if args.use_lora:
        cmd.append("--use_lora")
    
    if args.hf_token:
        cmd.extend(["--hf_token", args.hf_token])
    
    if args.use_cached:
        cmd.append("--use_cached")
    
    logger.info(f"执行命令: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"蒸馏过程出错: {e}")
        return False

def run_expert_ensemble_distillation(args):
    """运行专家模型组合蒸馏"""
    logger.info("开始专家模型组合蒸馏")
    
    # 定义领域专家模型
    security_expert = "mistralai/Mistral-7B-Instruct-v0.2"  # 安全领域
    coding_expert = "Qwen/Qwen-7B-Chat"                    # 编程领域
    general_expert = "meta-llama/Llama-2-7b-chat-hf"       # 通用领域
    
    cmd = [
        "python", "multi_teacher_distillation.py",
        "--student_model_path", args.student_model,
        "--output_dir", args.output_dir,
        "--samples_per_model", str(args.samples // 3),  # 每个模型平均分配样本
        "--domain", "combined",  # 使用综合领域
        "--teacher_models", security_expert, coding_expert, general_expert,
        "--custom_models"  # 不添加自定义模型，保持列表为空
    ]
    
    if args.use_4bit:
        cmd.append("--use_4bit")
    
    if args.use_lora:
        cmd.append("--use_lora")
    
    if args.hf_token:
        cmd.extend(["--hf_token", args.hf_token])
    
    if args.use_cached:
        cmd.append("--use_cached")
    
    logger.info(f"执行命令: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"蒸馏过程出错: {e}")
        return False

def main():
    """主函数"""
    args = parse_args()
    
    logger.info("=== 黑客AI知识蒸馏工具 ===")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查模型
    if not check_model_exists(args.student_model):
        sys.exit(1)
    
    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 根据模式执行对应的蒸馏流程
    success = False
    if args.mode == "single":
        success = run_single_teacher_distillation(args)
    elif args.mode == "multi":
        success = run_multi_teacher_distillation(args)
    elif args.mode == "expert":
        success = run_expert_ensemble_distillation(args)
    
    if success:
        logger.info(f"蒸馏完成！模型已保存到 {args.output_dir}")
        logger.info("现在可以使用这个模型进行安全领域的问答")
    else:
        logger.error("蒸馏过程失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 