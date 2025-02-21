# theHarvester 扫描模块

这个模块提供了对 theHarvester 工具的 Python 封装，使其能够在 WSL 环境中运行并获取结果。

## 前提条件

1. 安装 WSL
2. 安装 Kali Linux WSL
3. 在 Kali Linux 中安装 theHarvester：
   ```bash
   apt-get update
   apt-get install -y theharvester
   ```

## 使用方法

```python
from reconnaissance.theHarvester import HarvesterScanner

# 创建扫描器实例
scanner = HarvesterScanner()

# 运行扫描
result = scanner.run_harvester(
    domain='example.com',  # 目标域名
    limit=100,            # 结果限制数（默认100）
    sources='all'         # 数据源（默认'all'）
)

# 打印结果
print(result)
```

## 可用数据源

- all: 所有源
- baidu: 百度
- bing: 必应
- google: 谷歌
- linkedin: 领英
- twitter: 推特
- yahoo: 雅虎

## 返回结果格式

```python
{
    'status': 'success',  # 或 'error'
    'scan_time': '2024-02-16 19:30:00',
    'scan_sources': 'all',
    'limit': 100,
    'emails': [...],
    'hosts': [...],
    'urls': [...],
    'error': None  # 如果发生错误，这里会包含错误信息
}
```

## 错误处理

该模块会处理以下类型的错误：
1. WSL 执行错误
2. theHarvester 运行错误
3. 结果解析错误

所有错误都会被捕获并返回一个包含错误信息的字典。 