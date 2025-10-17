# n8n Integration 故障排查指南

## 问题1: 401 Unauthorized - API 认证失败

### 症状
```bash
❌ 创建工作流失败: 401
   响应: {"message":"unauthorized"}
```

### 根本原因
n8n API Key **不能通过环境变量配置**，必须通过 UI 手动生成。

### 解决方案

#### 步骤1：在 n8n UI 中生成 API Key

1. 访问 n8n：http://localhost:5678
2. 登录（首次使用需创建账户）
3. 点击右上角用户头像 → **Settings**
4. 找到 **n8n API** 或 **API Keys** 选项
5. 点击 **Create API Key**
6. 输入描述（如 "Translation System"）
7. **立即复制 key**（只显示一次！）

#### 步骤2：使用 API Key 运行脚本

**方式A：交互式输入（推荐）**
```bash
cd n8n/scripts
python3 auto_create_via_api.py --interactive
```

**方式B：命令行参数**
```bash
python3 auto_create_via_api.py --api-key "n8n_api_你的key"
```

**方式C：环境变量**
```bash
export N8N_REAL_API_KEY="n8n_api_你的key"
python3 auto_create_via_api.py
```

### 验证

测试 API Key 是否有效：
```bash
curl -H "X-N8N-API-KEY: n8n_api_你的key" \
     http://localhost:5678/api/v1/workflows
```

成功返回：`{"data":[]}`
失败返回：`{"message":"unauthorized"}`

---

## 问题2: n8n 服务未运行

### 症状
```bash
❌ 无法连接到 n8n: Connection refused
```

### 解决方案

启动 n8n 服务：
```bash
cd integrations/n8n/docker
docker-compose up -d
```

检查服务状态：
```bash
docker ps | grep translation_n8n
```

查看日志：
```bash
docker logs translation_n8n
```

健康检查：
```bash
curl http://localhost:5678/healthz
```

---

## 问题3: 后端服务未运行

### 症状
```bash
⚠️  后端服务未运行，工作流将无法正常工作
```

### 影响
工作流可以创建，但提交表单时会失败（无法连接到翻译 API）。

### 解决方案

启动后端服务：
```bash
cd backend_v2
python3 main.py
```

或使用 Docker（如果配置了）：
```bash
docker-compose up backend
```

验证：
```bash
curl http://localhost:8013/health
```

---

## 问题4: 找不到 API Key 设置选项

### 症状
在 n8n UI 中找不到 "n8n API" 或 "API Keys" 选项。

### 原因
n8n 版本过旧，不支持 API Key 功能。

### 解决方案

更新 n8n 到最新版本：
```bash
cd n8n/docker
docker-compose pull
docker-compose down
docker-compose up -d
```

检查版本（应该 >= 1.0）：
```bash
docker exec translation_n8n n8n --version
```

---

## 问题5: API Key 格式不正确

### 症状
```bash
⚠️  警告: API Key 格式可能不正确
   通常应该以 'n8n_api_' 开头
```

### 原因
- 复制时包含了空格或换行符
- 使用了旧版本 n8n 的 key 格式

### 解决方案

1. **重新生成 key：**
   - 删除旧 key：Settings → n8n API → Delete
   - 创建新 key：Create API Key
   - 仔细复制（双击全选，避免手动选择）

2. **验证格式：**
   ```bash
   echo "你的key" | xxd  # 检查是否有隐藏字符
   ```

3. **使用交互式输入：**
   ```bash
   python3 auto_create_via_api.py --interactive
   ```

---

## 问题6: 工作流创建后无法访问

### 症状
工作流创建成功，但无法获取表单 URL。

### 原因
- Webhook 未正确注册
- 工作流未激活

### 解决方案

1. **检查工作流状态：**
   访问 n8n UI，确认工作流已激活（绿色勾选）

2. **手动激活：**
   ```bash
   # 使用 API 激活
   curl -X PATCH \
        -H "X-N8N-API-KEY: your_key" \
        -H "Content-Type: application/json" \
        -d '{"active": true}' \
        http://localhost:5678/api/v1/workflows/{workflow_id}
   ```

3. **重新创建工作流：**
   ```bash
   python3 auto_create_via_api.py --api-key "your_key"
   ```

---

## 问题7: 权限不足

### 症状
```bash
❌ 创建工作流失败: 403
   响应: {"message":"forbidden"}
```

### 原因
- API Key 权限不足
- 用户角色限制

### 解决方案

1. **检查用户角色：**
   确保创建 API Key 的用户是 Owner 或 Admin

2. **重新生成 API Key：**
   使用管理员账户生成新的 key

3. **检查 n8n 配置：**
   ```bash
   docker exec translation_n8n env | grep N8N
   ```

---

## 问题8: 表单提交后没有响应

### 症状
表单提交后长时间等待，最终超时。

### 调试步骤

1. **检查后端日志：**
   ```bash
   # 如果是 Python 直接运行
   # 查看终端输出

   # 如果是 Docker
   docker logs backend_container
   ```

2. **检查网络连接：**
   ```bash
   # 从 n8n 容器内部测试
   docker exec translation_n8n curl http://backend:8013/health
   ```

3. **检查工作流执行日志：**
   访问 n8n UI → Executions → 查看失败的执行

4. **测试 API 端点：**
   ```bash
   curl -X POST http://localhost:8013/api/tasks/split \
        -F "file=@test.xlsx" \
        -F "source_lang=CH" \
        -F "target_langs=EN"
   ```

---

## 问题9: Docker 网络连接问题

### 症状
```bash
❌ 后端健康检查失败: Connection refused
```

### 原因
n8n 容器和后端容器不在同一网络。

### 解决方案

1. **检查网络配置：**
   ```bash
   docker network ls
   docker network inspect translation_network
   ```

2. **确保容器在同一网络：**
   ```bash
   # docker-compose.yml 中
   services:
     n8n:
       networks:
         - translation_network
     backend:
       networks:
         - translation_network
   ```

3. **使用容器名称而非 localhost：**
   ```yaml
   # 工作流中使用
   url: "http://backend:8013/api/tasks/split"
   # 而非
   url: "http://localhost:8013/api/tasks/split"
   ```

---

## 问题10: 环境变量未加载

### 症状
脚本找不到 API Key 环境变量。

### 解决方案

1. **手动导出环境变量：**
   ```bash
   export N8N_REAL_API_KEY="your_key"
   python3 auto_create_via_api.py
   ```

2. **使用 dotenv 文件（推荐）：**
   ```bash
   # 创建 .env.local
   echo "N8N_REAL_API_KEY=your_key" > .env.local

   # 加载并运行
   source .env.local
   python3 auto_create_via_api.py
   ```

3. **直接使用参数：**
   ```bash
   python3 auto_create_via_api.py --api-key "your_key"
   ```

---

## 常用诊断命令

### 检查所有服务状态
```bash
# n8n 服务
curl http://localhost:5678/healthz

# 后端服务
curl http://localhost:8013/health

# Docker 容器
docker ps
```

### 查看日志
```bash
# n8n 日志
docker logs translation_n8n --tail 100 -f

# 后端日志（如果是 Docker）
docker logs backend_container --tail 100 -f
```

### 测试 API
```bash
# 测试 n8n API
curl -H "X-N8N-API-KEY: your_key" \
     http://localhost:5678/api/v1/workflows

# 测试后端 API
curl http://localhost:8013/api/tasks/split
```

### 清理并重启
```bash
# 停止所有服务
docker-compose down

# 清理数据（可选，会删除所有工作流）
docker volume rm n8n_data

# 重新启动
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

---

## 获取帮助

### 文档资源
- n8n API 设置指南：`N8N_API_KEY_SETUP.md`
- n8n 集成 README：`../README.md`
- 项目主 README：`../../README.md`

### 在线资源
- n8n 官方文档：https://docs.n8n.io/
- n8n Community：https://community.n8n.io/
- GitHub Issues：https://github.com/n8n-io/n8n/issues

### 日志位置
- n8n 日志：`docker logs translation_n8n`
- 后端日志：`backend_v2/logs/` 或终端输出
- 工作流执行日志：n8n UI → Executions

### 联系支持
如果问题仍未解决，请提供以下信息：
1. 错误信息完整输出
2. n8n 版本：`docker exec translation_n8n n8n --version`
3. Docker 日志：`docker logs translation_n8n --tail 50`
4. 操作步骤和复现方法
