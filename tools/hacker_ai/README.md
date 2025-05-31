# 我的黑客AI训练工具

这是一个用于训练我自己的黑客安全领域AI模型的工具，从大型语言模型中提取安全知识，训练一个小型高效的黑客AI模型。

## 使用方法

1. 先安装依赖：
```bash
python requirements/install.py
```

2. 修改配置文件 `configs/training_config.json` 中的参数，主要参数：
```json
{
  "training": {
    "mode": "expert",       // 训练模式: "single", "multi", 或 "expert"
    "student_model": "./models/student/deepseek-coder-1.3b",
    "domain": "security",   // 训练领域
    "use_4bit": true,       // 是否使用4位量化
    "hf_token": ""          // Hugging Face API令牌（如需要）
  }
}
```

3. 开始训练：
```bash
python my_train.py
```

## 训练使用的模型

可以在 `configs/training_config.json` 文件中的 `models.expert_models` 部分配置专家模型：

```json
"expert_models": {
  "security": "mistralai/Mistral-7B-Instruct-v0.2",
  "coding": "meta-llama/Llama-2-7b-chat-hf",
  "general": "openchat/openchat-3.5-0106"
}
```

## 文件说明

- `my_train.py`: 训练脚本
- `configs/`: 配置文件目录
  - `training_config.json`: 训练参数配置
- `requirements/`: 依赖管理目录
  - `install.py`: 安装依赖脚本
  - `requirements.txt`: 依赖列表
- `scripts/`: 核心训练功能脚本
- `models/`: 模型存储目录 