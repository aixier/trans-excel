"""
Session缓存模块 - 基于diskcache实现多worker Session共享

此模块解决了SessionManager在多uvicorn worker环境下的进程隔离问题，
通过diskcache提供跨进程的Session元数据共享存储。

Architecture:
    ┌─────────────────────────────┐
    │  diskcache (跨worker共享)    │
    │  - session元数据             │
    │  - 状态信息                  │
    └─────────────────────────────┘
              ↕
    ┌─────────────────────────────┐
    │  内存 (单worker)             │
    │  - DataFrame (重数据)        │
    │  - 按需加载                  │
    └─────────────────────────────┘

Usage:
    from utils.session_cache import session_cache

    # 保存session元数据
    session_cache.set_session(session_id, session_dict)

    # 获取session元数据
    data = session_cache.get_session(session_id)

    # 检查session是否存在
    if session_cache.exists(session_id):
        ...
"""

from typing import Optional, Dict, Any
from pathlib import Path
import os
import logging

try:
    from diskcache import Cache
    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False
    print("WARNING: diskcache is not installed. Multi-worker session sharing will not work.")
    print("Install it with: pip install diskcache>=5.6.3")
    # Fallback to simple dict cache for single worker mode
    class Cache:
        def __init__(self, *args, **kwargs):
            self._data = {}

        def __setitem__(self, key, value):
            self._data[key] = value

        def __getitem__(self, key):
            return self._data[key]

        def __contains__(self, key):
            return key in self._data

        def __delitem__(self, key):
            del self._data[key]

        def __len__(self):
            return len(self._data)

        def __iter__(self):
            return iter(self._data)

        def get(self, key, default=None):
            return self._data.get(key, default)

        def clear(self):
            self._data.clear()

logger = logging.getLogger(__name__)


class SessionCache:
    """多worker共享的Session缓存（基于diskcache）

    Features:
        - 自动并发控制（基于SQLite WAL + 文件锁）
        - 跨进程共享（所有uvicorn worker可见）
        - 持久化存储（容器重启不丢失）
        - 自动序列化（支持dict/list等Python对象）

    Performance:
        - 读取: ~100,000 ops/sec
        - 写入: ~10,000 ops/sec
        - 满足监控查询（2秒/次）和状态更新（50次/秒）需求

    Attributes:
        cache: diskcache.Cache实例
    """

    def __init__(self):
        """初始化Session缓存

        缓存目录优先级：
        1. 环境变量 SESSION_CACHE_DIR
        2. 代码目录下的 data/sessions
        3. /tmp/translation_sessions (fallback)
        """
        cache_dir = self._get_cache_dir()

        logger.info(f"Initializing SessionCache at: {cache_dir}")

        # 初始化diskcache
        # timeout=1: 文件锁超时1秒（避免死锁）
        self.cache = Cache(str(cache_dir), timeout=1)

        logger.info(f"SessionCache initialized successfully (size: {len(self.cache)})")

    def _get_cache_dir(self) -> Path:
        """获取缓存目录路径

        Returns:
            Path: 缓存目录路径
        """
        # 优先使用环境变量
        cache_dir_str = os.getenv('SESSION_CACHE_DIR')
        if cache_dir_str:
            cache_dir = Path(cache_dir_str)
            cache_dir.mkdir(parents=True, exist_ok=True)
            return cache_dir

        # 使用代码目录下的data/sessions（跟随代码挂载持久化）
        try:
            base_dir = Path(__file__).parent.parent  # backend_v2/
            cache_dir = base_dir / 'data' / 'sessions'
            cache_dir.mkdir(parents=True, exist_ok=True)
            return cache_dir
        except Exception as e:
            logger.warning(f"Failed to create cache dir in code directory: {e}")
            # Fallback to /tmp
            cache_dir = Path('/tmp/translation_sessions')
            cache_dir.mkdir(parents=True, exist_ok=True)
            return cache_dir

    def set_session(self, session_id: str, session_dict: Dict[str, Any]) -> bool:
        """保存session元数据到缓存

        Args:
            session_id: Session ID
            session_dict: Session元数据字典（不包含DataFrame等重数据）

        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            key = f'session:{session_id}'
            self.cache[key] = session_dict
            logger.debug(f"Saved session to cache: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save session {session_id} to cache: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """从缓存获取session元数据

        Args:
            session_id: Session ID

        Returns:
            Optional[Dict]: Session元数据字典，不存在返回None
        """
        try:
            key = f'session:{session_id}'
            data = self.cache.get(key)
            if data:
                logger.debug(f"Retrieved session from cache: {session_id}")
            return data
        except Exception as e:
            logger.error(f"Failed to get session {session_id} from cache: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """从缓存删除session

        Args:
            session_id: Session ID

        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            deleted = False

            # Delete main session data
            key = f'session:{session_id}'
            if key in self.cache:
                del self.cache[key]
                deleted = True

            # ✅ Also delete realtime progress data (separate key)
            realtime_key = f'realtime_progress:{session_id}'
            if realtime_key in self.cache:
                del self.cache[realtime_key]
                deleted = True

            if deleted:
                logger.debug(f"Deleted session from cache: {session_id}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete session {session_id} from cache: {e}")
            return False

    def exists(self, session_id: str) -> bool:
        """检查session是否存在于缓存中

        Args:
            session_id: Session ID

        Returns:
            bool: 存在返回True，不存在返回False
        """
        try:
            key = f'session:{session_id}'
            return key in self.cache
        except Exception as e:
            logger.error(f"Failed to check session {session_id} existence: {e}")
            return False

    def clear_all(self) -> bool:
        """清空所有缓存（用于测试或维护）

        Warning:
            此操作会删除所有session数据，生产环境慎用

        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            self.cache.clear()
            logger.warning("Cleared all session cache")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    def get_all_session_ids(self) -> list:
        """获取所有缓存中的session ID列表

        Returns:
            list: Session ID列表
        """
        try:
            session_ids = []
            for key in self.cache:
                if isinstance(key, str) and key.startswith('session:'):
                    session_id = key[8:]  # 去掉 'session:' 前缀
                    session_ids.append(session_id)
            return session_ids
        except Exception as e:
            logger.error(f"Failed to get all session IDs: {e}")
            return []

    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """清理过期的session缓存

        Args:
            max_age_hours: 最大保留时间（小时），默认24小时

        Returns:
            int: 清理的session数量
        """
        from datetime import datetime, timedelta

        try:
            cleaned_count = 0
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

            for session_id in self.get_all_session_ids():
                session_data = self.get_session(session_id)
                if session_data:
                    last_accessed_str = session_data.get('last_accessed')
                    if last_accessed_str:
                        try:
                            last_accessed = datetime.fromisoformat(last_accessed_str)
                            if last_accessed < cutoff_time:
                                self.delete_session(session_id)
                                cleaned_count += 1
                        except (ValueError, TypeError):
                            pass

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired sessions")

            return cleaned_count
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0


# 全局单例
session_cache = SessionCache()
