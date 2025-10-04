"""Language metadata service - 语言元数据服务"""

from typing import Dict, List

class LanguageMetadata:
    """集中管理语言元数据"""

    # 语言完整信息（单一数据源）
    LANGUAGES = {
        'CH': {
            'code': 'CH',
            'name': '中文',
            'abbr': 'CN',
            'english_name': 'Chinese',
            'can_be_source': True,
            'can_be_target': True,
            'enabled': True
        },
        'EN': {
            'code': 'EN',
            'name': '英文',
            'abbr': 'EN',
            'english_name': 'English',
            'can_be_source': True,
            'can_be_target': True,
            'enabled': True
        },
        'TR': {
            'code': 'TR',
            'name': '土耳其语',
            'abbr': 'TR',
            'english_name': 'Turkish',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        },
        'TH': {
            'code': 'TH',
            'name': '泰语',
            'abbr': 'TH',
            'english_name': 'Thai',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        },
        'PT': {
            'code': 'PT',
            'name': '葡萄牙语',
            'abbr': 'PT',
            'english_name': 'Portuguese',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        },
        'VN': {
            'code': 'VN',
            'name': '越南语',
            'abbr': 'VN',
            'english_name': 'Vietnamese',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        },
        'IND': {
            'code': 'IND',
            'name': '印尼语',
            'abbr': 'ID',
            'english_name': 'Indonesian',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        },
        'ES': {
            'code': 'ES',
            'name': '西班牙语',
            'abbr': 'ES',
            'english_name': 'Spanish',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        },
        'AR': {
            'code': 'AR',
            'name': '阿拉伯语',
            'abbr': 'AR',
            'english_name': 'Arabic',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        },
        'FR': {
            'code': 'FR',
            'name': '法语',
            'abbr': 'FR',
            'english_name': 'French',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        },
        'DE': {
            'code': 'DE',
            'name': '德语',
            'abbr': 'DE',
            'english_name': 'German',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        },
        'JP': {
            'code': 'JP',
            'name': '日语',
            'abbr': 'JP',
            'english_name': 'Japanese',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        },
        'KR': {
            'code': 'KR',
            'name': '韩语',
            'abbr': 'KR',
            'english_name': 'Korean',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        },
        'RU': {
            'code': 'RU',
            'name': '俄语',
            'abbr': 'RU',
            'english_name': 'Russian',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        },
        'TW': {
            'code': 'TW',
            'name': '繁体中文',
            'abbr': 'TW',
            'english_name': 'Traditional Chinese',
            'can_be_source': True,
            'can_be_target': True,
            'enabled': True
        },
        'BR': {
            'code': 'BR',
            'name': '巴西葡语',
            'abbr': 'BR',
            'english_name': 'Brazilian Portuguese',
            'can_be_source': False,
            'can_be_target': True,
            'enabled': True
        }
    }

    @classmethod
    def get_language_info(cls, code: str) -> Dict:
        """获取单个语言的完整信息"""
        return cls.LANGUAGES.get(code, {
            'code': code,
            'name': code,
            'abbr': code,
            'english_name': code,
            'can_be_source': False,
            'can_be_target': False,
            'enabled': False
        })

    @classmethod
    def get_available_source_languages(cls) -> List[Dict]:
        """获取所有可用的源语言"""
        return [
            lang for lang in cls.LANGUAGES.values()
            if lang['can_be_source'] and lang['enabled']
        ]

    @classmethod
    def get_available_target_languages(cls) -> List[Dict]:
        """获取所有可用的目标语言"""
        return [
            lang for lang in cls.LANGUAGES.values()
            if lang['can_be_target'] and lang['enabled']
        ]

    @classmethod
    def enrich_language_list(cls, language_codes: List[str]) -> List[Dict]:
        """
        丰富语言代码列表，添加完整的元数据

        Args:
            language_codes: 语言代码列表，如 ['CH', 'EN', 'TH']

        Returns:
            包含完整元数据的语言列表
        """
        return [cls.get_language_info(code) for code in language_codes]

    @classmethod
    def get_display_name(cls, code: str, format_type: str = 'full') -> str:
        """
        获取语言的显示名称

        Args:
            code: 语言代码
            format_type: 显示格式
                - 'full': "中文 (CN)"
                - 'name': "中文"
                - 'abbr': "CN"
                - 'english': "Chinese"
        """
        lang = cls.get_language_info(code)

        if format_type == 'full':
            return f"{lang['name']} ({lang['abbr']})"
        elif format_type == 'name':
            return lang['name']
        elif format_type == 'abbr':
            return lang['abbr']
        elif format_type == 'english':
            return lang['english_name']
        else:
            return lang['name']
