#!/usr/bin/env python3
"""
测试任务仓库的内存缓存和批量持久化功能
"""

import asyncio
import time
import uuid
from datetime import datetime

# 添加项目路径
import sys
sys.path.append('/mnt/d/work/trans_excel/translation_system/backend')

from database.task_repository import TaskRepository


async def test_task_repository():
    """测试任务仓库功能"""
    print("=" * 60)
    print(" 测试任务仓库 ".center(60))
    print("=" * 60)

    # 创建仓库实例（5秒批量写入）
    repo = TaskRepository(max_cache_size=100, flush_interval=5)

    # 测试1: 创建任务
    print("\n1. 测试创建任务...")
    tasks = []
    for i in range(5):
        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "file_name": f"test_{i}.xlsx",
            "total_tasks": 100,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "progress": 0
        }
        await repo.save_task(task_id, task_data, immediate=False)
        tasks.append(task_id)
        print(f"   创建任务 {i+1}: {task_id[:8]}...")

    # 测试2: 读取任务（缓存命中）
    print("\n2. 测试缓存命中...")
    for i, task_id in enumerate(tasks[:3]):
        task = await repo.get_task(task_id)
        if task:
            print(f"   任务 {i+1}: {task['file_name']} - 状态: {task['status']}")

    # 测试3: 更新进度（高频操作）
    print("\n3. 测试进度更新...")
    task_id = tasks[0]
    for progress in [10, 30, 50, 70, 90, 100]:
        await repo.update_task_progress(task_id, progress,
                                       completed=progress, failed=0)
        print(f"   进度更新: {progress}%")
        await asyncio.sleep(0.5)

    # 测试4: 状态更新（立即持久化）
    print("\n4. 测试状态更新...")
    task_id = tasks[1]
    await repo.update_task_status(task_id, "processing", immediate=False)
    print(f"   任务 {task_id[:8]}... 状态更新为: processing")

    await asyncio.sleep(1)
    await repo.update_task_status(task_id, "completed", immediate=True)
    print(f"   任务 {task_id[:8]}... 状态更新为: completed (立即持久化)")

    # 测试5: 列表查询
    print("\n5. 测试任务列表...")
    all_tasks = await repo.list_tasks(limit=10)
    print(f"   总任务数: {len(all_tasks)}")

    pending_tasks = await repo.list_tasks(status="pending", limit=10)
    print(f"   待处理任务: {len(pending_tasks)}")

    # 测试6: 统计信息
    print("\n6. 缓存统计信息:")
    stats = repo.get_stats()
    print(f"   缓存命中次数: {stats['cache_hits']}")
    print(f"   缓存未命中次数: {stats['cache_misses']}")
    print(f"   缓存大小: {stats['cache_size']}")
    print(f"   脏数据数量: {stats['dirty_count']}")
    print(f"   缓存命中率: {stats['cache_hit_rate']:.2%}")

    # 等待批量写入
    print("\n7. 等待批量写入（5秒后自动触发）...")
    print("   提示: 实际使用中会自动定时批量写入数据库")
    await asyncio.sleep(6)

    print("\n8. 批量写入后统计:")
    stats = repo.get_stats()
    print(f"   批量写入次数: {stats.get('batch_writes', 0)}")
    print(f"   数据库写入次数: {stats.get('db_writes', 0)}")
    print(f"   脏数据数量: {stats['dirty_count']}")

    # 关闭仓库
    print("\n9. 关闭仓库...")
    await repo.shutdown()

    print("\n✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_task_repository())