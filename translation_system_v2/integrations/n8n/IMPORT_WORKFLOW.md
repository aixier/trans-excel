# 📥 导入工作流指南

## 🎯 目标
将 Web 表单翻译工作流导入到 n8n

---

## ✅ 前提条件

- ✅ n8n 服务已启动（docker ps 可以看到 translation_n8n）
- ✅ 可以访问 http://localhost:5678

---

## 📋 导入步骤（5步）

### 步骤1: 打开 n8n 界面

打开浏览器访问: **http://localhost:5678**

### 步骤2: 首次登录（如果需要）

如果是首次访问，n8n 会要求创建账号：

- Email: 输入任意邮箱（如 admin@example.com）
- Password: 输入密码（如 Trans@n8n2024!）
- First Name: Admin
- Last Name: User

点击 "Continue" 完成设置

### 步骤3: 创建新工作流

1. 点击左上角的 "+" 或 "Add workflow"
2. 工作流编辑器会打开一个空白工作流

### 步骤4: 导入工作流 JSON

**方式1: 从剪贴板导入（推荐）**

1. 复制工作流 JSON 文件内容：
   ```bash
   cat /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/workflows/08_web_form_translation.json
   ```

2. 在 n8n 界面点击右上角的 "..." (三个点)
3. 选择 "Import from URL / File"
4. 选择 "From file" 标签
5. 点击上传按钮，选择文件：
   `/mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/workflows/08_web_form_translation.json`

**方式2: 从容器内导入**

1. 在 n8n 界面点击右上角的 "..." (三个点)
2. 选择 "Import from URL / File"
3. 选择 "From file" 标签
4. 由于工作流文件已挂载到容器内 `/workflows/` 目录
5. 需要手动将文件内容粘贴到 n8n

### 步骤5: 激活工作流

1. 导入成功后，工作流会显示在编辑器中
2. 点击右上角的 "Inactive" 开关
3. 将工作流设置为 "Active"（激活）
4. 点击 "Save" 保存

---

## 🌐 访问 Web 表单

工作流激活后，Web 表单可以通过以下地址访问：

```
http://localhost:5678/form/<workflow-webhook-path>
```

**获取完整 URL**:

1. 在 n8n 工作流编辑器中
2. 点击第一个节点 "Translation Form"（Form Trigger）
3. 在右侧面板可以看到 "Form URL"
4. 复制这个 URL 就可以访问表单了

通常 URL 类似：
```
http://localhost:5678/form/translate
```

---

## 🔍 验证工作流

### 检查节点配置

导入后检查关键节点：

1. **Translation Form** (Form Trigger)
   - 检查表单字段是否正确

2. **Upload & Split Tasks** (HTTP Request)
   - URL 应该是: `http://backend:8013/api/tasks/split`

3. **Execute Translation** (HTTP Request)
   - URL 应该是: `http://backend:8013/api/execute/start`

4. **Download Result** (HTTP Request)
   - URL 应该是: `http://backend:8013/api/download/{{session_id}}`

### 测试连接

在 n8n 编辑器中：

1. 点击 "Upload & Split Tasks" 节点
2. 点击 "Test step" 测试后端连接
3. 如果后端正常，应该能连接成功

---

## ❓ 常见问题

### Q1: 找不到导入选项？

**位置**: 点击 n8n 界面右上角的 "..." (三个点菜单)

### Q2: 导入后工作流是空的？

**原因**: JSON 格式可能有问题

**解决**:
```bash
# 验证 JSON 格式
cat /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/workflows/08_web_form_translation.json | python3 -m json.tool
```

### Q3: 激活工作流时报错？

**可能原因**:
- 后端服务未启动
- n8n 无法连接到 backend 容器

**检查**:
```bash
# 检查后端
docker ps | grep translation_backend

# 检查网络
docker network inspect docker_translation_network
```

### Q4: Form URL 是什么？

**获取方式**:
1. 打开工作流
2. 点击 "Translation Form" 节点
3. 右侧面板会显示 "Production URL" 和 "Test URL"
4. 使用 Production URL

---

## 🎉 完成后

访问表单 URL，你应该能看到：

```
┌──────────────────────────────────────────────┐
│  📄 Excel 文件翻译系统                       │
│  上传 Excel 文件，自动翻译为多种语言         │
├──────────────────────────────────────────────┤
│                                              │
│  Excel 文件 *                                │
│  [选择文件]                                  │
│                                              │
│  目标语言 *                                  │
│  ☑ 英文 (EN)                                │
│  ☐ 泰文 (TH)                                │
│                                              │
│  术语表                                      │
│  [下拉选择]                                  │
│                                              │
│  [提交]                                      │
└──────────────────────────────────────────────┘
```

---

**下一步**: 上传 Excel 文件测试翻译功能！🚀
