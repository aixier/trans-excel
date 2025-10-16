"""Backward-compatible import for the pipeline registry."""

from services.executor.pipeline.registry import (
    TaskPipelineConfig,
    TaskPipelineRegistry,
    task_pipeline_registry,
)

__all__ = [
    "TaskPipelineConfig",
    "TaskPipelineRegistry",
    "task_pipeline_registry",
]
