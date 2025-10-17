# 最近项目列表 - 功能说明

## 新增功能概览

极简上传页面中的"最近项目"列表现已支持：

✅ **复选框选择** - 单选/多选项目
✅ **全选功能** - 一键全选当前页所有项目
✅ **批量删除** - 一次删除多个项目
✅ **单个删除** - 独立删除按钮
✅ **分页显示** - 每页10个项目，支持翻页
✅ **状态显示** - 项目状态徽章
✅ **操作按钮** - 根据状态显示不同操作

---

## UI 界面

```
┌────────────────────────────────────────────────────────┐
│  最近项目                [删除选中(3)]  [查看全部→]   │
├────────────────────────────────────────────────────────┤
│  ☑️ 全选        共 47 个项目                          │
├────────────────────────────────────────────────────────┤
│  ☑️  📄 game_v1.xlsx                    [继续] [🗑️]   │
│      3分钟前 • 待配置                                  │
├────────────────────────────────────────────────────────┤
│  ☐  📄 translation_final.xlsx            [📥] [🗑️]   │
│      1小时前 • 已完成                                  │
├────────────────────────────────────────────────────────┤
│  ☑️  📄 test_caps.xlsx                   [继续] [🗑️]   │
│      2小时前 • 待配置                                  │
├────────────────────────────────────────────────────────┤
│  ...                                                   │
├────────────────────────────────────────────────────────┤
│  [<]  [1]  [2]  [3]  [4]  [5]  [>]                    │
└────────────────────────────────────────────────────────┘
```

---

## 功能详解

### 1. 复选框选择

每个项目前都有一个复选框，支持单独选中：

```javascript
// 选中状态保存在 Set 中
this.selectedSessions = new Set();

// 切换选中状态
toggleSession(sessionId, checked) {
  if (checked) {
    this.selectedSessions.add(sessionId);
  } else {
    this.selectedSessions.delete(sessionId);
  }
  this.updateSelectedCount();
}
```

**特性**：
- 选中状态跨页面保持
- 实时更新选中计数
- 自动更新"全选"复选框状态（全选/半选/未选）

### 2. 全选功能

顶部的"全选"复选框支持三种状态：

| 状态 | 显示 | 说明 |
|------|------|------|
| 未选中 | ☐ | 当前页没有选中任何项目 |
| 半选 | ☑️ (indeterminate) | 当前页选中了部分项目 |
| 全选 | ✅ | 当前页所有项目都被选中 |

```javascript
toggleSelectAll(checked) {
  const checkboxes = document.querySelectorAll('.session-checkbox');
  checkboxes.forEach(checkbox => {
    const sessionId = checkbox.dataset.sessionId;
    checkbox.checked = checked;
    if (checked) {
      this.selectedSessions.add(sessionId);
    } else {
      this.selectedSessions.delete(sessionId);
    }
  });
  this.updateSelectedCount();
}
```

**注意**：全选只影响当前页，不会选中其他页的项目。

### 3. 批量删除

选中项目后，右上角会显示"删除选中"按钮：

```
[删除选中 (3)]  ← 显示选中的项目数量
```

**流程**：
1. 选中一个或多个项目
2. 点击"删除选中"按钮
3. 确认对话框：`确认删除选中的 3 个项目？`
4. 逐个调用删除API
5. 显示结果：`成功删除 3 个项目`

```javascript
async batchDeleteSessions() {
  const count = this.selectedSessions.size;
  if (count === 0) return;

  const confirmed = confirm(`确认删除选中的 ${count} 个项目？\n\n此操作不可恢复。`);
  if (!confirmed) return;

  const sessionIds = Array.from(this.selectedSessions);
  let successCount = 0;
  let failCount = 0;

  this.showLoading(`正在删除 ${count} 个项目...`);

  for (const sessionId of sessionIds) {
    try {
      await window.api.deleteSession(sessionId);
      successCount++;
    } catch (error) {
      failCount++;
    }
  }

  // 显示结果
  if (failCount === 0) {
    this.showToast(`成功删除 ${successCount} 个项目`, 'success');
  } else {
    this.showToast(`删除完成：成功 ${successCount} 个，失败 ${failCount} 个`, 'warning');
  }
}
```

**特性**：
- 显示加载状态
- 逐个删除（避免并发问题）
- 容错处理（部分失败不影响其他）
- 清除API缓存
- 自动刷新列表

### 4. 单个删除

每个项目右侧都有独立的删除按钮 🗑️：

```javascript
async deleteSingleSession(sessionId, filename) {
  const confirmed = confirm(`确认删除项目 "${filename}"？\n\n此操作不可恢复。`);
  if (!confirmed) return;

  try {
    await window.api.deleteSession(sessionId);
    window.api.clearCache();

    this.selectedSessions.delete(sessionId);
    this.showToast('删除成功', 'success');

    await this.loadRecentProjects();
  } catch (error) {
    this.showToast('删除失败: ' + error.message, 'error');
  }
}
```

**特性**：
- 确认对话框显示文件名
- 删除成功后自动刷新列表
- Toast提示反馈
- 从选中集合中移除

### 5. 分页功能

每页显示10个项目，自动生成分页控件：

```
[<]  [1]  [2]  [3]  ...  [10]  [>]
```

**特性**：
- 智能省略号（超过5页时显示）
- 当前页高亮显示
- 首尾按钮（快速跳转）
- 上一页/下一页按钮
- 边界禁用（第1页禁用上一页，最后页禁用下一页）

```javascript
renderPagination() {
  const totalPages = Math.ceil(this.totalSessions / this.pageSize);
  const maxVisiblePages = 5;

  // 计算显示范围
  let startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
  let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

  // 生成分页HTML
  // [<] [1] ... [4] [5] [6] ... [10] [>]
}
```

**分页策略**：
- 总是显示第1页和最后一页
- 当前页居中显示
- 最多显示5个连续页码
- 使用 `...` 表示省略

### 6. 状态显示

每个项目显示不同状态的徽章：

| 状态 | 徽章 | 颜色 | 说明 |
|------|------|------|------|
| created | 待配置 | 蓝色 (info) | 刚上传，未配置 |
| split_complete | 已配置 | 蓝色 (info) | 已拆分，未执行 |
| executing | 执行中 | 黄色 (warning) | 正在翻译 |
| completed | 已完成 | 绿色 (success) | 翻译完成 |
| failed | 失败 | 红色 (error) | 执行失败 |

```javascript
getStatusBadgeClass(stage) {
  const classMap = {
    'created': 'badge-info',
    'split_complete': 'badge-info',
    'executing': 'badge-warning',
    'completed': 'badge-success',
    'failed': 'badge-error'
  };
  return classMap[stage] || 'badge-ghost';
}
```

### 7. 智能操作按钮

根据项目状态显示不同的操作按钮：

| 状态 | 显示按钮 | 功能 |
|------|----------|------|
| 待配置 | [继续] [🗑️] | 继续配置 + 删除 |
| 已配置 | [继续] [🗑️] | 继续执行 + 删除 |
| 执行中 | [👁️] | 查看进度 |
| 已完成 | [📥] [🗑️] | 下载结果 + 删除 |
| 失败 | [继续] [🗑️] | 重试 + 删除 |

```javascript
renderSessionActions(session) {
  if (session.stage === 'executing') {
    return `
      <button class="btn btn-sm btn-ghost" onclick="simpleUploadPage.viewSession('${session.sessionId}')">
        <i class="bi bi-eye"></i>
      </button>
    `;
  } else if (session.stage === 'completed') {
    return `
      <button class="btn btn-sm btn-success btn-outline" onclick="simpleUploadPage.downloadSession('${session.sessionId}')">
        <i class="bi bi-download"></i>
      </button>
      <button class="btn btn-sm btn-error btn-ghost" onclick="simpleUploadPage.deleteSingleSession('${session.sessionId}', '${session.filename}')">
        <i class="bi bi-trash"></i>
      </button>
    `;
  } else {
    return `
      <button class="btn btn-sm btn-primary btn-outline" onclick="simpleUploadPage.continueSession('${session.sessionId}')">
        <i class="bi bi-play-fill"></i>
        继续
      </button>
      <button class="btn btn-sm btn-error btn-ghost" onclick="simpleUploadPage.deleteSingleSession('${session.sessionId}', '${session.filename}')">
        <i class="bi bi-trash"></i>
      </button>
    `;
  }
}
```

---

## 交互细节

### 选中状态管理

```javascript
// 使用 Set 存储选中的 sessionId
this.selectedSessions = new Set();

// 优点：
// 1. 自动去重
// 2. 快速查找 O(1)
// 3. 方便转换为数组
```

### 半选状态（Indeterminate）

当部分项目被选中时，"全选"复选框显示为半选状态：

```javascript
const selectAllCheckbox = document.getElementById('selectAllCheckbox');
selectAllCheckbox.indeterminate = count > 0 && count < checkboxes.length;
```

效果：
- `indeterminate = false, checked = false` → ☐ 未选
- `indeterminate = true` → ☑️ 半选（横线）
- `indeterminate = false, checked = true` → ✅ 全选

### 分页后选中状态保持

切换页面后，之前选中的项目状态会保留：

```javascript
// 渲染时检查选中状态
${this.selectedSessions.has(session.sessionId) ? 'checked' : ''}
```

### Toast 通知

成功/失败操作都有Toast提示：

```javascript
this.showToast('删除成功', 'success');  // 绿色
this.showToast('删除失败', 'error');    // 红色
this.showToast('部分成功', 'warning');   // 黄色
```

特性：
- 固定在右上角
- 3秒后自动消失
- 淡出动画
- 多个Toast不会重叠

---

## 配置选项

### 修改每页显示数量

```javascript
constructor() {
  // ...
  this.pageSize = 10;  // 修改这里，可设置为 5, 10, 20, 50 等
}
```

### 修改最大可见页码数

```javascript
renderPagination() {
  const maxVisiblePages = 5;  // 修改这里，可设置为 3, 5, 7 等
  // ...
}
```

### 禁用批量删除

```javascript
// 注释掉批量删除按钮
/*
<button class="btn btn-sm btn-error btn-outline gap-2 hidden" id="batchDeleteBtn">
  删除选中
</button>
*/
```

---

## API依赖

需要后端提供以下API：

```
GET /api/sessions
  - 获取所有会话列表
  - 返回: { sessions: [...], count: N }

DELETE /api/sessions/{session_id}
  - 删除单个会话
  - 返回: { status: 'success', session_id, deleted_files: [...] }

GET /api/download/{session_id}
  - 下载会话结果文件
  - 返回: Blob (Excel文件)

GET /api/download/{session_id}/info
  - 获取下载文件信息
  - 返回: { filename, size, ... }
```

---

## 性能优化

### 1. 前端分页

所有数据一次性加载，前端进行分页：

```javascript
const sessions = allSessions.slice(startIndex, endIndex);
```

**优点**：
- 切换页面无需请求API
- 响应快速

**缺点**：
- 首次加载时间稍长（如果项目很多）

**建议**：
- 项目数 < 100：使用前端分页
- 项目数 > 100：考虑后端分页

### 2. 批量删除优化

逐个删除而非并发删除：

```javascript
for (const sessionId of sessionIds) {
  await window.api.deleteSession(sessionId);
}
```

**原因**：
- 避免并发请求过多
- 容错处理更简单
- 可以显示进度

**改进方向**：
- 限制并发数（如3个）
- 显示实时进度条

### 3. 缓存清除

删除后清除API缓存：

```javascript
window.api.clearCache();
```

确保下次加载时获取最新数据。

---

## 键盘快捷键（未来扩展）

可以添加键盘快捷键支持：

```javascript
document.addEventListener('keydown', (e) => {
  // Ctrl+A 全选
  if (e.ctrlKey && e.key === 'a') {
    e.preventDefault();
    this.toggleSelectAll(true);
  }

  // Delete 删除选中
  if (e.key === 'Delete' && this.selectedSessions.size > 0) {
    this.batchDeleteSessions();
  }
});
```

---

## 总结

新增的最近项目列表功能完整实现了：

✅ **复选和全选** - 灵活的项目选择
✅ **批量操作** - 一次删除多个项目
✅ **分页显示** - 大量项目也不卡顿
✅ **状态管理** - 清晰的项目状态
✅ **智能操作** - 根据状态显示合适的按钮
✅ **用户反馈** - Toast提示和确认对话框

所有功能都已集成到 `simple-upload-page.js` 中，无需额外配置即可使用！
