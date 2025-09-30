"""
Configuration management for Persistence Service
"""
import os
import yaml
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class ServiceSettings(BaseSettings):
    """Service configuration"""
    host: str = "0.0.0.0"
    port: int = 8011
    debug: bool = False


class BufferSettings(BaseSettings):
    """Buffer configuration"""
    max_buffer_size: int = 1000
    flush_interval: int = 30


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = "ai_terminal"
    pool_size: int = 10
    pool_min_size: int = 5
    pool_recycle: int = 3600


class LoggingSettings(BaseSettings):
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/persistence_service.log"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5


class Settings:
    """Global settings manager"""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize settings from config file or environment variables

        Args:
            config_file: Path to config YAML file
        """
        self.config_file = config_file or os.getenv(
            "PERSISTENCE_CONFIG",
            "config/config.yaml"
        )

        # Load from YAML if exists
        config_data = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config_data = yaml.safe_load(f) or {}

        # Initialize settings
        self.service = ServiceSettings(**config_data.get('service', {}))
        self.buffer = BufferSettings(**config_data.get('buffer', {}))
        self.database = DatabaseSettings(**config_data.get('database', {}))
        self.logging = LoggingSettings(**config_data.get('logging', {}))

        # Allow environment variable overrides
        self._apply_env_overrides()

    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        # Database overrides - support both DB_* and MYSQL_* prefixes
        db_host = os.getenv("DB_HOST") or os.getenv("MYSQL_HOST")
        if db_host:
            self.database.host = db_host

        db_port = os.getenv("DB_PORT") or os.getenv("MYSQL_PORT")
        if db_port:
            self.database.port = int(db_port)

        db_user = os.getenv("DB_USER") or os.getenv("MYSQL_USER")
        if db_user:
            self.database.user = db_user

        db_password = os.getenv("DB_PASSWORD") or os.getenv("MYSQL_PASSWORD")
        if db_password:
            self.database.password = db_password

        db_database = os.getenv("DB_DATABASE") or os.getenv("MYSQL_DATABASE")
        if db_database:
            self.database.database = db_database

        # Service overrides
        if os.getenv("SERVICE_HOST"):
            self.service.host = os.getenv("SERVICE_HOST")
        if os.getenv("SERVICE_PORT"):
            self.service.port = int(os.getenv("SERVICE_PORT"))
        if os.getenv("SERVICE_DEBUG"):
            self.service.debug = os.getenv("SERVICE_DEBUG").lower() == "true"

    def get_database_url(self) -> str:
        """Get database connection URL"""
        return (
            f"mysql://{self.database.user}:{self.database.password}@"
            f"{self.database.host}:{self.database.port}/{self.database.database}"
        )


# Global settings instance
settings = Settings()