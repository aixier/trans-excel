"""Batch allocation service."""

from typing import List, Dict, Any
from utils.config_manager import config_manager


class BatchAllocator:
    """Allocate tasks into batches based on character count."""

    def __init__(self, max_chars_per_batch: int = None):
        # Use custom value if provided, otherwise use config default
        self.max_chars_per_batch = max_chars_per_batch or config_manager.max_chars_per_batch

    def allocate_batches(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Allocate tasks into batches based on max_chars_per_batch and task_type.

        Args:
            tasks: List of task dictionaries with 'source_text', 'target_lang', 'task_type', etc.

        Returns:
            List of tasks with batch_id assigned
        """
        if not tasks:
            return []

        # Group tasks by target language AND task type
        # Different task types cannot be in the same batch
        tasks_by_key = {}
        for task in tasks:
            lang = task.get('target_lang', 'UNKNOWN')
            task_type = task.get('task_type', 'normal')
            # Create composite key: language + task type
            key = f"{lang}_{task_type.upper()}"

            if key not in tasks_by_key:
                tasks_by_key[key] = []
            tasks_by_key[key].append(task)

        # Allocate batches for each language+type combination
        for key, key_tasks in tasks_by_key.items():
            batch_num = 0
            current_chars = 0

            for task in key_tasks:
                # Calculate task character count
                source_text = task.get('source_text', '')
                source_context = task.get('source_context', '')
                task_chars = len(source_text) + len(source_context)

                # Check if adding this task would exceed the batch limit
                if current_chars > 0 and current_chars + task_chars > self.max_chars_per_batch:
                    # Start a new batch
                    batch_num += 1
                    current_chars = 0

                # Assign batch_id with task type in the name
                # Format: BATCH_{lang}_{TYPE}_{num}
                lang = task.get('target_lang', 'UNKNOWN')
                task_type = task.get('task_type', 'normal').upper()
                task['batch_id'] = f"BATCH_{lang}_{task_type}_{batch_num:03d}"
                task['char_count'] = task_chars
                current_chars += task_chars

        return tasks

    def calculate_batch_statistics(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics about batch allocation."""
        if not tasks:
            return {
                'total_batches': 0,
                'batch_distribution': {},
                'avg_chars_per_batch': 0,
                'max_chars_in_batch': 0,
                'min_chars_in_batch': 0
            }

        # Group by batch_id
        batches = {}
        for task in tasks:
            batch_id = task.get('batch_id', 'UNKNOWN')
            if batch_id not in batches:
                batches[batch_id] = {
                    'tasks': [],
                    'total_chars': 0,
                    'target_lang': task.get('target_lang', 'UNKNOWN')
                }
            batches[batch_id]['tasks'].append(task)
            batches[batch_id]['total_chars'] += task.get('char_count', 0)

        # Calculate statistics
        batch_chars = [b['total_chars'] for b in batches.values()]

        # Build detailed batch distribution with tasks and batches count per language
        batch_distribution = {}
        for batch_id, batch_info in batches.items():
            lang = batch_info['target_lang']
            if lang not in batch_distribution:
                batch_distribution[lang] = {
                    'batches': 0,
                    'tasks': 0,
                    'chars': 0
                }
            batch_distribution[lang]['batches'] += 1
            batch_distribution[lang]['tasks'] += len(batch_info['tasks'])
            batch_distribution[lang]['chars'] += batch_info['total_chars']

        return {
            'total_batches': len(batches),
            'batch_distribution': batch_distribution,
            'avg_chars_per_batch': sum(batch_chars) / len(batch_chars) if batch_chars else 0,
            'max_chars_in_batch': max(batch_chars) if batch_chars else 0,
            'min_chars_in_batch': min(batch_chars) if batch_chars else 0,
            'batches': batches
        }

    def optimize_batches(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize batch allocation for better distribution.
        Sort tasks by size before allocation to minimize waste.
        """
        if not tasks:
            return []

        # Group by target language
        tasks_by_lang = {}
        for task in tasks:
            lang = task.get('target_lang', 'UNKNOWN')
            if lang not in tasks_by_lang:
                tasks_by_lang[lang] = []

            # Pre-calculate char count
            source_text = task.get('source_text', '')
            source_context = task.get('source_context', '')
            task['char_count'] = len(source_text) + len(source_context)
            tasks_by_lang[lang].append(task)

        # Sort each language group by char count (descending)
        # This helps pack batches more efficiently
        for lang in tasks_by_lang:
            tasks_by_lang[lang].sort(key=lambda x: x['char_count'], reverse=True)

        # Allocate using bin packing algorithm
        for lang, lang_tasks in tasks_by_lang.items():
            batches = []  # List of (batch_chars, task_list)

            for task in lang_tasks:
                task_chars = task['char_count']

                # Find the best batch to add this task to
                best_batch = None
                for i, (batch_chars, batch_tasks) in enumerate(batches):
                    if batch_chars + task_chars <= self.max_chars_per_batch:
                        best_batch = i
                        break

                if best_batch is not None:
                    # Add to existing batch
                    batches[best_batch] = (
                        batches[best_batch][0] + task_chars,
                        batches[best_batch][1] + [task]
                    )
                else:
                    # Create new batch
                    batches.append((task_chars, [task]))

            # Assign batch IDs
            for batch_num, (_, batch_tasks) in enumerate(batches):
                batch_id = f"BATCH_{lang}_{batch_num:03d}"
                for task in batch_tasks:
                    task['batch_id'] = batch_id

        return tasks

    def split_large_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a task that's too large for a single batch.
        This should be rare but handles edge cases.
        """
        source_text = task.get('source_text', '')

        if len(source_text) <= self.max_chars_per_batch:
            return [task]

        # Split into chunks
        chunks = []
        chunk_size = self.max_chars_per_batch - 1000  # Leave room for context

        for i in range(0, len(source_text), chunk_size):
            chunk_task = task.copy()
            chunk_task['source_text'] = source_text[i:i + chunk_size]
            chunk_task['task_id'] = f"{task['task_id']}_part{i // chunk_size + 1}"
            chunks.append(chunk_task)

        return chunks