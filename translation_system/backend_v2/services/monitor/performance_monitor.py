"""Real-time performance monitoring service."""

import os
import psutil
import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import threading
import time
import gc

from services.logging.log_persister import log_persister
from utils.session_manager import session_manager


@dataclass
class SystemMetrics:
    """System performance metrics at a point in time."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    active_sessions: int
    python_objects: int
    thread_count: int


@dataclass
class SessionMetrics:
    """Per-session performance metrics."""
    session_id: str
    timestamp: datetime
    tasks_total: int
    tasks_completed: int
    tasks_failed: int
    tasks_pending: int
    processing_rate: float  # tasks per minute
    avg_response_time: float  # seconds
    memory_usage_mb: float
    error_rate: float


@dataclass
class Alert:
    """Performance alert."""
    alert_id: str
    timestamp: datetime
    level: str  # WARNING, CRITICAL
    category: str  # SYSTEM, SESSION, MEMORY, etc.
    message: str
    metrics: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class PerformanceMonitor:
    """Real-time system and session performance monitoring."""

    def __init__(
        self,
        collection_interval: int = 30,  # seconds
        retention_hours: int = 24,
        alert_thresholds: Dict[str, float] = None
    ):
        """
        Initialize PerformanceMonitor.

        Args:
            collection_interval: Metrics collection interval in seconds
            retention_hours: Hours to retain metrics in memory
            alert_thresholds: Thresholds for alerts
        """
        self.collection_interval = collection_interval
        self.retention_hours = retention_hours
        self.logger = logging.getLogger(self.__class__.__name__)

        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'error_rate': 0.1,  # 10%
            'low_memory_mb': 500.0
        }

        # Metrics storage
        max_metrics = int((retention_hours * 3600) / collection_interval)
        self.system_metrics: deque = deque(maxlen=max_metrics)
        self.session_metrics: Dict[str, deque] = {}
        self.metrics_lock = threading.Lock()

        # Alerts
        self.alerts: List[Alert] = []
        self.alert_callbacks: List[Callable] = []

        # Monitoring task control
        self._monitor_task = None
        self._running = False

        # Performance statistics
        self.stats = {
            'monitoring_start': None,
            'total_collections': 0,
            'total_alerts': 0,
            'last_collection': None,
            'collection_errors': 0
        }

        # Process reference for resource monitoring
        self.process = psutil.Process(os.getpid())

    async def start(self):
        """Start performance monitoring."""
        if self._running:
            return

        self._running = True
        self.stats['monitoring_start'] = datetime.now()

        self._monitor_task = asyncio.create_task(self._monitoring_loop())

        self.logger.info(
            f"Performance monitoring started "
            f"(interval={self.collection_interval}s, retention={self.retention_hours}h)"
        )

        # Log initial system info
        await self._log_system_info()

    async def stop(self):
        """Stop performance monitoring."""
        if not self._running:
            return

        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Performance monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                # Collect system metrics
                await self._collect_system_metrics()

                # Collect session metrics
                await self._collect_session_metrics()

                # Check for alerts
                await self._check_alerts()

                # Update statistics
                self.stats['total_collections'] += 1
                self.stats['last_collection'] = datetime.now()

                await asyncio.sleep(self.collection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.stats['collection_errors'] += 1
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry

    async def _collect_system_metrics(self):
        """Collect system-wide performance metrics."""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Disk usage for current directory
            disk_usage = psutil.disk_usage('.')

            # Active sessions
            active_sessions = len(session_manager.get_active_sessions())

            # Python-specific metrics
            python_objects = len(gc.get_objects())
            thread_count = threading.active_count()

            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=disk_usage.percent,
                disk_free_gb=disk_usage.free / (1024 * 1024 * 1024),
                active_sessions=active_sessions,
                python_objects=python_objects,
                thread_count=thread_count
            )

            with self.metrics_lock:
                self.system_metrics.append(metrics)

        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")

    async def _collect_session_metrics(self):
        """Collect per-session performance metrics."""
        try:
            active_sessions = session_manager.get_active_sessions()

            for session_id, session_info in active_sessions.items():
                try:
                    # Get task statistics
                    task_manager = session_manager.get_task_manager(session_id)
                    if not task_manager or not task_manager.df is not None:
                        continue

                    stats = task_manager.get_statistics()

                    # Calculate processing rate (tasks per minute)
                    processing_rate = self._calculate_processing_rate(session_id, stats)

                    # Calculate average response time (if available)
                    avg_response_time = self._calculate_avg_response_time(session_id)

                    # Estimate memory usage for session
                    memory_usage = self._estimate_session_memory(session_id)

                    # Calculate error rate
                    total_tasks = stats.get('total', 1)
                    failed_tasks = stats.get('by_status', {}).get('failed', 0)
                    error_rate = failed_tasks / total_tasks if total_tasks > 0 else 0

                    metrics = SessionMetrics(
                        session_id=session_id,
                        timestamp=datetime.now(),
                        tasks_total=stats.get('total', 0),
                        tasks_completed=stats.get('by_status', {}).get('completed', 0),
                        tasks_failed=failed_tasks,
                        tasks_pending=stats.get('by_status', {}).get('pending', 0),
                        processing_rate=processing_rate,
                        avg_response_time=avg_response_time,
                        memory_usage_mb=memory_usage,
                        error_rate=error_rate
                    )

                    # Store metrics
                    with self.metrics_lock:
                        if session_id not in self.session_metrics:
                            max_session_metrics = int((self.retention_hours * 3600) / self.collection_interval)
                            self.session_metrics[session_id] = deque(maxlen=max_session_metrics)

                        self.session_metrics[session_id].append(metrics)

                except Exception as e:
                    self.logger.warning(f"Failed to collect metrics for session {session_id}: {e}")

        except Exception as e:
            self.logger.error(f"Failed to collect session metrics: {e}")

    def _calculate_processing_rate(self, session_id: str, stats: Dict[str, Any]) -> float:
        """Calculate processing rate (tasks per minute)."""
        try:
            if session_id not in self.session_metrics:
                return 0.0

            with self.metrics_lock:
                recent_metrics = list(self.session_metrics[session_id])

            if len(recent_metrics) < 2:
                return 0.0

            # Compare with previous metric
            current_completed = stats.get('by_status', {}).get('completed', 0)
            previous_completed = recent_metrics[-1].tasks_completed

            time_diff = (datetime.now() - recent_metrics[-1].timestamp).total_seconds() / 60.0
            if time_diff <= 0:
                return 0.0

            tasks_processed = max(0, current_completed - previous_completed)
            return tasks_processed / time_diff

        except Exception:
            return 0.0

    def _calculate_avg_response_time(self, session_id: str) -> float:
        """Calculate average response time from recent metrics."""
        # This would need integration with batch executor metrics
        # For now, return a placeholder
        return 0.0

    def _estimate_session_memory(self, session_id: str) -> float:
        """Estimate memory usage for a session."""
        try:
            # Get session components
            excel_df = session_manager.get_excel_df(session_id)
            task_manager = session_manager.get_task_manager(session_id)

            memory_mb = 0.0

            # Estimate Excel DataFrame memory
            if excel_df:
                for df in excel_df.sheets.values():
                    memory_mb += df.memory_usage(deep=True).sum() / (1024 * 1024)

            # Estimate Task DataFrame memory
            if task_manager and task_manager.df is not None:
                memory_mb += task_manager.df.memory_usage(deep=True).sum() / (1024 * 1024)

            return memory_mb

        except Exception:
            return 0.0

    async def _check_alerts(self):
        """Check for performance issues and generate alerts."""
        try:
            if not self.system_metrics:
                return

            latest_metrics = self.system_metrics[-1]
            alerts = []

            # System alerts
            if latest_metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
                alerts.append(self._create_alert(
                    'CRITICAL' if latest_metrics.cpu_percent > 95 else 'WARNING',
                    'SYSTEM',
                    f"High CPU usage: {latest_metrics.cpu_percent:.1f}%",
                    {'cpu_percent': latest_metrics.cpu_percent}
                ))

            if latest_metrics.memory_percent > self.alert_thresholds['memory_percent']:
                alerts.append(self._create_alert(
                    'CRITICAL' if latest_metrics.memory_percent > 95 else 'WARNING',
                    'MEMORY',
                    f"High memory usage: {latest_metrics.memory_percent:.1f}%",
                    {
                        'memory_percent': latest_metrics.memory_percent,
                        'memory_used_mb': latest_metrics.memory_used_mb,
                        'memory_available_mb': latest_metrics.memory_available_mb
                    }
                ))

            if latest_metrics.disk_usage_percent > self.alert_thresholds['disk_usage_percent']:
                alerts.append(self._create_alert(
                    'CRITICAL',
                    'DISK',
                    f"Low disk space: {latest_metrics.disk_usage_percent:.1f}% used",
                    {
                        'disk_usage_percent': latest_metrics.disk_usage_percent,
                        'disk_free_gb': latest_metrics.disk_free_gb
                    }
                ))

            if latest_metrics.memory_available_mb < self.alert_thresholds['low_memory_mb']:
                alerts.append(self._create_alert(
                    'CRITICAL',
                    'MEMORY',
                    f"Low available memory: {latest_metrics.memory_available_mb:.0f} MB",
                    {'memory_available_mb': latest_metrics.memory_available_mb}
                ))

            # Session-specific alerts
            for session_id, session_metrics_list in self.session_metrics.items():
                if not session_metrics_list:
                    continue

                latest_session = session_metrics_list[-1]

                if latest_session.error_rate > self.alert_thresholds['error_rate']:
                    alerts.append(self._create_alert(
                        'WARNING',
                        'SESSION',
                        f"High error rate in session {session_id[:8]}: {latest_session.error_rate:.1%}",
                        {
                            'session_id': session_id,
                            'error_rate': latest_session.error_rate,
                            'failed_tasks': latest_session.tasks_failed,
                            'total_tasks': latest_session.tasks_total
                        }
                    ))

            # Process alerts
            for alert in alerts:
                await self._process_alert(alert)

        except Exception as e:
            self.logger.error(f"Failed to check alerts: {e}")

    def _create_alert(
        self,
        level: str,
        category: str,
        message: str,
        metrics: Dict[str, Any]
    ) -> Alert:
        """Create an alert."""
        alert_id = f"{category}_{level}_{int(time.time())}"

        return Alert(
            alert_id=alert_id,
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            metrics=metrics
        )

    async def _process_alert(self, alert: Alert):
        """Process a new alert."""
        # Check if similar alert already exists
        existing_alert = self._find_similar_alert(alert)
        if existing_alert:
            return

        # Add to alerts list
        self.alerts.append(alert)
        self.stats['total_alerts'] += 1

        # Log alert
        await log_persister.log(
            session_id="system",
            level=alert.level,
            message=f"Performance Alert: {alert.message}",
            component="PerformanceMonitor",
            details=alert.metrics
        )

        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")

        self.logger.warning(f"Performance Alert [{alert.level}]: {alert.message}")

    def _find_similar_alert(self, new_alert: Alert) -> Optional[Alert]:
        """Find similar unresolved alert."""
        for alert in self.alerts:
            if (alert.category == new_alert.category and
                alert.level == new_alert.level and
                not alert.resolved and
                (datetime.now() - alert.timestamp).total_seconds() < 300):  # 5 minutes
                return alert
        return None

    async def _log_system_info(self):
        """Log initial system information."""
        try:
            system_info = {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024 * 1024 * 1024),
                'disk_total_gb': psutil.disk_usage('.').total / (1024 * 1024 * 1024),
                'python_version': f"{psutil.version_info}",
                'platform': os.name
            }

            await log_persister.log(
                session_id="system",
                level="INFO",
                message="System information logged",
                component="PerformanceMonitor",
                details=system_info
            )

        except Exception as e:
            self.logger.error(f"Failed to log system info: {e}")

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        try:
            with self.metrics_lock:
                if not self.system_metrics:
                    return {'error': 'No metrics available'}

                latest_system = self.system_metrics[-1]

                current_metrics = {
                    'system': {
                        'timestamp': latest_system.timestamp.isoformat(),
                        'cpu_percent': latest_system.cpu_percent,
                        'memory_percent': latest_system.memory_percent,
                        'memory_used_mb': latest_system.memory_used_mb,
                        'memory_available_mb': latest_system.memory_available_mb,
                        'disk_usage_percent': latest_system.disk_usage_percent,
                        'disk_free_gb': latest_system.disk_free_gb,
                        'active_sessions': latest_system.active_sessions,
                        'python_objects': latest_system.python_objects,
                        'thread_count': latest_system.thread_count
                    },
                    'sessions': {},
                    'alerts': {
                        'active_alerts': [
                            {
                                'alert_id': alert.alert_id,
                                'timestamp': alert.timestamp.isoformat(),
                                'level': alert.level,
                                'category': alert.category,
                                'message': alert.message
                            }
                            for alert in self.alerts if not alert.resolved
                        ],
                        'total_alerts': len(self.alerts)
                    },
                    'statistics': self.stats.copy()
                }

                # Add session metrics
                for session_id, session_metrics_list in self.session_metrics.items():
                    if session_metrics_list:
                        latest_session = session_metrics_list[-1]
                        current_metrics['sessions'][session_id] = {
                            'timestamp': latest_session.timestamp.isoformat(),
                            'tasks_total': latest_session.tasks_total,
                            'tasks_completed': latest_session.tasks_completed,
                            'tasks_failed': latest_session.tasks_failed,
                            'tasks_pending': latest_session.tasks_pending,
                            'processing_rate': latest_session.processing_rate,
                            'avg_response_time': latest_session.avg_response_time,
                            'memory_usage_mb': latest_session.memory_usage_mb,
                            'error_rate': latest_session.error_rate
                        }

                return current_metrics

        except Exception as e:
            self.logger.error(f"Failed to get current metrics: {e}")
            return {'error': str(e)}

    def get_historical_metrics(
        self,
        session_id: str = None,
        hours: int = 1
    ) -> Dict[str, Any]:
        """Get historical metrics."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            historical_data = {'system': [], 'sessions': {}}

            with self.metrics_lock:
                # System metrics
                for metric in self.system_metrics:
                    if metric.timestamp >= cutoff_time:
                        historical_data['system'].append({
                            'timestamp': metric.timestamp.isoformat(),
                            'cpu_percent': metric.cpu_percent,
                            'memory_percent': metric.memory_percent,
                            'memory_used_mb': metric.memory_used_mb,
                            'disk_usage_percent': metric.disk_usage_percent,
                            'active_sessions': metric.active_sessions
                        })

                # Session metrics
                if session_id:
                    sessions_to_process = {session_id: self.session_metrics.get(session_id, deque())}
                else:
                    sessions_to_process = self.session_metrics

                for sid, session_metrics_list in sessions_to_process.items():
                    historical_data['sessions'][sid] = []
                    for metric in session_metrics_list:
                        if metric.timestamp >= cutoff_time:
                            historical_data['sessions'][sid].append({
                                'timestamp': metric.timestamp.isoformat(),
                                'tasks_total': metric.tasks_total,
                                'tasks_completed': metric.tasks_completed,
                                'processing_rate': metric.processing_rate,
                                'error_rate': metric.error_rate,
                                'memory_usage_mb': metric.memory_usage_mb
                            })

            return historical_data

        except Exception as e:
            self.logger.error(f"Failed to get historical metrics: {e}")
            return {'error': str(e)}

    def add_alert_callback(self, callback: Callable):
        """Add callback for alert notifications."""
        self.alert_callbacks.append(callback)

    def resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                self.logger.info(f"Alert resolved: {alert.message}")
                break

    async def cleanup_old_data(self):
        """Clean up old metrics and alerts."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

            # Clean up old alerts (keep resolved alerts for 1 hour)
            alert_cutoff = datetime.now() - timedelta(hours=1)
            self.alerts = [
                alert for alert in self.alerts
                if not alert.resolved or alert.resolved_at > alert_cutoff
            ]

            self.logger.debug("Cleaned up old monitoring data")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old monitoring data: {e}")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()