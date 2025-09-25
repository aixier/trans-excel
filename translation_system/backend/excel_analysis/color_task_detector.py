"""
基于颜色的翻译任务检测器
模块化设计，支持扩展不同颜色规则
"""
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import logging
import re

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型枚举"""
    BLANK_FILL = "blank_fill"  # 填充空白单元格
    YELLOW_SOURCE = "yellow_source"  # 黄色单元格作为源语言
    BLUE_OPTIMIZE = "blue_optimize"  # 蓝色单元格优化（缩短）
    RED_PRIORITY = "red_priority"  # 红色高优先级（预留）
    GREEN_REVIEW = "green_review"  # 绿色需要复查（预留）


@dataclass
class ColorRule:
    """颜色规则定义"""
    color_codes: List[str]  # 支持的颜色代码列表
    task_type: TaskType  # 对应的任务类型
    description: str  # 规则描述
    priority: int  # 优先级（数字越小优先级越高）

    def matches(self, color: str) -> bool:
        """检查颜色是否匹配规则"""
        if not color:
            return False
        # 标准化颜色代码
        color = color.upper().replace('#', '').replace('0X', '')
        return any(code.upper().replace('#', '') in color for code in self.color_codes)


@dataclass
class TranslationTask:
    """翻译任务"""
    row_index: int
    source_column: str
    target_column: Optional[str]
    source_text: str
    task_type: TaskType
    cell_address: str
    comment: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'row': self.row_index,
            'source_col': self.source_column,
            'target_col': self.target_column,
            'source_text': self.source_text,
            'task_type': self.task_type.value,
            'cell_address': self.cell_address,
            'comment': self.comment,
            'metadata': self.metadata
        }


class ColorTaskDetector:
    """基于颜色的任务检测器"""

    def __init__(self, custom_rules: Optional[List[ColorRule]] = None, source_langs: Optional[List[str]] = None):
        """
        初始化检测器

        Args:
            custom_rules: 自定义颜色规则列表
        """
        # 默认颜色规则（扩展颜色范围）
        self.default_rules = [
            ColorRule(
                color_codes=[
                    'FFFF00', 'FFFFFF00',  # 标准黄色
                    'FFD700', 'FFFFD700',  # 金色
                    'FFFFE0', 'FFFFFFE0',  # 浅黄色
                    'FFF8DC', 'FFFFF8DC',  # 玉米丝色
                    'FFFACD', 'FFFFFACD',  # 柠檬绸色
                    'FFEFD5', 'FFFFEFD5',  # 番木瓜色
                    'FFE4B5', 'FFFFE4B5',  # 鹿皮色
                ],
                task_type=TaskType.YELLOW_SOURCE,
                description="黄色单元格作为新的源语言进行翻译",
                priority=2
            ),
            ColorRule(
                color_codes=[
                    '0000FF', 'FF0000FF',  # 标准蓝色
                    '00B0F0', 'FF00B0F0',  # 浅蓝色（Excel常用）
                    '0070C0', 'FF0070C0',  # 深浅蓝色
                    '4169E1', 'FF4169E1',  # 皇室蓝
                    '6495ED', 'FF6495ED',  # 矢车菊蓝
                    '00BFFF', 'FF00BFFF',  # 深天蓝
                    '87CEEB', 'FF87CEEB',  # 天蓝色
                    'ADD8E6', 'FFADD8E6',  # 淡蓝色
                    '4472C4', 'FF4472C4',  # Excel主题蓝
                    '5B9BD5', 'FF5B9BD5',  # Excel浅蓝
                ],
                task_type=TaskType.BLUE_OPTIMIZE,
                description="蓝色单元格内容需要优化（缩短）",
                priority=3
            ),
            # 预留的规则
            ColorRule(
                color_codes=['FF0000', 'DC143C', 'FF6347'],  # 红色系
                task_type=TaskType.RED_PRIORITY,
                description="红色单元格表示高优先级任务",
                priority=1
            ),
            ColorRule(
                color_codes=['00FF00', '32CD32', '90EE90'],  # 绿色系
                task_type=TaskType.GREEN_REVIEW,
                description="绿色单元格需要人工复查",
                priority=4
            )
        ]

        # 合并自定义规则
        self.rules = custom_rules if custom_rules else self.default_rules
        self.rules.sort(key=lambda x: x.priority)  # 按优先级排序

        # 保存源语言配置
        self.source_langs = source_langs

        logger.info(f"颜色任务检测器初始化完成，共{len(self.rules)}条规则")
        if source_langs:
            logger.info(f"指定源语言: {source_langs}")

    def detect_tasks_by_phase(
        self,
        df: pd.DataFrame,
        metadata: Dict[str, Any],
        phase: int = 1
    ) -> List[TranslationTask]:
        """
        按阶段检测任务

        Args:
            df: 数据DataFrame
            metadata: 单元格元数据 {cell_address: CellMetadata}
            phase: 翻译阶段 (1=空白填充, 2=黄色翻译, 3=蓝色优化)

        Returns:
            该阶段的任务列表
        """
        if phase == 1:
            return self._detect_blank_fill_tasks(df, metadata)
        elif phase == 2:
            return self._detect_yellow_source_tasks(df, metadata)
        elif phase == 3:
            return self._detect_blue_optimize_tasks(df, metadata)
        else:
            logger.warning(f"未知的翻译阶段: {phase}")
            return []

    def _detect_blank_fill_tasks(
        self,
        df: pd.DataFrame,
        metadata: Dict[str, Any]
    ) -> List[TranslationTask]:
        """
        阶段1：检测空白单元格填充任务

        找出需要翻译的空白单元格，并关联批注信息
        """
        tasks = []

        # 识别源语言列和目标语言列
        source_columns = self._identify_source_columns(df)
        target_columns = self._identify_target_columns(df)

        logger.info(f"识别到源语言列: {source_columns}")
        logger.info(f"识别到目标语言列: {target_columns}")

        for idx, row in df.iterrows():
            for source_col in source_columns:
                source_text = row[source_col]
                if pd.isna(source_text) or str(source_text).strip() == '':
                    continue

                # 对每个目标语言列检查是否需要翻译
                for target_col in target_columns:
                    target_text = row[target_col]
                    if pd.isna(target_text) or str(target_text).strip() == '':
                        # 需要翻译
                        source_addr = self._get_cell_address(source_col, idx, df)
                        target_addr = self._get_cell_address(target_col, idx, df)

                        # 获取源单元格的批注
                        comment = None
                        if source_addr in metadata:
                            comment = metadata[source_addr].comment

                        task = TranslationTask(
                            row_index=idx,
                            source_column=source_col,
                            target_column=target_col,
                            source_text=str(source_text),
                            task_type=TaskType.BLANK_FILL,
                            cell_address=target_addr,
                            comment=comment
                        )
                        tasks.append(task)

        logger.info(f"阶段1：检测到{len(tasks)}个空白填充任务")
        return tasks

    def _detect_yellow_source_tasks(
        self,
        df: pd.DataFrame,
        metadata: Dict[str, Any]
    ) -> List[TranslationTask]:
        """
        阶段2：检测黄色单元格作为源语言的翻译任务

        黄色单元格的内容需要翻译到同行的其他列
        """
        tasks = []
        yellow_rule = next((r for r in self.rules if r.task_type == TaskType.YELLOW_SOURCE), None)

        if not yellow_rule:
            logger.info("未配置黄色单元格规则")
            return tasks

        # 遍历所有元数据，找出黄色单元格
        for cell_addr, cell_meta in metadata.items():
            # 处理元数据格式（可能是dict或CellMetadata对象）
            fill_color = None
            comment = None

            if hasattr(cell_meta, 'fill_color'):
                # CellMetadata对象
                fill_color = cell_meta.fill_color
                comment = cell_meta.comment
            elif isinstance(cell_meta, dict):
                # dict格式
                fill_color = cell_meta.get('fill_color')
                comment = cell_meta.get('comment')

            if fill_color and yellow_rule.matches(fill_color):
                col_letter, row_num = self._parse_cell_address(cell_addr)
                row_idx = row_num - 2  # Excel行号转DataFrame索引（减去标题行）

                if row_idx < 0 or row_idx >= len(df):
                    continue

                source_col = df.columns[self._column_letter_to_index(col_letter)]
                source_text = df.iloc[row_idx][source_col]

                if pd.isna(source_text) or str(source_text).strip() == '':
                    continue

                logger.debug(f"发现黄色单元格 {cell_addr}: {source_text}")

                # 黄色单元格优先级最高：无论目标列有无内容，都要覆盖翻译
                for target_col in df.columns:
                    if target_col != source_col and self._is_translatable_column(target_col):
                        target_addr = self._get_cell_address(target_col, row_idx, df)

                        # 检查目标单元格是否已有内容
                        target_text = df.iloc[row_idx][target_col]
                        has_content = pd.notna(target_text) and str(target_text).strip() != ''

                        if has_content:
                            logger.info(f"黄色单元格优先级最高：将覆盖 {target_addr} 的现有内容")

                        task = TranslationTask(
                            row_index=row_idx,
                            source_column=source_col,
                            target_column=target_col,
                            source_text=str(source_text),
                            task_type=TaskType.YELLOW_SOURCE,
                            cell_address=target_addr,
                            comment=comment,
                            metadata={'original_color': fill_color, 'override': True}  # 标记需要覆盖
                        )
                        tasks.append(task)

        logger.info(f"阶段2：检测到{len(tasks)}个黄色源语言任务")
        return tasks

    def _detect_blue_optimize_tasks(
        self,
        df: pd.DataFrame,
        metadata: Dict[str, Any]
    ) -> List[TranslationTask]:
        """
        阶段3：检测蓝色单元格的优化任务

        蓝色单元格的内容需要缩短优化
        """
        tasks = []
        blue_rule = next((r for r in self.rules if r.task_type == TaskType.BLUE_OPTIMIZE), None)

        if not blue_rule:
            logger.info("未配置蓝色单元格规则")
            return tasks

        # 遍历所有元数据，找出蓝色单元格
        for cell_addr, cell_meta in metadata.items():
            # 处理元数据格式（可能是dict或CellMetadata对象）
            fill_color = None
            comment = None

            if hasattr(cell_meta, 'fill_color'):
                # CellMetadata对象
                fill_color = cell_meta.fill_color
                comment = cell_meta.comment
            elif isinstance(cell_meta, dict):
                # dict格式
                fill_color = cell_meta.get('fill_color')
                comment = cell_meta.get('comment')

            if fill_color and blue_rule.matches(fill_color):
                col_letter, row_num = self._parse_cell_address(cell_addr)
                row_idx = row_num - 2  # Excel行号转DataFrame索引

                if row_idx < 0 or row_idx >= len(df):
                    continue

                col_name = df.columns[self._column_letter_to_index(col_letter)]
                cell_value = df.iloc[row_idx][col_name]

                if pd.isna(cell_value) or str(cell_value).strip() == '':
                    continue

                logger.debug(f"发现蓝色单元格 {cell_addr}: {cell_value}")

                # 优化任务不需要目标列
                task = TranslationTask(
                    row_index=row_idx,
                    source_column=col_name,
                    target_column=None,  # 优化任务回写到原单元格
                    source_text=str(cell_value),
                    task_type=TaskType.BLUE_OPTIMIZE,
                    cell_address=cell_addr,
                    comment=comment or "请缩短内容，保持核心意思",
                    metadata={'original_color': fill_color}
                )
                tasks.append(task)

        logger.info(f"阶段3：检测到{len(tasks)}个蓝色优化任务")
        return tasks

    def _identify_source_columns(self, df: pd.DataFrame) -> List[str]:
        """识别源语言列"""
        source_cols = []

        if self.source_langs:
            # 如果指定了源语言，按照指定的语言查找列
            for col in df.columns:
                col_upper = str(col).upper()
                for src_lang in self.source_langs:
                    src_upper = src_lang.upper()
                    # 匹配列名中的语言标识
                    if src_upper in col_upper or (src_upper == 'CH' and self._is_chinese_column(df[col])):
                        source_cols.append(col)
                        break
        else:
            # 默认逻辑：寻找中文列
            for col in df.columns:
                if self._is_chinese_column(df[col]):
                    source_cols.append(col)

        return source_cols

    def _identify_target_columns(self, df: pd.DataFrame) -> List[str]:
        """识别目标语言列"""
        target_cols = []
        language_patterns = ['PT', 'TH', 'EN', 'ES', 'IND', 'VN']

        for col in df.columns:
            col_upper = str(col).upper()
            if any(pattern in col_upper for pattern in language_patterns):
                target_cols.append(col)

        return target_cols

    def _is_chinese_column(self, series: pd.Series) -> bool:
        """检查列是否包含中文"""
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        non_empty_values = series.dropna().astype(str)

        if len(non_empty_values) == 0:
            return False

        chinese_count = sum(1 for val in non_empty_values if chinese_pattern.search(val))
        return chinese_count > len(non_empty_values) * 0.3  # 30%以上包含中文

    def _is_translatable_column(self, col_name: str) -> bool:
        """检查列是否可作为翻译目标"""
        col_upper = str(col_name).upper()
        # 排除ID、备注等列
        exclude_patterns = ['ID', 'NOTE', 'COMMENT', '备注', '说明']
        if any(pattern in col_upper for pattern in exclude_patterns):
            return False

        # 包含语言标记的列
        language_patterns = ['PT', 'TH', 'EN', 'ES', 'IND', 'VN', 'TEXT']
        return any(pattern in col_upper for pattern in language_patterns)

    def _get_cell_address(self, col_name: str, row_idx: int, df: pd.DataFrame = None) -> str:
        """获取单元格地址"""
        # 如果提供了dataframe，从中获取列索引
        if df is not None and isinstance(col_name, str):
            col_idx = list(df.columns).index(col_name)
        elif isinstance(col_name, str):
            # 尝试从列名推断索引（假设标准命名）
            col_idx = 0  # 默认值
            for i, char in enumerate(['ID', 'Text_CN', 'Text_PT', 'Text_TH', 'Text_EN', '备注']):
                if char == col_name:
                    col_idx = i
                    break
        else:
            col_idx = col_name

        col_letter = self._index_to_column_letter(col_idx)
        return f"{col_letter}{row_idx + 2}"  # +2 因为Excel从1开始且有标题行

    def _parse_cell_address(self, address: str) -> Tuple[str, int]:
        """解析单元格地址为列字母和行号"""
        import re
        match = re.match(r'([A-Z]+)(\d+)', address.upper())
        if match:
            return match.group(1), int(match.group(2))
        return '', 0

    def _column_letter_to_index(self, letter: str) -> int:
        """列字母转索引"""
        index = 0
        for i, char in enumerate(reversed(letter.upper())):
            index += (ord(char) - ord('A') + 1) * (26 ** i)
        return index - 1

    def _index_to_column_letter(self, index: int) -> str:
        """索引转列字母"""
        letter = ''
        while index >= 0:
            letter = chr(index % 26 + ord('A')) + letter
            index = index // 26 - 1
        return letter

    def add_rule(self, rule: ColorRule):
        """添加新的颜色规则"""
        self.rules.append(rule)
        self.rules.sort(key=lambda x: x.priority)
        logger.info(f"添加新规则: {rule.description}")

    def remove_rule(self, task_type: TaskType):
        """移除指定类型的规则"""
        self.rules = [r for r in self.rules if r.task_type != task_type]
        logger.info(f"移除规则类型: {task_type.value}")