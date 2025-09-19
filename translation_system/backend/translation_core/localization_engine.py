"""
区域化翻译引擎
升级Demo中的通用提示词为区域化本地化引擎
"""
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class RegionConfig:
    """地区配置"""
    code: str               # 地区代码 (na, sa, eu, me, as)
    name: str              # 地区名称
    languages: List[str]    # 支持的语言
    cultural_context: str   # 文化背景描述
    localization_notes: str # 本地化注意事项


class LocalizationEngine:
    """区域化翻译引擎 - 升级Demo中的通用提示词"""

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
        """创建区域化翻译提示词 - 升级Demo中的通用提示词"""

        region = self.regions.get(region_code, self.regions['na'])

        # 基础提示词 (基于Demo的JSON格式要求)
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

        # 添加翻译要求 (保持Demo的JSON格式)
        base_prompt += f"""

翻译要求：
1. 保持原文的游戏语境和情感色彩
2. 使用符合{region.name}地区玩家习惯的表达方式
3. 保护文中的占位符（如 %s, %d, {{num}}, <font></font> 等），翻译后必须完整保留
4. 如果是游戏术语，优先使用约定俗成的翻译
5. 保持译文的自然流畅，符合目标语言的表达习惯

请直接返回翻译结果，不需要解释过程。"""

        return base_prompt

    def create_batch_prompt(
        self,
        texts: List[str],
        target_languages: List[str],
        region_code: str,
        game_background: str = None,
        task_type: str = 'new'
    ) -> str:
        """创建批量翻译提示词 - 基于Demo的批处理格式"""

        region = self.regions.get(region_code, self.regions['na'])

        # 构建语言列表
        language_names = [self._get_language_name(lang) for lang in target_languages]

        base_prompt = f"""你是专业的游戏本地化翻译专家，专门为{region.name}地区进行本地化翻译。

地区特点：
- 文化背景：{region.cultural_context}
- 本地化要点：{region.localization_notes}

翻译任务：
- 源语言：中文
- 目标语言：{', '.join(language_names)}
- 目标地区：{region.name}"""

        if game_background:
            base_prompt += f"\n- 游戏背景：{game_background}"

        # JSON格式要求 (与Demo格式一致)
        base_prompt += f"""

返回JSON格式：
{{
  "translations": [
    {{
      "id": "text_0",
      "original_text": "原文","""

        for lang in target_languages:
            base_prompt += f'\n      "{lang}": "{self._get_language_name(lang)}翻译",'

        base_prompt = base_prompt.rstrip(',')
        base_prompt += """
    }
  ]
}

翻译要求：
1. 保持原文的游戏语境和情感色彩
2. 使用符合目标地区文化特点的表达方式
3. 保护占位符完整性
4. 返回纯JSON格式，不要其他内容"""

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