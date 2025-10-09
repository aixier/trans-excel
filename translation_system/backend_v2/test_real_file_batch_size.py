"""测试真实文件的批次拆分"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models.excel_dataframe import ExcelDataFrame
from services.task_splitter import TaskSplitter
from services.batch_allocator import BatchAllocator
from services.excel_loader import ExcelLoader


def test_real_file():
    """测试真实 Excel 文件的拆分"""

    excel_path = "/mnt/d/work/trans_excel/sfdaf.xlsx"

    print("=" * 60)
    print("测试真实文件的批次拆分")
    print("=" * 60)
    print(f"文件: {excel_path}\n")

    # 加载 Excel
    excel_df = ExcelLoader.load_excel(excel_path)
    print(f"✓ Excel 加载成功")
    print(f"  Sheet 数量: {len(excel_df.get_sheet_names())}")
    print(f"  Sheet 名称: {excel_df.get_sheet_names()}")

    # 测试1: max_chars_per_batch = 2000 (默认)
    print(f"\n{'='*60}")
    print("测试1: max_chars_per_batch = 2000")
    print(f"{'='*60}")

    splitter1 = TaskSplitter(
        excel_df,
        game_info=None,
        extract_context=False,  # 关闭上下文提取以加快速度
        max_chars_per_batch=2000
    )

    task_manager1 = splitter1.split_tasks(
        source_lang=None,  # 自动检测
        target_langs=['EN']
    )

    tasks1 = task_manager1.df.to_dict('records') if task_manager1.df is not None else []

    # 统计批次
    batches1 = {}
    total_chars1 = 0
    for task in tasks1:
        batch_id = task.get('batch_id', 'UNKNOWN')
        if batch_id not in batches1:
            batches1[batch_id] = []
        batches1[batch_id].append(task)
        total_chars1 += task.get('char_count', 0)

    print(f"总任务数: {len(tasks1)}")
    print(f"总批次数: {len(batches1)}")
    print(f"总字符数: {total_chars1}")
    print(f"平均每任务字符数: {total_chars1 / len(tasks1):.1f}" if tasks1 else "N/A")

    print("\n批次详情:")
    for batch_id in sorted(batches1.keys())[:5]:  # 只显示前5个批次
        batch_tasks = batches1[batch_id]
        batch_chars = sum(t.get('char_count', 0) for t in batch_tasks)
        print(f"  {batch_id}: {len(batch_tasks)} 任务, {batch_chars} 字符")
    if len(batches1) > 5:
        print(f"  ... (还有 {len(batches1) - 5} 个批次)")

    # 测试2: max_chars_per_batch = 1000
    print(f"\n{'='*60}")
    print("测试2: max_chars_per_batch = 1000")
    print(f"{'='*60}")

    splitter2 = TaskSplitter(
        excel_df,
        game_info=None,
        extract_context=False,
        max_chars_per_batch=1000
    )

    task_manager2 = splitter2.split_tasks(
        source_lang=None,
        target_langs=['EN']
    )

    tasks2 = task_manager2.df.to_dict('records') if task_manager2.df is not None else []

    # 统计批次
    batches2 = {}
    total_chars2 = 0
    for task in tasks2:
        batch_id = task.get('batch_id', 'UNKNOWN')
        if batch_id not in batches2:
            batches2[batch_id] = []
        batches2[batch_id].append(task)
        total_chars2 += task.get('char_count', 0)

    print(f"总任务数: {len(tasks2)}")
    print(f"总批次数: {len(batches2)}")
    print(f"总字符数: {total_chars2}")
    print(f"平均每任务字符数: {total_chars2 / len(tasks2):.1f}" if tasks2 else "N/A")

    print("\n批次详情:")
    for batch_id in sorted(batches2.keys())[:5]:
        batch_tasks = batches2[batch_id]
        batch_chars = sum(t.get('char_count', 0) for t in batch_tasks)
        print(f"  {batch_id}: {len(batch_tasks)} 任务, {batch_chars} 字符")
    if len(batches2) > 5:
        print(f"  ... (还有 {len(batches2) - 5} 个批次)")

    # 对比结果
    print(f"\n{'='*60}")
    print("对比结果:")
    print(f"{'='*60}")

    print(f"\n参数设置:")
    print(f"  测试1: max_chars_per_batch = 2000")
    print(f"  测试2: max_chars_per_batch = 1000")

    print(f"\n任务数量 (应该相同):")
    print(f"  测试1: {len(tasks1)} 任务")
    print(f"  测试2: {len(tasks2)} 任务")
    print(f"  {'✓ 任务数量相同' if len(tasks1) == len(tasks2) else '✗ 任务数量不同 (异常!)'}")

    print(f"\n批次数量 (应该不同):")
    print(f"  测试1: {len(batches1)} 批次 (2000字符/批次)")
    print(f"  测试2: {len(batches2)} 批次 (1000字符/批次)")

    if len(batches2) > len(batches1):
        print(f"  ✓ 批次数量随限制减小而增加 ({len(batches1)} → {len(batches2)})")
        print(f"  增加了 {len(batches2) - len(batches1)} 个批次")
    elif len(batches2) == len(batches1):
        print(f"  ⚠️  批次数量未变化")
        print(f"  可能原因: 每个任务字符数较少，单个任务即可独立成批次")
    else:
        print(f"  ✗ 批次数量异常减少")

    print(f"\n{'='*60}")
    print("结论:")
    print(f"{'='*60}")
    print(f"• max_chars_per_batch 参数不影响任务数量")
    print(f"• 任务数量由 Excel 中需要翻译的单元格数量决定")
    print(f"• max_chars_per_batch 仅影响批次数量（如何分组）")

    return {
        'tasks1': len(tasks1),
        'tasks2': len(tasks2),
        'batches1': len(batches1),
        'batches2': len(batches2)
    }


if __name__ == '__main__':
    try:
        result = test_real_file()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
