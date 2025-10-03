# MCP Servers 架构设计

> 📘 **必读**: 请先阅读 [MCP_DESIGN_PRINCIPLES.md](./MCP_DESIGN_PRINCIPLES.md) 了解核心设计理念

## 🎯 设计原则

1. **完全独立** - 每个 MCP Server 可独立运行，不依赖其他 MCP Server
2. **领域通用** - 提供完整的领域能力，适用多种场景，非项目专用
3. **自包含** - 包含完成职责所需的所有能力（MySQL/Redis/OSS等）
4. **客户端编排** - 数据通过 URL 传递，客户端负责工作流编排
5. **可独立发布** - 每个 MCP Server 可作为独立产品发布到包管理器

---

## 🏗️ 系统架构

### 架构分层

系统分为两层：
1. **后端服务层**（HTTP）- 基础设施服务（认证、计费、管理）
2. **MCP Server层**（stdio）- 业务能力服务

### 整体架构图

```
┌─────────────────────────────────────────────┐
│      Claude Desktop / 前端 / API Gateway     │
│           (工作流编排 + Token 管理)          │
└───────────┬─────────────────────────────────┘
            │
            ├──── backend_service (HTTP :9000)
            │     统一后端服务（非 MCP Server）
            │     - 认证模块 (/auth)
            │     - 计费模块 (/billing)
            │     - 管理模块 (/admin)
            │
            ├──── storage_mcp (stdio :8020)
            │     通用文件存储能力
            │
            ├──── excel_mcp (stdio :8021) ⭐ UPGRADED
            │     通用 Excel 处理能力 + 翻译任务拆分
            │     (已整合 task_mcp 功能 - v2.0.0)
            │
            └──── llm_mcp (stdio :8023)
                  通用 LLM 调用能力
```

### 数据流示例

```
用户完整工作流（Excel 翻译）:

1. 登录获取 Token
   前端 → backend_service:9000/auth/login → Token

2. 分析 Excel + 拆分任务（使用统一的 excel_mcp）
   方式A: 前端 → excel_mcp (Token, excel_file_upload) → excel_session_id
           前端 → excel_mcp (Token, excel_session_id) → analysis_result (JSON)
           前端 → excel_mcp (excel_split_tasks, session_id, target_langs) → 开始拆分
           前端 → excel_mcp (excel_get_tasks, session_id) → split_result (完成后)
           前端 → excel_mcp (excel_export_tasks, session_id) → tasks_excel_url

   方式B: 前端 → storage_mcp (Token, file) → file_url
           前端 → excel_mcp (Token, file_url) → excel_session_id
           前端 → excel_mcp (Token, excel_session_id) → analysis_result (JSON)
           前端 → excel_mcp (excel_split_tasks, session_id, target_langs) → 开始拆分
           前端 → excel_mcp (excel_get_tasks, session_id) → split_result
           前端 → excel_mcp (excel_export_tasks, session_id) → tasks_excel_url

3. 执行翻译
   前端 → llm_mcp (Token, tasks_excel_url OR file_upload) → llm_session_id
   前端 → llm_mcp (Token, llm_session_id) → translate_status (进度查询)
   前端 → llm_mcp (Token, llm_session_id) → download_url (完成后获取下载链接)

   llm_mcp 内部 → backend_service:9000/billing/quota/deduct

关键:
- 前端负责编排（而非 MCP Server 相互调用）
- 数据通过 HTTP URL 或直接上传文件传递（不使用 base64）
- 每个 MCP Server 独立运行（可单独使用）
- 异步处理：提交任务获取 session_id，轮询查询状态
- Session 管理：内存存储，不依赖 MySQL/Redis，每个 MCP Server 独立管理
- MCP Server 之间通过文件 URL 传递数据（如 excel_mcp 导出任务 Excel → llm_mcp 读取）
- 不能跨 MCP Server 引用 session_id（session 是内存私有的）
- llm_mcp 调用 backend_service 进行计费扣费
```

---

## 🔐 后端服务（HTTP，非 MCP Server）

### backend_service - 端口 9000

**定位**: 统一的 HTTP 后端服务，提供认证、计费、管理等基础设施功能

**为什么不是 MCP Server**:
- 基础设施服务，应该独立于业务能力
- HTTP 服务更适合认证和计费场景（支持 Web/Mobile 客户端）
- 避免 MCP Server 之间的依赖关系
- 部署运维简单（一个服务 vs 多个服务）

**技术栈**: FastAPI / Express / Nest.js

**主要模块**:

#### 1. 认证模块 (/auth)
- **Token 验证 API** - **所有 MCP Server 统一调用此 API 进行 token 验证**
- 用户认证（登录/注册/登出）
- Token 生成/刷新/撤销
- 用户管理
- 租户管理

**🔑 核心设计：统一 Token 验证**

所有 MCP Server 不再自己验证 token，而是统一调用 `backend_service:9000/auth/validate` API：

```python
# MCP Server 的 token_validator.py
class TokenValidator:
    def validate(self, token: str) -> Dict[str, Any]:
        # 调用统一验证 API
        response = requests.post(
            "http://localhost:9000/auth/validate",
            json={"token": token}
        )
        return response.json()['payload']
```

**优势**：
- ✅ 避免各 MCP Server 重复验证逻辑
- ✅ 集中管理权限和配额
- ✅ 易于维护和升级
- ✅ 统一的安全策略

#### 2. 计费模块 (/billing)
- 配额管理（查询/扣除/充值）
- 订阅管理（创建/升级/取消）
- 账单历史
- 使用统计
- 支付集成

#### 3. 管理模块 (/admin) - 可选
- 用户管理界面
- 系统统计
- 日志查询

**HTTP API**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
认证模块 (/auth)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST   /auth/validate           # 🔥 Token验证 (所有MCP Server调用)
POST   /auth/generate           # 生成JWT Token (开发调试用)
POST   /auth/reload_config      # 重新加载token配置
GET    /auth/token_ids          # 列出所有token ID

POST   /auth/login              # 用户登录
POST   /auth/register           # 用户注册
POST   /auth/refresh            # 刷新 Token
POST   /auth/logout             # 登出
GET    /auth/user/me            # 获取当前用户
PUT    /auth/user/me            # 更新用户信息

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
计费模块 (/billing)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET    /billing/quota           # 查询配额
POST   /billing/quota/deduct    # 扣除配额（MCP Server调用）
POST   /billing/quota/recharge  # 充值配额

GET    /billing/subscription    # 查询订阅
POST   /billing/subscription    # 创建/升级订阅
DELETE /billing/subscription    # 取消订阅

GET    /billing/history         # 账单历史
GET    /billing/usage           # 使用统计

POST   /billing/payment         # 创建支付
POST   /billing/webhook         # 支付回调

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
管理模块 (/admin) - 可选，需要管理员权限
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET    /admin/users             # 用户列表
GET    /admin/users/:id         # 用户详情
PUT    /admin/users/:id/quota   # 调整用户配额
PUT    /admin/users/:id/status  # 启用/禁用用户

GET    /admin/stats             # 系统统计
GET    /admin/logs              # 系统日志

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
健康检查 (/health)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET    /health                  # 服务健康状态
GET    /health/db               # 数据库健康状态
GET    /health/redis            # Redis 健康状态
```

**🔧 Token 配置文件 (backend_service/tokens.json)**:

```json
{
  "secret_key": "dev-secret-key-change-in-production",
  "fixed_tokens": {
    "test_token_123": {
      "user_id": "test_user",
      "tenant_id": "test_tenant",
      "username": "test@example.com",
      "permissions": {
        "storage:read": true,
        "storage:write": true,
        "excel:analyze": true,
        "task:split": true,
        "llm:translate": true
      },
      "resources": {
        "oss": {
          "provider": "local",
          "bucket": "test-bucket",
          "prefix": "test/"
        }
      },
      "quota": {
        "llm_credits": 100000,
        "storage_mb": 5000
      }
    }
  }
}
```

**说明**:
- `fixed_tokens`: 固定 token 配置，用于开发测试（无需生成 JWT）
- 支持两种 token 类型：固定 token 和 JWT token
- Token 配置详细说明见：`backend_service/TOKENS_DESIGN.md`

**文件结构**:
```
backend_service/
├── main.py                    # 服务入口
├── config.py                  # 配置管理
│
├── api/                       # API 路由
│   ├── auth.py               # 认证相关 API
│   ├── billing.py            # 计费相关 API
│   ├── admin.py              # 管理相关 API
│   └── health.py             # 健康检查
│
├── services/                  # 业务逻辑
│   ├── auth_service.py       # 认证服务
│   ├── token_service.py      # Token 管理
│   ├── user_service.py       # 用户管理
│   ├── billing_service.py    # 计费服务
│   ├── quota_service.py      # 配额管理
│   └── subscription_service.py # 订阅管理
│
├── models/                    # 数据模型
│   ├── user.py
│   ├── tenant.py
│   ├── quota.py
│   ├── subscription.py
│   └── billing_record.py
│
├── database/                  # 数据库
│   ├── db.py                 # 数据库连接
│   └── migrations/           # 数据库迁移
│
├── utils/                     # 工具
│   ├── jwt_utils.py
│   ├── redis_utils.py
│   └── payment_gateway.py
│
├── static/                    # 管理后台前端（可选）
│   └── admin/
│       └── index.html
│
├── requirements.txt
└── README.md
```

**Token 结构**:
```json
{
  "user_id": "user_123",
  "tenant_id": "tenant_abc",
  "username": "john@example.com",
  "roles": ["translator", "reviewer"],
  "permissions": {
    "storage:read": true,
    "storage:write": true,
    "excel:analyze": true,
    "llm:translate": true
  },
  "resources": {
    "oss": {
      "provider": "aliyun",
      "bucket": "translation-system",
      "prefix": "tenants/abc/users/123/"
    },
    "mysql": {
      "host": "localhost",
      "port": 3306,
      "database": "translation_db",
      "schema": "tenant_abc"
    },
    "redis": {
      "host": "localhost",
      "port": 6379,
      "db": 5,
      "prefix": "t_abc:u_123:"
    }
  },
  "quota": {
    "llm_credits": 50000,
    "storage_mb": 5000,
    "llm_tier": "pro",
    "storage_tier": "free"
  },
  "subscriptions": {
    "llm_mcp": {
      "tier": "pro",
      "expires_at": 1735689600,
      "auto_renew": true
    },
    "storage_mcp": {
      "tier": "free"
    }
  },
  "exp": 1696348800,  # 过期时间
  "iat": 1696262400   # 签发时间
}
```

**数据库设计**:
```sql
-- 用户表
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(50),
    status ENUM('active', 'disabled') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 租户表
CREATE TABLE tenants (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 配额表
CREATE TABLE quotas (
    user_id VARCHAR(50),
    service VARCHAR(50),  -- "llm_mcp", "storage_mcp"
    amount BIGINT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, service)
);

-- 订阅表
CREATE TABLE subscriptions (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    service VARCHAR(50) NOT NULL,
    tier VARCHAR(50) NOT NULL,
    status ENUM('active', 'cancelled', 'expired') DEFAULT 'active',
    started_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    auto_renew BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 账单记录表
CREATE TABLE billing_records (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    service VARCHAR(50) NOT NULL,
    amount INT NOT NULL,
    transaction_id VARCHAR(100),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_service_time (user_id, service, created_at)
);

-- 支付记录表
CREATE TABLE payments (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    payment_method VARCHAR(50),
    status ENUM('pending', 'success', 'failed') DEFAULT 'pending',
    provider VARCHAR(50),
    provider_payment_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**快速启动（MVP版本）**:

10分钟搭建最简版本，支持 MCP Server 立即开发：

```python
# backend_service/main.py - MVP 最简版本

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta

app = FastAPI(title="Translation Backend")

SECRET_KEY = "dev-secret-key-change-in-production"

# ============ 认证模块 ============

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
def login(req: LoginRequest):
    # MVP: 硬编码测试用户
    if req.username == "dev@test.com" and req.password == "dev123":
        payload = {
            "user_id": "dev_001",
            "tenant_id": "tenant_dev",
            "username": req.username,
            "permissions": {
                "storage:read": True, "storage:write": True,
                "excel:analyze": True, "llm:translate": True
            },
            "resources": {
                "oss": {"prefix": "tenants/dev/users/001/"},
                "mysql": {"schema": "tenant_dev"},
                "redis": {"prefix": "dev:001:"}
            },
            "quota": {
                "llm_credits": 100000,
                "storage_mb": 5000
            },
            "exp": (datetime.utcnow() + timedelta(days=1)).timestamp()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 86400
        }
    raise HTTPException(401, "Invalid credentials")

@app.post("/auth/refresh")
def refresh_token(refresh_token: str):
    # MVP: 简单实现
    return {"access_token": "refreshed_token", "expires_in": 1800}

# ============ 计费模块 ============

quota_db = {}  # MVP: 内存存储

@app.get("/billing/quota")
def get_quota(user_id: str):
    return quota_db.get(user_id, {"llm_credits": 100000})

@app.post("/billing/quota/deduct")
def deduct_quota(user_id: str, service: str, amount: int):
    current = quota_db.get(user_id, {}).get(service, 100000)
    if current < amount:
        raise HTTPException(400, "Insufficient quota")
    quota_db.setdefault(user_id, {})[service] = current - amount
    return {"success": True, "remaining": current - amount}

@app.post("/billing/quota/recharge")
def recharge_quota(user_id: str, service: str, amount: int):
    current = quota_db.get(user_id, {}).get(service, 0)
    quota_db.setdefault(user_id, {})[service] = current + amount
    return {"success": True, "new_quota": current + amount}

# ============ 健康检查 ============

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "backend_service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
```

启动方式：
```bash
# 安装依赖
pip install fastapi uvicorn pyjwt

# 启动服务
python backend_service/main.py

# 测试
curl -X POST http://localhost:9000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"dev@test.com","password":"dev123"}'
```

✓ MVP 版本包含认证和计费核心功能，10分钟完成，其他团队成员可立即开始开发 MCP Server！

---

## 📦 MCP Servers 列表

### 1. storage_mcp - 端口 8020

**定位**: 通用文件存储能力提供方

**领域范围**: 文件存储、OSS 代理、STS 凭证、配额管理

**适用场景**:
- Excel 文件上传下载
- 图片/视频存储
- 文档管理系统
- 备份服务
- 任何需要文件存储的应用

**核心能力**:
- ✅ 文件上传/下载/删除
- ✅ 多存储后端支持（OSS/S3/Local）
- ✅ STS 临时凭证生成
- ✅ 预签名 URL 生成
- ✅ 文件元数据管理
- ✅ 配额管理
- ✅ 多租户隔离
- ✅ 文件版本控制（可选）
- ✅ 文件分享（可选）

**MCP 工具**:
```
storage_upload          # 上传文件
storage_download        # 下载文件
storage_delete          # 删除文件
storage_list            # 列出文件
storage_get_info        # 获取文件信息
storage_presigned_url   # 生成预签名 URL
storage_get_sts         # 获取 STS 临时凭证
storage_quota_check     # 检查配额
storage_create_folder   # 创建文件夹
storage_move            # 移动文件
storage_copy            # 复制文件
```

**自包含能力**:
- ✅ OSS 读写（核心能力）
- ✅ MySQL（存储文件元数据）
- ✅ Redis（缓存、配额计数）
- ✅ Token 验证（JWT 自验证）

**文件结构**:
```
storage_mcp/
├── server.py              # MCP stdio 入口
├── mcp_tools.py           # MCP 工具定义
├── mcp_handler.py         # JSON-RPC 处理
├── utils/                 # 自包含工具（不是共享库）
│   ├── token_validator.py # JWT 验证
│   ├── db_client.py       # MySQL 客户端
│   ├── redis_client.py    # Redis 客户端
│   └── oss_client.py      # OSS 客户端
├── services/
│   ├── storage_service.py # 存储服务
│   ├── oss_provider.py    # OSS 提供者
│   ├── s3_provider.py     # S3 提供者
│   ├── local_provider.py  # 本地存储提供者
│   └── quota_service.py   # 配额管理
├── models/
│   ├── file_metadata.py   # 文件元数据模型
│   └── storage_config.py  # 存储配置模型
├── static/
│   └── index.html         # Web 测试界面
├── sse_server.py          # HTTP 网关（可选）
├── README.md              # 完整文档
├── QUICKSTART.md          # 快速开始
├── requirements.txt       # 依赖清单
└── examples/              # 使用示例
    ├── standalone.py      # 独立使用
    └── with_excel.py      # 配合 excel_mcp
```

**发布信息**:
- GitHub: `github.com/your-org/storage-mcp-server`
- PyPI: `pip install storage-mcp-server`
- 版本: v1.0.0

---

### 2. excel_mcp - 端口 8021

**定位**: 通用 Excel 文件处理能力提供方

**领域范围**: Excel 解析、分析、转换、生成

**适用场景**:
- 数据分析工具
- ETL 系统
- 报表生成
- 文档转换
- Excel 问答系统
- 翻译系统（作为其中一个场景）

**核心能力**:
- ✅ Excel 文件加载（.xlsx/.xls/.csv）- 从 HTTP URL 或直接上传
- ✅ 异步任务队列（处理耗时分析任务，避免阻塞）
- ✅ Session 管理（通过 session_id 跟踪分析状态和结果）
- ✅ 结构分析（工作表、行列、单元格、合并区域）
- ✅ 语言检测（检测文本语言分布）
- ✅ 格式检测（颜色、字体、边框、注释、公式）
- ✅ 统计分析（行数、列数、非空单元格、字符分布、任务估算）
- ✅ 数据提取（按规则提取数据）
- ✅ 数据转换（Excel → JSON/CSV）
- ✅ 工作表操作（解析、查询、过滤）
- ✅ 特殊内容提取（公式、图片、VBA 宏）

**MCP 工具**:
```
excel_analyze           # 综合分析 Excel（异步，返回 session_id）
excel_get_status        # 查询分析状态（通过 session_id）
excel_get_sheets        # 获取工作表列表（需要 session_id）
excel_parse_sheet       # 解析指定工作表数据
excel_extract_data      # 按规则提取数据
excel_get_cell_info     # 获取单元格详细信息（格式、颜色、注释）
excel_convert_to_json   # 转换为 JSON
excel_convert_to_csv    # 转换为 CSV
excel_generate_from_json # 从 JSON 生成 Excel
excel_merge_sheets      # 合并工作表
excel_split_by_column   # 按列拆分
excel_validate_format   # 验证格式
excel_extract_formulas  # 提取公式
excel_extract_images    # 提取图片
excel_read_vba          # 读取 VBA 宏
```

**输入输出示例**:
```python
# ========== 核心工具 1：excel_analyze（异步分析）==========
# 输入方式 1：传入可访问的 HTTP URL
{
  "tool": "excel_analyze",
  "arguments": {
    "token": "Bearer xxx",
    "file_url": "http://oss.example.com/files/abc123/data.xlsx",  # 可直接访问的 URL
    "options": {
      "detect_language": true,
      "detect_formats": true,
      "analyze_colors": true
    }
  }
}

# 输入方式 2：直接上传文件（multipart）
{
  "tool": "excel_analyze",
  "arguments": {
    "token": "Bearer xxx",
    "file": <binary file data>,  # 直接上传的文件
    "filename": "data.xlsx",
    "options": {
      "detect_language": true,
      "detect_formats": true,
      "analyze_colors": true
    }
  }
}

# 输出：返回 session_id（分析任务已提交到队列）
{
  "session_id": "session_abc123",
  "status": "queued",  # queued, processing, completed, failed
  "message": "Analysis task submitted to queue",
  "estimated_time": 30  # 预计处理时间（秒）
}


# ========== 核心工具 2：excel_get_status（查询分析状态）==========
# 输入：session_id
{
  "tool": "excel_get_status",
  "arguments": {
    "token": "Bearer xxx",
    "session_id": "session_abc123"
  }
}

# 输出情况 1：处理中
{
  "session_id": "session_abc123",
  "status": "processing",
  "progress": 45,  # 进度百分比
  "message": "Analyzing sheet 2 of 4"
}

# 输出情况 2：完成
{
  "session_id": "session_abc123",
  "status": "completed",
  "progress": 100,
  "result": {
    "file_info": {
      "filename": "data.xlsx",
      "sheets": ["Sheet1", "Sheet2"],
      "sheet_count": 2,
      "total_rows": 1000,
      "total_cols": 10
    },
    "language_detection": {
      "source_langs": ["ja", "en"],
      "target_langs": ["zh", "th", "vi"],
      "sheet_details": [
        {
          "sheet_name": "Sheet1",
          "source_languages": ["ja"],
          "target_languages": ["zh", "th"],
          "confidence": 0.95
        }
      ]
    },
    "statistics": {
      "non_empty_cells": 8500,
      "empty_cells": 1500,
      "formula_cells": 50,
      "merged_cells": 20,
      "estimated_tasks": 800,
      "char_distribution": {
        "min": 5,
        "max": 200,
        "avg": 45.5,
        "total": 36400
      }
    },
    "format_analysis": {
      "colored_cells": 150,
      "color_distribution": {
        "yellow": 80,
        "blue": 50,
        "other": 20
      },
      "cells_with_comments": 30
    }
  }
}

# 输出情况 3：失败
{
  "session_id": "session_abc123",
  "status": "failed",
  "error": {
    "code": "INVALID_FORMAT",
    "message": "File is not a valid Excel file"
  }
}


# ========== 其他工具示例 ==========
# excel_get_sheets（获取工作表列表）
{
  "tool": "excel_get_sheets",
  "arguments": {
    "token": "Bearer xxx",
    "session_id": "session_abc123"  # 使用已分析的 session
  }
}

# 输出
{
  "session_id": "session_abc123",
  "sheets": [
    {"name": "Sheet1", "rows": 500, "cols": 8},
    {"name": "Sheet2", "rows": 500, "cols": 8}
  ]
}


# excel_parse_sheet（解析工作表）
{
  "tool": "excel_parse_sheet",
  "arguments": {
    "token": "Bearer xxx",
    "session_id": "session_abc123",
    "sheet_name": "Sheet1",
    "limit": 100  # 只返回前 100 行
  }
}

# 输出
{
  "session_id": "session_abc123",
  "sheet_name": "Sheet1",
  "data": [
    {"A": "ID", "B": "Source", "C": "Target"},
    {"A": "1", "B": "こんにちは", "C": "你好"},
    ...
  ],
  "total_rows": 500,
  "returned_rows": 100
}
```

**数据流设计（符合 MCP 原则）**:
```
1. 输入：
   - 方式 A：file_url（可直接访问的 HTTP URL）
     excel_mcp 内部使用 HTTP 客户端下载文件

   - 方式 B：直接上传文件
     客户端直接传输文件二进制数据

2. 处理：
   - 异步队列处理（避免长时间阻塞）
   - 解析 → 分析 → 提取 → 保存到 Redis/MySQL
   - 返回 session_id 供后续查询

3. 输出：
   - 立即返回：session_id + status
   - 轮询查询：通过 excel_get_status 获取分析结果（JSON）
```

**自包含能力**:
- ✅ HTTP 客户端（从 URL 下载 Excel 文件）
- ✅ 文件上传处理（接收客户端直接上传的文件）
- ✅ Session 管理（内存存储，单例模式，自动过期清理）
- ✅ 异步任务队列（可选，处理耗时分析任务）
- ✅ Token 验证（JWT 自验证）
- ❌ MySQL/Redis（不依赖，使用内存管理）
- ❌ OSS 读写（不依赖 OSS）

**文件结构**:
```
excel_mcp/
├── server.py              # MCP stdio 入口
├── mcp_tools.py           # MCP 工具定义
├── mcp_handler.py         # JSON-RPC 处理
│
├── utils/                 # 工具类
│   ├── token_validator.py # JWT 验证
│   ├── session_manager.py # Session 管理（内存存储，参考 backend_v2）
│   ├── http_client.py     # HTTP 客户端（下载文件）
│   └── color_detector.py  # 颜色检测工具
│
├── services/
│   ├── excel_loader.py    # Excel 加载（从 URL 或上传文件）
│   ├── excel_analyzer.py  # 结构分析（参考 backend_v2）
│   ├── excel_parser.py    # 数据解析
│   ├── format_detector.py # 格式检测
│   ├── language_detector.py # 语言检测
│   └── task_queue.py      # 异步任务队列（可选，简单队列）
│
├── models/
│   ├── excel_dataframe.py # Excel 数据框架
│   ├── analysis_result.py # 分析结果模型
│   ├── session_data.py    # Session 数据模型
│   └── parse_rules.py     # 解析规则
│
├── static/
│   └── index.html         # Web 测试界面
│
├── README.md              # 完整文档
├── QUICKSTART.md          # 快速开始
├── requirements.txt       # 依赖清单
└── examples/
    ├── standalone.py      # 独立使用
    ├── data_analysis.py   # 数据分析场景
    └── translation.py     # 翻译场景
```

**Session 管理说明**:
- `utils/session_manager.py`：
  - 单例模式，内存存储
  - 管理 session_id → SessionData 映射
  - 自动清理过期 session（默认 8 小时）
  - 不依赖 MySQL/Redis

- `models/session_data.py`：
  - SessionData 类定义
  - 存储：excel_df, analysis, metadata, created_at, last_accessed
  - 轻量级，纯内存管理

**🚀 启动方式**:

excel_mcp 支持两种运行模式：

1. **stdio 模式** (用于 Claude Desktop)：
```bash
python3 server.py
```

2. **HTTP 模式** (用于 Web 测试)：
```bash
python3 server.py --http           # 默认端口 8021
python3 server.py --http --port=8888  # 自定义端口
```

HTTP 模式特性：
- 自动启动 HTTP 服务器（基于 aiohttp）
- 提供 `/mcp/tool` 接口供前端调用
- 自动服务静态测试页面：`http://localhost:8021/static/index.html`
- 支持 CORS，方便前端调试

**Token 验证**:
- excel_mcp 调用 `backend_service:9000/auth/validate` 进行统一验证
- 无需在 excel_mcp 中配置密钥或验证逻辑
- 参考实现：`excel_mcp/utils/token_validator.py`

**发布信息**:
- GitHub: `github.com/your-org/excel-mcp-server`
- PyPI: `pip install excel-mcp-server`
- 版本: v1.0.0

---

### 3. task_mcp - 端口 8022

**定位**: 通用任务编排与执行能力提供方

**领域范围**: 任务拆分、批次分配、工作流管理、任务调度

**适用场景**:
- 翻译任务编排（游戏本地化、文档翻译）
- 批量数据处理
- ETL 任务管理
- 任何需要任务编排的场景

**核心能力**:
- ✅ 任务拆分（从 Excel 拆分为多个任务）- 支持 URL 或直接上传
- ✅ 异步任务队列（处理耗时拆分任务，避免阻塞）
- ✅ Session 管理（通过 session_id 跟踪拆分状态和结果）
- ✅ 批次分配（智能分配批次）
- ✅ 任务类型识别（normal/yellow/blue 三种类型）
- ✅ 上下文提取（游戏信息、注释、相邻单元格等）
- ✅ 多目标语言支持（一次性为多个目标语言生成任务）
- ✅ 任务状态追踪
- ✅ 任务过滤与查询
- ✅ 任务数据导出（导出为 Excel）

**MCP 工具**:
```
task_split              # 拆分任务（异步，返回 session_id）
task_get_split_status   # 查询拆分状态（通过 session_id）
task_get_status         # 查询任务状态（通过 session_id）
task_get_dataframe      # 获取任务数据（分页）
task_export             # 导出任务为 Excel
task_get_batch_info     # 获取批次信息
task_update_status      # 更新任务状态
task_filter             # 过滤任务
```

**输入输出示例**:
```python
# ========== 核心工具 1：task_split（异步拆分）==========
# 输入方式 1：传入 Excel URL（推荐）
{
  "tool": "task_split",
  "arguments": {
    "token": "Bearer xxx",
    "excel_url": "http://oss.example.com/files/abc123/data.xlsx",
    "source_lang": null,  # null 表示自动检测，或指定 "EN", "CH"
    "target_langs": ["TR", "TH", "PT", "VN"],  # 多个目标语言
    "extract_context": true,  # 是否提取上下文（默认 true）
    "context_options": {
      "game_info": true,  # 游戏信息
      "comments": true,  # 单元格注释
      "neighbors": true,  # 相邻单元格
      "content_analysis": true,  # 内容特征分析
      "sheet_type": true  # 表格类型
    }
  }
}

# 输入方式 2：直接上传 Excel 文件
{
  "tool": "task_split",
  "arguments": {
    "token": "Bearer xxx",
    "file": <binary file data>,
    "filename": "data.xlsx",
    "source_lang": "EN",
    "target_langs": ["TR", "TH"],
    "extract_context": false  # 关闭上下文提取以提升速度
  }
}

# 输出：返回 session_id（拆分任务已提交到队列）
{
  "session_id": "task_session_xyz789",
  "status": "processing",  # processing, already_processing
  "message": "任务已提交，开始拆分...",
  "progress": 0
}


# ========== 核心工具 2：task_get_split_status（查询拆分进度）==========
{
  "tool": "task_get_split_status",
  "arguments": {
    "token": "Bearer xxx",
    "session_id": "task_session_xyz789"
  }
}

# 输出情况 1：处理中
{
  "session_id": "task_session_xyz789",
  "status": "processing",
  "progress": 45,  # 0-100
  "message": "正在处理表格: Sheet2 (2/4)",
  "total_sheets": 4,
  "processed_sheets": 2
}

# 输出情况 2：完成
{
  "session_id": "task_session_xyz789",
  "status": "completed",
  "progress": 100,
  "message": "拆分完成!",
  "result": {
    "task_count": 800,
    "batch_count": 25,
    "batch_distribution": {
      "TR": 10,
      "TH": 8,
      "PT": 7
    },
    "type_batch_distribution": {
      "normal": 20,  # 常规翻译（空白单元格）
      "yellow": 3,   # 黄色重翻译
      "blue": 2      # 蓝色缩短
    },
    "statistics": {
      "total": 800,
      "total_chars": 36400,
      "avg_chars": 45.5,
      "min_chars": 5,
      "max_chars": 200
    }
  }
}


# ========== 其他工具示例 ==========
# task_get_dataframe（获取任务数据，分页）
{
  "tool": "task_get_dataframe",
  "arguments": {
    "token": "Bearer xxx",
    "session_id": "task_session_xyz789",
    "limit": 100,  # 每页数量
    "offset": 0,   # 偏移量
    "filter": {
      "target_lang": "TR",  # 可选过滤条件
      "task_type": "normal"
    }
  }
}

# 输出
{
  "session_id": "task_session_xyz789",
  "total": 800,
  "limit": 100,
  "offset": 0,
  "tasks": [
    {
      "task_id": "task_001",
      "batch_id": "TR_normal_001",
      "group_id": "group_001",
      "source_lang": "EN",
      "target_lang": "TR",
      "source_text": "Hello World",
      "task_type": "normal",
      "char_count": 11,
      "status": "pending",
      "context": {
        "column_header": "Turkish",
        "game_info": {...},
        "comment": null
      }
    },
    ...
  ]
}


# task_export（导出为 Excel）
{
  "tool": "task_export",
  "arguments": {
    "token": "Bearer xxx",
    "session_id": "task_session_xyz789"
  }
}

# 输出：返回 Excel 文件的下载 URL 或直接返回文件
{
  "session_id": "task_session_xyz789",
  "filename": "tasks_task_session_xyz789.xlsx",
  "download_url": "http://localhost:8022/download/tasks_xyz789.xlsx",
  "file_size": 102400,
  "rows": 800
}
```

**数据流设计（符合 MCP 原则）**:
```
1. 输入：
   - 方式 A：excel_url（可直接访问的 HTTP URL）
   - 方式 B：直接上传文件

2. 处理：
   - 异步队列处理（避免长时间阻塞）
   - 下载/读取 Excel → 拆分 → 分配批次 → 生成任务 DataFrame
   - 返回 session_id 供后续查询

3. 输出：
   - 立即返回：session_id + status
   - 轮询查询：通过 task_get_split_status 获取进度
   - 导出结果：通过 task_export 导出 Excel
```

**自包含能力**:
- ✅ HTTP 客户端（从 URL 下载 Excel 文件）
- ✅ 文件上传处理（接收客户端直接上传的文件）
- ✅ Session 管理（内存存储，独立管理自己的 session）
- ✅ 异步任务队列（处理耗时拆分任务）
- ✅ Token 验证（JWT 自验证）
- ❌ MySQL/Redis（不依赖，使用内存管理）
- ❌ OSS（不依赖 OSS）

**文件结构**:
```
task_mcp/
├── server.py              # MCP stdio 入口
├── mcp_tools.py           # MCP 工具定义
├── mcp_handler.py         # JSON-RPC 处理
│
├── utils/                 # 工具类
│   ├── token_validator.py # JWT 验证
│   ├── session_manager.py # Session 管理（内存存储）
│   └── http_client.py     # HTTP 客户端（下载文件）
│
├── services/
│   ├── excel_loader.py    # Excel 加载（从 URL 或上传文件）
│   ├── task_queue.py      # 异步任务队列
│   ├── task_splitter.py   # 任务拆分（参考 backend_v2）
│   ├── batch_allocator.py # 批次分配
│   ├── context_extractor.py # 上下文提取
│   ├── task_manager.py    # 任务管理
│   └── excel_generator.py # Excel 生成器
│
├── models/
│   ├── task_dataframe.py  # 任务数据框架
│   ├── session_data.py    # Session 数据模型
│   ├── batch.py           # 批次模型
│   ├── context.py         # 上下文模型
│   └── split_options.py   # 拆分选项模型
│
├── static/
│   └── index.html         # Web 测试界面
│
├── README.md              # 完整文档
├── QUICKSTART.md          # 快速开始
├── requirements.txt       # 依赖清单
└── examples/
    ├── standalone.py      # 独立使用
    ├── translation.py     # 翻译场景
    └── etl.py            # ETL 场景
```

**发布信息**:
- GitHub: `github.com/your-org/task-mcp-server`
- PyPI: `pip install task-mcp-server`
- 版本: v1.0.0

---

### 4. llm_mcp - 端口 8023

**定位**: 通用 LLM 调用与管理能力提供方

**领域范围**: LLM API 调用、Prompt 管理、成本控制、结果处理

**适用场景**:
- 批量翻译
- 文本摘要
- 问答系统
- 代码生成
- 内容审核
- 任何需要 LLM 的场景

**核心能力**:
- ✅ 多 LLM 提供者（OpenAI/Anthropic/Qwen/Gemini/本地模型）
- ✅ Excel 批量翻译（输入 task_mcp 的 Excel 或 URL，输出翻译后的 Excel）
- ✅ 异步任务队列（处理耗时翻译任务，避免阻塞）
- ✅ Session 管理（通过 session_id 跟踪翻译状态和结果）
- ✅ Prompt 模板管理
- ✅ 批量调用优化
- ✅ 流式输出支持
- ✅ 成本计算与统计
- ✅ 配额管理（调用 backend_service 扣费）
- ✅ 重试与错误处理
- ✅ 响应缓存
- ✅ 并发控制
- ✅ 结果验证
- ✅ Token 计数
- ✅ 多轮对话管理（可选）

**MCP 工具**:
```
llm_translate_excel     # Excel 批量翻译（异步，返回 session_id）
llm_get_translate_status # 查询翻译状态（通过 session_id）
llm_download_result     # 下载翻译结果（Excel 文件）
llm_call                # 调用 LLM（单次）
llm_call_batch          # 批量调用
llm_call_stream         # 流式调用
llm_translate_text      # 文本翻译
llm_summarize           # 摘要（预设 Prompt）
llm_qa                  # 问答（预设 Prompt）
llm_retry               # 重试失败调用
llm_estimate_cost       # 估算成本
llm_get_quota           # 查询配额
llm_get_usage           # 查询使用统计
llm_list_models         # 列出可用模型
llm_prompt_save         # 保存 Prompt 模板
llm_prompt_load         # 加载 Prompt 模板
```

**输入输出示例**:
```python
# ========== 核心工具 1：llm_translate_excel（异步翻译）==========
# 输入方式 1：传入 Excel URL（推荐，如 task_mcp 导出的 Excel 文件）
{
  "tool": "llm_translate_excel",
  "arguments": {
    "token": "Bearer xxx",
    "excel_url": "http://oss.example.com/files/abc123/tasks.xlsx",  # task_mcp 导出的文件
    "provider": "openai",
    "model": "gpt-4",
    "translation_config": {
      "temperature": 0.3,
      "max_retries": 3,
      "batch_size": 10,
      "preserve_formatting": true
    }
  }
}

# 输入方式 2：直接上传 Excel 文件
{
  "tool": "llm_translate_excel",
  "arguments": {
    "token": "Bearer xxx",
    "file": <binary file data>,
    "filename": "tasks.xlsx",
    "provider": "qwen",
    "model": "qwen-plus",
    "translation_config": {
      "temperature": 0.3,
      "batch_size": 20
    }
  }
}

# 输出：返回 session_id（翻译任务已提交到队列）
{
  "session_id": "llm_session_abc123",
  "status": "queued",  # queued, processing, completed, failed
  "message": "Translation task submitted to queue",
  "estimated_time": 300,  # 预计处理时间（秒）
  "estimated_cost": 15000  # 预计消耗 credits
}


# ========== 核心工具 2：llm_get_translate_status（查询翻译状态）==========
{
  "tool": "llm_get_translate_status",
  "arguments": {
    "token": "Bearer xxx",
    "session_id": "llm_session_abc123"
  }
}

# 输出情况 1：处理中
{
  "session_id": "llm_session_abc123",
  "status": "processing",
  "progress": 65,  # 0-100
  "message": "Translating batch 13 of 20",
  "statistics": {
    "total_tasks": 800,
    "completed": 520,
    "failed": 5,
    "remaining": 275,
    "cost_so_far": 9800  # 已消耗 credits
  }
}

# 输出情况 2：完成
{
  "session_id": "llm_session_abc123",
  "status": "completed",
  "progress": 100,
  "message": "Translation completed!",
  "result": {
    "total_tasks": 800,
    "translated": 795,
    "failed": 5,
    "cost": 14500,  # 总消耗 credits
    "duration": 285,  # 实际耗时（秒）
    "download_url": "http://localhost:8023/download/llm_session_abc123.xlsx",
    "file_size": 256000,
    "failed_tasks": [
      {"task_id": "task_012", "error": "Rate limit exceeded"},
      {"task_id": "task_045", "error": "Invalid response"}
    ]
  }
}

# 输出情况 3：失败
{
  "session_id": "llm_session_abc123",
  "status": "failed",
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "Insufficient credits"
  }
}


# ========== 核心工具 3：llm_download_result（下载翻译结果）==========
{
  "tool": "llm_download_result",
  "arguments": {
    "token": "Bearer xxx",
    "session_id": "llm_session_abc123",
    "format": "excel"  # excel, json, csv
  }
}

# 输出：返回文件下载信息
{
  "session_id": "llm_session_abc123",
  "filename": "translated_llm_session_abc123.xlsx",
  "download_url": "http://localhost:8023/download/llm_session_abc123.xlsx",
  "file_size": 256000,
  "expires_at": 1696348800  # URL 过期时间
}


# ========== 其他工具示例 ==========
# llm_call（单次调用）
{
  "tool": "llm_call",
  "arguments": {
    "token": "Bearer xxx",
    "provider": "openai",
    "model": "gpt-4",
    "prompt": "Translate to Chinese: Hello World",
    "temperature": 0.3
  }
}

# 输出
{
  "response": "你好世界",
  "cost": 15,
  "tokens": {"prompt": 8, "completion": 4, "total": 12}
}


# llm_estimate_cost（估算成本）
{
  "tool": "llm_estimate_cost",
  "arguments": {
    "token": "Bearer xxx",
    "excel_url": "http://oss.example.com/files/abc123/tasks.xlsx",  # 或直接上传文件
    "provider": "openai",
    "model": "gpt-4"
  }
}

# 输出
{
  "estimated_cost": 15000,
  "estimated_tokens": 120000,
  "estimated_time": 300,
  "breakdown": {
    "normal_tasks": {"count": 700, "cost": 10500},
    "yellow_tasks": {"count": 80, "cost": 3200},
    "blue_tasks": {"count": 20, "cost": 1300}
  }
}
```

**数据流设计（符合 MCP 原则）**:
```
1. 输入：
   - 方式 A：excel_url（可直接访问的 HTTP URL，如 task_mcp 导出的文件）
   - 方式 B：直接上传文件

2. 处理：
   - 异步队列处理（避免长时间阻塞）
   - 下载/读取 Excel → 解析任务 → 批量调用 LLM → 写入翻译结果 → 生成 Excel
   - 返回 session_id 供后续查询
   - 调用 backend_service:9000/billing/quota/deduct 扣费

3. 输出：
   - 立即返回：session_id + status + estimated_cost
   - 轮询查询：通过 llm_get_translate_status 获取进度
   - 下载结果：通过 llm_download_result 下载翻译后的 Excel
```

**自包含能力**:
- ✅ HTTP 客户端（从 URL 下载 Excel 文件）
- ✅ 文件上传处理（接收客户端直接上传的文件）
- ✅ Session 管理（内存存储，独立管理自己的 session）
- ✅ 异步任务队列（处理耗时翻译任务）
- ✅ LLM API 调用（OpenAI/Qwen/Anthropic 等）
- ✅ Token 验证（JWT 自验证）
- ✅ 成本计算（调用 backend_service 扣费）
- ❌ MySQL/Redis（不依赖，使用内存管理）
- ❌ OSS（不依赖 OSS）

**文件结构**:
```
llm_mcp/
├── server.py              # MCP stdio 入口
├── mcp_tools.py           # MCP 工具定义
├── mcp_handler.py         # JSON-RPC 处理
│
├── utils/                 # 工具类
│   ├── token_validator.py # JWT 验证
│   ├── session_manager.py # Session 管理（内存存储）
│   ├── http_client.py     # HTTP 客户端（下载文件、调用 backend_service）
│   └── cost_calculator.py # 成本计算工具
│
├── services/
│   ├── excel_loader.py    # Excel 加载（从 URL 或上传文件）
│   ├── task_queue.py      # 异步任务队列
│   ├── batch_translator.py # 批量翻译执行器
│   ├── llm_executor.py    # LLM 调用执行器
│   ├── openai_provider.py # OpenAI 提供者
│   ├── anthropic_provider.py # Anthropic 提供者
│   ├── qwen_provider.py   # Qwen 提供者
│   ├── gemini_provider.py # Gemini 提供者
│   ├── quota_service.py   # 配额管理（调用 backend_service）
│   ├── prompt_manager.py  # Prompt 管理
│   ├── result_validator.py # 结果验证
│   └── excel_generator.py # Excel 生成器
│
├── models/
│   ├── llm_request.py
│   ├── llm_response.py
│   ├── translation_task.py
│   ├── session_data.py    # Session 数据模型
│   ├── prompt_template.py
│   └── billing.py
│
├── prompts/               # Prompt 模板库
│   ├── translation.json
│   ├── summarization.json
│   └── qa.json
│
├── static/
│   └── index.html         # Web 测试界面
│
├── README.md              # 完整文档
├── QUICKSTART.md          # 快速开始
├── requirements.txt       # 依赖清单
└── examples/
    ├── standalone.py      # 独立使用
    ├── translation.py     # 翻译场景
    ├── summarization.py   # 摘要场景
    └── custom_prompt.py   # 自定义 Prompt
```

**发布信息**:
- GitHub: `github.com/your-org/llm-mcp-server`
- PyPI: `pip install llm-mcp-server`
- 版本: v1.0.0

---

## 📋 统一文件结构规范

### 必需部分（MCP 核心）

```
{service}_mcp/
├── server.py              # stdio 通信入口
├── mcp_tools.py           # MCP 工具定义
├── mcp_handler.py         # JSON-RPC 协议处理
└── README.md              # 完整文档
```

### 推荐部分（最佳实践）

```
{service}_mcp/
├── utils/                 # 自包含工具（非共享库）
│   ├── token_validator.py # JWT 验证
│   ├── db_client.py       # MySQL 客户端
│   ├── redis_client.py    # Redis 客户端
│   └── oss_client.py      # OSS 客户端（按需）
│
├── services/              # 核心业务逻辑
│   └── xxx_service.py
│
├── models/                # 数据模型
│   └── xxx_model.py
│
├── static/                # Web 测试界面
│   └── index.html
│
├── sse_server.py          # HTTP 网关（可选）
├── QUICKSTART.md          # 快速开始
├── requirements.txt       # 依赖清单
└── examples/              # 使用示例
    ├── standalone.py      # 独立使用
    └── integration.py     # 集成示例
```

### 关键说明

**utils/ 不是共享库**:
- 每个 MCP Server 有自己的 utils/
- 可以有相同的文件名（如 token_validator.py）
- 实现可以不同（按各自需求）
- 不强制使用相同语言
- 通过规范对齐，而非代码共享

**如何处理代码复用**:
1. 方案 A: 各自实现（真正独立）
2. 方案 B: 发布 SDK 包（如 `pip install mcp-common-sdk`）
3. 方案 C: 规范对齐（共享规范文档，独立实现）

推荐方案 B 或 C。

---

## 🔐 Token 验证机制

### JWT 自验证（推荐）

每个 MCP Server 独立验证 Token，无需调用 auth_service：

```python
# utils/token_validator.py
import jwt

class TokenValidator:
    def __init__(self, public_key):
        self.public_key = public_key  # 从环境变量读取

    def validate(self, token):
        try:
            # JWT 自验证（本地验证签名）
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"]
            )

            # 检查过期
            if payload["exp"] < time.time():
                raise TokenExpired()

            # 检查黑名单（Redis）
            if redis.exists(f"blacklist:{token}"):
                raise TokenRevoked()

            return payload
        except Exception as e:
            raise InvalidToken(str(e))
```

**优点**:
- ✅ 无需调用 auth_service（性能高）
- ✅ auth_service 故障不影响业务
- ✅ 真正的独立性

**Token 撤销**:
- auth_service 将 Token 加入 Redis 黑名单
- MCP Server 验证前先检查黑名单

---

## 📊 数据隔离策略

### OSS 路径隔离

```
路径规范: tenants/{tenant_id}/users/{user_id}/{category}/{file_id}

示例:
- Excel 文件: tenants/abc/users/123/excel-files/file_001.xlsx
- 分析结果: tenants/abc/users/123/analysis/excel_001.json
- 任务数据: tenants/abc/users/123/tasks/session_001.json
```

Token 中的 `resources.oss.prefix` 自动应用：

```python
# 从 Token 中提取
oss_prefix = token_payload["resources"]["oss"]["prefix"]
# "tenants/abc/users/123/"

# 自动拼接
file_path = f"{oss_prefix}excel-files/{file_name}"
```

### MySQL Schema 隔离

```sql
-- 为每个租户创建独立 Schema
CREATE SCHEMA tenant_abc;
CREATE SCHEMA tenant_xyz;

-- 所有表创建在专属 Schema
CREATE TABLE tenant_abc.files (...);
CREATE TABLE tenant_abc.tasks (...);
```

Token 中的 `resources.mysql.schema` 自动应用。

### Redis 键隔离

```
键格式: {tenant_id}:{user_id}:{resource}:{id}

示例:
- Excel 缓存: t_abc:u_123:excel:file_001
- 任务缓存: t_abc:u_123:tasks:session_001
- 配额计数: quota:llm:t_abc:u_123
```

Token 中的 `resources.redis.prefix` 自动应用。

---

## ✅ 设计检查清单

### 每个 MCP Server 发布前必须确认：

#### 独立性检查
- [ ] 可以单独启动运行
- [ ] 不依赖其他 MCP Server
- [ ] 不调用其他 MCP Server 的工具
- [ ] 可以用任何语言实现（不强制 Python）
- [ ] 有独立的 Git 仓库

#### 能力完整性检查
- [ ] 提供该领域的完整能力（不只是项目需要的部分）
- [ ] 所有 MCP 工具都有完整的 inputSchema
- [ ] 支持多种使用场景（不绑定特定项目）
- [ ] 有丰富的配置选项

#### 自包含检查
- [ ] 包含所有必需能力（MySQL/Redis/OSS等）
- [ ] Token 自验证（JWT）
- [ ] 数据隔离自动应用（基于 Token）
- [ ] 错误处理完善
- [ ] 日志记录完整

#### 发布标准检查
- [ ] 有 README.md（能力范围、适用场景、API 文档）
- [ ] 有 QUICKSTART.md（安装、快速开始）
- [ ] 有 requirements.txt / package.json / go.mod
- [ ] 有 examples/（独立使用示例、集成示例）
- [ ] 有 CHANGELOG.md
- [ ] 可发布到包管理器（PyPI/npm/pkg.go.dev）

#### 多租户检查
- [ ] Token 验证集成
- [ ] 权限检查
- [ ] 配额检查
- [ ] 数据隔离（OSS/MySQL/Redis）
- [ ] 审计日志

---

## 🎓 最佳实践

### 1. 如何设计通用工具

```python
# ❌ 错误: 项目专用
@tool("analyze_translation_excel")
async def analyze_translation_excel(token, file_url):
    """只能用于翻译项目"""
    # 假设必须有 source_text/target_text 列
    ...

# ✅ 正确: 领域通用
@tool("analyze_structure")
async def analyze_structure(token, file_url, options=None):
    """通用 Excel 结构分析，任何场景都可用"""
    # 返回完整结构，由调用方决定如何使用
    ...

@tool("extract_columns")
async def extract_columns(token, file_url, column_mapping):
    """按映射提取列"""
    # 翻译项目: {"source": "A", "target": "B"}
    # 销售分析: {"product": "A", "revenue": "C"}
    ...
```

### 2. 如何处理文件数据

```python
# 输入方式 1: 从 HTTP URL 下载（推荐方式）
@tool("analyze_excel")
async def analyze_excel(token, file_url, options=None):
    # 使用 HTTP 客户端下载文件
    data = await http_client.download(file_url)

    # 创建 session_id
    session_id = generate_session_id()

    # 异步处理
    await task_queue.submit(session_id, data, options)

    return {
        "session_id": session_id,
        "status": "queued",
        "message": "Analysis task submitted"
    }

# 输入方式 2: 直接上传文件
@tool("analyze_excel")
async def analyze_excel(token, file=None, file_url=None, filename=None, options=None):
    if file:
        # 直接接收二进制文件数据
        data = file  # binary data
    elif file_url:
        # 从 URL 下载
        data = await http_client.download(file_url)
    else:
        raise ValueError("Must provide either file or file_url")

    session_id = generate_session_id()
    await task_queue.submit(session_id, data, options)

    return {
        "session_id": session_id,
        "status": "queued"
    }

# 查询状态工具
@tool("get_analysis_status")
async def get_analysis_status(token, session_id):
    session_data = session_manager.get(session_id)

    if session_data.status == "completed":
        return {
            "session_id": session_id,
            "status": "completed",
            "result": session_data.result  # JSON 结果
        }
    elif session_data.status == "processing":
        return {
            "session_id": session_id,
            "status": "processing",
            "progress": session_data.progress
        }
    else:
        return {
            "session_id": session_id,
            "status": session_data.status
        }

# 输出: 对于 Excel 文件，提供下载 URL
@tool("export_result")
async def export_result(token, session_id, format="excel"):
    session_data = session_manager.get(session_id)
    output_excel = generate_excel(session_data.result)

    # 保存到临时目录
    temp_file_path = save_temp_file(output_excel, session_id)

    return {
        "session_id": session_id,
        "filename": f"result_{session_id}.xlsx",
        "download_url": f"http://localhost:8021/download/{session_id}.xlsx",
        "file_size": len(output_excel)
    }
```

### 3. 如何实现客户端编排

```python
# 客户端（前端/Claude Desktop）负责编排

# 方式 A: 直接上传文件（适合小文件）
import time

# 步骤 1: 读取文件
with open("data.xlsx", "rb") as f:
    file_data = f.read()

# 步骤 2: 分析 Excel（异步）
result = excel_mcp.excel_analyze(token, file=file_data, filename="data.xlsx")
excel_session_id = result["session_id"]  # "session_abc123"

# 轮询查询分析状态
while True:
    status = excel_mcp.excel_get_status(token, session_id=excel_session_id)
    if status["status"] == "completed":
        analysis_result = status["result"]
        break
    elif status["status"] == "failed":
        raise Exception(status["error"])
    time.sleep(2)  # 等待 2 秒后重试

# 步骤 3: 拆分任务（传入原始 Excel 文件或 URL）
result = task_mcp.task_split(
    token,
    file=file_data,  # 直接传入文件，或使用 excel_url
    source_lang=None,  # 自动检测
    target_langs=["TR", "TH", "PT"],
    extract_context=True
)
task_session_id = result["session_id"]  # "task_session_xyz789"

# 轮询查询拆分状态
while True:
    status = task_mcp.task_get_split_status(token, session_id=task_session_id)
    if status["status"] == "completed":
        split_result = status["result"]
        print(f"拆分完成! 共 {split_result['task_count']} 个任务")
        break
    elif status["status"] == "failed":
        raise Exception(status["error"])
    time.sleep(2)

# 导出任务为 Excel 文件
export_result = task_mcp.task_export(token, session_id=task_session_id)
tasks_excel_url = export_result["download_url"]  # "http://localhost:8022/download/task_session_xyz789.xlsx"

# 步骤 4: 执行翻译（传入任务 Excel URL）
result = llm_mcp.llm_translate_excel(
    token,
    excel_url=tasks_excel_url,  # 使用 task_mcp 导出的 Excel URL
    provider="openai",
    model="gpt-4"
)
llm_session_id = result["session_id"]  # "llm_session_abc123"

# 轮询查询翻译状态
while True:
    status = llm_mcp.llm_get_translate_status(token, session_id=llm_session_id)
    print(f"翻译进度: {status['progress']}%")
    if status["status"] == "completed":
        download_url = status["result"]["download_url"]
        print(f"翻译完成! 下载链接: {download_url}")
        break
    elif status["status"] == "failed":
        raise Exception(status["error"])
    time.sleep(5)

# 步骤 5: 下载翻译结果
download_result = llm_mcp.llm_download_result(token, session_id=llm_session_id)
# 或直接使用 HTTP 客户端下载
import requests
response = requests.get(download_url)
with open("translated.xlsx", "wb") as f:
    f.write(response.content)


# 方式 B: 使用 storage_mcp + URL 传递（适合大文件）
# 步骤 1: 上传到 storage
storage_result = storage_mcp.storage_upload(token, file_data, filename="data.xlsx")
file_url = storage_result["file_url"]  # "http://oss.example.com/files/abc123/data.xlsx"

# 步骤 2-4: 使用 file_url（异步模式相同）
excel_result = excel_mcp.excel_analyze(token, file_url=file_url)
# 轮询 excel_mcp.excel_get_status(...)

task_result = task_mcp.task_split(token, excel_url=file_url, target_langs=["TR"])
# 轮询 task_mcp.task_get_split_status(...)

llm_result = llm_mcp.llm_translate_excel(token, excel_url=file_url, provider="openai")
# 轮询 llm_mcp.llm_get_translate_status(...)


# 方式 C: 混合场景 - 复用 Excel 文件 URL
# 如果同一个 Excel 需要多次处理（例如先分析，再拆分）
storage_result = storage_mcp.storage_upload(token, file_data, filename="data.xlsx")
excel_url = storage_result["file_url"]

# excel_mcp 分析
excel_result = excel_mcp.excel_analyze(token, file_url=excel_url)
# 轮询获取分析结果

# task_mcp 也使用相同的 Excel URL（不是 excel_session_id）
task_result = task_mcp.task_split(token, excel_url=excel_url, target_langs=["TR"])
# 轮询获取任务拆分结果，导出为 Excel URL
export_result = task_mcp.task_export(token, session_id=task_result["session_id"])
tasks_excel_url = export_result["download_url"]

# llm_mcp 使用 task_mcp 导出的 Excel URL
llm_result = llm_mcp.llm_translate_excel(token, excel_url=tasks_excel_url, provider="qwen")
# 轮询获取翻译结果
```

---

**版本**: V3.0（基于独立性重新设计）
**创建时间**: 2025-10-02
**更新时间**: 2025-10-02
**状态**: 📐 架构设计
