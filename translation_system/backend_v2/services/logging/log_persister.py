"""Log persistence service for execution logs and system events."""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import threading
from logging.handlers import RotatingFileHandler

from database.mysql_connector import mysql_connector


@dataclass
class LogEntry:
    """Structure for a log entry."""
    timestamp: datetime
    session_id: str
    level: str
    message: str
    component: str
    details: Dict[str, Any] = field(default_factory=dict)
    thread_id: Optional[int] = None
    process_id: Optional[int] = None


class LogPersister:
    """Advanced log persistence service with file and database storage."""

    def __init__(
        self,
        log_dir: str = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        max_files: int = 10,
        flush_interval: int = 5,  # seconds
        batch_size: int = 100
    ):
        """
        Initialize LogPersister.

        Args:
            log_dir: Directory for log files
            max_file_size: Maximum size per log file
            max_files: Maximum number of log files to keep
            flush_interval: Interval to flush logs to storage
            batch_size: Batch size for database writes
        """
        self.log_dir = Path(log_dir) if log_dir else Path("./logs")
        self.log_dir.mkdir(exist_ok=True)

        self.max_file_size = max_file_size
        self.max_files = max_files
        self.flush_interval = flush_interval
        self.batch_size = batch_size

        self.logger = logging.getLogger(self.__class__.__name__)

        # In-memory buffer for logs
        self.log_buffer: deque = deque(maxlen=10000)  # Keep max 10k logs in memory
        self.buffer_lock = threading.Lock()

        # File handlers for different log levels
        self.file_handlers: Dict[str, RotatingFileHandler] = {}
        self._setup_file_handlers()

        # Background task control
        self._flush_task = None
        self._running = False

        # Statistics
        self.stats = {
            'total_logs': 0,
            'logs_to_file': 0,
            'logs_to_db': 0,
            'db_errors': 0,
            'file_errors': 0,
            'last_flush': None
        }

    def _setup_file_handlers(self):
        """Setup rotating file handlers for different log levels."""
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

        for level in levels:
            log_file = self.log_dir / f"translation_system_{level.lower()}.log"

            handler = RotatingFileHandler(
                log_file,
                maxBytes=self.max_file_size,
                backupCount=self.max_files,
                encoding='utf-8'
            )

            # Custom formatter for structured logging
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)

            self.file_handlers[level] = handler

        # General application log
        app_log_file = self.log_dir / "application.log"
        app_handler = RotatingFileHandler(
            app_log_file,
            maxBytes=self.max_file_size * 2,  # Larger for general log
            backupCount=self.max_files,
            encoding='utf-8'
        )
        app_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        app_handler.setFormatter(app_formatter)
        self.file_handlers['APPLICATION'] = app_handler

    async def start(self):
        """Start the log persistence service."""
        if self._running:
            return

        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        self.logger.info("Log persistence service started")

    async def stop(self):
        """Stop the log persistence service."""
        if not self._running:
            return

        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self.flush_logs()

        # Close file handlers
        for handler in self.file_handlers.values():
            handler.close()

        self.logger.info("Log persistence service stopped")

    async def log(
        self,
        session_id: str,
        level: str,
        message: str,
        component: str,
        details: Dict[str, Any] = None
    ):
        """
        Log an entry with persistence.

        Args:
            session_id: Session identifier
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            component: Component name
            details: Additional details
        """
        try:
            log_entry = LogEntry(
                timestamp=datetime.now(),
                session_id=session_id,
                level=level.upper(),
                message=message,
                component=component,
                details=details or {},
                thread_id=threading.get_ident(),
                process_id=os.getpid()
            )

            # Add to buffer
            with self.buffer_lock:
                self.log_buffer.append(log_entry)

            self.stats['total_logs'] += 1

            # Also log to standard logger for immediate visibility
            log_level = getattr(logging, level.upper(), logging.INFO)
            self.logger.log(
                log_level,
                f"[{session_id[:8]}] [{component}] {message}"
            )

        except Exception as e:
            # Don't let logging errors break the application
            self.logger.error(f"Failed to log entry: {e}")

    async def _flush_loop(self):
        """Background loop to flush logs periodically."""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush_logs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in flush loop: {e}")

    async def flush_logs(self):
        """Flush buffered logs to file and database."""
        if not self.log_buffer:
            return

        # Get logs from buffer
        with self.buffer_lock:
            logs_to_process = list(self.log_buffer)
            self.log_buffer.clear()

        if not logs_to_process:
            return

        # Write to files
        await self._write_to_files(logs_to_process)

        # Write to database
        await self._write_to_database(logs_to_process)

        self.stats['last_flush'] = datetime.now().isoformat()
        self.logger.debug(f"Flushed {len(logs_to_process)} log entries")

    async def _write_to_files(self, logs: List[LogEntry]):
        """Write logs to file handlers."""
        try:
            for log_entry in logs:
                # Format log message
                details_str = ""
                if log_entry.details:
                    details_str = f" | Details: {json.dumps(log_entry.details, ensure_ascii=False)}"

                log_message = (
                    f"{log_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | "
                    f"{log_entry.level:<8} | "
                    f"{log_entry.component:<20} | "
                    f"[{log_entry.session_id[:8]}] | "
                    f"{log_entry.message}"
                    f"{details_str}"
                )

                # Write to level-specific handler
                level_handler = self.file_handlers.get(log_entry.level)
                if level_handler:
                    level_handler.emit(
                        logging.LogRecord(
                            name=log_entry.component,
                            level=getattr(logging, log_entry.level, logging.INFO),
                            pathname="",
                            lineno=0,
                            msg=log_message,
                            args=(),
                            exc_info=None
                        )
                    )

                # Also write to application log
                app_handler = self.file_handlers.get('APPLICATION')
                if app_handler:
                    app_handler.emit(
                        logging.LogRecord(
                            name="Application",
                            level=getattr(logging, log_entry.level, logging.INFO),
                            pathname="",
                            lineno=0,
                            msg=log_message,
                            args=(),
                            exc_info=None
                        )
                    )

            self.stats['logs_to_file'] += len(logs)

        except Exception as e:
            self.stats['file_errors'] += 1
            self.logger.error(f"Failed to write logs to files: {e}")

    async def _write_to_database(self, logs: List[LogEntry]):
        """Write logs to database in batches."""
        try:
            # Process logs in batches
            for i in range(0, len(logs), self.batch_size):
                batch = logs[i:i + self.batch_size]

                for log_entry in batch:
                    try:
                        await mysql_connector.log_execution(
                            session_id=log_entry.session_id,
                            level=log_entry.level,
                            message=log_entry.message,
                            details=log_entry.details,
                            component=log_entry.component
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to write log to database: {e}")
                        self.stats['db_errors'] += 1
                        continue

            self.stats['logs_to_db'] += len(logs)

        except Exception as e:
            self.stats['db_errors'] += 1
            self.logger.error(f"Failed to write logs to database: {e}")

    async def query_logs(
        self,
        session_id: str = None,
        level: str = None,
        component: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query logs from database.

        Args:
            session_id: Session identifier to filter by
            level: Log level to filter by
            component: Component to filter by
            start_time: Start time for date range
            end_time: End time for date range
            limit: Maximum number of results

        Returns:
            List of log entries
        """
        try:
            # Build query
            where_clauses = []
            params = []

            if session_id:
                where_clauses.append("session_id = %s")
                params.append(session_id)

            if level:
                where_clauses.append("level = %s")
                params.append(level.upper())

            if component:
                where_clauses.append("component = %s")
                params.append(component)

            if start_time:
                where_clauses.append("timestamp >= %s")
                params.append(start_time)

            if end_time:
                where_clauses.append("timestamp <= %s")
                params.append(end_time)

            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)

            query = f"""
                SELECT *
                FROM execution_logs
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT %s
            """
            params.append(limit)

            results = await mysql_connector.fetch_all(query, tuple(params))
            return results

        except Exception as e:
            self.logger.error(f"Failed to query logs: {e}")
            return []

    def get_log_files(self) -> List[Dict[str, Any]]:
        """Get information about log files."""
        log_files = []

        try:
            for log_file in self.log_dir.glob("*.log*"):
                stat = log_file.stat()

                file_info = {
                    'filename': log_file.name,
                    'path': str(log_file),
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'is_rotated': '.log.' in log_file.name
                }

                log_files.append(file_info)

            # Sort by modification time (newest first)
            log_files.sort(key=lambda x: x['modified_time'], reverse=True)

        except Exception as e:
            self.logger.error(f"Failed to get log files info: {e}")

        return log_files

    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        return {
            'stats': self.stats.copy(),
            'buffer_size': len(self.log_buffer),
            'running': self._running,
            'log_dir': str(self.log_dir),
            'file_handlers': list(self.file_handlers.keys())
        }

    async def cleanup_old_logs(self, days_old: int = 30):
        """
        Clean up old log files.

        Args:
            days_old: Remove files older than this many days
        """
        try:
            if not self.log_dir.exists():
                return

            current_time = datetime.now()
            cleanup_count = 0

            for log_file in self.log_dir.glob("*.log*"):
                try:
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    age_days = (current_time - file_time).days

                    if age_days > days_old:
                        log_file.unlink()
                        cleanup_count += 1
                        self.logger.debug(f"Removed old log file: {log_file}")

                except Exception as e:
                    self.logger.warning(f"Failed to remove log file {log_file}: {e}")

            if cleanup_count > 0:
                self.logger.info(f"Cleaned up {cleanup_count} old log files")

            # Also cleanup database logs if configured
            try:
                await mysql_connector.execute(
                    "DELETE FROM execution_logs WHERE timestamp < %s",
                    (current_time - timedelta(days=days_old),)
                )
            except Exception as e:
                self.logger.warning(f"Failed to cleanup old database logs: {e}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")

    async def export_session_logs(self, session_id: str, format: str = 'json') -> str:
        """
        Export logs for a specific session.

        Args:
            session_id: Session identifier
            format: Export format ('json', 'csv', 'txt')

        Returns:
            Path to exported file
        """
        try:
            # Query logs for session
            logs = await self.query_logs(session_id=session_id, limit=10000)

            if not logs:
                raise ValueError(f"No logs found for session {session_id}")

            # Create export filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_logs_{session_id[:8]}_{timestamp}.{format}"
            export_path = self.log_dir / "exports" / filename

            # Create exports directory
            export_path.parent.mkdir(exist_ok=True)

            if format == 'json':
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False, default=str)

            elif format == 'csv':
                import pandas as pd
                df = pd.DataFrame(logs)
                df.to_csv(export_path, index=False, encoding='utf-8')

            elif format == 'txt':
                with open(export_path, 'w', encoding='utf-8') as f:
                    for log in logs:
                        f.write(
                            f"{log['timestamp']} | {log['level']:<8} | "
                            f"{log['component']:<20} | {log['message']}\n"
                        )
                        if log.get('details'):
                            f.write(f"  Details: {json.dumps(log['details'])}\n")
                        f.write("\n")

            else:
                raise ValueError(f"Unsupported export format: {format}")

            self.logger.info(f"Exported session logs to: {export_path}")
            return str(export_path)

        except Exception as e:
            self.logger.error(f"Failed to export session logs: {e}")
            raise


# Global log persister instance
log_persister = LogPersister()