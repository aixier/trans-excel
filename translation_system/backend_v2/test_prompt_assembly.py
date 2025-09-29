#!/usr/bin/env python3
"""
演示prompt组装流程的测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.llm.prompt_template import PromptTemplate
from models.game_info import GameInfo
from services.context_extractor import ContextExtractor

def demo_prompt_assembly():
    """演示完整的prompt组装流程"""

    print("=" * 80)
    print("🚀 Prompt组装流程演示")
    print("=" * 80)

    # 1. 初始化组件
    template = PromptTemplate()

    # 2. 模拟游戏信息
    game_info_dict = {
        'game_type': '角色扮演游戏 (RPG)',
        'world_view': '中世纪奇幻世界',
        'game_style': '严肃剧情向',
        'target_region': '巴西'
    }

    # 3. 模拟任务数据
    sample_tasks = [
        {
            'task_id': 'TASK_0001',
            'source_text': 'Welcome to the magical world!',
            'source_lang': 'EN',
            'target_lang': 'PT',
            'source_context': '[Column] UI_Text | [Type] Short text/UI element | [Sheet Type] UI/Interface text',
            'task_type': 'normal'
        },
        {
            'task_id': 'TASK_0002',
            'source_text': 'Your adventure begins now. Choose your destiny wisely.',
            'source_lang': 'EN',
            'target_lang': 'PT',
            'source_context': '[Column] Dialog_Text | [Type] Description text | [Sheet Type] Dialog/Conversation',
            'task_type': 'yellow'
        },
        {
            'task_id': 'TASK_0003',
            'source_text': 'Press {BUTTON_A} to continue',
            'source_lang': 'EN',
            'target_lang': 'TH',
            'source_context': '[Column] Tutorial_Text | [Type] Short text/UI element | [Format] Contains variables',
            'task_type': 'blue'
        }
    ]

    print("\n1️⃣ 单个任务Prompt组装演示")
    print("-" * 60)

    for i, task in enumerate(sample_tasks, 1):
        print(f"\n📝 任务 {i}: {task['task_id']} ({task['task_type']} 类型)")
        print(f"源文本: {task['source_text']}")
        print(f"上下文: {task['source_context']}")

        # 组装单个任务的prompt
        single_prompt = template.build_translation_prompt(
            source_text=task['source_text'],
            source_lang=task['source_lang'],
            target_lang=task['target_lang'],
            context=task['source_context'],
            game_info=game_info_dict
        )

        print(f"\n🎯 生成的Prompt:")
        print("─" * 50)
        print(single_prompt)
        print("─" * 50)

        if i == 1:  # 只展示第一个完整示例，其他简化
            break

    print("\n\n2️⃣ 批量任务Prompt组装演示")
    print("-" * 60)

    # 按目标语言分组进行批量处理
    pt_tasks = [task for task in sample_tasks if task['target_lang'] == 'PT']
    th_tasks = [task for task in sample_tasks if task['target_lang'] == 'TH']

    if pt_tasks:
        print(f"\n📦 葡萄牙语批次 ({len(pt_tasks)} 个任务)")
        pt_texts = [task['source_text'] for task in pt_tasks]

        batch_prompt = template.build_batch_prompt(
            texts=pt_texts,
            source_lang='EN',
            target_lang='PT',
            context='UI和对话文本混合批次',
            game_info=game_info_dict
        )

        print(f"\n🎯 批量Prompt:")
        print("─" * 50)
        print(batch_prompt)
        print("─" * 50)

    if th_tasks:
        print(f"\n📦 泰语批次 ({len(th_tasks)} 个任务)")
        th_texts = [task['source_text'] for task in th_tasks]

        batch_prompt = template.build_batch_prompt(
            texts=th_texts,
            source_lang='EN',
            target_lang='TH',
            context='教程文本批次',
            game_info=game_info_dict
        )

        print(f"\n🎯 批量Prompt:")
        print("─" * 50)
        print(batch_prompt)
        print("─" * 50)

    print("\n\n3️⃣ 简化版Prompt组装演示 (无游戏信息)")
    print("-" * 60)

    simple_prompt = template.build_translation_prompt(
        source_text="Settings",
        source_lang='EN',
        target_lang='PT',
        context="",
        game_info=None
    )

    print(f"\n🎯 简化版Prompt:")
    print("─" * 50)
    print(simple_prompt)
    print("─" * 50)

    print("\n\n4️⃣ 任务类型区分示例")
    print("-" * 60)

    task_types = {
        'normal': '普通翻译任务',
        'yellow': '黄色重译任务 - 需要重新翻译',
        'blue': '蓝色缩短任务 - 需要缩短长度'
    }

    for task_type, description in task_types.items():
        task = next((t for t in sample_tasks if t['task_type'] == task_type), sample_tasks[0])
        print(f"\n🏷️ {description}")
        print(f"示例文本: {task['source_text']}")
        print(f"上下文标记: {task['task_type']}")

    print("\n\n5️⃣ Prompt组装流程总结")
    print("-" * 60)

    flow_summary = """
    📋 Prompt组装流程:

    1. 输入收集:
       ├─ 源文本 (source_text)
       ├─ 源语言/目标语言 (source_lang/target_lang)
       ├─ 上下文信息 (context)
       ├─ 游戏信息 (game_info)
       └─ 任务类型 (task_type)

    2. 模板选择:
       ├─ 有游戏信息 → GAME_TRANSLATION_PROMPT
       └─ 无游戏信息 → SIMPLE_TRANSLATION_PROMPT

    3. 参数映射:
       ├─ 语言代码转换 (EN→英文, PT→葡萄牙语)
       ├─ 地区映射 (PT→巴西)
       └─ 上下文格式化

    4. 模板填充:
       ├─ 占位符替换 ({source_lang_name}, {target_lang_name})
       ├─ 动态内容插入 (source_text, context, game_info)
       └─ 格式化输出

    5. 批量处理:
       ├─ 多文本编号列表
       ├─ 统一上下文
       └─ 结构化输出要求
    """

    print(flow_summary)

    print("\n✅ Prompt组装演示完成!")
    print("=" * 80)

if __name__ == "__main__":
    demo_prompt_assembly()