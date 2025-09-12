# 批处理进度更新修复方案

## 问题描述
批处理API模式（`batch_api`）下，任务创建后进度一直停留在0%，`current_step`为空，用户无法看到处理进展。

## 问题原因
1. `_execute_batch_api`方法没有更新`task.progress`和`task.current_step`
2. 批处理器没有进度回调机制
3. 长时间等待批处理完成，没有中间状态更新

## 解决方案

### 1. 增强批处理执行方法
在`smart_translation_service.py`的`_execute_batch_api`方法中添加多阶段进度更新：

```python
# 阶段1：准备 (1%)
task.current_step = "准备批处理任务"
task.progress = 1.0

# 阶段2：读取文件 (5%)
task.current_step = "读取Excel文件"
task.progress = 5.0

# 阶段3：提取文本 (10%)
task.current_step = "提取待翻译文本"
task.progress = 10.0

# 阶段4：创建批处理 (15%)
task.current_step = "创建批处理任务"
task.progress = 15.0

# 阶段5：批处理执行 (15%-90%)
# 动态更新，根据完成的请求数计算

# 阶段6：保存结果 (90%-100%)
task.current_step = "保存翻译结果"
task.progress = 90.0
```

### 2. 实现批处理监控
新增`_execute_batch_with_monitoring`方法，实现：
- 按语言分批处理
- 每个语言占用相应的进度范围
- 批次级进度更新
- 实时反馈处理状态

### 3. 批处理器进度回调
在`batch_processor.py`中添加`progress_callback`参数：
- `translate_batch`方法支持进度回调
- `process_batch`方法传递回调
- `_wait_for_completion`方法中触发回调
- 提供批次ID、状态、完成数、总数等信息

### 4. 进度信息结构
```python
{
    'task_id': 'xxx',
    'status': 'running',
    'progress': 45.5,  # 百分比
    'current_step': '翻译到 pt: 处理批次 3/10',
    'batch_info': {
        'current_language': 'pt',
        'total_requests': 23351,
        'completed_requests': 10000,
        'failed_requests': 0,
        'elapsed_time': 300
    }
}
```

## 测试验证
运行`test_batch_progress.py`测试脚本，验证进度更新：
```bash
python3 /mnt/d/work/trans_excel/test_batch_progress.py
```

## 前端显示建议
1. 显示当前处理阶段
2. 显示处理的语言和批次
3. 显示预计剩余时间
4. 批处理特有的提示（如"批处理模式，成本节省50%"）

## 效果对比

### 修复前
```json
{
    "progress": 0.0,
    "current_step": "",
    "status": "running",
    "elapsed_time": 836.89
}
```

### 修复后
```json
{
    "progress": 45.5,
    "current_step": "翻译到 pt: 处理批次 3/10",
    "status": "running",
    "elapsed_time": 300.0,
    "batch_info": {
        "current_language": "pt",
        "total_requests": 23351,
        "completed_requests": 10000
    }
}
```

## 注意事项
1. 批处理API的实际进度依赖于阿里云API的状态返回
2. 轮询间隔设置为5秒，避免频繁调用
3. 网络异常时有重试机制
4. 进度更新需要通过WebSocket或轮询传递给前端