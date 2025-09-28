"""日志配置模块"""

import sys
from pathlib import Path
from loguru import logger
import yaml


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def setup_logger():
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()
    
    # 加载配置
    config = load_config()
    log_config = config.get('logging', {})
    
    # 获取日志配置参数
    level = log_config.get('level', 'INFO')
    format_str = log_config.get('format', 
                                '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}')
    file_path = log_config.get('file_path', 'logs/app.log')
    rotation = log_config.get('rotation', '10 MB')
    retention = log_config.get('retention', '30 days')
    compression = log_config.get('compression', 'zip')
    
    # 确保日志目录存在
    log_dir = Path(file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=format_str,
        level=level,
        colorize=True
    )
    
    # 添加文件处理器
    logger.add(
        file_path,
        format=format_str,
        level=level,
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding='utf-8'
    )
    
    logger.info("日志系统初始化完成")
    return logger


# 初始化日志
setup_logger()
