"""Task execution pipeline registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

import pandas as pd

from services.executor.post_processing import PostProcessor

if TYPE_CHECKING:  # pragma: no cover
    from models.task_dataframe import TaskDataFrameManager


ProcessFunc = Callable[[Dict[str, Any], 'TaskDataFrameManager'], str]
PostProcessFunc = Callable[[Dict[str, Any], str], str]


@dataclass
class TaskPipelineConfig:
    requires_llm: bool = True
    direct_processor: Optional[ProcessFunc] = None
    post_processor: PostProcessFunc = PostProcessor.apply_post_processing


class TaskPipelineRegistry:
    def __init__(self) -> None:
        self._pipelines: Dict[str, TaskPipelineConfig] = {}

        # Default pipelines
        self.register('normal', TaskPipelineConfig())
        self.register('yellow', TaskPipelineConfig())
        self.register('blue', TaskPipelineConfig())
        self.register('caps', TaskPipelineConfig(requires_llm=False, direct_processor=self._process_caps_direct))

    def register(self, task_type: str, config: TaskPipelineConfig) -> None:
        self._pipelines[task_type] = config

    def get(self, task_type: Optional[str]) -> TaskPipelineConfig:
        key = task_type or 'normal'
        return self._pipelines.get(key, self._pipelines['normal'])

    @staticmethod
    def _process_caps_direct(task: Dict[str, Any], task_manager: 'TaskDataFrameManager') -> str:
        from models.task_dataframe import TaskStatus  # Lazy import

        if task_manager and getattr(task_manager, 'df', None) is not None:
            df = task_manager.df
            try:
                mask = (
                    (df['sheet_name'] == task.get('sheet_name'))
                    & (df['row_idx'] == task.get('row_idx'))
                    & (df['col_idx'] == task.get('col_idx'))
                    & (df['task_type'] != 'caps')
                    & (df['status'] == TaskStatus.COMPLETED)
                )

                if mask.any():
                    value = df.loc[mask, 'result'].iloc[-1]
                    if isinstance(value, str):
                        return value
                    if value is not None and not pd.isna(value):
                        return str(value)
            except KeyError:  # pragma: no cover - defensive
                pass

        return (
            task.get('reference_en')
            or task.get('original_target_value')
            or task.get('result')
            or task.get('source_text')
            or ''
        )


task_pipeline_registry = TaskPipelineRegistry()
