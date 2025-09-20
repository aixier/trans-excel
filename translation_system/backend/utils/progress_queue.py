"""
进度更新队列管理器
批量缓存进度更新，定期同步到数据库
减少频繁的数据库操作，提高系统性能
"""
import threading
import queue
import time
import logging
import json
from typing import Dict, Any
from datetime import datetime, timezone
import pymysql
from config.settings import settings

logger = logging.getLogger(__name__)


class ProgressQueueManager:
    """
    进度队列管理器 - 单例模式
    缓存进度更新，批量写入数据库
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.queue = queue.Queue(maxsize=1000)
            self.progress_cache = {}  # 缓存最新进度
            self.running = False
            self.worker_thread = None
            self.flush_interval = 2  # 每2秒批量更新
            self.batch_size = 50  # 批量更新大小

            # 同步数据库连接
            self.db_config = {
                'host': settings.mysql_host,
                'port': settings.mysql_port,
                'user': settings.mysql_user,
                'password': settings.mysql_password,
                'database': settings.mysql_database,
                'charset': 'utf8mb4',
                'autocommit': True,
                'cursorclass': pymysql.cursors.DictCursor
            }

    def start(self):
        """启动队列处理线程"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            logger.info("✅ 进度队列管理器已启动")

    def stop(self):
        """停止队列处理"""
        if self.running:
            self.running = False
            # 最后一次刷新
            self._flush_to_db()
            if self.worker_thread:
                self.worker_thread.join(timeout=5)
            logger.info("✅ 进度队列管理器已停止")

    def add_progress(self, task_id: str, progress_data: Dict[str, Any]):
        """
        添加进度更新到队列
        progress_data包含: translated_rows, current_iteration, api_calls, tokens_used等
        """
        try:
            # 更新缓存
            if task_id not in self.progress_cache:
                self.progress_cache[task_id] = {
                    'translated_rows': 0,
                    'total_api_calls': 0,
                    'total_tokens_used': 0,
                    'total_cost': 0.0,
                    'updated_at': datetime.now(timezone.utc)
                }

            cache = self.progress_cache[task_id]

            # 累加统计值
            if 'api_calls' in progress_data:
                cache['total_api_calls'] += progress_data['api_calls']
            if 'tokens_used' in progress_data:
                cache['total_tokens_used'] += progress_data['tokens_used']
            if 'cost' in progress_data:
                cache['total_cost'] += progress_data['cost']

            # 更新其他值
            for key in ['translated_rows', 'current_iteration', 'status',
                       'current_sheet', 'error_message', 'sheet_progress']:
                if key in progress_data:
                    cache[key] = progress_data[key]

            cache['updated_at'] = datetime.now(timezone.utc)

            # 添加到队列（非阻塞）
            self.queue.put_nowait((task_id, cache.copy()))

        except queue.Full:
            # 队列满时直接更新数据库
            self._flush_to_db()
            self.queue.put_nowait((task_id, cache.copy()))
        except Exception as e:
            logger.error(f"添加进度失败: {e}")

    def _worker(self):
        """后台工作线程，定期批量更新数据库"""
        last_flush = time.time()

        while self.running:
            try:
                current_time = time.time()

                # 定时刷新或队列达到批量大小
                if (current_time - last_flush >= self.flush_interval or
                    self.queue.qsize() >= self.batch_size):
                    self._flush_to_db()
                    last_flush = current_time

                # 短暂休眠避免CPU占用
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"进度队列工作线程错误: {e}")
                time.sleep(1)

    def _flush_to_db(self):
        """批量更新数据库"""
        if self.queue.empty():
            return

        updates = {}

        # 收集所有待更新数据
        while not self.queue.empty():
            try:
                task_id, progress = self.queue.get_nowait()
                updates[task_id] = progress
            except queue.Empty:
                break

        if not updates:
            return

        # 批量更新数据库
        connection = None
        try:
            connection = pymysql.connect(**self.db_config)
            with connection.cursor() as cursor:
                for task_id, progress in updates.items():
                    sql = """
                        UPDATE translation_tasks
                        SET translated_rows = %s,
                            current_iteration = %s,
                            total_api_calls = %s,
                            total_tokens_used = %s,
                            total_cost = %s,
                            status = %s,
                            current_sheet = %s,
                            error_message = %s,
                            sheet_progress = %s,
                            updated_at = %s
                        WHERE id = %s
                    """

                    params = (
                        progress.get('translated_rows', 0),
                        progress.get('current_iteration', 0),
                        progress.get('total_api_calls', 0),
                        progress.get('total_tokens_used', 0),
                        progress.get('total_cost', 0.0),
                        progress.get('status', 'translating'),
                        progress.get('current_sheet'),
                        progress.get('error_message'),
                        json.dumps(progress.get('sheet_progress', {})) if progress.get('sheet_progress') else None,
                        progress.get('updated_at', datetime.now(timezone.utc)),
                        task_id
                    )

                    cursor.execute(sql, params)

                    # 如果状态是completed，更新完成时间
                    if progress.get('status') == 'completed':
                        cursor.execute(
                            "UPDATE translation_tasks SET completed_at = %s WHERE id = %s",
                            (datetime.now(timezone.utc), task_id)
                        )

            connection.commit()
            logger.info(f"✅ 批量更新了 {len(updates)} 个任务进度")

        except pymysql.Error as e:
            logger.error(f"数据库更新失败: {e}")
            if connection:
                connection.rollback()
        except Exception as e:
            logger.error(f"批量更新异常: {e}")
        finally:
            if connection:
                connection.close()

    def get_progress(self, task_id: str) -> Dict[str, Any]:
        """获取缓存的进度信息"""
        return self.progress_cache.get(task_id, {})

    def force_flush(self):
        """强制刷新到数据库"""
        self._flush_to_db()


# 全局实例
progress_queue = ProgressQueueManager()


# 便捷函数
def update_task_progress(task_id: str, **kwargs):
    """
    更新任务进度的便捷函数

    参数:
        task_id: 任务ID
        **kwargs: 进度数据，如 translated_rows, api_calls, tokens_used等
    """
    progress_queue.add_progress(task_id, kwargs)


def start_progress_queue():
    """启动进度队列"""
    progress_queue.start()


def stop_progress_queue():
    """停止进度队列"""
    progress_queue.stop()