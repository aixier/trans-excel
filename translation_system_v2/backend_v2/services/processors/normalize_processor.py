"""Normalize processor for punctuation conversion.

This processor converts Chinese (full-width) punctuation to English (half-width)
punctuation, useful for normalizing text formats and ensuring consistency.
"""

from typing import Dict, Any, Optional, List
from .processor import Processor


class NormalizeProcessor(Processor):
    """Processor that normalizes punctuation from Chinese to English format.

    Use cases:
    - Converting full-width punctuation to half-width
    - Normalizing mixed-format text
    - Pre-processing before translation
    - Post-processing for consistency

    Conversion mappings:
    - Chinese comma (,) -> English comma (,)
    - Chinese period (。) -> English period (.)
    - Chinese semicolon (;) -> English semicolon (;)
    - Chinese colon (:) -> English colon (:)
    - Chinese question mark (?) -> English question mark (?)
    - Chinese exclamation (!) -> English exclamation (!)
    - Chinese parentheses (( )) -> English parentheses (( ))
    - Chinese quotes (" ") -> English quotes (" ")
    - Chinese ellipsis (…) -> English ellipsis (...)

    Example:
        >>> processor = NormalizeProcessor()
        >>> task = {
        ...     'task_id': 'NORM_001',
        ...     'operation': 'normalize',
        ...     'source_text': '你好,世界!'
        ... }
        >>> processor.process(task)
        '你好,世界!'

        >>> # Mixed punctuation
        >>> task = {
        ...     'task_id': 'NORM_002',
        ...     'operation': 'normalize',
        ...     'source_text': '"这是测试。"(完成)'
        ... }
        >>> processor.process(task)
        '"这是测试."(完成)'
    """

    # Punctuation conversion mapping
    PUNCTUATION_MAP = {
        # Comma
        ',': ',',
        # Period
        '。': '.',
        # Semicolon
        ';': ';',
        # Colon
        ':': ':',
        # Question mark
        '?': '?',
        # Exclamation mark
        '!': '!',
        # Left parenthesis
        '(': '(',
        # Right parenthesis
        ')': ')',
        # Left bracket
        '[': '[',
        # Right bracket
        ']': ']',
        # Left brace
        '{': '{',
        # Right brace
        '}': '}',
        # Left angle quote
        '《': '<',
        # Right angle quote
        '》': '>',
        # Left double quote
        '"': '"',
        # Right double quote
        '"': '"',
        # Left single quote
        '\u2018': "'",
        # Right single quote
        '\u2019': "'",
        # Ellipsis
        '…': '...',
        # Em dash
        '—': '-',
        # En dash
        '–': '-',
        # Middle dot
        '·': '.',
        # Full-width space
        '\u3000': ' ',
    }

    def get_operation_type(self) -> str:
        """Return the operation type.

        Returns:
            str: 'normalize'
        """
        return 'normalize'

    def process(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Convert Chinese punctuation to English punctuation.

        Args:
            task: Task dictionary containing:
                - task_id: Task identifier
                - operation: Must be 'normalize'
                - source_text: Text to normalize
                - depends_on: Optional dependency task ID

            context: Optional context containing:
                - previous_tasks: Dict mapping task_id to task data

        Returns:
            str: Normalized text with English punctuation

        Raises:
            ValueError: If task validation fails

        Processing logic:
            1. Validate task data
            2. Get source text (from dependency or task itself)
            3. Replace each Chinese punctuation with English equivalent
            4. Return normalized result

        Note:
            - Processes text character by character
            - Preserves non-punctuation characters
            - Handles Unicode correctly
        """
        # Validate task
        if not self.validate_task(task):
            raise ValueError(f"Invalid task data for normalize processing: {task.get('task_id')}")

        # Get source text (handles context dependency)
        source_text = self.get_source_text(task, context)

        # Handle empty text
        if not source_text:
            self.logger.debug(
                f"Task {task.get('task_id')} has empty source text, returning empty string"
            )
            return ""

        # Normalize punctuation
        result = self._normalize_punctuation(source_text)

        # Log if changes were made
        if result != source_text:
            changes = sum(1 for a, b in zip(source_text, result) if a != b)
            self.logger.debug(
                f"Normalized task {task.get('task_id')}: {changes} punctuation changes"
            )

        return result

    def _normalize_punctuation(self, text: str) -> str:
        """Convert Chinese punctuation to English punctuation.

        Args:
            text: Text with Chinese punctuation

        Returns:
            str: Text with English punctuation

        Implementation:
            Handles single-character and multi-character replacements separately.
            Single-character replacements use str.translate() for efficiency.
            Multi-character replacements use str.replace().
        """
        # Separate single-char and multi-char replacements
        # For str.maketrans(), both source and target must be single characters
        # If target is multi-char (like '...'), use str.replace() instead
        single_char_map = {}
        multi_char_replacements = []

        for source, target in self.PUNCTUATION_MAP.items():
            if len(source) == 1 and len(target) == 1:
                single_char_map[source] = target
            else:
                multi_char_replacements.append((source, target))

        # Apply single-character replacements using translate
        if single_char_map:
            translation_table = str.maketrans(single_char_map)
            text = text.translate(translation_table)

        # Apply multi-character replacements using replace
        for source, target in multi_char_replacements:
            text = text.replace(source, target)

        return text

    def process_batch(
        self,
        tasks: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Process multiple tasks in batch.

        Normalization is fast with str.translate(), so we use the default
        implementation.

        Args:
            tasks: List of tasks to process
            context: Optional context with previous results

        Returns:
            List[str]: List of normalized texts
        """
        return super().process_batch(tasks, context)
