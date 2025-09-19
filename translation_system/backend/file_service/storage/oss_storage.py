"""
阿里云OSS存储实现
"""
import oss2
from .base import CloudStorage
from typing import BinaryIO, Dict, Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class OSSStorage(CloudStorage):
    """阿里云OSS存储实现"""

    def __init__(self):
        auth = oss2.Auth(settings.oss_access_key_id, settings.oss_access_key_secret)
        self.bucket = oss2.Bucket(auth, settings.oss_endpoint, settings.oss_bucket_name)

    async def upload(self, file: BinaryIO, file_path: str, metadata: Dict = None) -> str:
        """上传文件返回文件路径"""
        try:
            headers = {}
            if metadata:
                headers.update(metadata)

            result = self.bucket.put_object(file_path, file, headers=headers)
            logger.info(f"文件上传成功: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"文件上传失败: {file_path}, 错误: {e}")
            raise

    async def upload_bytes(self, content: bytes, file_path: str, metadata: Dict = None) -> str:
        """上传字节内容"""
        try:
            headers = {}
            if metadata:
                headers.update(metadata)

            result = self.bucket.put_object(file_path, content, headers=headers)
            logger.info(f"字节内容上传成功: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"字节内容上传失败: {file_path}, 错误: {e}")
            raise

    async def download(self, file_path: str) -> bytes:
        """下载文件"""
        try:
            result = self.bucket.get_object(file_path)
            content = result.read()
            logger.info(f"文件下载成功: {file_path}")
            return content

        except Exception as e:
            logger.error(f"文件下载失败: {file_path}, 错误: {e}")
            raise

    async def get_download_url(self, file_path: str, expire_seconds: int = 3600) -> str:
        """获取临时下载链接"""
        try:
            url = self.bucket.sign_url('GET', file_path, expire_seconds)
            logger.info(f"生成下载链接: {file_path}")
            return url

        except Exception as e:
            logger.error(f"生成下载链接失败: {file_path}, 错误: {e}")
            raise

    async def delete(self, file_path: str) -> bool:
        """删除文件"""
        try:
            self.bucket.delete_object(file_path)
            logger.info(f"文件删除成功: {file_path}")
            return True

        except Exception as e:
            logger.error(f"文件删除失败: {file_path}, 错误: {e}")
            return False

    async def exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        try:
            return self.bucket.object_exists(file_path)
        except Exception as e:
            logger.error(f"检查文件存在失败: {file_path}, 错误: {e}")
            return False

    async def get_file_info(self, file_path: str) -> Optional[Dict]:
        """获取文件信息"""
        try:
            meta = self.bucket.head_object(file_path)
            return {
                'size': meta.content_length,
                'last_modified': meta.last_modified,
                'content_type': meta.content_type,
                'etag': meta.etag
            }
        except Exception as e:
            logger.error(f"获取文件信息失败: {file_path}, 错误: {e}")
            return None