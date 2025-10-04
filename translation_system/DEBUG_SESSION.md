# Session Not Found 问题诊断指南

## 问题症状
- 测试页面（test_pages）1-4步骤：✅ 正常
- 前端主应用（frontend_v2）：❌ 拆分任务时返回 `"Session not found or Excel not loaded"`

## 诊断步骤

### 1. 检查前端session数据

**在浏览器Console执行：**

```javascript
// 1. 查看当前session
console.log('Current Session:', sessionManager.session);

// 2. 查看localStorage
console.log('LocalStorage Session:', localStorage.getItem('currentSession'));

// 3. 查看session_id
console.log('SessionID:', sessionManager.session?.sessionId);

// 4. 检查session是否过期
const session = JSON.parse(localStorage.getItem('currentSession'));
console.log('Created:', new Date(session.createdAt));
console.log('Expires:', new Date(session.expiresAt));
console.log('Now:', new Date());
console.log('Is Expired:', Date.now() > session.expiresAt);
```

### 2. 验证后端session是否存在

**方法A：直接API调用（推荐）**

```javascript
// 在浏览器Console执行
const sessionId = sessionManager.session.sessionId;

// 检查分析状态
fetch(`/api/analyze/status/${sessionId}`)
  .then(r => r.json())
  .then(d => console.log('Backend Session:', d))
  .catch(e => console.error('Session Not Found:', e));

// 检查所有活跃session
fetch('/api/monitor/sessions')
  .then(r => r.json())
  .then(d => console.log('All Backend Sessions:', d))
  .catch(e => console.error('Error:', e));
```

**方法B：使用curl（在终端）**

```bash
# 1. 获取session_id（从浏览器Console复制）
SESSION_ID="c8dcc409-35aa-40d1-a7d3-363b2a91242a"

# 2. 检查session状态
curl http://localhost:8071/api/analyze/status/$SESSION_ID | jq

# 3. 查看所有活跃session
curl http://localhost:8071/api/monitor/sessions | jq

# 4. 检查全局执行状态
curl http://localhost:8071/api/execute/status/global | jq
```

### 3. 对比前后端数据

**检查清单：**

- [ ] 前端 `sessionManager.session.sessionId` 是否存在？
- [ ] 前端 session 是否过期？（expiresAt < now）
- [ ] 后端 `/api/analyze/status/{session_id}` 返回200？
- [ ] 后端 `/api/monitor/sessions` 列表中有该session？
- [ ] 前后端 session_id 字符串完全一致？

### 4. 查看网络请求

**Chrome DevTools → Network：**

1. **上传请求：**
   - 请求：`POST /api/analyze/upload`
   - 响应：查看 `response.session_id` 的值
   - ✅ 记录这个值

2. **拆分请求：**
   - 请求：`POST /api/tasks/split`
   - Payload：查看 `request.session_id` 的值
   - ❓ 对比是否与上传响应的session_id一致

3. **错误响应：**
   - 状态码：400 / 404？
   - 响应体：`{"detail":"Session not found or Excel not loaded"}`

### 5. 常见原因排查

#### 原因1：前端使用了错误的session_id

**症状：**
- 上传返回 session_id: `abc-123`
- 拆分发送 session_id: `xyz-789`（不一致！）

**诊断：**
```javascript
// 上传成功后立即检查
console.log('Upload Response SessionID:', result.session_id);
console.log('SessionManager SessionID:', sessionManager.session.sessionId);
console.log('Match:', result.session_id === sessionManager.session.sessionId);
```

**修复：**
- 确保 `sessionManager.createSession()` 使用上传响应的 `session_id`
- 不要在中途修改 `sessionManager.session.sessionId`

#### 原因2：后端session被提前清理

**症状：**
- 上传时session创建成功
- 配置页面加载正常（说明session存在）
- 点击拆分时session突然不存在

**诊断：**
```javascript
// 在config页面render后检查
fetch(`/api/analyze/status/${sessionManager.session.sessionId}`)
  .then(r => console.log('Backend Status:', r.status));

// 在拆分前再次检查
fetch(`/api/analyze/status/${sessionManager.session.sessionId}`)
  .then(r => console.log('Before Split:', r.status));
```

**可能原因：**
- 后端超时清理（8小时未访问）
- 后端内存不足强制清理
- 多个session创建触发清理逻辑

#### 原因3：Docker重启丢失session

**症状：**
- 前端localStorage有session
- 后端内存session全部丢失

**验证：**
```bash
# 检查Docker启动时间
docker ps -a | grep excel-translation

# 对比session创建时间
# 如果Docker启动时间 > session创建时间，说明重启了
```

**临时解决：**
- 清理localStorage重新上传
- 或实现session恢复机制

#### 原因4：source_lang 格式错误

**症状：**
- 请求体：`"source_lang":"EN"`
- 后端期望：`"source_lang":"auto"` 或 `null`

**检查：**
```javascript
// 查看发送的配置
console.log('Split Config:', {
  session_id: sessionId,
  source_lang: config.source_lang,
  target_langs: config.target_langs
});
```

**后端验证逻辑：**
```python
# backend_v2/api/task_api.py
session_data = session_manager.get_session(session_id)
if not session_data:
    raise HTTPException(404, "Session not found")

excel_df = session_data.excel_df
if not excel_df:
    raise HTTPException(400, "Excel not loaded")
```

### 6. 实时监控方案

**添加调试代码到 config.js:**

```javascript
// config.js:341 修改
async startSplit() {
    // ... 前面的代码 ...

    // 🔍 添加调试日志
    console.log('=== Split Debug Info ===');
    console.log('SessionManager:', sessionManager.session);
    console.log('SessionID:', sessionManager.session?.sessionId);
    console.log('Config:', this.config);

    // 验证后端session
    try {
        const check = await fetch(`/api/analyze/status/${sessionManager.session.sessionId}`);
        console.log('Backend Session Status:', check.status, check.ok ? 'EXISTS' : 'NOT FOUND');
    } catch (e) {
        console.error('Backend Check Failed:', e);
    }

    try {
        // 开始拆分
        console.log('Sending Split Request...');
        await API.splitTasks(sessionManager.session.sessionId, this.config);
        console.log('Split Request Success!');
        // ...
    } catch (error) {
        console.error('Split Request Failed:', error);
        // ...
    }
}
```

### 7. 快速修复验证

**如果是前端session丢失：**

```javascript
// 在浏览器Console执行
// 1. 清理旧session
localStorage.clear();

// 2. 刷新页面
location.reload();

// 3. 重新上传文件
```

**如果是后端session丢失：**

```bash
# 1. 重启Docker容器
docker restart excel-translation

# 2. 清理前端缓存
localStorage.clear();

# 3. 重新上传测试
```

### 8. 对比测试页面与主应用

**测试页面成功的关键：**

```javascript
// test_pages/2_task_split.html:516
const requestBody = {
    session_id: sessionId,  // ← 直接从输入框读取
    source_lang: sourceLang || null,
    target_langs: targetLangs,
    extract_context: extractContext,
    context_options: extractContext ? contextOptions : null
};
```

**主应用的差异：**

```javascript
// frontend_v2/js/pages/config.js:341
await API.splitTasks(sessionManager.session.sessionId, this.config);
//                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
//                    从 sessionManager 读取，可能为 undefined

// api.js:86
session_id: sessionId,  // ← 如果 sessionId 是 undefined，后端会报错
```

**修复建议：**

```javascript
// config.js 增加验证
async startSplit() {
    if (this.splitting || this.config.target_langs.length === 0) return;

    // ✅ 验证 session 存在
    if (!sessionManager.session || !sessionManager.session.sessionId) {
        UIHelper.showToast('会话已失效，请重新上传文件', 'error');
        router.navigate('/create');
        return;
    }

    // ✅ 打印调试信息
    console.log('Split with SessionID:', sessionManager.session.sessionId);

    // ... 后续代码
}
```

## 最终诊断脚本

**复制到浏览器Console一键诊断：**

```javascript
(async function diagnoseSession() {
    console.log('=== SESSION DIAGNOSIS ===\n');

    // 1. 前端session
    console.log('1. Frontend Session:');
    console.log('  - sessionManager.session:', sessionManager.session);
    console.log('  - sessionId:', sessionManager.session?.sessionId);
    console.log('  - localStorage:', localStorage.getItem('currentSession'));

    const sessionId = sessionManager.session?.sessionId;
    if (!sessionId) {
        console.error('❌ No sessionId in frontend!');
        return;
    }

    // 2. 后端session
    console.log('\n2. Backend Session:');
    try {
        const resp = await fetch(`/api/analyze/status/${sessionId}`);
        if (resp.ok) {
            const data = await resp.json();
            console.log('  ✅ Backend session exists:', data);
        } else {
            console.error('  ❌ Backend session not found:', resp.status);
        }
    } catch (e) {
        console.error('  ❌ Backend check failed:', e);
    }

    // 3. 所有活跃session
    console.log('\n3. All Active Sessions:');
    try {
        const resp = await fetch('/api/monitor/sessions');
        const data = await resp.json();
        console.log('  Total:', data.sessions?.length || 0);
        console.log('  Sessions:', data.sessions);
        console.log('  Current in list:', data.sessions?.some(s => s.session_id === sessionId) ? '✅' : '❌');
    } catch (e) {
        console.error('  ❌ Failed:', e);
    }

    // 4. 拆分请求模拟
    console.log('\n4. Split Request Test:');
    const config = {
        session_id: sessionId,
        source_lang: "EN",
        target_langs: ["TR"],
        extract_context: true,
        context_options: {}
    };
    console.log('  Request payload:', config);

    try {
        const resp = await fetch('/api/tasks/split', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        });
        if (resp.ok) {
            const data = await resp.json();
            console.log('  ✅ Split success:', data);
        } else {
            const error = await resp.json();
            console.error('  ❌ Split failed:', resp.status, error);
        }
    } catch (e) {
        console.error('  ❌ Request failed:', e);
    }

    console.log('\n=== DIAGNOSIS COMPLETE ===');
})();
```

## 总结

**最可能的原因（按概率排序）：**

1. **前端 sessionManager.session 为 null/undefined** (70%)
   - 页面刷新后 sessionManager 对象重置
   - localStorage有数据但没有加载到 sessionManager

2. **后端session被清理** (20%)
   - 超时清理
   - Docker重启

3. **session_id 不匹配** (10%)
   - 前后端使用了不同的ID

**立即执行：**

1. 在浏览器Console运行诊断脚本（上面的最终诊断脚本）
2. 截图所有Console输出
3. 检查Network请求的Payload

---

**文档生成时间：** 2025-10-04
**问题：** Session not found in split request
**分析者：** Claude Code
