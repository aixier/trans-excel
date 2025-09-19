"""
配置管理系统
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import os


class TranslationConfig(BaseSettings):
    """翻译系统配置类"""

    # 数据库配置
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str
    mysql_database: str = "translation_system"

    # OSS配置
    oss_access_key_id: str
    oss_access_key_secret: str
    oss_bucket_name: str
    oss_endpoint: str

    # LLM配置
    llm_provider: str = "dashscope"
    llm_model: str = "qwen-plus"
    llm_api_key: str
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 缓存配置 (可选，如未配置则使用内存缓存)
    redis_host: Optional[str] = None
    redis_port: Optional[int] = None
    redis_password: Optional[str] = ""
    redis_db: Optional[int] = 0

    @field_validator('redis_host', mode='before')
    @classmethod
    def validate_redis_host(cls, v):
        """验证Redis主机字段，空字符串转为None"""
        if v == "" or v is None:
            return None
        return v

    @field_validator('redis_port', 'redis_db', mode='before')
    @classmethod
    def validate_redis_int_fields(cls, v):
        """验证Redis整数字段，空字符串转为None"""
        if v == "" or v is None:
            return None
        return int(v)

    # 翻译配置
    default_batch_size: int = 3
    default_max_concurrent: int = 10
    default_max_iterations: int = 5
    default_target_languages: List[str] = ["pt", "th", "ind"]
    default_region_code: str = "na"

    # 应用配置
    app_name: str = "游戏本地化智能翻译系统"
    app_version: str = "1.0.0"
    debug: bool = False
    debug_mode: bool = False  # debug的别名
    server_port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # 允许额外字段

    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        return f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"

    @property
    def redis_url(self) -> str:
        """获取Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def use_redis(self) -> bool:
        """检查是否使用Redis缓存"""
        return bool(self.redis_host and self.redis_port)


# 全局配置实例
settings = TranslationConfig()