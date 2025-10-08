"""Unit tests for SessionStatus state module."""

import pytest
from models.session_state import SessionStatus, SessionStage


class TestSessionStatusInitialization:
    """Test initialization of SessionStatus."""

    def test_default_initialization(self):
        """Test default initialization values."""
        status = SessionStatus("test_session")

        assert status.session_id == "test_session"
        assert status.stage == SessionStage.CREATED
        assert status.updated_at is not None


class TestSessionStatusUpdateStage:
    """Test update_stage functionality."""

    def test_update_stage(self):
        """Test update_stage() updates the stage."""
        status = SessionStatus("test_session")

        # Update to ANALYZED
        status.update_stage(SessionStage.ANALYZED)
        assert status.stage == SessionStage.ANALYZED

        # Update to SPLIT_COMPLETE
        status.update_stage(SessionStage.SPLIT_COMPLETE)
        assert status.stage == SessionStage.SPLIT_COMPLETE

        # Update to EXECUTING
        status.update_stage(SessionStage.EXECUTING)
        assert status.stage == SessionStage.EXECUTING

        # Update to COMPLETED
        status.update_stage(SessionStage.COMPLETED)
        assert status.stage == SessionStage.COMPLETED


class TestSessionStagePermissions:
    """Test can_split(), can_execute(), can_download() methods."""

    def test_can_split(self):
        """Test can_split() returns True only in ANALYZED stage."""
        assert SessionStage.CREATED.can_split() is False
        assert SessionStage.ANALYZED.can_split() is True  # ✨ Only here
        assert SessionStage.SPLIT_COMPLETE.can_split() is False
        assert SessionStage.EXECUTING.can_split() is False
        assert SessionStage.COMPLETED.can_split() is False
        assert SessionStage.FAILED.can_split() is False

    def test_can_execute(self):
        """Test can_execute() returns True only in SPLIT_COMPLETE stage."""
        assert SessionStage.CREATED.can_execute() is False
        assert SessionStage.ANALYZED.can_execute() is False
        assert SessionStage.SPLIT_COMPLETE.can_execute() is True  # ✨ Only here
        assert SessionStage.EXECUTING.can_execute() is False
        assert SessionStage.COMPLETED.can_execute() is False
        assert SessionStage.FAILED.can_execute() is False

    def test_can_download(self):
        """Test can_download() returns True only in COMPLETED stage."""
        assert SessionStage.CREATED.can_download() is False
        assert SessionStage.ANALYZED.can_download() is False
        assert SessionStage.SPLIT_COMPLETE.can_download() is False
        assert SessionStage.EXECUTING.can_download() is False
        assert SessionStage.COMPLETED.can_download() is True  # ✨ Only here
        assert SessionStage.FAILED.can_download() is False


class TestSessionStatusSerialization:
    """Test to_dict() serialization."""

    def test_to_dict(self):
        """Test to_dict() output."""
        status = SessionStatus("test_session")
        status.update_stage(SessionStage.ANALYZED)
        data = status.to_dict()

        assert data["session_id"] == "test_session"
        assert data["stage"] == "analyzed"
        assert "updated_at" in data


class TestSessionStatusWorkflow:
    """Test complete session workflow."""

    def test_complete_workflow(self):
        """Test complete session stage workflow."""
        status = SessionStatus("test_session")

        # Initial: CREATED
        assert status.stage == SessionStage.CREATED
        assert not status.stage.can_split()

        # After upload: ANALYZED
        status.update_stage(SessionStage.ANALYZED)
        assert status.stage.can_split()
        assert not status.stage.can_execute()

        # After split: SPLIT_COMPLETE
        status.update_stage(SessionStage.SPLIT_COMPLETE)
        assert not status.stage.can_split()
        assert status.stage.can_execute()

        # During execution: EXECUTING
        status.update_stage(SessionStage.EXECUTING)
        assert not status.stage.can_execute()
        assert not status.stage.can_download()

        # After execution: COMPLETED
        status.update_stage(SessionStage.COMPLETED)
        assert status.stage.can_download()
