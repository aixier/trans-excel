"""Orchestrator base class for pipeline execution.

This module defines the abstract base class for orchestrators, which are
responsible for coordinating the execution of multi-stage data transformation
pipelines.

The orchestrator's responsibilities:
- Manage pipeline stages (add, validate)
- Execute stages in correct order
- Handle dependencies between stages
- Pass context between stages
- Validate pipeline configuration

The orchestrator does NOT:
- Implement splitting logic (delegated to Splitter)
- Implement transformation logic (delegated to Transformer)
- Implement processing logic (delegated to Processor)
- Handle specific business rules

Example:
    >>> from services.orchestrator import Orchestrator, PipelineStage
    >>> from services.data_state import ExcelState
    >>>
    >>> orchestrator = BaseOrchestrator()
    >>> orchestrator.add_stage(stage1)
    >>> orchestrator.add_stage(stage2)
    >>>
    >>> initial_state = ExcelState.from_excel_dataframe(df)
    >>> final_state = orchestrator.execute(initial_state)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

from .pipeline_stage import PipelineStage


logger = logging.getLogger(__name__)


class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""
    pass


class InvalidPipelineError(OrchestratorError):
    """Raised when pipeline configuration is invalid."""
    pass


class CircularDependencyError(OrchestratorError):
    """Raised when circular dependencies are detected."""
    pass


class StageExecutionError(OrchestratorError):
    """Raised when a stage execution fails."""
    pass


class Orchestrator(ABC):
    """Abstract base class for pipeline orchestrators.

    An orchestrator coordinates the execution of multiple pipeline stages,
    managing dependencies and data flow between stages.

    Attributes:
        stages: List of pipeline stages in execution order
        results: Dictionary storing results from each stage

    Example:
        >>> class MyOrchestrator(Orchestrator):
        ...     def execute(self, initial_data_state):
        ...         # Custom execution logic
        ...         pass
        >>>
        >>> orchestrator = MyOrchestrator()
        >>> orchestrator.add_stage(stage)
        >>> result = orchestrator.execute(initial_state)
    """

    def __init__(self):
        """Initialize the orchestrator."""
        self.stages: List[PipelineStage] = []
        self.results: Dict[str, Any] = {}

    def add_stage(self, stage: PipelineStage):
        """Add a stage to the pipeline.

        Args:
            stage: PipelineStage to add

        Raises:
            ValueError: If stage is None or stage_id is duplicate
            TypeError: If stage is not a PipelineStage instance
        """
        if stage is None:
            raise ValueError("stage cannot be None")

        if not isinstance(stage, PipelineStage):
            raise TypeError(f"stage must be PipelineStage, got {type(stage)}")

        # Check for duplicate stage_id
        if any(s.stage_id == stage.stage_id for s in self.stages):
            raise ValueError(f"Duplicate stage_id: {stage.stage_id}")

        self.stages.append(stage)
        logger.debug(f"Added stage: {stage.stage_id}")

    @abstractmethod
    def execute(self, initial_data_state) -> Any:
        """Execute the entire pipeline.

        This method must be implemented by subclasses to define the
        execution logic.

        Args:
            initial_data_state: Initial DataState to process

        Returns:
            Final DataState after all stages complete

        Raises:
            OrchestratorError: If execution fails
        """
        pass

    def validate_pipeline(self) -> bool:
        """Validate the pipeline configuration.

        Checks:
        - All dependencies reference existing stages
        - No circular dependencies exist
        - Stages are in valid order

        Returns:
            bool: True if pipeline is valid, False otherwise

        Raises:
            InvalidPipelineError: If critical validation errors are found
        """
        if not self.stages:
            logger.warning("Pipeline is empty")
            return False

        # Check dependency references
        stage_ids = {s.stage_id for s in self.stages}

        for stage in self.stages:
            if stage.depends_on:
                for dep_id in stage.depends_on:
                    if dep_id not in stage_ids:
                        raise InvalidPipelineError(
                            f"Stage '{stage.stage_id}' depends on non-existent "
                            f"stage '{dep_id}'"
                        )

        # Check for circular dependencies
        if self._has_circular_dependency():
            raise CircularDependencyError(
                "Circular dependency detected in pipeline"
            )

        logger.debug("Pipeline validation passed")
        return True

    def _has_circular_dependency(self) -> bool:
        """Check if pipeline has circular dependencies using topological sort.

        Returns:
            bool: True if circular dependency exists, False otherwise
        """
        # Build adjacency list
        graph = {stage.stage_id: stage.depends_on[:] for stage in self.stages}

        # Track visited nodes
        visiting = set()  # Currently in DFS path
        visited = set()   # Fully processed nodes

        def has_cycle(node: str) -> bool:
            """DFS to detect cycle."""
            if node in visiting:
                return True  # Back edge found - cycle!

            if node in visited:
                return False  # Already processed this path

            visiting.add(node)

            # Check all dependencies
            for dep in graph.get(node, []):
                if has_cycle(dep):
                    return True

            visiting.remove(node)
            visited.add(node)
            return False

        # Check each node
        for stage_id in graph:
            if stage_id not in visited:
                if has_cycle(stage_id):
                    logger.error(f"Circular dependency detected involving: {stage_id}")
                    return True

        return False

    def get_stage(self, stage_id: str) -> PipelineStage:
        """Get a stage by its ID.

        Args:
            stage_id: ID of the stage to retrieve

        Returns:
            PipelineStage: The stage with the given ID

        Raises:
            ValueError: If no stage with given ID exists
        """
        for stage in self.stages:
            if stage.stage_id == stage_id:
                return stage

        raise ValueError(f"No stage found with id: {stage_id}")

    def get_stage_count(self) -> int:
        """Get the number of stages in the pipeline.

        Returns:
            int: Number of stages
        """
        return len(self.stages)

    def clear(self):
        """Clear all stages and results from the orchestrator."""
        self.stages.clear()
        self.results.clear()
        logger.debug("Orchestrator cleared")

    def __repr__(self) -> str:
        """Return string representation of the orchestrator."""
        return f"{self.__class__.__name__}(stages={len(self.stages)})"
