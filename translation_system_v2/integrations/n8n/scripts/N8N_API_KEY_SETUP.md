# n8n API Key 设置指南

## 问题说明

如果你遇到 `401 Unauthorized` 错误，这是因为：

**❌ 错误做法：通过环境变量设置 API Key**
```bash
# .env 文件中的这个设置无法用于 API 认证
N8N_API_KEY=n8n_api_Trans2024SecureKey_98765
```

**✅ 正确做法：通过 n8n UI 生成 API Key**

---

## 步骤1：访问 n8n UI

打开浏览器访问：
```
http://localhost:5678
```

如果是首次访问，需要创建管理员账户。

---

## 步骤2：生成 API Key

### 方法A：通过设置页面（推荐）

1. 登录 n8n 后，点击右上角用户头像
2. 选择 **Settings** (设置)
3. 在左侧菜单找到 **n8n API** 或 **API Keys**
4. 点击 **Create API Key** 按钮
5. 输入描述（例如："Translation System API"）
6. 点击创建
7. **立即复制生成的 API Key**（只会显示一次！）

### 方法B：通过用户设置

1. 登录后点击右上角头像
2. 选择 **Personal Settings** 或 **Account Settings**
3. 找到 **API Keys** 标签
4. 点击 **Generate API Key**
5. 复制生成的 key

---

## 步骤3：使用 API Key

### 方式1：通过环境变量

创建一个新的 `.env.local` 文件：

```bash
# 实际从 n8n UI 生成的 API Key
N8N_REAL_API_KEY=n8n_api_xxxxxxxxxxxxxxxxxxxxxxxxxx
```

然后运行脚本：

```bash
export N8N_REAL_API_KEY="你从UI复制的API_KEY"
python3 n8n/scripts/auto_create_via_api.py
```

### 方式2：直接传递给脚本

```bash
python3 n8n/scripts/auto_create_via_api.py --api-key "你的API_KEY"
```

### 方式3：交互式输入

```bash
python3 n8n/scripts/auto_create_via_api.py --interactive
```

---

## 步骤4：验证 API Key

使用 curl 测试：

```bash
# 替换为你的实际 API Key
export API_KEY="n8n_api_xxxxxxxxxxxxxxxxxxxxxxxxxx"

curl -H "X-N8N-API-KEY: $API_KEY" \
     http://localhost:5678/api/v1/workflows
```

如果返回工作流列表（或空列表 `{"data":[]}`），说明认证成功！

如果返回 `{"message":"unauthorized"}`，请检查：
- API Key 是否正确复制（注意空格）
- n8n 服务是否正常运行
- n8n 版本是否支持 API Key 认证

---

## 常见问题

### Q1: 找不到 API Key 设置选项？

**原因：** 旧版本 n8n 可能不支持 API Key 功能

**解决方案：** 更新 n8n 到最新版本

```bash
cd n8n/docker
docker-compose pull
docker-compose down
docker-compose up -d
```

### Q2: API Key 创建后立即失效？

**原因：** 可能是容器重启导致

**解决方案：** 确保 n8n 数据持久化

```bash
# 检查 volume 是否正确挂载
docker volume ls | grep n8n
```

### Q3: 使用环境变量中的 API Key 仍然失败？

**原因：** 环境变量 `N8N_API_KEY` 不是用于 API 认证的

**解决方案：** 必须使用 UI 生成的 key

---

## 安全建议

1. **不要提交 API Key 到 Git**
   ```bash
   # 添加到 .gitignore
   echo ".env.local" >> .gitignore
   ```

2. **定期轮换 API Key**
   - 在 n8n UI 中删除旧 key
   - 生成新 key
   - 更新脚本配置

3. **限制 API Key 访问范围**
   - 仅在可信环境使用
   - 不要在公网暴露 n8n API 端口

---

## 快速开始

**最简单的方式：**

1. 访问 http://localhost:5678
2. 登录 → Settings → n8n API → Create API Key
3. 复制 API Key
4. 运行：
   ```bash
   python3 n8n/scripts/auto_create_via_api.py --api-key "粘贴你的key"
   ```

---

## 参考资源

- n8n 官方文档：https://docs.n8n.io/api/authentication/
- n8n Community：https://community.n8n.io/
- GitHub Issues：https://github.com/n8n-io/n8n/issues
