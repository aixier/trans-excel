"""
术语管理器
"""
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import json
import re
import time
from database.connection import AsyncSession
from database.models import Terminology
from sqlalchemy import select, func
from excel_analysis.header_analyzer import SheetInfo, ColumnType
import pandas as pd
import logging

logger = logging.getLogger(__name__)


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
        self.project_terms_cache = {}  # 项目术语内存缓存 {project_id: {source: TerminologyEntry}}
        self.cache_loaded = {}  # 记录哪些项目已加载 {project_id: bool}

    async def preload_all_terminology(self, db: AsyncSession, project_id: str):
        """预加载项目的所有术语到内存（只执行一次）"""
        if self.cache_loaded.get(project_id, False):
            logger.info(f"术语表已缓存，跳过加载: {project_id}")
            return

        logger.info(f"开始预加载术语表: {project_id}")
        start_time = time.time()

        try:
            # 从数据库加载所有术语
            query = select(Terminology).where(Terminology.project_id == project_id)
            result = await db.execute(query)
            rows = result.scalars().all()

            # 构建内存缓存
            self.project_terms_cache[project_id] = {}
            for row in rows:
                entry = TerminologyEntry(
                    source=row.source,
                    target=json.loads(row.target_translations) if isinstance(row.target_translations, str) else row.target_translations,
                    category=row.category,
                    priority=row.priority,
                    context=row.context,
                    case_sensitive=row.case_sensitive
                )
                self.project_terms_cache[project_id][row.source] = entry

            # 标记已加载
            self.cache_loaded[project_id] = True

            load_time = time.time() - start_time
            logger.info(f"术语表预加载完成: {project_id}, 数量: {len(self.project_terms_cache[project_id])}, 耗时: {load_time:.3f}秒")

        except Exception as e:
            logger.error(f"术语表预加载失败: {project_id}, 错误: {e}")
            raise

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

    def match_terminology_for_batch(
        self,
        batch_texts: List[str],
        project_id: str,
        target_languages: List[str]
    ) -> Dict[str, TerminologyEntry]:
        """为批次文本匹配相关术语（内存操作，毫秒级）"""
        if project_id not in self.project_terms_cache:
            logger.warning(f"项目术语未预加载: {project_id}")
            return {}

        start_time = time.time()

        # 合并所有文本为一个大字符串，用于快速匹配
        combined_text = ' '.join(batch_texts).lower() if batch_texts else ''

        # 获取项目的所有术语
        all_terms = self.project_terms_cache[project_id]
        matched_terms = {}

        # 快速匹配相关术语
        for source, entry in all_terms.items():
            # 检查术语是否出现在批次文本中
            search_term = source.lower() if not entry.case_sensitive else source
            search_text = combined_text if not entry.case_sensitive else ' '.join(batch_texts)

            if search_term in search_text:
                # 检查术语是否有目标语言的翻译
                has_target_translation = any(
                    lang in entry.target for lang in target_languages
                )
                if has_target_translation:
                    matched_terms[source] = entry

        match_time = (time.time() - start_time) * 1000  # 转换为毫秒
        logger.debug(f"术语匹配完成: 批次大小={len(batch_texts)}, 匹配数={len(matched_terms)}, 耗时={match_time:.2f}ms")

        return matched_terms

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

    def format_terminology_for_prompt(
        self,
        terminology: Dict[str, TerminologyEntry],
        target_languages: List[str]
    ) -> str:
        """根据术语数量自适应格式化术语表用于Prompt"""
        if not terminology:
            return ""

        # 获取第一个目标语言作为示例
        primary_language = target_languages[0] if target_languages else 'en'

        # 过滤出有目标语言翻译的术语
        valid_terms = {}
        for source, entry in terminology.items():
            if primary_language in entry.target:
                valid_terms[source] = entry.target[primary_language]

        if not valid_terms:
            return ""

        term_count = len(valid_terms)

        # 根据术语数量选择格式化策略
        if term_count <= 20:
            # 完整列出所有术语
            formatted = "\n\n术语表（必须严格遵守）："
            for source, target in valid_terms.items():
                formatted += f"\n- {source} → {target}"
            return formatted

        elif term_count <= 50:
            # 按类别分组（如果有类别信息）
            formatted = "\n\n术语表（必须严格遵守）："
            categorized = {}

            for source, entry in terminology.items():
                if primary_language not in entry.target:
                    continue
                category = entry.category or '通用'
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append((source, entry.target[primary_language]))

            for category, terms in categorized.items():
                if terms:
                    formatted += f"\n\n【{category}】"
                    # 每个类别最多显示10个
                    for source, target in terms[:10]:
                        formatted += f"\n- {source} → {target}"
                    if len(terms) > 10:
                        formatted += f"\n... 还有{len(terms) - 10}个{category}术语"

            return formatted

        else:
            # 大量术语，简化显示
            formatted = f"\n\n术语表（必须严格遵守）："
            formatted += f"\n本次翻译涉及 {term_count} 个专业术语，核心术语如下："

            # 按优先级排序，显示前15个
            sorted_terms = sorted(
                terminology.items(),
                key=lambda x: x[1].priority,
                reverse=True
            )[:15]

            for source, entry in sorted_terms:
                if primary_language in entry.target:
                    formatted += f"\n- {source} → {entry.target[primary_language]}"

            formatted += f"\n... 还有 {term_count - 15} 个术语"
            formatted += "\n\n注：所有术语翻译必须与术语表保持一致。"

            return formatted

    def batch_apply_terminology(
        self,
        texts: List[str],
        target_language: str,
        terminology: Dict[str, TerminologyEntry]
    ) -> List[str]:
        """批量应用术语翻译"""
        return [self.apply_terminology(text, target_language, terminology) for text in texts]