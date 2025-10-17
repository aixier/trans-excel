# n8n 集成实现方案

本文档详细说明 n8n 与翻译系统集成的完整实现方案。

---

## 📋 目录

1. [架构设计](#架构设计)
2. [工作流设计](#工作流设计)
3. [实现步骤](#实现步骤)
4. [节点配置详解](#节点配置详解)
5. [数据流转](#数据流转)
6. [错误处理](#错误处理)
7. [性能优化](#性能优化)
8. [部署方案](#部署方案)

---

## 🏗️ 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         n8n Instance                        │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐  │
│  │   Trigger    │   │   Workflow   │   │   Action     │  │
│  │              │→→→│   Execution  │→→→│   Nodes      │  │
│  │  (Webhook/   │   │              │   │              │  │
│  │   Schedule)  │   │   Flow       │   │  (HTTP Req)  │  │
│  └──────────────┘   └──────────────┘   └──────────────┘  │
│                            ↓↑                              │
└────────────────────────────║───────────────────────────────┘
                             ║
                             ║ HTTP/REST API
                             ║
┌────────────────────────────║───────────────────────────────┐
│                     Backend API Server                      │
│                     (localhost:8013)                        │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐  │
│  │  Task Split  │   │   Execute    │   │   Download   │  │
│  │     API      │   │     API      │   │     API      │  │
│  └──────────────┘   └──────────────┘   └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. n8n Workflow（工作流引擎）
- **职责**: 编排任务流程，协调各个节点
- **特性**:
  - 可视化流程编辑
  - 条件分支
  - 循环处理
  - 错误重试

#### 2. HTTP Request 节点
- **职责**: 调用后端API
- **类型**:
  - `POST /api/tasks/split` - 上传并拆分任务
  - `POST /api/execute/start` - 开始执行翻译
  - `GET /api/execute/status/{id}` - 查询状态（轮询）
  - `GET /api/download/{id}` - 下载结果

#### 3. Trigger 节点
- **Webhook Trigger**: 外部HTTP请求触发
- **Schedule Trigger**: 定时触发（Cron表达式）
- **Manual Trigger**: 手动触发（测试用）

---

## 🔄 工作流设计

### 工作流1: 基础翻译流程

**文件**: `workflows/01_basic_translation.json`

**流程图**:
```
[Manual Trigger]
       ↓
[Read File from Path]
       ↓
[Upload & Split]
(POST /api/tasks/split)
       ↓
[Wait & Poll Status]
(GET /api/tasks/split/status/{id})
       ↓ (status == split_complete)
[Execute Translation]
(POST /api/execute/start)
       ↓
[Poll Execution Status]
(GET /api/execute/status/{id})
       ↓ (status == completed)
[Download Result]
(GET /api/download/{id})
       ↓
[Save to File]
```

**节点配置**:

```json
{
  "nodes": [
    {
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [100, 300]
    },
    {
      "name": "Read File",
      "type": "n8n-nodes-base.readBinaryFile",
      "parameters": {
        "filePath": "/data/input/game.xlsx"
      },
      "position": [300, 300]
    },
    {
      "name": "Upload & Split",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://localhost:8013/api/tasks/split",
        "sendBinaryData": true,
        "binaryPropertyName": "data",
        "bodyParameters": {
          "source_lang": "CH",
          "target_langs": "EN,TH",
          "rule_set": "translation"
        }
      },
      "position": [500, 300]
    },
    {
      "name": "Poll Split Status",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "=http://localhost:8013/api/tasks/split/status/{{$json.session_id}}",
        "options": {
          "repeat": {
            "until": "={{$json.status === 'split_complete'}}",
            "interval": 1000,
            "maxRetries": 300
          }
        }
      },
      "position": [700, 300]
    },
    {
      "name": "Execute Translation",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://localhost:8013/api/execute/start",
        "jsonParameters": true,
        "bodyParametersJson": "={\n  \"session_id\": \"{{$json.session_id}}\",\n  \"processor\": \"llm_qwen\",\n  \"max_workers\": 10\n}"
      },
      "position": [900, 300]
    },
    {
      "name": "Poll Execution Status",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "=http://localhost:8013/api/execute/status/{{$json.session_id}}",
        "options": {
          "repeat": {
            "until": "={{$json.status === 'completed'}}",
            "interval": 2000,
            "maxRetries": 1800
          }
        }
      },
      "position": [1100, 300]
    },
    {
      "name": "Download Result",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "=http://localhost:8013/api/download/{{$json.session_id}}",
        "options": {
          "responseFormat": "file"
        }
      },
      "position": [1300, 300]
    },
    {
      "name": "Save Result",
      "type": "n8n-nodes-base.writeBinaryFile",
      "parameters": {
        "fileName": "=result_{{$json.session_id}}.xlsx",
        "dataPropertyName": "data"
      },
      "position": [1500, 300]
    }
  ]
}
```

---

### 工作流2: 术语表翻译流程

**文件**: `workflows/02_translation_with_glossary.json`

**新增步骤**:
```
[Read File]
       ↓
[Check Glossary Exists]
(GET /api/glossaries/list)
       ↓
[IF Glossary Not Exists]
   ├→ [Upload Glossary]
   │  (POST /api/glossaries/upload)
   └→ [Continue]
       ↓
[Upload & Split]
       ↓
[Execute with Glossary]
(POST /api/execute/start with glossary_config)
       ↓
[Download Result]
```

**关键配置**:

```json
{
  "name": "Upload Glossary",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://localhost:8013/api/glossaries/upload",
    "sendBinaryData": true,
    "binaryPropertyName": "glossary",
    "bodyParameters": {
      "glossary_id": "terms"
    }
  }
}
```

```json
{
  "name": "Execute with Glossary",
  "parameters": {
    "bodyParametersJson": "={\n  \"session_id\": \"{{$json.session_id}}\",\n  \"processor\": \"llm_qwen\",\n  \"glossary_config\": {\n    \"enabled\": true,\n    \"id\": \"terms\"\n  }\n}"
  }
}
```

---

### 工作流3: 批量处理流程

**文件**: `workflows/03_batch_translation.json`

**流程图**:
```
[Schedule Trigger: Daily 2AM]
       ↓
[List Files in Directory]
       ↓
[Loop: For Each File]
   ├→ [Read File]
   ├→ [Upload & Split]
   ├→ [Execute Translation]
   ├→ [Download Result]
   └→ [Save to Output Folder]
       ↓
[Send Summary Email]
(Total: 10 files, Success: 9, Failed: 1)
```

**关键节点**:

```json
{
  "name": "Schedule Trigger",
  "type": "n8n-nodes-base.scheduleTrigger",
  "parameters": {
    "rule": {
      "interval": [
        {
          "field": "cronExpression",
          "expression": "0 2 * * *"
        }
      ]
    }
  }
}
```

```json
{
  "name": "List Files",
  "type": "n8n-nodes-base.executeCommand",
  "parameters": {
    "command": "find /data/input -name '*.xlsx' -type f"
  }
}
```

```json
{
  "name": "Loop Files",
  "type": "n8n-nodes-base.splitInBatches",
  "parameters": {
    "batchSize": 1,
    "options": {}
  }
}
```

---

### 工作流4: 链式处理（翻译+大写）

**文件**: `workflows/04_chain_translation_caps.json`

**流程图**:
```
[Upload File]
       ↓
[Stage 1: Translation]
   ├→ Split (rule_set=translation)
   ├→ Execute (processor=llm_qwen)
   └→ Store session_A
       ↓
[Stage 2: CAPS Conversion]
   ├→ Split (parent_session_id=session_A, rule_set=caps_only)
   ├→ Execute (processor=uppercase)
   └→ Store session_B
       ↓
[Download Final Result]
(Use session_B)
```

**关键点**:

```json
{
  "name": "Split Translation Tasks",
  "parameters": {
    "bodyParameters": {
      "rule_set": "translation",
      "target_langs": "EN"
    }
  }
}
```

```json
{
  "name": "Split CAPS Tasks",
  "parameters": {
    "bodyParameters": {
      "parent_session_id": "={{$json.session_id}}",
      "rule_set": "caps_only"
    }
  }
}
```

---

### 工作流5: Webhook触发流程

**文件**: `workflows/05_webhook_triggered.json`

**流程图**:
```
[Webhook Trigger]
(POST https://n8n.example.com/webhook/translate)
       ↓
[Parse Request Body]
(Extract file_url, target_langs, callback_url)
       ↓
[Download File from URL]
       ↓
[Upload & Split]
       ↓
[Execute Translation]
       ↓
[Download Result]
       ↓
[Upload Result to Cloud Storage]
       ↓
[Callback to Original System]
(POST to callback_url with result_url)
```

**Webhook配置**:

```json
{
  "name": "Webhook Trigger",
  "type": "n8n-nodes-base.webhook",
  "parameters": {
    "path": "translate",
    "responseMode": "responseNode",
    "options": {}
  }
}
```

**请求示例**:
```bash
curl -X POST https://n8n.example.com/webhook/translate \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://storage.example.com/game.xlsx",
    "target_langs": ["EN", "TH"],
    "callback_url": "https://api.example.com/translation/callback"
  }'
```

---

### 工作流6: 条件分支处理

**文件**: `workflows/06_conditional_processing.json`

**流程图**:
```
[Upload File]
       ↓
[Get Session Details]
(GET /api/sessions/detail/{id})
       ↓
[IF: task_count < 100]
   ├→ YES: [Fast Mode]
   │        (max_workers=20, no glossary)
   └→ NO:  [Accurate Mode]
            (max_workers=5, with glossary)
       ↓
[IF: Has CAPS Sheet]
   ├→ YES: [Execute Translation + CAPS]
   └→ NO:  [Execute Translation Only]
       ↓
[Download Result]
```

**IF节点配置**:

```json
{
  "name": "Check Task Count",
  "type": "n8n-nodes-base.if",
  "parameters": {
    "conditions": {
      "number": [
        {
          "value1": "={{$json.task_count}}",
          "operation": "smaller",
          "value2": 100
        }
      ]
    }
  }
}
```

---

## 🔧 实现步骤

### 阶段1: 环境准备 (1小时)

#### 步骤1.1: 安装n8n

**方式A: Docker（推荐）**

创建文件 `docker/docker-compose.yml`:
```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - GENERIC_TIMEZONE=Asia/Shanghai
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    volumes:
      - n8n_data:/home/node/.n8n
      - ./workflows:/workflows
      - /mnt/d/work/trans_excel:/data
    networks:
      - translation_network

  backend:
    image: translation_backend:latest
    ports:
      - "8013:8013"
    networks:
      - translation_network

networks:
  translation_network:
    driver: bridge

volumes:
  n8n_data:
```

启动命令:
```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/docker
docker-compose up -d
```

---

**方式B: npm（本地开发）**

```bash
npm install -g n8n
n8n start
```

---

#### 步骤1.2: 验证n8n安装

```bash
# 访问n8n界面
open http://localhost:5678

# 创建第一个账户
# 用户名: admin
# 密码: <设置密码>
```

---

#### 步骤1.3: 配置API连接

在n8n中创建Credential:

1. 点击 "Credentials" → "New"
2. 选择 "HTTP Header Auth"
3. 名称: `Translation API Auth`
4. 配置:
   - Header Name: `Authorization` (如果后端需要)
   - Header Value: `Bearer <your-token>` (如果后端需要)

---

### 阶段2: 创建基础工作流 (2小时)

#### 步骤2.1: 导入工作流模板

创建文件 `workflows/01_basic_translation.json`（完整JSON见上文）

导入步骤:
1. 在n8n界面点击 "Import from File"
2. 选择 `01_basic_translation.json`
3. 点击 "Import"

---

#### 步骤2.2: 配置节点参数

**修改API地址**:
- 如果n8n在Docker中: `http://backend:8013`
- 如果n8n在本地: `http://localhost:8013`
- 如果n8n在远程: `http://<your-backend-ip>:8013`

---

#### 步骤2.3: 测试工作流

1. 点击 "Execute Workflow"
2. 修改文件路径为实际路径
3. 观察每个节点的执行结果
4. 检查最终生成的文件

---

### 阶段3: 创建高级工作流 (3小时)

#### 步骤3.1: 术语表集成

创建 `workflows/02_translation_with_glossary.json`

关键点:
- 检查术语表是否存在
- 如果不存在则上传
- 在执行时启用术语表

---

#### 步骤3.2: 批量处理

创建 `workflows/03_batch_translation.json`

关键点:
- 使用Schedule Trigger
- 使用Loop节点遍历文件
- 收集执行结果
- 发送汇总通知

---

#### 步骤3.3: 链式处理

创建 `workflows/04_chain_translation_caps.json`

关键点:
- 第一阶段保存session_id
- 第二阶段使用parent_session_id
- 下载最终session的结果

---

### 阶段4: Webhook集成 (2小时)

#### 步骤4.1: 创建Webhook工作流

创建 `workflows/05_webhook_triggered.json`

配置Webhook URL: `https://your-n8n.com/webhook/translate`

---

#### 步骤4.2: 测试Webhook

```bash
curl -X POST https://your-n8n.com/webhook/translate \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/data/input/test.xlsx",
    "target_langs": ["EN"],
    "callback_url": "https://example.com/callback"
  }'
```

---

### 阶段5: 文档和示例 (2小时)

#### 步骤5.1: 创建README

编写 `n8n/README.md` - 快速开始指南

---

#### 步骤5.2: 创建工作流目录

编写 `docs/WORKFLOW_CATALOG.md` - 所有工作流说明

---

#### 步骤5.3: 准备示例数据

复制示例文件到 `examples/`:
- `sample_files/small_test.xlsx`
- `glossaries/game_terms.json`
- `configs/config_fast.json`

---

## 📊 数据流转

### 数据流示意图

```
┌──────────────────────────────────────────────────────────┐
│                    n8n Workflow                          │
└──────────────────────────────────────────────────────────┘
                           │
                           │ 1. Upload File
                           ↓
                    ┌─────────────┐
                    │  POST /api/ │
                    │ tasks/split │
                    └─────────────┘
                           │
                           │ Response: {session_id: "xxx"}
                           ↓
                    ┌─────────────┐
                    │ Store in    │
                    │ $json obj   │
                    └─────────────┘
                           │
                           │ 2. Poll Status
                           ↓
                    ┌─────────────┐
                    │  GET /api/  │
                    │ tasks/split │
                    │ /status/xxx │
                    └─────────────┘
                           │
                           │ Response: {status: "split_complete"}
                           ↓
                    ┌─────────────┐
                    │  IF status  │
                    │ == complete │
                    └─────────────┘
                           │
                           │ 3. Execute Translation
                           ↓
                    ┌─────────────┐
                    │  POST /api/ │
                    │execute/start│
                    │{session_id} │
                    └─────────────┘
                           │
                           │ 4. Poll Execution
                           ↓
                    ┌─────────────┐
                    │  GET /api/  │
                    │execute/     │
                    │status/xxx   │
                    └─────────────┘
                           │
                           │ Response: {status: "completed"}
                           ↓
                    ┌─────────────┐
                    │ Download    │
                    │ GET /api/   │
                    │download/xxx │
                    └─────────────┘
                           │
                           │ Binary File Stream
                           ↓
                    ┌─────────────┐
                    │ Save to     │
                    │ File System │
                    └─────────────┘
```

### 变量传递

**n8n内部变量**:

```javascript
// 节点1输出
$json = {
  "session_id": "abc-123",
  "total_tasks": 100
}

// 节点2可以访问
url = `http://localhost:8013/api/execute/start`
body = {
  "session_id": $json.session_id  // "abc-123"
}
```

---

## ⚠️ 错误处理

### 错误类型和处理策略

#### 1. 网络错误

**场景**: API无法访问

**处理**:
```json
{
  "name": "HTTP Request",
  "parameters": {
    "options": {
      "timeout": 30000,
      "retry": {
        "maxRetries": 3,
        "waitBetween": 1000
      }
    }
  }
}
```

#### 2. 超时错误

**场景**: 翻译时间过长

**处理**:
- 增加轮询超时时间: `maxRetries: 1800` (1小时)
- 添加超时通知节点

#### 3. 文件不存在

**场景**: 输入文件路径错误

**处理**:
```json
{
  "name": "Check File Exists",
  "type": "n8n-nodes-base.executeCommand",
  "parameters": {
    "command": "test -f /data/input/file.xlsx && echo 'exists' || echo 'not_found'"
  }
}
```

#### 4. Session失效

**场景**: Session被清理或过期

**处理**:
- 检查session是否存在
- 如果不存在，重新上传文件

---

## 🚀 性能优化

### 1. 并发控制

```json
{
  "name": "Execute Translation",
  "parameters": {
    "bodyParametersJson": "={\n  \"session_id\": \"{{$json.session_id}}\",\n  \"processor\": \"llm_qwen\",\n  \"max_workers\": 10\n}"
  }
}
```

**建议**:
- 小文件(<100行): `max_workers: 20`
- 中等文件(100-1000行): `max_workers: 10`
- 大文件(>1000行): `max_workers: 5`

---

### 2. 轮询间隔

**拆分阶段**: `interval: 1000ms` (1秒)
**执行阶段**: `interval: 2000ms` (2秒)

**原因**: 拆分很快，执行较慢

---

### 3. 批量处理优化

```json
{
  "name": "Process Batch",
  "type": "n8n-nodes-base.splitInBatches",
  "parameters": {
    "batchSize": 5,
    "options": {
      "reset": false
    }
  }
}
```

**建议**: 每次处理5个文件，避免同时启动过多任务

---

## 🐳 部署方案

### Docker Compose完整配置

```yaml
version: '3.8'

services:
  # n8n工作流引擎
  n8n:
    image: n8nio/n8n:latest
    container_name: translation_n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - GENERIC_TIMEZONE=Asia/Shanghai
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - N8N_USER_MANAGEMENT_DISABLED=false
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    volumes:
      - n8n_data:/home/node/.n8n
      - ./workflows:/workflows:ro
      - /mnt/d/work/trans_excel:/data
    networks:
      - translation_network
    depends_on:
      - backend

  # 翻译后端API
  backend:
    build: ../../../backend_v2
    container_name: translation_backend
    restart: unless-stopped
    ports:
      - "8013:8013"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ../../../backend_v2/data:/app/data
      - ../../../backend_v2/logs:/app/logs
    networks:
      - translation_network

networks:
  translation_network:
    driver: bridge

volumes:
  n8n_data:
```

### 环境变量

创建 `.env` 文件:
```bash
# n8n配置
N8N_ENCRYPTION_KEY=<random-32-char-string>
N8N_USER=admin
N8N_PASSWORD=<your-secure-password>

# 后端配置
QWEN_API_KEY=<your-qwen-api-key>
OPENAI_API_KEY=<your-openai-api-key>
```

---

## ✅ 实施检查清单

### 阶段1: 准备
- [ ] 安装n8n（Docker或npm）
- [ ] 验证n8n可访问（http://localhost:5678）
- [ ] 确认后端运行（http://localhost:8013）
- [ ] 创建n8n账户

### 阶段2: 基础工作流
- [ ] 导入基础翻译工作流
- [ ] 配置API地址
- [ ] 测试手动触发
- [ ] 验证文件生成

### 阶段3: 高级工作流
- [ ] 创建术语表工作流
- [ ] 创建批量处理工作流
- [ ] 创建链式处理工作流
- [ ] 测试所有工作流

### 阶段4: 自动化
- [ ] 配置定时触发
- [ ] 配置Webhook触发
- [ ] 测试自动执行
- [ ] 设置错误通知

### 阶段5: 文档
- [ ] 编写README
- [ ] 创建工作流目录
- [ ] 准备示例数据
- [ ] 编写故障排除指南

---

## 📚 相关文档

- [工作流目录](./WORKFLOW_CATALOG.md) - 所有工作流详细说明
- [Docker部署](./DOCKER_DEPLOYMENT.md) - 生产环境部署指南
- [故障排除](./TROUBLESHOOTING.md) - 常见问题解决
- [最佳实践](./BEST_PRACTICES.md) - 性能和安全建议

---

## 🎯 总结

### 核心优势

1. **零代码修改**: 后端API无需任何改动
2. **可视化编排**: 拖拽式工作流设计
3. **高度灵活**: 支持任意复杂流程
4. **易于维护**: 工作流独立于业务代码
5. **快速部署**: Docker一键启动

### 适用场景

✅ **推荐使用**:
- 定时批量翻译
- 复杂多步骤流程
- 需要与其他服务集成
- 需要条件分支和错误处理

❌ **不推荐使用**:
- 简单的单次手动翻译（用浏览器前端）
- 需要实时交互的场景（用浏览器前端）
- 高频次API调用（直接调用API更高效）

---

**方案设计完成！开始实施请参考[实现步骤](#实现步骤)** 🚀
