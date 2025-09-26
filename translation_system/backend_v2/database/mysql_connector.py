"""MySQL connector with connection pool support."""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import aiomysql
from aiomysql import Pool, Connection
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class MySQLConnector:
    """MySQL database connector with connection pooling."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize MySQL connector.

        Args:
            config: Database configuration
        """
        self.config = config or self._get_default_config()
        self.pool: Optional[Pool] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self._initialized = False

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default database configuration from environment."""
        return {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'translation_system'),
            'minsize': int(os.getenv('MYSQL_POOL_MIN', 1)),
            'maxsize': int(os.getenv('MYSQL_POOL_MAX', 10)),
            'charset': 'utf8mb4',
            'autocommit': False,
            'echo': False
        }

    async def initialize(self):
        """Initialize connection pool."""
        if self._initialized:
            return

        try:
            self.pool = await aiomysql.create_pool(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                db=self.config['database'],
                minsize=self.config['minsize'],
                maxsize=self.config['maxsize'],
                charset=self.config['charset'],
                autocommit=self.config['autocommit']
            )
            self._initialized = True
            self.logger.info(f"MySQL connection pool initialized: {self.config['host']}:{self.config['port']}")

        except Exception as e:
            self.logger.error(f"Failed to initialize MySQL connection pool: {e}")
            raise

    async def close(self):
        """Close connection pool."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self._initialized = False
            self.logger.info("MySQL connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        if not self._initialized:
            await self.initialize()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                yield cursor

    @asynccontextmanager
    async def transaction(self):
        """Execute operations in a transaction."""
        if not self._initialized:
            await self.initialize()

        async with self.pool.acquire() as conn:
            await conn.begin()
            try:
                async with conn.cursor() as cursor:
                    yield cursor
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise

    async def execute(self, query: str, params: tuple = None) -> int:
        """
        Execute a query without returning results.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Number of affected rows
        """
        async with self.get_connection() as cursor:
            await cursor.execute(query, params)
            return cursor.rowcount

    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute multiple queries.

        Args:
            query: SQL query template
            params_list: List of parameter tuples

        Returns:
            Total number of affected rows
        """
        async with self.transaction() as cursor:
            await cursor.executemany(query, params_list)
            return cursor.rowcount

    async def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Row as dictionary or None
        """
        async with self.get_connection() as cursor:
            await cursor.execute(query, params)
            row = await cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    async def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Fetch all rows.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of rows as dictionaries
        """
        async with self.get_connection() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
            if rows:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []

    # Session management methods
    async def create_session(self, session_data: Dict[str, Any]) -> str:
        """
        Create a new translation session.

        Args:
            session_data: Session data

        Returns:
            Session ID
        """
        query = """
            INSERT INTO translation_sessions 
            (session_id, filename, file_path, status, game_info, llm_provider, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            session_data['session_id'],
            session_data['filename'],
            session_data.get('file_path', ''),
            session_data.get('status', 'created'),
            json.dumps(session_data.get('game_info', {})),
            session_data.get('llm_provider', ''),
            json.dumps(session_data.get('metadata', {}))
        )
        await self.execute(query, params)
        return session_data['session_id']

    async def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update session data."""
        set_clauses = []
        params = []

        for key, value in updates.items():
            if key in ['game_info', 'metadata']:
                value = json.dumps(value)
            set_clauses.append(f"{key} = %s")
            params.append(value)

        params.append(session_id)
        query = f"""
            UPDATE translation_sessions 
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE session_id = %s
        """
        await self.execute(query, tuple(params))

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        query = "SELECT * FROM translation_sessions WHERE session_id = %s"
        session = await self.fetch_one(query, (session_id,))
        if session:
            # Parse JSON fields
            if session.get('game_info'):
                session['game_info'] = json.loads(session['game_info'])
            if session.get('metadata'):
                session['metadata'] = json.loads(session['metadata'])
        return session

    # Task management methods
    async def insert_tasks(self, tasks: List[Dict[str, Any]]):
        """Bulk insert translation tasks."""
        if not tasks:
            return

        query = """
            INSERT INTO translation_tasks (
                task_id, session_id, batch_id, group_id, sheet_name,
                row_index, col_index, source_text, source_lang, target_lang,
                source_context, status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        params_list = []
        for task in tasks:
            params = (
                task['task_id'],
                task['session_id'],
                task.get('batch_id', ''),
                task.get('group_id', ''),
                task.get('sheet_name', ''),
                task.get('row', 0),
                task.get('col', 0),
                task['source_text'],
                task.get('source_lang', 'CH'),
                task.get('target_lang', 'PT'),
                task.get('source_context', ''),
                task.get('status', 'pending')
            )
            params_list.append(params)

        await self.execute_many(query, params_list)

    async def update_task(self, task_id: str, updates: Dict[str, Any]):
        """Update a single task."""
        set_clauses = []
        params = []

        # Handle special fields
        if 'start_time' in updates:
            set_clauses.append('started_at = %s')
            params.append(updates['start_time'])

        if 'end_time' in updates:
            set_clauses.append('completed_at = %s')
            params.append(updates['end_time'])

        # Handle regular fields
        regular_fields = ['status', 'result', 'confidence', 'token_count', 
                         'cost', 'llm_model', 'error_message', 'retry_count',
                         'duration_ms', 'is_final']
        
        for field in regular_fields:
            if field in updates:
                set_clauses.append(f"{field} = %s")
                params.append(updates[field])

        if not set_clauses:
            return

        params.append(task_id)
        query = f"""
            UPDATE translation_tasks 
            SET {', '.join(set_clauses)}
            WHERE task_id = %s
        """
        await self.execute(query, tuple(params))

    async def get_tasks_by_session(self, session_id: str, 
                                   status: str = None) -> List[Dict[str, Any]]:
        """Get tasks for a session."""
        if status:
            query = """
                SELECT * FROM translation_tasks 
                WHERE session_id = %s AND status = %s
                ORDER BY task_id
            """
            params = (session_id, status)
        else:
            query = """
                SELECT * FROM translation_tasks 
                WHERE session_id = %s
                ORDER BY task_id
            """
            params = (session_id,)

        return await self.fetch_all(query, params)

    async def get_pending_tasks(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pending tasks for processing."""
        query = """
            SELECT * FROM translation_tasks 
            WHERE session_id = %s AND status = 'pending'
            ORDER BY group_id, task_id
            LIMIT %s
        """
        return await self.fetch_all(query, (session_id, limit))

    # Statistics methods
    async def update_session_statistics(self, session_id: str):
        """Update session statistics using stored procedure."""
        async with self.get_connection() as cursor:
            await cursor.callproc('UpdateSessionStatistics', (session_id,))

    async def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """Get detailed session progress."""
        query = """
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
                COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_tasks,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks,
                AVG(CASE WHEN status = 'completed' THEN confidence END) as avg_confidence,
                SUM(CASE WHEN status = 'completed' THEN token_count ELSE 0 END) as total_tokens,
                SUM(cost) as total_cost
            FROM translation_tasks
            WHERE session_id = %s
        """
        result = await self.fetch_one(query, (session_id,))
        return result or {}

    # Logging methods
    async def log_execution(self, session_id: str, level: str, 
                           message: str, details: Dict[str, Any] = None,
                           component: str = None):
        """Log execution details."""
        query = """
            INSERT INTO execution_logs (session_id, level, message, details, component)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (
            session_id,
            level,
            message,
            json.dumps(details or {}),
            component
        )
        await self.execute(query, params)

    # Cost tracking methods
    async def track_cost(self, cost_data: Dict[str, Any]):
        """Track API costs."""
        query = """
            INSERT INTO cost_tracking (
                session_id, batch_id, provider, model, 
                input_tokens, output_tokens, total_tokens,
                cost_usd, cost_cny, exchange_rate
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            cost_data['session_id'],
            cost_data.get('batch_id', ''),
            cost_data['provider'],
            cost_data['model'],
            cost_data.get('input_tokens', 0),
            cost_data.get('output_tokens', 0),
            cost_data.get('total_tokens', 0),
            cost_data.get('cost_usd', 0),
            cost_data.get('cost_cny', 0),
            cost_data.get('exchange_rate', 7.3)
        )
        await self.execute(query, params)

    # Cleanup methods
    async def cleanup_old_sessions(self, days_old: int = 7):
        """Clean up old sessions."""
        async with self.get_connection() as cursor:
            await cursor.callproc('CleanupOldSessions', (days_old,))
            self.logger.info(f"Cleaned up sessions older than {days_old} days")


# Global MySQL connector instance
mysql_connector = MySQLConnector()