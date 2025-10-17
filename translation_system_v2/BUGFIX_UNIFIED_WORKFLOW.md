# 统一工作流页面 - Bug修复记录

## 问题1: 第二次拆分（CAPS）缺少 target_langs 参数

### 错误信息
```bash
curl 'http://localhost:8013/api/tasks/split' \
  --data-raw '...parent_session_id=xxx&rule_set=caps_only&extract_context=false...'

{"detail":"target_langs is required"}
```

### 根本原因
在执行CAPS拆分时，FormData中没有包含 `target_langs` 参数，导致后端验证失败。

### 修复方案
```javascript
// 修复前 ❌
const splitFormData = new FormData();
splitFormData.append('parent_session_id', parentSessionId);
splitFormData.append('rule_set', 'caps_only');
splitFormData.append('extract_context', 'false');

// 修复后 ✅
const targetLangs = document.getElementById('targetLangs').value.split(',').map(s => s.trim());
const splitFormData = new FormData();
splitFormData.append('parent_session_id', parentSessionId);
splitFormData.append('target_langs', JSON.stringify(targetLangs));  // 添加 target_langs
splitFormData.append('rule_set', 'caps_only');
splitFormData.append('extract_context', 'false');
```

**文件**: `frontend_v2/js/pages/unified-workflow-page.js:393-398`

---

## 问题2: 页面没有展示翻译进度

### 症状
- 后端日志显示翻译正在执行并有进度
- WebSocket连接被拒绝（403 Forbidden）
- 前端页面进度条停留在0%，没有更新

### 后端日志
```
2025-10-17 14:22:57,536 - ConnectionManager - INFO - Broadcasting progress to session ed019d95-947d-4655-b81d-c6efa7276eaa: 0.0% (0/7)
INFO:     ('127.0.0.1', 38014) - "WebSocket /api/websocket/progress/ed019d95-947d-4655-b81d-c6efa7276eaa" 403
INFO:     connection rejected (403 Forbidden)
```

### 根本原因
1. WebSocket连接失败（可能是session未准备好或权限问题）
2. 原代码没有实现轮询回退机制
3. 轮询逻辑中缺少详细的进度和状态更新

### 修复方案

#### 1. 改进轮询执行状态方法
```javascript
// 修复前 ❌ - 简单轮询，没有状态更新
async pollExecutionStatus(sessionId, phaseNum) {
  while (true) {
    const response = await fetch(`${this.apiUrl}/api/execute/status/${sessionId}`);
    const data = await response.json();

    const progress = total > 0 ? Math.round((completed / total) * 100) : 0;
    // 只更新进度条
    document.getElementById(`phase${phaseNum}Progress`).style.width = `${progress}%`;

    if (data.status === 'completed') return;
    await this.delay(2000);
  }
}

// 修复后 ✅ - 完整的进度和状态更新
async pollExecutionStatus(sessionId, phaseNum) {
  let attemptCount = 0;
  const maxAttempts = 300; // 最多轮询10分钟

  while (attemptCount < maxAttempts) {
    attemptCount++;

    try {
      const response = await fetch(`${this.apiUrl}/api/execute/status/${sessionId}`);
      const data = await response.json();

      const stats = data.statistics || {};
      const byStatus = stats.by_status || {};
      const total = stats.total || 0;
      const completed = byStatus.completed || 0;
      const processing = byStatus.processing || 0;
      const failed = byStatus.failed || 0;
      const progress = total > 0 ? Math.round((completed / total) * 100) : 0;

      // 更新进度条
      document.getElementById(`phase${phaseNum}Progress`).style.width = `${progress}%`;
      document.getElementById(`phase${phaseNum}Progress`).textContent = `${progress}%`;

      // 更新详细文本
      document.getElementById(`phase${phaseNum}Text`).textContent =
        `已完成 ${completed}/${total} | 处理中: ${processing} | 失败: ${failed}`;

      // 更新状态框
      if (data.status === 'completed') {
        this.updatePhaseStatus(phaseNum, 'success', `✅ 已完成 ${completed}/${total} 任务`);
        return;
      } else if (data.status === 'failed') {
        this.updatePhaseStatus(phaseNum, 'error', `❌ 执行失败 (${failed} 个任务失败)`);
        throw new Error('执行失败');
      } else if (data.status === 'running' || data.status === 'processing') {
        this.updatePhaseStatus(phaseNum, 'processing', `⚡ 正在处理... ${completed}/${total}`);
      }

    } catch (error) {
      console.error(`Poll error (attempt ${attemptCount}):`, error);
      if (attemptCount >= maxAttempts) throw error;
    }

    await this.delay(2000);
  }

  throw new Error('执行超时');
}
```

**文件**: `frontend_v2/js/pages/unified-workflow-page.js:464-511`

#### 2. 改进拆分状态轮询
```javascript
// 修复后 ✅ - 添加超时保护和错误处理
async pollSplitStatus(sessionId) {
  let attemptCount = 0;
  const maxAttempts = 60; // 最多等待1分钟

  while (attemptCount < maxAttempts) {
    attemptCount++;

    try {
      const response = await fetch(`${this.apiUrl}/api/tasks/split/status/${sessionId}`);
      const data = await response.json();

      if (data.status === 'completed') {
        console.log(`Split completed: ${data.task_count || 0} tasks`);
        return;
      } else if (data.status === 'failed') {
        throw new Error(data.message || '拆分失败');
      }

    } catch (error) {
      console.error(`Poll split error (attempt ${attemptCount}):`, error);
      if (attemptCount >= maxAttempts) throw error;
    }

    await this.delay(1000);
  }

  throw new Error('拆分超时');
}
```

**文件**: `frontend_v2/js/pages/unified-workflow-page.js:446-481`

---

## 修复总结

### 修改文件
1. `frontend_v2/js/pages/unified-workflow-page.js`

### 关键改进

✅ **CAPS拆分修复**
- 添加 `target_langs` 参数到FormData
- 确保CAPS拆分请求包含所有必需参数

✅ **进度显示修复**
- 完整实现轮询进度监控
- 显示任务完成数、处理中数量、失败数量
- 实时更新进度条和百分比
- 更新状态框显示详细信息

✅ **错误处理增强**
- 添加超时保护（执行10分钟，拆分1分钟）
- 添加重试计数和错误日志
- 更清晰的错误消息

### 测试验证

**测试步骤**:
1. 访问 `http://127.0.0.1:8090/#/upload`
2. 上传包含CAPS sheet的Excel文件
3. 观察三个阶段的进度条
4. 验证每个阶段的进度实时更新
5. 验证CAPS阶段正常执行（无target_langs错误）
6. 下载各阶段的中间结果

**预期结果**:
- ✅ 阶段1: 拆分和翻译进度正常显示
- ✅ 阶段2: 翻译执行进度实时更新（完成数/总数/处理中/失败）
- ✅ 阶段3: CAPS检测和转换正常执行
- ✅ 所有阶段都可以下载中间结果

---

**修复日期**: 2025-10-17
**修复者**: Claude
