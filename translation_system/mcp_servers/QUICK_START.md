# MCP 服务器快速启动指南

## 快速开始（5分钟）

### 1. 启动 backend_service (认证服务)

```bash
cd /mnt/d/work/trans_excel/translation_system/mcp_servers/backend_service
python3 server.py
```

**服务信息**:
- 端口: `9000`
- 功能: Token验证、用户认证、配额管理
- 健康检查: `http://localhost:9000/health`

### 2. 启动 excel_mcp (HTTP模式)

```bash
cd /mnt/d/work/trans_excel/translation_system/mcp_servers/excel_mcp
python3 server.py --http
```

**服务信息**:
- 端口: `8021`
- 功能: Excel分析、解析、转换
- 测试页面: `http://localhost:8021/static/index.html`

### 3. 使用测试Token

在测试页面的 Token 输入框中填入：
```
test_token_123
```

### 4. 上传Excel文件测试

1. 访问 `http://localhost:8021/static/index.html`
2. 输入 token: `test_token_123`
3. 点击 "Upload File" 选项卡
4. 拖拽或选择一个 Excel 文件
5. 点击 "Analyze" 按钮
6. 查看分析结果

---

## 详细说明

### Token 验证流程

```
用户请求 → excel_mcp → backend_service:9000/auth/validate → 返回用户信息
```

### Token 配置文件

位置: `/mnt/d/work/trans_excel/translation_system/mcp_servers/backend_service/tokens.json`

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

### 添加新的测试Token

1. 编辑 `backend_service/tokens.json`
2. 在 `fixed_tokens` 中添加新的 token
3. 重新加载配置：
```bash
curl -X POST http://localhost:9000/auth/reload_config
```

---

## 服务端口总览

| 服务 | 端口 | 用途 | 启动命令 |
|-----|------|------|---------|
| backend_service | 9000 | 认证/计费 | `python3 server.py` |
| storage_mcp | 8020 | 文件存储 | `python3 server.py --http` |
| excel_mcp | 8021 | Excel处理 | `python3 server.py --http` |
| task_mcp | 8022 | 任务拆分 | `python3 server.py --http` |
| llm_mcp | 8023 | LLM翻译 | `python3 server.py --http` |

---

## 运行模式

### stdio 模式 (用于 Claude Desktop)

```bash
python3 server.py
```

- 通过标准输入/输出通信
- 集成到 Claude Desktop 配置文件
- 用于 AI助手调用

### HTTP 模式 (用于 Web 测试)

```bash
python3 server.py --http                # 使用默认端口
python3 server.py --http --port=8888   # 自定义端口
```

- 启动 HTTP 服务器
- 提供 `/mcp/tool` API 接口
- 自动服务静态测试页面
- 支持 CORS 跨域

---

## API 调用示例

### 1. 验证 Token

```bash
curl -X POST http://localhost:9000/auth/validate \
  -H "Content-Type: application/json" \
  -d '{"token": "test_token_123"}'
```

响应：
```json
{
  "valid": true,
  "payload": {
    "user_id": "test_user",
    "tenant_id": "test_tenant",
    "permissions": {...},
    "quota": {...}
  }
}
```

### 2. 分析 Excel

```bash
curl -X POST http://localhost:8021/mcp/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "excel_analyze",
    "arguments": {
      "token": "test_token_123",
      "file_url": "https://example.com/test.xlsx"
    }
  }'
```

响应：
```json
{
  "session_id": "excel_abc123",
  "status": "queued",
  "message": "Analysis task submitted"
}
```

### 3. 查询分析状态

```bash
curl -X POST http://localhost:8021/mcp/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "excel_get_status",
    "arguments": {
      "token": "test_token_123",
      "session_id": "excel_abc123"
    }
  }'
```

响应：
```json
{
  "session_id": "excel_abc123",
  "status": "completed",
  "progress": 100,
  "result": {
    "file_info": {...},
    "statistics": {...}
  }
}
```

---

## 常见问题

### Q1: Token 验证失败

**错误**: `Token validation failed: Invalid token: Not enough segments`

**原因**: backend_service 未启动或 token 配置未加载

**解决**:
1. 确保 backend_service 已启动：`curl http://localhost:9000/health`
2. 重新加载配置：`curl -X POST http://localhost:9000/auth/reload_config`

### Q2: 无法访问测试页面

**错误**: `ERR_CONNECTION_REFUSED`

**解决**:
1. 确认使用 `--http` 参数启动服务
2. 检查端口是否被占用：`lsof -i:8021`
3. 查看服务日志确认启动成功

### Q3: CORS 错误

**错误**: `No 'Access-Control-Allow-Origin' header`

**解决**:
- HTTP 模式已自动配置 CORS
- 确保使用 HTTP 模式启动：`python3 server.py --http`

---

## 下一步

1. 📖 查看完整文档：[MCP_SERVERS_DESIGN.md](./MCP_SERVERS_DESIGN.md)
2. 📋 了解 Token 配置：[backend_service/TOKENS_DESIGN.md](./backend_service/TOKENS_DESIGN.md)
3. 🔧 查看开发路线图：[DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md)
4. 📚 学习使用指南：[MCP_USAGE_GUIDE.md](./MCP_USAGE_GUIDE.md)
