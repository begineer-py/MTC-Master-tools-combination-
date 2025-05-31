#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试 LogConfig.logger
"""

try:
    from config.config import LogConfig
    print(f"LogConfig导入成功")
    
    if hasattr(LogConfig, "logger"):
        print(f"LogConfig.logger 存在")
        LogConfig.logger.info("This is a test log message")
        print(f"日志测试完成")
    else:
        print(f"Error: LogConfig.logger 不存在")
except Exception as e:
    print(f"发生错误: {e}") 