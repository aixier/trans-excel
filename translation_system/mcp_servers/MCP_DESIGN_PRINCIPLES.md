# MCP 设计精髓与核心原则

## 🎯 MCP 的本质

**MCP (Model Context Protocol)** 是一种基于 stdio 的进程间通信协议，旨在构建**可插拔的能力插件**，而不是微服务架构。

### 核心理念

> **每个 MCP Server = 独立的领域能力提供方**

- ✅ 像浏览器插件一样可插拔
- ✅ 可以用任何语言实现
- ✅ 独立发布、独立使用
- ✅ 通用设计、不绑定特定项目

---

## 🚫 常见误区

### ❌ 误区 1：MCP Server 是微服务

```
错误理解:
excel_mcp → 调用 storage_mcp → 调用 auth_mcp
（形成服务依赖链）

正确理解:
每个 MCP Server 完全独立
客户端（Claude Desktop/前端）负责编排
数据通过 URL 传递，而非服务调用
```

### ❌ 误区 2：共享代码库降低耦合

```
错误做法:
/common/
  ├── oss_client.py      # 所有服务共享
  ├── db_client.py
  └── redis_client.py

问题:
- 必须使用相同语言
- 必须同步更新版本
- 无法独立部署
- 破坏可插拔性

正确做法:
每个 MCP Server 自包含实现
或通过规范对齐（非代码共享）
或发布独立的 SDK 包（有版本管理）
```

### ❌ 误区 3：auth_mcp 作为 MCP Server

```
错误设计:
auth_mcp (MCP Server) 提供认证功能
其他 MCP Server 调用 auth_mcp 验证 Token

问题:
- 创建循环依赖
- auth 成为单点故障
- 违背独立性原则

正确设计:
backend_service (HTTP Service) 独立运行
  - 认证模块: Token 签发/刷新
  - 计费模块: 配额管理
  - 管理模块: 用户管理
MCP Server 使用 JWT 自验证
backend_service 只负责基础设施（非业务能力）
```

### ❌ 误区 4：项目专用设计

```
错误设计:
excel_mcp 专门为翻译项目设计
- 假设必须有 source_language/target_language 列
- 固定返回翻译专用格式
- 只能在翻译系统中使用

正确设计:
excel_mcp 提供通用 Excel 处理能力
- 识别所有列类型（文本/数字/日期/公式）
- 返回通用结构化数据
- 可用于数据分析、ETL、报表等任何场景
```

---

## ✅ 核心设计原则

### 原则 1：完全独立性

**每个 MCP Server 必须能够独立运行，不依赖其他 MCP Server**

```
测试标准:
1. 单独启动该 MCP Server
2. 只提供必要的资源配置（Token、OSS配置等）
3. 能够完成该领域的所有核心功能

示例:
excel_mcp 独立启动后，给定文件URL，即可完成：
- Excel 加载（自己实现 OSS 读取）
- 结构分析
- 数据提取
- 格式转换
无需调用任何其他 MCP Server
```

### 原则 2：领域完整性

**每个 MCP Server 应提供该领域的完整能力，而不只是项目需要的部分**

```
对比:
❌ 项目专用: excel_mcp 只提供 analyze_for_translation
✅ 领域通用: excel_mcp 提供
    - analyze_structure      # 分析结构
    - parse_sheet           # 解析工作表
    - extract_data          # 提取数据
    - validate_format       # 格式验证
    - convert_to_json       # 转换为JSON
    - convert_to_csv        # 转换为CSV
    - generate_excel        # 生成Excel
    - merge_sheets          # 合并工作表
    - split_by_column       # 按列拆分
    - detect_formulas       # 检测公式
    - extract_images        # 提取图片
    - read_vba_macros       # 读取VBA宏
```

### 原则 3：自包含实现

**每个 MCP Server 包含完成职责所需的所有能力**

```
能力分层:

核心能力（所有 MCP Server 必备）:
- Token 验证（JWT 自验证）
- MySQL 读写（存储业务数据）
- Redis 读写（缓存、会话）

专属能力（按职责需要）:
- storage_mcp: OSS 读写
- excel_mcp: OSS 读（通过共享工具库或自己实现）
- task_mcp: MQ 发布/订阅
- llm_mcp: LLM API 调用
- monitor_mcp: WebSocket 推送

禁止能力（职责边界）:
- excel_mcp 禁止 OSS 写（只读）
- 其他 MCP Server 禁止 OSS 写
- 只有 storage_mcp 可以写 OSS

实现方式:
方案 1: 每个 MCP Server 自己实现（真正独立）
方案 2: 使用发布的 SDK 包（有版本管理）
方案 3: 通过配置规范对齐（共享标准，独立实现）
```

### 原则 4：数据流编排在客户端

**MCP Server 之间不相互调用，数据通过 URL 传递，客户端负责编排**

```
工作流编排:

❌ 错误方式（服务间调用）:
用户 → excel_mcp → 调用 storage_mcp 下载文件
                 → 调用 storage_mcp 上传结果

✅ 正确方式（客户端编排）:
步骤 1: 用户 → storage_mcp.upload_file(file)
       返回: {url: "oss://tenant/user/file.xlsx"}

步骤 2: 用户 → excel_mcp.analyze_excel(url)
       excel_mcp 内部: 使用自己的 OSS 客户端读取 URL
       返回: {analysis_url: "oss://tenant/user/analysis.json"}

步骤 3: 用户 → task_mcp.split_tasks(analysis_url)
       task_mcp 内部: 使用自己的 OSS 客户端读取 URL
       返回: {tasks_url: "oss://tenant/user/tasks.json"}
```

### 原则 5：通过规范对齐，而非代码共享

**共享的是"标准"和"协议"，而不是"实现代码"**

```
应该共享的:

1. 配置格式规范
   // config_schema.json
   {
     "token": "JWT格式规范",
     "resources": {
       "oss": {...},
       "mysql": {...},
       "redis": {...}
     }
   }

2. 数据存储规范
   // storage_spec.md
   - OSS 路径: tenants/{tenant_id}/users/{user_id}/{category}/{file_id}
   - MySQL Schema: tenant_{tenant_id}
   - Redis 前缀: t{tenant_id}:u{user_id}:

3. Token 格式规范
   // token_spec.md
   - 算法: RS256
   - Payload 结构: {user_id, tenant_id, permissions, resources, quota}
   - 过期时间: 30分钟

4. API 接口规范
   // db_schema.sql
   CREATE TABLE files (...);

不应该共享的:

❌ 具体实现代码（/common/oss_client.py）
❌ 强制的技术栈（必须 Python）
❌ 版本同步要求（必须同时更新）
```

### 原则 6：可独立发布

**每个 MCP Server 应该能够作为独立产品发布**

```
发布标准:

1. 独立仓库
   github.com/your-org/excel-mcp-server
   github.com/your-org/storage-mcp-server

2. 包管理器
   pip install excel-mcp-server
   npm install @your-org/excel-mcp
   go get github.com/your-org/excel-mcp

3. 完整文档
   README.md:
   - 能力范围说明
   - 适用场景列举
   - 独立使用示例
   - 配置要求
   - API 文档

   QUICKSTART.md:
   - 安装步骤
   - 快速开始
   - 常见问题

4. 使用示例
   examples/
     ├── standalone/         # 独立使用
     ├── with_llm/          # 配合其他 MCP
     └── integration/       # 集成到项目

5. 版本管理
   CHANGELOG.md
   语义化版本: v1.2.3
```

---

## 🏗️ 架构模式

### 模式 1: MCP Servers + backend_service

```
架构:
┌─────────────────────────────────────────────┐
│           Claude Desktop / 前端              │
│        (工作流编排 + Token 管理)             │
└───────────┬─────────────────────────────────┘
            │
            ├──── backend_service (HTTP, :9000)
            │     统一后端服务
            │     - 认证模块 (/auth)
            │     - 计费模块 (/billing)
            │     - 管理模块 (/admin)
            │
            ├──── storage_mcp (stdio, :8020)
            │     通用文件存储能力
            │
            ├──── excel_mcp (stdio, :8021)
            │     通用 Excel 处理能力
            │
            ├──── task_mcp (stdio, :8022)
            │     通用任务编排能力
            │
            ├──── llm_mcp (stdio, :8023)
            │     通用 LLM 调用能力
            │
            └──── monitor_mcp (stdio, :8024)
                  通用监控能力

数据流:
1. 登录: 前端 → backend_service:9000/auth/login → 返回 Token
2. 上传: 前端 → storage_mcp (携带Token) → 返回 URL
3. 分析: 前端 → excel_mcp (携带Token + URL) → 返回 analysis_url
4. 拆分: 前端 → task_mcp (携带Token + analysis_url) → 返回 tasks_url
5. 翻译: 前端 → llm_mcp (携带Token + tasks_url) → 返回 result_url
        llm_mcp → backend_service:9000/billing/quota/deduct
6. 监控: 前端 → monitor_mcp (携带Token + execution_id) → 实时推送
```

### 模式 2: Token 验证机制

```
JWT 自验证 vs 调用认证服务:

✅ 推荐: JWT 自验证
┌──────────────┐
│  MCP Server  │
│              │
│ 1. 提取Token │
│ 2. 验证签名  │ ← 本地验证（公钥）
│ 3. 检查过期  │
│ 4. 提取信息  │
│ 5. 执行业务  │
└──────────────┘

优点:
- 无需调用 backend_service（性能高）
- backend_service 故障不影响业务
- 真正的独立性

Token 撤销机制:
- Redis 黑名单: blacklist:{token}
- MCP Server 先检查黑名单，再验证签名
- 仅紧急场景使用（如密码泄露）

❌ 不推荐: 每次调用 backend_service
┌──────────────┐      ┌─────────────────┐
│  MCP Server  │──────>│ backend_service │
│              │ 验证  │                 │
│ 1. 提取Token │<──────│ 1. 查询DB       │
│ 2. 等待验证  │ 结果  │ 2. 检查过期     │
│ 3. 执行业务  │      │ 3. 返回信息     │
└──────────────┘      └─────────────────┘

问题:
- 性能开销大（每次网络调用）
- backend_service 成为单点故障
- 违背独立性原则
```

### 模式 3: 资源隔离

```
多租户数据隔离:

Token 携带资源配置:
{
  "tenant_id": "tenant_abc",
  "user_id": "user_123",
  "resources": {
    "oss": {
      "provider": "aliyun",
      "bucket": "translation-system",
      "prefix": "tenants/abc/users/123/"  ← 自动隔离
    },
    "mysql": {
      "host": "localhost",
      "database": "translation_db",
      "schema": "tenant_abc"  ← 自动隔离
    },
    "redis": {
      "host": "localhost",
      "db": 5,
      "prefix": "t_abc:u_123:"  ← 自动隔离
    }
  }
}

MCP Server 自动应用:
# storage_mcp/services/storage_service.py
class StorageService:
    def __init__(self, token_payload):
        oss_config = token_payload["resources"]["oss"]
        self.prefix = oss_config["prefix"]  # 自动获取前缀

    async def upload_file(self, file_name, data):
        # 自动添加租户/用户前缀
        path = f"{self.prefix}{file_name}"
        await oss_client.upload(path, data)
        return {"url": f"oss://{path}"}

# excel_mcp/services/excel_service.py
class ExcelService:
    def __init__(self, token_payload):
        oss_config = token_payload["resources"]["oss"]
        self.oss_client = OSSClient(oss_config)

    async def analyze_excel(self, file_url):
        # 自己读取文件（不调用 storage_mcp）
        file_data = await self.oss_client.download(file_url)
        analysis = self._do_analysis(file_data)
        return analysis
```

---

## 📋 设计检查清单

### 每个 MCP Server 设计时必须确认：

#### 独立性检查
- [ ] 可以单独启动运行
- [ ] 不依赖其他 MCP Server
- [ ] 不调用其他 MCP Server
- [ ] 可以用任何语言实现
- [ ] 可以独立发布到包管理器

#### 能力完整性检查
- [ ] 提供该领域的完整能力（不只是项目需要的）
- [ ] 工具定义清晰（inputSchema 完整）
- [ ] 可以在多种场景使用（不绑定特定项目）
- [ ] 有丰富的配置选项（灵活性）

#### 自包含检查
- [ ] 包含所有必需能力（MySQL/Redis/OSS等）
- [ ] Token 自验证（不依赖 backend_service）
- [ ] 数据隔离自动应用（基于 Token）
- [ ] 错误处理完善
- [ ] 日志记录完整

#### 数据流检查
- [ ] 接收 URL 作为输入（而非直接文件）
- [ ] 返回 URL 作为输出（大数据）
- [ ] 客户端负责编排（而非服务间调用）
- [ ] 支持 SessionID 追踪业务流

#### 发布标准检查
- [ ] 有独立仓库
- [ ] 有完整 README（能力范围、适用场景）
- [ ] 有 QUICKSTART（安装、快速开始）
- [ ] 有使用示例（standalone/integration）
- [ ] 有版本管理（CHANGELOG）
- [ ] 可发布到包管理器

---

## 🎓 最佳实践

### 1. 如何处理代码复用

```
场景: 所有 MCP Server 都需要 OSS/MySQL/Redis 客户端

方案 A: 各自实现（真正独立）
优点: 完全独立，可以用不同语言
缺点: 代码重复

方案 B: 发布 SDK 包（推荐）
pip install translation-mcp-sdk==1.0.0

优点:
- 代码复用
- 有版本管理（不强制同步）
- 可以独立升级

缺点:
- 需要维护 SDK

方案 C: 规范对齐
共享: mcp_specs/（规范文档）
- token_spec.md
- storage_spec.md
- db_schema.sql
- config_schema.json

各自实现: 按规范实现

优点:
- 语言无关
- 完全解耦

缺点:
- 需要确保实现一致性
```

### 2. 如何设计通用能力

```
对比项目专用 vs 领域通用:

项目专用设计:
@tool("analyze_translation_excel")
async def analyze_translation_excel(token, file_url):
    """专门为翻译项目设计"""
    # 假设必须有 source_text/target_text 列
    # 固定返回翻译专用格式
    ...

领域通用设计:
@tool("analyze_structure")
async def analyze_structure(token, file_url, options=None):
    """通用Excel结构分析"""
    # 返回完整的结构信息，任何应用都可使用
    ...

@tool("parse_sheet")
async def parse_sheet(token, file_url, sheet_name, parse_rules=None):
    """灵活的工作表解析"""
    # 支持自定义解析规则
    ...

@tool("extract_columns")
async def extract_columns(token, file_url, column_mapping):
    """按映射提取列"""
    # 翻译项目可以传: {"source": "A", "target": "B"}
    # 其他项目可以传自己的映射
    ...

关键: 提供灵活的配置，而非固定的假设
```

### 3. 如何处理认证

```
✅ 正确的认证架构:

1. backend_service (统一 HTTP 后端服务)
   - 端口: 9000
   - 认证模块 (/auth): Token 签发/刷新
   - 计费模块 (/billing): 配额管理
   - 管理模块 (/admin): 用户管理
   - 技术: FastAPI/Express/Nest.js

2. MCP Servers (stdio 服务)
   - 职责: 业务能力
   - 认证: JWT 自验证
   - 公钥: 从环境变量读取

Token 签发:
前端 → backend_service:9000/auth/login
     → 返回 JWT Token

Token 验证:
前端 → excel_mcp (携带 Token)
     → excel_mcp 本地验证 JWT 签名
     → 提取 user_id, tenant_id, permissions
     → 执行业务逻辑

Token 撤销:
管理员 → backend_service:9000/auth/revoke
      → 写入 Redis: blacklist:{token}
所有 MCP Server → 先检查黑名单，再验证签名

配额扣除:
llm_mcp → backend_service:9000/billing/quota/deduct
       → 扣除用户配额
```

---

## 📖 总结

### MCP 设计的核心思想

1. **协议优于实现** - 通过规范对齐行为，而非共享代码
2. **独立优于复用** - 每个 MCP Server 完全独立，可插拔
3. **通用优于专用** - 领域能力完整，适用多种场景
4. **编排在客户端** - MCP Server 提供能力，客户端编排流程

### 设计哲学

> MCP Server 不是微服务的组件，而是可复用的能力插件

- 就像浏览器插件一样，可以随意组合
- 就像 npm 包一样，可以独立发布
- 就像 CLI 工具一样，可以单独使用

**最终目标**: 构建一个可复用的 MCP Server 生态，每个 Server 都是独立的产品。

---

**版本**: V1.0
**创建时间**: 2025-10-02
**状态**: 📐 设计原则
