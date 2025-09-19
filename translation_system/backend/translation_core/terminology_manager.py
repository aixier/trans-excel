"""
术语管理器
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import re
from database.connection import AsyncSession
from database.models import Terminology
from sqlalchemy import select
from excel_analysis.header_analyzer import SheetInfo, ColumnType
import pandas as pd


@dataclass
class TerminologyEntry:
    """术语条目"""
    source: str              # 源语言术语
    target: Dict[str, str]   # 各语言翻译 {'en': 'Health', 'pt': 'Saúde'}
    category: str = None     # 分类 (UI, Battle, Economy)
    priority: int = 1        # 优先级 (1-5, 5最高)
    context: str = None      # 使用上下文
    case_sensitive: bool = True  # 是否大小写敏感


class TerminologyManager:
    """术语管理器"""

    def __init__(self):
        self.terminology_cache = {}  # 缓存术语表

    async def load_terminology(self, db: AsyncSession, project_id: str, language: str = None) -> Dict[str, TerminologyEntry]:
        """加载项目术语表"""
        cache_key = f"{project_id}_{language}"

        if cache_key in self.terminology_cache:
            return self.terminology_cache[cache_key]

        # 从数据库加载术语
        query = select(Terminology).where(Terminology.project_id == project_id)

        if language:
            # 过滤包含指定语言的术语
            query = query.where(Terminology.target_translations.op('JSON_CONTAINS_PATH')('$.' + language))

        result = await db.execute(query)
        rows = result.scalars().all()

        terminology = {}
        for row in rows:
            entry = TerminologyEntry(
                source=row.source,
                target=json.loads(row.target_translations) if isinstance(row.target_translations, str) else row.target_translations,
                category=row.category,
                priority=row.priority,
                context=row.context,
                case_sensitive=row.case_sensitive
            )
            terminology[row.source] = entry

        self.terminology_cache[cache_key] = terminology
        return terminology

    def apply_terminology(self, text: str, target_language: str, terminology: Dict[str, TerminologyEntry]) -> str:
        """在文本中应用术语翻译"""
        if not text or not terminology:
            return text

        result_text = text

        # 按优先级排序术语 (高优先级先处理)
        sorted_terms = sorted(terminology.items(),
                            key=lambda x: x[1].priority,
                            reverse=True)

        for source_term, entry in sorted_terms:
            if target_language not in entry.target:
                continue

            target_term = entry.target[target_language]

            # 根据大小写敏感性进行替换
            if entry.case_sensitive:
                result_text = result_text.replace(source_term, target_term)
            else:
                # 不区分大小写的替换
                pattern = re.compile(re.escape(source_term), re.IGNORECASE)
                result_text = pattern.sub(target_term, result_text)

        return result_text

    async def create_terminology_from_excel(self, db: AsyncSession, project_id: str, df: pd.DataFrame, sheet_info: SheetInfo):
        """从Excel术语表创建术语库"""
        if not sheet_info.is_terminology:
            return

        source_cols = [col for col in sheet_info.columns if col.column_type == ColumnType.SOURCE]
        target_cols = [col for col in sheet_info.columns if col.column_type == ColumnType.TARGET]

        if not source_cols:
            return

        source_col = source_cols[0].name

        for _, row in df.iterrows():
            source_text = row[source_col]
            if pd.isna(source_text) or str(source_text).strip() == '':
                continue

            # 构建目标语言翻译字典
            target_translations = {}
            for target_col in target_cols:
                target_text = row[target_col.name]
                if pd.notna(target_text) and str(target_text).strip():
                    target_translations[target_col.language] = str(target_text).strip()

            if target_translations:
                await self.save_terminology(db, project_id, source_text, target_translations)

    async def save_terminology(self, db: AsyncSession, project_id: str, source: str, target_translations: Dict[str, str]):
        """保存术语到数据库"""
        # 检查是否已存在
        query = select(Terminology).where(
            Terminology.project_id == project_id,
            Terminology.source == source
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            # 更新现有术语
            existing.target_translations = target_translations
            existing.updated_at = func.now()
        else:
            # 创建新术语
            new_terminology = Terminology(
                project_id=project_id,
                source=source,
                target_translations=target_translations
            )
            db.add(new_terminology)

        await db.commit()

        # 清除缓存
        self.terminology_cache.clear()

    def batch_apply_terminology(
        self,
        texts: List[str],
        target_language: str,
        terminology: Dict[str, TerminologyEntry]
    ) -> List[str]:
        """批量应用术语翻译"""
        return [self.apply_terminology(text, target_language, terminology) for text in texts]