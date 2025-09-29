#!/usr/bin/env python3
"""
测试源语言智能选择功能
验证修改后的 localization_engine.py 是否正确工作
"""

import sys
import os

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from translation_core.localization_engine import LocalizationEngine

def test_smart_source_language():
    """测试智能源语言选择功能"""
    engine = LocalizationEngine()

    print("=== 测试智能源语言选择功能 ===")

    # 测试亚洲语言目标
    asian_targets = ['vn', 'th', 'ja', 'ko']
    for lang in asian_targets:
        source = engine._get_smart_source_language(lang)
        print(f"目标语言: {lang} -> 源语言: {source} (期望: ch)")
        assert source == 'ch', f"亚洲语言 {lang} 应该选择中文作为源语言"

    # 测试其他语言目标
    other_targets = ['en', 'pt', 'es', 'ar', 'ru']
    for lang in other_targets:
        source = engine._get_smart_source_language(lang)
        print(f"目标语言: {lang} -> 源语言: {source} (期望: en)")
        assert source == 'en', f"非亚洲语言 {lang} 应该选择英文作为源语言"

    print("✅ 智能源语言选择功能测试通过!")

def test_language_name_mapping():
    """测试语言名称映射功能"""
    engine = LocalizationEngine()

    print("\n=== 测试语言名称映射功能 ===")

    # 测试源语言映射
    test_cases = [
        ('ch', 'Chinese (中文)'),
        ('cn', 'Chinese (中文)'),
        ('en', 'English (英语)'),
        ('vn', 'Vietnamese (越南语)'),
        ('th', 'Thai (泰语)')
    ]

    for lang_code, expected_name in test_cases:
        actual_name = engine._get_language_name(lang_code)
        print(f"语言代码: {lang_code} -> 名称: {actual_name}")
        assert actual_name == expected_name, f"语言 {lang_code} 的名称映射错误"

    print("✅ 语言名称映射功能测试通过!")

def test_create_prompt_with_dynamic_source():
    """测试动态源语言的提示词创建"""
    engine = LocalizationEngine()

    print("\n=== 测试动态源语言提示词创建 ===")

    # 测试单个翻译提示词
    prompt1 = engine.create_localized_prompt(
        source_text="测试文本",
        target_language="vn",
        region_code="as",
        source_language="ch"  # 显式指定源语言
    )

    assert "源语言：Chinese (中文)" in prompt1
    assert "目标语言：Vietnamese (越南语)" in prompt1
    print("✅ 单个翻译提示词包含正确的源语言")

    # 测试自动选择源语言
    prompt2 = engine.create_localized_prompt(
        source_text="测试文本",
        target_language="vn",
        region_code="as"
        # 不指定 source_language，应该自动选择 'ch'
    )

    assert "源语言：Chinese (中文)" in prompt2
    print("✅ 自动选择源语言功能正常")

    # 测试批量翻译提示词
    prompt3 = engine.create_batch_prompt(
        texts=["文本1", "文本2"],
        target_languages=["en", "pt"],
        region_code="na",
        source_language="ch"  # 显式指定源语言
    )

    assert "源语言：Chinese (中文)" in prompt3
    assert "目标语言：English (英语), Portuguese (葡萄牙语)" in prompt3
    print("✅ 批量翻译提示词包含正确的源语言")

    # 测试自动选择源语言（英文目标）
    prompt4 = engine.create_batch_prompt(
        texts=["文本1", "文本2"],
        target_languages=["en"],
        region_code="na"
        # 不指定 source_language，应该自动选择 'en'
    )

    assert "源语言：English (英语)" in prompt4
    print("✅ 英文目标自动选择英文源语言功能正常")

def main():
    """运行所有测试"""
    try:
        test_smart_source_language()
        test_language_name_mapping()
        test_create_prompt_with_dynamic_source()

        print("\n🎉 所有测试通过! 源语言智能选择功能正常工作!")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()