"""
任务仓库 - 统一的数据库访问层
实现内存缓存和批量持久化策略
"""
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)


class TaskRepository:
    """
    任务仓库 - 管理任务的内存缓存和数据库持久化

    策略：
    1. 所有读写先通过内存缓存
    2. 定时批量写入数据库（默认5秒）
    3. 关键操作立即持久化
    4. LRU缓存策略避免内存溢出
    """

    def __init__(self, max_cache_size: int = 1000, flush_interval: int = 5):
        # 内存缓存（使用OrderedDict实现LRU）
        self._cache: OrderedDict[str, Dict] = OrderedDict()
        self._max_cache_size = max_cache_size

        # 脏数据标记（需要持久化的任务ID）
        self._dirty_tasks: set = set()

        # 批量写入配置
        self._flush_interval = flush_interval  # 秒
        self._last_flush = datetime.now()
        self._flush_lock = threading.Lock()

        # 统计信息
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "db_reads": 0,
            "db_writes": 0,
            "batch_writes": 0
        }

        # 启动定时刷新任务
        self._start_flush_timer()

    def _start_flush_timer(self):
        """启动定时刷新任务"""
        async def flush_periodically():
            while True:
                await asyncio.sleep(self._flush_interval)
                await self.flush_dirty_tasks()

        # 在后台运行定时任务
        try:
            loop = asyncio.get_event_loop()
            asyncio.ensure_future(flush_periodically())
        except RuntimeError:
            # 如果没有事件循环，稍后再试
            pass

    async def get_task(self, task_id: str, db_session=None) -> Optional[Dict]:
        """
        获取任务 - 优先从缓存读取
        """
        # 1. 尝试从缓存获取
        if task_id in self._cache:
            # 更新LRU顺序
            self._cache.move_to_end(task_id)
            self._stats["cache_hits"] += 1
            return self._cache[task_id]

        self._stats["cache_misses"] += 1

        # 2. 从数据库加载（如果提供了session）
        if db_session:
            task_data = await self._load_from_db(task_id, db_session)
            if task_data:
                self._add_to_cache(task_id, task_data)
                return task_data

        return None

    async def save_task(self, task_id: str, task_data: Dict, immediate: bool = False):
        """
        保存任务 - 写入缓存并标记为脏数据

        Args:
            task_id: 任务ID
            task_data: 任务数据
            immediate: 是否立即持久化到数据库
        """
        # 1. 更新缓存
        self._add_to_cache(task_id, task_data)

        # 2. 标记为脏数据
        self._dirty_tasks.add(task_id)

        # 3. 如果需要立即持久化
        if immediate:
            await self.flush_task(task_id)

    async def update_task_progress(self, task_id: str, progress: int,
                                  completed: int = 0, failed: int = 0):
        """
        更新任务进度 - 高频操作，仅更新缓存
        注意：这个函数保留用于简单的进度更新，复杂更新请使用project_manager
        """
        if task_id in self._cache:
            task = self._cache[task_id]
            # 更新新旧字段
            task["completion_percentage"] = progress
            task["progress"] = progress  # 兼容旧字段
            task["translated_rows"] = completed
            task["completed_tasks"] = completed  # 兼容旧字段
            task["failed_tasks"] = failed
            task["updated_at"] = datetime.utcnow()

            # 标记为脏数据
            self._dirty_tasks.add(task_id)

            # 移到LRU末尾
            self._cache.move_to_end(task_id)

    async def update_task_status(self, task_id: str, status: str,
                                error_msg: str = None, immediate: bool = True):
        """
        更新任务状态 - 关键操作，默认立即持久化
        """
        if task_id in self._cache:
            task = self._cache[task_id]
            task["status"] = status
            task["updated_at"] = datetime.utcnow()

            if error_msg:
                task["error_message"] = error_msg

            # 状态变更需要立即持久化
            if immediate:
                await self.flush_task(task_id)
            else:
                self._dirty_tasks.add(task_id)

    async def list_tasks(self, status: Optional[str] = None,
                         limit: int = 20, offset: int = 0) -> List[Dict]:
        """
        列出任务 - 从缓存中筛选
        """
        all_tasks = list(self._cache.values())

        # 按状态过滤
        if status:
            filtered = [t for t in all_tasks if t.get("status") == status]
        else:
            filtered = all_tasks

        # 按创建时间降序排序
        filtered.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)

        # 分页
        return filtered[offset:offset + limit]

    def get_task_count(self, status: Optional[str] = None) -> int:
        """获取任务数量"""
        if status:
            return sum(1 for t in self._cache.values() if t.get("status") == status)
        return len(self._cache)

    async def flush_task(self, task_id: str, db_session=None):
        """
        立即持久化单个任务
        """
        if task_id not in self._cache:
            return

        if not db_session:
            logger.warning(f"无法持久化任务 {task_id}：未提供数据库会话")
            return

        task_data = self._cache[task_id]

        try:
            await self._save_to_db(task_id, task_data, db_session)
            self._dirty_tasks.discard(task_id)
            self._stats["db_writes"] += 1

            logger.debug(f"任务 {task_id} 已持久化到数据库")
        except Exception as e:
            logger.error(f"持久化任务 {task_id} 失败: {e}")

    async def flush_dirty_tasks(self, db_session=None):
        """
        批量持久化脏数据
        """
        if not self._dirty_tasks:
            return

        if not db_session:
            logger.debug("跳过批量持久化：未提供数据库会话")
            return

        with self._flush_lock:
            tasks_to_flush = list(self._dirty_tasks)

        if not tasks_to_flush:
            return

        logger.info(f"批量持久化 {len(tasks_to_flush)} 个任务")

        success_count = 0
        for task_id in tasks_to_flush:
            if task_id in self._cache:
                try:
                    await self._save_to_db(task_id, self._cache[task_id], db_session)
                    self._dirty_tasks.discard(task_id)
                    success_count += 1
                except Exception as e:
                    logger.error(f"批量持久化任务 {task_id} 失败: {e}")

        self._stats["batch_writes"] += 1
        self._stats["db_writes"] += success_count

        logger.info(f"批量持久化完成: {success_count}/{len(tasks_to_flush)} 成功")

    def _add_to_cache(self, task_id: str, task_data: Dict):
        """添加到缓存（LRU策略）"""
        # 如果缓存已满，删除最旧的项
        if len(self._cache) >= self._max_cache_size:
            # 删除最旧的项（但不删除脏数据）
            for old_id in list(self._cache.keys()):
                if old_id not in self._dirty_tasks:
                    del self._cache[old_id]
                    break
                if len(self._cache) >= self._max_cache_size * 1.2:
                    # 紧急情况：强制删除
                    del self._cache[old_id]
                    self._dirty_tasks.discard(old_id)
                    break

        self._cache[task_id] = task_data
        self._cache.move_to_end(task_id)  # 移到末尾（最新）

    async def _load_from_db(self, task_id: str, db_session) -> Optional[Dict]:
        """从数据库加载任务"""
        # TODO: 实现实际的数据库查询
        # 这里需要根据实际的数据库模型来实现
        self._stats["db_reads"] += 1

        try:
            from sqlalchemy import text
            result = await db_session.execute(
                text("SELECT * FROM translation_tasks WHERE id = :task_id"),
                {"task_id": task_id}
            )
            row = result.first()

            if row:
                return dict(row)
        except Exception as e:
            logger.error(f"从数据库加载任务 {task_id} 失败: {e}")

        return None

    async def _save_to_db(self, task_id: str, task_data: Dict, db_session):
        """保存任务到数据库"""
        # TODO: 实现实际的数据库保存
        # 这里需要根据实际的数据库模型来实现

        try:
            from sqlalchemy import text

            # 简化的UPSERT操作
            await db_session.execute(
                text("""
                    INSERT INTO translation_tasks (id, status, created_at, updated_at, data)
                    VALUES (:id, :status, :created_at, :updated_at, :data)
                    ON DUPLICATE KEY UPDATE
                        status = VALUES(status),
                        updated_at = VALUES(updated_at),
                        data = VALUES(data)
                """),
                {
                    "id": task_id,
                    "status": task_data.get("status"),
                    "created_at": task_data.get("created_at"),
                    "updated_at": task_data.get("updated_at", datetime.utcnow()),
                    "data": json.dumps(task_data)  # 将完整数据存为JSON
                }
            )
            await db_session.commit()
        except Exception as e:
            logger.error(f"保存任务 {task_id} 到数据库失败: {e}")
            raise

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            **self._stats,
            "cache_size": len(self._cache),
            "dirty_count": len(self._dirty_tasks),
            "cache_hit_rate": self._stats["cache_hits"] / max(1, self._stats["cache_hits"] + self._stats["cache_misses"])
        }

    async def shutdown(self, db_session=None):
        """
        关闭时持久化所有脏数据
        """
        logger.info("正在关闭任务仓库，持久化所有脏数据...")
        await self.flush_dirty_tasks(db_session)
        logger.info("任务仓库已关闭")


# 全局实例
_task_repository: Optional[TaskRepository] = None


def get_task_repository() -> TaskRepository:
    """获取任务仓库单例"""
    global _task_repository
    if _task_repository is None:
        _task_repository = TaskRepository()
    return _task_repository


async def init_task_repository(db_session=None):
    """初始化任务仓库（加载现有任务）"""
    repo = get_task_repository()

    if db_session:
        try:
            # 加载最近的任务到缓存
            from sqlalchemy import text
            result = await db_session.execute(
                text("""
                    SELECT * FROM translation_tasks
                    WHERE created_at > :cutoff
                    ORDER BY created_at DESC
                    LIMIT 100
                """),
                {"cutoff": datetime.utcnow() - timedelta(days=7)}
            )

            for row in result:
                task_data = dict(row)
                if "data" in task_data and isinstance(task_data["data"], str):
                    # 解析JSON数据
                    task_data.update(json.loads(task_data["data"]))

                repo._cache[task_data["id"]] = task_data

            logger.info(f"从数据库加载了 {len(repo._cache)} 个最近的任务")
        except Exception as e:
            logger.error(f"初始化任务仓库失败: {e}")