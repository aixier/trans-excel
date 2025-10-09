"""测试批次统计信息"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.batch_allocator import BatchAllocator


def test_batch_statistics():
    """测试批次统计功能"""

    print("=" * 60)
    print("测试批次统计信息")
    print("=" * 60)

    # 创建测试任务
    test_tasks = [
        # 英语任务
        {'task_id': 'T1', 'source_text': 'A' * 100, 'source_context': '', 'target_lang': 'EN', 'task_type': 'normal'},
        {'task_id': 'T2', 'source_text': 'B' * 150, 'source_context': '', 'target_lang': 'EN', 'task_type': 'normal'},
        {'task_id': 'T3', 'source_text': 'C' * 200, 'source_context': '', 'target_lang': 'EN', 'task_type': 'yellow'},
        # 葡语任务
        {'task_id': 'T4', 'source_text': 'D' * 120, 'source_context': '', 'target_lang': 'PT', 'task_type': 'normal'},
        {'task_id': 'T5', 'source_text': 'E' * 80, 'source_context': '', 'target_lang': 'PT', 'task_type': 'blue'},
    ]

    allocator = BatchAllocator(max_chars_per_batch=300)
    allocated = allocator.allocate_batches(test_tasks)

    # 计算统计信息
    stats = allocator.calculate_batch_statistics(allocated)

    print(f"\n总批次数: {stats['total_batches']}")
    print(f"平均每批次字符数: {stats['avg_chars_per_batch']:.1f}")
    print(f"最大批次字符数: {stats['max_chars_in_batch']}")
    print(f"最小批次字符数: {stats['min_chars_in_batch']}")

    print(f"\n批次分布:")
    for lang, info in stats['batch_distribution'].items():
        print(f"  {lang}:")
        print(f"    批次数: {info['batches']}")
        print(f"    任务数: {info['tasks']}")
        print(f"    字符数: {info['chars']}")

    print(f"\n所有批次详情:")
    for batch_id, batch_info in stats['batches'].items():
        print(f"  {batch_id}:")
        print(f"    任务数: {len(batch_info['tasks'])}")
        print(f"    字符数: {batch_info['total_chars']}")
        print(f"    语言: {batch_info['target_lang']}")

    # 验证数据结构
    print(f"\n{'='*60}")
    print("验证结果:")
    print(f"{'='*60}")

    assert 'batch_distribution' in stats
    assert 'batches' in stats['batch_distribution'].get('EN', {})
    assert 'tasks' in stats['batch_distribution'].get('EN', {})
    assert 'chars' in stats['batch_distribution'].get('EN', {})

    print("✅ 批次统计数据结构正确")
    print(f"✅ 包含详细信息: batches, tasks, chars")

    return stats


if __name__ == '__main__':
    try:
        stats = test_batch_statistics()
        print(f"\n✅ 测试通过")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
