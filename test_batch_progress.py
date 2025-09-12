#!/usr/bin/env python3
"""
测试批处理进度更新
"""

import asyncio
import time
import json
from datetime import datetime


class MockBatchProcessor:
    """模拟批处理器"""
    
    async def translate_batch(self, texts, target_languages, batch_size=10, progress_callback=None):
        """模拟批处理翻译"""
        total = len(texts)
        
        for i in range(0, total, batch_size):
            batch_end = min(i + batch_size, total)
            progress = (batch_end / total) * 100
            
            if progress_callback:
                await progress_callback({
                    'batch_id': 'test_batch_001',
                    'status': 'processing',
                    'progress': progress,
                    'completed': batch_end,
                    'total': total,
                    'failed': 0,
                    'elapsed': time.time(),
                    'message': f'处理中: {batch_end}/{total} ({progress:.1f}%)'
                })
            
            # 模拟处理延迟
            await asyncio.sleep(0.5)
        
        # 返回模拟结果
        return {
            lang: ['translated_' + str(i) for i in range(len(texts))]
            for lang in target_languages
        }


class TaskSimulator:
    """任务模拟器"""
    
    def __init__(self):
        self.task_id = "test_task_001"
        self.progress = 0.0
        self.current_step = ""
        self.status = "running"
        
    async def execute_batch_api(self):
        """模拟执行批处理API"""
        print(f"\n{'='*60}")
        print(f"开始模拟批处理任务: {self.task_id}")
        print(f"{'='*60}\n")
        
        # 阶段1: 准备
        await self.update_progress(1.0, "准备批处理任务")
        await asyncio.sleep(1)
        
        # 阶段2: 读取文件
        await self.update_progress(5.0, "读取Excel文件")
        await asyncio.sleep(1)
        
        # 阶段3: 提取文本
        await self.update_progress(10.0, "提取待翻译文本")
        texts = ['text_' + str(i) for i in range(100)]  # 模拟100条文本
        print(f"提取了 {len(texts)} 条文本")
        await asyncio.sleep(1)
        
        # 阶段4: 创建批处理
        await self.update_progress(15.0, "创建批处理任务")
        target_langs = ['en', 'pt', 'es']
        print(f"目标语言: {target_langs}")
        await asyncio.sleep(1)
        
        # 阶段5: 执行批处理（带监控）
        processor = MockBatchProcessor()
        
        for lang_idx, lang in enumerate(target_langs):
            lang_base = 15.0 + (lang_idx * 25.0)  # 每个语言占25%进度
            
            async def batch_callback(info):
                # 将批处理进度映射到总进度
                batch_progress = info['progress'] / 100  # 0-1
                overall_progress = lang_base + (batch_progress * 25.0)
                
                await self.update_progress(
                    overall_progress,
                    f"翻译到 {lang}: {info['message']}"
                )
            
            print(f"\n开始翻译到 {lang}...")
            await processor.translate_batch(
                texts, [lang], 
                batch_size=20,
                progress_callback=batch_callback
            )
            print(f"✓ 完成 {lang} 翻译")
        
        # 阶段6: 保存结果
        await self.update_progress(90.0, "保存翻译结果")
        await asyncio.sleep(1)
        
        # 完成
        await self.update_progress(100.0, "翻译完成")
        self.status = "completed"
        
        print(f"\n{'='*60}")
        print(f"任务完成！")
        print(f"{'='*60}\n")
    
    async def update_progress(self, progress, step):
        """更新进度"""
        self.progress = progress
        self.current_step = step
        
        # 打印进度条
        bar_length = 40
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r[{bar}] {progress:5.1f}% - {step}", end='')
        if progress >= 100:
            print()  # 完成时换行
        
        # 模拟返回给前端的数据
        status_data = {
            'task_id': self.task_id,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'timestamp': datetime.now().isoformat()
        }
        
        # 写入状态文件（可选）
        with open('/tmp/batch_progress.json', 'w') as f:
            json.dump(status_data, f, indent=2)


async def main():
    """主函数"""
    simulator = TaskSimulator()
    
    # 启动进度监控
    async def monitor_progress():
        """监控进度"""
        while simulator.status == "running":
            await asyncio.sleep(2)
            print(f"\n[监控] 当前进度: {simulator.progress:.1f}% - {simulator.current_step}")
    
    # 并发执行任务和监控
    await asyncio.gather(
        simulator.execute_batch_api(),
        monitor_progress()
    )
    
    print("\n测试完成！")
    print(f"最终状态: {simulator.status}")
    print(f"最终进度: {simulator.progress}%")


if __name__ == "__main__":
    asyncio.run(main())