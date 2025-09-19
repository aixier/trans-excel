# 游戏本地化智能翻译系统架构设计

## 1. 架构概述

专为游戏本地化设计的智能翻译系统，支持Excel表头分析、占位符保护、术语一致性、区域化翻译和持续维护。

### 1.1 业务场景
- **游戏本地化翻译**：支持游戏文本的专业翻译和维护
- **Excel智能分析**：自动分析表头、Sheet结构，识别翻译对象
- **占位符保护**：保护 `%s` `%d` `{num}` `\n` `<font></font>` 等特殊标记
- **术语一致性**：维护游戏术语表，确保翻译一致性
- **区域化翻译**：针对不同地区（欧美、南美、中东等）提供本地化翻译
- **持续维护**：支持新增、修改、缩短等不同类型的翻译需求

### 1.2 设计原则
- **游戏导向**：专注游戏本地化的特殊需求
- **智能分析**：自动识别翻译内容和规则
- **术语管理**：统一术语库管理和应用
- **简化架构**：去除复杂中间件，专注核心功能
- **持续迭代**：支持游戏版本的持续更新

### 1.3 系统架构图
```
                    ┌─────────────────────────────────────┐
                    │           Web Interface             │
                    │        (Upload & Monitor)           │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────────────────────────┐
                    │          FastAPI Gateway            │
                    │        (RESTful APIs Only)          │
                    └─────────────────┬───────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
┌───────────────┐          ┌─────────────────┐           ┌─────────────────┐
│ Excel Analysis│          │Translation Core │           │ Project Manager │
│   Service     │          │    Service      │           │    Service      │
│               │          │                 │           │                 │
│ • 表头分析    │          │ • 占位符保护    │           │ • 项目管理      │
│ • Sheet识别   │          │ • 术语应用      │           │ • 版本控制      │
│ • 翻译检测    │          │ • 区域化翻译    │           │ • 状态跟踪      │
└───────┬───────┘          └─────────┬───────┘           └─────────┬───────┘
        │                             │                             │
        └─────────────────────────────┼─────────────────────────────┘
                                      │
                    ┌─────────────────────────────────────┐
                    │           Data Layer                │
                    └─────────────────┬───────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
    ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
    │   阿里云OSS    │        │     MySQL     │        │  File System  │
    │   Storage     │        │   Database    │        │   (Temp)      │
    │               │        │               │        │               │
    │ • Excel文件   │        │ • 项目数据    │        │ • 临时文件    │
    │ • 结果文件    │        │ • 术语库      │        │ • 处理缓存    │
    │ • 版本历史    │        │ • 翻译历史    │        │               │
    └───────────────┘        └───────────────┘        └───────────────┘
```

## 2. 核心服务设计

### 2.1 Excel分析服务 (`excel_analysis/`)

#### 2.1.1 表头分析器

```python
# excel_analysis/header_analyzer.py
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class ColumnType(str, Enum):
    KEY = "key"                    # 键列 (如: ID, Key)
    SOURCE = "source"              # 源语言列 (如: CH, Chinese, 中文)
    TARGET = "target"              # 目标语言列 (如: EN, PT, TH, IND)
    CONTEXT = "context"            # 上下文列 (如: Context, Remark)
    STATUS = "status"              # 状态列 (如: Status, Flag)
    METADATA = "metadata"          # 元数据列 (如: Category, Type)

@dataclass
class ColumnInfo:
    index: int
    name: str
    column_type: ColumnType
    language: Optional[str] = None  # 语言代码 (en, pt, th, ind)
    is_required: bool = False       # 是否必需翻译
    sample_data: List[str] = None   # 样本数据

@dataclass
class SheetInfo:
    name: str
    is_terminology: bool = False    # 是否术语表
    columns: List[ColumnInfo] = None
    total_rows: int = 0
    translatable_rows: int = 0

class HeaderAnalyzer:
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

    def analyze_sheet(self, df, sheet_name: str) -> SheetInfo:
        """分析单个Sheet的结构"""
        columns = []

        for idx, col_name in enumerate(df.columns):
            col_info = self._analyze_column(idx, col_name, df[col_name])
            columns.append(col_info)

        # 检测是否为术语表
        is_terminology = self._is_terminology_sheet(sheet_name, columns)

        # 计算可翻译行数
        translatable_rows = self._count_translatable_rows(df, columns)

        return SheetInfo(
            name=sheet_name,
            is_terminology=is_terminology,
            columns=columns,
            total_rows=len(df),
            translatable_rows=translatable_rows
        )

    def _analyze_column(self, index: int, name: str, data) -> ColumnInfo:
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

        # 判断是否必需翻译
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

    def _count_translatable_rows(self, df, columns: List[ColumnInfo]) -> int:
        """计算需要翻译的行数"""
        source_cols = [col.name for col in columns if col.column_type == ColumnType.SOURCE]
        target_cols = [col.name for col in columns if col.column_type == ColumnType.TARGET]

        if not source_cols or not target_cols:
            return 0

        # 有源文本且目标列为空的行
        source_col = source_cols[0]
        has_source = df[source_col].notna() & (df[source_col].astype(str).str.strip() != '')

        translatable_count = 0
        for target_col in target_cols:
            needs_translation = has_source & (df[target_col].isna() | (df[target_col].astype(str).str.strip() == ''))
            translatable_count += needs_translation.sum()

        return translatable_count
```

#### 2.1.2 翻译检测器

```python
# excel_analysis/translation_detector.py
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class TranslationTask:
    sheet_name: str
    row_index: int
    source_text: str
    target_column: str
    target_language: str
    task_type: str = "new"          # new, modify, shorten
    background_color: str = None     # 单元格背景色
    original_translation: str = None # 原有翻译

class TranslationDetector:
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
        df,
        sheet_info: SheetInfo,
        include_colors: bool = True
    ) -> List[TranslationTask]:
        """检测需要翻译的任务"""
        tasks = []

        # 获取源语言列和目标语言列
        source_cols = [col for col in sheet_info.columns if col.column_type == ColumnType.SOURCE]
        target_cols = [col for col in sheet_info.columns if col.column_type == ColumnType.TARGET]

        if not source_cols:
            return tasks

        source_col = source_cols[0]

        for target_col in target_cols:
            for idx, row in df.iterrows():
                source_text = row[source_col.name]
                target_text = row[target_col.name]

                # 跳过空的源文本
                if pd.isna(source_text) or str(source_text).strip() == '':
                    continue

                # 获取背景色 (如果支持)
                background_color = None
                if include_colors:
                    background_color = self._get_cell_background_color(df, idx, target_col.name)

                # 判断任务类型
                task_type = self._determine_task_type(target_text, background_color)

                if task_type in ['new', 'modify', 'shorten']:
                    task = TranslationTask(
                        sheet_name=sheet_info.name,
                        row_index=idx,
                        source_text=str(source_text).strip(),
                        target_column=target_col.name,
                        target_language=target_col.language,
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

        # 2. 根据内容判断
        if pd.isna(target_text) or str(target_text).strip() == '':
            return 'new'  # 新翻译
        else:
            return 'skip'  # 已有翻译，跳过

    def _get_cell_background_color(self, df, row_idx: int, col_name: str) -> str:
        """获取单元格背景色 (需要使用openpyxl)"""
        # 这里需要从Excel文件中读取颜色信息
        # 简化实现，实际需要使用openpyxl库
        try:
            # 实际实现需要访问Excel的样式信息
            return None
        except:
            return None
```

### 2.2 翻译核心服务 (`translation_core/`)

#### 2.2.1 占位符保护器

```python
# translation_core/placeholder_protector.py
import re
from typing import Dict, List, Tuple

class PlaceholderProtector:
    def __init__(self):
        # 占位符规则配置
        self.placeholder_patterns = [
            # C风格占位符
            (r'%[sdioxX%]', 'C_STYLE'),
            (r'%\d*\.?\d*[sdioxX]', 'C_STYLE_NUM'),

            # 花括号占位符
            (r'\{[^}]*\}', 'BRACE_STYLE'),
            (r'\{\d+\}', 'BRACE_NUM'),

            # HTML标签
            (r'<[^>]+>', 'HTML_TAG'),
            (r'<\/[^>]+>', 'HTML_CLOSE_TAG'),

            # 特殊字符
            (r'\\n', 'NEWLINE'),
            (r'\\t', 'TAB'),
            (r'\\r', 'RETURN'),

            # Unity富文本标签
            (r'<color=[^>]*>', 'UNITY_COLOR_OPEN'),
            (r'<\/color>', 'UNITY_COLOR_CLOSE'),
            (r'<size=[^>]*>', 'UNITY_SIZE_OPEN'),
            (r'<\/size>', 'UNITY_SIZE_CLOSE'),

            # 自定义占位符
            (r'\[player_name\]', 'PLAYER_NAME'),
            (r'\[item_name\]', 'ITEM_NAME'),
            (r'\[currency\]', 'CURRENCY')
        ]

    def protect_placeholders(self, text: str) -> Tuple[str, Dict[str, str]]:
        """保护文本中的占位符，返回保护后的文本和映射表"""
        if not text:
            return text, {}

        protected_text = text
        placeholder_map = {}

        for pattern, placeholder_type in self.placeholder_patterns:
            matches = re.finditer(pattern, protected_text, re.IGNORECASE)

            for match in reversed(list(matches)):  # 从后往前替换避免索引问题
                original = match.group()
                placeholder_id = f"__PLACEHOLDER_{len(placeholder_map)}__"

                placeholder_map[placeholder_id] = {
                    'original': original,
                    'type': placeholder_type,
                    'position': match.span()
                }

                protected_text = (protected_text[:match.start()] +
                                placeholder_id +
                                protected_text[match.end():])

        return protected_text, placeholder_map

    def restore_placeholders(self, text: str, placeholder_map: Dict[str, str]) -> str:
        """恢复文本中的占位符"""
        if not text or not placeholder_map:
            return text

        restored_text = text

        for placeholder_id, info in placeholder_map.items():
            if placeholder_id in restored_text:
                restored_text = restored_text.replace(placeholder_id, info['original'])

        return restored_text

    def validate_placeholders(self, original: str, translated: str) -> List[str]:
        """验证翻译后占位符是否完整"""
        warnings = []

        # 提取原文占位符
        _, original_placeholders = self.protect_placeholders(original)

        # 检查译文中占位符
        for placeholder_id, info in original_placeholders.items():
            original_placeholder = info['original']
            if original_placeholder not in translated:
                warnings.append(f"缺失占位符: {original_placeholder}")

        # 检查是否有多余的占位符
        for pattern, _ in self.placeholder_patterns:
            translated_matches = re.findall(pattern, translated, re.IGNORECASE)
            original_matches = re.findall(pattern, original, re.IGNORECASE)

            if len(translated_matches) > len(original_matches):
                warnings.append(f"多余的占位符: {pattern}")

        return warnings
```

#### 2.2.2 术语管理器

```python
# translation_core/terminology_manager.py
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class TerminologyEntry:
    source: str              # 源语言术语
    target: Dict[str, str]   # 各语言翻译 {'en': 'Health', 'pt': 'Saúde'}
    category: str = None     # 分类 (UI, Battle, Economy)
    priority: int = 1        # 优先级 (1-5, 5最高)
    context: str = None      # 使用上下文
    case_sensitive: bool = True  # 是否大小写敏感

class TerminologyManager:
    def __init__(self, mysql_connection):
        self.db = mysql_connection
        self.terminology_cache = {}  # 缓存术语表

    async def load_terminology(self, project_id: str, language: str = None) -> Dict[str, TerminologyEntry]:
        """加载项目术语表"""
        cache_key = f"{project_id}_{language}"

        if cache_key in self.terminology_cache:
            return self.terminology_cache[cache_key]

        # 从数据库加载术语
        query = """
        SELECT source, target_translations, category, priority, context, case_sensitive
        FROM terminology
        WHERE project_id = %s
        """
        params = [project_id]

        if language:
            query += " AND JSON_CONTAINS_PATH(target_translations, 'one', %s)"
            params.append(f'$.{language}')

        results = await self.db.fetch_all(query, params)

        terminology = {}
        for row in results:
            entry = TerminologyEntry(
                source=row['source'],
                target=json.loads(row['target_translations']),
                category=row['category'],
                priority=row['priority'],
                context=row['context'],
                case_sensitive=row['case_sensitive']
            )
            terminology[row['source']] = entry

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

    async def create_terminology_from_excel(self, project_id: str, df, sheet_info: SheetInfo):
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
                await self.save_terminology(project_id, source_text, target_translations)

    async def save_terminology(self, project_id: str, source: str, target_translations: Dict[str, str]):
        """保存术语到数据库"""
        query = """
        INSERT INTO terminology (project_id, source, target_translations, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
        ON DUPLICATE KEY UPDATE
        target_translations = VALUES(target_translations),
        updated_at = NOW()
        """

        await self.db.execute(query, [
            project_id,
            source,
            json.dumps(target_translations, ensure_ascii=False)
        ])

        # 清除缓存
        self.terminology_cache.clear()
```

#### 2.2.3 区域化翻译引擎

```python
# translation_core/localization_engine.py
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class RegionConfig:
    code: str               # 地区代码 (na, sa, eu, me, as)
    name: str              # 地区名称
    languages: List[str]    # 支持的语言
    cultural_context: str   # 文化背景描述
    localization_notes: str # 本地化注意事项

class LocalizationEngine:
    def __init__(self):
        self.regions = {
            'na': RegionConfig(
                code='na',
                name='North America (欧美)',
                languages=['en'],
                cultural_context='Western culture, individualistic, direct communication',
                localization_notes='Use casual, friendly tone. Avoid overly formal language.'
            ),
            'sa': RegionConfig(
                code='sa',
                name='South America (南美)',
                languages=['pt', 'es'],
                cultural_context='Latin culture, community-oriented, expressive communication',
                localization_notes='Use warm, expressive language. Consider local slang and expressions.'
            ),
            'me': RegionConfig(
                code='me',
                name='Middle East (中东)',
                languages=['ar'],
                cultural_context='Traditional values, family-oriented, respectful communication',
                localization_notes='Use respectful, formal language. Be sensitive to cultural and religious values.'
            ),
            'as': RegionConfig(
                code='as',
                name='Southeast Asia (东南亚)',
                languages=['th', 'ind'],
                cultural_context='Diverse cultures, hierarchical, polite communication',
                localization_notes='Use polite, respectful language. Consider local customs and hierarchies.'
            ),
            'eu': RegionConfig(
                code='eu',
                name='Europe (欧洲)',
                languages=['en', 'es', 'pt'],
                cultural_context='Diverse European cultures, formal communication',
                localization_notes='Use precise, well-structured language. Consider cultural diversity.'
            )
        }

    def create_localized_prompt(
        self,
        source_text: str,
        target_language: str,
        region_code: str,
        game_background: str = None,
        task_type: str = 'new'
    ) -> str:
        """创建区域化翻译提示词"""

        region = self.regions.get(region_code, self.regions['na'])

        # 基础提示词
        base_prompt = f"""你是专业的游戏本地化翻译专家，专门为{region.name}地区进行本地化翻译。

地区特点：
- 文化背景：{region.cultural_context}
- 本地化要点：{region.localization_notes}

翻译任务：
- 源语言：中文
- 目标语言：{self._get_language_name(target_language)}
- 目标地区：{region.name}"""

        # 添加游戏背景
        if game_background:
            base_prompt += f"\n- 游戏背景：{game_background}"

        # 根据任务类型调整提示词
        if task_type == 'modify':
            base_prompt += "\n\n任务类型：修改现有翻译，使其更符合地区文化特点。"
        elif task_type == 'shorten':
            base_prompt += "\n\n任务类型：缩短翻译长度，保持意思不变的同时使表达更简洁。"
        else:
            base_prompt += "\n\n任务类型：全新翻译，确保符合地区文化和游戏语境。"

        # 添加翻译要求
        base_prompt += f"""

翻译要求：
1. 保持原文的游戏语境和情感色彩
2. 使用符合{region.name}地区玩家习惯的表达方式
3. 保护文中的占位符（如 %s, %d, {{num}}, <font></font> 等），翻译后必须完整保留
4. 如果是游戏术语，优先使用约定俗成的翻译
5. 保持译文的自然流畅，符合目标语言的表达习惯

请直接返回翻译结果，不需要解释过程。"""

        return base_prompt

    def _get_language_name(self, lang_code: str) -> str:
        """获取语言名称"""
        lang_names = {
            'en': 'English (英语)',
            'pt': 'Portuguese (葡萄牙语)',
            'th': 'Thai (泰语)',
            'ind': 'Indonesian (印尼语)',
            'es': 'Spanish (西班牙语)',
            'ar': 'Arabic (阿拉伯语)',
            'ru': 'Russian (俄语)'
        }
        return lang_names.get(lang_code, lang_code)

    def validate_region_language(self, region_code: str, language: str) -> bool:
        """验证地区是否支持指定语言"""
        region = self.regions.get(region_code)
        if not region:
            return False
        return language in region.languages or language == 'en'  # 英语作为通用语言
```

### 2.3 API网关服务 (`api_gateway/`)

#### 2.3.1 路由定义

```python
# api_gateway/routers/translation.py
from fastapi import APIRouter, UploadFile, HTTPException, Depends
from typing import Optional

router = APIRouter(prefix="/api/v1/translation", tags=["translation"])

@router.post("/upload", response_model=TaskResponse)
async def upload_file(
    file: UploadFile,
    target_languages: str = "pt,th,ind",
    total_rows: int = 190,
    batch_size: int = 3,
    max_concurrent: int = 10,
    user_id: str = Depends(get_current_user)
):
    """
    上传Excel文件并启动翻译任务

    Returns:
        TaskResponse: 包含task_id和初始状态
    """
    pass

@router.get("/task/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """查询任务状态和进度"""
    pass

@router.get("/task/{task_id}/download")
async def download_result(task_id: str):
    """下载翻译完成的文件"""
    pass

@router.post("/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消正在执行的任务"""
    pass

@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    user_id: str = Depends(get_current_user),
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """获取用户任务列表"""
    pass
```

#### 2.3.2 数据模型

```python
# api_gateway/models/task.py
from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict

class TaskStatus(str, Enum):
    PENDING = "pending"           # 等待处理
    UPLOADING = "uploading"       # 文件上传中
    ANALYZING = "analyzing"       # 文件分析中
    TRANSLATING = "translating"   # 翻译中
    ITERATING = "iterating"       # 迭代翻译中
    COMPLETED = "completed"       # 完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消

class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str
    created_at: datetime

class TaskProgress(BaseModel):
    total_rows: int
    translated_rows: int
    current_iteration: int
    max_iterations: int
    completion_percentage: float
    estimated_time_remaining: Optional[int]  # 秒

class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: TaskProgress
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    download_url: Optional[str]  # 完成时提供下载链接

class TranslationMetrics(BaseModel):
    total_api_calls: int
    total_tokens_used: int
    total_cost: float
    average_response_time: float
    success_rate: float
```

### 2.4 项目管理服务 (`project_manager/`)

#### 2.4.1 项目管理器

```python
# project_manager/manager.py
from typing import List, Dict, Optional
import uuid
from datetime import datetime

class ProjectManager:
    def __init__(self, mysql_connection, oss_storage):
        self.db = mysql_connection
        self.storage = oss_storage

    async def create_project(
        self,
        name: str,
        description: str,
        target_languages: List[str],
        user_id: str,
        game_background: str = None,
        region_code: str = 'na'
    ) -> str:
        """创建新项目"""
        project_id = str(uuid.uuid4())

        query = """
        INSERT INTO projects (id, name, description, target_languages, game_background,
                            region_code, user_id, status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', NOW(), NOW())
        """

        await self.db.execute(query, [
            project_id, name, description,
            json.dumps(target_languages),
            game_background, region_code, user_id
        ])

        return project_id

    async def create_version(
        self,
        project_id: str,
        version_name: str,
        description: str = None
    ) -> str:
        """创建项目版本"""
        version_id = str(uuid.uuid4())

        query = """
        INSERT INTO project_versions (id, project_id, version_name, description,
                                    status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, 'active', NOW(), NOW())
        """

        await self.db.execute(query, [
            version_id, project_id, version_name, description
        ])

        return version_id

    async def upload_translation_file(
        self,
        project_id: str,
        version_id: str,
        file: UploadFile,
        file_type: str = 'source'  # source, terminology, completed
    ) -> str:
        """上传翻译文件到项目"""
        # 1. 上传文件到OSS
        file_path = f"projects/{project_id}/versions/{version_id}/{file_type}/{file.filename}"
        file_url = await self.storage.upload(file.file, file_path)

        # 2. 记录文件信息
        file_id = str(uuid.uuid4())
        query = """
        INSERT INTO project_files (id, project_id, version_id, file_name, file_path,
                                 file_type, file_size, upload_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """

        await self.db.execute(query, [
            file_id, project_id, version_id, file.filename,
            file_path, file_type, file.size
        ])

        return file_id

    async def get_project_summary(self, project_id: str) -> Dict:
        """获取项目概览信息"""
        # 项目基本信息
        project_query = """
        SELECT * FROM projects WHERE id = %s
        """
        project = await self.db.fetch_one(project_query, [project_id])

        if not project:
            raise ValueError("Project not found")

        # 版本信息
        versions_query = """
        SELECT * FROM project_versions WHERE project_id = %s ORDER BY created_at DESC
        """
        versions = await self.db.fetch_all(versions_query, [project_id])

        # 翻译任务统计
        tasks_query = """
        SELECT status, COUNT(*) as count FROM translation_tasks
        WHERE project_id = %s GROUP BY status
        """
        task_stats = await self.db.fetch_all(tasks_query, [project_id])

        return {
            'project': dict(project),
            'versions': [dict(v) for v in versions],
            'task_statistics': {stat['status']: stat['count'] for stat in task_stats}
        }
```

### 2.5 数据库设计

#### 2.5.1 MySQL表结构

```sql
-- 项目表
CREATE TABLE projects (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_languages JSON NOT NULL, -- ['pt', 'th', 'ind']
    game_background TEXT,
    region_code VARCHAR(10) DEFAULT 'na',
    user_id VARCHAR(100) NOT NULL,
    status ENUM('active', 'archived', 'deleted') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);

-- 项目版本表
CREATE TABLE project_versions (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    version_name VARCHAR(100) NOT NULL,
    description TEXT,
    status ENUM('active', 'archived') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE KEY uk_project_version (project_id, version_name)
);

-- 项目文件表
CREATE TABLE project_files (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    version_id VARCHAR(36) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type ENUM('source', 'terminology', 'completed', 'template') NOT NULL,
    file_size BIGINT DEFAULT 0,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (version_id) REFERENCES project_versions(id),
    INDEX idx_project_version (project_id, version_id),
    INDEX idx_file_type (file_type)
);

-- 翻译任务表
CREATE TABLE translation_tasks (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    version_id VARCHAR(36) NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    input_file_id VARCHAR(36) NOT NULL,
    output_file_id VARCHAR(36) NULL,
    config JSON NOT NULL, -- 翻译配置
    status ENUM('pending', 'analyzing', 'translating', 'iterating', 'completed', 'failed', 'cancelled') DEFAULT 'pending',

    -- 进度信息
    total_rows INT DEFAULT 0,
    translated_rows INT DEFAULT 0,
    current_iteration INT DEFAULT 0,
    max_iterations INT DEFAULT 5,

    -- 统计信息
    total_api_calls INT DEFAULT 0,
    total_tokens_used INT DEFAULT 0,
    total_cost DECIMAL(10,4) DEFAULT 0.0000,

    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (version_id) REFERENCES project_versions(id),
    INDEX idx_project_version (project_id, version_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- 术语表
CREATE TABLE terminology (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    source VARCHAR(500) NOT NULL,
    target_translations JSON NOT NULL, -- {'en': 'Health', 'pt': 'Saúde'}
    category VARCHAR(100),
    priority INT DEFAULT 1,
    context TEXT,
    case_sensitive BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE KEY uk_project_source (project_id, source),
    INDEX idx_project_category (project_id, category),
    INDEX idx_priority (priority)
);

-- 翻译日志表
CREATE TABLE translation_logs (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    iteration INT NOT NULL,
    batch_id INT NOT NULL,
    request_data JSON,
    response_data JSON,
    tokens_used INT DEFAULT 0,
    duration_ms DECIMAL(10,2) DEFAULT 0.00,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES translation_tasks(id),
    INDEX idx_task_iteration (task_id, iteration),
    INDEX idx_created_at (created_at)
);
```

### 2.6 配置管理

#### 2.6.1 环境配置

```python
# config/settings.py
from pydantic import BaseSettings
from typing import List

class TranslationConfig(BaseSettings):
    # 数据库配置
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str
    mysql_database: str = "translation_system"

    # OSS配置
    oss_access_key_id: str
    oss_access_key_secret: str
    oss_bucket_name: str
    oss_endpoint: str

    # LLM配置
    llm_provider: str = "dashscope"
    llm_model: str = "qwen-plus"
    llm_api_key: str
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 翻译配置
    default_batch_size: int = 3
    default_max_concurrent: int = 10
    default_max_iterations: int = 5
    default_target_languages: List[str] = ["pt", "th", "ind"]
    default_region_code: str = "na"

    # 应用配置
    app_name: str = "游戏本地化智能翻译系统"
    app_version: str = "1.0.0"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False
```

## 3. 使用示例

### 3.1 基本使用流程

```python
# 1. 创建项目
project_manager = ProjectManager(mysql_connection, oss_storage)
project_id = await project_manager.create_project(
    name="RPG游戏本地化",
    description="RPG游戏多语言本地化项目",
    target_languages=["pt", "th", "ind"],
    user_id="user123",
    game_background="中世纪奇幻RPG游戏",
    region_code="sa"  # 南美地区
)

# 2. 创建版本
version_id = await project_manager.create_version(
    project_id=project_id,
    version_name="v1.0.0",
    description="首个版本"
)

# 3. 上传翻译文件
file_id = await project_manager.upload_translation_file(
    project_id=project_id,
    version_id=version_id,
    file=uploaded_file,
    file_type="source"
)

# 4. 分析Excel结构
analyzer = HeaderAnalyzer()
with pd.ExcelFile(file_path) as excel_file:
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name)
        sheet_info = analyzer.analyze_sheet(df, sheet_name)
        print(f"Sheet: {sheet_name}")
        print(f"  - 总行数: {sheet_info.total_rows}")
        print(f"  - 可翻译行数: {sheet_info.translatable_rows}")
        print(f"  - 是否术语表: {sheet_info.is_terminology}")

# 5. 检测翻译任务
detector = TranslationDetector()
tasks = detector.detect_translation_tasks(df, sheet_info, include_colors=True)
print(f"检测到 {len(tasks)} 个翻译任务")

# 6. 应用占位符保护
protector = PlaceholderProtector()
for task in tasks:
    protected_text, placeholder_map = protector.protect_placeholders(task.source_text)
    print(f"原文: {task.source_text}")
    print(f"保护后: {protected_text}")

# 7. 生成区域化提示词
localization_engine = LocalizationEngine()
prompt = localization_engine.create_localized_prompt(
    source_text=task.source_text,
    target_language=task.target_language,
    region_code="sa",  # 南美地区
    game_background="中世纪奇幻RPG游戏",
    task_type=task.task_type
)
print("生成的提示词:", prompt)
```

### 3.2 API使用示例

```bash
# 上传文件并开始翻译
curl -X POST "http://localhost:8000/api/v1/translation/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@game_texts.xlsx" \
  -F "target_languages=pt,th,ind" \
  -F "batch_size=3" \
  -F "max_concurrent=10"

# 查询任务状态
curl -X GET "http://localhost:8000/api/v1/translation/task/{task_id}/status"

# 下载完成的文件
curl -X GET "http://localhost:8000/api/v1/translation/task/{task_id}/download" \
  -o completed_translation.xlsx
```

## 4. 架构优势

### 4.1 游戏本地化专业性
- **占位符保护**：自动识别和保护游戏中的变量和标记
- **术语一致性**：确保游戏术语在整个项目中的一致性
- **区域化适配**：针对不同地区的文化特点进行本地化

### 4.2 智能化分析
- **自动表头识别**：智能识别Excel中的语言列和内容类型
- **颜色标记检测**：支持Excel中的颜色标记工作流程
- **翻译需求检测**：自动检测哪些内容需要翻译

### 4.3 灵活性和可扩展性
- **模块化设计**：各组件独立，易于测试和维护
- **多LLM支持**：可轻松切换不同的翻译服务
- **多存储支持**：支持阿里云OSS、AWS S3等多种存储

### 4.4 高性能处理
- **并发批处理**：支持高并发批量翻译
- **迭代优化**：自动重试未完成的翻译
- **进度监控**：实时跟踪翻译进度

## 5. 部署配置

### 5.1 环境变量配置

```env
# 数据库配置
MYSQL_HOST=rm-uf6k1x3m6t3340l2g.mysql.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USER=trans_excel
MYSQL_PASSWORD=Trans_excel_123
MYSQL_DATABASE=trans_excel

# OSS配置
OSS_ACCESS_KEY_ID=LTAI5tSDhYXXXXXXXXXX
OSS_ACCESS_KEY_SECRET=your_oss_secret_key
OSS_BUCKET_NAME=trans-excel
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com

# LLM配置
LLM_PROVIDER=dashscope
LLM_API_KEY=sk-your-api-key
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 应用配置
DEFAULT_BATCH_SIZE=3
DEFAULT_MAX_CONCURRENT=10
DEFAULT_MAX_ITERATIONS=5
DEFAULT_REGION_CODE=na
```

### 5.2 启动命令

```bash
# 安装依赖
pip install -r requirements.txt

# 数据库初始化
python scripts/init_database.py

# 启动服务
uvicorn api_gateway.main:app --host 0.0.0.0 --port 8000
```

## 6. 项目结构

```
translation_system/
├── README.md
├── requirements.txt
├── .env.example
├── scripts/
│   ├── init_database.py
│   └── migrate.py
├── api_gateway/
│   ├── __init__.py
│   ├── main.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── translation.py
│   │   └── project.py
│   └── models/
│       ├── __init__.py
│       └── task.py
├── excel_analysis/
│   ├── __init__.py
│   ├── header_analyzer.py
│   └── translation_detector.py
├── translation_core/
│   ├── __init__.py
│   ├── placeholder_protector.py
│   ├── terminology_manager.py
│   └── localization_engine.py
├── project_manager/
│   ├── __init__.py
│   └── manager.py
├── file_service/
│   ├── __init__.py
│   ├── oss_storage.py
│   └── local_storage.py
├── database/
│   ├── __init__.py
│   ├── connection.py
│   └── models.py
├── config/
│   ├── __init__.py
│   └── settings.py
└── utils/
    ├── __init__.py
    ├── file_utils.py
    └── logging.py
```

这个架构设计专注于游戏本地化的核心需求，去除了复杂的中间件，使用现有的MySQL和OSS基础设施，提供了完整的游戏翻译解决方案。