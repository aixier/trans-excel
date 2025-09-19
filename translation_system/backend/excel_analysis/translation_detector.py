"""
翻译检测器
基于test_concurrent_batch.py的翻译任务检测逻辑
"""
from typing import List, Dict, Tuple
from dataclasses import dataclass
import pandas as pd
from .header_analyzer import SheetInfo, ColumnType


@dataclass
class TranslationTask:
    """翻译任务"""
    sheet_name: str
    row_index: int
    source_text: str
    target_column: str
    target_language: str
    task_type: str = "new"          # new, modify, shorten
    background_color: str = None     # 单元格背景色
    original_translation: str = None # 原有翻译


class TranslationDetector:
    """翻译检测器 - 升级Demo中的空行检测逻辑"""

    def __init__(self):
        # 颜色标记规则
        self.color_mapping = {
            'FFFFFF00': 'modify',   # 黄色 - 修改翻译
            'FF0000FF': 'shorten',  # 蓝色 - 缩短翻译
            'FF00FF00': 'completed', # 绿色 - 已完成
            'FFFF0000': 'error'     # 红色 - 错误标记
        }

    def detect_translation_tasks(
        self,
        df: pd.DataFrame,
        sheet_info: SheetInfo,
        include_colors: bool = True
    ) -> List[TranslationTask]:
        """检测需要翻译的任务 - 按行动态检测源语言和翻译需求"""
        tasks = []

        # 获取所有语言列
        language_cols = [col for col in sheet_info.columns if col.language is not None]

        if not language_cols:
            return tasks

        # 按行检测
        for idx, row in df.iterrows():
            # 找出该行的源语言（优先EN，其次CH，再其他有内容的）
            source_text = None
            source_lang = None
            source_col_name = None

            # 先检查EN列
            for col in language_cols:
                if col.language == 'en':
                    value = row[col.name]
                    if pd.notna(value) and str(value).strip():
                        source_text = str(value).strip()
                        source_lang = 'en'
                        source_col_name = col.name
                        break

            # 如果没有EN，检查CH列
            if not source_text:
                for col in language_cols:
                    if col.language == 'ch':
                        value = row[col.name]
                        if pd.notna(value) and str(value).strip():
                            source_text = str(value).strip()
                            source_lang = 'ch'
                            source_col_name = col.name
                            break

            # 如果都没有，使用任何有内容的列
            if not source_text:
                for col in language_cols:
                    value = row[col.name]
                    if pd.notna(value) and str(value).strip():
                        source_text = str(value).strip()
                        source_lang = col.language
                        source_col_name = col.name
                        break

            # 如果没有源文本，跳过该行
            if not source_text:
                continue

            # 检查每个目标语言列是否需要翻译
            for col in language_cols:
                if col.name == source_col_name:  # 跳过源语言列
                    continue

                target_text = row[col.name]

                # 获取背景色 (如果支持)
                background_color = None
                if include_colors:
                    background_color = self._get_cell_background_color(df, idx, col.name)

                # 判断任务类型
                task_type = self._determine_task_type(target_text, background_color)

                if task_type in ['new', 'modify', 'shorten']:
                    task = TranslationTask(
                        sheet_name=sheet_info.name,
                        row_index=idx,
                        source_text=source_text,
                        target_column=col.name,
                        target_language=col.language,
                        task_type=task_type,
                        background_color=background_color,
                        original_translation=str(target_text) if pd.notna(target_text) else None
                    )
                    tasks.append(task)

        return tasks

    def _determine_task_type(self, target_text, background_color: str) -> str:
        """根据内容和颜色确定任务类型"""
        # 1. 根据颜色判断
        if background_color in self.color_mapping:
            color_task = self.color_mapping[background_color]
            if color_task in ['modify', 'shorten']:
                return color_task
            elif color_task == 'completed':
                return 'skip'  # 已完成，跳过

        # 2. 根据内容判断 (与Demo中的空行检测逻辑一致)
        if pd.isna(target_text) or str(target_text).strip() == '':
            return 'new'  # 新翻译
        else:
            return 'skip'  # 已有翻译，跳过

    def _get_cell_background_color(self, df: pd.DataFrame, row_idx: int, col_name: str) -> str:
        """获取单元格背景色 (需要使用openpyxl)"""
        # 这里需要从Excel文件中读取颜色信息
        # 简化实现，实际需要使用openpyxl库
        try:
            # 实际实现需要访问Excel的样式信息
            return None
        except:
            return None

    def group_tasks_by_batch(self, tasks: List[TranslationTask], batch_size: int = 3) -> List[List[TranslationTask]]:
        """按批次分组任务 - 基于Demo的批处理逻辑"""
        batches = []
        current_batch = []

        for task in tasks:
            current_batch.append(task)

            if len(current_batch) >= batch_size:
                batches.append(current_batch)
                current_batch = []

        # 添加最后一个批次
        if current_batch:
            batches.append(current_batch)

        return batches

    def get_task_statistics(self, tasks: List[TranslationTask]) -> Dict[str, int]:
        """获取任务统计信息"""
        stats = {
            'total': len(tasks),
            'new': 0,
            'modify': 0,
            'shorten': 0
        }

        for task in tasks:
            if task.task_type in stats:
                stats[task.task_type] += 1

        return stats