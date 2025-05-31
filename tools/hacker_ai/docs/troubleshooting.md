# 黑客AI工具 - 问题排查指南

## 安装问题

### PyTorch 安装失败

**症状**：PyTorch安装超时或下载失败

**解决方案**：
1. 尝试手动安装PyTorch：
   ```bash
   # CUDA版本
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   
   # 仅CPU版本 (更小更快)
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```
   
2. 如果仍然超时，可以尝试从[PyTorch官网](https://pytorch.org/get-started/locally/)下载合适的wheel文件，然后手动安装。

### DeepSpeed 安装问题

**症状**：DeepSpeed安装失败，出现编译错误

**解决方案**：
1. DeepSpeed在Windows上需要特殊配置，通常需要安装MSVC编译器。
2. 如果不需要DeepSpeed功能，可以忽略此错误。项目的基本功能不依赖DeepSpeed。
3. 如果确实需要DeepSpeed，请参考[官方安装指南](https://www.deepspeed.ai/tutorials/advanced-install/)。

### 其他依赖安装问题

**症状**：某些依赖包安装失败

**解决方案**：
1. 确保您有最新的pip：
   ```bash
   python -m pip install --upgrade pip
   ```
2. 尝试单独安装失败的包：
   ```bash
   pip install <包名>
   ```
3. 如果某个包持续安装失败，可能与Python版本不兼容，请尝试更换Python版本（推荐3.9-3.10）。

## 运行问题

### 找不到模块

**症状**：`ModuleNotFoundError: No module named 'xxx'`

**解决方案**：
1. 确保已成功安装所有依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 检查Python环境是否正确：如果使用了虚拟环境，确保已激活。

### CUDA相关错误

**症状**：`RuntimeError: CUDA error: no kernel image is available for execution on the device`

**解决方案**：
1. 检查CUDA版本与PyTorch版本是否匹配
2. 尝试使用CPU模式：
   ```bash
   python run.py --no-cuda
   ```

### 内存不足错误

**症状**：`RuntimeError: CUDA out of memory`或者程序崩溃

**解决方案**：
1. 启用4位量化模式：
   ```bash
   python run.py distill --use_4bit
   ```
2. 使用更小的批处理大小：
   ```bash
   python run.py distill --batch_size 1
   ```
3. 尝试使用LoRA模式：
   ```bash
   python run.py distill --use_lora
   ```

## API访问问题

### Hugging Face API错误

**症状**：`APIError: Authorization header is invalid`

**解决方案**：
1. 确保您的HF令牌有效且权限正确
2. 通过环境变量设置令牌：
   ```bash
   # Windows
   set HF_API_TOKEN=your_token_here
   
   # Linux/Mac
   export HF_API_TOKEN=your_token_here
   ```

### API请求限制

**症状**：`TooManyRequestsError`或请求被拒绝

**解决方案**：
1. 减少并发请求数量
2. 增加请求之间的延迟
3. 使用缓存模式：
   ```bash
   python run.py distill --use_cached
   ```

## 如需进一步帮助

如果您遇到的问题未在此文档中列出，请：

1. 检查GitHub仓库的Issues页面是否有类似问题
2. 提交详细的问题报告，包括:
   - 错误信息
   - 系统环境(操作系统、Python版本)
   - 重现步骤 