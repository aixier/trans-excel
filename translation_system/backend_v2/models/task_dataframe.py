"""Task DataFrame model definition."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime


# Task DataFrame columns definition
TASK_DF_COLUMNS = {
    'task_id': str,                   # 1. 任务唯一标识符
    'batch_id': str,                  # 2. 批次ID (用于LLM批量调用)
    'group_id': str,                  # 3. 分组ID (业务分组)
    'source_lang': 'category',        # 4. 源语言 (CH/EN)
    'source_text': str,               # 5. 源文本
    'source_context': str,            # 6. 源文本上下文
    'game_context': str,              # 7. 游戏背景信息
    'target_lang': 'category',        # 8. 目标语言 (PT/TH/VN)
    'excel_id': str,                  # 9. Excel文件标识符
    'sheet_name': str,                # 10. Sheet名称
    'row_idx': 'int32',               # 11. 行索引
    'col_idx': 'int32',               # 12. 列索引
    'cell_ref': str,                  # 13. 单元格引用 (如A1)
    'status': 'category',             # 14. 任务状态 (pending/processing/completed/failed)
    'priority': 'int8',               # 15. 优先级 (1-10)
    'result': str,                    # 16. 翻译结果
    'confidence': 'float32',          # 17. 置信度 (0-1)
    'char_count': 'int32',            # 18. 字符数
    'created_at': 'datetime64[ns]',   # 19. 创建时间
    'updated_at': 'datetime64[ns]',   # 20. 更新时间
    'start_time': 'datetime64[ns]',   # 21. 开始处理时间
    'end_time': 'datetime64[ns]',     # 22. 结束处理时间
    'duration_ms': 'int32',           # 23. 处理耗时(毫秒)
    'retry_count': 'int8',            # 24. 重试次数
    'error_message': str,             # 25. 错误信息
    'llm_model': str,                 # 26. 使用的LLM模型
    'token_count': 'int32',           # 27. Token使用量
    'cost': 'float32',                # 28. 成本
    'reviewer_notes': str,            # 29. 审核备注
    'is_final': bool                  # 30. 是否最终版本
}

# Task status enum
class TaskStatus:
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


@dataclass
class TaskDataFrameManager:
    """Manager for task DataFrame operations."""

    def __init__(self):
        self.df = None

    def create_empty_dataframe(self) -> pd.DataFrame:
        """Create an empty task DataFrame with proper schema."""
        df = pd.DataFrame(columns=list(TASK_DF_COLUMNS.keys()))

        # Set data types
        for col, dtype in TASK_DF_COLUMNS.items():
            if dtype == 'category':
                df[col] = df[col].astype('category')
            elif dtype == 'datetime64[ns]':
                df[col] = pd.to_datetime(df[col])
            elif dtype in ['int8', 'int32']:
                df[col] = pd.array([], dtype=dtype)
            elif dtype in ['float32']:
                df[col] = pd.array([], dtype=dtype)
            elif dtype == bool:
                df[col] = df[col].astype(bool)

        return df

    def add_task(self, task_data: Dict[str, Any]) -> None:
        """Add a new task to the DataFrame."""
        if self.df is None:
            self.df = self.create_empty_dataframe()

        # Set default values
        task_data.setdefault('status', TaskStatus.PENDING)
        task_data.setdefault('priority', 5)
        task_data.setdefault('retry_count', 0)
        task_data.setdefault('is_final', False)
        task_data.setdefault('created_at', datetime.now())
        task_data.setdefault('updated_at', datetime.now())
        task_data.setdefault('confidence', 0.0)
        task_data.setdefault('char_count', len(task_data.get('source_text', '')))

        # Append to DataFrame
        self.df = pd.concat([self.df, pd.DataFrame([task_data])], ignore_index=True)

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> None:
        """Update task by task_id."""
        if self.df is None:
            return

        mask = self.df['task_id'] == task_id
        if mask.any():
            updates['updated_at'] = datetime.now()
            for key, value in updates.items():
                self.df.loc[mask, key] = value

    def get_task(self, task_id: str) -> Optional[pd.Series]:
        """Get task by task_id."""
        if self.df is None:
            return None

        mask = self.df['task_id'] == task_id
        if mask.any():
            return self.df[mask].iloc[0]
        return None

    def get_tasks_by_batch(self, batch_id: str) -> pd.DataFrame:
        """Get all tasks in a batch."""
        if self.df is None:
            return pd.DataFrame()

        return self.df[self.df['batch_id'] == batch_id]

    def get_tasks_by_group(self, group_id: str) -> pd.DataFrame:
        """Get all tasks in a group."""
        if self.df is None:
            return pd.DataFrame()

        return self.df[self.df['group_id'] == group_id]

    def get_pending_tasks(self, limit: int = None) -> pd.DataFrame:
        """Get pending tasks sorted by priority (descending)."""
        if self.df is None:
            return pd.DataFrame()

        pending = self.df[self.df['status'] == TaskStatus.PENDING]

        # Sort by priority (descending) and then by task_id for stable ordering
        pending = pending.sort_values(
            by=['priority', 'task_id'],
            ascending=[False, True]  # Higher priority first, then by task_id
        )

        if limit:
            return pending.head(limit)
        return pending

    def get_statistics(self) -> Dict[str, Any]:
        """Get task statistics."""
        if self.df is None or len(self.df) == 0:
            return {
                'total': 0,
                'by_status': {},
                'by_language': {},
                'by_group': {}
            }

        # Convert numpy types to Python types
        total_chars = self.df['char_count'].sum() if 'char_count' in self.df.columns else 0
        avg_confidence = self.df['confidence'].mean() if 'confidence' in self.df.columns else 0.0

        stats = {
            'total': int(len(self.df)),
            'by_status': {k: int(v) for k, v in self.df['status'].value_counts().to_dict().items()},
            'by_language': {k: int(v) for k, v in self.df['target_lang'].value_counts().to_dict().items()},
            'by_group': {k: int(v) for k, v in self.df['group_id'].value_counts().to_dict().items()},
            'total_chars': int(total_chars) if not pd.isna(total_chars) else 0,
            'avg_confidence': float(avg_confidence) if not pd.isna(avg_confidence) else 0.0
        }

        # Add task type distribution if column exists
        if 'task_type' in self.df.columns:
            stats['by_type'] = {k: int(v) for k, v in self.df['task_type'].value_counts().to_dict().items()}

        return stats

    def export_to_excel(self, filepath: str) -> None:
        """Export DataFrame to Excel file."""
        if self.df is not None:
            self.df.to_excel(filepath, index=False)

    def import_from_dataframe(self, df: pd.DataFrame) -> None:
        """Import from existing DataFrame."""
        self.df = df.copy()