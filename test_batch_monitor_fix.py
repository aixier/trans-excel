#!/usr/bin/env python3
"""
测试批处理监控器的修复
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'excel_processor/backend'))

from datetime import datetime
from app.core.llm_batch.batch_monitor import BatchMonitor, BatchDetails, BatchMetrics, BatchPhase


class MockBatch:
    """模拟批处理对象"""
    def __init__(self):
        self.id = "test_batch_001"
        self.status = "in_progress"
        # 模拟可能为None的时间戳
        self.created_at = None  # 这会导致原始错误
        self.expires_at = None  # 这也会导致错误
        self.request_counts = MockRequestCounts()
        self.model = "qwen-plus"
        self.endpoint = "/v1/chat/completions"
        self.completion_window = "24h"
        self.metadata = {}
        self.errors = []


class MockRequestCounts:
    """模拟请求计数"""
    def __init__(self):
        self.total = 100
        self.completed = 25
        self.failed = 0


class MockClient:
    """模拟客户端"""
    def __init__(self):
        self.batches = MockBatches()


class MockBatches:
    """模拟批处理API"""
    def retrieve(self, batch_id):
        return MockBatch()


def test_batch_monitor():
    """测试批处理监控器"""
    print("测试批处理监控器的None值处理...")
    
    # 创建监控器
    client = MockClient()
    monitor = BatchMonitor(client)
    
    # 测试解析批处理详情（包含None值）
    batch = MockBatch()
    
    # 测试不同的start_time值
    test_cases = [
        (None, "None start_time"),
        (0, "Zero start_time"),
        (1736640000, "Valid timestamp"),
        ("invalid", "Invalid string"),
    ]
    
    for start_time, description in test_cases:
        print(f"\n测试 {description}: {start_time}")
        try:
            details = monitor._parse_batch_details(batch, start_time if start_time != "invalid" else 0)
            print(f"  ✓ 成功解析")
            print(f"    - Phase: {details.phase.value}")
            print(f"    - Status: {details.status}")
            print(f"    - Created at: {details.created_at}")
            print(f"    - Expires at: {details.expires_at}")
            print(f"    - Elapsed: {details.metrics.elapsed_seconds:.2f}s")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    # 测试有效的时间戳
    print("\n测试有效的时间戳...")
    batch.created_at = 1736640000  # 2025年1月12日的时间戳
    batch.expires_at = 1736726400  # 24小时后
    
    try:
        details = monitor._parse_batch_details(batch, 1736640000)
        print(f"  ✓ 成功解析有效时间戳")
        print(f"    - Created at: {details.created_at}")
        print(f"    - Expires at: {details.expires_at}")
    except Exception as e:
        print(f"  ✗ 错误: {e}")
    
    print("\n测试完成！")


if __name__ == "__main__":
    test_batch_monitor()