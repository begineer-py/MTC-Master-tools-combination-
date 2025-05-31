#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import argparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="测试配置文件加载")
    parser.add_argument("--config", type=str, default="./configs/single_teacher_config.json",
                        help="配置文件路径")
    return parser.parse_args()

def load_config(config_path):
    """加载JSON配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"成功加载配置文件: {config_path}")
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        raise

def print_config(config):
    """打印配置信息"""
    print("\n===== 配置信息 =====")
    
    # 模型设置
    model_settings = config.get("model_settings", {})
    print("\n[模型设置]")
    for key, value in model_settings.items():
        print(f"{key}: {value}")
    
    # 蒸馏设置
    distillation_settings = config.get("distillation_settings", {})
    print("\n[蒸馏设置]")
    for key, value in distillation_settings.items():
        print(f"{key}: {value}")
    
    # 训练设置
    training_settings = config.get("training_settings", {})
    print("\n[训练设置]")
    for key, value in training_settings.items():
        print(f"{key}: {value}")
    
    # 领域设置
    domain_settings = config.get("domain_settings", {})
    print("\n[领域设置]")
    for key, value in domain_settings.items():
        print(f"{key}: {value}")
    
    # 专家模型（如果有）
    if "expert_models" in config:
        expert_models = config.get("expert_models", {})
        print("\n[专家模型]")
        for key, value in expert_models.items():
            print(f"{key}: {value}")
    
    print("\n===================\n")

def main():
    """主函数"""
    args = parse_args()
    
    # 测试加载单教师配置
    single_config = load_config(args.config)
    print_config(single_config)
    
    # 如果指定的是单教师配置，再测试加载多教师配置
    if args.config == "./configs/single_teacher_config.json":
        multi_config = load_config("./configs/multi_teacher_config.json")
        print_config(multi_config)

if __name__ == "__main__":
    main() 