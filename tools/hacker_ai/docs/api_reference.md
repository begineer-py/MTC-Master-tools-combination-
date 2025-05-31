# API参考

## Hugging Face API客户端

`huggingface_api_client.py` 提供了与Hugging Face API交互的接口。

### HuggingFaceClient类

用于调用Hugging Face推理API的客户端类。

```python
from utils.huggingface_api_client import HuggingFaceClient

# 初始化客户端
client = HuggingFaceClient(api_token="YOUR_HF_TOKEN")

# 调用模型
response = client.query_model(
    model_id="mistralai/Mistral-7B-Instruct-v0.2",
    prompt="解释SQL注入攻击",
    params={
        "temperature": 0.7,
        "max_length": 512
    }
)
```

#### 主要方法

- `__init__(api_token=None)`: 初始化客户端，如未提供token则尝试从环境变量获取
- `query_model(model_id, prompt, params=None)`: 向指定模型发送查询
- `query_security_model(prompt)`: 查询专门用于安全领域的模型

## 蒸馏脚本API

### 单一教师蒸馏

`scripts/distill_from_huggingface.py` 提供单一教师模型蒸馏功能。

#### 命令行参数

```
--student_model_path: 学生模型路径（必需）
--teacher_model_id: 教师模型ID（默认为deepseek-ai/deepseek-coder-33b-instruct）
--output_dir: 输出目录（默认为./distilled_model）
--num_samples: 从教师模型获取的样本数量（默认100）
--temperature: 教师模型生成时的温度（默认0.7）
--max_length: 生成回复的最大长度（默认512）
--use_4bit: 是否使用4位量化（默认否）
--use_lora: 是否使用LoRA参数高效微调（默认否）
--domain: 查询的领域类型 [security/coding/general]（默认security）
```

### 多教师蒸馏

`scripts/multi_teacher_distillation.py` 提供多教师模型混合蒸馏功能。

#### 命令行参数

```
--student_model_path: 学生模型路径（必需）
--output_dir: 输出目录（默认为./multi_distilled_model）
--teacher_models: 教师模型ID列表
--domain: 查询的领域类型 [security/coding/general/combined]（默认security）
--samples_per_model: 每个模型的样本数量（默认20）
--use_cached: 使用缓存的知识数据（默认否）
--use_4bit: 是否使用4位量化（默认否）
--use_lora: 是否使用LoRA参数高效微调（默认是）
```

### 启动脚本

`scripts/run_distillation.py` 提供简化的启动方式。

#### 命令行参数

```
--mode: 蒸馏模式 [single/multi/expert]（必需）
--student_model: 学生模型路径（默认为./deepseek-coder-1.3b）
--domain: 蒸馏领域 [security/coding/general/combined]（默认combined）
--output_dir: 输出目录（默认为./distilled_hacker_ai）
--use_4bit: 是否使用4位量化
--use_lora: 是否使用LoRA（默认是）
--hf_token: Hugging Face API令牌
--samples: 收集的样本总数（默认100）
--use_cached: 使用缓存的知识数据
```

## 配置文件API

### models_config.json

模型配置文件，定义可用的模型和它们的特性：

```json
{
  "teacher_models": [
    {
      "id": "mistralai/Mistral-7B-Instruct-v0.2",
      "description": "强大的开源指令模型",
      "domain": "general",
      "template": "<s>[INST] {prompt} [/INST]"
    },
    // 其他模型...
  ]
}
```

### training_config.json

训练配置文件，定义蒸馏过程中的训练参数：

```json
{
  "learning_rate": 2e-4,
  "num_train_epochs": 3,
  "per_device_train_batch_size": 4,
  "gradient_accumulation_steps": 4,
  "warmup_ratio": 0.05,
  "weight_decay": 0.01
}
``` 