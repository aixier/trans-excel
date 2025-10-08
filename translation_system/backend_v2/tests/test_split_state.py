"""Unit tests for SplitProgress state module."""

import pytest
from services.split_state import SplitProgress, SplitStatus, SplitStage


class TestSplitProgressInitialization:
    """Test initialization of SplitProgress."""

    def test_default_initialization(self):
        """Test default initialization values."""
        progress = SplitProgress("test_session")

        assert progress.session_id == "test_session"
        assert progress.status == SplitStatus.NOT_STARTED
        assert progress.stage == SplitStage.ANALYZING
        assert progress.progress == 0.0
        assert progress.message == ""
        assert progress.ready_for_next_stage is False  # ✨ KEY: Must be False initially
        assert progress.metadata == {}
        assert progress.error is None


class TestSplitProgressSaving:
    """Test the saving state functionality - KEY for race condition fix."""

    def test_mark_saving(self):
        """Test mark_saving() sets correct state."""
        progress = SplitProgress("test_session")

        # Mark as saving
        progress.mark_saving()

        assert progress.status == SplitStatus.SAVING
        assert progress.stage == SplitStage.SAVING
        assert progress.ready_for_next_stage is False  # ✨ KEY: Must be False during save


class TestSplitProgressCompletion:
    """Test the completion state functionality."""

    def test_mark_completed(self):
        """Test mark_completed() sets ready_for_next_stage=True."""
        progress = SplitProgress("test_session")
        metadata = {"task_count": 100, "batch_count": 10}

        # Mark as completed
        progress.mark_completed(metadata)

        assert progress.status == SplitStatus.COMPLETED
        assert progress.stage == SplitStage.DONE
        assert progress.progress == 100.0
        assert progress.ready_for_next_stage is True  # ✨ KEY: Only True here
        assert progress.metadata == metadata


class TestSplitProgressFailed:
    """Test the failed state functionality."""

    def test_mark_failed(self):
        """Test mark_failed() sets error and ready=False."""
        progress = SplitProgress("test_session")
        error_msg = "Test error"

        # Mark as failed
        progress.mark_failed(error_msg)

        assert progress.status == SplitStatus.FAILED
        assert progress.error == error_msg
        assert progress.ready_for_next_stage is False


class TestSplitProgressIsReady:
    """Test the is_ready() validation method - KEY for execute_api."""

    def test_is_ready_initial_state(self):
        """Test is_ready() returns False initially."""
        progress = SplitProgress("test_session")
        assert progress.is_ready() is False

    def test_is_ready_while_saving(self):
        """Test is_ready() returns False while saving."""
        progress = SplitProgress("test_session")
        progress.mark_saving()
        assert progress.is_ready() is False  # ✨ KEY: Not ready during save

    def test_is_ready_when_completed(self):
        """Test is_ready() returns True only when completed."""
        progress = SplitProgress("test_session")
        progress.mark_completed({"task_count": 100})
        assert progress.is_ready() is True  # ✨ KEY: Ready after completion

    def test_is_ready_when_failed(self):
        """Test is_ready() returns False when failed."""
        progress = SplitProgress("test_session")
        progress.mark_failed("error")
        assert progress.is_ready() is False


class TestSplitProgressSerialization:
    """Test to_dict() serialization."""

    def test_to_dict_basic(self):
        """Test basic to_dict() output."""
        progress = SplitProgress("test_session")
        data = progress.to_dict()

        assert data["session_id"] == "test_session"
        assert data["status"] == "not_started"
        assert data["stage"] == "analyzing"
        assert data["progress"] == 0.0
        assert data["message"] == ""
        assert data["ready_for_next_stage"] is False  # ✨ KEY field
        assert "updated_at" in data

    def test_to_dict_with_saving_state(self):
        """Test to_dict() during saving state."""
        progress = SplitProgress("test_session")
        progress.mark_saving()
        progress.update(progress=95, message="Saving...")
        data = progress.to_dict()

        assert data["status"] == "saving"
        assert data["stage"] == "saving"
        assert data["progress"] == 95
        assert data["ready_for_next_stage"] is False  # ✨ KEY: False during save

    def test_to_dict_with_metadata(self):
        """Test to_dict() includes metadata when completed."""
        progress = SplitProgress("test_session")
        metadata = {"task_count": 150, "batch_count": 15}
        progress.mark_completed(metadata)
        data = progress.to_dict()

        assert data["metadata"] == metadata
        assert data["status"] == "completed"
        assert data["ready_for_next_stage"] is True


class TestSplitProgressWorkflow:
    """Test complete workflow scenarios."""

    def test_complete_workflow(self):
        """Test complete split workflow."""
        progress = SplitProgress("test_session")

        # Start processing
        progress.update(
            status=SplitStatus.PROCESSING,
            stage=SplitStage.ANALYZING,
            progress=10,
            message="Analyzing..."
        )
        assert progress.is_ready() is False

        # Continue processing
        progress.update(progress=50, message="Allocating batches...")
        assert progress.is_ready() is False

        # Enter saving state
        progress.mark_saving()
        assert progress.status == SplitStatus.SAVING
        assert progress.is_ready() is False  # ✨ KEY: Not ready during save

        # Complete
        progress.mark_completed({"task_count": 200})
        assert progress.is_ready() is True  # ✨ KEY: Ready only after completion

    def test_race_condition_scenario(self):
        """Test the race condition scenario that we're fixing."""
        progress = SplitProgress("test_session")

        # Simulate the old behavior (without saving state)
        # This would have caused ready=True too early
        progress.update(
            status=SplitStatus.PROCESSING,
            progress=90,
            message="Creating DataFrame..."
        )
        assert progress.is_ready() is False

        # ✨ NEW: Mark as saving BEFORE actual save
        progress.mark_saving()
        assert progress.ready_for_next_stage is False

        # Simulate save taking 42 seconds
        # During this time, frontend polling gets ready_for_next_stage=False
        # and won't try to execute

        # After save completes and verification succeeds
        progress.mark_completed({"task_count": 500})
        assert progress.ready_for_next_stage is True

        # Now frontend can safely proceed to execution
