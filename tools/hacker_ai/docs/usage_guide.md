# 黑客AI知识蒸馏工具

这个工具集允许你利用Hugging Face的免费API来获取安全、编程和黑客知识，并通过知识蒸馏技术将这些知识转移到更小的本地模型中（如deepseek-coder-1.3b或任何其他本地模型）。

## 特点

- 支持从多个免费大型语言模型获取知识
- 专注于网络安全、渗透测试和安全编程领域
- 自动生成多样化的安全问题提示
- 支持LoRA参数高效微调
- 提供多种蒸馏模式:
  - 单一教师模型蒸馏
  - 多教师模型知识混合
  - 领域专家模型组合

## 依赖

```bash
pip install torch transformers peft datasets tqdm
```

## 快速开始

1. 准备一个学生模型（例如从Hugging Face下载的deepseek-coder-1.3b）
2. 获取Hugging Face API令牌（可选但推荐）
3. 运行蒸馏脚本

### 使用单一教师模型（最简单的方式）

```bash
python run_distillation.py --mode single --student_model ./deepseek-coder-1.3b --hf_token YOUR_HF_TOKEN --samples 50
```

### 使用多个教师模型（获取更多样的知识）

```bash
python run_distillation.py --mode multi --student_model ./deepseek-coder-1.3b --hf_token YOUR_HF_TOKEN --domain combined --samples 140
```

### 使用领域专家组合（特定领域知识更准确）

```bash
python run_distillation.py --mode expert --student_model ./deepseek-coder-1.3b --hf_token YOUR_HF_TOKEN --samples 90
```

## 参数说明

```
--mode: 蒸馏模式 (single/multi/expert)
--student_model: 学生模型路径（本地模型）
--domain: 蒸馏领域 (security/coding/general/combined)
--output_dir: 输出目录
--use_4bit: 是否使用4位量化
--use_lora: 是否使用LoRA参数高效微调（默认开启）
--hf_token: Hugging Face API令牌
--teacher_model: 单教师模式下的教师模型
--samples: 收集的样本总数
--use_cached: 使用缓存的知识数据
```

## 默认使用的免费模型

该工具默认使用以下免费可访问的Hugging Face模型:

1. openchat/openchat-3.5-0106
2. THUDM/chatglm3-6b (对中文支持良好)
3. Qwen/Qwen-7B-Chat (阿里巴巴的优秀开源模型)
4. 01-ai/Yi-6B-Chat (中英双语能力强)
5. mistralai/Mistral-7B-Instruct-v0.2 (强大的开源指令模型)
6. meta-llama/Llama-2-7b-chat-hf (Meta优秀的开源模型)
7. google/gemma-7b-it (Google开源指令模型)

## 高级用法

### 自定义脚本

本项目包含三个主要脚本：

1. `distill_from_huggingface.py` - 单一教师模型蒸馏
2. `multi_teacher_distillation.py` - 多教师模型混合蒸馏
3. `run_distillation.py` - 简化的启动脚本

你可以直接调用这些脚本，并根据需要配置更多高级参数。

### 使用缓存的知识数据

如果你已经运行过蒸馏并收集了知识数据，可以使用缓存的数据来节省API请求:

```bash
python run_distillation.py --mode multi --student_model ./deepseek-coder-1.3b --use_cached
```

### 自定义教师模型

你可以通过修改`multi_teacher_distillation.py`中的`DEFAULT_FREE_MODELS`列表来自定义教师模型。

## 常见问题

### API请求失败怎么办？

- 确保你的Hugging Face API令牌有效
- 尝试减少样本数量
- 使用`--use_cached`参数避免重复请求
- 检查是否达到了API请求限制

### 为什么要使用多个模型？

不同的模型在不同领域有各自的优势。通过组合多个模型的知识，可以获得更全面、更准确的领域知识。

### 为什么使用LoRA而不是全参数微调？

LoRA是一种参数高效的微调方法，可以大幅减少训练参数数量，节省显存，加快训练速度，同时保持良好的性能。

## 注意事项

- 本工具仅用于教育和研究目的
- 请遵守Hugging Face的使用条款
- 请合法合规地使用生成的模型和知识

## 许可

本项目使用MIT许可证。请注意，蒸馏得到的模型可能受到原始模型许可证的限制。 