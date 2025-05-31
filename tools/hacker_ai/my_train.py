#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
import torch # Import torch early for CUDA check

class HackerAITrainer:
    def __init__(self):
        """初始化训练器，加载配置并设置参数"""
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化 HackerAITrainer...")

        self.config = self._load_config()
        self._load_parameters()

        # 在加载参数后执行检查
        if not self._check_dependencies():
             self.logger.error("依赖检查失败，请先安装依赖: python requirements/install.py")
             sys.exit(1)

        if not self._check_model_exists(self.student_model):
            sys.exit(1)

        self._ensure_output_dir()
        self.logger.info("HackerAITrainer 初始化完成.")

    def _setup_logging(self):
        """配置日志记录器"""
        log_file = "./logs/hacker_ai_train.log"
        # 确保日志文件目录存在 (如果需要)
        # log_dir = Path(log_file).parent
        # log_dir.mkdir(parents=True, exist_ok=True) # 如果日志文件不在当前目录

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'), # 指定编码
                logging.StreamHandler(sys.stdout)
            ]
        )

    def _load_config(self):
        """从配置文件加载训练参数"""
        config_path = Path(__file__).parent / "configs" / "training_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.info(f"已成功加载配置文件: {config_path}")
            return config
        except FileNotFoundError:
            self.logger.error(f"配置文件未找到: {config_path}")
            self.logger.error("将使用默认参数。")
            return {} # 返回空字典而不是None，简化get_param逻辑
        except json.JSONDecodeError as e:
            self.logger.error(f"解析配置文件失败: {e}")
            self.logger.error("将使用默认参数。")
            return {}
        except Exception as e:
            self.logger.error(f"加载配置文件时发生未知错误: {e}")
            self.logger.error("将使用默认参数。")
            return {}

    def _get_param(self, param_path, default_value=None):
        """从配置中获取参数，支持层级路径如 'training.mode'"""
        parts = param_path.split('.')
        value = self.config
        try:
            for part in parts:
                if not isinstance(value, dict): # 检查是否可以索引
                     raise TypeError(f"配置路径 '{param_path}' 中的 '{part}' 之前的元素不是字典")
                value = value[part]
            return value
        except (KeyError, TypeError):
            self.logger.warning(f"配置中未找到参数 '{param_path}' 或路径无效，使用默认值: {default_value}")
            return default_value

    def _load_parameters(self):
        """从配置加载所有训练参数"""
        self.logger.info("加载训练参数...")
        # 训练模式: "single", "multi", 或 "expert"
        self.train_mode = self._get_param("training.mode", "expert")

        # 学生模型路径
        self.student_model = self._get_param("training.student_model", "./models/student/deepseek-coder-1.3b")

        # 训练领域: "security", "coding", "general", 或 "combined"
        self.domain = self._get_param("training.domain", "security")

        # 输出目录
        self.output_dir = self._get_param("training.output_dir", "./models/trained/hacker_ai")

        # 是否使用4位量化
        self.use_4bit = self._get_param("training.use_4bit", True)

        # 是否使用LoRA训练
        self.use_lora = self._get_param("training.use_lora", True)

        # Hugging Face API令牌（如果没有可以留空）
        self.hf_token = self._get_param("training.hf_token", "")

        # 单教师模式下的教师模型
        self.teacher_model = self._get_param("models.teacher_model", "mistralai/Mistral-7B-Instruct-v0.2")

        # 训练样本总数
        self.samples = self._get_param("training.samples", 500)

        # 训练批次大小
        self.batch_size = self._get_param("training.batch_size", 4)

        # 训练轮次
        self.epochs = self._get_param("training.epochs", 3)

        # 学习率
        self.learning_rate = self._get_param("training.learning_rate", 2e-4)

        # 是否使用缓存的知识数据
        self.use_cached = self._get_param("training.use_cached", True)

        # 专家模型 (用于 expert 模式)
        self.expert_models = self._get_param("models.expert_models", {})
        self.security_expert = self.expert_models.get("security", "mistralai/Mistral-7B-Instruct-v0.2")
        self.coding_expert = self.expert_models.get("coding", "meta-llama/Llama-2-7b-chat-hf")
        self.general_expert = self.expert_models.get("general", "openchat/openchat-3.5-0106")

        # 单教师训练特定配置
        self.single_config = self._get_param("single_teacher", {})
        self.single_lr = self.single_config.get("learning_rate", self.learning_rate)
        self.single_epochs = self.single_config.get("num_train_epochs", self.epochs)
        self.single_batch_size = self.single_config.get("per_device_train_batch_size", self.batch_size)

        # 多教师训练特定配置
        self.multi_config = self._get_param("multi_teacher", {})
        self.multi_lr = self.multi_config.get("learning_rate", self.learning_rate)
        self.multi_epochs = self.multi_config.get("num_train_epochs", self.epochs)
        self.multi_batch_size = self.multi_config.get("per_device_train_batch_size", self.batch_size)

        self.logger.info("训练参数加载完成.")
        self.logger.info(f"  训练模式: {self.train_mode}")
        self.logger.info(f"  学生模型: {self.student_model}")
        self.logger.info(f"  输出目录: {self.output_dir}")


    def _check_dependencies(self):
        """快速检查关键依赖"""
        self.logger.info("检查关键依赖...")
        try:
            import transformers # 检查 transformers
            self.logger.info(f"  torch version: {torch.__version__}")
            self.logger.info(f"  transformers version: {transformers.__version__}")

            # 快速检查CUDA
            if torch.cuda.is_available():
                self.logger.info(f"  CUDA可用: {torch.cuda.get_device_name(0)}")
            else:
                self.logger.warning("  CUDA不可用，将使用CPU训练（非常慢）")

            self.logger.info("依赖检查通过.")
            return True
        except ImportError as e:
            self.logger.error(f"缺少关键依赖: {e}")
            return False
        except Exception as e:
            self.logger.error(f"检查依赖时发生错误: {e}", exc_info=True) # 添加堆栈跟踪
            return False


    def _check_model_exists(self, model_path):
        """检查模型路径是否存在"""
        self.logger.info(f"检查模型路径: {model_path}")
        model_p = Path(model_path)
        if not model_p.exists() or not model_p.is_dir():
            self.logger.error(f"模型路径不存在或不是一个目录: {model_path}")
            self.logger.error("请确保已下载模型或提供正确的路径。")
            return False
        self.logger.info("模型路径检查通过.")
        return True

    def _ensure_output_dir(self):
        """确保输出目录存在"""
        try:
            output_p = Path(self.output_dir)
            output_p.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"确保输出目录存在: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"创建输出目录失败: {self.output_dir} - {e}", exc_info=True)
            sys.exit(1) # 如果无法创建输出目录，则退出

    def _run_command(self, cmd):
        """执行子进程命令并记录输出"""
        self.logger.info(f"执行命令: {' '.join(cmd)}")
        try:
            # 使用 Popen 实时捕获输出 (如果需要更详细的日志)
            # process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            # while True:
            #     output = process.stdout.readline()
            #     if output == '' and process.poll() is not None:
            #         break
            #     if output:
            #         self.logger.info(output.strip())
            # rc = process.poll()
            # if rc != 0:
            #      raise subprocess.CalledProcessError(rc, cmd)

            # 或者使用 run (更简单，但输出在结束后才完整显示)
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            self.logger.info("命令标准输出:\n" + result.stdout)
            if result.stderr:
                 self.logger.warning("命令标准错误:\n" + result.stderr) # 使用 warning 级别记录 stderr
            self.logger.info("命令成功执行.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"命令执行失败，返回码: {e.returncode}")
            self.logger.error(f"命令: {' '.join(e.cmd)}")
            if e.stdout:
                 self.logger.error("标准输出:\n" + e.stdout)
            if e.stderr:
                 self.logger.error("标准错误:\n" + e.stderr)
            return False
        except FileNotFoundError:
            self.logger.error(f"命令执行失败: 找不到可执行文件 '{cmd[0]}'")
            self.logger.error("请确保 Python 环境和脚本路径正确。")
            return False
        except Exception as e:
            self.logger.error(f"执行命令时发生未知错误: {e}", exc_info=True)
            return False


    def _run_single_teacher_training(self):
        """运行单一教师模型训练"""
        self.logger.info(f"开始单一教师训练，教师模型: {self.teacher_model}")

        script_path = Path(__file__).parent / "scripts" / "distill_from_huggingface.py"

        cmd = [
            sys.executable, str(script_path),
            "--student_model_path", self.student_model,
            "--teacher_model_id", self.teacher_model,
            "--output_dir", self.output_dir,
            "--num_samples", str(self.samples),
            "--domain", self.domain,
            "--batch_size", str(self.single_batch_size),
            "--num_train_epochs", str(self.single_epochs),
            "--learning_rate", str(self.single_lr)
        ]

        if self.use_4bit:
            cmd.append("--use_4bit")

        if self.use_lora:
            cmd.append("--use_lora")

        if self.hf_token:
            cmd.extend(["--hf_token", self.hf_token])

        return self._run_command(cmd)

    def _run_multi_teacher_training(self):
        """运行多教师模型训练"""
        self.logger.info("开始多教师训练")

        script_path = Path(__file__).parent / "scripts" / "multi_teacher_distillation.py"

        # 计算每个模型的样本数 (假设有7个内置模型，如果不是expert模式)
        # TODO: 让 multi_teacher_distillation.py 脚本自己处理内置模型列表和样本分配可能更健壮
        num_teachers = 7 # 假设值
        samples_per_model = self.samples // num_teachers if num_teachers > 0 else self.samples
        if samples_per_model == 0 and self.samples > 0:
             samples_per_model = 1 # 至少分配1个样本
             self.logger.warning(f"总样本数 {self.samples} 小于教师数量 {num_teachers}，每个教师至少分配 1 个样本。")


        cmd = [
            sys.executable, str(script_path),
            "--student_model_path", self.student_model,
            "--output_dir", self.output_dir,
            "--samples_per_model", str(samples_per_model),
            "--domain", self.domain,
            "--batch_size", str(self.multi_batch_size),
            "--num_train_epochs", str(self.multi_epochs),
            "--learning_rate", str(self.multi_lr)
        ]

        if self.use_4bit:
            cmd.append("--use_4bit")

        if self.use_lora:
            cmd.append("--use_lora")

        if self.hf_token:
            cmd.extend(["--hf_token", self.hf_token])

        if self.use_cached:
            cmd.append("--use_cached")

        return self._run_command(cmd)

    def _run_expert_training(self):
        """运行专家模型组合训练"""
        self.logger.info("开始专家模型组合训练")

        script_path = Path(__file__).parent / "scripts" / "multi_teacher_distillation.py"

        expert_teachers = [self.security_expert, self.coding_expert, self.general_expert]
        num_experts = len(expert_teachers)
        if num_experts == 0:
            self.logger.error("专家模型列表为空，无法进行专家训练。")
            return False

        samples_per_expert = self.samples // num_experts if num_experts > 0 else self.samples
        if samples_per_expert == 0 and self.samples > 0:
             samples_per_expert = 1 # 至少分配1个样本
             self.logger.warning(f"总样本数 {self.samples} 小于专家数量 {num_experts}，每个专家至少分配 1 个样本。")


        cmd = [
            sys.executable, str(script_path),
            "--student_model_path", self.student_model,
            "--output_dir", self.output_dir,
            "--samples_per_model", str(samples_per_expert),
            "--domain", "combined",  # 专家模式通常使用综合领域
            "--teacher_models", *expert_teachers, # 使用 * 解包列表
            "--batch_size", str(self.multi_batch_size), # 使用 multi 配置或 expert 特定配置
            "--num_train_epochs", str(self.multi_epochs),
            "--learning_rate", str(self.multi_lr),
            "--custom_models"  # 告知脚本使用提供的模型列表
        ]

        if self.use_4bit:
            cmd.append("--use_4bit")

        if self.use_lora:
            cmd.append("--use_lora")

        if self.hf_token:
            cmd.extend(["--hf_token", self.hf_token])

        if self.use_cached:
            cmd.append("--use_cached")

        return self._run_command(cmd)

    def run(self):
        """运行主训练流程"""
        self.logger.info("=== 开始训练我的黑客AI模型 ===")
        self.logger.info(f"训练模式: {self.train_mode}")

        # 检查已在 __init__ 中完成

        success = False
        try:
            if self.train_mode == "single":
                success = self._run_single_teacher_training()
            elif self.train_mode == "multi":
                success = self._run_multi_teacher_training()
            elif self.train_mode == "expert":
                success = self._run_expert_training()
            else:
                self.logger.error(f"未知的训练模式: {self.train_mode}")
                sys.exit(1)

            if success:
                self.logger.info(f"训练完成！模型已保存到 {self.output_dir}")
                self.logger.info("可以使用这个模型进行黑客安全领域的工作")
            else:
                self.logger.error("训练过程失败")
                sys.exit(1)
        except Exception as e:
             self.logger.error(f"训练过程中发生意外错误: {e}", exc_info=True)
             sys.exit(1)


if __name__ == "__main__":
    try:
        trainer = HackerAITrainer()
        trainer.run()
    except SystemExit as e:
         # 捕获 sys.exit() 以便脚本可以正常退出而不是抛出异常
         # 日志记录应已在发生错误的地方完成
         sys.exit(e.code) # 保持退出码
    except Exception as e:
         # 捕获初始化或其他未处理的异常
         logging.critical(f"启动训练器时发生严重错误: {e}", exc_info=True) # 使用 critical 级别
         sys.exit(1) # 以错误状态退出