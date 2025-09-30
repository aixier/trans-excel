"""
Storage Backend Registry - Task 4.3
Plugin registry for managing multiple storage backends
"""
import logging
from typing import Dict
from .backend import StorageBackend

logger = logging.getLogger(__name__)


class StorageBackendRegistry:
    """
    Storage backend registry
    Manages registration and routing of storage backends
    """

    _backends: Dict[str, StorageBackend] = {}
    _routing_rules: Dict[str, str] = {}

    @classmethod
    def register(cls, name: str, backend: StorageBackend):
        """
        Register a storage backend

        Args:
            name: Backend name (e.g., 'mysql', 'redis', 'oss')
            backend: StorageBackend instance
        """
        cls._backends[name] = backend
        logger.info(f"Registered storage backend: {name}")

    @classmethod
    def register_collection(cls, collection: str, backend_name: str):
        """
        Register routing rule for a collection

        Args:
            collection: Collection/table name
            backend_name: Backend name to route to
        """
        if backend_name not in cls._backends:
            raise ValueError(f"Backend not registered: {backend_name}")

        cls._routing_rules[collection] = backend_name
        logger.info(f"Registered collection routing: {collection} -> {backend_name}")

    @classmethod
    def get_backend(cls, collection: str) -> StorageBackend:
        """
        Get storage backend for a collection

        Args:
            collection: Collection/table name

        Returns:
            StorageBackend instance

        Raises:
            ValueError: If no backend registered for collection
        """
        backend_name = cls._routing_rules.get(collection)
        if not backend_name:
            raise ValueError(f"No backend registered for collection: {collection}")

        backend = cls._backends.get(backend_name)
        if not backend:
            raise ValueError(f"Backend not found: {backend_name}")

        return backend

    @classmethod
    def get_backend_by_name(cls, name: str) -> StorageBackend:
        """
        Get storage backend by name

        Args:
            name: Backend name

        Returns:
            StorageBackend instance

        Raises:
            ValueError: If backend not found
        """
        backend = cls._backends.get(name)
        if not backend:
            raise ValueError(f"Backend not found: {name}")

        return backend

    @classmethod
    def list_backends(cls) -> list:
        """
        List all registered backends

        Returns:
            List of backend names
        """
        return list(cls._backends.keys())

    @classmethod
    def list_collections(cls) -> Dict[str, str]:
        """
        List all collection routing rules

        Returns:
            Dictionary of collection -> backend mappings
        """
        return cls._routing_rules.copy()

    @classmethod
    async def initialize_all(cls):
        """
        Initialize all registered backends
        """
        logger.info(f"Initializing {len(cls._backends)} storage backends...")
        for name, backend in cls._backends.items():
            try:
                await backend.initialize()
                logger.info(f"Backend '{name}' initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize backend '{name}': {e}")
                raise

    @classmethod
    async def close_all(cls):
        """
        Close all registered backends
        """
        logger.info(f"Closing {len(cls._backends)} storage backends...")
        for name, backend in cls._backends.items():
            try:
                await backend.close()
                logger.info(f"Backend '{name}' closed successfully")
            except Exception as e:
                logger.error(f"Failed to close backend '{name}': {e}")

    @classmethod
    async def health_check_all(cls) -> Dict[str, bool]:
        """
        Health check all registered backends

        Returns:
            Dictionary of backend name -> health status
        """
        results = {}
        for name, backend in cls._backends.items():
            try:
                results[name] = await backend.health_check()
            except Exception as e:
                logger.error(f"Health check failed for backend '{name}': {e}")
                results[name] = False

        return results


# ============================================================================
# Initialize and register storage backends
# ============================================================================

def setup_storage_backends():
    """
    Setup and register storage backends
    Called during application startup
    """
    from .mysql_plugin import MySQLPlugin

    # Create MySQL plugin
    mysql_plugin = MySQLPlugin()

    # Register MySQL backend
    StorageBackendRegistry.register("mysql", mysql_plugin)

    # Register collection routing rules
    StorageBackendRegistry.register_collection("translation_sessions", "mysql")
    StorageBackendRegistry.register_collection("translation_tasks", "mysql")

    logger.info("Storage backends setup complete")
    logger.info(f"Backends: {StorageBackendRegistry.list_backends()}")
    logger.info(f"Collections: {StorageBackendRegistry.list_collections()}")