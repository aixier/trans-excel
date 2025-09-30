"""
Query Service - Task 5.2
Handles query operations with filtering, pagination, and sorting
"""
import logging
from typing import Dict, Any, Optional
from models.api_models import (
    QueryResponse, Pagination, SessionFilters, TaskFilters
)
from storage.registry import StorageBackendRegistry

logger = logging.getLogger(__name__)


class QueryService:
    """
    Query service for sessions and tasks
    Provides high-level query interface with pagination
    """

    async def query_sessions(
        self,
        filters: SessionFilters,
        pagination: Pagination
    ) -> QueryResponse:
        """
        Query sessions with filters and pagination

        Args:
            filters: Session filters
            pagination: Pagination parameters

        Returns:
            QueryResponse with results
        """
        try:
            # Get storage backend
            backend = StorageBackendRegistry.get_backend("translation_sessions")

            # Query
            result = await backend.query(
                "translation_sessions",
                filters.model_dump(exclude_none=True),
                page=pagination.page,
                page_size=pagination.page_size,
                sort_by=pagination.sort_by,
                order=pagination.order
            )

            # Calculate total pages
            total_pages = (result['total'] + pagination.page_size - 1) // pagination.page_size

            return QueryResponse(
                total=result['total'],
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=total_pages,
                items=result['items']
            )

        except Exception as e:
            logger.error(f"Failed to query sessions: {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get single session by ID

        Args:
            session_id: Session ID

        Returns:
            Session dictionary or None
        """
        try:
            backend = StorageBackendRegistry.get_backend("translation_sessions")
            return await backend.read("translation_sessions", session_id)

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise

    async def query_tasks(
        self,
        filters: TaskFilters,
        pagination: Pagination
    ) -> QueryResponse:
        """
        Query tasks with filters and pagination

        Args:
            filters: Task filters
            pagination: Pagination parameters

        Returns:
            QueryResponse with results
        """
        try:
            # Get storage backend
            backend = StorageBackendRegistry.get_backend("translation_tasks")

            # Query
            result = await backend.query(
                "translation_tasks",
                filters.model_dump(exclude_none=True),
                page=pagination.page,
                page_size=pagination.page_size,
                sort_by=pagination.sort_by,
                order=pagination.order
            )

            # Calculate total pages
            total_pages = (result['total'] + pagination.page_size - 1) // pagination.page_size

            return QueryResponse(
                total=result['total'],
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=total_pages,
                items=result['items']
            )

        except Exception as e:
            logger.error(f"Failed to query tasks: {e}")
            raise

    async def get_task(self, task_id: str) -> Optional[Dict]:
        """
        Get single task by ID

        Args:
            task_id: Task ID

        Returns:
            Task dictionary or None
        """
        try:
            backend = StorageBackendRegistry.get_backend("translation_tasks")
            return await backend.read("translation_tasks", task_id)

        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            raise

    async def get_session_tasks(
        self,
        session_id: str,
        filters: TaskFilters,
        pagination: Pagination
    ) -> QueryResponse:
        """
        Get tasks for a specific session

        Args:
            session_id: Session ID
            filters: Task filters
            pagination: Pagination parameters

        Returns:
            QueryResponse with results
        """
        # Set session_id filter
        filters.session_id = session_id

        return await self.query_tasks(filters, pagination)


# Global singleton instance
query_service = QueryService()