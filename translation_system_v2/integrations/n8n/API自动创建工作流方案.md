# 🚀 通过 n8n REST API 自动创建工作流（终极方案）

## ✅ 解决的问题

之前遇到的所有问题：
- ❌ JSON 导入后 webhook 不注册
- ❌ "Unused Respond to Webhook" 错误
- ❌ 手动创建太麻烦
- ❌ 表单 URL 无法访问

**现在通过 n8n REST API 实现 100% 自动化！**

---

## 📋 前提条件

### 1. Backend_v2 独立运行

Backend_v2 **不在** docker-compose 中，需要单独启动：

```bash
# 在 backend_v2 目录
cd /mnt/d/work/trans_excel/translation_system_v2/backend_v2
python3 main.py
```

确认运行：
```bash
curl http://localhost:8013/health
```

### 2. 启动 n8n 容器

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/docker
docker-compose up -d
```

确认运行：
```bash
curl http://localhost:5678/healthz
```

---

## 🎯 一键自动创建工作流

### 方法1: 直接运行脚本（推荐）

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/scripts
python3 auto_create_via_api.py
```

### 方法2: 使用环境变量

```bash
export N8N_API_KEY=n8n_api_Trans2024SecureKey_98765
export N8N_HOST=localhost
export N8N_PORT=5678

python3 auto_create_via_api.py
```

---

## 📊 脚本执行流程

脚本会自动完成以下步骤：

### [步骤1] 健康检查
- ✅ 检查 n8n 服务状态
- ✅ 检查 backend 服务状态

### [步骤2] 清理旧工作流
- 🗑️ 自动删除所有包含"翻译"的旧工作流
- 🗑️ 避免重复和冲突

### [步骤3] 创建新工作流
- 📝 通过 API POST `/api/v1/workflows`
- 📝 创建完整的 3 节点工作流：
  - **表单节点**: Form Trigger
  - **API 节点**: HTTP Request 调用 backend
  - **响应节点**: Respond to Webhook

### [步骤4] 激活工作流
- 🚀 通过 API PATCH `/api/v1/workflows/{id}`
- 🚀 设置 `active: true`

### [步骤5] 获取表单 URL
- 📋 自动提取 webhook ID
- 📋 生成表单访问地址

---

## 🎉 预期输出

成功后会看到：

```
============================================================
🤖 n8n 工作流自动创建脚本
   通过 REST API 实现完全自动化
============================================================

[步骤1] 健康检查...
✅ n8n 服务运行正常
✅ 后端服务运行正常

[步骤2] 清理旧工作流...
🗑️  删除已存在的工作流: 最终翻译表单 (ID: abc123)
   ✅ 已删除
✅ 已删除 1 个旧工作流

[步骤3] 创建新工作流...
📝 正在创建工作流...
✅ 工作流创建成功！
   工作流ID: xyz789
   工作流名称: Excel翻译表单_自动创建

[步骤4] 激活工作流...
🚀 正在激活工作流 xyz789...
✅ 工作流已激活！

[步骤5] 获取表单访问地址...

============================================================
🎉 工作流创建成功！
============================================================
工作流ID: xyz789
工作流名称: Excel翻译表单_自动创建
激活状态: ✅ 已激活

📋 表单访问地址:
   http://localhost:5678/form/abc-def-123-456

💡 使用方法:
   1. 在浏览器访问上述URL
   2. 上传Excel文件
   3. 选择目标语言
   4. 提交后保存返回的session_id
   5. 使用session_id查询状态和下载结果

============================================================

✅ 自动化创建完成！
```

---

## 📝 工作流配置详情

### 表单字段配置

| 字段名称 | 类型 | 是否必填 | 说明 |
|---------|------|---------|------|
| Excel文件 | File | ✅ | 上传待翻译的Excel文件 |
| 目标语言 | Dropdown | ✅ | 选项：英文(EN)、泰文(TH)、日文(JP)、韩文(KR) |
| 术语库 | Text | ❌ | 可选，留空使用默认术语库 |

### API 调用配置

- **URL**: `http://backend:8013/api/tasks/split`
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Parameters**:
  - `file`: 上传的Excel文件
  - `source_lang`: CH（固定）
  - `target_langs`: 表单选择的目标语言
  - `glossary_name`: 术语库名称（默认 default）

### 响应格式

```json
{
  "success": true,
  "session_id": "abc-123-def-456",
  "message": "任务已创建",
  "status_url": "http://localhost:8013/api/tasks/split/status/abc-123-def-456",
  "download_url": "http://localhost:8013/api/download/abc-123-def-456",
  "tips": "请保存session_id，完成后访问download_url下载结果"
}
```

---

## 🔧 技术细节

### n8n REST API 配置

在 `.env` 文件中已配置：
```bash
N8N_API_KEY=n8n_api_Trans2024SecureKey_98765
```

在 `docker-compose.yml` 中启用：
```yaml
- N8N_API_KEY_ENABLED=true
- N8N_API_KEY=${N8N_API_KEY}
```

### API 认证

所有 API 请求使用 Header 认证：
```
X-N8N-API-KEY: n8n_api_Trans2024SecureKey_98765
```

### API 端点

- **创建工作流**: `POST /api/v1/workflows`
- **激活工作流**: `PATCH /api/v1/workflows/{id}`
- **获取工作流**: `GET /api/v1/workflows/{id}`
- **删除工作流**: `DELETE /api/v1/workflows/{id}`
- **列出工作流**: `GET /api/v1/workflows`

---

## 🐛 故障排查

### 1. API 认证失败

**错误**: `401 Unauthorized`

**解决**:
```bash
# 检查 .env 文件中的 API Key
cat /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/docker/.env | grep N8N_API_KEY

# 重启 n8n 容器
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/docker
docker-compose restart
```

### 2. n8n 服务未运行

**错误**: `无法连接到 n8n`

**解决**:
```bash
# 启动 n8n
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/docker
docker-compose up -d

# 查看日志
docker logs translation_n8n
```

### 3. backend 服务未运行

**错误**: `无法连接到后端`

**解决**:
```bash
# 启动 backend_v2
cd /mnt/d/work/trans_excel/translation_system_v2/backend_v2
python3 main.py

# 或在后台运行
nohup python3 main.py > backend.log 2>&1 &
```

### 4. 表单无法访问

**错误**: `Problem loading form`

**可能原因**:
1. 工作流未正确激活
2. Webhook 未注册

**解决**:
```bash
# 重新运行自动创建脚本
python3 auto_create_via_api.py

# 检查工作流状态
curl -H "X-N8N-API-KEY: n8n_api_Trans2024SecureKey_98765" \
  http://localhost:5678/api/v1/workflows
```

### 5. Backend 连接问题

**错误**: API 节点调用 backend 失败

**检查**:
1. Backend 是否在运行
2. Docker 网络是否正确配置

**解决**:
```bash
# 检查 backend 健康状态
curl http://localhost:8013/health

# 检查 Docker 网络
docker network ls | grep translation

# 确保 backend 可以从 n8n 访问
# 如果 backend 在宿主机运行，URL 使用: http://host.docker.internal:8013
# 如果 backend 在 Docker 中，URL 使用: http://backend:8013
```

---

## 🔄 重新创建工作流

如果需要重新创建工作流（例如修改配置）：

```bash
# 方法1: 直接运行脚本（会自动删除旧工作流）
python3 auto_create_via_api.py

# 方法2: 手动删除后重新创建
# 先获取工作流列表
curl -H "X-N8N-API-KEY: n8n_api_Trans2024SecureKey_98765" \
  http://localhost:5678/api/v1/workflows

# 删除指定工作流
curl -X DELETE \
  -H "X-N8N-API-KEY: n8n_api_Trans2024SecureKey_98765" \
  http://localhost:5678/api/v1/workflows/{workflow_id}

# 重新创建
python3 auto_create_via_api.py
```

---

## 📚 参考资源

- n8n REST API 文档: https://docs.n8n.io/api
- n8n Workflow 社区模板: https://n8n.io/workflows
- Form Trigger 节点文档: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.formtrigger/

---

## ✨ 优势总结

相比手动创建或 JSON 导入：

| 特性 | 手动创建 | JSON 导入 | API 创建 ✅ |
|-----|---------|----------|------------|
| 自动化程度 | ❌ 完全手动 | ⚠️ 半自动 | ✅ 完全自动 |
| Webhook 注册 | ✅ 可靠 | ❌ 不可靠 | ✅ 可靠 |
| 可重复性 | ❌ 低 | ⚠️ 中 | ✅ 高 |
| 配置管理 | ❌ 难 | ⚠️ 中 | ✅ 易 |
| 批量操作 | ❌ 不支持 | ⚠️ 有限 | ✅ 支持 |
| 时间成本 | ⚠️ 5-10分钟 | ⚠️ 3-5分钟 | ✅ 10秒 |

---

## 🎯 下一步

1. ✅ 运行自动创建脚本
2. ✅ 获取表单 URL
3. ✅ 测试表单功能
4. ✅ 开始翻译任务

**现在就运行脚本吧！**

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/scripts
python3 auto_create_via_api.py
```
