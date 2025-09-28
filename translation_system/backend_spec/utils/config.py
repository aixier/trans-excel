"""配置管理模块"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from loguru import logger


class ConfigManager:
    """配置管理器（单例模式）"""
    
    _instance: Optional['ConfigManager'] = None
    _config: Dict[str, Any] = {}
    _env: str = 'development'
    
    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载配置文件"""
        # 确定环境
        self._env = os.getenv('ENV', 'development')
        logger.info(f"运行环境: {self._env}")
        
        # 加载配置文件
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            logger.info("配置文件加载成功")
            
            # 合并环境特定配置
            if self._env in self._config:
                env_config = self._config[self._env]
                self._merge_config(self._config, env_config)
                
            # 处理环境变量覆盖
            self._process_env_vars()
            
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            raise
    
    def _merge_config(self, base: Dict, override: Dict):
        """递归合并配置"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _process_env_vars(self):
        """处理环境变量覆盖"""
        # API端口
        if 'API_PORT' in os.environ:
            self._config['api']['port'] = int(os.environ['API_PORT'])
        
        # 日志级别
        if 'LOG_LEVEL' in os.environ:
            self._config['logging']['level'] = os.environ['LOG_LEVEL']
        
        # 数据库URL
        if 'DATABASE_URL' in os.environ:
            if 'database' not in self._config:
                self._config['database'] = {}
            self._config['database']['url'] = os.environ['DATABASE_URL']
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号路径）"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值（支持点号路径）"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @property
    def env(self) -> str:
        """获取当前环境"""
        return self._env
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self._env == 'development'
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self._env == 'production'
    
    def to_dict(self) -> Dict[str, Any]:
        """获取完整配置字典"""
        return self._config.copy()


# 创建全局配置实例
config = ConfigManager()
