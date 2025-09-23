"""
LLM配置管理器
管理多个LLM配置，支持动态切换
"""
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from .llm_factory import LLMFactory, LLMProvider
from .base_llm import BaseLLM


logger = logging.getLogger(__name__)


class LLMConfigManager:
    """LLM配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file or self._get_default_config_file()
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.active_profile: Optional[str] = None
        self._llm_instances: Dict[str, BaseLLM] = {}

        # 加载配置
        self.load_configs()

    def _get_default_config_file(self) -> str:
        """获取默认配置文件路径"""
        config_dir = Path(__file__).parent.parent / "config"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "llm_configs.json")

    def load_configs(self):
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.configs = data.get("profiles", {})
                    self.active_profile = data.get("active_profile")
                    logger.info(f"Loaded {len(self.configs)} LLM configurations")
            except Exception as e:
                logger.error(f"Failed to load LLM configs: {e}")
                self._load_default_configs()
        else:
            logger.info("Config file not found, loading defaults")
            self._load_default_configs()
            self.save_configs()

    def _load_default_configs(self):
        """加载默认配置"""
        self.configs = {
            "qwen-default": {
                "provider": "qwen",
                "model": "qwen-plus",
                "api_key": os.getenv("QWEN_API_KEY", ""),
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "temperature": 0.3,
                "max_tokens": 4000,
                "description": "阿里云通义千问Plus - 默认配置"
            },
            "qwen-max": {
                "provider": "qwen",
                "model": "qwen-max",
                "api_key": os.getenv("QWEN_API_KEY", ""),
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "temperature": 0.3,
                "max_tokens": 8000,
                "description": "阿里云通义千问Max - 高性能"
            },
            "qwen-turbo": {
                "provider": "qwen",
                "model": "qwen-turbo",
                "api_key": os.getenv("QWEN_API_KEY", ""),
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "temperature": 0.5,
                "max_tokens": 4000,
                "description": "阿里云通义千问Turbo - 快速响应"
            },
            "openai-gpt35": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "temperature": 0.3,
                "max_tokens": 4000,
                "description": "OpenAI GPT-3.5 Turbo"
            },
            "openai-gpt4": {
                "provider": "openai",
                "model": "gpt-4",
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "temperature": 0.3,
                "max_tokens": 4000,
                "description": "OpenAI GPT-4"
            },
            "gemini-pro": {
                "provider": "gemini",
                "model": "gemini-pro",
                "api_key": os.getenv("GEMINI_API_KEY", ""),
                "temperature": 0.3,
                "max_tokens": 4000,
                "description": "Google Gemini Pro"
            }
        }
        self.active_profile = "qwen-default"

    def save_configs(self):
        """保存配置到文件"""
        try:
            data = {
                "profiles": self.configs,
                "active_profile": self.active_profile
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved LLM configs to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save LLM configs: {e}")

    def add_profile(self, profile_name: str, config: Dict[str, Any]):
        """
        添加配置文件

        Args:
            profile_name: 配置名称
            config: 配置内容
        """
        # 验证配置
        provider = config.get("provider")
        if not provider:
            raise ValueError("Provider is required")

        if not LLMFactory.validate_config(provider, config):
            raise ValueError("Invalid configuration")

        self.configs[profile_name] = config
        self.save_configs()
        logger.info(f"Added LLM profile: {profile_name}")

    def remove_profile(self, profile_name: str):
        """删除配置文件"""
        if profile_name in self.configs:
            del self.configs[profile_name]
            # 清理缓存的实例
            if profile_name in self._llm_instances:
                del self._llm_instances[profile_name]
            # 如果删除的是当前激活的配置，重置
            if self.active_profile == profile_name:
                self.active_profile = None
            self.save_configs()
            logger.info(f"Removed LLM profile: {profile_name}")

    def get_profile(self, profile_name: str) -> Dict[str, Any]:
        """获取配置文件"""
        if profile_name not in self.configs:
            raise ValueError(f"Profile {profile_name} not found")
        return self.configs[profile_name].copy()

    def list_profiles(self) -> List[str]:
        """列出所有配置文件"""
        return list(self.configs.keys())

    def set_active_profile(self, profile_name: str):
        """设置活动配置文件"""
        if profile_name not in self.configs:
            raise ValueError(f"Profile {profile_name} not found")
        self.active_profile = profile_name
        self.save_configs()
        logger.info(f"Set active LLM profile: {profile_name}")

    def get_active_profile(self) -> Optional[str]:
        """获取活动配置文件名称"""
        return self.active_profile

    async def get_llm(self, profile_name: Optional[str] = None) -> BaseLLM:
        """
        获取LLM实例

        Args:
            profile_name: 配置名称，如果为None则使用活动配置

        Returns:
            BaseLLM: LLM实例
        """
        profile = profile_name or self.active_profile
        if not profile:
            raise ValueError("No profile specified and no active profile set")

        if profile not in self.configs:
            raise ValueError(f"Profile {profile} not found")

        # 检查缓存
        if profile not in self._llm_instances:
            config = self.configs[profile].copy()
            # 移除描述字段
            config.pop("description", None)
            # 创建LLM实例
            llm = LLMFactory.create_from_config(config)
            await llm.initialize()
            self._llm_instances[profile] = llm

        return self._llm_instances[profile]

    def update_api_key(self, profile_name: str, api_key: str):
        """
        更新API密钥

        Args:
            profile_name: 配置名称
            api_key: 新的API密钥
        """
        if profile_name not in self.configs:
            raise ValueError(f"Profile {profile_name} not found")

        self.configs[profile_name]["api_key"] = api_key
        # 清除缓存的实例，下次会重新创建
        if profile_name in self._llm_instances:
            del self._llm_instances[profile_name]
        self.save_configs()
        logger.info(f"Updated API key for profile: {profile_name}")

    def get_profile_info(self, profile_name: str) -> Dict[str, Any]:
        """
        获取配置文件详细信息

        Args:
            profile_name: 配置名称

        Returns:
            Dict: 配置信息
        """
        if profile_name not in self.configs:
            raise ValueError(f"Profile {profile_name} not found")

        config = self.configs[profile_name]
        provider = config.get("provider")

        # 获取提供商信息
        provider_info = LLMFactory.get_provider_info(provider)

        return {
            "profile_name": profile_name,
            "config": config,
            "provider_info": provider_info,
            "is_active": profile_name == self.active_profile,
            "has_api_key": bool(config.get("api_key"))
        }

    async def test_profile(self, profile_name: str) -> bool:
        """
        测试配置文件是否可用

        Args:
            profile_name: 配置名称

        Returns:
            bool: 是否可用
        """
        try:
            llm = await self.get_llm(profile_name)
            return await llm.health_check()
        except Exception as e:
            logger.error(f"Profile {profile_name} test failed: {e}")
            return False

    async def cleanup(self):
        """清理所有LLM实例"""
        for llm in self._llm_instances.values():
            await llm.close()
        self._llm_instances.clear()
        logger.info("Cleaned up all LLM instances")