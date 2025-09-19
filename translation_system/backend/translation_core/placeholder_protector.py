"""
占位符保护器
基于test_concurrent_batch.py扩展的游戏占位符保护功能
"""
import re
from typing import Dict, List, Tuple


class PlaceholderProtector:
    """占位符保护器 - 扩展Demo中的JSON格式保护"""

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

    def batch_protect_placeholders(self, texts: List[str]) -> Tuple[List[str], List[Dict[str, str]]]:
        """批量保护占位符 - 用于批处理翻译"""
        protected_texts = []
        placeholder_maps = []

        for text in texts:
            protected_text, placeholder_map = self.protect_placeholders(text)
            protected_texts.append(protected_text)
            placeholder_maps.append(placeholder_map)

        return protected_texts, placeholder_maps

    def batch_restore_placeholders(self, texts: List[str], placeholder_maps: List[Dict[str, str]]) -> List[str]:
        """批量恢复占位符"""
        restored_texts = []

        for text, placeholder_map in zip(texts, placeholder_maps):
            restored_text = self.restore_placeholders(text, placeholder_map)
            restored_texts.append(restored_text)

        return restored_texts