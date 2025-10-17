# 🎯 激活完整业务工作流指南

## 问题
你的完整业务工作流（包含所有翻译逻辑）导入后无法访问。

---

## ✅ 正确的激活流程（5步）

### 步骤1: 确认工作流已导入

打开 n8n: http://localhost:5678

在工作流列表中应该能看到：
- "Web Form Translation (网页表单翻译)" 或类似名称

如果看不到：
1. 点击筛选器（漏斗图标）
2. 勾选 "Show archived workflows"
3. 如果在归档列表，点击 "..." → "Unarchive"

---

### 步骤2: 打开工作流编辑器

1. 点击工作流名称进入编辑器
2. 你应该能看到完整的节点链：
   ```
   Translation Form
   → Process Form Data
   → Upload & Split Tasks
   → Poll Split Status
   → Check Split Complete
   → Execute Translation
   → Poll Execution Status
   → Check Execution Complete
   → Download Result
   → Save Result File
   → Return Success
   ```

---

### 步骤3: 检查关键节点配置

#### 3.1 检查 Translation Form 节点

点击第一个节点 "Translation Form"，确认：

- ✅ Type: "Form Trigger"
- ✅ 有表单字段配置（Excel 文件、目标语言、术语表、翻译引擎）
- ✅ 右侧面板应该显示 "Webhook URLs" 区域

**重要**: 如果右侧没有显示 URL，说明工作流还没激活。

#### 3.2 检查后端 API 节点

确认以下节点的 URL 正确：

- "Upload & Split Tasks": `http://backend:8013/api/tasks/split`
- "Execute Translation": `http://backend:8013/api/execute/start`
- "Poll Split Status": `http://backend:8013/api/tasks/split/status/{{ session_id }}`
- "Download Result": `http://backend:8013/api/download/{{ session_id }}`

**注意**: 使用 `backend:8013` 而不是 `localhost:8013`（容器内网络）

---

### 步骤4: 激活工作流 ⚠️ 关键步骤

1. **点击右上角 "Inactive" 开关**
   - 开关应该变成 "Active"（绿色）

2. **立即点击 "Save" 按钮**
   - 非常重要！不保存的话激活不会生效

3. **等待几秒**
   - n8n 会注册 webhook

4. **刷新页面验证**
   - 刷新后状态应该还是 "Active"
   - 如果变回 "Inactive"，说明激活失败

---

### 步骤5: 获取表单 URL

工作流激活成功后：

1. **点击 "Translation Form" 节点**

2. **在右侧面板找到 "Webhook URLs"**

   你会看到两个 URL：
   - **Test URL**: 用于测试（工作流未激活时）
   - **Production URL**: 用于生产（工作流激活后）✅

3. **复制 Production URL**

   格式类似：
   ```
   http://localhost:5678/form-test/a1b2c3d4-e5f6-7890-abcd-ef1234567890
   ```
   或
   ```
   http://localhost:5678/form/xxxxxxxxxxxxx
   ```

4. **访问这个 URL**（不是 /form/translate）

---

## ⚠️ 常见问题

### 问题1: 点击 Active 后又变回 Inactive

**原因**:
- 节点配置有错误
- n8n 无法注册 webhook

**解决**:
1. 查看浏览器控制台错误（F12）
2. 查看 n8n 日志：
   ```bash
   docker logs translation_n8n --tail 50
   ```
3. 检查每个节点是否有红色错误标记

---

### 问题2: 右侧面板没有显示 Webhook URLs

**原因**:
- 工作流未激活
- Form Trigger 节点配置不完整

**解决**:
1. 确保工作流已激活并保存
2. 点击其他节点再点回 Form Trigger
3. 重新激活工作流

---

### 问题3: URL 访问显示 404

**原因**:
- 使用了错误的 URL
- 工作流实际上没有激活成功

**解决**:
1. 必须使用从节点获取的 Production URL
2. 不要使用 `/form/translate`（这是自定义路径，需要特殊配置）
3. 检查工作流状态确实是 Active

---

### 问题4: 后端无法连接

**症状**: 工作流执行时后端 API 调用失败

**检查**:
```bash
# 检查后端是否运行
docker ps | grep translation_backend

# 检查网络
docker network inspect docker_translation_network

# 测试后端
curl http://localhost:8013/health
```

**解决**:
- 确保后端容器运行正常
- 确保 n8n 和 backend 在同一个 Docker 网络
- 节点中使用 `http://backend:8013` 而不是 `http://localhost:8013`

---

## 🔍 调试技巧

### 1. 查看 n8n 日志

```bash
# 实时查看日志
docker logs -f translation_n8n

# 查看最近的错误
docker logs translation_n8n 2>&1 | grep -i error | tail -20
```

### 2. 测试工作流

在 n8n 编辑器中：
1. 点击任意节点
2. 点击 "Test step" 或 "Execute node"
3. 查看执行结果和错误信息

### 3. 手动测试后端 API

```bash
# 测试健康检查
curl http://localhost:8013/health

# 测试从容器内访问
docker exec translation_n8n curl http://backend:8013/health
```

---

## 📋 完整检查清单

激活工作流前的检查：

- [ ] n8n 和 backend 容器都在运行
- [ ] 工作流已导入（不在归档列表）
- [ ] 所有节点配置正确（特别是 API URLs）
- [ ] Form Trigger 节点配置完整
- [ ] 后端 API 可以访问（curl http://localhost:8013/health）

激活工作流：

- [ ] 点击 "Inactive" → "Active"
- [ ] 点击 "Save" 保存 ⚠️
- [ ] 刷新页面确认还是 Active
- [ ] Form Trigger 节点显示 Production URL
- [ ] 复制 Production URL

测试：

- [ ] 访问 Production URL 能看到表单
- [ ] 表单显示所有字段（Excel 文件、目标语言等）
- [ ] 上传测试文件不报错

---

## 🎯 预期结果

成功激活后，访问 Production URL 应该看到：

```
┌──────────────────────────────────────────────────────┐
│  📄 Excel 文件翻译系统                                │
│  上传 Excel 文件，自动翻译为多种语言                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Excel 文件 *                                        │
│  [选择文件]                                          │
│                                                      │
│  目标语言 *                                          │
│  □ 英文 (EN)                                        │
│  □ 泰文 (TH)                                        │
│  □ 葡萄牙文 (PT)                                    │
│  □ 越南文 (VN)                                      │
│                                                      │
│  术语表                                              │
│  [下拉选择]                                          │
│  - 不使用                                            │
│  - 游戏术语 (game_terms)                            │
│  - 商业术语 (business_terms)                        │
│  - 技术术语 (technical_terms)                       │
│                                                      │
│  翻译引擎                                            │
│  [下拉选择]                                          │
│  - 通义千问 (推荐)                                   │
│  - OpenAI GPT                                        │
│                                                      │
│  [提交]                                              │
└──────────────────────────────────────────────────────┘
```

---

## 🚀 快速操作流程

```bash
# 1. 确认服务运行
docker ps | grep translation

# 2. 打开 n8n
open http://localhost:5678

# 3. 在 n8n UI 中：
#    - 打开 "Web Form Translation" 工作流
#    - 点击 Active → Save
#    - 点击 Form Trigger 节点
#    - 复制 Production URL
#    - 访问该 URL

# 4. 测试表单
#    - 上传 Excel 文件
#    - 选择目标语言
#    - 提交
```

---

**现在立即操作**：打开 http://localhost:5678，激活工作流并获取 Production URL！🎯
