#!/usr/bin/env python3
"""
Architecture compliance tests - Ensure PipelineSession architecture is followed.

These tests prevent regression to old SessionData architecture.
"""

import pytest
from pathlib import Path
import re


class TestArchitectureCompliance:
    """Test suite for architecture compliance."""

    BASE_DIR = Path(__file__).parent.parent

    # Forbidden old architecture imports
    FORBIDDEN_PATTERNS = [
        r'from utils\.session_manager import',
        r'from models\.session_state import',
        r'from services\.split_state import',
        r'from services\.execution_state import',
        r'\bSessionData\b',
        r'\bSessionManager\b(?!.*Pipeline)',  # Allow PipelineSessionManager
        r'session\.session_status\.update_stage',  # Old pattern
        r'session\.session_status\.stage',  # Old pattern
    ]

    # Required new architecture patterns (should exist in codebase)
    REQUIRED_PATTERNS = [
        r'from utils\.pipeline_session_manager import',
        r'from models\.pipeline_session import',
        r'\bPipelineSession\b',
        r'\bTransformationStage\b',
    ]

    # Files to exclude from checks
    EXCLUDED_FILES = [
        'migrate_to_pipeline_architecture.py',
        'test_architecture_compliance.py',
        '_archived_old_architecture',
        '__pycache__',
        '.pytest_cache',
    ]

    def _get_python_files(self):
        """Get all Python files to check."""
        python_files = []
        for py_file in self.BASE_DIR.rglob("*.py"):
            # Skip excluded files/directories
            if any(excluded in str(py_file) for excluded in self.EXCLUDED_FILES):
                continue
            python_files.append(py_file)
        return python_files

    def test_no_old_architecture_imports(self):
        """Test that no code uses old architecture imports."""
        violations = []

        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for pattern in self.FORBIDDEN_PATTERNS:
                    if re.search(pattern, content):
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if re.search(pattern, line):
                                # Skip comments and docstrings
                                stripped = line.strip()
                                if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                                    continue

                                violations.append({
                                    'file': py_file.relative_to(self.BASE_DIR),
                                    'line': i,
                                    'pattern': pattern,
                                    'content': line.strip()
                                })
            except Exception as e:
                pytest.fail(f"Failed to read {py_file}: {e}")

        if violations:
            error_msg = "\n❌ Found old architecture usage:\n\n"
            for v in violations:
                error_msg += f"  {v['file']}:{v['line']}\n"
                error_msg += f"    Pattern: {v['pattern']}\n"
                error_msg += f"    Code: {v['content']}\n\n"
            pytest.fail(error_msg)

    def test_new_architecture_present(self):
        """Test that new architecture is being used."""
        codebase_content = ""

        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    codebase_content += f.read() + "\n"
            except Exception:
                pass

        missing_patterns = []
        for pattern in self.REQUIRED_PATTERNS:
            if not re.search(pattern, codebase_content):
                missing_patterns.append(pattern)

        if missing_patterns:
            error_msg = "\n❌ Required new architecture patterns not found:\n\n"
            for pattern in missing_patterns:
                error_msg += f"  - {pattern}\n"
            pytest.fail(error_msg)

    def test_pipeline_session_manager_singleton(self):
        """Test that pipeline_session_manager is a singleton."""
        from utils.pipeline_session_manager import pipeline_session_manager, PipelineSessionManager

        # Should be a singleton instance
        assert isinstance(pipeline_session_manager, PipelineSessionManager)

        # Verify key methods exist
        assert hasattr(pipeline_session_manager, 'create_session')
        assert hasattr(pipeline_session_manager, 'get_session')
        assert hasattr(pipeline_session_manager, 'get_tasks')
        assert hasattr(pipeline_session_manager, 'set_tasks')

    def test_transformation_stage_enum(self):
        """Test that TransformationStage enum has correct values."""
        from models.pipeline_session import TransformationStage

        expected_stages = {
            'created', 'input_loaded', 'split_complete',
            'executing', 'completed', 'failed'
        }

        actual_stages = {stage.value for stage in TransformationStage}

        assert actual_stages == expected_stages, (
            f"TransformationStage values mismatch. "
            f"Expected: {expected_stages}, Got: {actual_stages}"
        )

    def test_pipeline_session_structure(self):
        """Test that PipelineSession has correct structure."""
        from models.pipeline_session import PipelineSession

        # Required attributes for session-per-transformation pattern
        required_attrs = [
            'session_id',
            'parent_session_id',  # For chaining
            'input_state',        # Data state N
            'tasks',              # Task table (intermediate)
            'output_state',       # Data state N+1
            'stage',              # TransformationStage
            'metadata',
        ]

        # Create a test instance
        test_session = PipelineSession(session_id="test")

        missing_attrs = []
        for attr in required_attrs:
            if not hasattr(test_session, attr):
                missing_attrs.append(attr)

        if missing_attrs:
            pytest.fail(
                f"PipelineSession missing required attributes: {missing_attrs}"
            )

    def test_old_architecture_files_archived(self):
        """Test that old architecture files are archived or deleted."""
        old_files = [
            self.BASE_DIR / 'utils' / 'session_manager.py',
            self.BASE_DIR / 'models' / 'session_state.py',
            self.BASE_DIR / 'services' / 'split_state.py',
            self.BASE_DIR / 'services' / 'execution_state.py',
        ]

        existing_old_files = [f for f in old_files if f.exists()]

        if existing_old_files:
            error_msg = "\n❌ Old architecture files still exist (should be archived):\n\n"
            for f in existing_old_files:
                error_msg += f"  - {f.relative_to(self.BASE_DIR)}\n"
            pytest.fail(error_msg)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
