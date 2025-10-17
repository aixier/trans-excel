# ✅ n8n 表单翻译服务已就绪

## 🎉 设置完成

两个翻译工作流已成功激活，webhook 已生成，可以立即使用！

---

## 📋 可用的表单 URL

### 1️⃣ 完整版表单（推荐）⭐

```
http://localhost:5678/form/1a8bb92f-46e0-49cc-b496-3fe5fb8677b1
```

**工作流**: Web Form Translation (网页表单翻译)
**特点**:
- ✅ 全自动流程：上传 → 拆分 → 翻译 → 下载
- ✅ 自动轮询任务状态
- ✅ 翻译完成后自动返回结果
- ✅ 用户体验好（一次操作完成）
- ⏱️ 等待时间：几分钟（取决于文件大小）

**适合场景**:
- 终端用户直接使用
- 不需要手动查询状态
- 需要立即获得翻译结果

---

### 2️⃣ 简化版表单

```
http://localhost:5678/form/7477ad27-a99c-4f74-8652-6d4d35ddc0d0
```

**工作流**: Excel翻译表单_自动创建
**特点**:
- ✅ 快速响应：立即返回 session_id
- ✅ 轻量级：只有3个节点
- ✅ 适合集成：可配合前端应用
- ⏱️ 响应时间：<1秒

**返回格式**:
```json
{
  "success": true,
  "session_id": "xxx-xxx-xxx",
  "message": "任务已创建",
  "status_url": "http://localhost:8013/api/tasks/split/status/xxx-xxx-xxx",
  "download_url": "http://localhost:8013/api/download/xxx-xxx-xxx",
  "tips": "请保存session_id，完成后访问download_url下载结果"
}
```

**适合场景**:
- 前端应用集成（前端负责轮询）
- 需要自定义后续处理逻辑
- 快速测试功能

---

## 🧪 快速测试

### 测试步骤

1. **打开表单 URL**
   - 推荐先测试完整版：`http://localhost:5678/form/1a8bb92f-46e0-49cc-b496-3fe5fb8677b1`

2. **填写表单**
   - **Excel文件**: 上传包含中文的 Excel 文件
   - **目标语言**: 选择一个目标语言（EN/TH/JP/KR/PT/VN）
   - **术语库**: 可选，留空使用默认术语库

3. **提交并等待**
   - 完整版：等待几分钟，自动返回翻译结果
   - 简化版：立即返回 session_id 和查询URL

4. **查看结果**
   - 完整版：直接显示下载链接或翻译后内容
   - 简化版：需要访问 `status_url` 查询进度，完成后访问 `download_url`

---

## 📊 功能对比

| 功能 | 简化版 | 完整版 |
|------|:------:|:------:|
| 文件上传 | ✅ | ✅ |
| 多语言支持 | ✅ | ✅ |
| 术语库支持 | ✅ | ✅ |
| 自动拆分任务 | ✅ | ✅ |
| 自动轮询状态 | ❌ | ✅ |
| 自动下载结果 | ❌ | ✅ |
| 错误重试 | ❌ | ✅ |
| 响应时间 | <1秒 | 几分钟 |
| 节点数量 | 3 | 13 |
| 学习成本 | 低 | 中 |

---

## 🔧 使用简化版的后续操作

如果使用简化版表单，需要手动查询状态：

### 1. 查询拆分状态
```bash
curl http://localhost:8013/api/tasks/split/status/{session_id}
```

返回示例：
```json
{
  "session_id": "xxx",
  "stage": "SPLIT_COMPLETED",
  "tasks_count": 100,
  "split_status": "completed"
}
```

### 2. 执行翻译
```bash
curl -X POST http://localhost:8013/api/execute/start \
  -H "Content-Type: application/json" \
  -d '{"session_id": "xxx"}'
```

### 3. 查询执行状态
```bash
curl http://localhost:8013/api/execute/status/{session_id}
```

### 4. 下载结果
```bash
curl http://localhost:8013/api/download/{session_id} -o result.xlsx
```

---

## 🌐 在前端应用中集成

### 嵌入表单（iframe）

```html
<iframe
  src="http://localhost:5678/form/1a8bb92f-46e0-49cc-b496-3fe5fb8677b1"
  width="100%"
  height="600"
  frameborder="0">
</iframe>
```

### 直接调用后端 API

如果不想使用 n8n 表单，可以直接调用后端 API：

```javascript
// 1. 上传文件并拆分任务
const formData = new FormData();
formData.append('file', excelFile);
formData.append('source_lang', 'CH');
formData.append('target_langs', 'EN');

const splitResponse = await fetch('http://localhost:8013/api/tasks/split', {
  method: 'POST',
  body: formData
});
const { session_id } = await splitResponse.json();

// 2. 执行翻译
await fetch('http://localhost:8013/api/execute/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id })
});

// 3. 轮询状态
const statusUrl = `http://localhost:8013/api/execute/status/${session_id}`;
// ... 定期查询直到完成

// 4. 下载结果
window.location.href = `http://localhost:8013/api/download/${session_id}`;
```

---

## 🛠️ 管理工作流

### 查看工作流列表
```
http://localhost:5678/home/workflows
```

### 编辑工作流
点击工作流名称进入编辑器，可以：
- 修改表单字段
- 调整请求参数
- 添加错误处理
- 配置通知（邮件、Slack等）

### 停用/激活工作流
- 在工作流列表页面，点击右侧的开关按钮
- 或在编辑页面，点击右上角的激活开关

### 查看执行历史
在工作流编辑页面，点击 "Executions" 标签，可以看到：
- 每次执行的时间
- 执行状态（成功/失败）
- 输入输出数据
- 错误日志

---

## ❓ 常见问题

### Q1: 表单显示 "Problem loading form"？
**A**:
1. 确保工作流已激活（右上角开关为绿色）
2. 确保 n8n 服务正在运行
3. 检查 webhook ID 是否正确

### Q2: 提交后没有响应？
**A**:
1. 检查后端服务是否运行：`curl http://localhost:8013/health`
2. 查看 n8n 工作流的执行历史（Executions 标签）
3. 查看浏览器控制台的错误信息

### Q3: 翻译速度很慢？
**A**:
- 完整版需要等待翻译完成，时间取决于文件大小和任务数量
- 可以在后端配置中调整 `max_concurrent_workers` 提高并发
- 或使用简化版，不阻塞等待

### Q4: 可以修改表单样式吗？
**A**:
- n8n Form Trigger 的样式由 n8n 控制，自定义能力有限
- 可以修改表单标题、描述、字段
- 如需完全自定义，建议使用前端应用直接调用 API

### Q5: 支持批量上传吗？
**A**:
- 当前表单一次只能上传一个文件
- 如需批量处理，可以：
  1. 编写脚本循环调用 API
  2. 修改 n8n 工作流添加批量处理逻辑

---

## 📚 相关文档

- [n8n Webhook 激活指南](./scripts/n8n_webhook_guide.md)
- [工作流版本对比](./workflows/README_WORKFLOWS.md)
- [API Key 设置指南](./scripts/N8N_API_KEY_SETUP.md)
- [故障排查指南](./TROUBLESHOOTING.md)
- [快速修复 401 错误](./QUICK_FIX_401.md)

---

## 🎯 下一步

1. **测试表单功能**
   - 使用完整版 URL 上传测试文件
   - 验证翻译结果是否正确

2. **集成到应用**
   - 如果是前端应用，可以嵌入 iframe 或直接调用 API
   - 如果是命令行工具，使用简化版 + 脚本轮询

3. **自定义配置**
   - 根据需要修改表单字段
   - 调整后端翻译参数
   - 配置通知和日志

---

**🎉 恭喜！你的 n8n 表单翻译服务已经可以使用了！**

立即体验：[http://localhost:5678/form/1a8bb92f-46e0-49cc-b496-3fe5fb8677b1](http://localhost:5678/form/1a8bb92f-46e0-49cc-b496-3fe5fb8677b1)
