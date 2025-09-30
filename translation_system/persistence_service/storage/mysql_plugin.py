"""
MySQL Storage Plugin - Task 4.2
Implementation of StorageBackend for MySQL
"""
import logging
from typing import List, Dict, Any, Optional
from .backend import StorageBackend
from database.mysql_connector import mysql_connector

logger = logging.getLogger(__name__)


class MySQLPlugin(StorageBackend):
    """
    MySQL storage backend implementation
    Wraps mysql_connector and implements StorageBackend interface
    """

    def __init__(self):
        self.connector = mysql_connector
        logger.info("MySQL Plugin initialized")

    async def initialize(self):
        """
        Initialize MySQL connection pool
        """
        await self.connector.initialize()
        logger.info("MySQL Plugin connection pool initialized")

    async def close(self):
        """
        Close MySQL connection pool
        """
        await self.connector.close()
        logger.info("MySQL Plugin connection pool closed")

    async def health_check(self) -> bool:
        """
        Check MySQL database health

        Returns:
            True if healthy, False otherwise
        """
        return await self.connector.health_check()

    async def write(self, collection: str, data: List[Dict]) -> int:
        """
        Batch write data to MySQL

        Args:
            collection: Table name (translation_sessions or translation_tasks)
            data: List of data dictionaries

        Returns:
            Number of affected rows
        """
        if not data:
            return 0

        if collection == "translation_sessions":
            return await self.connector.batch_upsert_sessions(data)
        elif collection == "translation_tasks":
            return await self.connector.batch_upsert_tasks(data)
        else:
            raise ValueError(f"Unknown collection: {collection}")

    async def read(self, collection: str, key: str) -> Optional[Dict]:
        """
        Read single record by key

        Args:
            collection: Table name
            key: Primary key value (session_id or task_id)

        Returns:
            Data dictionary or None
        """
        if collection == "translation_sessions":
            return await self.connector.get_session_by_id(key)
        elif collection == "translation_tasks":
            return await self.connector.get_task_by_id(key)
        else:
            raise ValueError(f"Unknown collection: {collection}")

    async def query(
        self,
        collection: str,
        filters: Dict[str, Any],
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Query data with filtering, pagination, and sorting

        Args:
            collection: Table name
            filters: Filter conditions
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_by: Column to sort by
            order: Sort order ('asc' or 'desc')

        Returns:
            Dictionary with 'total' count and 'items' list
        """
        if collection == "translation_sessions":
            return await self.connector.query_sessions(
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                order=order
            )
        elif collection == "translation_tasks":
            return await self.connector.query_tasks(
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                order=order
            )
        else:
            raise ValueError(f"Unknown collection: {collection}")

    async def delete(self, collection: str, key: str) -> bool:
        """
        Delete record by key

        Args:
            collection: Table name
            key: Primary key value

        Returns:
            True if deleted, False if not found
        """
        if collection == "translation_sessions":
            return await self.connector.delete_session(key)
        elif collection == "translation_tasks":
            # Tasks are deleted via CASCADE when session is deleted
            # Direct task deletion not supported yet
            raise NotImplementedError("Direct task deletion not supported")
        else:
            raise ValueError(f"Unknown collection: {collection}")

    async def get_incomplete_sessions(self) -> List[Dict]:
        """
        Get all incomplete sessions (helper method)

        Returns:
            List of incomplete session dictionaries
        """
        return await self.connector.get_incomplete_sessions()

    async def get_session_with_tasks(self, session_id: str) -> Dict:
        """
        Get session with all its incomplete tasks (helper method)

        Args:
            session_id: Session ID

        Returns:
            Dictionary with session and tasks
        """
        return await self.connector.get_session_with_tasks(session_id)

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics (helper method)

        Returns:
            Dictionary with statistics
        """
        sessions_stats = await self.connector.get_sessions_stats()
        tasks_stats = await self.connector.get_tasks_stats()
        storage_stats = await self.connector.get_database_stats()

        return {
            'sessions': sessions_stats,
            'tasks': tasks_stats,
            'storage': storage_stats
        }