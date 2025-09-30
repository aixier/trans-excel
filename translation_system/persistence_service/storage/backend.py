"""
Storage Backend Abstract Interface - Task 4.1
Defines the contract for all storage backend implementations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class StorageBackend(ABC):
    """
    Abstract base class for storage backends
    All storage plugins must implement this interface
    """

    @abstractmethod
    async def write(self, collection: str, data: List[Dict]) -> int:
        """
        Batch write data to storage

        Args:
            collection: Collection/table name
            data: List of data dictionaries

        Returns:
            Number of affected rows/documents
        """
        pass

    @abstractmethod
    async def read(self, collection: str, key: str) -> Optional[Dict]:
        """
        Read single record by key

        Args:
            collection: Collection/table name
            key: Primary key value

        Returns:
            Data dictionary or None if not found
        """
        pass

    @abstractmethod
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
            collection: Collection/table name
            filters: Filter conditions
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_by: Column/field to sort by
            order: Sort order ('asc' or 'desc')

        Returns:
            Dictionary with 'total' count and 'items' list
        """
        pass

    @abstractmethod
    async def delete(self, collection: str, key: str) -> bool:
        """
        Delete record by key

        Args:
            collection: Collection/table name
            key: Primary key value

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if storage backend is healthy

        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    async def initialize(self):
        """
        Initialize storage backend (e.g., connection pools)
        """
        pass

    @abstractmethod
    async def close(self):
        """
        Close storage backend and cleanup resources
        """
        pass