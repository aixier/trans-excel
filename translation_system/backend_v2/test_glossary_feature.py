"""测试术语功能完整流程"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.glossary_manager import glossary_manager
from services.llm.prompt_template import PromptTemplate


def test_glossary_loading():
    """测试术语表加载"""
    print("=" * 80)
    print("测试1: 术语表加载")
    print("=" * 80)

    # 加载默认术语表
    glossary = glossary_manager.load_glossary('default')

    if glossary:
        print(f"✅ 加载成功")
        print(f"  ID: {glossary['id']}")
        print(f"  名称: {glossary['name']}")
        print(f"  术语数量: {len(glossary['terms'])}")
        print(f"  支持语言: {glossary['languages']}")

        # 显示前5个术语
        print(f"\n  前5个术语:")
        for term in glossary['terms'][:5]:
            print(f"    - {term['source']}: {term['translations']}")

        return True
    else:
        print("❌ 加载失败")
        return False


def test_term_matching():
    """测试术语匹配"""
    print("\n" + "=" * 80)
    print("测试2: 术语智能匹配")
    print("=" * 80)

    glossary = glossary_manager.load_glossary('default')
    if not glossary:
        print("❌ 术语表未加载")
        return False

    # 测试文本
    test_cases = [
        ("提升攻击力100点", "PT"),
        ("生命值不足，请补充", "TH"),
        ("获得金币和钻石", "VN"),
        ("这是一段普通文本", "EN")  # 不包含术语
    ]

    for text, target_lang in test_cases:
        matched = glossary_manager.match_terms_in_text(text, glossary, target_lang)

        print(f"\n  文本: '{text}'")
        print(f"  目标语言: {target_lang}")

        if matched:
            print(f"  ✅ 匹配到 {len(matched)} 个术语:")
            for term in matched:
                print(f"    - {term['source']} → {term['target']}")
        else:
            print(f"  ℹ️  未匹配到术语")

    return True


def test_batch_matching():
    """测试批量文本术语匹配"""
    print("\n" + "=" * 80)
    print("测试3: 批量文本术语匹配（去重）")
    print("=" * 80)

    glossary = glossary_manager.load_glossary('default')
    if not glossary:
        print("❌ 术语表未加载")
        return False

    # 批量文本（有重复术语）
    texts = [
        "攻击力+100",
        "防御力+50",
        "攻击力和防御力各提升20"  # 重复术语
    ]

    matched = glossary_manager.match_terms_in_batch(texts, glossary, 'PT')

    print(f"\n  批量文本:")
    for text in texts:
        print(f"    - {text}")

    print(f"\n  ✅ 合并匹配到 {len(matched)} 个术语（已去重）:")
    for term in matched:
        print(f"    - {term['source']} → {term['target']}")

    # 验证去重
    if len(matched) == 2:  # 应该是2个（攻击力、防御力），不是3个
        print(f"\n  ✅ 去重正确")
        return True
    else:
        print(f"\n  ❌ 去重失败，期望2个，实际{len(matched)}个")
        return False


def test_prompt_injection():
    """测试Prompt注入"""
    print("\n" + "=" * 80)
    print("测试4: Prompt术语注入")
    print("=" * 80)

    prompt_template = PromptTemplate()

    # 测试用例
    source_text = "提升攻击力100点，恢复生命值50%"
    glossary_config = {
        'enabled': True,
        'id': 'default'
    }

    # 构建Prompt
    prompt = prompt_template.build_translation_prompt(
        source_text=source_text,
        source_lang='CH',
        target_lang='PT',
        context='',
        game_info={'game_type': 'MMORPG'},
        glossary_config=glossary_config
    )

    print(f"\n  源文本: {source_text}")
    print(f"\n  生成的Prompt:")
    print("  " + "-" * 76)
    print(prompt)
    print("  " + "-" * 76)

    # 验证术语是否注入
    if '相关游戏术语' in prompt:
        print(f"\n  ✅ 术语已注入到Prompt")
        if '攻击力 → Ataque' in prompt and '生命值 → Vida' in prompt:
            print(f"  ✅ 术语正确: 攻击力→Ataque, 生命值→Vida")
            return True
        else:
            print(f"  ❌ 术语内容不正确")
            return False
    else:
        print(f"\n  ❌ 术语未注入")
        return False


if __name__ == '__main__':
    print("\n🧪 游戏术语功能完整测试\n")

    results = []
    results.append(("术语表加载", test_glossary_loading()))
    results.append(("术语匹配", test_term_matching()))
    results.append(("批量去重", test_batch_matching()))
    results.append(("Prompt注入", test_prompt_injection()))

    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")

    all_passed = all(r[1] for r in results)
    print(f"\n{'✅ 所有测试通过！' if all_passed else '❌ 部分测试失败'}")

    sys.exit(0 if all_passed else 1)
