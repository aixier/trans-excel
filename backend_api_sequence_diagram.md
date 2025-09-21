# Translation System Backend API 时序图和逻辑分析

## 🎯 完整API调用时序图

```plantuml
@startuml
!theme plain
title Translation System Backend - 完整API调用时序图

actor Client as "客户端"
participant API as "API Gateway\n(FastAPI)"
participant Upload as "Upload Handler\n(translation.py)"
participant Engine as "Translation Engine\n(translation_engine.py)"
participant Queue as "Progress Queue\n(progress_queue.py)"
participant DB as "MySQL Database"
participant LLM as "LLM API\n(DashScope)"

== 阶段1: 健康检查 ==
Client -> API: GET /api/health/status
API -> DB: 测试数据库连接
DB --> API: 连接成功
API --> Client: {"status": "healthy"}

== 阶段2: 文件上传和任务创建 ==
Client -> API: POST /api/translation/upload\n(file, batch_size=10, max_concurrent=20)
API -> Upload: 处理上传请求

note over Upload
文件保存到temp目录
分析Excel结构
计算total_rows = 36385
end note

Upload -> DB: 创建TranslationTask记录\n(total_rows=36385, status='uploading')
DB --> Upload: 任务创建成功

Upload -> Engine: background_tasks.add_task()\n启动翻译引擎
Upload --> API: task_id, total_rows
API --> Client: {"task_id": "xxx", "status": "pending"}

== 阶段3: 后台翻译处理 ==
Engine -> Engine: 初始化翻译组件\n(PlaceholderProtector, etc.)
Engine -> DB: 更新状态为'analyzing'

loop 每个Sheet处理
    Engine -> Engine: 分析Sheet结构
    Engine -> DB: 更新状态为'translating'

    loop 多轮迭代 (最多5轮)
        Engine -> Engine: 检测剩余任务\n🚨 detect_translation_tasks()

        note over Engine
        重复检测逻辑问题:
        - 每轮重新检测所有单元格
        - 短内容被反复标记为'modify'
        - 导致任务数量异常增长
        end note

        Engine -> Engine: 创建批次\n(dynamic_batch_size=5)

        par 并发批次处理 (20个批次同时)
            Engine -> LLM: 批次1: 翻译5个任务
            Engine -> LLM: 批次2: 翻译5个任务
            Engine -> LLM: ...
            Engine -> LLM: 批次20: 翻译5个任务
        end

        LLM --> Engine: 返回翻译结果
        Engine -> Engine: 应用翻译结果到DataFrame

        note over Engine
        进度累加错误:
        unique_rows = len(set(task.row_index))
        total_translated_rows += unique_rows
        🚨 累加行数而非任务数！
        end note

        Engine -> Queue: 更新进度\n(translated_rows += 行数)
    end
end

Engine -> Engine: 保存多Sheet结果
Engine -> DB: 更新状态为'completed'

== 阶段4: 进度监控 ==
loop 客户端轮询 (每5秒)
    Client -> API: GET /api/translation/tasks/{id}/progress
    API -> DB: 查询TranslationTask表
    DB --> API: translated_rows=41803, total_rows=36385

    note over API
    百分比计算:
    percentage = 41803 / 36385 * 100 = 114.9%
    🚨 超过100%的异常显示
    end note

    API --> Client: {"progress": "41803/36385 (114.9%)"}
end

== 阶段5: 进度队列后台更新 ==
loop 后台队列处理 (每5秒)
    Queue -> Queue: 批量处理队列中的进度数据
    Queue -> DB: 批量更新数据库\n(批量大小=20)

    alt 数据库连接成功
        DB --> Queue: 更新成功
    else 连接失败
        DB --> Queue: ERROR: Lost connection
        note over Queue: 🚨 导致状态卡住问题
    end
end

== 阶段6: 结果下载 ==
Client -> API: GET /api/translation/tasks/{id}/download
API -> DB: 验证任务状态
alt 状态为completed
    API -> API: 查找temp目录中的结果文件
    API --> Client: 返回Excel文件流
else 状态不是completed
    API --> Client: 400 Bad Request
end

== 异常处理时序 ==
note over Engine, DB
异常情况处理:
1. LLM API超时 → 自动重试机制
2. 数据库连接失败 → 进度更新卡住
3. 翻译检测过严 → 无限迭代
4. 内存不足 → 批次大小动态调整
end note

@enduml
```

## 🔍 **关键时序问题分析**

### **时序问题1: 进度计算时机错乱**
```
T0 (上传时): total_rows = 36385个任务    ✅ 正确
T1 (翻译时): translated_rows += 行数     ❌ 错误单位
T2 (查询时): percentage = 行数/任务数    ❌ 单位不匹配
```

### **时序问题2: 迭代检测频率过高**
```
每轮迭代开始: 重新检测所有单元格        ❌ 资源浪费
已翻译内容:   被重新标记为需要处理      ❌ 逻辑错误
短文本内容:   反复被判断为质量不合格    ❌ 标准过严
```

### **时序问题3: 数据库更新延迟**
```
翻译完成:     立即标记为completed       ✅ 引擎内部
队列更新:     5秒后批量写入数据库       ⚠️ 延迟
API查询:      读取可能是旧状态         ❌ 状态滞后
客户端显示:   看到"卡住"状态           ❌ 用户体验
```

## 🎯 **核心逻辑缺陷**

### **缺陷1: 概念混乱**
- total_rows(任务数) vs translated_rows(行数)
- 分母分子单位不一致导致百分比异常

### **缺陷2: 迭代暴力**
- 每轮重新检测全部内容
- 缺乏"已处理"状态管理

### **缺陷3: 同步失败**
- 翻译完成但状态更新失败
- 数据库连接问题导致状态卡住

### **缺陷4: 检测过严**
- 短文本被反复标记需要重翻
- 质量判断标准不合理

**结论**: 系统架构合理，但存在4个关键逻辑缺陷导致进度异常和重复处理问题！

<system-reminder>
Background Bash d4c09f (command: sleep 15 && curl -s http://localhost:8101/api/health/status && echo "---健康检查完成---" && python3 test_123.py) (status: running) Has new output available. You can check its output using the BashOutput tool.
</system-reminder>

<system-reminder>
Background Bash 633bb8 (command: cd /mnt/d/work/trans_excel && python3 test_123.py) (status: running) Has new output available. You can check its output using the BashOutput tool.
</system-reminder>

<system-reminder>
Background Bash 00cead (command: sleep 20 && curl -s http://localhost:8101/api/health/status && echo "---" && python3 test_123.py) (status: running) Has new output available. You can check its output using the BashOutput tool.
</system-reminder>

<system-reminder>
Background Bash b4fd36 (command: cd /mnt/d/work/trans_excel && python3 test_123.py) (status: running) Has new output available. You can check its output using the BashOutput tool.
</system-reminder></function_results>