# Excel MCP v2.0 时序图文档

## 目录
1. [完整工作流程](#完整工作流程)
2. [Excel 分析流程](#excel-分析流程)
3. [任务拆分流程](#任务拆分流程)
4. [任务导出流程](#任务导出流程)
5. [异步任务处理](#异步任务处理)

## 完整工作流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Web as Web UI
    participant API as HTTP API
    participant Handler as MCP Handler
    participant Queue as Task Queue
    participant Services as Services
    participant Session as Session Manager

    User->>Web: 1. 上传Excel文件
    Web->>API: POST /mcp/tool (excel_analyze)
    API->>Handler: handle_tool_call()
    Handler->>Handler: Token验证
    Handler->>Queue: submit_analysis_task()
    Queue-->>Handler: session_id
    Handler-->>Web: {session_id, status: "queued"}

    Queue->>Services: 异步处理分析
    Services->>Session: 更新进度和结果

    Web->>API: 轮询状态 (excel_get_status)
    API->>Handler: handle_tool_call()
    Handler->>Session: get_session()
    Session-->>Web: {status: "completed", analysis}

    User->>Web: 2. 配置任务拆分
    Web->>API: POST /mcp/tool (excel_split_tasks)
    API->>Handler: handle_tool_call()
    Handler->>Queue: submit_task_split()
    Queue-->>Web: {status: "splitting"}

    Queue->>Services: 异步拆分任务
    Services->>Services: 分配批次
    Services->>Session: 更新任务列表

    Web->>API: 轮询状态
    API->>Session: get_session()
    Session-->>Web: {status: "completed", has_tasks: true}

    User->>Web: 3. 导出任务
    Web->>API: POST /mcp/tool (excel_export_tasks)
    API->>Handler: handle_tool_call()
    Handler->>Queue: submit_export_task()
    Queue-->>Web: {status: "exporting"}

    Queue->>Services: 异步导出
    Services->>Session: 更新导出信息

    Web->>API: 轮询导出状态
    API->>Session: get_session()
    Session-->>Web: {download_url}

    User->>Web: 下载文件
```

## Excel 分析流程

```mermaid
sequenceDiagram
    participant Client
    participant Handler as MCP Handler
    participant Queue as Task Queue
    participant Loader as Excel Loader
    participant Analyzer as Excel Analyzer
    participant Session as Session Manager

    Client->>Handler: excel_analyze(file_url, options)
    Handler->>Handler: validate_token()

    alt Token 无效
        Handler-->>Client: Error: Invalid token
    end

    Handler->>Session: create_session()
    Session-->>Handler: session_id

    Handler->>Queue: submit_analysis_task(session_id, file_url, options)
    Queue->>Queue: 加入队列
    Queue-->>Handler: 任务已提交
    Handler-->>Client: {session_id, status: "queued"}

    Note over Queue: 异步处理开始

    Queue->>Queue: _process_queue()
    Queue->>Session: 更新状态(ANALYZING)

    Queue->>Loader: load_from_url(file_url)
    Loader->>Loader: 下载文件
    Loader->>Loader: 解析Excel
    Loader->>Loader: 提取颜色信息
    Loader->>Loader: 提取注释信息
    Loader-->>Queue: ExcelDataFrame对象

    Queue->>Session: 保存excel_df
    Queue->>Session: 更新进度(40%)

    Queue->>Analyzer: analyze(excel_df, options)
    Analyzer->>Analyzer: 语言检测
    Analyzer->>Analyzer: 统计分析
    Analyzer->>Analyzer: 任务预估
    Analyzer->>Analyzer: 格式分析
    Analyzer-->>Queue: AnalysisResult

    Queue->>Session: 保存分析结果
    Queue->>Session: 更新状态(COMPLETED)
    Queue->>Session: 设置has_analysis=true

    Note over Client: 轮询获取结果

    Client->>Handler: excel_get_status(session_id)
    Handler->>Session: get_session(session_id)
    Session-->>Handler: SessionData
    Handler-->>Client: {status: "completed", result: analysis}
```

## 任务拆分流程

```mermaid
sequenceDiagram
    participant Client
    participant Handler as MCP Handler
    participant Queue as Task Queue
    participant Splitter as Task Splitter
    participant Session as Session Manager

    Client->>Handler: excel_split_tasks(session_id, source_lang, target_langs, options)
    Handler->>Handler: validate_token()
    Handler->>Session: get_session(session_id)

    alt 会话不存在
        Handler-->>Client: Error: Session not found
    end

    alt 未完成分析
        Handler-->>Client: Error: Analysis not completed
    end

    Handler->>Queue: submit_task_split(session_id, params)
    Queue-->>Handler: 任务已提交
    Handler-->>Client: {session_id, status: "splitting"}

    Note over Queue: 异步拆分开始

    Queue->>Session: 更新状态(SPLITTING)
    Queue->>Session: 获取excel_df

    Queue->>Splitter: split_excel(excel_df, source_lang, target_langs, options)

    loop 每个工作表
        Splitter->>Splitter: 检测语言列
        Splitter->>Splitter: 识别源列和目标列

        loop 每一行
            Splitter->>Splitter: 获取源文本
            Splitter->>Splitter: 检查单元格颜色

            alt 源单元格是蓝色
                Splitter->>Splitter: 创建BLUE任务(缩短)
            end

            loop 每个目标语言
                Splitter->>Splitter: 检查目标单元格

                alt 目标是黄色
                    Splitter->>Splitter: 创建YELLOW任务(重翻译)
                else 目标是蓝色
                    Splitter->>Splitter: 创建BLUE任务(缩短)
                else 目标为空
                    Splitter->>Splitter: 创建NORMAL任务(新翻译)
                end

                alt 提取上下文
                    Splitter->>Splitter: 提取游戏信息
                    Splitter->>Splitter: 提取相邻单元格
                    Splitter->>Splitter: 分析内容类型
                end
            end
        end
    end

    Splitter->>Splitter: allocate_batches(tasks)
    Note over Splitter: 按语言和类型分组
    Note over Splitter: 每批次≤50000字符

    Splitter->>Splitter: generate_summary()
    Splitter-->>Queue: {tasks, summary}

    Queue->>Session: 保存tasks
    Queue->>Session: 保存tasks_summary
    Queue->>Session: 设置has_tasks=true
    Queue->>Session: 更新状态(COMPLETED)

    Client->>Handler: excel_get_status(session_id)
    Handler->>Session: get_session()
    Session-->>Client: {status: "completed", has_tasks: true}

    Client->>Handler: excel_get_tasks(session_id)
    Handler->>Session: get_tasks()
    Session-->>Client: {tasks, summary}
```

## 任务导出流程

```mermaid
sequenceDiagram
    participant Client
    participant Handler as MCP Handler
    participant Queue as Task Queue
    participant Exporter as Task Exporter
    participant Session as Session Manager
    participant FileSystem as File System

    Client->>Handler: excel_export_tasks(session_id, format, include_context)
    Handler->>Handler: validate_token()
    Handler->>Session: get_session(session_id)

    alt 没有任务
        Handler-->>Client: Error: No tasks available
    end

    Handler->>Queue: submit_export_task(session_id, format, include_context)
    Queue-->>Handler: 任务已提交
    Handler-->>Client: {status: "exporting"}

    Note over Queue: 异步导出开始

    Queue->>Session: 更新状态(PROCESSING)
    Queue->>Session: 获取tasks

    alt format = "excel"
        Queue->>Exporter: export_to_excel(tasks, session_id)
        Exporter->>Exporter: 创建DataFrame
        Exporter->>Exporter: 扁平化context
        Exporter->>Exporter: 选择导出列
        Exporter->>FileSystem: 保存.xlsx文件
    else format = "json"
        Queue->>Exporter: export_to_json(tasks, session_id)
        Exporter->>FileSystem: 保存.json文件
    else format = "csv"
        Queue->>Exporter: export_to_csv(tasks, session_id)
        Exporter->>FileSystem: 保存.csv文件
    end

    Exporter-->>Queue: export_path

    Queue->>Queue: 生成download_url
    Queue->>Session: 保存export_path
    Queue->>Session: 保存download_url
    Queue->>Session: 更新状态(COMPLETED)

    Note over Client: 轮询导出状态

    Client->>Handler: excel_export_tasks(session_id)
    Handler->>Session: get_session()

    alt 导出完成
        Session-->>Handler: metadata[download_url]
        Handler-->>Client: {status: "completed", download_url}
    else 还在处理
        Handler-->>Client: {status: "exporting"}
    end

    Client->>Client: 显示下载链接
    Client->>FileSystem: GET /static/exports/{filename}
    FileSystem-->>Client: 文件内容
```

## 异步任务处理

```mermaid
sequenceDiagram
    participant API as API Layer
    participant Queue as Task Queue
    participant Worker as Worker Process
    participant Service as Service Layer
    participant Session as Session Manager

    API->>Queue: submit_task()
    Queue->>Queue: queue.put(task)
    Queue->>Queue: 检查processing标志

    alt 未在处理
        Queue->>Queue: processing = True
        Queue->>Worker: create_task(_process_queue)
    end

    API-->>API: 立即返回

    Note over Worker: 异步处理循环

    loop while not queue.empty()
        Worker->>Queue: queue.get()
        Queue-->>Worker: task

        Worker->>Session: 更新状态(PROCESSING)

        alt task.type = "analysis"
            Worker->>Service: analyze_excel()
        else task.type = "split"
            Worker->>Service: split_tasks()
        else task.type = "export"
            Worker->>Service: export_tasks()
        end

        Service-->>Worker: result

        Worker->>Session: 保存结果
        Worker->>Session: 更新状态(COMPLETED)

        Worker->>Queue: queue.task_done()
    end

    Worker->>Queue: processing = False
```

## 批次分配算法

```mermaid
flowchart TD
    A[开始] --> B[按目标语言分组任务]
    B --> C{遍历每个语言组}
    C --> D[初始化当前批次]
    D --> E{遍历语言组中的任务}

    E --> F[获取任务字符数]
    F --> G{当前批次+任务 > 50000字符?}

    G -->|是| H[分配batch_id给当前批次]
    H --> I[batch_counter++]
    I --> J[开始新批次]
    J --> K[添加任务到新批次]

    G -->|否| L[添加任务到当前批次]

    K --> M{还有更多任务?}
    L --> M

    M -->|是| E
    M -->|否| N[分配batch_id给剩余任务]

    N --> O{还有更多语言?}
    O -->|是| C
    O -->|否| P[返回带batch_id的任务列表]

    P --> Q[结束]
```

## 颜色检测流程

```mermaid
flowchart TD
    A[获取单元格颜色值] --> B{颜色值存在?}
    B -->|否| C[返回None]
    B -->|是| D[加载颜色配置]

    D --> E{检测黄色}
    E --> F[匹配patterns]
    F --> G{匹配成功?}
    G -->|是| H[返回is_yellow=True]
    G -->|否| I[匹配hex_values]
    I --> J{匹配成功?}
    J -->|是| H
    J -->|否| K[检查RGB范围]
    K --> L{在范围内?}
    L -->|是| H
    L -->|否| M{检测蓝色}

    M --> N[匹配蓝色hex_values]
    N --> O{匹配成功?}
    O -->|是| P[返回is_blue=True]
    O -->|否| Q[检查蓝色RGB范围]
    Q --> R{在范围内?}
    R -->|是| P
    R -->|否| S[返回False]
```

## 前端轮询机制

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend (JavaScript)
    participant Backend as Backend API
    participant Session as Session Store

    User->>Frontend: 触发操作(分析/拆分/导出)
    Frontend->>Backend: 发起异步任务请求
    Backend->>Backend: 提交到任务队列
    Backend-->>Frontend: {session_id, status: "processing"}

    Frontend->>Frontend: 显示进度条
    Frontend->>Frontend: 启动轮询定时器(1秒间隔)

    loop 轮询直到完成
        Frontend->>Backend: get_status(session_id)
        Backend->>Session: 查询会话状态
        Session-->>Backend: 当前状态和进度
        Backend-->>Frontend: {status, progress, result?}

        alt status = "completed"
            Frontend->>Frontend: 停止轮询
            Frontend->>Frontend: 显示结果
            Frontend->>User: 操作完成
        else status = "failed"
            Frontend->>Frontend: 停止轮询
            Frontend->>Frontend: 显示错误
            Frontend->>User: 操作失败
        else status = "processing/splitting/exporting"
            Frontend->>Frontend: 更新进度条
            Frontend->>Frontend: 继续轮询
        end
    end
```

## 错误处理流程

```mermaid
flowchart TD
    A[请求进入] --> B{Token验证}
    B -->|失败| C[返回401错误]
    B -->|成功| D{参数验证}
    D -->|无效| E[返回400错误]
    D -->|有效| F[执行业务逻辑]

    F --> G{执行是否成功?}
    G -->|成功| H[返回成功响应]
    G -->|失败| I{错误类型}

    I -->|业务错误| J[更新会话状态为FAILED]
    J --> K[记录错误信息]
    K --> L[返回错误响应]

    I -->|系统错误| M[记录错误日志]
    M --> N[返回500错误]

    I -->|资源不存在| O[返回404错误]

    L --> P[前端显示错误]
    N --> P
    O --> P
    C --> P
    E --> P
```

## 任务状态机

```mermaid
stateDiagram-v2
    [*] --> Created: 创建会话
    Created --> Analyzing: 开始分析
    Analyzing --> Completed: 分析完成
    Analyzing --> Failed: 分析失败

    Completed --> Splitting: 开始拆分
    Splitting --> Completed: 拆分完成
    Splitting --> Failed: 拆分失败

    Completed --> Processing: 开始导出
    Processing --> Completed: 导出完成
    Processing --> Failed: 导出失败

    Failed --> [*]: 结束
    Completed --> [*]: 结束

    note right of Completed
        可以有多个完成状态:
        - has_analysis: true
        - has_tasks: true
        - has_export: true
    end note

    note left of Failed
        失败时记录:
        - error.code
        - error.message
    end note
```

## 性能优化策略

```mermaid
flowchart LR
    A[性能优化] --> B[内存管理]
    A --> C[并发处理]
    A --> D[批次处理]
    A --> E[缓存策略]

    B --> B1[会话过期清理]
    B --> B2[流式文件处理]
    B --> B3[按需加载数据]

    C --> C1[异步任务队列]
    C --> C2[asyncio.to_thread]
    C --> C3[并行工具调用]

    D --> D1[50K字符/批次]
    D --> D2[按语言分组]
    D --> D3[按类型分批]

    E --> E1[会话缓存]
    E --> E2[分析结果缓存]
    E --> E3[8小时过期时间]
```

---

**版本**: v2.0.0
**更新日期**: 2025-10-03
**说明**: 本文档包含了 Excel MCP v2.0 的主要工作流程时序图和流程图