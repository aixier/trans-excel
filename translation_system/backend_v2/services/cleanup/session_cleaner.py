"""Session cleaner service for cleaning up expired sessions."""

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from database.mysql_connector import mysql_connector
from utils.session_manager import session_manager
from services.persistence.checkpoint_service import checkpoint_service
from services.export.excel_exporter import excel_exporter

logger = logging.getLogger(__name__)


class SessionCleaner:
    """Clean up expired sessions and temporary files."""

    def __init__(self, cleanup_interval: int = 3600):
        """
        Initialize session cleaner.

        Args:
            cleanup_interval: Cleanup interval in seconds (default 1 hour)
        """
        self.cleanup_interval = cleanup_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Configuration
        self.session_ttl_hours = 24  # Sessions expire after 24 hours
        self.temp_file_ttl_hours = 12  # Temp files expire after 12 hours
        self.export_ttl_days = 7  # Exported files kept for 7 days
        self.checkpoint_ttl_days = 3  # Checkpoints kept for 3 days
        
        # Directories to clean
        self.temp_dirs = [
            Path("./temp"),
            Path("./uploads"),
            Path("./temp/exports")
        ]

    async def start_cleanup_service(self):
        """
        Start the cleanup service.
        """
        if self.is_running:
            self.logger.warning("Cleanup service is already running")
            return

        self.is_running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("Session cleanup service started")

    async def stop_cleanup_service(self):
        """
        Stop the cleanup service.
        """
        if not self.is_running:
            return

        self.is_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Session cleanup service stopped")

    async def _cleanup_loop(self):
        """
        Main cleanup loop.
        """
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.run_cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def run_cleanup(self) -> Dict[str, Any]:
        """
        Run a cleanup cycle.

        Returns:
            Cleanup statistics
        """
        start_time = datetime.now()
        self.logger.info("Starting cleanup cycle")

        stats = {
            'sessions_cleaned': 0,
            'temp_files_removed': 0,
            'exports_removed': 0,
            'checkpoints_removed': 0,
            'database_rows_cleaned': 0,
            'errors': []
        }

        # Clean expired sessions
        try:
            session_stats = await self._clean_expired_sessions()
            stats['sessions_cleaned'] = session_stats['cleaned']
        except Exception as e:
            self.logger.error(f"Failed to clean sessions: {e}")
            stats['errors'].append(f"Session cleanup: {str(e)}")

        # Clean temporary files
        try:
            temp_stats = await self._clean_temp_files()
            stats['temp_files_removed'] = temp_stats['removed']
        except Exception as e:
            self.logger.error(f"Failed to clean temp files: {e}")
            stats['errors'].append(f"Temp file cleanup: {str(e)}")

        # Clean old exports
        try:
            await excel_exporter.cleanup_old_exports(self.export_ttl_days)
            # Count removed exports
            stats['exports_removed'] = 0  # Would need to modify excel_exporter to return count
        except Exception as e:
            self.logger.error(f"Failed to clean exports: {e}")
            stats['errors'].append(f"Export cleanup: {str(e)}")

        # Clean old checkpoints
        try:
            await checkpoint_service.cleanup_old_checkpoints(self.checkpoint_ttl_days)
            stats['checkpoints_removed'] = 0  # Would need to modify checkpoint_service to return count
        except Exception as e:
            self.logger.error(f"Failed to clean checkpoints: {e}")
            stats['errors'].append(f"Checkpoint cleanup: {str(e)}")

        # Clean database
        try:
            db_stats = await self._clean_database()
            stats['database_rows_cleaned'] = db_stats['rows_cleaned']
        except Exception as e:
            self.logger.error(f"Failed to clean database: {e}")
            stats['errors'].append(f"Database cleanup: {str(e)}")

        duration = (datetime.now() - start_time).total_seconds()
        stats['duration_seconds'] = duration

        self.logger.info(
            f"Cleanup completed: {stats['sessions_cleaned']} sessions, "
            f"{stats['temp_files_removed']} temp files, "
            f"{stats['database_rows_cleaned']} DB rows, "
            f"duration={duration:.2f}s"
        )

        return stats

    async def _clean_expired_sessions(self) -> Dict[str, int]:
        """
        Clean expired sessions from memory and database.

        Returns:
            Cleanup statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=self.session_ttl_hours)
        cleaned_count = 0

        # Get all sessions from session manager
        sessions = session_manager.get_all_sessions()
        
        for session_id, session_data in sessions.items():
            try:
                # Check session age
                created_at = session_data.get('created_at')
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at)
                
                if created_at and created_at < cutoff_time:
                    # Check if session is still active
                    task_manager = session_manager.get_task_manager(session_id)
                    if task_manager and task_manager.df is not None:
                        df = task_manager.df
                        processing = len(df[df['status'] == 'processing'])
                        if processing > 0:
                            # Skip active sessions
                            continue
                    
                    # Remove session
                    session_manager.remove_session(session_id)
                    cleaned_count += 1
                    self.logger.debug(f"Removed expired session: {session_id}")
                    
            except Exception as e:
                self.logger.error(f"Failed to clean session {session_id}: {e}")

        # Clean database sessions
        if mysql_connector._initialized:
            await mysql_connector.cleanup_old_sessions(self.session_ttl_hours // 24)

        return {'cleaned': cleaned_count}

    async def _clean_temp_files(self) -> Dict[str, int]:
        """
        Clean temporary files.

        Returns:
            Cleanup statistics
        """
        removed_count = 0
        cutoff_time = datetime.now() - timedelta(hours=self.temp_file_ttl_hours)

        for temp_dir in self.temp_dirs:
            if not temp_dir.exists():
                continue

            try:
                # Clean files
                for file_path in temp_dir.glob("*"):
                    if file_path.is_file():
                        # Check file age
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_time:
                            file_path.unlink()
                            removed_count += 1
                            self.logger.debug(f"Removed temp file: {file_path}")
                    
                # Clean empty directories
                for dir_path in temp_dir.glob("*/"):
                    if dir_path.is_dir():
                        try:
                            # Check if directory is empty or old
                            dir_time = datetime.fromtimestamp(dir_path.stat().st_mtime)
                            if dir_time < cutoff_time:
                                if not any(dir_path.iterdir()):
                                    dir_path.rmdir()
                                else:
                                    shutil.rmtree(dir_path)
                                removed_count += 1
                                self.logger.debug(f"Removed temp directory: {dir_path}")
                        except Exception as e:
                            self.logger.warning(f"Failed to remove directory {dir_path}: {e}")
                            
            except Exception as e:
                self.logger.error(f"Failed to clean temp dir {temp_dir}: {e}")

        return {'removed': removed_count}

    async def _clean_database(self) -> Dict[str, int]:
        """
        Clean old database records.

        Returns:
            Cleanup statistics
        """
        if not mysql_connector._initialized:
            return {'rows_cleaned': 0}

        rows_cleaned = 0

        try:
            # Clean old execution logs
            cutoff_date = datetime.now() - timedelta(days=7)
            query = "DELETE FROM execution_logs WHERE timestamp < %s"
            result = await mysql_connector.execute(query, (cutoff_date,))
            rows_cleaned += result

            # Clean old performance metrics
            query = "DELETE FROM performance_metrics WHERE timestamp < %s"
            result = await mysql_connector.execute(query, (cutoff_date,))
            rows_cleaned += result

            # Clean orphaned tasks (tasks without sessions)
            query = """
                DELETE t FROM translation_tasks t
                LEFT JOIN translation_sessions s ON t.session_id = s.session_id
                WHERE s.session_id IS NULL
            """
            result = await mysql_connector.execute(query)
            rows_cleaned += result

            self.logger.info(f"Cleaned {rows_cleaned} database rows")

        except Exception as e:
            self.logger.error(f"Database cleanup failed: {e}")

        return {'rows_cleaned': rows_cleaned}

    async def force_clean_session(self, session_id: str) -> bool:
        """
        Force clean a specific session.

        Args:
            session_id: Session ID to clean

        Returns:
            True if successful
        """
        try:
            # Remove from session manager
            session_manager.remove_session(session_id)

            # Clean temp files
            for temp_dir in self.temp_dirs:
                if temp_dir.exists():
                    for file_path in temp_dir.glob(f"*{session_id}*"):
                        if file_path.is_file():
                            file_path.unlink()
                        elif file_path.is_dir():
                            shutil.rmtree(file_path)

            # Clean database records if connected
            if mysql_connector._initialized:
                # Delete tasks
                query = "DELETE FROM translation_tasks WHERE session_id = %s"
                await mysql_connector.execute(query, (session_id,))
                
                # Delete session
                query = "DELETE FROM translation_sessions WHERE session_id = %s"
                await mysql_connector.execute(query, (session_id,))

            self.logger.info(f"Force cleaned session: {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to force clean session {session_id}: {e}")
            return False

    def get_cleanup_status(self) -> Dict[str, Any]:
        """
        Get cleanup service status.

        Returns:
            Status information
        """
        return {
            'is_running': self.is_running,
            'cleanup_interval': self.cleanup_interval,
            'session_ttl_hours': self.session_ttl_hours,
            'temp_file_ttl_hours': self.temp_file_ttl_hours,
            'export_ttl_days': self.export_ttl_days,
            'checkpoint_ttl_days': self.checkpoint_ttl_days,
            'temp_directories': [str(d) for d in self.temp_dirs]
        }


# Global session cleaner instance
session_cleaner = SessionCleaner()