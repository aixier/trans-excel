"""Batch size dynamic adjustment based on response times."""

import logging
import statistics
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque


logger = logging.getLogger(__name__)


@dataclass
class ResponseTimeMetrics:
    """Metrics for response time tracking."""
    timestamp: datetime
    response_time: float
    batch_size: int
    success: bool
    error_type: Optional[str] = None
    token_count: Optional[int] = None


class BatchOptimizer:
    """Dynamic batch size optimizer based on response times and success rates."""

    def __init__(
        self,
        initial_batch_size: int = 5,
        min_batch_size: int = 1,
        max_batch_size: int = 20,
        target_response_time: float = 10.0,  # Target 10 seconds
        adjustment_factor: float = 0.1,  # 10% adjustment
        history_window: int = 50  # Keep last 50 metrics
    ):
        """
        Initialize BatchOptimizer.

        Args:
            initial_batch_size: Starting batch size
            min_batch_size: Minimum allowed batch size
            max_batch_size: Maximum allowed batch size
            target_response_time: Target response time in seconds
            adjustment_factor: Factor for batch size adjustments
            history_window: Number of recent metrics to keep
        """
        self.current_batch_size = initial_batch_size
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.target_response_time = target_response_time
        self.adjustment_factor = adjustment_factor

        # History tracking
        self.metrics_history: deque = deque(maxlen=history_window)
        self.last_adjustment_time = datetime.now()
        self.adjustment_cooldown = timedelta(seconds=30)  # Wait 30s between adjustments

        self.logger = logging.getLogger(self.__class__.__name__)

        # Performance tracking
        self.total_requests = 0
        self.total_successes = 0
        self.total_failures = 0
        self.total_response_time = 0.0

        self.logger.info(
            f"BatchOptimizer initialized: "
            f"initial_size={initial_batch_size}, "
            f"range=({min_batch_size}, {max_batch_size}), "
            f"target_time={target_response_time}s"
        )

    def record_response(
        self,
        response_time: float,
        batch_size: int,
        success: bool,
        error_type: str = None,
        token_count: int = None
    ):
        """
        Record a response time for batch optimization.

        Args:
            response_time: Response time in seconds
            batch_size: Batch size used
            success: Whether the request succeeded
            error_type: Type of error if failed
            token_count: Number of tokens processed
        """
        metrics = ResponseTimeMetrics(
            timestamp=datetime.now(),
            response_time=response_time,
            batch_size=batch_size,
            success=success,
            error_type=error_type,
            token_count=token_count
        )

        self.metrics_history.append(metrics)

        # Update counters
        self.total_requests += 1
        if success:
            self.total_successes += 1
            self.total_response_time += response_time
        else:
            self.total_failures += 1

        self.logger.debug(
            f"Recorded response: time={response_time:.2f}s, "
            f"batch_size={batch_size}, success={success}"
        )

    def optimize_batch_size(self) -> int:
        """
        Optimize batch size based on recent performance.

        Returns:
            Optimized batch size
        """
        if len(self.metrics_history) < 3:
            # Not enough data for optimization
            return self.current_batch_size

        # Check cooldown period
        if datetime.now() - self.last_adjustment_time < self.adjustment_cooldown:
            return self.current_batch_size

        try:
            # Calculate recent performance metrics
            recent_metrics = list(self.metrics_history)[-10:]  # Last 10 requests
            success_rate = self._calculate_success_rate(recent_metrics)
            avg_response_time = self._calculate_avg_response_time(recent_metrics)

            old_batch_size = self.current_batch_size
            new_batch_size = self._adjust_batch_size(
                avg_response_time, success_rate
            )

            if new_batch_size != old_batch_size:
                self.current_batch_size = new_batch_size
                self.last_adjustment_time = datetime.now()

                self.logger.info(
                    f"Batch size adjusted: {old_batch_size} -> {new_batch_size} "
                    f"(avg_time={avg_response_time:.2f}s, "
                    f"success_rate={success_rate:.1%})"
                )

            return self.current_batch_size

        except Exception as e:
            self.logger.error(f"Failed to optimize batch size: {e}")
            return self.current_batch_size

    def _calculate_success_rate(self, metrics: List[ResponseTimeMetrics]) -> float:
        """Calculate success rate from metrics."""
        if not metrics:
            return 1.0

        successful = sum(1 for m in metrics if m.success)
        return successful / len(metrics)

    def _calculate_avg_response_time(self, metrics: List[ResponseTimeMetrics]) -> float:
        """Calculate average response time from successful requests."""
        successful_times = [
            m.response_time for m in metrics if m.success
        ]

        if not successful_times:
            return self.target_response_time

        return statistics.mean(successful_times)

    def _adjust_batch_size(
        self,
        avg_response_time: float,
        success_rate: float
    ) -> int:
        """
        Adjust batch size based on performance metrics.

        Args:
            avg_response_time: Average response time
            success_rate: Success rate (0-1)

        Returns:
            Adjusted batch size
        """
        current_size = self.current_batch_size

        # If success rate is too low, reduce batch size aggressively
        if success_rate < 0.8:
            adjustment = -max(1, int(current_size * 0.3))  # Reduce by 30%
            self.logger.debug(f"Low success rate ({success_rate:.1%}), reducing batch size")

        # If response time is much higher than target, reduce batch size
        elif avg_response_time > self.target_response_time * 1.5:
            adjustment = -max(1, int(current_size * self.adjustment_factor))
            self.logger.debug(f"High response time ({avg_response_time:.2f}s), reducing batch size")

        # If response time is much lower than target, increase batch size
        elif avg_response_time < self.target_response_time * 0.7 and success_rate > 0.95:
            adjustment = max(1, int(current_size * self.adjustment_factor))
            self.logger.debug(f"Low response time ({avg_response_time:.2f}s), increasing batch size")

        else:
            # Performance is acceptable, no adjustment
            adjustment = 0

        new_size = max(
            self.min_batch_size,
            min(self.max_batch_size, current_size + adjustment)
        )

        return new_size

    def get_recommended_batch_size(self, urgency_factor: float = 1.0) -> int:
        """
        Get recommended batch size with urgency consideration.

        Args:
            urgency_factor: Factor to adjust batch size (0.5 = slower, 2.0 = faster)

        Returns:
            Recommended batch size
        """
        base_size = self.optimize_batch_size()

        # Adjust based on urgency
        if urgency_factor < 1.0:
            # Lower urgency, prefer smaller batches for stability
            adjusted_size = max(1, int(base_size * urgency_factor))
        elif urgency_factor > 1.0:
            # Higher urgency, try larger batches (within limits)
            adjusted_size = min(self.max_batch_size, int(base_size * urgency_factor))
        else:
            adjusted_size = base_size

        return adjusted_size

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        if not self.metrics_history:
            return {
                'current_batch_size': self.current_batch_size,
                'total_requests': 0,
                'success_rate': 0,
                'avg_response_time': 0,
                'recent_metrics': []
            }

        # Recent metrics (last 10)
        recent = list(self.metrics_history)[-10:]
        recent_success_rate = self._calculate_success_rate(recent)
        recent_avg_time = self._calculate_avg_response_time(recent)

        # Overall metrics
        overall_success_rate = (
            self.total_successes / self.total_requests
            if self.total_requests > 0 else 0
        )
        overall_avg_time = (
            self.total_response_time / self.total_successes
            if self.total_successes > 0 else 0
        )

        return {
            'current_batch_size': self.current_batch_size,
            'min_batch_size': self.min_batch_size,
            'max_batch_size': self.max_batch_size,
            'target_response_time': self.target_response_time,
            'total_requests': self.total_requests,
            'total_successes': self.total_successes,
            'total_failures': self.total_failures,
            'overall_success_rate': overall_success_rate,
            'overall_avg_response_time': overall_avg_time,
            'recent_success_rate': recent_success_rate,
            'recent_avg_response_time': recent_avg_time,
            'last_adjustment': self.last_adjustment_time.isoformat(),
            'history_size': len(self.metrics_history)
        }

    def reset_metrics(self):
        """Reset all metrics and counters."""
        self.metrics_history.clear()
        self.total_requests = 0
        self.total_successes = 0
        self.total_failures = 0
        self.total_response_time = 0.0
        self.last_adjustment_time = datetime.now()

        self.logger.info("Batch optimizer metrics reset")

    def export_metrics(self) -> List[Dict[str, Any]]:
        """Export metrics history for analysis."""
        return [
            {
                'timestamp': m.timestamp.isoformat(),
                'response_time': m.response_time,
                'batch_size': m.batch_size,
                'success': m.success,
                'error_type': m.error_type,
                'token_count': m.token_count
            }
            for m in self.metrics_history
        ]