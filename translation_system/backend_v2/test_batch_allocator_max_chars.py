"""测试 max_chars_per_batch 是否真正起作用"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.batch_allocator import BatchAllocator
from utils.config_manager import config_manager


def test_max_chars_per_batch():
    """测试批次分配是否受 max_chars_per_batch 限制"""

    # 获取当前配置
    max_chars = config_manager.max_chars_per_batch
    print(f"当前配置的 max_chars_per_batch: {max_chars}")

    # 创建测试任务 - 每个任务约500字符
    test_tasks = []
    for i in range(10):
        task = {
            'task_id': f'TASK_{i:04d}',
            'source_text': 'A' * 500,  # 500字符
            'source_context': 'B' * 100,  # 100字符
            'target_lang': 'EN',
            'task_type': 'normal'
        }
        test_tasks.append(task)

    print(f"\n创建了 {len(test_tasks)} 个测试任务，每个任务约 600 字符")
    print(f"总字符数: {len(test_tasks) * 600} 字符")
    print(f"预期批次数: {(len(test_tasks) * 600) // max_chars + 1}")

    # 使用 BatchAllocator 分配批次
    allocator = BatchAllocator()
    allocated_tasks = allocator.allocate_batches(test_tasks)

    # 统计批次
    batches = {}
    for task in allocated_tasks:
        batch_id = task['batch_id']
        if batch_id not in batches:
            batches[batch_id] = []
        batches[batch_id].append(task)

    print(f"\n实际生成批次数: {len(batches)}")
    print("\n批次详情:")
    for batch_id, tasks in sorted(batches.items()):
        total_chars = sum(task.get('char_count', 0) for task in tasks)
        print(f"  {batch_id}: {len(tasks)} 个任务, 总字符数: {total_chars}")

        # 检查是否超过限制
        if total_chars > max_chars:
            print(f"    ⚠️  警告: 超过 max_chars_per_batch ({max_chars})")
        else:
            print(f"    ✓ 符合限制 (< {max_chars})")

    # 获取统计信息
    stats = allocator.calculate_batch_statistics(allocated_tasks)
    print(f"\n统计信息:")
    print(f"  总批次数: {stats['total_batches']}")
    print(f"  平均每批次字符数: {stats['avg_chars_per_batch']:.0f}")
    print(f"  最大批次字符数: {stats['max_chars_in_batch']}")
    print(f"  最小批次字符数: {stats['min_chars_in_batch']}")

    # 验证是否真正起作用
    max_batch_chars = stats['max_chars_in_batch']
    if max_batch_chars <= max_chars:
        print(f"\n✅ max_chars_per_batch 参数起作用！所有批次都 <= {max_chars} 字符")
        return True
    else:
        print(f"\n❌ max_chars_per_batch 参数未起作用！最大批次 {max_batch_chars} > {max_chars}")
        return False


def test_split_large_task():
    """测试超大任务是否会被拆分"""

    max_chars = config_manager.max_chars_per_batch
    print(f"\n{'='*60}")
    print(f"测试超大任务拆分 (max_chars_per_batch: {max_chars})")
    print(f"{'='*60}")

    # 创建一个超大任务（超过 max_chars_per_batch）
    large_text = 'X' * (max_chars + 5000)  # 超过限制
    large_task = {
        'task_id': 'TASK_LARGE',
        'source_text': large_text,
        'source_context': '',
        'target_lang': 'EN',
        'task_type': 'normal'
    }

    print(f"创建超大任务: {len(large_text)} 字符 (超过限制 {len(large_text) - max_chars} 字符)")

    allocator = BatchAllocator()
    split_tasks = allocator.split_large_task(large_task)

    print(f"\n拆分结果: {len(split_tasks)} 个子任务")
    for i, task in enumerate(split_tasks):
        text_len = len(task['source_text'])
        print(f"  子任务 {i+1}: {task['task_id']}, {text_len} 字符")

    if len(split_tasks) > 1:
        print(f"\n✅ split_large_task 功能正常工作！")
        return True
    else:
        print(f"\n❌ split_large_task 未拆分超大任务！")
        return False


if __name__ == '__main__':
    result1 = test_max_chars_per_batch()
    result2 = test_split_large_task()

    print(f"\n{'='*60}")
    print(f"测试总结:")
    print(f"  批次分配: {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"  超大任务拆分: {'✅ 通过' if result2 else '❌ 失败'}")
    print(f"{'='*60}")
