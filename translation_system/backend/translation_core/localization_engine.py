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
                languages=['th', 'ind', 'vn'],  # 添加越南语支持
                cultural_context='Diverse cultures, hierarchical, polite communication',
                localization_notes='Use polite, respectful language. Consider local customs and hierarchies.'
            ),
            'eu': RegionConfig(
                code='eu',
                name='Europe (欧洲)',
                languages=['en', 'es', 'pt'],
                cultural_context='Diverse European cultures, formal communication',
                localization_notes='Use precise, well-structured language. Consider cultural diversity.'
            ),
        }

    def create_localized_prompt(
        self,
        source_text: str,
        target_language: str,
        region_code: str,
        game_background: str = None,
        task_type: str = 'new',
        source_language: str = None  # 新增源语言参数
    ) -> str:
        """创建区域化翻译提示词 - 升级Demo中的通用提示词"""

        # 根据目标语言自动选择区域，如果没有提供或无效则使用自动选择
        if region_code not in self.regions:
            region_code = self.get_region_for_language(target_language)
        region = self.regions.get(region_code, self.regions['na'])

        # 智能源语言选择：如果未指定源语言，根据目标语言智能选择
        if not source_language:
            source_language = self._get_smart_source_language(target_language)

        # 基础提示词 (基于Demo的JSON格式要求)
        base_prompt = f"""你是专业的游戏本地化翻译专家，专门为{region.name}地区进行本地化翻译。

地区特点：
- 文化背景：{region.cultural_context}
- 本地化要点：{region.localization_notes}

翻译任务：
- 源语言：{self._get_language_name(source_language)}
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
1. 必须将所有中文内容完全翻译为目标语言，绝对不能保留任何中文字符
2. 保持原文的游戏语境和情感色彩
3. 使用符合{region.name}地区玩家习惯的表达方式
4. 保护文中的占位符（如 %s, %d, {{num}}, <font></font> 等），翻译后必须完整保留
5. 如果是游戏术语，优先使用约定俗成的翻译
6. 保持译文的自然流畅，符合目标语言的表达习惯
7. 输出结果中绝对不允许出现任何中文字符或汉字

请直接返回翻译结果，不需要解释过程。"""

        return base_prompt

    def create_batch_prompt(
        self,
        texts: List[str],
        target_languages: List[str],
        region_code: str,
        game_background: str = None,
        task_type: str = 'new',
        cell_comments: Dict[str, str] = None,
        cell_colors: Dict[str, Dict] = None,
        terminology: Dict = None,  # 新增术语参数
        source_language: str = None  # 新增源语言参数
    ) -> str:
        """创建批量翻译提示词 - 基于Demo的批处理格式，支持单元格元数据"""

        # 根据第一个目标语言自动选择区域，如果未提供有效区域
        if region_code not in self.regions and target_languages:
            region_code = self.get_region_for_language(target_languages[0])
        region = self.regions.get(region_code, self.regions['na'])

        # 智能源语言选择：如果未指定源语言，根据目标语言智能选择
        if not source_language and target_languages:
            source_language = self._get_smart_source_language(target_languages[0])

        # 构建语言列表
        language_names = [self._get_language_name(lang) for lang in target_languages]

        base_prompt = f"""你是专业的游戏本地化翻译专家，专门为{region.name}地区进行本地化翻译。

地区特点：
- 文化背景：{region.cultural_context}
- 本地化要点：{region.localization_notes}

翻译任务：
- 源语言：{self._get_language_name(source_language)}
- 目标语言：{', '.join(language_names)}
- 目标地区：{region.name}"""

        if game_background:
            base_prompt += f"\n- 游戏背景：{game_background}"

        # 添加批注信息作为翻译指导
        if cell_comments:
            base_prompt += "\n\n🔴【最高优先级】批注约束（违反将视为翻译失败）："
            base_prompt += "\n以下每条批注都是强制性要求，必须完全理解并严格执行批注中的所有指示："

            for text_id, comment in cell_comments.items():
                # 每条批注都作为硬性规则，完整保留原始内容
                base_prompt += f"\n\n📌 {text_id}:"
                base_prompt += f"\n   批注内容：「{comment}」"
                base_prompt += f"\n   ⚠️ 此批注为强制性约束，必须完全满足批注中的所有要求！"

            base_prompt += "\n\n🔴 关键说明："
            base_prompt += "\n1. 每条批注都包含特定的翻译要求，必须仔细阅读并完全遵守"
            base_prompt += "\n2. 批注可能包含：字数限制、风格要求、特殊用词指导等"
            base_prompt += "\n3. 批注的优先级高于一般翻译规则"
            base_prompt += "\n4. 如批注有具体数字要求（如字数），必须严格满足"
            base_prompt += "\n5. 宁可调整译文内容也要满足批注要求"

        # 添加术语表（在批注后、JSON格式前）
        if terminology:
            # 导入术语管理器以使用格式化方法
            from .terminology_manager import TerminologyManager
            term_manager = TerminologyManager()
            terminology_text = term_manager.format_terminology_for_prompt(
                terminology,
                target_languages
            )
            if terminology_text:
                base_prompt += terminology_text

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

翻译要求（按优先级排序）：
1. 🔴【最高优先级】批注要求：批注中的所有指示都是强制性的，必须完全满足
2. 🔴【次高优先级】完整理解批注：仔细理解批注的真实意图并严格执行
3. 必须将所有中文内容完全翻译为目标语言，绝对不能保留任何中文字符
4. 保护占位符完整性（如 %s, %d, {{num}}, <font> 等）
5. 在满足批注要求的前提下保持核心语义
6. 使用符合目标地区文化特点的表达方式
7. 输出结果中绝对不允许出现任何中文字符或汉字
8. 返回纯JSON格式，不要其他内容

⚠️ 最终提醒：批注是用户的特殊要求，代表最高优先级，必须无条件满足！"""

        return base_prompt

    def _get_language_name(self, lang_code: str) -> str:
        """获取语言名称"""
        lang_names = {
            'ch': 'Chinese (中文)',
            'cn': 'Chinese (中文)',
            'en': 'English (英语)',
            'pt': 'Portuguese (葡萄牙语)',
            'th': 'Thai (泰语)',
            'ind': 'Indonesian (印尼语)',
            'es': 'Spanish (西班牙语)',
            'ar': 'Arabic (阿拉伯语)',
            'ru': 'Russian (俄语)',
            'tr': 'Turkish (土耳其语)',
            'ja': 'Japanese (日语)',
            'ko': 'Korean (韩语)',
            'vn': 'Vietnamese (越南语)'
        }
        return lang_names.get(lang_code.lower(), lang_code)

    def get_region_for_language(self, language: str) -> str:
        """根据目标语言自动选择最合适的区域"""
        # 语言到区域的映射
        language_to_region = {
            'en': 'na',      # 英语 -> 北美
            'pt': 'sa',      # 葡萄牙语 -> 南美
            'es': 'sa',      # 西班牙语 -> 南美
            'ar': 'me',      # 阿拉伯语 -> 中东
            'th': 'as',      # 泰语 -> 东南亚
            'ind': 'as',     # 印尼语 -> 东南亚
            'vn': 'as',      # 越南语 -> 东南亚
            'ja': 'as',      # 日语 -> 亜洲
            'ko': 'as',      # 韩语 -> 亚洲
            'ru': 'eu',      # 俄语 -> 欧洲
            'tr': 'me',      # 土耳其语 -> 中东
        }
        return language_to_region.get(language.lower(), 'na')  # 默认北美

    def validate_region_language(self, region_code: str, language: str) -> bool:
        """验证地区是否支持指定语言"""
        region = self.regions.get(region_code)
        if not region:
            return False
        return language in region.languages or language == 'en'  # 英语作为通用语言

    def _get_smart_source_language(self, target_language: str) -> str:
        """
        根据目标语言智能选择源语言

        选择规则：
        - 亚洲语言目标 (VN/JP/KR/TH/TW) → 源语言默认CH
        - 其他语言目标 → 源语言优先EN，其次CH

        Args:
            target_language: 目标语言代码

        Returns:
            推荐的源语言代码
        """
        target_lang = target_language.lower()

        # 亚洲语言列表
        asian_languages = ['vn', 'vi', 'jp', 'ja', 'kr', 'ko', 'th', 'tw', 'cn', 'ch']

        if target_lang in asian_languages:
            # 亚洲语言目标 → 中文作为源语言
            return 'ch'
        else:
            # 其他语言目标 → 英文优先，中文次之
            # 这里默认返回英文，实际项目中可以进一步检查是否有英文内容
            return 'en'