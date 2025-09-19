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
            'ch': ['中文', 'chinese', 'cn', 'zh', 'chi', 'ch'],  # 简体中文
            'tw': ['繁体中文', 'traditional', 'tw', 'cht', 'tc', 'hk'],  # 繁体中文
            'en': ['english', 'eng', 'en'],
            'pt': ['portuguese', 'pt', 'por', 'brazil', 'br'],
            'th': ['thai', 'th', 'thailand', 'tha'],
            'ind': ['indonesian', 'id', 'ind', 'indonesia'],
            'tr': ['turkish', 'tr', 'tur', 'turkey'],  # 土耳其语
            'es': ['spanish', 'es', 'esp', 'spain'],
            'ar': ['arabic', 'ar', 'arab'],
            'ru': ['russian', 'ru', 'rus'],
            'ja': ['japanese', 'ja', 'jp', 'jpn'],  # 日语
            'ko': ['korean', 'ko', 'kr', 'kor'],  # 韩语
            'vn': ['vietnamese', 'vn', 'vi', 'vie', 'vietnam'],  # 越南语
            'de': ['german', 'de', 'ger', 'deu'],  # 德语
            'fr': ['french', 'fr', 'fra'],  # 法语
            'it': ['italian', 'it', 'ita']  # 意大利语
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
        # 清理列名中的特殊字符（如冒号）
        clean_name = name.strip(':').strip()
        name_lower = clean_name.lower()

        # 识别语言
        language = None
        column_type = ColumnType.METADATA  # 默认类型

        # 检查是否为语言列
        for lang_code, patterns in self.language_patterns.items():
            if any(pattern in name_lower for pattern in patterns):
                language = lang_code
                # 所有语言列都先标记为TARGET，后续会根据每行内容动态判断
                column_type = ColumnType.TARGET
                break

        # 如果不是语言列，检查其他类型
        if not language:
            for col_type, patterns in self.column_patterns.items():
                if any(pattern in name_lower for pattern in patterns):
                    column_type = col_type
                    break

        # 获取样本数据
        sample_data = data.dropna().head(3).astype(str).tolist()

        # 不需要在这里判断是否必需翻译，因为需要按行判断
        is_required = False

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
        """计算需要翻译的行数 - 按行检测每个单元格"""
        # 获取所有语言列
        language_cols = [col.name for col in columns if col.language is not None]

        if not language_cols:
            return 0

        translatable_count = 0

        # 逐行检查
        for idx, row in df.iterrows():
            # 找出该行中有内容的语言列
            has_content = {}
            for col in language_cols:
                value = row[col]
                has_content[col] = pd.notna(value) and str(value).strip() != ''

            # 如果至少有一个语言列有内容
            if any(has_content.values()):
                # 计算空的语言列数量（需要翻译的）
                empty_cols = [col for col, has_val in has_content.items() if not has_val]
                translatable_count += len(empty_cols)

        return translatable_count

    def get_translation_batches(self, df: pd.DataFrame, sheet_info: SheetInfo, batch_size: int = 3) -> List[List[tuple]]:
        """获取翻译批次 - 按行动态检测源语言和翻译需求"""
        # 获取所有语言列
        language_cols = [(col.name, col.language) for col in sheet_info.columns if col.language is not None]

        if not language_cols:
            return []

        batches = []
        current_batch = []

        for idx, row in df.iterrows():
            # 找出该行的源语言（优先EN，其次CH，再其他有内容的）
            source_text = None
            source_lang = None

            # 先检查EN列
            for col_name, lang in language_cols:
                if lang == 'en' and pd.notna(row[col_name]) and str(row[col_name]).strip():
                    source_text = str(row[col_name]).strip()
                    source_lang = 'en'
                    break

            # 如果没有EN，检查CH列
            if not source_text:
                for col_name, lang in language_cols:
                    if lang == 'ch' and pd.notna(row[col_name]) and str(row[col_name]).strip():
                        source_text = str(row[col_name]).strip()
                        source_lang = 'ch'
                        break

            # 如果都没有，使用任何有内容的列
            if not source_text:
                for col_name, lang in language_cols:
                    if pd.notna(row[col_name]) and str(row[col_name]).strip():
                        source_text = str(row[col_name]).strip()
                        source_lang = lang
                        break

            # 如果没有源文本，跳过该行
            if not source_text:
                continue

            # 检查是否有空的目标语言列（需要翻译）
            needs_translation = False
            target_langs = []
            for col_name, lang in language_cols:
                if lang != source_lang:  # 不是源语言列
                    target_value = row[col_name]
                    if pd.isna(target_value) or str(target_value).strip() == '':
                        needs_translation = True
                        target_langs.append(lang)

            if needs_translation:
                current_batch.append((idx, source_text, source_lang, target_langs))

                if len(current_batch) >= batch_size:
                    batches.append(current_batch)
                    current_batch = []

        # 添加最后一个批次
        if current_batch:
            batches.append(current_batch)

        return batches