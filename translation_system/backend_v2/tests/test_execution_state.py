"""Unit tests for ExecutionProgress state module."""

import pytest
from services.execution_state import ExecutionProgress, ExecutionStatus


class TestExecutionProgressInitialization:
    """Test initialization of ExecutionProgress."""

    def test_default_initialization(self):
        """Test default initialization values."""
        progress = ExecutionProgress("test_session")

        assert progress.session_id == "test_session"
        assert progress.status == ExecutionStatus.IDLE
        assert progress.ready_for_monitoring is False
        assert progress.ready_for_download is False
        assert progress.statistics == {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "processing": 0
        }
        assert progress.error is None


class TestExecutionProgressStates:
    """Test different execution states."""

    def test_mark_initializing(self):
        """Test mark_initializing() state."""
        progress = ExecutionProgress("test_session")
        progress.mark_initializing()

        assert progress.status == ExecutionStatus.INITIALIZING
        assert progress.ready_for_monitoring is False

    def test_mark_running(self):
        """Test mark_running() enables monitoring."""
        progress = ExecutionProgress("test_session")
        progress.mark_running()

        assert progress.status == ExecutionStatus.RUNNING
        assert progress.ready_for_monitoring is True  # ✨ KEY: Can start monitoring
        assert progress.ready_for_download is False

    def test_mark_completed(self):
        """Test mark_completed() enables download."""
        progress = ExecutionProgress("test_session")
        progress.mark_completed()

        assert progress.status == ExecutionStatus.COMPLETED
        assert progress.ready_for_download is True  # ✨ KEY: Can download results

    def test_mark_failed(self):
        """Test mark_failed() sets error."""
        progress = ExecutionProgress("test_session")
        error_msg = "Execution error"
        progress.mark_failed(error_msg)

        assert progress.status == ExecutionStatus.FAILED
        assert progress.error == error_msg


class TestExecutionProgressReadyFlags:
    """Test ready flag methods."""

    def test_is_ready_for_monitoring_false_initially(self):
        """Test is_ready_for_monitoring() is False initially."""
        progress = ExecutionProgress("test_session")
        assert progress.is_ready_for_monitoring() is False

    def test_is_ready_for_monitoring_true_when_running(self):
        """Test is_ready_for_monitoring() is True when running."""
        progress = ExecutionProgress("test_session")
        progress.mark_running()
        assert progress.is_ready_for_monitoring() is True

    def test_is_ready_for_download_false_initially(self):
        """Test is_ready_for_download() is False initially."""
        progress = ExecutionProgress("test_session")
        assert progress.is_ready_for_download() is False

    def test_is_ready_for_download_true_when_completed(self):
        """Test is_ready_for_download() is True when completed."""
        progress = ExecutionProgress("test_session")
        progress.mark_completed()
        assert progress.is_ready_for_download() is True


class TestExecutionProgressStatistics:
    """Test statistics update."""

    def test_update_statistics(self):
        """Test update_statistics() updates stats."""
        progress = ExecutionProgress("test_session")
        stats = {
            "total": 100,
            "completed": 50,
            "failed": 5,
            "processing": 45
        }
        progress.update_statistics(stats)

        assert progress.statistics["total"] == 100
        assert progress.statistics["completed"] == 50
        assert progress.statistics["failed"] == 5
        assert progress.statistics["processing"] == 45


class TestExecutionProgressSerialization:
    """Test to_dict() serialization."""

    def test_to_dict_basic(self):
        """Test basic to_dict() output."""
        progress = ExecutionProgress("test_session")
        data = progress.to_dict()

        assert data["session_id"] == "test_session"
        assert data["status"] == "idle"
        assert data["ready_for_monitoring"] is False
        assert data["ready_for_download"] is False
        assert "statistics" in data
        assert "updated_at" in data

    def test_to_dict_with_running_state(self):
        """Test to_dict() when running."""
        progress = ExecutionProgress("test_session")
        progress.mark_running()
        progress.update_statistics({"total": 100, "completed": 25})
        data = progress.to_dict()

        assert data["status"] == "running"
        assert data["ready_for_monitoring"] is True
        assert data["ready_for_download"] is False
        assert data["statistics"]["total"] == 100


class TestExecutionProgressWorkflow:
    """Test complete workflow scenarios."""

    def test_complete_workflow(self):
        """Test complete execution workflow."""
        progress = ExecutionProgress("test_session")

        # Start initializing
        progress.mark_initializing()
        assert progress.is_ready_for_monitoring() is False
        assert progress.is_ready_for_download() is False

        # Start running
        progress.mark_running()
        assert progress.is_ready_for_monitoring() is True  # ✨ Can monitor now
        assert progress.is_ready_for_download() is False

        # Update statistics during execution
        progress.update_statistics({"total": 100, "completed": 50, "processing": 50})
        assert progress.is_ready_for_monitoring() is True

        # Complete execution
        progress.mark_completed()
        assert progress.is_ready_for_download() is True  # ✨ Can download now
