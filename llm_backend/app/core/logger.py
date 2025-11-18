from loguru import logger
import sys
from pathlib import Path

log_dir = Path("logs") # 当前引用了该文件时的工作目录下的 logs 目录
log_dir.mkdir(exist_ok=True) # 如果 logs 目录不存在则创建, exist_ok=True 表示如果目录已经存在则不报错

logger.remove() # 移除默认的控制台输出

# 添加控制台输出
logger.add(
    sys.stdout, # 控制台输出, 即标准输出
    format='''<green>{time: YYYY-MM-DD HH:mm:ss SSS}</green> | 
              <level>{level: <8}</level> | 
              <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>
              ''',
    level="INFO"
)

# 添加文件输出
logger.add(
    "logs/app.log", # 普通日志文件
    rotation="20MB", # 日志文件大小超过20MB时轮转
    retention="7 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}", # 日志格式
    level="INFO",
    encoding="utf-8"
)

def get_logger(service: str):
    """获取带有服务名称的 logger"""
    return logger.bind(service=service)

def log_structured(event_type: str, data: dict):
    """结构化日志记录"""
    logger.info({"event_type": event_type, "data": data})