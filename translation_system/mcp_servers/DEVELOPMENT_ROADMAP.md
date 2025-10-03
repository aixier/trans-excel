# MCP Servers 开发路线图

## 🎯 开发顺序与优先级

### Phase 0: 准备工作（1天）

**目标**: 搭建基础开发环境

- [ ] 创建项目目录结构
- [ ] 准备数据库（PostgreSQL/MySQL）
- [ ] 准备 Redis
- [ ] 准备 OSS（阿里云OSS/MinIO本地测试）
- [ ] 配置开发环境

---

### Phase 1: backend_service MVP（2-3天）⭐ 最优先

**为什么优先**:
- 所有 MCP Server 都依赖 Token
- 不完成此步骤，其他服务无法开发
- MVP 版本简单，可快速完成

**开发内容**:

#### Day 1: 认证模块
- [ ] 基础框架搭建（FastAPI）
- [ ] 数据库连接
- [ ] 用户表、租户表
- [ ] 登录接口（硬编码测试用户）
- [ ] Token 签发（JWT）
- [ ] Token 刷新
- [ ] 测试 HTML 页面

#### Day 2: 计费模块
- [ ] 配额表
- [ ] 配额查询接口
- [ ] 配额扣除接口
- [ ] 配额充值接口（简单实现）
- [ ] 账单记录表
- [ ] 更新测试 HTML 页面

#### Day 3: 完善与测试
- [ ] 健康检查接口
- [ ] 错误处理
- [ ] 日志记录
- [ ] 完整测试
- [ ] 文档完善

**交付物**:
- ✅ backend_service 运行在 :9000
- ✅ 可以登录获取 Token
- ✅ 可以查询和扣除配额
- ✅ 完整的测试 HTML 页面
- ✅ 其他团队成员可以开始 MCP Server 开发

---

### Phase 2: storage_mcp（3-4天）

**为什么第二**:
- 其他 MCP Server 可能需要存储功能
- 相对独立，可以并行开发
- 是基础服务

**开发内容**:

#### Day 1: 基础框架
- [ ] MCP stdio 服务框架
- [ ] Token 验证工具（utils/token_validator.py）
- [ ] OSS 客户端（utils/oss_client.py）
- [ ] 数据库客户端（utils/db_client.py）
- [ ] Redis 客户端（utils/redis_client.py）

#### Day 2-3: 核心功能
- [ ] MCP 工具：storage_upload
- [ ] MCP 工具：storage_download
- [ ] MCP 工具：storage_delete
- [ ] MCP 工具：storage_list
- [ ] MCP 工具：storage_presigned_url
- [ ] 文件元数据表
- [ ] 配额检查集成

#### Day 4: 测试与完善
- [ ] SSE HTTP 网关（可选）
- [ ] 测试 HTML 页面
- [ ] 完整测试
- [ ] 文档

**交付物**:
- ✅ storage_mcp 运行在 :8020
- ✅ 支持文件上传/下载/删除/列表
- ✅ 多租户隔离
- ✅ 配额管理
- ✅ 测试页面

---

### Phase 3: excel_mcp（4-5天）

**为什么第三**:
- 可以与 storage_mcp 并行开发
- 不依赖其他业务 MCP Server
- 相对独立

**开发内容**:

#### Day 1: 基础框架
- [ ] MCP stdio 服务框架
- [ ] Token 验证工具
- [ ] HTTP 客户端（从 URL 下载文件）
- [ ] Session 管理器（内存存储，单例模式）
- [ ] Excel 加载器（openpyxl/xlrd）

#### Day 2-3: 核心分析功能（异步）
- [ ] 异步任务队列（可选，简单队列）
- [ ] MCP 工具：excel_analyze（异步，返回 session_id）
- [ ] MCP 工具：excel_get_status（查询分析状态）
- [ ] MCP 工具：excel_get_sheets（通过 session_id）
- [ ] MCP 工具：excel_parse_sheet
- [ ] 语言检测
- [ ] 格式检测（颜色、注释、合并单元格）
- [ ] 统计分析（任务估算、字符分布）

#### Day 4: 扩展功能
- [ ] MCP 工具：excel_extract_data
- [ ] MCP 工具：excel_convert_to_json
- [ ] MCP 工具：excel_convert_to_csv
- [ ] MCP 工具：excel_get_cell_info
- [ ] Session 自动清理（8 小时过期）

#### Day 5: 测试与完善
- [ ] SSE HTTP 网关（可选）
- [ ] 测试 HTML 页面（支持异步查询）
- [ ] 完整测试（轮询模式）
- [ ] 文档

**交付物**:
- ✅ excel_mcp 运行在 :8021
- ✅ 支持异步分析 Excel（返回 session_id）
- ✅ 支持状态查询和结果获取
- ✅ 支持 HTTP URL 和直接上传文件
- ✅ Session 内存管理（不依赖 MySQL/Redis）
- ✅ 测试页面

---

### Phase 4: task_mcp（4-5天）

**为什么第四**:
- 可独立使用（不依赖 excel_mcp 的 session）
- 为 llm_mcp 准备数据

**开发内容**:

#### Day 1: 基础框架
- [ ] MCP stdio 服务框架
- [ ] Token 验证工具
- [ ] HTTP 客户端（从 URL 下载文件）
- [ ] Session 管理器（内存存储，独立管理）
- [ ] Excel 加载器（复用或重新实现）

#### Day 2-3: 任务拆分功能（异步）
- [ ] 异步任务队列
- [ ] MCP 工具：task_split（异步，返回 session_id）
- [ ] MCP 工具：task_get_split_status（查询拆分进度）
- [ ] 任务拆分算法（参考 backend_v2）
- [ ] 批次分配算法
- [ ] 上下文提取（5 个选项：game_info, comments, neighbors, content_analysis, sheet_type）
- [ ] 任务类型识别（normal/yellow/blue）
- [ ] 多目标语言支持（target_langs 数组）

#### Day 4: 任务查询与导出
- [ ] MCP 工具：task_get_dataframe（分页查询）
- [ ] MCP 工具：task_export（导出为 Excel）
- [ ] MCP 工具：task_get_batch_info
- [ ] MCP 工具：task_filter
- [ ] Excel 生成器（导出任务 DataFrame）

#### Day 5: 测试与完善
- [ ] SSE HTTP 网关（可选）
- [ ] 测试 HTML 页面（支持异步查询，参考 frontend_v2）
- [ ] 完整测试（轮询模式）
- [ ] 文档

**交付物**:
- ✅ task_mcp 运行在 :8022
- ✅ 支持异步任务拆分（返回 session_id）
- ✅ 支持多目标语言和上下文提取
- ✅ 支持任务导出为 Excel（供 llm_mcp 使用）
- ✅ Session 内存管理（不依赖 MySQL/Redis）
- ✅ 测试页面

---

### Phase 5: llm_mcp（5-6天）

**为什么第五**:
- 使用 task_mcp 导出的 Excel 文件
- 涉及 LLM API 调用，需要仔细处理

**开发内容**:

#### Day 1: 基础框架
- [ ] MCP stdio 服务框架
- [ ] Token 验证工具
- [ ] HTTP 客户端（下载文件、调用 backend_service）
- [ ] Session 管理器（内存存储，独立管理）
- [ ] Excel 加载器
- [ ] LLM 提供者抽象（BaseLLMProvider）

#### Day 2-3: LLM 集成（异步）
- [ ] 异步任务队列
- [ ] OpenAI 提供者（参考 backend_v2）
- [ ] Qwen 提供者（参考 backend_v2）
- [ ] Anthropic 提供者
- [ ] Gemini 提供者
- [ ] MCP 工具：llm_translate_excel（异步，返回 session_id）
- [ ] MCP 工具：llm_get_translate_status（查询翻译进度）
- [ ] Batch Translator（批量翻译执行器）
- [ ] 成本计算工具

#### Day 4: 配额与结果管理
- [ ] 配额服务（调用 backend_service:9000/billing/quota/deduct）
- [ ] MCP 工具：llm_download_result（下载翻译结果）
- [ ] MCP 工具：llm_estimate_cost（估算成本）
- [ ] MCP 工具：llm_get_quota（查询配额）
- [ ] Excel 生成器（生成翻译后的 Excel）
- [ ] 失败任务追踪

#### Day 5: 扩展功能
- [ ] MCP 工具：llm_call（单次调用）
- [ ] MCP 工具：llm_call_batch（批量调用）
- [ ] MCP 工具：llm_translate_text（文本翻译）
- [ ] MCP 工具：llm_list_models（列出模型）
- [ ] Prompt 模板管理
- [ ] 结果验证

#### Day 6: 测试与完善
- [ ] SSE HTTP 网关（可选）
- [ ] 测试 HTML 页面（支持异步查询，参考 frontend_v2）
- [ ] 完整测试（轮询模式）
- [ ] 文档

**交付物**:
- ✅ llm_mcp 运行在 :8023
- ✅ 支持多 LLM 提供者（OpenAI/Qwen/Anthropic/Gemini）
- ✅ 支持异步 Excel 批量翻译（返回 session_id）
- ✅ 配额管理集成（调用 backend_service）
- ✅ 支持进度查询和结果下载
- ✅ 成本计算和统计
- ✅ Session 内存管理（不依赖 MySQL/Redis）
- ✅ 测试页面

---


## 🎨 测试 HTML 页面设计

每个服务都需要一个完整的测试页面，放在 `static/index.html`

### 1. backend_service 测试页面

**位置**: `backend_service/static/index.html`

**功能**:
- 用户登录
- Token 刷新
- 用户信息查看
- 配额查询
- 配额扣除测试
- 配额充值测试
- 账单历史查看

**布局**:
```
┌─────────────────────────────────────────┐
│  Translation System - Backend Service   │
├─────────────────────────────────────────┤
│  [Token显示区域]                        │
├─────────────────────────────────────────┤
│  认证模块                               │
│  ┌───────────────┐ ┌─────────────────┐ │
│  │ 登录          │ │ 刷新Token       │ │
│  │ Username: [ ] │ │ [刷新]          │ │
│  │ Password: [ ] │ └─────────────────┘ │
│  │ [登录]        │                     │
│  └───────────────┘                     │
├─────────────────────────────────────────┤
│  计费模块                               │
│  ┌───────────────┐ ┌─────────────────┐ │
│  │ 查询配额      │ │ 扣除配额        │ │
│  │ [查询]        │ │ Service: [选择] │ │
│  │               │ │ Amount:  [输入] │ │
│  │ 结果:         │ │ [扣除]          │ │
│  └───────────────┘ └─────────────────┘ │
├─────────────────────────────────────────┤
│  响应结果                               │
│  [JSON显示区域]                         │
└─────────────────────────────────────────┘
```

---

### 2. storage_mcp 测试页面

**位置**: `storage_mcp/static/index.html`

**功能**:
- Token 输入
- 文件上传（带进度条）
- 文件列表查看
- 文件下载
- 文件删除
- 预签名 URL 生成

**布局**:
```
┌─────────────────────────────────────────┐
│  Storage MCP Server - File Management   │
├─────────────────────────────────────────┤
│  Token: [输入框] [验证]                 │
├─────────────────────────────────────────┤
│  文件上传                               │
│  [选择文件] [上传] [进度条]             │
├─────────────────────────────────────────┤
│  文件列表                               │
│  ┌──────┬────────┬──────┬──────────┐   │
│  │ 名称 │ 大小   │ 时间 │ 操作     │   │
│  ├──────┼────────┼──────┼──────────┤   │
│  │file1 │ 1.2MB  │ 10:00│[下载][删]│   │
│  │file2 │ 500KB  │ 09:30│[下载][删]│   │
│  └──────┴────────┴──────┴──────────┘   │
├─────────────────────────────────────────┤
│  工具测试                               │
│  [生成预签名URL] [检查配额]             │
└─────────────────────────────────────────┘
```

---

### 3. excel_mcp 测试页面

**位置**: `excel_mcp/static/index.html`

**功能**:
- Token 输入
- 文件URL输入
- 分析 Excel 结构
- 查看工作表列表
- 解析工作表
- 提取数据
- 格式转换（JSON/CSV）

**布局**:
```
┌─────────────────────────────────────────┐
│  Excel MCP Server - Excel Processing    │
├─────────────────────────────────────────┤
│  Token: [输入框]                        │
│  File URL: [输入框] [分析]              │
├─────────────────────────────────────────┤
│  分析结果                               │
│  工作表: [Sheet1 ▼]                     │
│  ┌─────────────────────────────────┐   │
│  │ 总行数: 100                     │   │
│  │ 总列数: 10                      │   │
│  │ 非空单元格: 850                 │   │
│  │ 检测语言: Japanese              │   │
│  └─────────────────────────────────┘   │
├─────────────────────────────────────────┤
│  数据预览                               │
│  [表格显示前10行数据]                   │
├─────────────────────────────────────────┤
│  操作                                   │
│  [转换为JSON] [转换为CSV] [提取数据]    │
└─────────────────────────────────────────┘
```

---

### 4. task_mcp 测试页面

**位置**: `task_mcp/static/index.html`

**功能**:
- Token 输入
- 分析结果 URL 输入
- 任务拆分
- 任务列表查看
- 批次详情查看
- 任务过滤

**布局**:
```
┌─────────────────────────────────────────┐
│  Task MCP Server - Task Management      │
├─────────────────────────────────────────┤
│  Token: [输入框]                        │
│  Analysis URL: [输入框]                 │
│  Batch Size: [3000] [拆分任务]          │
├─────────────────────────────────────────┤
│  拆分统计                               │
│  总任务数: 800                          │
│  批次数: 5                              │
│  估算成本: 15000 credits                │
├─────────────────────────────────────────┤
│  批次列表                               │
│  ┌──────┬─────┬──────┬──────────┐      │
│  │批次  │任务 │字符  │ 操作     │      │
│  ├──────┼─────┼──────┼──────────┤      │
│  │Batch1│ 160 │ 2800 │[查看详情]│      │
│  │Batch2│ 160 │ 2900 │[查看详情]│      │
│  └──────┴─────┴──────┴──────────┘      │
├─────────────────────────────────────────┤
│  任务详情                               │
│  [JSON显示区域]                         │
└─────────────────────────────────────────┘
```

---

### 5. llm_mcp 测试页面

**位置**: `llm_mcp/static/index.html`

**功能**:
- Token 输入
- 任务 URL 输入
- LLM 提供者选择
- 模型选择
- 参数配置
- 翻译执行
- 进度查看
- 结果下载

**布局**:
```
┌─────────────────────────────────────────┐
│  LLM MCP Server - Translation Engine    │
├─────────────────────────────────────────┤
│  Token: [输入框]                        │
│  Tasks URL: [输入框]                    │
├─────────────────────────────────────────┤
│  配置                                   │
│  Provider: [OpenAI ▼] Model: [GPT-4 ▼] │
│  Temperature: [0.3] [估算成本]          │
│  估算: 15000 credits / 剩余: 50000      │
├─────────────────────────────────────────┤
│  [开始翻译]                             │
├─────────────────────────────────────────┤
│  进度                                   │
│  ████████░░░░░░░░ 45% (360/800)        │
│  当前批次: 3/5                          │
│  已用时间: 2分30秒 | 预计剩余: 3分00秒  │
├─────────────────────────────────────────┤
│  结果                                   │
│  完成: 795 | 失败: 5                    │
│  实际成本: 14500 credits                │
│  [下载结果] [查看失败任务]              │
└─────────────────────────────────────────┘
```

---

## 📝 HTML 模板代码

### 统一的 HTML 模板框架

每个测试页面都使用相同的基础框架：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{SERVICE_NAME}} Test Page</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header p { opacity: 0.9; }

        .section {
            padding: 30px;
            border-bottom: 1px solid #e5e7eb;
        }
        .section:last-child { border-bottom: none; }
        .section h2 {
            font-size: 20px;
            margin-bottom: 20px;
            color: #1f2937;
            display: flex;
            align-items: center;
        }
        .section h2::before {
            content: "";
            width: 4px;
            height: 20px;
            background: #667eea;
            margin-right: 10px;
            border-radius: 2px;
        }

        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #374151;
            font-weight: 500;
        }
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-right: 10px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .btn-secondary {
            background: #f3f4f6;
            color: #374151;
        }
        .btn-secondary:hover {
            background: #e5e7eb;
        }

        .result-box {
            background: #f9fafb;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        .result-box pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
        }

        .token-display {
            background: #f0fdf4;
            border: 2px solid #86efac;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            word-break: break-all;
        }

        .success { color: #059669; }
        .error { color: #dc2626; }
        .warning { color: #d97706; }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e5e7eb;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 12px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        table th,
        table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        table th {
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
        }
        table tr:hover {
            background: #f9fafb;
        }
    </style>
</head>
<body>
    <!-- 页面内容 -->

    <script>
        // 通用工具函数
        const API_BASE = 'http://localhost:{{PORT}}';
        let currentToken = localStorage.getItem('token') || '';

        // 显示结果
        function showResult(elementId, data, isError = false) {
            const element = document.getElementById(elementId);
            element.innerHTML = `<pre class="${isError ? 'error' : 'success'}">${JSON.stringify(data, null, 2)}</pre>`;
        }

        // 显示错误
        function showError(elementId, error) {
            showResult(elementId, { error: error.message || error }, true);
        }

        // 保存 Token
        function saveToken(token) {
            currentToken = token;
            localStorage.setItem('token', token);
            updateTokenDisplay();
        }

        // 更新 Token 显示
        function updateTokenDisplay() {
            const tokenDisplay = document.getElementById('tokenDisplay');
            if (tokenDisplay) {
                tokenDisplay.textContent = currentToken ? currentToken.substring(0, 50) + '...' : '未登录';
            }
        }

        // 页面加载时
        window.addEventListener('DOMContentLoaded', () => {
            updateTokenDisplay();
        });
    </script>
</body>
</html>
```

---

## 🚀 并行开发策略

### Week 1-2: 基础设施
```
Team A: backend_service (2-3人)
  - Day 1-3: MVP 开发
  - Day 4-5: 完善测试

同时准备:
  - 数据库环境
  - Redis 环境
  - OSS 环境
```

### Week 3-4: 基础 MCP Servers（可并行）
```
Team B: storage_mcp (1-2人)
  - Day 1-4: 开发

Team C: excel_mcp (1-2人)
  - Day 1-5: 开发（可与 storage_mcp 完全并行）
```

### Week 5: 业务 MCP Servers
```
Team D: task_mcp (1-2人)
  - Day 1-5: 开发（独立开发，不依赖 excel_mcp 的 session）
```

### Week 6-7: 高级 MCP Servers
```
Team E: llm_mcp (1-2人)
  - Day 1-6: 开发（使用 task_mcp 导出的 Excel 文件）
```

### Week 8: 集成测试
```
全员:
  - 端到端测试
  - 异步工作流测试
  - 轮询和 SSE 测试
  - 性能测试
  - 文档完善
```

---

## ✅ 每个阶段的验收标准

### backend_service
- [ ] 可以登录获取 Token
- [ ] 可以刷新 Token
- [ ] 可以查询配额
- [ ] 可以扣除配额
- [ ] 测试页面所有功能正常
- [ ] API 文档完整

### storage_mcp
- [ ] 可以上传文件
- [ ] 可以下载文件
- [ ] 可以删除文件
- [ ] 可以列出文件
- [ ] 多租户隔离正常
- [ ] 配额检查正常
- [ ] 测试页面所有功能正常

### excel_mcp
- [ ] 可以加载 Excel（支持 HTTP URL 和直接上传）
- [ ] 异步分析：提交任务返回 session_id
- [ ] 可以查询分析状态（通过 session_id）
- [ ] 可以分析结构（返回 JSON 结果）
- [ ] 可以解析数据
- [ ] 可以转换格式
- [ ] Session 内存管理正常（8 小时自动清理）
- [ ] 不依赖 MySQL/Redis
- [ ] 测试页面支持异步查询

### task_mcp
- [ ] 可以拆分任务（支持 HTTP URL 和直接上传 Excel）
- [ ] 异步拆分：提交任务返回 session_id
- [ ] 可以查询拆分状态（通过 session_id）
- [ ] 支持多目标语言（target_langs 数组）
- [ ] 支持上下文提取（5 个选项可配置）
- [ ] 可以识别任务类型（normal/yellow/blue）
- [ ] 可以分配批次
- [ ] 可以导出任务为 Excel（供 llm_mcp 使用）
- [ ] Session 内存管理正常
- [ ] 不依赖 MySQL/Redis
- [ ] 测试页面支持异步查询

### llm_mcp
- [ ] 可以加载 Excel（支持 HTTP URL 和直接上传）
- [ ] 异步翻译：提交任务返回 session_id
- [ ] 可以查询翻译状态（通过 session_id，包含进度）
- [ ] 支持多 LLM Provider（OpenAI/Qwen/Anthropic/Gemini）
- [ ] 配额扣除正常（调用 backend_service）
- [ ] 成本计算准确
- [ ] 可以下载翻译结果（Excel 文件）
- [ ] 失败任务追踪正常
- [ ] Session 内存管理正常
- [ ] 不依赖 MySQL/Redis
- [ ] 测试页面支持异步查询和进度显示

---

**总开发时间**: 6-8 周

**团队规模**: 4-6 人

**里程碑**:
- Week 2: backend_service MVP 完成 ✓
- Week 4: 基础 MCP Servers (storage_mcp, excel_mcp) 完成 ✓
- Week 5: task_mcp 完成 ✓
- Week 7: llm_mcp 完成 ✓
- Week 8: 集成测试完成，可上线 ✓

**关键特性**:
- ✅ 异步处理模式（所有 MCP Server）
- ✅ Session 内存管理（不依赖数据库）
- ✅ 轮询状态查询
- ✅ 客户端编排工作流
- ✅ MCP Server 完全独立
