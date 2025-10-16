"""Base orchestrator implementation with dependency management.

This module provides a concrete implementation of the Orchestrator base class
that supports:
- Sequential stage execution
- Dependency resolution
- Context building and passing
- Result storage
- Comprehensive logging

Example:
    >>> from services.orchestrator import BaseOrchestrator, PipelineStage
    >>> from services.splitter import EmptyCellRule, TaskSplitter
    >>> from services.processors import UppercaseProcessor
    >>>
    >>> orchestrator = BaseOrchestrator()
    >>>
    >>> # Add translation stage
    >>> orchestrator.add_stage(PipelineStage(
    ...     stage_id='translate',
    ...     splitter_rules=[EmptyCellRule()],
    ...     transformer=MockTransformer(LLMProcessor())
    ... ))
    >>>
    >>> # Add uppercase stage (depends on translate)
    >>> orchestrator.add_stage(PipelineStage(
    ...     stage_id='uppercase',
    ...     splitter_rules=[CapsSheetRule()],
    ...     transformer=MockTransformer(UppercaseProcessor()),
    ...     depends_on=['translate']
    ... ))
    >>>
    >>> # Execute pipeline
    >>> final_state = orchestrator.execute(initial_state)
"""

import logging
import time
from typing import Dict, Any

from .orchestrator import (
    Orchestrator,
    OrchestratorError,
    StageExecutionError
)
from .pipeline_stage import PipelineStage
from services.splitter import TaskSplitter


logger = logging.getLogger(__name__)


class BaseOrchestrator(Orchestrator):
    """Base orchestrator implementation.

    This orchestrator executes stages sequentially, respecting dependencies
    and passing context between stages.

    The execution flow:
    1. Validate pipeline configuration
    2. For each stage:
       a. Split tasks using stage's rules
       b. Build context from dependent stages
       c. Execute transformation
       d. Store results
       e. Update current state
    3. Return final state

    Context structure:
        {
            'stage_id_1': tasks_dataframe_1,
            'stage_id_2': tasks_dataframe_2,
            ...
        }

    Attributes:
        stages: List of pipeline stages
        results: Dictionary storing stage results
        _splitter: TaskSplitter instance for task splitting
    """

    def __init__(self):
        """Initialize the base orchestrator."""
        super().__init__()
        self._splitter = TaskSplitter()

    def execute(self, initial_data_state) -> Any:
        """Execute the entire pipeline.

        Args:
            initial_data_state: Initial DataState to process

        Returns:
            Final DataState after all stages complete

        Raises:
            OrchestratorError: If pipeline validation fails
            StageExecutionError: If any stage fails to execute
        """
        logger.info(f"[Orchestrator] Starting pipeline with {len(self.stages)} stages")
        start_time = time.time()

        # 1. Validate pipeline
        if not self.validate_pipeline():
            raise OrchestratorError("Pipeline validation failed")

        # 2. Initialize
        current_state = initial_data_state
        self.results = {}

        # 3. Execute each stage
        for i, stage in enumerate(self.stages, 1):
            logger.info(
                f"[Orchestrator] Executing stage {i}/{len(self.stages)}: "
                f"{stage.stage_id}"
            )
            stage_start = time.time()

            try:
                # 4. Split tasks
                tasks = self._split_stage(stage, current_state)
                logger.info(
                    f"[Orchestrator] Stage {stage.stage_id}: "
                    f"Generated {len(tasks)} tasks"
                )

                # 5. Build context (dependent stage results)
                context = self._build_context(stage)
                if context:
                    logger.debug(
                        f"[Orchestrator] Stage {stage.stage_id}: "
                        f"Context includes dependencies: {list(context.keys())}"
                    )

                # 6. Execute transformation
                new_state = stage.transformer.execute(
                    current_state,
                    tasks,
                    context
                )

                # 7. Store results
                self.results[stage.stage_id] = {
                    'data_state': new_state,
                    'tasks': tasks,
                    'context': context,
                }

                # 8. Update current state
                current_state = new_state

                # Log stage completion
                stage_duration = time.time() - stage_start
                logger.info(
                    f"[Orchestrator] Stage {stage.stage_id} completed: "
                    f"{len(tasks)} tasks in {stage_duration:.2f}s"
                )

            except Exception as e:
                logger.error(
                    f"[Orchestrator] Stage {stage.stage_id} failed: {e}",
                    exc_info=True
                )
                raise StageExecutionError(
                    f"Stage '{stage.stage_id}' failed"
                ) from e

        # 9. Log completion
        total_duration = time.time() - start_time
        logger.info(
            f"[Orchestrator] Pipeline completed successfully in "
            f"{total_duration:.2f}s"
        )

        return current_state

    def _split_stage(self, stage: PipelineStage, data_state) -> Any:
        """Execute task splitting for a stage.

        Args:
            stage: PipelineStage to split
            data_state: Current DataState

        Returns:
            TaskDataFrame with generated tasks

        Raises:
            StageExecutionError: If splitting fails
        """
        try:
            tasks = self._splitter.split(data_state, stage.splitter_rules)
            return tasks
        except Exception as e:
            logger.error(f"Task splitting failed for stage {stage.stage_id}: {e}")
            raise StageExecutionError(
                f"Task splitting failed for stage '{stage.stage_id}'"
            ) from e

    def _build_context(self, stage: PipelineStage) -> Dict[str, Any]:
        """Build context for a stage from its dependencies.

        The context contains the task results from all dependent stages,
        allowing the current stage to access previous results.

        Args:
            stage: PipelineStage to build context for

        Returns:
            Dictionary mapping stage_id -> tasks dataframe
            Empty dict if no dependencies

        Example:
            >>> # Stage 'uppercase' depends on 'translate'
            >>> context = self._build_context(uppercase_stage)
            >>> # context = {'translate': translate_tasks_df}
        """
        context = {}

        if not stage.depends_on:
            return context

        for dep_stage_id in stage.depends_on:
            if dep_stage_id in self.results:
                # Pass the tasks dataframe from the dependent stage
                context[dep_stage_id] = self.results[dep_stage_id]['tasks']
                logger.debug(
                    f"[Orchestrator] Added dependency '{dep_stage_id}' to "
                    f"context for stage '{stage.stage_id}'"
                )
            else:
                # This should not happen if validation is correct
                logger.warning(
                    f"[Orchestrator] Dependency '{dep_stage_id}' not found "
                    f"in results for stage '{stage.stage_id}'"
                )

        return context

    def get_stage_result(self, stage_id: str) -> Dict[str, Any]:
        """Get the result of a specific stage.

        Args:
            stage_id: ID of the stage

        Returns:
            Dictionary containing:
                - 'data_state': The DataState after this stage
                - 'tasks': The TaskDataFrame for this stage
                - 'context': The context passed to this stage

        Raises:
            ValueError: If no result exists for the given stage_id
        """
        if stage_id not in self.results:
            raise ValueError(f"No result found for stage: {stage_id}")

        return self.results[stage_id]

    def get_stage_tasks(self, stage_id: str) -> Any:
        """Get the tasks generated by a specific stage.

        Args:
            stage_id: ID of the stage

        Returns:
            TaskDataFrame with tasks from this stage

        Raises:
            ValueError: If no result exists for the given stage_id
        """
        result = self.get_stage_result(stage_id)
        return result['tasks']

    def get_final_state(self):
        """Get the final data state after all stages.

        Returns:
            Final DataState, or None if no stages have been executed

        Raises:
            RuntimeError: If pipeline has not been executed yet
        """
        if not self.results:
            raise RuntimeError("Pipeline has not been executed yet")

        # Get the last stage's result
        last_stage_id = self.stages[-1].stage_id
        return self.results[last_stage_id]['data_state']

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of the pipeline execution.

        Returns:
            Dictionary containing:
                - 'total_stages': Number of stages
                - 'completed_stages': Number of completed stages
                - 'stages': List of stage summaries

        Example:
            >>> summary = orchestrator.get_execution_summary()
            >>> print(f"Completed {summary['completed_stages']}/{summary['total_stages']}")
        """
        summary = {
            'total_stages': len(self.stages),
            'completed_stages': len(self.results),
            'stages': []
        }

        for stage in self.stages:
            stage_info = {
                'stage_id': stage.stage_id,
                'completed': stage.stage_id in self.results,
                'depends_on': stage.depends_on,
            }

            if stage.stage_id in self.results:
                result = self.results[stage.stage_id]
                stage_info['tasks_count'] = len(result['tasks'])

            summary['stages'].append(stage_info)

        return summary

    def __repr__(self) -> str:
        """Return string representation."""
        return (f"BaseOrchestrator(stages={len(self.stages)}, "
                f"completed={len(self.results)})")
