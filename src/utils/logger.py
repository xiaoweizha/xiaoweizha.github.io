"""
日志管理模块

统一的日志配置和管理。
"""

import sys
import logging
from typing import Any, Dict, Optional
from pathlib import Path
import structlog
from structlog import processors, dev


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None
) -> None:
    """
    设置日志配置

    Args:
        level: 日志级别
        format_type: 日志格式 (json/console)
        log_file: 日志文件路径
    """
    # 设置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 配置处理器
    processors_list = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        processors.TimeStamper(fmt="iso"),
        processors.StackInfoRenderer(),
        processors.format_exc_info,
        processors.UnicodeDecoder(),
    ]

    if format_type == "console":
        processors_list.append(dev.ConsoleRenderer(colors=True))
    else:
        processors_list.append(processors.JSONRenderer())

    # 配置structlog
    structlog.configure(
        processors=processors_list,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 配置标准库logging
    handlers = []

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    handlers.append(console_handler)

    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        handlers.append(file_handler)

    # 配置根日志器
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=handlers
    )

    # 设置第三方库日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    获取日志器

    Args:
        name: 日志器名称

    Returns:
        结构化日志器
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    日志器混入类

    为类提供统一的日志功能。
    """

    @property
    def logger(self) -> structlog.BoundLogger:
        """获取类日志器"""
        return get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def log_method_call(self, method_name: str, **kwargs) -> None:
        """记录方法调用"""
        self.logger.debug(
            f"调用方法: {method_name}",
            **kwargs
        )

    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """记录错误"""
        self.logger.error(
            f"发生错误: {str(error)}",
            error_type=type(error).__name__,
            **(context or {})
        )

    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """记录性能指标"""
        self.logger.info(
            f"性能指标: {operation}",
            duration=duration,
            **kwargs
        )