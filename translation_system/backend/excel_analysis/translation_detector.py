"""
翻译检测器
基于test_concurrent_batch.py的翻译任务检测逻辑
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import pandas as pd
import logging
from .header_analyzer import SheetInfo, ColumnType

logger = logging.getLogger(__name__)


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
        include_colors: bool = True,
        source_langs: Optional[List[str]] = None,  # 源语言参数
        target_langs: Optional[List[str]] = None  # 目标语言参数
    ) -> List[TranslationTask]:
        """检测需要翻译的任务 - 按行动态检测源语言和翻译需求"""
        tasks = []

        # 清理DataFrame列名（去除冒号等特殊字符）- 如果还没有清理
        if any(':' in col for col in df.columns):
            df.columns = [col.strip(':').strip() for col in df.columns]

        # 获取所有语言列
        language_cols = [col for col in sheet_info.columns if col.language is not None]

        if not language_cols:
            return tasks

        # 按行检测
        for idx, row in df.iterrows():
            # 找出该行的源语言
            source_text = None
            source_lang = None
            source_col_name = None

            if source_langs:
                # 如果指定了源语言，按照指定顺序查找
                for src_lang in source_langs:
                    src_lang_lower = src_lang.lower()
                    for col in language_cols:
                        if col.language and col.language.lower() == src_lang_lower:
                            value = row[col.name]
                            if pd.notna(value) and str(value).strip():
                                source_text = str(value).strip()
                                source_lang = col.language
                                source_col_name = col.name
                                break
                    if source_text:
                        break
            else:
                # 未指定源语言，使用默认优先级：EN > CH > 其他
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

                # 如果指定了目标语言，只检测这些语言
                if target_langs:
                    # 将目标语言转换为小写进行比较
                    target_langs_lower = [lang.lower() for lang in target_langs]
                    if col.language and col.language.lower() not in target_langs_lower:
                        continue

                target_text = row[col.name]

                # 获取背景色 (如果支持)
                background_color = None
                if include_colors:
                    background_color = self._get_cell_background_color(df, idx, col.name)

                # 判断任务类型 - 增强版本
                task_type = self._determine_task_type_enhanced(target_text, background_color)

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

    def _determine_task_type_enhanced(self, target_text, background_color: str) -> str:
        """增强的任务类型判断 - 支持增量翻译"""
        # 先检查颜色标记
        if background_color and background_color in self.color_mapping:
            color_type = self.color_mapping[background_color]
            if color_type == 'completed':
                return 'completed'  # 已完成，跳过
            return color_type

        # 检查文本内容
        if pd.isna(target_text) or str(target_text).strip() == '':
            return 'new'  # 空值，需要翻译

        # 如果有内容，检查是否需要修改
        text_str = str(target_text).strip()

        # 简单的翻译质量检查
        if len(text_str) < 2:
            return 'modify'  # 内容太短，可能需要重新翻译
        elif text_str.lower() in ['todo', 'tbd', 'pending', '待翻译', '未翻译']:
            return 'new'  # 占位符，需要翻译

        return 'completed'  # 有合理内容，跳过

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

    def merge_sheet_tasks(
        self,
        sheet_tasks: Dict[str, List[TranslationTask]],
        batch_size: int
    ) -> List[List[TranslationTask]]:
        """
        合并多个Sheet的翻译任务进行批处理
        优化：相同语言对的任务可以合并处理
        """
        # 按源语言和目标语言分组
        grouped_tasks = {}

        for sheet_name, tasks in sheet_tasks.items():
            for task in tasks:
                # 创建分组键（基于目标语言）
                key = f"{task.target_language}"

                if key not in grouped_tasks:
                    grouped_tasks[key] = []

                # 添加Sheet信息到任务
                task.sheet_name = sheet_name
                grouped_tasks[key].append(task)

        # 创建批次
        all_batches = []
        for key, tasks in grouped_tasks.items():
            # 按批次大小分组
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                all_batches.append(batch)

        logger.info(f"跨Sheet批处理：{len(all_batches)}个批次")
        return all_batches

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