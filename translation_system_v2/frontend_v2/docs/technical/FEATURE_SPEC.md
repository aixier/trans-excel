# 功能实现说明
## StringLock - 详细功能规格

> **文档版本**: v1.0
> **最后更新**: 2025-10-17
> **作者**: 产品团队 + 技术团队
> **状态**: Draft（草稿）

---

## 📋 目录

1. [文档目的](#文档目的)
2. [功能模块详述](#功能模块详述)
3. [API对接说明](#api对接说明)
4. [状态管理方案](#状态管理方案)
5. [错误处理策略](#错误处理策略)
6. [性能优化方案](#性能优化方案)

---

## 📖 文档目的

本文档旨在为前端开发团队提供详细的功能实现说明，包括：

1. **业务逻辑** - 每个功能的详细流程和边界条件
2. **API对接** - 前后端接口对接规范
3. **状态管理** - 数据流转和状态管理方案
4. **异常处理** - 错误场景和处理策略
5. **性能优化** - 关键路径的性能优化

---

## 🧩 功能模块详述

### 1️⃣ 智能工作台（Dashboard）

#### 1.1 核心指标卡片

**业务逻辑**:
```javascript
/**
 * 获取工作台统计数据
 */
async function loadDashboardStats() {
  try {
    // 1. 从LocalStorage获取所有会话
    const sessions = SessionManager.getAllSessions();

    // 2. 过滤今日会话
    const today = new Date().toDateString();
    const todaySessions = sessions.filter(s =>
      new Date(s.createdAt).toDateString() === today
    );

    // 3. 统计待办（未完成的会话）
    const pendingSessions = sessions.filter(s =>
      s.stage !== 'completed' && s.stage !== 'failed'
    );

    // 4. 统计执行中
    const runningSessions = sessions.filter(s =>
      s.stage === 'executing'
    );

    // 5. 统计本月完成
    const monthStart = new Date();
    monthStart.setDate(1);
    monthStart.setHours(0, 0, 0, 0);

    const completedThisMonth = sessions.filter(s =>
      s.stage === 'completed' &&
      new Date(s.completedAt) >= monthStart
    );

    // 6. 计算本月成本
    const monthlyCost = completedThisMonth.reduce((sum, s) => {
      return sum + (s.executionResult?.cost || 0);
    }, 0);

    // 7. 返回统计数据
    return {
      todayPending: todaySessions.filter(s => s.stage !== 'completed').length,
      running: runningSessions.length,
      runningProgress: runningSessions.length > 0
        ? runningSessions[0].progress || 0
        : 0,
      monthlyCompleted: completedThisMonth.length,
      monthlyCost: monthlyCost,
      budget: 50.0  // 从配置读取
    };
  } catch (error) {
    console.error('Failed to load dashboard stats:', error);
    throw error;
  }
}
```

**渲染逻辑**:
```javascript
function renderStatCards(stats) {
  // 今日待办
  document.getElementById('todayPending').textContent = stats.todayPending;
  document.getElementById('pendingTrend').textContent = `↑ ${stats.pendingTrend || 0}`;

  // 执行中任务
  document.getElementById('running').textContent = stats.running;
  if (stats.running > 0) {
    document.getElementById('runningProgress').value = stats.runningProgress;
    document.getElementById('runningPercent').textContent = `${stats.runningProgress}%`;
  }

  // 本月完成
  document.getElementById('monthlyCompleted').textContent = stats.monthlyCompleted;

  // 本月成本
  document.getElementById('monthlyCost').textContent = `$${stats.monthlyCost.toFixed(2)}`;
  const budgetPercent = (stats.monthlyCost / stats.budget) * 100;
  document.getElementById('budgetProgress').value = budgetPercent;

  // 成本预警（超过80%显示警告）
  if (budgetPercent > 80) {
    document.getElementById('costWarning').classList.remove('hidden');
  }
}
```

#### 1.2 最近项目列表

**数据加载**:
```javascript
/**
 * 加载最近项目列表
 * @param {number} limit - 显示条数，默认10
 */
async function loadRecentSessions(limit = 10) {
  try {
    // 1. 从LocalStorage获取所有会话
    const sessions = SessionManager.getAllSessions();

    // 2. 按更新时间排序
    sessions.sort((a, b) => b.updatedAt - a.updatedAt);

    // 3. 取前N条
    const recentSessions = sessions.slice(0, limit);

    // 4. 对于执行中的会话，实时更新进度
    const runningSessions = recentSessions.filter(s => s.stage === 'executing');
    if (runningSessions.length > 0) {
      // 启动轮询更新进度
      startProgressPolling(runningSessions);
    }

    return recentSessions;
  } catch (error) {
    console.error('Failed to load recent sessions:', error);
    throw error;
  }
}
```

**表格渲染**:
```javascript
function renderSessionTable(sessions) {
  const tbody = document.querySelector('#sessionTable tbody');
  tbody.innerHTML = '';

  sessions.forEach(session => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>
        <input type="checkbox" class="checkbox checkbox-sm"
               data-session-id="${session.sessionId}"/>
      </td>
      <td>
        <div class="flex items-center gap-2">
          <i class="bi bi-file-earmark-excel text-success"></i>
          <span class="font-medium">${session.filename}</span>
        </div>
      </td>
      <td>${renderStatusBadge(session.stage)}</td>
      <td>${renderProgress(session)}</td>
      <td>${formatTimeAgo(session.updatedAt)}</td>
      <td>${renderActions(session)}</td>
    `;
    tbody.appendChild(row);
  });
}

function renderStatusBadge(stage) {
  const statusMap = {
    'created': { icon: 'bi-circle', label: '待配置', class: 'badge-info' },
    'configured': { icon: 'bi-gear', label: '已配置', class: 'badge-info' },
    'executing': { icon: 'bi-lightning-fill', label: '执行中', class: 'badge-warning' },
    'completed': { icon: 'bi-check-circle-fill', label: '已完成', class: 'badge-success' },
    'failed': { icon: 'bi-x-circle-fill', label: '失败', class: 'badge-error' }
  };

  const status = statusMap[stage] || statusMap.created;
  return `
    <span class="badge ${status.class} gap-1">
      <i class="${status.icon}"></i>
      ${status.label}
    </span>
  `;
}

function renderProgress(session) {
  if (session.stage === 'executing' && session.progress) {
    return `
      <div class="flex items-center gap-2">
        <progress class="progress progress-warning w-20"
                  value="${session.progress.completed}"
                  max="${session.progress.total}"></progress>
        <span class="text-sm">${Math.round((session.progress.completed / session.progress.total) * 100)}%</span>
      </div>
    `;
  } else if (session.stage === 'completed') {
    return `
      <div class="flex items-center gap-2">
        <progress class="progress progress-success w-20" value="100" max="100"></progress>
        <span class="text-sm">100%</span>
      </div>
    `;
  } else {
    return '<span class="text-base-content/50">—</span>';
  }
}
```

**实时进度更新**:
```javascript
/**
 * 启动进度轮询（仅用于执行中的会话）
 */
function startProgressPolling(sessions) {
  // 每5秒轮询一次
  const pollInterval = setInterval(async () => {
    for (const session of sessions) {
      try {
        const progress = await API.getExecutionProgress(session.sessionId);

        // 更新LocalStorage
        SessionManager.updateSessionProgress(session.sessionId, progress);

        // 更新UI
        updateProgressInTable(session.sessionId, progress);

        // 如果完成，停止轮询
        if (progress.completed >= progress.total) {
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error(`Failed to poll progress for ${session.sessionId}:`, error);
      }
    }
  }, 5000);

  // 页面卸载时清除定时器
  window.addEventListener('beforeunload', () => {
    clearInterval(pollInterval);
  });
}
```

---

### 2️⃣ 会话管理（Sessions）

#### 2.1 筛选功能

**筛选器数据结构**:
```javascript
const filterState = {
  searchText: '',       // 搜索关键词
  timeRange: 'all',     // all|today|week|month|custom
  customStart: null,    // 自定义开始日期
  customEnd: null,      // 自定义结束日期
  status: 'all',        // all|created|executing|completed|failed
  project: 'all'        // all|project1|project2
};
```

**筛选逻辑**:
```javascript
function applyFilters(sessions, filters) {
  let filtered = [...sessions];

  // 1. 搜索过滤
  if (filters.searchText) {
    const searchLower = filters.searchText.toLowerCase();
    filtered = filtered.filter(s =>
      s.filename.toLowerCase().includes(searchLower) ||
      s.sessionId.toLowerCase().includes(searchLower)
    );
  }

  // 2. 时间范围过滤
  if (filters.timeRange !== 'all') {
    const now = new Date();
    let startDate;

    switch (filters.timeRange) {
      case 'today':
        startDate = new Date(now.setHours(0, 0, 0, 0));
        break;
      case 'week':
        startDate = new Date(now.setDate(now.getDate() - 7));
        break;
      case 'month':
        startDate = new Date(now.setMonth(now.getMonth() - 1));
        break;
      case 'custom':
        startDate = filters.customStart;
        break;
    }

    filtered = filtered.filter(s => new Date(s.createdAt) >= startDate);

    if (filters.timeRange === 'custom' && filters.customEnd) {
      filtered = filtered.filter(s => new Date(s.createdAt) <= filters.customEnd);
    }
  }

  // 3. 状态过滤
  if (filters.status !== 'all') {
    filtered = filtered.filter(s => s.stage === filters.status);
  }

  // 4. 项目过滤
  if (filters.project !== 'all') {
    filtered = filtered.filter(s =>
      s.gameInfo?.game_name === filters.project
    );
  }

  return filtered;
}
```

#### 2.2 批量操作

**选择状态管理**:
```javascript
class SelectionManager {
  constructor() {
    this.selectedIds = new Set();
  }

  toggleSelect(sessionId) {
    if (this.selectedIds.has(sessionId)) {
      this.selectedIds.delete(sessionId);
    } else {
      this.selectedIds.add(sessionId);
    }
    this.updateUI();
  }

  selectAll(sessionIds) {
    sessionIds.forEach(id => this.selectedIds.add(id));
    this.updateUI();
  }

  clearAll() {
    this.selectedIds.clear();
    this.updateUI();
  }

  getSelected() {
    return Array.from(this.selectedIds);
  }

  updateUI() {
    // 更新全选checkbox状态
    const allCheckboxes = document.querySelectorAll('input[data-session-id]');
    const checkedCount = Array.from(allCheckboxes).filter(cb => cb.checked).length;

    const selectAllCheckbox = document.getElementById('selectAll');
    selectAllCheckbox.checked = checkedCount === allCheckboxes.length;
    selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < allCheckboxes.length;

    // 显示/隐藏批量操作栏
    const batchToolbar = document.getElementById('batchToolbar');
    if (this.selectedIds.size > 0) {
      batchToolbar.classList.remove('hidden');
      document.getElementById('selectedCount').textContent = this.selectedIds.size;
    } else {
      batchToolbar.classList.add('hidden');
    }
  }
}
```

**批量下载**:
```javascript
async function batchDownload(sessionIds) {
  try {
    UIHelper.showLoading(true, `正在打包 ${sessionIds.length} 个文件...`);

    // 方案1：后端打包（推荐）
    const response = await API.batchDownload(sessionIds);
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `translations_${Date.now()}.zip`;
    a.click();

    // 方案2：前端逐个下载（备选）
    // for (const sessionId of sessionIds) {
    //   await API.downloadSession(sessionId);
    // }

    UIHelper.showToast('批量下载成功', 'success');
  } catch (error) {
    UIHelper.showToast(`批量下载失败: ${error.message}`, 'error');
  } finally {
    UIHelper.showLoading(false);
  }
}
```

**批量删除**:
```javascript
async function batchDelete(sessionIds) {
  // 二次确认
  const confirmed = await UIHelper.showDialog({
    type: 'warning',
    title: '确认删除',
    message: `确定要删除这 ${sessionIds.length} 个会话吗？删除后无法恢复。`,
    actions: [
      { label: '取消', className: 'btn-ghost' },
      {
        label: '确定删除',
        className: 'btn-error',
        action: async () => {
          try {
            UIHelper.showLoading(true, '删除中...');

            // 逐个删除（后端可能没有批量删除接口）
            const results = await Promise.allSettled(
              sessionIds.map(id => API.deleteSession(id))
            );

            const successCount = results.filter(r => r.status === 'fulfilled').length;
            const failCount = results.filter(r => r.status === 'rejected').length;

            // 从LocalStorage删除
            sessionIds.forEach(id => SessionManager.deleteSession(id));

            // 刷新列表
            await loadSessions();

            // 清除选择
            selectionManager.clearAll();

            UIHelper.showToast(
              `删除完成: 成功 ${successCount} 个，失败 ${failCount} 个`,
              failCount > 0 ? 'warning' : 'success'
            );
          } catch (error) {
            UIHelper.showToast(`删除失败: ${error.message}`, 'error');
          } finally {
            UIHelper.showLoading(false);
          }
        }
      }
    ]
  });
}
```

#### 2.3 会话详情侧边栏

**抽屉式侧边栏**:
```javascript
class SessionDetailDrawer {
  constructor() {
    this.drawer = null;
    this.sessionId = null;
  }

  async open(sessionId) {
    this.sessionId = sessionId;

    // 创建抽屉DOM
    this.drawer = document.createElement('div');
    this.drawer.className = 'drawer drawer-end drawer-open';
    this.drawer.innerHTML = `
      <input type="checkbox" class="drawer-toggle" checked/>
      <div class="drawer-side">
        <label class="drawer-overlay" onclick="sessionDetailDrawer.close()"></label>
        <div class="bg-base-100 w-96 p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-bold">会话详情</h2>
            <button class="btn btn-sm btn-ghost btn-circle" onclick="sessionDetailDrawer.close()">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
          <div id="drawerContent">
            <div class="loading loading-spinner loading-lg"></div>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(this.drawer);

    // 加载详情数据
    await this.loadDetails(sessionId);
  }

  async loadDetails(sessionId) {
    try {
      // 1. 从LocalStorage获取基本信息
      const session = SessionManager.getSession(sessionId);

      // 2. 从后端获取最新统计信息
      const stats = await API.getSessionStats(sessionId);

      // 3. 合并数据
      const details = { ...session, ...stats };

      // 4. 渲染内容
      this.renderContent(details);
    } catch (error) {
      document.getElementById('drawerContent').innerHTML = `
        <div class="alert alert-error">
          <i class="bi bi-exclamation-triangle"></i>
          <span>加载失败: ${error.message}</span>
        </div>
      `;
    }
  }

  renderContent(details) {
    const content = document.getElementById('drawerContent');
    content.innerHTML = `
      <!-- 基本信息 -->
      <div class="mb-6">
        <h3 class="font-semibold mb-2 flex items-center gap-2">
          <i class="bi bi-file-earmark-excel"></i>
          基本信息
        </h3>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-base-content/60">文件名</span>
            <span class="font-medium">${details.filename}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-base-content/60">Session ID</span>
            <div class="flex items-center gap-2">
              <code class="text-xs">${details.sessionId.substring(0, 16)}...</code>
              <button class="btn btn-xs btn-ghost" onclick="navigator.clipboard.writeText('${details.sessionId}')">
                <i class="bi bi-clipboard"></i>
              </button>
            </div>
          </div>
          <div class="flex justify-between">
            <span class="text-base-content/60">上传时间</span>
            <span>${new Date(details.createdAt).toLocaleString()}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-base-content/60">文件大小</span>
            <span>${UIHelper.formatFileSize(details.fileSize || 0)}</span>
          </div>
        </div>
      </div>

      <!-- 配置信息 -->
      ${this.renderConfigInfo(details)}

      <!-- 执行统计 -->
      ${this.renderExecutionStats(details)}

      <!-- 成本统计 -->
      ${this.renderCostStats(details)}

      <!-- 操作日志 -->
      ${this.renderLogs(details)}

      <!-- 操作按钮 -->
      <div class="flex gap-2 mt-6">
        <button class="btn btn-primary flex-1" onclick="router.navigate('/execute/${details.sessionId}')">
          <i class="bi bi-eye"></i>
          查看详情
        </button>
        ${details.stage === 'completed' ? `
          <button class="btn btn-success flex-1" onclick="executePage.downloadResult('${details.sessionId}')">
            <i class="bi bi-download"></i>
            下载结果
          </button>
        ` : ''}
      </div>
    `;
  }

  close() {
    if (this.drawer) {
      this.drawer.remove();
      this.drawer = null;
    }
  }
}
```

---

### 3️⃣ 术语库管理（Glossary）

#### 3.1 术语库CRUD

**数据结构**:
```javascript
// 术语库
const glossary = {
  id: 'glossary-uuid-123',
  name: '游戏通用术语',
  description: '游戏中常用的通用术语翻译',
  createdAt: 1697520000000,
  updatedAt: 1697520000000,
  termCount: 500,
  active: true,  // 是否激活
  version: 1,
  terms: [...]   // 术语列表（或者分页加载）
};

// 术语条目
const term = {
  id: 'term-uuid-456',
  source: '攻击力',           // 源术语
  translations: {            // 多语言翻译
    EN: 'ATK',
    JP: '攻撃力',
    TH: 'พลังโจมตี'
  },
  notes: '属性名称，常用于角色面板',
  tags: ['属性', '通用'],
  context: '',              // 使用场景
  createdAt: 1697520000000,
  updatedAt: 1697520000000
};
```

**创建术语库**:
```javascript
async function createGlossary(glossaryData) {
  try {
    UIHelper.showLoading(true);

    // 1. 验证数据
    if (!glossaryData.name || !glossaryData.name.trim()) {
      throw new Error('术语库名称不能为空');
    }

    // 2. 调用API创建
    const result = await API.createGlossary({
      name: glossaryData.name,
      description: glossaryData.description || '',
      terms: []  // 初始为空
    });

    // 3. 刷新列表
    await loadGlossaryList();

    // 4. 跳转到新创建的术语库
    selectGlossary(result.id);

    UIHelper.showToast('术语库创建成功', 'success');

    return result;
  } catch (error) {
    UIHelper.showToast(`创建失败: ${error.message}`, 'error');
    throw error;
  } finally {
    UIHelper.showLoading(false);
  }
}
```

**导入术语库**:
```javascript
async function importGlossary(file, glossaryId) {
  try {
    UIHelper.showLoading(true, '解析文件中...');

    // 1. 解析Excel文件
    const data = await parseExcelFile(file);

    // 2. 验证数据格式
    const validation = validateGlossaryData(data);
    if (!validation.valid) {
      throw new Error(validation.message);
    }

    // 3. 预览导入数据（前10条）
    const confirmed = await showImportPreview(data.slice(0, 10));
    if (!confirmed) {
      return;
    }

    UIHelper.showLoading(true, '导入中...');

    // 4. 调用API批量导入
    const result = await API.importTerms(glossaryId, data);

    // 5. 刷新术语列表
    await loadTerms(glossaryId);

    UIHelper.showToast(
      `导入成功: ${result.successCount} 条，失败: ${result.failCount} 条`,
      result.failCount > 0 ? 'warning' : 'success'
    );

    return result;
  } catch (error) {
    UIHelper.showToast(`导入失败: ${error.message}`, 'error');
    throw error;
  } finally {
    UIHelper.showLoading(false);
  }
}

// 解析Excel文件（使用SheetJS）
async function parseExcelFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: 'array' });

        // 读取第一个Sheet
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(firstSheet);

        // 转换为术语格式
        const terms = jsonData.map(row => ({
          source: row['源术语'] || row['source'],
          translations: {
            EN: row['EN'] || row['English'] || '',
            JP: row['JP'] || row['日本語'] || '',
            TH: row['TH'] || row['ไทย'] || '',
            PT: row['PT'] || row['Português'] || ''
          },
          notes: row['备注'] || row['notes'] || ''
        }));

        resolve(terms);
      } catch (error) {
        reject(new Error('文件解析失败: ' + error.message));
      }
    };

    reader.onerror = () => reject(new Error('文件读取失败'));
    reader.readAsArrayBuffer(file);
  });
}

// 验证术语数据
function validateGlossaryData(data) {
  if (!Array.isArray(data) || data.length === 0) {
    return { valid: false, message: '文件为空或格式不正确' };
  }

  // 检查必填字段
  const invalidRows = data.filter(term => !term.source);
  if (invalidRows.length > 0) {
    return { valid: false, message: `${invalidRows.length} 条术语缺少源术语` };
  }

  // 检查至少有一个翻译
  const noTranslation = data.filter(term =>
    !term.translations || Object.values(term.translations).every(t => !t)
  );
  if (noTranslation.length > 0) {
    return { valid: false, message: `${noTranslation.length} 条术语缺少翻译` };
  }

  return { valid: true };
}
```

#### 3.2 术语搜索和筛选

```javascript
class TermSearcher {
  constructor(glossaryId) {
    this.glossaryId = glossaryId;
    this.allTerms = [];
    this.filteredTerms = [];
    this.searchText = '';
    this.filterLang = 'all';
  }

  async loadTerms() {
    try {
      // 从后端加载术语（如果数据量大，需要分页）
      this.allTerms = await API.getTerms(this.glossaryId);
      this.filteredTerms = [...this.allTerms];
      this.render();
    } catch (error) {
      console.error('Failed to load terms:', error);
    }
  }

  search(text) {
    this.searchText = text.toLowerCase();
    this.applyFilters();
  }

  filterByLanguage(lang) {
    this.filterLang = lang;
    this.applyFilters();
  }

  applyFilters() {
    this.filteredTerms = this.allTerms.filter(term => {
      // 搜索过滤
      if (this.searchText) {
        const sourceMatch = term.source.toLowerCase().includes(this.searchText);
        const translationMatch = Object.values(term.translations).some(t =>
          t.toLowerCase().includes(this.searchText)
        );
        if (!sourceMatch && !translationMatch) {
          return false;
        }
      }

      // 语言过滤
      if (this.filterLang !== 'all') {
        if (!term.translations[this.filterLang]) {
          return false;
        }
      }

      return true;
    });

    this.render();
  }

  render() {
    // 渲染术语表格
    const tbody = document.querySelector('#termTable tbody');
    tbody.innerHTML = '';

    this.filteredTerms.forEach(term => {
      const row = this.createTermRow(term);
      tbody.appendChild(row);
    });

    // 更新统计
    document.getElementById('termCount').textContent =
      `${this.filteredTerms.length} / ${this.allTerms.length} 条`;
  }

  createTermRow(term) {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${term.source}</td>
      <td>${term.translations.EN || '-'}</td>
      <td>${term.translations.JP || '-'}</td>
      <td>${term.translations.TH || '-'}</td>
      <td>
        <button class="btn btn-xs btn-ghost" onclick="termSearcher.editTerm('${term.id}')">
          <i class="bi bi-pencil"></i>
        </button>
        <button class="btn btn-xs btn-ghost text-error" onclick="termSearcher.deleteTerm('${term.id}')">
          <i class="bi bi-trash"></i>
        </button>
      </td>
    `;
    return row;
  }

  async editTerm(termId) {
    const term = this.allTerms.find(t => t.id === termId);
    if (!term) return;

    // 显示编辑Modal
    await showTermEditModal(term);
  }

  async deleteTerm(termId) {
    const confirmed = await UIHelper.confirm('确定要删除这条术语吗？');
    if (!confirmed) return;

    try {
      await API.deleteTerm(this.glossaryId, termId);
      await this.loadTerms();
      UIHelper.showToast('删除成功', 'success');
    } catch (error) {
      UIHelper.showToast(`删除失败: ${error.message}`, 'error');
    }
  }
}
```

---

### 4️⃣ 数据分析（Analytics）

#### 4.1 数据聚合

```javascript
class AnalyticsEngine {
  constructor() {
    this.sessions = [];
    this.timeRange = 'month';
    this.stats = null;
  }

  async loadData(timeRange = 'month') {
    this.timeRange = timeRange;
    this.sessions = await this.fetchSessionsInRange(timeRange);
    this.stats = this.calculateStats();
    return this.stats;
  }

  async fetchSessionsInRange(range) {
    const sessions = SessionManager.getAllSessions();
    const now = new Date();
    let startDate;

    switch (range) {
      case 'day':
        startDate = new Date(now.setHours(0, 0, 0, 0));
        break;
      case 'week':
        startDate = new Date(now.setDate(now.getDate() - 7));
        break;
      case 'month':
        startDate = new Date(now.setMonth(now.getMonth() - 1));
        break;
      case 'year':
        startDate = new Date(now.setFullYear(now.getFullYear() - 1));
        break;
    }

    return sessions.filter(s => new Date(s.createdAt) >= startDate);
  }

  calculateStats() {
    // 1. 翻译量统计
    const totalTasks = this.sessions.reduce((sum, s) =>
      sum + (s.executionResult?.totalTasks || 0), 0
    );

    const completedSessions = this.sessions.filter(s => s.stage === 'completed');
    const completedTasks = completedSessions.reduce((sum, s) =>
      sum + (s.executionResult?.completedTasks || 0), 0
    );

    // 2. 成本统计
    const totalCost = completedSessions.reduce((sum, s) =>
      sum + (s.executionResult?.cost || 0), 0
    );

    // 3. 按语言分组
    const langStats = this.groupByLanguage(completedSessions);

    // 4. 按模型分组
    const modelStats = this.groupByModel(completedSessions);

    // 5. 成功率
    const successRate = totalTasks > 0
      ? (completedTasks / totalTasks) * 100
      : 0;

    // 6. 趋势数据
    const trends = this.calculateTrends();

    return {
      totalTasks,
      completedTasks,
      totalCost,
      successRate,
      langStats,
      modelStats,
      trends
    };
  }

  groupByLanguage(sessions) {
    const stats = {};

    sessions.forEach(session => {
      const targetLangs = session.config?.target_langs || [];
      const taskCount = session.executionResult?.completedTasks || 0;
      const avgCount = Math.floor(taskCount / targetLangs.length);

      targetLangs.forEach(lang => {
        if (!stats[lang]) {
          stats[lang] = 0;
        }
        stats[lang] += avgCount;
      });
    });

    return stats;
  }

  groupByModel(sessions) {
    const stats = {};

    sessions.forEach(session => {
      const model = session.config?.llm_model || 'unknown';
      const cost = session.executionResult?.cost || 0;

      if (!stats[model]) {
        stats[model] = { count: 0, cost: 0 };
      }

      stats[model].count += 1;
      stats[model].cost += cost;
    });

    return stats;
  }

  calculateTrends() {
    // 按日期分组统计
    const dailyStats = {};

    this.sessions.forEach(session => {
      const date = new Date(session.createdAt).toLocaleDateString();

      if (!dailyStats[date]) {
        dailyStats[date] = { tasks: 0, cost: 0 };
      }

      dailyStats[date].tasks += session.executionResult?.completedTasks || 0;
      dailyStats[date].cost += session.executionResult?.cost || 0;
    });

    // 转换为数组并排序
    return Object.entries(dailyStats)
      .map(([date, stats]) => ({ date, ...stats }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));
  }
}
```

#### 4.2 图表渲染（Chart.js）

```javascript
class ChartRenderer {
  constructor() {
    this.charts = {};
  }

  renderTrendChart(data) {
    const ctx = document.getElementById('trendChart').getContext('2d');

    // 销毁旧图表
    if (this.charts.trend) {
      this.charts.trend.destroy();
    }

    this.charts.trend = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.map(d => d.date),
        datasets: [{
          label: '翻译量',
          data: data.map(d => d.tasks),
          borderColor: '#4F46E5',
          backgroundColor: 'rgba(79, 70, 229, 0.1)',
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            mode: 'index',
            intersect: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 500 }
          }
        }
      }
    });
  }

  renderLanguageChart(data) {
    const ctx = document.getElementById('languageChart').getContext('2d');

    if (this.charts.language) {
      this.charts.language.destroy();
    }

    const languages = Object.keys(data);
    const counts = Object.values(data);
    const total = counts.reduce((a, b) => a + b, 0);

    this.charts.language = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: languages,
        datasets: [{
          data: counts,
          backgroundColor: [
            '#4F46E5',  // 靛蓝
            '#10B981',  // 绿色
            '#F59E0B',  // 琥珀
            '#EF4444',  // 红色
            '#8B5CF6'   // 紫色
          ]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label || '';
                const value = context.parsed;
                const percent = ((value / total) * 100).toFixed(1);
                return `${label}: ${value} (${percent}%)`;
              }
            }
          }
        }
      }
    });
  }

  destroy() {
    Object.values(this.charts).forEach(chart => chart.destroy());
    this.charts = {};
  }
}
```

---

## 🔌 API对接说明

### API封装层

```javascript
class API {
  constructor() {
    this.baseURL = APP_CONFIG.API_BASE_URL || 'http://localhost:8013';
    this.token = null;
  }

  setToken(token) {
    this.token = token;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      // 处理HTTP错误
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ========== 会话管理 ==========

  async uploadFile(file, gameInfo = null) {
    const formData = new FormData();
    formData.append('file', file);
    if (gameInfo) {
      formData.append('game_info', JSON.stringify(gameInfo));
    }

    return this.request('/api/tasks/split', {
      method: 'POST',
      headers: {},  // FormData自动设置Content-Type
      body: formData
    });
  }

  async getTaskStatus(sessionId) {
    return this.request(`/api/tasks/status/${sessionId}`);
  }

  async startExecution(sessionId, options) {
    return this.request('/api/execute/start', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        ...options
      })
    });
  }

  async getExecutionProgress(sessionId) {
    return this.request(`/api/execute/status/${sessionId}`);
  }

  async downloadSession(sessionId) {
    const url = `${this.baseURL}/api/download/${sessionId}`;
    window.location.href = url;
  }

  // ========== 术语库管理 ==========

  async createGlossary(data) {
    return this.request('/api/glossaries', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getGlossaries() {
    return this.request('/api/glossaries/list');
  }

  async getGlossary(id) {
    return this.request(`/api/glossaries/${id}`);
  }

  async updateGlossary(id, data) {
    return this.request(`/api/glossaries/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async deleteGlossary(id) {
    return this.request(`/api/glossaries/${id}`, {
      method: 'DELETE'
    });
  }

  async importTerms(glossaryId, terms) {
    return this.request(`/api/glossaries/${glossaryId}/import`, {
      method: 'POST',
      body: JSON.stringify({ terms })
    });
  }

  async getTerms(glossaryId, page = 1, pageSize = 100) {
    return this.request(`/api/glossaries/${glossaryId}/terms?page=${page}&pageSize=${pageSize}`);
  }

  // ========== 数据分析 ==========

  async getAnalytics(timeRange = 'month') {
    // 如果后端有聚合API，直接调用
    // 否则前端自己计算
    return this.request(`/api/analytics?range=${timeRange}`);
  }
}

const api = new API();
```

---

## 💾 状态管理方案

### LocalStorage数据结构

```javascript
// localStorage的key命名规范
const STORAGE_KEYS = {
  SESSIONS: 'translation_hub_sessions',         // 会话列表
  CURRENT_SESSION: 'translation_hub_current',   // 当前会话
  USER_PREFS: 'translation_hub_preferences',    // 用户偏好
  GLOSSARIES: 'translation_hub_glossaries'      // 术语库列表（缓存）
};

// 会话数据示例
const sessionData = {
  sessionId: 'uuid-123',
  filename: 'game.xlsx',
  stage: 'executing',  // created|configured|executing|completed|failed
  createdAt: 1697520000000,
  updatedAt: 1697520100000,
  completedAt: null,

  // 分析结果
  analysis: {
    statistics: {
      sheet_count: 5,
      total_cells: 1200,
      estimated_tasks: 800
    }
  },

  // 配置信息
  config: {
    source_lang: 'CH',
    target_langs: ['EN', 'JP'],
    llm_model: 'qwen-plus',
    glossary_id: 'glossary-456'
  },

  // 执行进度
  progress: {
    total: 800,
    completed: 480,
    processing: 20,
    pending: 280,
    failed: 20
  },

  // 执行结果
  executionResult: {
    totalTasks: 800,
    completedTasks: 780,
    failedTasks: 20,
    cost: 2.50,
    duration: 1800000  // 毫秒
  }
};
```

### SessionManager实现

```javascript
class SessionManager {
  // ========== 静态方法（操作LocalStorage） ==========

  static getAllSessions() {
    const data = localStorage.getItem(STORAGE_KEYS.SESSIONS);
    return data ? JSON.parse(data) : [];
  }

  static getSession(sessionId) {
    const sessions = this.getAllSessions();
    return sessions.find(s => s.sessionId === sessionId);
  }

  static saveSession(session) {
    const sessions = this.getAllSessions();
    const index = sessions.findIndex(s => s.sessionId === session.sessionId);

    if (index >= 0) {
      sessions[index] = session;
    } else {
      sessions.push(session);
    }

    localStorage.setItem(STORAGE_KEYS.SESSIONS, JSON.stringify(sessions));
  }

  static deleteSession(sessionId) {
    const sessions = this.getAllSessions();
    const filtered = sessions.filter(s => s.sessionId !== sessionId);
    localStorage.setItem(STORAGE_KEYS.SESSIONS, JSON.stringify(filtered));
  }

  static updateSessionProgress(sessionId, progress) {
    const session = this.getSession(sessionId);
    if (session) {
      session.progress = progress;
      session.updatedAt = Date.now();
      this.saveSession(session);
    }
  }

  static updateSessionStage(sessionId, stage) {
    const session = this.getSession(sessionId);
    if (session) {
      session.stage = stage;
      session.updatedAt = Date.now();
      if (stage === 'completed') {
        session.completedAt = Date.now();
      }
      this.saveSession(session);
    }
  }

  // ========== 实例方法（管理当前会话） ==========

  constructor() {
    this.session = null;
    this.loadCurrentSession();
  }

  loadCurrentSession() {
    const data = localStorage.getItem(STORAGE_KEYS.CURRENT_SESSION);
    if (data) {
      this.session = JSON.parse(data);
    }
  }

  saveCurrentSession() {
    if (this.session) {
      localStorage.setItem(STORAGE_KEYS.CURRENT_SESSION, JSON.stringify(this.session));
    }
  }

  createSession(sessionId, filename, analysis) {
    this.session = {
      sessionId,
      filename,
      stage: 'created',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      analysis
    };

    this.saveCurrentSession();
    SessionManager.saveSession(this.session);
  }

  updateConfig(config) {
    if (this.session) {
      this.session.config = config;
      this.session.stage = 'configured';
      this.session.updatedAt = Date.now();
      this.saveCurrentSession();
      SessionManager.saveSession(this.session);
    }
  }

  clearSession() {
    this.session = null;
    localStorage.removeItem(STORAGE_KEYS.CURRENT_SESSION);
  }
}

const sessionManager = new SessionManager();
```

---

## 🚨 错误处理策略

### 错误分类

```javascript
const ErrorTypes = {
  NETWORK_ERROR: 'network_error',      // 网络连接失败
  API_ERROR: 'api_error',              // API调用失败
  VALIDATION_ERROR: 'validation_error', // 数据验证失败
  AUTH_ERROR: 'auth_error',            // 认证失败
  BUSINESS_ERROR: 'business_error',    // 业务逻辑错误
  UNKNOWN_ERROR: 'unknown_error'       // 未知错误
};
```

### 全局错误处理器

```javascript
class ErrorHandler {
  static handle(error, context = '') {
    console.error(`[${context}]`, error);

    const errorType = this.classifyError(error);
    const message = this.getErrorMessage(error, errorType);
    const actions = this.getErrorActions(errorType);

    UIHelper.showErrorDialog({
      type: errorType,
      message,
      actions
    });
  }

  static classifyError(error) {
    if (!navigator.onLine) {
      return ErrorTypes.NETWORK_ERROR;
    }

    if (error.message.includes('401') || error.message.includes('Unauthorized')) {
      return ErrorTypes.AUTH_ERROR;
    }

    if (error.message.includes('404')) {
      return ErrorTypes.API_ERROR;
    }

    if (error.name === 'ValidationError') {
      return ErrorTypes.VALIDATION_ERROR;
    }

    return ErrorTypes.UNKNOWN_ERROR;
  }

  static getErrorMessage(error, type) {
    const messages = {
      [ErrorTypes.NETWORK_ERROR]: '网络连接失败，请检查网络后重试',
      [ErrorTypes.API_ERROR]: `服务器错误: ${error.message}`,
      [ErrorTypes.VALIDATION_ERROR]: `数据验证失败: ${error.message}`,
      [ErrorTypes.AUTH_ERROR]: '认证失败，请重新登录',
      [ErrorTypes.BUSINESS_ERROR]: error.message,
      [ErrorTypes.UNKNOWN_ERROR]: `未知错误: ${error.message}`
    };

    return messages[type] || messages[ErrorTypes.UNKNOWN_ERROR];
  }

  static getErrorActions(type) {
    switch (type) {
      case ErrorTypes.NETWORK_ERROR:
        return [
          { label: '重试', action: () => window.location.reload() },
          { label: '取消', className: 'btn-ghost' }
        ];

      case ErrorTypes.AUTH_ERROR:
        return [
          { label: '重新登录', action: () => router.navigate('/login') },
          { label: '取消', className: 'btn-ghost' }
        ];

      default:
        return [
          { label: '确定', className: 'btn-primary' }
        ];
    }
  }
}

// 全局错误监听
window.addEventListener('unhandledrejection', (event) => {
  ErrorHandler.handle(event.reason, 'UnhandledRejection');
});
```

---

## ⚡ 性能优化方案

### 1. 懒加载

```javascript
// 图片懒加载
function setupLazyLoading() {
  const images = document.querySelectorAll('img[data-src]');

  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        imageObserver.unobserve(img);
      }
    });
  });

  images.forEach(img => imageObserver.observe(img));
}

// 组件懒加载
async function loadComponentWhenNeeded(componentName) {
  if (!window.loadedComponents) {
    window.loadedComponents = {};
  }

  if (!window.loadedComponents[componentName]) {
    const module = await import(`./components/${componentName}.js`);
    window.loadedComponents[componentName] = module.default;
  }

  return window.loadedComponents[componentName];
}
```

### 2. 防抖和节流

```javascript
// 防抖（适用于搜索框）
function debounce(func, delay = 300) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

// 节流（适用于滚动、窗口调整）
function throttle(func, limit = 100) {
  let inThrottle;
  return function (...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

// 使用示例
const searchInput = document.getElementById('searchInput');
searchInput.addEventListener('input', debounce((e) => {
  performSearch(e.target.value);
}, 500));

window.addEventListener('scroll', throttle(() => {
  updateScrollPosition();
}, 200));
```

### 3. 虚拟滚动（大列表优化）

```javascript
class VirtualScroller {
  constructor(container, items, rowHeight, renderRow) {
    this.container = container;
    this.items = items;
    this.rowHeight = rowHeight;
    this.renderRow = renderRow;

    this.visibleCount = Math.ceil(container.clientHeight / rowHeight) + 2;
    this.totalHeight = items.length * rowHeight;
    this.scrollTop = 0;

    this.setupScroller();
    this.render();
  }

  setupScroller() {
    this.container.style.overflowY = 'auto';
    this.container.style.position = 'relative';

    const spacer = document.createElement('div');
    spacer.style.height = `${this.totalHeight}px`;
    this.container.appendChild(spacer);

    this.viewport = document.createElement('div');
    this.viewport.style.position = 'absolute';
    this.viewport.style.top = '0';
    this.viewport.style.left = '0';
    this.viewport.style.right = '0';
    this.container.appendChild(this.viewport);

    this.container.addEventListener('scroll', () => {
      this.scrollTop = this.container.scrollTop;
      this.render();
    });
  }

  render() {
    const startIndex = Math.floor(this.scrollTop / this.rowHeight);
    const endIndex = Math.min(startIndex + this.visibleCount, this.items.length);

    this.viewport.style.transform = `translateY(${startIndex * this.rowHeight}px)`;
    this.viewport.innerHTML = '';

    for (let i = startIndex; i < endIndex; i++) {
      const row = this.renderRow(this.items[i], i);
      this.viewport.appendChild(row);
    }
  }
}

// 使用示例
const virtualScroller = new VirtualScroller(
  document.getElementById('sessionList'),
  sessions,  // 大量数据
  60,        // 行高
  (session) => {
    const row = document.createElement('div');
    row.className = 'session-row';
    row.innerHTML = `<div>${session.filename}</div>`;
    return row;
  }
);
```

### 4. 请求合并和缓存

```javascript
class RequestCache {
  constructor(ttl = 60000) {  // 默认缓存1分钟
    this.cache = new Map();
    this.ttl = ttl;
  }

  async get(key, fetcher) {
    const cached = this.cache.get(key);

    if (cached && Date.now() - cached.timestamp < this.ttl) {
      console.log(`Cache hit: ${key}`);
      return cached.data;
    }

    console.log(`Cache miss: ${key}`);
    const data = await fetcher();
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });

    return data;
  }

  clear(key) {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }
}

const requestCache = new RequestCache();

// 使用示例
async function getGlossaries() {
  return requestCache.get('glossaries', () => API.getGlossaries());
}
```

---

## 📝 开发检查清单

### 功能完整性

- [ ] 智能工作台
  - [ ] 核心指标卡片
  - [ ] 最近项目列表
  - [ ] 快速操作
- [ ] 会话管理
  - [ ] 筛选和搜索
  - [ ] 批量操作
  - [ ] 会话详情
- [ ] 术语库管理
  - [ ] CRUD操作
  - [ ] 导入/导出
  - [ ] 搜索和筛选
- [ ] 数据分析
  - [ ] 统计指标
  - [ ] 图表可视化
  - [ ] 趋势分析
- [ ] 翻译流程
  - [ ] 文件上传
  - [ ] 任务配置
  - [ ] 翻译执行
  - [ ] 结果下载

### 代码质量

- [ ] 命名规范（camelCase / PascalCase）
- [ ] 注释完整（关键逻辑有注释）
- [ ] 错误处理（try-catch / 用户友好提示）
- [ ] 性能优化（防抖/节流/懒加载）
- [ ] 浏览器兼容性（Chrome / Firefox / Safari）

### 用户体验

- [ ] 加载状态（骨架屏 / Loading）
- [ ] 空状态（友好提示 + 引导操作）
- [ ] 错误提示（明确 + 可操作）
- [ ] 响应式设计（移动端适配）
- [ ] 快捷键支持

---

**文档状态**: ✅ 已完成
**下一步**: 开始编码实现

