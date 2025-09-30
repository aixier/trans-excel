"""
MySQL Database Connector with Connection Pooling
"""
import json
import logging
import aiomysql
from typing import List, Dict, Any, Optional
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)


class MySQLConnector:
    """
    MySQL connection pool manager
    Handles database connections, batch operations, and queries
    """

    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None

    async def initialize(self):
        """
        Initialize connection pool
        """
        try:
            logger.info("Initializing MySQL connection pool...")
            logger.info(f"Connecting to {settings.database.host}:{settings.database.port}/{settings.database.database}")

            self.pool = await aiomysql.create_pool(
                host=settings.database.host,
                port=settings.database.port,
                user=settings.database.user,
                password=settings.database.password,
                db=settings.database.database,
                minsize=1,  # Start with 1 connection to avoid initialization timeout
                maxsize=settings.database.pool_size,
                pool_recycle=settings.database.pool_recycle,
                autocommit=False,
                charset='utf8mb4',
                connect_timeout=30  # 30 seconds connection timeout
            )

            # Test connection
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    logger.info(f"Database connection test successful: {result}")

            logger.info(f"MySQL connection pool initialized (size: {settings.database.pool_min_size}-{settings.database.pool_size})")

        except Exception as e:
            logger.error(f"Failed to initialize MySQL connection pool: {e}")
            raise

    async def close(self):
        """
        Close connection pool
        """
        if self.pool:
            logger.info("Closing MySQL connection pool...")
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("MySQL connection pool closed")

    async def health_check(self) -> bool:
        """
        Health check - ping database

        Returns:
            True if database is healthy, False otherwise
        """
        try:
            if not self.pool:
                return False

            async with self.pool.acquire() as conn:
                await conn.ping()
            return True

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def batch_upsert_sessions(self, sessions: List[Dict]) -> int:
        """
        Batch insert/update sessions (idempotent)

        Uses INSERT ... ON DUPLICATE KEY UPDATE for idempotency

        Args:
            sessions: List of session dictionaries

        Returns:
            Number of affected rows
        """
        if not sessions:
            return 0

        try:
            sql = """
                INSERT INTO translation_sessions
                (session_id, filename, file_path, status, game_info, llm_provider,
                 metadata, total_tasks, completed_tasks, failed_tasks, processing_tasks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    updated_at = CURRENT_TIMESTAMP,
                    status = VALUES(status),
                    total_tasks = GREATEST(total_tasks, VALUES(total_tasks)),
                    completed_tasks = GREATEST(completed_tasks, VALUES(completed_tasks)),
                    failed_tasks = GREATEST(failed_tasks, VALUES(failed_tasks)),
                    processing_tasks = VALUES(processing_tasks),
                    metadata = VALUES(metadata)
            """

            # Prepare values
            values = []
            for s in sessions:
                # Serialize JSON fields
                game_info_json = json.dumps(s.get('game_info')) if s.get('game_info') else None
                metadata_json = json.dumps(s.get('metadata')) if s.get('metadata') else None

                values.append((
                    s['session_id'],
                    s['filename'],
                    s['file_path'],
                    s['status'],
                    game_info_json,
                    s['llm_provider'],
                    metadata_json,
                    s.get('total_tasks', 0),
                    s.get('completed_tasks', 0),
                    s.get('failed_tasks', 0),
                    s.get('processing_tasks', 0)
                ))

            # Execute batch insert
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    affected = await cursor.executemany(sql, values)
                    await conn.commit()
                    logger.info(f"Batch upserted {len(sessions)} sessions ({affected} rows affected)")
                    return affected

        except Exception as e:
            logger.error(f"Failed to batch upsert sessions: {e}")
            raise

    async def batch_upsert_tasks(self, tasks: List[Dict]) -> int:
        """
        Batch insert/update tasks (idempotent)

        Uses INSERT ... ON DUPLICATE KEY UPDATE for idempotency

        Args:
            tasks: List of task dictionaries

        Returns:
            Number of affected rows
        """
        if not tasks:
            return 0

        try:
            sql = """
                INSERT INTO translation_tasks
                (task_id, session_id, batch_id, sheet_name, row_index, column_name,
                 source_text, target_text, context, status, confidence, error_message,
                 retry_count, start_time, end_time, duration_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    updated_at = CURRENT_TIMESTAMP,
                    target_text = VALUES(target_text),
                    status = VALUES(status),
                    confidence = VALUES(confidence),
                    error_message = VALUES(error_message),
                    retry_count = GREATEST(retry_count, VALUES(retry_count)),
                    end_time = VALUES(end_time),
                    duration_ms = VALUES(duration_ms)
            """

            # Prepare values
            values = []
            for t in tasks:
                # Convert datetime objects to strings if present
                start_time = t.get('start_time')
                if isinstance(start_time, datetime):
                    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')

                end_time = t.get('end_time')
                if isinstance(end_time, datetime):
                    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')

                values.append((
                    t['task_id'],
                    t['session_id'],
                    t['batch_id'],
                    t['sheet_name'],
                    t['row_index'],
                    t['column_name'],
                    t['source_text'],
                    t.get('target_text'),
                    t.get('context'),
                    t['status'],
                    t.get('confidence'),
                    t.get('error_message'),
                    t.get('retry_count', 0),
                    start_time,
                    end_time,
                    t.get('duration_ms')
                ))

            # Execute batch insert
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    affected = await cursor.executemany(sql, values)
                    await conn.commit()
                    logger.info(f"Batch upserted {len(tasks)} tasks ({affected} rows affected)")
                    return affected

        except Exception as e:
            logger.error(f"Failed to batch upsert tasks: {e}")
            raise

    async def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """
        Get session by ID

        Args:
            session_id: Session ID

        Returns:
            Session dictionary or None
        """
        try:
            sql = "SELECT * FROM translation_sessions WHERE session_id = %s"

            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (session_id,))
                    result = await cursor.fetchone()

                    if result:
                        # Parse JSON fields
                        if result.get('game_info'):
                            result['game_info'] = json.loads(result['game_info'])
                        if result.get('metadata'):
                            result['metadata'] = json.loads(result['metadata'])

                    return result

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise

    async def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """
        Get task by ID

        Args:
            task_id: Task ID

        Returns:
            Task dictionary or None
        """
        try:
            sql = "SELECT * FROM translation_tasks WHERE task_id = %s"

            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (task_id,))
                    result = await cursor.fetchone()
                    return result

        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            raise

    async def get_incomplete_sessions(self) -> List[Dict]:
        """
        Get all incomplete sessions (pending or processing)

        Returns:
            List of session dictionaries
        """
        try:
            sql = """
                SELECT * FROM translation_sessions
                WHERE status IN ('pending', 'processing')
                ORDER BY created_at DESC
            """

            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql)
                    results = await cursor.fetchall()

                    # Parse JSON fields
                    for result in results:
                        if result.get('game_info'):
                            result['game_info'] = json.loads(result['game_info'])
                        if result.get('metadata'):
                            result['metadata'] = json.loads(result['metadata'])

                    return results

        except Exception as e:
            logger.error(f"Failed to get incomplete sessions: {e}")
            raise

    async def get_session_with_tasks(self, session_id: str) -> Dict:
        """
        Get session with all its incomplete tasks

        Args:
            session_id: Session ID

        Returns:
            Dictionary with session and tasks
        """
        try:
            # Get session
            session = await self.get_session_by_id(session_id)
            if not session:
                raise ValueError(f"Session not found: {session_id}")

            # Get incomplete tasks
            sql = """
                SELECT * FROM translation_tasks
                WHERE session_id = %s AND status IN ('pending', 'processing')
                ORDER BY row_index, column_name
            """

            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (session_id,))
                    tasks = await cursor.fetchall()

            return {
                'session': session,
                'tasks': tasks
            }

        except Exception as e:
            logger.error(f"Failed to get session with tasks {session_id}: {e}")
            raise

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session (cascade deletes tasks)

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        try:
            sql = "DELETE FROM translation_sessions WHERE session_id = %s"

            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    affected = await cursor.execute(sql, (session_id,))
                    await conn.commit()
                    logger.info(f"Deleted session {session_id} ({affected} rows)")
                    return affected > 0

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise

    async def query_sessions(
        self,
        filters: Dict[str, Any],
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Query sessions with pagination, filtering, and sorting

        Args:
            filters: Dictionary of filters (status, from_date, to_date, llm_provider)
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_by: Column to sort by
            order: Sort order ('asc' or 'desc')

        Returns:
            Dictionary with total count and items
        """
        try:
            # Build WHERE clause
            where_clauses = []
            params = []

            if filters.get('status'):
                where_clauses.append("status = %s")
                params.append(filters['status'])

            if filters.get('from_date'):
                where_clauses.append("created_at >= %s")
                params.append(filters['from_date'])

            if filters.get('to_date'):
                where_clauses.append("created_at <= %s")
                params.append(filters['to_date'])

            if filters.get('llm_provider'):
                where_clauses.append("llm_provider = %s")
                params.append(filters['llm_provider'])

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            # Validate sort_by to prevent SQL injection
            allowed_sort_columns = ['session_id', 'filename', 'status', 'created_at', 'updated_at']
            if sort_by not in allowed_sort_columns:
                sort_by = 'created_at'

            # Validate order
            order = order.upper() if order.upper() in ['ASC', 'DESC'] else 'DESC'

            # Query total count
            count_sql = f"SELECT COUNT(*) as total FROM translation_sessions WHERE {where_clause}"

            # Query items with pagination
            offset = (page - 1) * page_size
            query_sql = f"""
                SELECT * FROM translation_sessions
                WHERE {where_clause}
                ORDER BY {sort_by} {order}
                LIMIT %s OFFSET %s
            """
            query_params = params + [page_size, offset]

            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Get total count
                    await cursor.execute(count_sql, params)
                    count_result = await cursor.fetchone()
                    total = count_result['total']

                    # Get items
                    await cursor.execute(query_sql, query_params)
                    items = await cursor.fetchall()

                    # Parse JSON fields
                    for item in items:
                        if item.get('game_info'):
                            item['game_info'] = json.loads(item['game_info'])
                        if item.get('metadata'):
                            item['metadata'] = json.loads(item['metadata'])

                    return {
                        'total': total,
                        'items': items
                    }

        except Exception as e:
            logger.error(f"Failed to query sessions: {e}")
            raise

    async def query_tasks(
        self,
        filters: Dict[str, Any],
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Query tasks with pagination, filtering, and sorting

        Args:
            filters: Dictionary of filters (session_id, status, sheet_name, from_date, to_date)
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_by: Column to sort by
            order: Sort order ('asc' or 'desc')

        Returns:
            Dictionary with total count and items
        """
        try:
            # Build WHERE clause
            where_clauses = []
            params = []

            if filters.get('session_id'):
                where_clauses.append("session_id = %s")
                params.append(filters['session_id'])

            if filters.get('status'):
                where_clauses.append("status = %s")
                params.append(filters['status'])

            if filters.get('sheet_name'):
                where_clauses.append("sheet_name = %s")
                params.append(filters['sheet_name'])

            if filters.get('from_date'):
                where_clauses.append("created_at >= %s")
                params.append(filters['from_date'])

            if filters.get('to_date'):
                where_clauses.append("created_at <= %s")
                params.append(filters['to_date'])

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            # Validate sort_by to prevent SQL injection
            allowed_sort_columns = ['task_id', 'session_id', 'status', 'created_at', 'updated_at', 'row_index']
            if sort_by not in allowed_sort_columns:
                sort_by = 'created_at'

            # Validate order
            order = order.upper() if order.upper() in ['ASC', 'DESC'] else 'DESC'

            # Query total count
            count_sql = f"SELECT COUNT(*) as total FROM translation_tasks WHERE {where_clause}"

            # Query items with pagination
            offset = (page - 1) * page_size
            query_sql = f"""
                SELECT * FROM translation_tasks
                WHERE {where_clause}
                ORDER BY {sort_by} {order}
                LIMIT %s OFFSET %s
            """
            query_params = params + [page_size, offset]

            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Get total count
                    await cursor.execute(count_sql, params)
                    count_result = await cursor.fetchone()
                    total = count_result['total']

                    # Get items
                    await cursor.execute(query_sql, query_params)
                    items = await cursor.fetchall()

                    return {
                        'total': total,
                        'items': items
                    }

        except Exception as e:
            logger.error(f"Failed to query tasks: {e}")
            raise

    async def get_sessions_stats(self) -> Dict[str, Any]:
        """
        Get session statistics

        Returns:
            Dictionary with statistics
        """
        try:
            sql = """
                SELECT
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing_count,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
                FROM translation_sessions
            """

            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql)
                    result = await cursor.fetchone()
                    return result

        except Exception as e:
            logger.error(f"Failed to get sessions stats: {e}")
            raise

    async def get_tasks_stats(self) -> Dict[str, Any]:
        """
        Get task statistics

        Returns:
            Dictionary with statistics
        """
        try:
            sql = """
                SELECT
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing_count,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                    AVG(confidence) as avg_confidence,
                    AVG(duration_ms) as avg_duration_ms
                FROM translation_tasks
            """

            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql)
                    result = await cursor.fetchone()
                    return result

        except Exception as e:
            logger.error(f"Failed to get tasks stats: {e}")
            raise

    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database storage statistics

        Returns:
            Dictionary with storage statistics
        """
        try:
            sql = """
                SELECT
                    table_name,
                    table_rows,
                    ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
                FROM information_schema.tables
                WHERE table_schema = %s
                AND table_name IN ('translation_sessions', 'translation_tasks')
            """

            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (settings.database.database,))
                    results = await cursor.fetchall()

                    stats = {}
                    for result in results:
                        stats[result['table_name']] = {
                            'rows': result['table_rows'],
                            'size_mb': float(result['size_mb'])
                        }

                    return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            raise


# Global singleton instance
mysql_connector = MySQLConnector()