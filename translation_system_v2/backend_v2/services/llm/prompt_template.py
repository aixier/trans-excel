"""Translation prompt templates."""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PromptTemplate:
    """Manage translation prompt templates."""

    # Main translation prompt template
    GAME_TRANSLATION_PROMPT = """你是一名专业的游戏翻译专家。请根据以下信息进行翻译：

游戏信息:
- 类型: {game_type}
- 世界观: {world_view}
- 风格: {game_style}
- 目标地区: {target_region}

上下文信息:
{context}

请将以下{source_lang_name}文本翻译成{target_lang_name}：
【原文】
{source_text}
【原文结束】

翻译要求：
1. 保持游戏术语的一致性
2. 符合目标地区的文化习惯和语言规范
3. 保留特殊标记和变量（如{{0}}, %s, %d, {{name}}等格式化占位符）
4. 注意UI文本长度限制，翻译不要过长
5. 保持原文的语气和风格
6. 对于专有名词（角色名、地名、技能名等）保持统一翻译

只返回翻译后的文本，不要包含其他解释或标记。"""

    # Simple translation prompt (no game context)
    SIMPLE_TRANSLATION_PROMPT = """请将以下{source_lang_name}文本准确翻译成{target_lang_name}：

【原文】
{source_text}
【原文结束】

翻译要求：
1. 准确传达原文含义
2. 符合目标语言的表达习惯
3. 保留特殊格式和标记
4. 不要添加额外的解释

只返回翻译后的文本。"""

    # Language name mapping
    LANGUAGE_NAMES = {
        # 中文
        'CH': '简体中文',
        'CN': '简体中文',
        'TW': '繁体中文',

        # 英语
        'EN': '英语',

        # 东亚语言
        'JP': '日语',
        'JA': '日语',
        'KR': '韩语',

        # 欧洲语言
        'ES': '西班牙语',
        'PT': '葡萄牙语',
        'BR': '巴西葡萄牙语',
        'PT-BR': '巴西葡萄牙语',
        'FR': '法语',
        'DE': '德语',
        'IT': '意大利语',
        'RU': '俄语',
        'PL': '波兰语',
        'NL': '荷兰语',

        # 东南亚语言
        'TH': '泰语',
        'VN': '越南语',
        'VI': '越南语',
        'IND': '印尼语',
        'ID': '印尼语',
        'MS': '马来语',

        # 中东/南亚语言
        'TR': '土耳其语',
        'AR': '阿拉伯语',
        'HI': '印地语'
    }

    # Target region mapping
    TARGET_REGIONS = {
        'CH': '中国',
        'TW': '台湾',
        'JP': '日本',
        'JA': '日本',
        'KR': '韩国',
        'ES': '西班牙/拉丁美洲',
        'PT': '葡萄牙',
        'BR': '巴西',
        'PT-BR': '巴西',
        'FR': '法国',
        'DE': '德国',
        'IT': '意大利',
        'RU': '俄罗斯',
        'PL': '波兰',
        'NL': '荷兰',
        'TH': '泰国',
        'VN': '越南',
        'VI': '越南',
        'IND': '印度尼西亚',
        'ID': '印度尼西亚',
        'MS': '马来西亚',
        'TR': '土耳其',
        'AR': '阿拉伯地区',
        'HI': '印度'
    }

    def build_translation_prompt(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        context: str = "",
        game_info: Dict[str, Any] = None,
        glossary_config: Dict[str, Any] = None  # ✨ New parameter
    ) -> str:
        """
        Build translation prompt based on available information.

        Args:
            source_text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            context: Translation context
            game_info: Game information
            glossary_config: Glossary configuration

        Returns:
            Formatted prompt string
        """
        # Get language names
        source_lang_name = self.LANGUAGE_NAMES.get(source_lang.upper(), source_lang)
        target_lang_name = self.LANGUAGE_NAMES.get(target_lang.upper(), target_lang)
        target_region = self.TARGET_REGIONS.get(target_lang.upper(), '')

        # Build base prompt
        if game_info and any(game_info.values()):
            prompt = self.GAME_TRANSLATION_PROMPT.format(
                game_type=game_info.get('game_type', '未知'),
                world_view=game_info.get('world_view', '未知'),
                game_style=game_info.get('game_style', '未知'),
                target_region=target_region,
                context=context or '无额外上下文',
                source_lang_name=source_lang_name,
                target_lang_name=target_lang_name,
                source_text=source_text
            )
        else:
            prompt = self.SIMPLE_TRANSLATION_PROMPT.format(
                source_lang_name=source_lang_name,
                target_lang_name=target_lang_name,
                source_text=source_text
            )

        # ✨ Inject glossary if enabled
        if glossary_config and glossary_config.get('enabled'):
            glossary_text = self._inject_glossary(
                source_text,
                glossary_config.get('id'),
                target_lang
            )
            if glossary_text:
                # Insert glossary before translation requirements
                prompt = prompt.replace('翻译要求：', f'{glossary_text}\n\n翻译要求：')

        return prompt

    def build_batch_prompt(
        self,
        texts: list,
        source_lang: str,
        target_lang: str,
        context: str = "",
        game_info: Dict[str, Any] = None,
        glossary_config: Dict[str, Any] = None  # ✨ New parameter
    ) -> str:
        """
        Build prompt for batch translation.

        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            context: Translation context
            game_info: Game information
            glossary_config: Glossary configuration

        Returns:
            Formatted prompt string
        """
        # Get language names
        source_lang_name = self.LANGUAGE_NAMES.get(source_lang.upper(), source_lang)
        target_lang_name = self.LANGUAGE_NAMES.get(target_lang.upper(), target_lang)
        target_region = self.TARGET_REGIONS.get(target_lang.upper(), '')

        # Format texts with numbers
        numbered_texts = '\n'.join([f"{i+1}. {text}" for i, text in enumerate(texts)])

        prompt = f"""你是一名专业的游戏翻译专家。请根据以下信息进行批量翻译：

游戏信息:
- 类型: {game_info.get('game_type', '未知') if game_info else '未知'}
- 世界观: {game_info.get('world_view', '未知') if game_info else '未知'}
- 目标地区: {target_region}

请将以下{source_lang_name}文本翻译成{target_lang_name}：

【原文列表】
{numbered_texts}
【原文结束】

请返回翻译结果，保持相同的编号格式：
1. [第一条翻译]
2. [第二条翻译]
...

翻译要求：
1. 保持游戏术语的一致性
2. 保留特殊格式和变量
3. 每行一个翻译结果，保持编号对应"""

        # ✨ Inject glossary for batch (match across all texts)
        if glossary_config and glossary_config.get('enabled'):
            glossary_text = self._inject_glossary_batch(
                texts,
                glossary_config.get('id'),
                target_lang
            )
            if glossary_text:
                prompt = prompt.replace('翻译要求：', f'{glossary_text}\n\n翻译要求：')

        return prompt

    def build_task_specific_prompt(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        task_type: str = 'normal',
        context: str = "",
        game_info: Dict[str, Any] = None,
        glossary_config: Dict[str, Any] = None  # ✨ New parameter
    ) -> str:
        """
        Build task-specific prompt based on task type.

        Args:
            source_text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            task_type: Task type ('normal', 'yellow', 'blue')
            context: Translation context
            game_info: Game information
            glossary_config: Glossary configuration

        Returns:
            Task-specific formatted prompt string
        """
        # 构建基础Prompt
        base_prompt = self.build_translation_prompt(
            source_text=source_text,
            source_lang=source_lang,
            target_lang=target_lang,
            context=context,
            game_info=game_info,
            glossary_config=glossary_config  # ✨ Pass through
        )

        # 根据任务类型添加特殊指令
        if task_type == 'yellow':
            # 黄色重译任务特殊指令
            # ✨ 检查是否有英文参考
            reference_en = (game_info or {}).get('reference_en', '') if game_info else ''

            if reference_en:
                # 有英文参考时的特殊Prompt
                additional_instruction = f"""

【英文参考翻译】
{reference_en}
【英文参考结束】

特别注意：
1. 这是重译任务，中文原文已修改
2. 请参考上述英文翻译，保持风格和术语一致
3. 提供准确、地道的{self.LANGUAGE_NAMES.get(target_lang.upper(), target_lang)}翻译
"""
            else:
                # 无英文参考时的标准重译提示
                additional_instruction = "\n\n特别注意：这是重译任务，请重新审视现有翻译质量，提供更准确和地道的翻译。"

            return base_prompt + additional_instruction
        elif task_type == 'blue':
            # 蓝色缩短任务特殊指令
            additional_instruction = "\n\n特别注意：请在保持意思的前提下减少3-10个字，尽量缩短译文长度。"
            return base_prompt + additional_instruction
        else:
            # 普通任务，返回基础Prompt
            return base_prompt

    def _inject_glossary(
        self,
        source_text: str,
        glossary_id: str,
        target_lang: str
    ) -> str:
        """
        Inject glossary terms for single text.

        Args:
            source_text: Text to analyze
            glossary_id: Glossary ID to use
            target_lang: Target language

        Returns:
            Formatted glossary string
        """
        if not glossary_id:
            return ""

        try:
            from services.glossary_manager import glossary_manager

            # Load glossary
            glossary = glossary_manager.load_glossary(glossary_id)
            if not glossary:
                return ""

            # Match terms in text
            matched_terms = glossary_manager.match_terms_in_text(
                source_text,
                glossary,
                target_lang
            )

            # Format for prompt
            if matched_terms:
                return glossary_manager.format_glossary_for_prompt(matched_terms)

        except Exception as e:
            logger.warning(f"Failed to inject glossary: {e}")

        return ""

    def _inject_glossary_batch(
        self,
        texts: List[str],
        glossary_id: str,
        target_lang: str
    ) -> str:
        """
        Inject glossary terms for batch texts.

        Args:
            texts: List of texts to analyze
            glossary_id: Glossary ID to use
            target_lang: Target language

        Returns:
            Formatted glossary string
        """
        if not glossary_id:
            return ""

        try:
            from services.glossary_manager import glossary_manager

            # Load glossary
            glossary = glossary_manager.load_glossary(glossary_id)
            if not glossary:
                return ""

            # Match terms across all texts
            matched_terms = glossary_manager.match_terms_in_batch(
                texts,
                glossary,
                target_lang
            )

            # Format for prompt
            if matched_terms:
                return glossary_manager.format_glossary_for_prompt(matched_terms)

        except Exception as e:
            logger.warning(f"Failed to inject glossary for batch: {e}")

        return ""