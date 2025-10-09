"""测试自定义 max_chars_per_batch 参数"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.batch_allocator import BatchAllocator


def test_custom_batch_size():
    """测试使用自定义批次大小"""

    print("=" * 60)
    print("测试自定义 max_chars_per_batch 参数")
    print("=" * 60)

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

    # 测试1: 使用默认值 (2000)
    print(f"\n{'='*60}")
    print("测试1: 使用默认配置值 (2000)")
    print(f"{'='*60}")

    allocator1 = BatchAllocator()  # 不传参数，使用配置默认值
    allocated1 = allocator1.allocate_batches([t.copy() for t in test_tasks])

    batches1 = {}
    for task in allocated1:
        batch_id = task['batch_id']
        if batch_id not in batches1:
            batches1[batch_id] = []
        batches1[batch_id].append(task)

    print(f"批次数: {len(batches1)}")
    print(f"max_chars_per_batch: {allocator1.max_chars_per_batch}")

    # 测试2: 使用自定义值 1200
    print(f"\n{'='*60}")
    print("测试2: 使用自定义值 (1200)")
    print(f"{'='*60}")

    allocator2 = BatchAllocator(max_chars_per_batch=1200)
    allocated2 = allocator2.allocate_batches([t.copy() for t in test_tasks])

    batches2 = {}
    for task in allocated2:
        batch_id = task['batch_id']
        if batch_id not in batches2:
            batches2[batch_id] = []
        batches2[batch_id].append(task)

    print(f"批次数: {len(batches2)}")
    print(f"max_chars_per_batch: {allocator2.max_chars_per_batch}")

    for batch_id, tasks in sorted(batches2.items()):
        total_chars = sum(task.get('char_count', 0) for task in tasks)
        print(f"  {batch_id}: {len(tasks)} 任务, {total_chars} 字符")
        if total_chars > 1200:
            print(f"    ⚠️ 超过限制!")
        else:
            print(f"    ✓ 符合限制")

    # 测试3: 使用自定义值 1000
    print(f"\n{'='*60}")
    print("测试3: 使用自定义值 (1000)")
    print(f"{'='*60}")

    allocator3 = BatchAllocator(max_chars_per_batch=1000)
    allocated3 = allocator3.allocate_batches([t.copy() for t in test_tasks])

    batches3 = {}
    for task in allocated3:
        batch_id = task['batch_id']
        if batch_id not in batches3:
            batches3[batch_id] = []
        batches3[batch_id].append(task)

    print(f"批次数: {len(batches3)}")
    print(f"max_chars_per_batch: {allocator3.max_chars_per_batch}")

    for batch_id, tasks in sorted(batches3.items()):
        total_chars = sum(task.get('char_count', 0) for task in tasks)
        print(f"  {batch_id}: {len(tasks)} 任务, {total_chars} 字符")
        if total_chars > 1000:
            print(f"    ⚠️ 超过限制!")
        else:
            print(f"    ✓ 符合限制")

    # 验证结果
    print(f"\n{'='*60}")
    print("验证结果:")
    print(f"{'='*60}")

    print(f"配置默认值 (2000): {len(batches1)} 批次")
    print(f"自定义值 (1200): {len(batches2)} 批次")
    print(f"自定义值 (1000): {len(batches3)} 批次")

    # 批次数应该随着限制变小而增加
    if len(batches1) < len(batches2) < len(batches3):
        print("\n✅ 测试通过！批次数随限制减小而增加")
        return True
    else:
        print("\n❌ 测试失败！批次数未按预期变化")
        return False


if __name__ == '__main__':
    result = test_custom_batch_size()
    sys.exit(0 if result else 1)
