"""
云存储抽象基类
"""
from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileMetadata:
    """文件元数据"""
    file_id: str
    original_name: str
    size: int
    mime_type: str
    upload_time: datetime
    user_id: str


class CloudStorage(ABC):
    """云存储抽象基类"""

    @abstractmethod
    async def upload(self, file: BinaryIO, file_path: str, metadata: Dict = None) -> str:
        """上传文件返回文件ID"""
        pass

    @abstractmethod
    async def upload_bytes(self, content: bytes, file_path: str, metadata: Dict = None) -> str:
        """上传字节内容"""
        pass

    @abstractmethod
    async def download(self, file_path: str) -> bytes:
        """下载文件"""
        pass

    @abstractmethod
    async def get_download_url(self, file_path: str, expire_seconds: int = 3600) -> str:
        """获取临时下载链接"""
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        pass

    @abstractmethod
    async def get_file_info(self, file_path: str) -> Optional[Dict]:
        """获取文件信息"""
        pass