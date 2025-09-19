"""
Excel表头分析器
基于test_concurrent_batch.py扩展的智能分析功能
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import re


class ColumnType(str, Enum):
    """列类型枚举"""
    KEY = "key"                    # 键列 (如: ID, Key)
    SOURCE = "source"              # 源语言列 (如: CH, Chinese, 中文)
    TARGET = "target"              # 目标语言列 (如: EN, PT, TH, IND)
    CONTEXT = "context"            # 上下文列 (如: Context, Remark)
    STATUS = "status"              # 状态列 (如: Status, Flag)
    METADATA = "metadata"          # 元数据列 (如: Category, Type)


@dataclass
class ColumnInfo:
    """列信息"""
    index: int
    name: str
    column_type: ColumnType
    language: Optional[str] = None  # 语言代码 (en, pt, th, ind)
    is_required: bool = False       # 是否必需翻译
    sample_data: List[str] = None   # 样本数据

    def __post_init__(self):
        if self.sample_data is None:
            self.sample_data = []


@dataclass
class SheetInfo:
    """Sheet信息"""
    name: str
    is_terminology: bool = False    # 是否术语表
    columns: List[ColumnInfo] = None
    total_rows: int = 0
    translatable_rows: int = 0

    def __post_init__(self):
        if self.columns is None:
            self.columns = []


class HeaderAnalyzer:
    """表头分析器 - 基于Demo的智能扩展"""

    def __init__(self):
        # 语言识别规则
        self.language_patterns = {
            'ch': ['中文', 'chinese', 'cn', 'zh', 'chi'],
            'en': ['english', 'eng', 'en'],
            'pt': ['portuguese', 'pt', 'por', 'brazil', 'br'],
            'th': ['thai', 'th', 'thailand', 'tha'],
            'ind': ['indonesian', 'id', 'ind', 'indonesia'],
            'es': ['spanish', 'es', 'esp', 'spain'],
            'ar': ['arabic', 'ar', 'arab'],
            'ru': ['russian', 'ru', 'rus']
        }

        # 列类型识别规则
        self.column_patterns = {
            ColumnType.KEY: ['id', 'key', 'index', '序号', '编号'],
            ColumnType.CONTEXT: ['context', 'remark', 'note', '备注', '说明', '上下文'],
            ColumnType.STATUS: ['status', 'flag', 'state', '状态', '标记'],
            ColumnType.METADATA: ['category', 'type', 'group', '分类', '类型', '组别']
        }

    def analyze_sheet(self, df: pd.DataFrame, sheet_name: str) -> SheetInfo:
        """分析单个Sheet的结构"""
        columns = []

        for idx, col_name in enumerate(df.columns):
            col_info = self._analyze_column(idx, col_name, df[col_name])
            columns.append(col_info)

        # 检测是否为术语表
        is_terminology = self._is_terminology_sheet(sheet_name, columns)

        # 计算可翻译行数 (基于Demo的空行检测逻辑)
        translatable_rows = self._count_translatable_rows(df, columns)

        return SheetInfo(
            name=sheet_name,
            is_terminology=is_terminology,
            columns=columns,
            total_rows=len(df),
            translatable_rows=translatable_rows
        )

    def _analyze_column(self, index: int, name: str, data: pd.Series) -> ColumnInfo:
        """分析单个列的类型和语言"""
        name_lower = name.lower().strip()

        # 识别语言
        language = None
        column_type = ColumnType.METADATA  # 默认类型

        # 检查是否为语言列
        for lang_code, patterns in self.language_patterns.items():
            if any(pattern in name_lower for pattern in patterns):
                language = lang_code
                column_type = ColumnType.SOURCE if lang_code == 'ch' else ColumnType.TARGET
                break

        # 如果不是语言列，检查其他类型
        if not language:
            for col_type, patterns in self.column_patterns.items():
                if any(pattern in name_lower for pattern in patterns):
                    column_type = col_type
                    break

        # 获取样本数据
        sample_data = data.dropna().head(3).astype(str).tolist()

        # 判断是否必需翻译 (升级Demo中的空行检测)
        is_required = (column_type == ColumnType.TARGET and
                      data.isna().sum() > len(data) * 0.5)  # 超过50%为空

        return ColumnInfo(
            index=index,
            name=name,
            column_type=column_type,
            language=language,
            is_required=is_required,
            sample_data=sample_data
        )

    def _is_terminology_sheet(self, sheet_name: str, columns: List[ColumnInfo]) -> bool:
        """判断是否为术语表"""
        name_lower = sheet_name.lower()
        terminology_keywords = ['terminology', 'term', 'glossary', '术语', '词汇']

        # 1. 根据Sheet名称判断
        if any(keyword in name_lower for keyword in terminology_keywords):
            return True

        # 2. 根据列结构判断 (通常术语表结构简单，只有源语言和目标语言)
        source_cols = [col for col in columns if col.column_type == ColumnType.SOURCE]
        target_cols = [col for col in columns if col.column_type == ColumnType.TARGET]

        return len(source_cols) == 1 and len(target_cols) >= 1 and len(columns) <= 5

    def _count_translatable_rows(self, df: pd.DataFrame, columns: List[ColumnInfo]) -> int:
        """计算需要翻译的行数 - 基于Demo中的智能识别逻辑"""
        source_cols = [col.name for col in columns if col.column_type == ColumnType.SOURCE]
        target_cols = [col.name for col in columns if col.column_type == ColumnType.TARGET]

        if not source_cols or not target_cols:
            return 0

        # 有源文本且目标列为空的行 (与Demo逻辑一致)
        source_col = source_cols[0]
        has_source = df[source_col].notna() & (df[source_col].astype(str).str.strip() != '')

        translatable_count = 0
        for target_col in target_cols:
            needs_translation = has_source & (df[target_col].isna() | (df[target_col].astype(str).str.strip() == ''))
            translatable_count += needs_translation.sum()

        return translatable_count

    def get_translation_batches(self, df: pd.DataFrame, sheet_info: SheetInfo, batch_size: int = 3) -> List[List[tuple]]:
        """获取翻译批次 - 升级Demo中的批次创建逻辑"""
        source_cols = [col for col in sheet_info.columns if col.column_type == ColumnType.SOURCE]
        target_cols = [col for col in sheet_info.columns if col.column_type == ColumnType.TARGET]

        if not source_cols:
            return []

        source_col = source_cols[0].name
        batches = []
        current_batch = []

        for idx, row in df.iterrows():
            source_text = row[source_col]

            # 跳过空的源文本
            if pd.isna(source_text) or str(source_text).strip() == '':
                continue

            # 检查是否需要翻译 (任意目标列为空)
            needs_translation = False
            for target_col in target_cols:
                target_text = row[target_col.name]
                if pd.isna(target_text) or str(target_text).strip() == '':
                    needs_translation = True
                    break

            if needs_translation:
                current_batch.append((idx, str(source_text).strip()))

                if len(current_batch) >= batch_size:
                    batches.append(current_batch)
                    current_batch = []

        # 添加最后一个批次
        if current_batch:
            batches.append(current_batch)

        return batches