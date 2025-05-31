#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import subprocess
import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hacker_ai_build.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ANSI颜色代码
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def parse_args():
    parser = argparse.ArgumentParser(description="黑客AI运行脚本")
    
    parser.add_argument("--action", type=str, choices=[
        "prepare_data", "prune_model", "train_model", "run_cli", "all"
    ], default="run_cli", help="要执行的动作")
    
    parser.add_argument("--small_model_path", type=str, default="./deepseek-coder-1.3b",
                        help="小模型路径 (deepseek-coder-1.3b)")
    
    parser.add_argument("--large_model_path", type=str, default="./deepseek-r1-abliterated-8b",
                        help="大模型路径 (deepseek-r1-abliterated-8b)")
    
    parser.add_argument("--output_dir", type=str, default="./hacker_ai_output",
                        help="输出目录")
    
    parser.add_argument("--data_dir", type=str, default="./security_data",
                        help="安全数据目录")
    
    parser.add_argument("--use_4bit", action="store_true",
                        help="是否使用4位量化")
    
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="生成温度 (0.1-1.0)")
    
    parser.add_argument("--skip_errors", action="store_true",
                        help="是否跳过错误继续执行")
    
    # Hugging Face相关选项
    parser.add_argument("--hf_token", type=str,
                        help="Hugging Face API令牌")
    
    parser.add_argument("--use_hf_fallback", action="store_true",
                        help="当本地模型无法回答时，是否使用Hugging Face API作为备选")
    
    parser.add_argument("--hf_model", type=str, default="deepseek-ai/deepseek-coder-33b-instruct",
                        help="要使用的Hugging Face模型ID")
    
    return parser.parse_args()

def run_command(cmd, description, skip_errors=False):
    """运行命令并处理输出"""
    logger.info(f"执行: {description}")
    logger.info(f"命令: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # 实时打印输出
        for line in process.stdout:
            print(line, end='')
        
        # 等待进程完成
        process.wait()
        
        # 检查返回码
        if process.returncode != 0:
            # 打印错误输出
            error_output = process.stderr.read()
            logger.error(f"命令失败，返回码: {process.returncode}")
            logger.error(f"错误信息: {error_output}")
            
            if not skip_errors:
                sys.exit(process.returncode)
            else:
                logger.warning("跳过错误继续执行")
                return False
        
        return True
    
    except Exception as e:
        logger.error(f"执行命令时出错: {e}")
        if not skip_errors:
            sys.exit(1)
        else:
            logger.warning("跳过错误继续执行")
            return False

def prepare_data(args):
    """准备安全数据集"""
    print(f"\n{Colors.HEADER}[1/4] 准备安全数据集{Colors.ENDC}\n")
    
    # 确保输出目录存在
    os.makedirs(args.data_dir, exist_ok=True)
    
    cmd = [
        sys.executable, "prepare_security_dataset.py",
        "--output_dir", args.data_dir,
        "--ctf_data", "--cve_data", "--pentest_data",
        "--max_samples", "1000"
    ]
    
    return run_command(cmd, "准备安全数据集", args.skip_errors)

def prune_model(args):
    """裁剪模型"""
    print(f"\n{Colors.HEADER}[2/4] 裁剪模型{Colors.ENDC}\n")
    
    # 确保输出目录存在
    pruned_dir = os.path.join(args.output_dir, "pruned_model")
    os.makedirs(pruned_dir, exist_ok=True)
    
    # 对小模型进行量化
    cmd = [
        sys.executable, "model_pruning.py",
        "--model_path", args.small_model_path,
        "--output_dir", pruned_dir,
        "--method", "quantize",
        "--quantize_type", "int8" if not args.use_4bit else "int4",
        "--security_focus"
    ]
    
    return run_command(cmd, "裁剪模型", args.skip_errors)

def train_model(args):
    """训练模型"""
    print(f"\n{Colors.HEADER}[3/4] 训练模型{Colors.ENDC}\n")
    
    # 确保输出目录存在
    trained_dir = os.path.join(args.output_dir, "trained_model")
    os.makedirs(trained_dir, exist_ok=True)
    
    # 训练命令
    cmd = [
        sys.executable, "train_security_model.py",
        "--base_model_path", args.small_model_path,
        "--security_model_path", args.large_model_path,
        "--data_path", args.data_dir,
        "--output_dir", trained_dir,
        "--merge_models"
    ]
    
    if args.use_4bit:
        cmd.append("--use_4bit")
    
    return run_command(cmd, "训练模型", args.skip_errors)

def run_cli(args):
    """运行命令行界面"""
    print(f"\n{Colors.HEADER}[4/4] 运行黑客AI命令行{Colors.ENDC}\n")
    
    # 检查模型路径
    final_model_dir = os.path.join(args.output_dir, "trained_model/final_model")
    merged_model_dir = os.path.join(args.output_dir, "trained_model/merged_model")
    pruned_model_dir = os.path.join(args.output_dir, "pruned_model")
    
    # 按优先级选择模型路径
    if os.path.exists(final_model_dir):
        model_path = final_model_dir
    elif os.path.exists(merged_model_dir):
        model_path = merged_model_dir
    elif os.path.exists(pruned_model_dir):
        model_path = pruned_model_dir
    else:
        model_path = args.small_model_path
    
    logger.info(f"使用模型: {model_path}")
    
    # 运行命令行界面
    cmd = [
        sys.executable, "hacker_ai_cli.py",
        "--model_path", model_path,
        "--temperature", str(args.temperature),
        "--save_history"
    ]
    
    if args.use_4bit:
        cmd.append("--use_4bit")
    
    # 添加Hugging Face相关参数
    if args.hf_token:
        cmd.extend(["--hf_token", args.hf_token])
    
    if args.use_hf_fallback:
        cmd.append("--use_hf_fallback")
    
    if args.hf_model:
        cmd.extend(["--hf_model", args.hf_model])
    
    # 命令行界面中断后不应视为错误
    try:
        run_command(cmd, "运行命令行界面", True)
    except KeyboardInterrupt:
        print("\n\n收到中断信号，关闭中...")

def check_requirements():
    """检查环境需求"""
    try:
        import torch
        import transformers
        import tqdm
        import peft
        
        # 检查CUDA可用性
        if torch.cuda.is_available():
            logger.info(f"已检测到CUDA: {torch.cuda.get_device_name(0)}")
        else:
            logger.warning("未检测到CUDA，性能可能受限")
        
        return True
    except ImportError as e:
        logger.error(f"缺少必要的Python包: {e}")
        logger.info("请运行: pip install torch transformers tqdm peft datasets")
        return False

def install_requirements():
    """安装必要的依赖"""
    requirements = [
        "torch", "transformers", "tqdm", "peft", "datasets", 
        "accelerate", "bitsandbytes", "sentencepiece", "safetensors",
        "requests"  # 增加Hugging Face API所需的依赖
    ]
    
    print(f"\n{Colors.HEADER}安装必要的依赖{Colors.ENDC}\n")
    cmd = [sys.executable, "-m", "pip", "install"] + requirements
    
    return run_command(cmd, "安装依赖", True)

def print_banner():
    """打印启动横幅"""
    banner = f"""
{Colors.RED}
 ██░ ██  ▄▄▄       ▄████▄   ██ ▄█▀▓█████  ██▀███      ▄▄▄       ██▓
▓██░ ██▒▒████▄    ▒██▀ ▀█   ██▄█▒ ▓█   ▀ ▓██ ▒ ██▒   ▒████▄    ▓██▒
▒██▀▀██░▒██  ▀█▄  ▒▓█    ▄ ▓███▄░ ▒███   ▓██ ░▄█ ▒   ▒██  ▀█▄  ▒██▒
░▓█ ░██ ░██▄▄▄▄██ ▒▓▓▄ ▄██▒▓██ █▄ ▒▓█  ▄ ▒██▀▀█▄     ░██▄▄▄▄██ ░██░
░▓█▒░██▓ ▓█   ▓██▒▒ ▓███▀ ░▒██▒ █▄░▒████▒░██▓ ▒██▒    ▓█   ▓██▒░██░
 ▒ ░░▒░▒ ▒▒   ▓▒█░░ ░▒ ▒  ░▒ ▒▒ ▓▒░░ ▒░ ░░ ▒▓ ░▒▓░    ▒▒   ▓▒█░░▓  
 ▒ ░▒░ ░  ▒   ▒▒ ░  ░  ▒   ░ ░▒ ▒░ ░ ░  ░  ░▒ ░ ▒░     ▒   ▒▒ ░ ▒ ░
 ░  ░░ ░  ░   ▒   ░        ░ ░░ ░    ░     ░░   ░      ░   ▒    ▒ ░
 ░  ░  ░      ░  ░░ ░      ░  ░      ░  ░   ░              ░  ░ ░  
                 ░                                               
{Colors.ENDC}

{Colors.CYAN}黑客AI构建与运行工具 v1.0{Colors.ENDC}
{Colors.RED}警告: 仅用于合法授权的安全测试和研究目的{Colors.ENDC}
"""
    print(banner)

def main():
    # 打印横幅
    print_banner()
    
    # 解析命令行参数
    args = parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 检查依赖
    if not check_requirements():
        logger.info("尝试安装必要的依赖...")
        if not install_requirements():
            logger.error("安装依赖失败，请手动安装")
            sys.exit(1)
    
    # 根据选择的动作执行
    if args.action == "prepare_data" or args.action == "all":
        prepare_data(args)
    
    if args.action == "prune_model" or args.action == "all":
        prune_model(args)
    
    if args.action == "train_model" or args.action == "all":
        train_model(args)
    
    if args.action == "run_cli" or args.action == "all":
        run_cli(args)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n收到中断信号，关闭中...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"运行时错误: {e}")
        sys.exit(1) 