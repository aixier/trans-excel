"""Translation prompt templates."""

from typing import Dict, Any


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
        'CH': '中文',
        'CN': '中文',
        'EN': '英文',
        'PT': '葡萄牙语',
        'PT-BR': '巴西葡萄牙语',
        'TH': '泰语',
        'VN': '越南语',
        'VI': '越南语'
    }

    # Target region mapping
    TARGET_REGIONS = {
        'PT': '巴西',
        'PT-BR': '巴西',
        'TH': '泰国',
        'VN': '越南',
        'VI': '越南'
    }

    def build_translation_prompt(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        context: str = "",
        game_info: Dict[str, Any] = None
    ) -> str:
        """
        Build translation prompt based on available information.

        Args:
            source_text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            context: Translation context
            game_info: Game information

        Returns:
            Formatted prompt string
        """
        # Get language names
        source_lang_name = self.LANGUAGE_NAMES.get(source_lang.upper(), source_lang)
        target_lang_name = self.LANGUAGE_NAMES.get(target_lang.upper(), target_lang)
        target_region = self.TARGET_REGIONS.get(target_lang.upper(), '')

        # If we have game info, use the detailed prompt
        if game_info and any(game_info.values()):
            return self.GAME_TRANSLATION_PROMPT.format(
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
            # Use simple prompt
            return self.SIMPLE_TRANSLATION_PROMPT.format(
                source_lang_name=source_lang_name,
                target_lang_name=target_lang_name,
                source_text=source_text
            )

    def build_batch_prompt(
        self,
        texts: list,
        source_lang: str,
        target_lang: str,
        context: str = "",
        game_info: Dict[str, Any] = None
    ) -> str:
        """
        Build prompt for batch translation.

        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            context: Translation context
            game_info: Game information

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

        return prompt