"""Comprehensive tests for the Orchestrator module.

Tests cover:
1. Single stage execution
2. Multi-stage serial execution
3. Dependency management and context passing
4. Pipeline validation (invalid dependencies)
5. Circular dependency detection
6. Stage failure handling
7. Result storage and retrieval
"""

import pytest
import pandas as pd
from typing import Dict, Any

from services.orchestrator import (
    BaseOrchestrator,
    PipelineStage,
    OrchestratorError,
    InvalidPipelineError,
    CircularDependencyError,
    StageExecutionError
)
from services.data_state import ExcelState, Cell
from services.splitter import SplitRule
from models.excel_dataframe import ExcelDataFrame


# ============================================================================
# Mock Classes
# ============================================================================

class MockTransformer:
    """Mock transformer for testing.

    This transformer simulates task execution without actually performing
    any real transformations. It marks all tasks as completed and generates
    mock results.
    """

    def __init__(self, processor=None):
        """Initialize mock transformer.

        Args:
            processor: Optional processor (not used in mock)
        """
        self.processor = processor
        self.execute_count = 0

    def execute(self, data_state, tasks, context=None):
        """Execute mock transformation.

        Args:
            data_state: Current DataState
            tasks: TaskDataFrame to execute
            context: Optional context from dependencies

        Returns:
            New DataState (copy of input with modifications)
        """
        self.execute_count += 1

        # Create a copy of the state
        new_state = data_state.copy()

        # Mark all tasks as completed and add mock results
        for idx, task in tasks.iterrows():
            tasks.loc[idx, 'status'] = 'completed'
            tasks.loc[idx, 'result'] = f"mock_result_{idx}"

            # Update state with mock result
            sheet = task['sheet_name']
            row = task['row_idx']
            col = task['col_idx']
            new_state.set_cell_value(sheet, row, col, f"mock_result_{idx}")

        return new_state


class MockProcessor:
    """Mock processor for testing."""

    def __init__(self, result_prefix="processed"):
        """Initialize mock processor.

        Args:
            result_prefix: Prefix for mock results
        """
        self.result_prefix = result_prefix
        self.process_count = 0

    def process(self, task, context=None):
        """Process a mock task.

        Args:
            task: Task to process
            context: Optional context

        Returns:
            Mock result string
        """
        self.process_count += 1
        return f"{self.result_prefix}_{self.process_count}"


class MockRule(SplitRule):
    """Mock rule for testing."""

    def __init__(self, match_count=5):
        """Initialize mock rule.

        Args:
            match_count: Number of tasks to generate
        """
        self.match_count = match_count

    def match(self, cell, context: Dict[str, Any]) -> bool:
        """Always returns True for simplicity."""
        return True

    def create_task(self, cell, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a mock task."""
        return {
            'task_id': f"task_{context['row_idx']}_{context['col_idx']}",
            'operation': 'mock',
            'priority': 5,
            'sheet_name': context['sheet_name'],
            'row_idx': context['row_idx'],
            'col_idx': context['col_idx'],
            'cell_ref': f"R{context['row_idx']}C{context['col_idx']}",
            'source_text': str(cell.value) if hasattr(cell, 'value') else str(cell),
            'source_lang': 'EN',
            'target_lang': 'CH',
            'status': 'pending',
        }


class AlwaysMatchRule(SplitRule):
    """Rule that matches all cells."""

    def match(self, cell, context: Dict[str, Any]) -> bool:
        """Always returns True."""
        return True

    def create_task(self, cell, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a mock task."""
        return {
            'task_id': f"task_{context['row_idx']}_{context['col_idx']}",
            'operation': 'mock',
            'priority': 5,
            'sheet_name': context['sheet_name'],
            'row_idx': context['row_idx'],
            'col_idx': context['col_idx'],
            'cell_ref': f"R{context['row_idx']}C{context['col_idx']}",
            'source_text': str(cell.value) if hasattr(cell, 'value') else str(cell),
            'source_lang': 'EN',
            'target_lang': 'CH',
            'status': 'pending',
        }


class FailingTransformer:
    """Transformer that always fails (for error testing)."""

    def execute(self, data_state, tasks, context=None):
        """Raise an error."""
        raise RuntimeError("Transformer intentionally failed")


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_excel_df():
    """Create a sample ExcelDataFrame for testing."""
    excel_df = ExcelDataFrame()

    # Create sample data
    df = pd.DataFrame({
        'EN': ['Hello', 'World', '', 'Test', ''],
        'CH': ['', '', '你好', '', '测试'],
    })

    # Use the proper interface to add sheet
    excel_df.add_sheet('Sheet1', df)

    return excel_df


@pytest.fixture
def sample_data_state(sample_excel_df):
    """Create a sample DataState for testing."""
    return ExcelState.from_excel_dataframe(sample_excel_df)


@pytest.fixture
def mock_transformer():
    """Create a mock transformer."""
    return MockTransformer(MockProcessor())


@pytest.fixture
def mock_rule():
    """Create a mock rule."""
    return AlwaysMatchRule()


# ============================================================================
# Test Cases
# ============================================================================

class TestPipelineStage:
    """Test PipelineStage dataclass."""

    def test_create_stage(self, mock_transformer, mock_rule):
        """Test creating a valid stage."""
        stage = PipelineStage(
            stage_id='test_stage',
            splitter_rules=[mock_rule],
            transformer=mock_transformer
        )

        assert stage.stage_id == 'test_stage'
        assert len(stage.splitter_rules) == 1
        assert stage.transformer is mock_transformer
        assert stage.depends_on == []

    def test_stage_with_dependencies(self, mock_transformer, mock_rule):
        """Test creating a stage with dependencies."""
        stage = PipelineStage(
            stage_id='test_stage',
            splitter_rules=[mock_rule],
            transformer=mock_transformer,
            depends_on=['stage1', 'stage2']
        )

        assert stage.depends_on == ['stage1', 'stage2']
        assert stage.has_dependencies() is True

    def test_stage_validation_empty_id(self, mock_transformer, mock_rule):
        """Test stage validation - empty stage_id."""
        with pytest.raises(ValueError, match="stage_id cannot be empty"):
            PipelineStage(
                stage_id='',
                splitter_rules=[mock_rule],
                transformer=mock_transformer
            )

    def test_stage_validation_empty_rules(self, mock_transformer):
        """Test stage validation - empty rules list."""
        with pytest.raises(ValueError, match="splitter_rules cannot be empty"):
            PipelineStage(
                stage_id='test',
                splitter_rules=[],
                transformer=mock_transformer
            )

    def test_stage_validation_none_transformer(self, mock_rule):
        """Test stage validation - None transformer."""
        with pytest.raises(ValueError, match="transformer cannot be None"):
            PipelineStage(
                stage_id='test',
                splitter_rules=[mock_rule],
                transformer=None
            )


class TestOrchestrator:
    """Test Orchestrator base class."""

    def test_add_stage(self, mock_transformer, mock_rule):
        """Test adding a stage to the orchestrator."""
        orchestrator = BaseOrchestrator()
        stage = PipelineStage(
            stage_id='test',
            splitter_rules=[mock_rule],
            transformer=mock_transformer
        )

        orchestrator.add_stage(stage)

        assert orchestrator.get_stage_count() == 1
        assert orchestrator.get_stage('test') == stage

    def test_add_duplicate_stage(self, mock_transformer, mock_rule):
        """Test adding duplicate stage IDs."""
        orchestrator = BaseOrchestrator()

        stage1 = PipelineStage('test', [mock_rule], mock_transformer)
        stage2 = PipelineStage('test', [mock_rule], mock_transformer)

        orchestrator.add_stage(stage1)

        with pytest.raises(ValueError, match="Duplicate stage_id"):
            orchestrator.add_stage(stage2)

    def test_get_nonexistent_stage(self):
        """Test getting a non-existent stage."""
        orchestrator = BaseOrchestrator()

        with pytest.raises(ValueError, match="No stage found"):
            orchestrator.get_stage('nonexistent')

    def test_clear(self, mock_transformer, mock_rule):
        """Test clearing orchestrator."""
        orchestrator = BaseOrchestrator()
        stage = PipelineStage('test', [mock_rule], mock_transformer)
        orchestrator.add_stage(stage)

        orchestrator.clear()

        assert orchestrator.get_stage_count() == 0
        assert len(orchestrator.results) == 0


class TestPipelineValidation:
    """Test pipeline validation logic."""

    def test_validate_empty_pipeline(self):
        """Test validation of empty pipeline."""
        orchestrator = BaseOrchestrator()

        assert orchestrator.validate_pipeline() is False

    def test_validate_valid_pipeline(self, mock_transformer, mock_rule):
        """Test validation of valid pipeline."""
        orchestrator = BaseOrchestrator()

        orchestrator.add_stage(PipelineStage('stage1', [mock_rule], mock_transformer))
        orchestrator.add_stage(PipelineStage(
            'stage2', [mock_rule], mock_transformer, depends_on=['stage1']
        ))

        assert orchestrator.validate_pipeline() is True

    def test_validate_invalid_dependency(self, mock_transformer, mock_rule):
        """Test validation with invalid dependency reference."""
        orchestrator = BaseOrchestrator()

        orchestrator.add_stage(PipelineStage(
            'stage1',
            [mock_rule],
            mock_transformer,
            depends_on=['nonexistent']  # Invalid dependency
        ))

        with pytest.raises(InvalidPipelineError, match="non-existent"):
            orchestrator.validate_pipeline()

    def test_detect_circular_dependency_simple(self, mock_transformer, mock_rule):
        """Test detection of simple circular dependency (A -> A)."""
        orchestrator = BaseOrchestrator()

        orchestrator.add_stage(PipelineStage(
            'stage1',
            [mock_rule],
            mock_transformer,
            depends_on=['stage1']  # Self-dependency
        ))

        with pytest.raises(CircularDependencyError, match="Circular dependency"):
            orchestrator.validate_pipeline()

    def test_detect_circular_dependency_complex(self, mock_transformer, mock_rule):
        """Test detection of complex circular dependency (A -> B -> C -> A)."""
        orchestrator = BaseOrchestrator()

        orchestrator.add_stage(PipelineStage(
            'A', [mock_rule], mock_transformer, depends_on=['C']
        ))
        orchestrator.add_stage(PipelineStage(
            'B', [mock_rule], mock_transformer, depends_on=['A']
        ))
        orchestrator.add_stage(PipelineStage(
            'C', [mock_rule], mock_transformer, depends_on=['B']
        ))

        with pytest.raises(CircularDependencyError):
            orchestrator.validate_pipeline()


class TestPipelineExecution:
    """Test pipeline execution."""

    def test_single_stage_execution(self, sample_data_state, mock_transformer, mock_rule):
        """Test execution of a single stage."""
        orchestrator = BaseOrchestrator()

        orchestrator.add_stage(PipelineStage(
            stage_id='test_stage',
            splitter_rules=[mock_rule],
            transformer=mock_transformer
        ))

        final_state = orchestrator.execute(sample_data_state)

        assert final_state is not None
        assert 'test_stage' in orchestrator.results
        assert mock_transformer.execute_count == 1

    def test_multi_stage_execution(self, sample_data_state, mock_rule):
        """Test execution of multiple stages in sequence."""
        orchestrator = BaseOrchestrator()

        transformer1 = MockTransformer(MockProcessor("stage1"))
        transformer2 = MockTransformer(MockProcessor("stage2"))

        orchestrator.add_stage(PipelineStage('stage1', [mock_rule], transformer1))
        orchestrator.add_stage(PipelineStage('stage2', [mock_rule], transformer2))

        final_state = orchestrator.execute(sample_data_state)

        assert final_state is not None
        assert 'stage1' in orchestrator.results
        assert 'stage2' in orchestrator.results
        assert transformer1.execute_count == 1
        assert transformer2.execute_count == 1

    def test_execution_with_dependencies(self, sample_data_state, mock_rule):
        """Test execution with stage dependencies."""
        orchestrator = BaseOrchestrator()

        transformer1 = MockTransformer(MockProcessor("translate"))
        transformer2 = MockTransformer(MockProcessor("uppercase"))

        orchestrator.add_stage(PipelineStage('translate', [mock_rule], transformer1))
        orchestrator.add_stage(PipelineStage(
            'uppercase',
            [mock_rule],
            transformer2,
            depends_on=['translate']  # Depends on translate
        ))

        final_state = orchestrator.execute(sample_data_state)

        # Verify both stages executed
        assert 'translate' in orchestrator.results
        assert 'uppercase' in orchestrator.results

        # Verify context was passed
        uppercase_result = orchestrator.results['uppercase']
        assert 'context' in uppercase_result
        assert 'translate' in uppercase_result['context']

    def test_stage_failure_handling(self, sample_data_state, mock_rule):
        """Test handling of stage execution failure."""
        orchestrator = BaseOrchestrator()

        orchestrator.add_stage(PipelineStage(
            'failing_stage',
            [mock_rule],
            FailingTransformer()
        ))

        with pytest.raises(StageExecutionError, match="failing_stage"):
            orchestrator.execute(sample_data_state)


class TestResultRetrieval:
    """Test result storage and retrieval."""

    def test_get_stage_result(self, sample_data_state, mock_transformer, mock_rule):
        """Test retrieving stage result."""
        orchestrator = BaseOrchestrator()
        orchestrator.add_stage(PipelineStage('test', [mock_rule], mock_transformer))

        orchestrator.execute(sample_data_state)

        result = orchestrator.get_stage_result('test')

        assert 'data_state' in result
        assert 'tasks' in result
        assert 'context' in result

    def test_get_stage_tasks(self, sample_data_state, mock_transformer, mock_rule):
        """Test retrieving stage tasks."""
        orchestrator = BaseOrchestrator()
        orchestrator.add_stage(PipelineStage('test', [mock_rule], mock_transformer))

        orchestrator.execute(sample_data_state)

        tasks = orchestrator.get_stage_tasks('test')

        assert tasks is not None
        assert len(tasks) > 0

    def test_get_final_state(self, sample_data_state, mock_transformer, mock_rule):
        """Test retrieving final state."""
        orchestrator = BaseOrchestrator()
        orchestrator.add_stage(PipelineStage('test', [mock_rule], mock_transformer))

        orchestrator.execute(sample_data_state)

        final_state = orchestrator.get_final_state()

        assert final_state is not None

    def test_get_final_state_before_execution(self):
        """Test getting final state before execution."""
        orchestrator = BaseOrchestrator()

        with pytest.raises(RuntimeError, match="not been executed"):
            orchestrator.get_final_state()

    def test_execution_summary(self, sample_data_state, mock_rule):
        """Test execution summary generation."""
        orchestrator = BaseOrchestrator()

        transformer1 = MockTransformer()
        transformer2 = MockTransformer()

        orchestrator.add_stage(PipelineStage('stage1', [mock_rule], transformer1))
        orchestrator.add_stage(PipelineStage('stage2', [mock_rule], transformer2))

        orchestrator.execute(sample_data_state)

        summary = orchestrator.get_execution_summary()

        assert summary['total_stages'] == 2
        assert summary['completed_stages'] == 2
        assert len(summary['stages']) == 2
        assert summary['stages'][0]['stage_id'] == 'stage1'
        assert summary['stages'][0]['completed'] is True


class TestContextPassing:
    """Test context building and passing between stages."""

    def test_context_includes_dependencies(self, sample_data_state, mock_rule):
        """Test that context includes all dependent stage results."""
        orchestrator = BaseOrchestrator()

        transformer1 = MockTransformer()
        transformer2 = MockTransformer()
        transformer3 = MockTransformer()

        orchestrator.add_stage(PipelineStage('stage1', [mock_rule], transformer1))
        orchestrator.add_stage(PipelineStage('stage2', [mock_rule], transformer2))
        orchestrator.add_stage(PipelineStage(
            'stage3',
            [mock_rule],
            transformer3,
            depends_on=['stage1', 'stage2']  # Depends on both
        ))

        orchestrator.execute(sample_data_state)

        # Check context for stage3
        stage3_result = orchestrator.results['stage3']
        context = stage3_result['context']

        assert 'stage1' in context
        assert 'stage2' in context
        assert len(context) == 2

    def test_context_empty_without_dependencies(self, sample_data_state, mock_transformer, mock_rule):
        """Test that context is empty when stage has no dependencies."""
        orchestrator = BaseOrchestrator()
        orchestrator.add_stage(PipelineStage('test', [mock_rule], mock_transformer))

        orchestrator.execute(sample_data_state)

        result = orchestrator.results['test']
        context = result['context']

        assert context == {}


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests with real-like scenarios."""

    def test_translation_pipeline(self, sample_data_state, mock_rule):
        """Test a realistic translation + CAPS pipeline."""
        orchestrator = BaseOrchestrator()

        # Stage 1: Translation
        translate_transformer = MockTransformer(MockProcessor("translate"))
        orchestrator.add_stage(PipelineStage(
            stage_id='translate',
            splitter_rules=[mock_rule],
            transformer=translate_transformer
        ))

        # Stage 2: CAPS (depends on translation)
        caps_transformer = MockTransformer(MockProcessor("uppercase"))
        orchestrator.add_stage(PipelineStage(
            stage_id='uppercase',
            splitter_rules=[mock_rule],
            transformer=caps_transformer,
            depends_on=['translate']
        ))

        # Execute
        final_state = orchestrator.execute(sample_data_state)

        # Verify execution
        assert final_state is not None
        assert orchestrator.get_stage_count() == 2
        assert len(orchestrator.results) == 2

        # Verify dependency
        uppercase_result = orchestrator.results['uppercase']
        assert 'translate' in uppercase_result['context']

        # Verify summary
        summary = orchestrator.get_execution_summary()
        assert summary['total_stages'] == 2
        assert summary['completed_stages'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
