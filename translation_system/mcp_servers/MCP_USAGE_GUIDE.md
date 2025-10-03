# MCP Servers 使用指南

> 📘 **必读**: 请先阅读 [MCP_DESIGN_PRINCIPLES.md](./MCP_DESIGN_PRINCIPLES.md) 了解核心设计理念

## 🎯 概述

本文档展示如何使用 MCP Servers，包括独立使用和组合使用。

### 核心理念

- **客户端编排**: 工作流由客户端（前端/Claude Desktop）编排
- **数据通过 URL 传递**: MCP Server 之间不直接通信
- **独立运行**: 每个 MCP Server 可单独使用
- **通用能力**: 每个 MCP Server 适用多种场景

---

## 🚀 快速开始

### 1. 获取 Token

```bash
# 调用 backend_service 认证模块 (HTTP 服务，非 MCP Server)
curl -X POST http://localhost:9000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john@example.com",
    "password": "password123"
  }'

# 返回
{
  "access_token": "eyJhbGc...",
  "refresh_token": "rt_abc...",
  "token_type": "Bearer",
  "expires_in": 1800
}

# 保存 access_token 用于后续调用
export TOKEN="eyJhbGc..."
```

### 2. 独立使用 MCP Server

每个 MCP Server 都可以独立使用：

```python
# 示例 1: 单独使用 storage_mcp
result = storage_mcp.upload_file(
    token=TOKEN,
    file_name="report.xlsx",
    file_data=file_content
)
print(result["file_url"])

# 示例 2: 单独使用 excel_mcp
analysis = excel_mcp.analyze_structure(
    token=TOKEN,
    file_url="https://oss.../file.xlsx"
)
print(analysis)

# 示例 3: 单独使用 llm_mcp
summary = llm_mcp.summarize(
    token=TOKEN,
    text="Long article text...",
    max_length=200
)
print(summary)
```

### 3. 组合使用（客户端编排）

```python
# 完整工作流（Excel 翻译）

# 步骤 1: 上传文件
upload_result = storage_mcp.upload_file(
    token=TOKEN,
    file_data=excel_file
)
file_url = upload_result["file_url"]  # 获取 URL

# 步骤 2: 分析 Excel（传入 URL）
analysis_result = excel_mcp.analyze_structure(
    token=TOKEN,
    file_url=file_url  # 使用步骤 1 的 URL
)
analysis_url = analysis_result.get("analysis_url")

# 步骤 3: 拆分任务（传入 URL）
task_result = task_mcp.split_tasks(
    token=TOKEN,
    analysis_url=analysis_url  # 使用步骤 2 的 URL
)
tasks_url = task_result["tasks_url"]

# 步骤 4: 执行翻译（传入 URL）
translation_result = llm_mcp.translate(
    token=TOKEN,
    tasks_url=tasks_url  # 使用步骤 3 的 URL
)
result_url = translation_result["result_url"]

# 步骤 5: 下载结果
final_file = storage_mcp.download(
    token=TOKEN,
    file_url=result_url
)
```

---

## 📊 使用时序图

### 时序 1: 用户登录获取 Token

```
前端/Claude Desktop         backend_service           Database
      |                          |                          |
      |  1. POST /auth/login     |                          |
      |------------------------->|                          |
      |  {username, password}    |                          |
      |                          |  2. 查询用户             |
      |                          |------------------------->|
      |                          |  3. 返回用户数据         |
      |                          |<-------------------------|
      |                          |                          |
      |                          |  4. 验证密码             |
      |                          |  5. 生成 JWT Token       |
      |                          |  6. 签名（私钥）         |
      |                          |                          |
      |  7. 返回 Token           |                          |
      |<-------------------------|                          |
      |  {access_token,          |                          |
      |   refresh_token,         |                          |
      |   expires_in}            |                          |
      |                          |                          |
      | 8. 保存 Token 到本地     |                          |
```

**关键点**:
- backend_service 是统一的 HTTP 后端服务（不是 MCP Server）
- Token 包含用户信息、权限、资源配置、配额信息
- 客户端负责保存和管理 Token

---

### 时序 2: storage_mcp 独立使用（上传文件）

```
前端/Claude Desktop         storage_mcp              OSS         Redis
      |                          |                      |           |
      |  1. storage_upload       |                      |           |
      |------------------------->|                      |           |
      |  {token, file_data}      |                      |           |
      |                          |  2. JWT 自验证       |           |
      |                          |  (本地验证签名)      |           |
      |                          |                      |           |
      |                          |  3. 检查黑名单       |           |
      |                          |------------------------------------->|
      |                          |  4. 黑名单查询结果   |           |
      |                          |<-------------------------------------|
      |                          |                      |           |
      |                          |  5. 提取资源配置     |           |
      |                          |  (oss_prefix)        |           |
      |                          |                      |           |
      |                          |  6. 上传到 OSS       |           |
      |                          |  (自动添加prefix)    |           |
      |                          |--------------------->|           |
      |                          |  7. 返回 URL         |           |
      |                          |<---------------------|           |
      |                          |                      |           |
      |                          |  8. 更新配额         |           |
      |                          |------------------------------------->|
      |                          |                      |           |
      |  9. 返回结果             |                      |           |
      |<-------------------------|                      |           |
      |  {file_url}              |                      |           |
```

**关键点**:
- storage_mcp 独立运行，不依赖其他 MCP Server
- JWT 自验证（无需调用 auth_service）
- 从 Token 中提取 OSS 配置（自动隔离）

---

### 时序 3: excel_mcp 独立使用（异步分析 Excel）

```
前端/Claude Desktop         excel_mcp              HTTP Client    Session Manager
      |                          |                      |                |
      |  1. excel_analyze        |                      |                |
      |------------------------->|                      |                |
      |  {token, file_url}       |                      |                |
      |                          |  2. JWT 自验证       |                |
      |                          |                      |                |
      |                          |  3. 生成 session_id  |                |
      |                          |-------------------------------->|      |
      |                          |  4. 返回 session_id  |                |
      |  {session_id, status}    |                      |                |
      |<-------------------------|                      |                |
      |                          |                      |                |
      |                          |  5. 从 URL 下载文件  |                |
      |                          |--------------------->|                |
      |                          |  6. 返回文件数据     |                |
      |                          |<---------------------|                |
      |                          |                      |                |
      |                          |  7. 解析 Excel       |                |
      |                          |  8. 分析结构         |                |
      |                          |  9. 检测语言         |                |
      |                          |                      |                |
      |                          | 10. 保存到 session   |                |
      |                          |-------------------------------->|      |
      |                          |                      |                |
      | 11. 轮询查询状态         |                      |                |
      |  excel_get_status        |                      |                |
      |------------------------->|                      |                |
      |  {session_id}            |                      |                |
      |                          | 12. 查询 session     |                |
      |                          |<--------------------------------|      |
      |                          | 13. 返回结果         |                |
      |  {status, progress,      |                      |                |
      |   result}                |                      |                |
      |<-------------------------|                      |                |
```

**关键点**:
- excel_mcp 独立运行，不调用其他 MCP Server
- 使用 HTTP 客户端下载文件
- 异步处理：立即返回 session_id，后台处理
- 客户端轮询查询状态和结果
- Session 存储在内存中（不依赖 MySQL/Redis）

---

### 时序 4: 组合工作流（客户端异步编排）

```
前端/Claude Desktop    storage_mcp    excel_mcp    task_mcp    llm_mcp
      |                    |              |            |           |
      | 1. 上传文件        |              |            |           |
      |------------------->|              |            |           |
      |<-------------------|              |            |           |
      | {file_url}         |              |            |           |
      |                    |              |            |           |
      | 2. 分析 Excel      |              |            |           |
      |---------------------------------->|            |           |
      | (传入 file_url)    |              |            |           |
      |<----------------------------------|            |           |
      | {excel_session_id} |              |            |           |
      |                    |              |            |           |
      | 3. 轮询查询分析状态 |             |            |           |
      |---------------------------------->|            |           |
      |<----------------------------------|            |           |
      | {status, result}   |              |            |           |
      |                    |              |            |           |
      | 4. 拆分任务        |              |            |           |
      |------------------------------------------------>|           |
      | (传入 file_url)    |              |            |           |
      |<------------------------------------------------|           |
      | {task_session_id}  |              |            |           |
      |                    |              |            |           |
      | 5. 轮询拆分状态    |              |            |           |
      |------------------------------------------------>|           |
      |<------------------------------------------------|           |
      | {status, result}   |              |            |           |
      |                    |              |            |           |
      | 6. 导出任务 Excel  |              |            |           |
      |------------------------------------------------>|           |
      |<------------------------------------------------|           |
      | {tasks_excel_url}  |              |            |           |
      |                    |              |            |           |
      | 7. 执行翻译        |              |            |           |
      |------------------------------------------------------------>|
      | (传入 tasks_excel_url)            |            |           |
      |<------------------------------------------------------------|
      | {llm_session_id}   |              |            |           |
      |                    |              |            |           |
      | 8. 轮询翻译状态    |              |            |           |
      |------------------------------------------------------------>|
      |<------------------------------------------------------------|
      | {status, progress} |              |            |           |
      |                    |              |            |           |
      | 9. 下载翻译结果    |              |            |           |
      |------------------------------------------------------------>|
      |<------------------------------------------------------------|
      | {download_url}     |              |            |           |
```

**关键点**:
- 前端负责编排（串联各个 MCP Server）
- MCP Server 之间不直接通信
- 数据通过 URL 传递（不能跨 MCP Server 引用 session_id）
- 异步模式：提交任务 → 获取 session_id → 轮询状态
- 每个 MCP Server 独立管理自己的 session（内存存储）

---

## 📖 完整使用示例

### 场景 1: 数据分析（独立使用 excel_mcp）

```python
"""
场景: 分析销售报表 Excel
只使用 excel_mcp，不需要其他 MCP Server
"""

# 1. 获取 Token
response = requests.post("http://localhost:9000/login", json={
    "username": "analyst@company.com",
    "password": "password"
})
token = response.json()["access_token"]

# 2. 分析 Excel 结构
analysis = excel_mcp.analyze_structure(
    token=token,
    file_url="https://oss.../sales_report.xlsx"
)

print(f"工作表: {analysis['sheets']}")
print(f"总单元格: {analysis['total_cells']}")

# 3. 提取数据
data = excel_mcp.extract_data(
    token=token,
    file_url="https://oss.../sales_report.xlsx",
    parse_rules={
        "sheet": "Sheet1",
        "columns": {
            "product": "A",
            "revenue": "C",
            "quantity": "D"
        },
        "start_row": 2
    }
)

# 4. 转换为 JSON
json_data = excel_mcp.convert_to_json(
    token=token,
    file_url="https://oss.../sales_report.xlsx",
    options={"pretty": True}
)

# 完成！无需任何其他 MCP Server
```

---

### 场景 2: 文本摘要（独立使用 llm_mcp）

```python
"""
场景: 文章摘要
只使用 llm_mcp，不需要其他 MCP Server
"""

# 1. 获取 Token
token = get_token()

# 2. 调用摘要
summary = llm_mcp.summarize(
    token=token,
    text="""
    Long article content here...
    Multiple paragraphs...
    """,
    options={
        "max_length": 200,
        "language": "zh",
        "provider": "openai",
        "model": "gpt-4"
    }
)

print(summary["summary"])
print(f"成本: {summary['cost']} credits")

# 完成！只用了 llm_mcp
```

---

### 场景 3: Excel 翻译（组合使用，异步模式）

```python
"""
场景: Excel 文件翻译
组合使用: storage_mcp + excel_mcp + task_mcp + llm_mcp
模式: 异步处理 + 轮询查询
"""
import time

# 客户端编排类
class TranslationWorkflow:
    def __init__(self, token):
        self.token = token

    def execute(self, file_path):
        # 步骤 1: 上传文件
        print("上传文件...")
        with open(file_path, "rb") as f:
            upload_result = storage_mcp.storage_upload(
                token=self.token,
                file_name=os.path.basename(file_path),
                file_data=f.read()
            )
        file_url = upload_result["file_url"]
        print(f"✓ 文件 URL: {file_url}")

        # 步骤 2: 分析 Excel（异步）
        print("分析 Excel 结构...")
        excel_result = excel_mcp.excel_analyze(
            token=self.token,
            file_url=file_url
        )
        excel_session_id = excel_result["session_id"]

        # 轮询查询分析状态
        while True:
            status = excel_mcp.excel_get_status(
                token=self.token,
                session_id=excel_session_id
            )
            if status["status"] == "completed":
                analysis = status["result"]
                print(f"✓ 检测到 {analysis['statistics']['estimated_tasks']} 个任务")
                break
            elif status["status"] == "failed":
                raise Exception(f"分析失败: {status['error']}")
            time.sleep(2)

        # 步骤 3: 拆分任务（异步）
        print("拆分翻译任务...")
        task_result = task_mcp.task_split(
            token=self.token,
            excel_url=file_url,  # 传入原始文件 URL
            source_lang=None,  # 自动检测
            target_langs=["TR", "TH"],
            extract_context=True
        )
        task_session_id = task_result["session_id"]

        # 轮询查询拆分状态
        while True:
            status = task_mcp.task_get_split_status(
                token=self.token,
                session_id=task_session_id
            )
            if status["status"] == "completed":
                split_result = status["result"]
                print(f"✓ 拆分为 {split_result['batch_count']} 个批次")
                break
            elif status["status"] == "failed":
                raise Exception(f"拆分失败: {status['error']}")
            time.sleep(2)

        # 导出任务为 Excel
        export_result = task_mcp.task_export(
            token=self.token,
            session_id=task_session_id
        )
        tasks_excel_url = export_result["download_url"]

        # 步骤 4: 执行翻译（异步）
        print("执行 LLM 翻译...")
        llm_result = llm_mcp.llm_translate_excel(
            token=self.token,
            excel_url=tasks_excel_url,  # 使用导出的任务 Excel
            provider="openai",
            model="gpt-4",
            translation_config={
                "temperature": 0.3,
                "max_retries": 3
            }
        )
        llm_session_id = llm_result["session_id"]

        # 轮询查询翻译状态
        while True:
            status = llm_mcp.llm_get_translate_status(
                token=self.token,
                session_id=llm_session_id
            )
            progress = status.get("progress", 0)
            print(f"翻译进度: {progress}%")

            if status["status"] == "completed":
                result = status["result"]
                print(f"✓ 翻译完成，成本: {result['cost']} credits")
                download_url = result["download_url"]
                break
            elif status["status"] == "failed":
                raise Exception(f"翻译失败: {status['error']}")
            time.sleep(5)

        # 步骤 5: 下载结果
        print("下载翻译结果...")
        import requests
        response = requests.get(download_url)

        # 保存到本地
        output_path = file_path.replace(".xlsx", "_translated.xlsx")
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"✓ 保存到: {output_path}")

        return output_path

# 使用
token = get_token()
workflow = TranslationWorkflow(token)
result_file = workflow.execute("input.xlsx")
```

---

## 🔐 Token 使用最佳实践

### 1. Token 管理

```python
class TokenManager:
    def __init__(self, backend_url="http://localhost:9000"):
        self.backend_url = backend_url
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None

    def login(self, username, password):
        """登录获取 Token"""
        response = requests.post(f"{self.backend_url}/auth/login", json={
            "username": username,
            "password": password
        })
        data = response.json()

        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.expires_at = time.time() + data["expires_in"]

        return self.access_token

    def get_token(self):
        """获取有效的 Token（自动刷新）"""
        # 检查是否即将过期（5分钟内）
        if self.expires_at - time.time() < 300:
            self.refresh()

        return self.access_token

    def refresh(self):
        """刷新 Token"""
        response = requests.post(f"{self.backend_url}/auth/refresh", json={
            "refresh_token": self.refresh_token
        })
        data = response.json()

        self.access_token = data["access_token"]
        self.expires_at = time.time() + data["expires_in"]

        return self.access_token

# 使用
token_manager = TokenManager("http://localhost:9000")
token_manager.login("user@example.com", "password")

# 后续调用自动使用有效 Token
token = token_manager.get_token()
result = excel_mcp.analyze(token=token, file_url="...")
```

### 2. Token 验证失败处理

```python
def call_mcp_tool_with_retry(tool_func, *args, **kwargs):
    """带重试的 MCP 工具调用"""
    try:
        return tool_func(*args, **kwargs)

    except TokenExpiredError:
        # Token 过期，刷新后重试
        print("Token 过期，刷新中...")
        kwargs["token"] = token_manager.refresh()
        return tool_func(*args, **kwargs)

    except TokenRevokedError:
        # Token 被撤销，需要重新登录
        print("Token 已被撤销，请重新登录")
        raise

    except PermissionDeniedError as e:
        # 权限不足
        print(f"权限不足: {e}")
        raise

# 使用
result = call_mcp_tool_with_retry(
    excel_mcp.analyze,
    token=token,
    file_url="..."
)
```

---

## 📊 多租户使用示例

### 场景: 两个租户同时使用

```python
"""
租户 A 和租户 B 同时使用同一套 MCP Servers
数据完全隔离
"""

# 租户 A 登录
response_a = requests.post("http://localhost:9000/auth/login", json={
    "username": "user@tenant-a.com",
    "password": "password"
})
token_a = response_a.json()["access_token"]
# Token A 包含:
# - tenant_id: "tenant_a"
# - resources.oss.prefix: "tenants/a/users/001/"

# 租户 B 登录
response_b = requests.post("http://localhost:9000/auth/login", json={
    "username": "user@tenant-b.com",
    "password": "password"
})
token_b = response_b.json()["access_token"]
# Token B 包含:
# - tenant_id: "tenant_b"
# - resources.oss.prefix: "tenants/b/users/002/"

# 租户 A 上传文件
result_a = storage_mcp.upload_file(
    token=token_a,
    file_data=file_a
)
# 文件自动保存到: tenants/a/users/001/...

# 租户 B 上传文件
result_b = storage_mcp.upload_file(
    token=token_b,
    file_data=file_b
)
# 文件自动保存到: tenants/b/users/002/...

# 数据隔离验证:
# 租户 A 无法访问租户 B 的文件
try:
    storage_mcp.download(
        token=token_a,  # 租户 A 的 Token
        file_url=result_b["file_url"]  # 租户 B 的文件
    )
except PermissionDeniedError:
    print("✓ 数据隔离正常，租户 A 无法访问租户 B 的文件")
```

---

## ⚡ 性能优化

### 1. 批量操作

```python
# ❌ 低效: 逐个上传
for file in files:
    storage_mcp.upload_file(token=token, file_data=file)

# ✅ 高效: 批量上传
storage_mcp.upload_batch(
    token=token,
    files=[
        {"file_name": "file1.xlsx", "file_data": data1},
        {"file_name": "file2.xlsx", "file_data": data2},
        {"file_name": "file3.xlsx", "file_data": data3}
    ]
)
```

### 2. 并行执行

```python
import asyncio

async def process_multiple_files(token, file_urls):
    # 并行分析多个 Excel 文件
    tasks = [
        excel_mcp.analyze_async(token=token, file_url=url)
        for url in file_urls
    ]

    results = await asyncio.gather(*tasks)
    return results

# 使用
file_urls = ["url1", "url2", "url3"]
results = asyncio.run(process_multiple_files(token, file_urls))
```

### 3. 使用缓存

```python
# excel_mcp 内部会缓存分析结果
# 相同文件的重复分析会从缓存读取

# 第一次: 实际分析（需要时间）
result1 = excel_mcp.analyze(token=token, file_url="file.xlsx")

# 第二次: 从缓存读取（快速）
result2 = excel_mcp.analyze(token=token, file_url="file.xlsx")

# 清除缓存（如果文件已更新）
excel_mcp.clear_cache(token=token, file_url="file.xlsx")
```

---

## 🔍 故障排查

### 1. Token 认证失败

```python
# 错误: "Invalid token"

# 排查步骤:
# 1. 检查 Token 格式
print(f"Token: {token[:20]}...")  # 应该是 "eyJhbGc..."

# 2. 解码 Token 查看内容
import jwt
payload = jwt.decode(token, options={"verify_signature": False})
print(f"过期时间: {payload['exp']}")
print(f"当前时间: {time.time()}")

# 3. 检查是否过期
if payload["exp"] < time.time():
    print("Token 已过期，需要刷新")
    token = token_manager.refresh()

# 4. 检查黑名单（如果有 Redis 访问权限）
import redis
r = redis.Redis()
if r.exists(f"blacklist:{token}"):
    print("Token 已被撤销，需要重新登录")
```

### 2. 文件访问失败

```python
# 错误: "File not found"

# 排查步骤:
# 1. 检查 URL 是否正确
print(f"File URL: {file_url}")

# 2. 检查 Token 的资源配置
payload = jwt.decode(token, options={"verify_signature": False})
oss_prefix = payload["resources"]["oss"]["prefix"]
print(f"OSS Prefix: {oss_prefix}")

# 3. 确认文件路径是否匹配
# Token 的 prefix: "tenants/a/users/001/"
# 文件 URL: "https://oss.../tenants/a/users/001/file.xlsx" ✓
# 文件 URL: "https://oss.../tenants/b/users/002/file.xlsx" ✗

# 4. 列出文件
files = storage_mcp.list(token=token, prefix="excel-files/")
print(f"可访问的文件: {files}")
```

### 3. 权限不足

```python
# 错误: "Permission denied"

# 排查步骤:
# 1. 检查 Token 的权限
payload = jwt.decode(token, options={"verify_signature": False})
permissions = payload["permissions"]
print(f"权限列表: {permissions}")

# 2. 确认所需权限
# excel_mcp.analyze 需要: "excel:analyze"
if not permissions.get("excel:analyze"):
    print("缺少 'excel:analyze' 权限")

# 3. 联系管理员分配权限
```

---

## ✅ 使用检查清单

### 开始使用前
- [ ] 已安装所需的 MCP Server（如 `pip install excel-mcp-server`）
- [ ] backend_service 正在运行（http://localhost:9000）
- [ ] 已创建用户账号
- [ ] 已获取有效的 access_token
- [ ] 了解 Token 的过期时间（通常 30 分钟）

### 每次调用 MCP 工具
- [ ] 携带有效的 Token
- [ ] Token 未过期
- [ ] 拥有所需权限
- [ ] 参数符合 inputSchema
- [ ] 使用 URL 而非直接传递大数据

### 组合使用时
- [ ] 客户端负责编排（不期望 MCP Server 相互调用）
- [ ] 数据通过 URL 传递
- [ ] 保存中间结果的 URL 用于下一步
- [ ] 处理错误和重试

---

## 🎓 最佳实践总结

### 1. 独立使用原则

每个 MCP Server 都应该能够独立使用：

```python
# ✅ 好的设计
# 只用 excel_mcp，不依赖其他服务
excel_mcp.analyze(token, file_url)

# ❌ 不好的设计
# 期望 excel_mcp 内部调用 storage_mcp
excel_mcp.analyze(token, file_id)  # file_id 需要内部调用 storage_mcp
```

### 2. 客户端编排原则

工作流由客户端编排，而非服务器端：

```python
# ✅ 好的设计
# 客户端明确编排每一步
file_url = storage_mcp.upload(...)
analysis = excel_mcp.analyze(file_url)
tasks = task_mcp.split(analysis)
result = llm_mcp.translate(tasks)

# ❌ 不好的设计
# 期望一个工具完成所有步骤
result = translation_mcp.translate_excel(file_data)  # 内部调用太多服务
```

### 3. URL 传递原则

使用 URL 传递数据，而非直接传递大数据：

```python
# ✅ 好的设计
@tool("analyze_excel")
def analyze_excel(token, file_url):  # 输入 URL
    data = oss_client.download(file_url)  # 自己下载
    result = do_analysis(data)

    if len(result) > 1MB:
        result_url = save_result(result)  # 保存后返回 URL
        return {"analysis_url": result_url}
    else:
        return {"analysis": result}  # 小数据直接返回

# ❌ 不好的设计
@tool("analyze_excel")
def analyze_excel(token, file_data):  # 直接传大数据
    result = do_analysis(file_data)
    return {"analysis": result}  # 直接返回大数据
```

---

**版本**: V3.0（基于独立性重新设计）
**创建时间**: 2025-10-02
**更新时间**: 2025-10-02
**状态**: 📖 使用指南
