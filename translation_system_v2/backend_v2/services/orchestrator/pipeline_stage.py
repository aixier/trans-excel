"""Pipeline stage configuration dataclass.

This module defines the PipelineStage dataclass, which represents a single
stage in a transformation pipeline.

A stage consists of:
- stage_id: Unique identifier for the stage
- splitter_rules: List of rules to apply when splitting tasks
- transformer: The transformer instance to execute tasks
- depends_on: Optional list of stage IDs that this stage depends on

Example:
    >>> from services.splitter import EmptyCellRule, YellowCellRule
    >>> from services.processors import LLMProcessor
    >>>
    >>> # Create a translation stage
    >>> stage = PipelineStage(
    ...     stage_id='translate',
    ...     splitter_rules=[EmptyCellRule(), YellowCellRule()],
    ...     transformer=MockTransformer(LLMProcessor()),
    ...     depends_on=[]
    ... )
"""

from dataclasses import dataclass, field
from typing import List, Any


@dataclass
class PipelineStage:
    """Configuration for a single pipeline stage.

    A pipeline stage represents one transformation step in the data processing
    workflow. It combines:
    - Rules to identify which cells need processing
    - A transformer to execute the processing
    - Dependencies on other stages

    Attributes:
        stage_id: Unique identifier for this stage (e.g., 'translate', 'uppercase')
        splitter_rules: List of SplitRule instances to identify cells to process
        transformer: Transformer instance to execute tasks (with a Processor)
        depends_on: List of stage IDs that must complete before this stage
                   (default: empty list)

    Example:
        >>> # Simple stage with no dependencies
        >>> stage1 = PipelineStage(
        ...     stage_id='translate',
        ...     splitter_rules=[EmptyCellRule()],
        ...     transformer=transformer
        ... )
        >>>
        >>> # Stage with dependencies
        >>> stage2 = PipelineStage(
        ...     stage_id='uppercase',
        ...     splitter_rules=[CapsSheetRule()],
        ...     transformer=transformer,
        ...     depends_on=['translate']  # Waits for 'translate' to complete
        ... )
    """

    stage_id: str
    splitter_rules: List[Any]  # List[SplitRule], but using Any to avoid circular import
    transformer: Any  # Transformer instance, using Any to avoid circular import
    depends_on: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate stage configuration after initialization."""
        if not self.stage_id:
            raise ValueError("stage_id cannot be empty")

        if not isinstance(self.stage_id, str):
            raise TypeError(f"stage_id must be str, got {type(self.stage_id)}")

        if not isinstance(self.splitter_rules, list):
            raise TypeError(f"splitter_rules must be list, got {type(self.splitter_rules)}")

        if not self.splitter_rules:
            raise ValueError("splitter_rules cannot be empty")

        if self.transformer is None:
            raise ValueError("transformer cannot be None")

        if not isinstance(self.depends_on, list):
            raise TypeError(f"depends_on must be list, got {type(self.depends_on)}")

        # Validate depends_on contains only strings
        for dep in self.depends_on:
            if not isinstance(dep, str):
                raise TypeError(f"depends_on must contain strings, got {type(dep)}")

    def has_dependencies(self) -> bool:
        """Check if this stage has any dependencies.

        Returns:
            bool: True if stage depends on other stages, False otherwise
        """
        return len(self.depends_on) > 0

    def __repr__(self) -> str:
        """Return string representation of the stage."""
        deps = f", depends_on={self.depends_on}" if self.depends_on else ""
        return (f"PipelineStage(stage_id='{self.stage_id}', "
                f"rules={len(self.splitter_rules)}{deps})")
