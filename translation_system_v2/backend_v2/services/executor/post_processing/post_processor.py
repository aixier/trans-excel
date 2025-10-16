"""Post-processing utilities for task execution."""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class PostProcessor:
    """Collection of lightweight post-processing helpers.

    The class exposes a single `apply_post_processing` method so that callers
    do not have to reason about individual handlers.  Each handler can be
    registered via ``register_processor`` if future task types require custom
    behaviour.
    """

    _PROCESSORS = {
        'caps': lambda text: text.upper(),
    }

    @classmethod
    def apply_post_processing(cls, task: Dict[str, Any], result: str) -> str:
        """Dispatch post-processing based on ``task_type`` or sheet metadata."""

        task_type = task.get('task_type', 'normal')
        sheet_name = (task.get('sheet_name') or '').lower()
        target_lang = (task.get('target_lang') or '').upper()

        # CAPS sheet fallback: if the sheet name indicates caps requirements,
        # always enforce uppercase for non-Chinese targets.
        if 'caps' in sheet_name and target_lang:
            try:
                return result.upper()
            except Exception:  # pragma: no cover - defensive
                logger.exception("Failed to apply CAPS post-processing")
                return result

        processor = cls._PROCESSORS.get(task_type)
        if processor:
            try:
                return processor(result)
            except Exception:  # pragma: no cover - defensive
                logger.exception("Post-processing failed for task %s", task.get('task_id'))
                return result

        return result

    @classmethod
    def register_processor(cls, task_type: str, func) -> None:
        """Register custom post-processing for a task type."""

        cls._PROCESSORS[task_type] = func
        logger.info("Registered post-processor for task type %s", task_type)
