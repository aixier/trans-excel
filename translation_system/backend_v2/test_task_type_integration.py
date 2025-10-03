#!/usr/bin/env python3
"""
测试任务类型集成的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.llm.base_provider import TranslationRequest
from services.llm.prompt_template import PromptTemplate

def test_translation_request_with_task_type():
    """测试TranslationRequest是否正确支持task_type"""

    print("🧪 测试TranslationRequest任务类型支持")
    print("=" * 60)

    # 测试不同类型的请求
    test_cases = [
        {
            'name': '普通翻译任务',
            'task_type': 'normal',
            'source_text': 'Welcome to the game!'
        },
        {
            'name': '黄色重译任务',
            'task_type': 'yellow',
            'source_text': 'Your adventure begins now.'
        },
        {
            'name': '蓝色缩短任务',
            'task_type': 'blue',
            'source_text': 'Press ENTER to continue the epic journey.'
        }
    ]

    template = PromptTemplate()

    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print("-" * 40)

        # 创建TranslationRequest
        request = TranslationRequest(
            source_text=case['source_text'],
            source_lang='EN',
            target_lang='PT',
            task_type=case['task_type'],
            context='[Type] Game UI text',
            game_info={'game_type': 'RPG', 'world_view': 'Fantasy'}
        )

        print(f"✓ TranslationRequest创建成功")
        print(f"  - 任务类型: {request.task_type}")
        print(f"  - 源文本: {request.source_text}")

        # 测试prompt生成
        prompt = template.build_task_specific_prompt(
            source_text=request.source_text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            task_type=request.task_type,
            context=request.context,
            game_info=request.game_info
        )

        print(f"✓ 任务特殊Prompt生成成功")

        # 检查是否包含特殊指令
        if case['task_type'] == 'yellow' and '重译任务' in prompt:
            print(f"✓ 黄色重译特殊指令已添加")
        elif case['task_type'] == 'blue' and '缩短' in prompt:
            print(f"✓ 蓝色缩短特殊指令已添加")
        elif case['task_type'] == 'normal':
            print(f"✓ 普通任务使用标准模板")

    print(f"\n{'=' * 60}")
    print("🎉 任务类型集成测试完成！")

def test_batch_task_type_determination():
    """测试批量任务类型决策逻辑"""

    print("\n🧪 测试批量任务类型决策")
    print("=" * 60)

    from services.llm.batch_translator import BatchTranslator

    # 直接创建BatchTranslator实例，不依赖Provider
    batch_translator = BatchTranslator(provider=None)

    test_batches = [
        {
            'name': '全部普通任务',
            'tasks': [
                {'task_type': 'normal', 'source_text': 'Text 1'},
                {'task_type': 'normal', 'source_text': 'Text 2'}
            ],
            'expected': 'normal'
        },
        {
            'name': '包含黄色重译任务',
            'tasks': [
                {'task_type': 'normal', 'source_text': 'Text 1'},
                {'task_type': 'yellow', 'source_text': 'Text 2'}
            ],
            'expected': 'yellow'
        },
        {
            'name': '包含蓝色缩短任务',
            'tasks': [
                {'task_type': 'normal', 'source_text': 'Text 1'},
                {'task_type': 'yellow', 'source_text': 'Text 2'},
                {'task_type': 'blue', 'source_text': 'Text 3'}
            ],
            'expected': 'blue'
        }
    ]

    for i, batch in enumerate(test_batches, 1):
        print(f"\n{i}. {batch['name']}")
        print("-" * 40)

        result = batch_translator._determine_batch_task_type(batch['tasks'])

        print(f"  输入任务类型: {[t['task_type'] for t in batch['tasks']]}")
        print(f"  预期结果: {batch['expected']}")
        print(f"  实际结果: {result}")

        if result == batch['expected']:
            print(f"  ✓ 测试通过")
        else:
            print(f"  ✗ 测试失败")

    print(f"\n{'=' * 60}")
    print("🎉 批量任务类型决策测试完成！")

if __name__ == "__main__":
    test_translation_request_with_task_type()
    test_batch_task_type_determination()