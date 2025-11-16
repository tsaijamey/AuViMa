"""
CDP日志配置

配置结构化日志记录器，用于CDP操作日志。
"""

import logging
import sys
from typing import Optional


class CDPLogger:
    """CDP日志管理器"""
    
    def __init__(self, name: str = "auvima.cdp", level: str = "INFO"):
        """
        初始化日志管理器
        
        Args:
            name: 日志器名称
            level: 日志级别
        """
        self.logger = logging.getLogger(name)
        self._setup_logger(level)
    
    def _setup_logger(self, level: str):
        """设置日志器配置"""
        # 清除已有的处理器
        self.logger.handlers.clear()
        
        # 设置日志级别
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # 创建格式化器
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(console_handler)
        
        # 防止日志传播到根日志器
        self.logger.propagate = False
    
    def debug(self, message: str, *args, **kwargs):
        """记录调试日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """记录信息日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """记录警告日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """记录错误日志"""
        self.logger.error(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """记录异常日志"""
        self.logger.exception(message, *args, **kwargs)


# 全局日志器实例
_logger: Optional[CDPLogger] = None


def get_logger(name: str = "auvima.cdp", level: str = "INFO") -> CDPLogger:
    """
    获取CDP日志器
    
    Args:
        name: 日志器名称
        level: 日志级别
        
    Returns:
        CDPLogger: 日志器实例
    """
    global _logger
    if _logger is None:
        _logger = CDPLogger(name, level)
    return _logger