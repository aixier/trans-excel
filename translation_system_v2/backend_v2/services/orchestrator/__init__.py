"""Orchestrator module for pipeline execution and dependency management.

This module provides the orchestrator layer responsible for coordinating
multi-stage data transformation pipelines.

Key components:
- PipelineStage: Configuration for a single pipeline stage
- Orchestrator: Abstract base class for orchestrators
- BaseOrchestrator: Concrete implementation with dependency management

Exceptions:
- OrchestratorError: Base exception for orchestrator errors
- InvalidPipelineError: Raised when pipeline configuration is invalid
- CircularDependencyError: Raised when circular dependencies detected
- StageExecutionError: Raised when a stage fails to execute

Example:
    >>> from services.orchestrator import BaseOrchestrator, PipelineStage
    >>> from services.splitter import EmptyCellRule, YellowCellRule
    >>> from services.processors import LLMProcessor, UppercaseProcessor
    >>>
    >>> # Create orchestrator
    >>> orchestrator = BaseOrchestrator()
    >>>
    >>> # Add stages
    >>> orchestrator.add_stage(PipelineStage(
    ...     stage_id='translate',
    ...     splitter_rules=[EmptyCellRule(), YellowCellRule()],
    ...     transformer=MockTransformer(LLMProcessor())
    ... ))
    >>>
    >>> orchestrator.add_stage(PipelineStage(
    ...     stage_id='uppercase',
    ...     splitter_rules=[CapsSheetRule()],
    ...     transformer=MockTransformer(UppercaseProcessor()),
    ...     depends_on=['translate']  # Depends on translate stage
    ... ))
    >>>
    >>> # Execute pipeline
    >>> final_state = orchestrator.execute(initial_state)
    >>>
    >>> # Get results
    >>> summary = orchestrator.get_execution_summary()
    >>> print(f"Completed {summary['completed_stages']} stages")
"""

from .pipeline_stage import PipelineStage
from .orchestrator import (
    Orchestrator,
    OrchestratorError,
    InvalidPipelineError,
    CircularDependencyError,
    StageExecutionError
)
from .base_orchestrator import BaseOrchestrator

__all__ = [
    # Core classes
    'PipelineStage',
    'Orchestrator',
    'BaseOrchestrator',

    # Exceptions
    'OrchestratorError',
    'InvalidPipelineError',
    'CircularDependencyError',
    'StageExecutionError',
]

__version__ = '1.0.0'
