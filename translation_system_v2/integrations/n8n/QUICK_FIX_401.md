# 快速修复 401 Unauthorized 错误

## 一句话解决方案
**环境变量中的 API Key 无效，必须从 n8n UI 生成真实的 API Key。**

---

## 3步快速修复

### 1️⃣ 生成 API Key（2分钟）

打开浏览器：
```
http://localhost:5678
```

登录后：
```
右上角头像 → Settings → n8n API → Create API Key → 复制 key
```

### 2️⃣ 运行脚本（交互式输入）

```bash
cd integrations/n8n/scripts
python3 auto_create_via_api.py --interactive
```

粘贴你刚才复制的 API Key。

### 3️⃣ 完成！

如果成功，你会看到：
```
✅ 工作流创建成功！
📋 表单访问地址: http://localhost:5678/form/xxxxx
```

---

## 其他方式

### 方式A：命令行参数
```bash
python3 auto_create_via_api.py --api-key "n8n_api_你的key"
```

### 方式B：环境变量
```bash
export N8N_REAL_API_KEY="n8n_api_你的key"
python3 auto_create_via_api.py
```

---

## 为什么会出现 401 错误？

`.env` 文件中的这个配置**无法**用于 API 认证：
```bash
# ❌ 这个不是真实的 API Key
N8N_API_KEY=n8n_api_Trans2024SecureKey_98765
```

**必须**通过 n8n UI 生成的 key 才有效：
```bash
# ✅ 这是真实的 API Key（示例）
N8N_REAL_API_KEY=n8n_api_abc123def456ghi789...
```

---

## 仍然失败？

查看详细故障排查文档：
```bash
cat TROUBLESHOOTING.md
```

或查看 API Key 设置指南：
```bash
cat scripts/N8N_API_KEY_SETUP.md
```

---

## 验证 API Key

测试你的 key 是否有效：
```bash
curl -H "X-N8N-API-KEY: 你的key" \
     http://localhost:5678/api/v1/workflows
```

成功：返回 `{"data":[...]}`
失败：返回 `{"message":"unauthorized"}`
