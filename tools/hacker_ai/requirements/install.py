#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import platform
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="黑客AI依赖安装工具")
    parser.add_argument("--cuda", type=str, choices=["11.7", "11.8", "12.1"], 
                      help="CUDA版本，如11.7、11.8或12.1")
    parser.add_argument("--no-verify", action="store_true", 
                      help="跳过环境验证")
    parser.add_argument("--extra", action="store_true", 
                      help="安装额外依赖（包括注释掉的可选依赖）")
    return parser.parse_args()

def get_python_version():
    """获取Python版本信息"""
    version = sys.version_info
    return f"{version.major}.{version.minor}.{version.micro}"

def get_system_info():
    """获取系统信息"""
    system = platform.system()
    if system == "Windows":
        return "Windows", platform.release()
    elif system == "Linux":
        try:
            import distro
            return distro.name(), distro.version()
        except ImportError:
            return "Linux", ""
    elif system == "Darwin":
        return "macOS", platform.mac_ver()[0]
    else:
        return system, ""

def check_cuda():
    """检查CUDA是否可用"""
    try:
        output = subprocess.check_output(["nvidia-smi"], stderr=subprocess.STDOUT).decode("utf-8")
        for line in output.split("\n"):
            if "CUDA Version:" in line:
                return line.split("CUDA Version:")[1].strip()
        return None
    except:
        return None

def install_requirements(cuda_version=None, install_extra=False):
    """安装requirements.txt中的依赖"""
    # 基础安装命令
    cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    
    # 如果指定了CUDA版本，安装对应版本的PyTorch
    if cuda_version:
        # 先删除requirements.txt中的torch和torchvision
        cmd_pytorch = [sys.executable, "-m", "pip", "uninstall", "-y", "torch", "torchvision"]
        print(f"移除现有PyTorch: {' '.join(cmd_pytorch)}")
        subprocess.run(cmd_pytorch)
        
        # 安装对应CUDA版本的PyTorch
        cuda_map = {
            "11.7": "cu117",
            "11.8": "cu118",
            "12.1": "cu121"
        }
        cuda_tag = cuda_map.get(cuda_version, "cu117")
        torch_cmd = [
            sys.executable, "-m", "pip", "install", 
            f"torch>=2.0.0+{cuda_tag}", 
            f"torchvision>=0.15.0+{cuda_tag}", 
            "--index-url", f"https://download.pytorch.org/whl/{cuda_tag}"
        ]
        print(f"安装PyTorch (CUDA {cuda_version}): {' '.join(torch_cmd)}")
        subprocess.run(torch_cmd)
    
    # 安装其他依赖
    print(f"安装依赖: {' '.join(cmd)}")
    subprocess.run(cmd)
    
    # 如果需要安装额外依赖
    if install_extra:
        # 读取requirements.txt找出被注释的依赖
        extra_packages = []
        with open("requirements.txt", "r") as f:
            for line in f:
                if line.strip().startswith("# ") and ">=" in line:
                    # 移除开头的"# "
                    package = line.strip()[2:]
                    extra_packages.append(package)
        
        if extra_packages:
            extra_cmd = [sys.executable, "-m", "pip", "install"] + extra_packages
            print(f"安装额外依赖: {' '.join(extra_cmd)}")
            subprocess.run(extra_cmd)

def verify_installation():
    """验证安装是否成功"""
    import importlib.util
    
    required_packages = [
        "torch", "transformers", "peft", "datasets", 
        "accelerate", "bitsandbytes", "sentencepiece"
    ]
    
    missing_packages = []
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"警告: 以下包安装失败: {', '.join(missing_packages)}")
        return False
    
    # 检查CUDA是否可用
    try:
        import torch
        if torch.cuda.is_available():
            print(f"CUDA可用: {torch.cuda.get_device_name(0)}")
        else:
            print("CUDA不可用，将使用CPU（速度较慢）")
    except:
        print("无法检查CUDA状态")
    
    return True

def main():
    args = parse_args()
    
    print("=== 黑客AI依赖安装工具 ===")
    
    # 获取系统信息
    system, version = get_system_info()
    python_version = get_python_version()
    cuda_version = check_cuda()
    
    print(f"系统: {system} {version}")
    print(f"Python版本: {python_version}")
    print(f"CUDA版本: {cuda_version or '未检测到'}")
    
    # 安装依赖
    cuda_version_arg = args.cuda
    if cuda_version_arg:
        print(f"使用指定的CUDA版本: {cuda_version_arg}")
    
    install_requirements(cuda_version_arg, args.extra)
    
    # 验证安装
    if not args.no_verify:
        print("\n验证安装...")
        verify_installation()
    
    print("\n安装完成！")
    print("\n可以通过以下命令开始训练:")
    print("python train.py --mode expert --domain security --use_4bit")

if __name__ == "__main__":
    main() 