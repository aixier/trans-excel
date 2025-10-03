# Tokens 配置文件设计说明

## 文件位置
`/mnt/d/work/trans_excel/translation_system/mcp_servers/backend_service/tokens.json`

## 设计目标

**统一的 Token 管理**：
- 所有 MCP Server 的 token 验证统一通过 `backend_service:9000/auth/validate` API
- 避免各 MCP Server 重复实现验证逻辑
- 集中管理用户权限、配额、资源隔离

---

## 字段说明

### 1. `secret_key` (字符串)

**用途**: JWT token 的加密密钥

**说明**:
- 用于生成和验证 JWT token
- 开发环境使用默认值 `"dev-secret-key-change-in-production"`
- **生产环境必须修改为强密钥**

**示例**:
```json
"secret_key": "dev-secret-key-change-in-production"
```

---

### 2. `fixed_tokens` (对象)

**用途**: 固定 token 配置（用于开发测试）

**说明**:
- Key: token 字符串（直接作为认证凭证使用）
- Value: token 对应的用户信息和权限配置
- 适合开发测试，无需生成 JWT
- 前端/测试工具直接使用 token 字符串即可

**为什么需要 fixed_tokens**:
- 简化开发测试流程（无需生成 JWT）
- 便于调试和演示
- 可以快速配置多个测试用户

**示例**:
```json
"fixed_tokens": {
  "test_token_123": { /* 用户配置 */ }
}
```

**使用方式**:
```bash
# 直接使用 token 字符串
curl -X POST http://localhost:9000/auth/validate \
  -H "Content-Type: application/json" \
  -d '{"token": "test_token_123"}'
```

---

### 3. Token 配置字段（每个 token 的详细配置）

#### 3.1 `user_id` (字符串)

**用途**: 用户唯一标识符

**说明**:
- 全局唯一的用户 ID
- 用于标识具体用户
- 日志、审计、数据隔离的关键字段

**示例**:
```json
"user_id": "test_user"
```

---

#### 3.2 `tenant_id` (字符串)

**用途**: 租户（多租户）唯一标识符

**说明**:
- 实现多租户架构的关键字段
- 同一租户下的用户共享资源池
- 数据隔离、配额管理的基础

**多租户场景**:
- `tenant_dev`: 开发租户
- `tenant_company_a`: 公司 A 的租户
- `tenant_company_b`: 公司 B 的租户

**示例**:
```json
"tenant_id": "test_tenant"
```

---

#### 3.3 `username` (字符串)

**用途**: 用户可读名称（邮箱/用户名）

**说明**:
- 人类可读的用户标识
- 通常是邮箱地址
- 用于日志显示、通知等

**示例**:
```json
"username": "test@example.com"
```

---

#### 3.4 `permissions` (对象)

**用途**: 用户权限配置（细粒度权限控制）

**说明**:
- Key: 权限名称（格式：`服务:操作`）
- Value: 布尔值（`true` = 有权限，`false` = 无权限）
- 实现基于角色的访问控制（RBAC）

**权限命名规范**:
```
<service>:<action>

service: 服务名（storage, excel, task, llm）
action:  操作名（read, write, analyze, translate, split）
```

**所有可用权限**:
| 权限名称 | 说明 | 对应 MCP Server |
|---------|------|----------------|
| `storage:read` | 文件读取 | storage_mcp |
| `storage:write` | 文件写入 | storage_mcp |
| `excel:analyze` | Excel 分析 | excel_mcp |
| `task:split` | 任务拆分 | task_mcp |
| `llm:translate` | LLM 翻译 | llm_mcp |

**示例**:
```json
"permissions": {
  "storage:read": true,      // 可以读取文件
  "storage:write": true,     // 可以上传文件
  "excel:analyze": true,     // 可以分析 Excel
  "task:split": true,        // 可以拆分任务
  "llm:translate": true      // 可以调用翻译
}
```

**使用场景**:
```python
# MCP Server 中检查权限
if not token_validator.check_permission(payload, 'excel:analyze'):
    return {"error": "Permission denied"}
```

---

#### 3.5 `resources` (对象)

**用途**: 用户的资源隔离配置

**说明**:
- 定义用户可以访问的资源范围
- 实现多租户数据隔离
- 每个用户只能访问自己的资源

**子字段说明**:

##### 3.5.1 `resources.oss` (对象存储配置)

| 字段 | 说明 | 示例 |
|-----|------|------|
| `provider` | 存储服务商 | `"local"`, `"aliyun"`, `"aws"` |
| `bucket` | 存储桶名称 | `"test-bucket"` |
| `prefix` | 文件路径前缀 | `"test/"`, `"tenants/dev/users/001/"` |

**作用**:
- 文件上传时自动添加前缀
- 文件下载时只能访问前缀内的文件
- 实现文件级别的隔离

**示例**:
```json
"oss": {
  "provider": "local",
  "bucket": "test-bucket",
  "prefix": "test/"
}
```

**实际效果**:
```python
# 用户上传文件 "myfile.xlsx"
# 实际存储路径: "test/myfile.xlsx"

# 用户只能访问 "test/" 开头的文件
# 无法访问其他租户的文件（如 "prod/"）
```

##### 3.5.2 `resources.mysql` (可选，数据库隔离)

| 字段 | 说明 | 示例 |
|-----|------|------|
| `schema` | 数据库 schema | `"tenant_dev"`, `"tenant_prod"` |

**作用**:
- 多租户数据库隔离
- 每个租户使用独立的 schema

**示例**:
```json
"mysql": {
  "schema": "tenant_test"
}
```

##### 3.5.3 `resources.redis` (可选，缓存隔离)

| 字段 | 说明 | 示例 |
|-----|------|------|
| `prefix` | Redis key 前缀 | `"test:"`, `"dev:001:"` |

**作用**:
- Redis key 隔离
- 避免不同用户的缓存冲突

**示例**:
```json
"redis": {
  "prefix": "test:"
}
```

---

#### 3.6 `quota` (对象)

**用途**: 用户配额限制

**说明**:
- 限制用户资源使用量
- 实现计费和配额管理
- 防止滥用

**子字段说明**:

| 字段 | 说明 | 单位 | 示例值 |
|-----|------|-----|-------|
| `llm_credits` | LLM 调用额度 | credits | `100000` |
| `storage_mb` | 存储空间限制 | MB | `5000` (5GB) |

**示例**:
```json
"quota": {
  "llm_credits": 100000,    // 10万 credits
  "storage_mb": 5000        // 5GB 存储空间
}
```

**使用场景**:
```python
# 扣除 LLM 配额
if user_quota.llm_credits < cost:
    return {"error": "Insufficient credits"}

user_quota.llm_credits -= cost
```

---

## 完整示例

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

---

## Token 验证流程

```
1. 前端/MCP Client 发送请求
   ↓
   headers: { token: "test_token_123" }

2. MCP Server (如 excel_mcp)
   ↓
   调用 backend_service:9000/auth/validate

3. backend_service
   ↓
   - 读取 tokens.json
   - 查找 fixed_tokens["test_token_123"]
   - 返回用户信息和权限

4. MCP Server
   ↓
   - 检查权限 (permissions)
   - 检查配额 (quota)
   - 使用资源配置 (resources)
   - 执行业务逻辑
```

---

## 使用方式

### 1. 前端使用固定 token

```javascript
// 在 HTML 页面的 token 输入框中填入
test_token_123

// 或带 Bearer 前缀
Bearer test_token_123
```

### 2. 添加新的测试用户

编辑 `tokens.json`:
```json
"fixed_tokens": {
  "test_token_123": { /* 现有用户 */ },
  "admin_token_456": {
    "user_id": "admin_001",
    "tenant_id": "admin_tenant",
    "username": "admin@example.com",
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
        "bucket": "admin-bucket",
        "prefix": "admin/"
      }
    },
    "quota": {
      "llm_credits": 1000000,
      "storage_mb": 50000
    }
  }
}
```

重新加载配置:
```bash
curl -X POST http://localhost:9000/auth/reload_config
```

---

## 安全建议

1. **生产环境**:
   - 修改 `secret_key` 为强密钥
   - 使用 JWT token 而非固定 token
   - 定期轮换密钥

2. **权限最小化**:
   - 只授予必需的权限
   - 定期审计权限配置

3. **配额管理**:
   - 设置合理的配额限制
   - 监控配额使用情况

4. **文件保护**:
   - tokens.json 不应提交到 git
   - 设置文件权限为 600
   - 生产环境使用环境变量或密钥管理服务
