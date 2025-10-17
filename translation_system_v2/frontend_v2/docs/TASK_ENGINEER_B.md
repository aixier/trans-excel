# 工程师B - 智能工作台 + 会话管理开发任务

> **角色**: 核心功能开发工程师
> **工期**: Week 2-4
> **工作量**: 13天（104小时）
> **依赖**: 等待工程师A完成组件库（Week 2）

---

## 🎯 任务目标

### 核心目标

1. **Week 2-3**: 开发智能工作台（系统首页Dashboard）
2. **Week 3-4**: 升级会话管理功能（筛选、批量操作、详情）
3. **Week 4**: 功能完善、Bug修复、集成测试

### 成功标准

- ✅ 智能工作台展示核心指标，数据实时更新
- ✅ 最近项目列表可以查看和快速操作
- ✅ 会话管理支持多维度筛选和批量操作
- ✅ 会话详情侧边栏展示完整信息
- ✅ 所有功能符合设计规范和需求文档

---

## 📋 详细任务清单

### Week 1: 准备阶段

#### 1.1 环境搭建和学习 (1天)

**任务**:
- [ ] 克隆代码仓库，搭建开发环境
- [ ] 阅读必读文档（见下方参考文档清单）
- [ ] 理解系统架构和数据流
- [ ] 等待工程师A完成基础架构（Week 1结束）

**参考文档**:
- `docs/README.md` - 文档导航
- `docs/requirements/REQUIREMENTS.md` - 核心功能模块
- `docs/design/UI_DESIGN.md` - 页面原型
- `docs/technical/FEATURE_SPEC.md` - 技术实现规范

---

### Week 2: 智能工作台开发（Part 1）

#### 2.1 核心指标卡片 (2天)

**目标**: 实现4个统计卡片，展示关键数据

**任务**:
- [ ] 创建dashboard.js页面逻辑
  ```javascript
  // 文件: js/pages/dashboard.js
  class DashboardPage {
    constructor() {
      this.stats = null;
      this.recentSessions = [];
    }

    async init() {
      await this.loadDashboardStats();
      await this.loadRecentSessions();
      this.render();
      this.setupAutoRefresh();
    }

    async loadDashboardStats() { /* ... */ }
    renderStatCards() { /* ... */ }
    setupAutoRefresh() { /* 每30秒刷新一次 */ }
  }
  ```

- [ ] 实现统计数据加载逻辑
  ```javascript
  async loadDashboardStats() {
    const sessions = SessionManager.getAllSessions();

    // 今日待办
    const todayPending = sessions.filter(s => /* 今日创建且未完成 */).length;

    // 执行中任务
    const running = sessions.filter(s => s.stage === 'executing');

    // 本月完成
    const monthStart = new Date();
    monthStart.setDate(1);
    const completedThisMonth = sessions.filter(s =>
      s.stage === 'completed' && new Date(s.completedAt) >= monthStart
    );

    // 本月成本
    const monthlyCost = completedThisMonth.reduce((sum, s) =>
      sum + (s.executionResult?.cost || 0), 0
    );

    return { todayPending, running, completedThisMonth, monthlyCost };
  }
  ```

- [ ] 使用StatCard组件渲染
  ```javascript
  renderStatCards() {
    const container = document.getElementById('statCards');

    // 今日待办卡片
    const todoCard = new StatCard({
      title: '今日待办',
      value: this.stats.todayPending,
      icon: 'bi-clipboard-check',
      trend: { value: 2, direction: 'up' }
    });

    // 执行中任务卡片
    const runningCard = new StatCard({
      title: '执行中任务',
      value: this.stats.running.length,
      icon: 'bi-lightning-fill',
      progress: this.stats.running[0]?.progress || 0
    });

    // 本月完成卡片
    const completedCard = new StatCard({
      title: '本月完成',
      value: this.stats.completedThisMonth.length,
      icon: 'bi-check-circle-fill',
      trend: { value: 15, direction: 'up', unit: '%' }
    });

    // 本月成本卡片
    const costCard = new StatCard({
      title: '本月成本',
      value: `$${this.stats.monthlyCost.toFixed(2)}`,
      icon: 'bi-cash-stack',
      progress: (this.stats.monthlyCost / 50.0) * 100 // 假设预算$50
    });

    container.innerHTML = `
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        ${todoCard.render()}
        ${runningCard.render()}
        ${completedCard.render()}
        ${costCard.render()}
      </div>
    `;
  }
  ```

- [ ] 实现自动刷新（轮询执行中任务）
  ```javascript
  setupAutoRefresh() {
    setInterval(async () => {
      // 只刷新执行中任务的进度
      const runningSessions = this.stats.running;
      for (const session of runningSessions) {
        try {
          const progress = await api.getExecutionProgress(session.sessionId);
          SessionManager.updateSessionProgress(session.sessionId, progress);
          this.updateRunningCard(progress);
        } catch (error) {
          console.error('Failed to refresh progress:', error);
        }
      }
    }, 30000); // 30秒刷新一次
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 智能工作台 - 核心指标卡片（108-127行）
- `docs/technical/FEATURE_SPEC.md` - 智能工作台 - loadDashboardStats（40-96行）
- `docs/design/UI_DESIGN.md` - Dashboard页面原型（207-258行）

**交付标准**:
- 4个指标卡片正确显示数据
- 执行中任务的进度实时更新
- 卡片样式符合设计规范

---

#### 2.2 最近项目列表 (2天)

**目标**: 展示最近10个会话，支持快速操作

**任务**:
- [ ] 实现数据加载逻辑
  ```javascript
  async loadRecentSessions(limit = 10) {
    const sessions = SessionManager.getAllSessions();

    // 按更新时间排序
    sessions.sort((a, b) => b.updatedAt - a.updatedAt);

    // 取前N条
    this.recentSessions = sessions.slice(0, limit);

    // 对于执行中的会话，启动轮询更新进度
    const runningSessions = this.recentSessions.filter(s => s.stage === 'executing');
    if (runningSessions.length > 0) {
      this.startProgressPolling(runningSessions);
    }
  }
  ```

- [ ] 使用DataTable组件渲染
  ```javascript
  renderRecentSessions() {
    const table = new DataTable({
      columns: [
        {
          key: 'filename',
          label: '文件名',
          render: (val, row) => `
            <div class="flex items-center gap-2">
              <i class="bi bi-file-earmark-excel text-success"></i>
              <span class="font-medium">${val}</span>
            </div>
          `
        },
        {
          key: 'stage',
          label: '状态',
          render: (val) => this.renderStatusBadge(val)
        },
        {
          key: 'progress',
          label: '进度',
          render: (val, row) => this.renderProgress(row)
        },
        {
          key: 'updatedAt',
          label: '更新时间',
          render: (val) => formatTimeAgo(val)
        },
        {
          key: 'actions',
          label: '操作',
          render: (val, row) => this.renderActions(row)
        }
      ],
      data: this.recentSessions,
      selectable: false,
      pagination: false
    });

    document.getElementById('recentSessions').innerHTML = table.render();
  }
  ```

- [ ] 实现状态Badge渲染
  ```javascript
  renderStatusBadge(stage) {
    const statusMap = {
      'created': { icon: 'bi-circle', label: '待配置', class: 'badge-info' },
      'split_complete': { icon: 'bi-gear', label: '已配置', class: 'badge-info' },
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
  ```

- [ ] 实现进度条渲染
  ```javascript
  renderProgress(session) {
    if (session.stage === 'executing' && session.progress) {
      const percent = Math.round((session.progress.completed / session.progress.total) * 100);
      return `
        <div class="flex items-center gap-2">
          <progress class="progress progress-warning w-20" value="${percent}" max="100"></progress>
          <span class="text-sm">${percent}%</span>
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

- [ ] 实现快速操作按钮
  ```javascript
  renderActions(session) {
    if (session.stage === 'executing') {
      return `<button class="btn btn-sm btn-ghost" onclick="router.navigate('/execute/${session.sessionId}')">
        <i class="bi bi-eye"></i> 查看
      </button>`;
    } else if (session.stage === 'completed') {
      return `<button class="btn btn-sm btn-success" onclick="dashboardPage.downloadResult('${session.sessionId}')">
        <i class="bi bi-download"></i> 下载
      </button>`;
    } else {
      return `<button class="btn btn-sm btn-primary" onclick="router.navigate('/config/${session.sessionId}')">
        <i class="bi bi-play-fill"></i> 继续
      </button>`;
    }
  }
  ```

- [ ] 实现进度轮询
  ```javascript
  startProgressPolling(sessions) {
    this.pollInterval = setInterval(async () => {
      for (const session of sessions) {
        try {
          const progress = await api.getExecutionProgress(session.sessionId);
          SessionManager.updateSessionProgress(session.sessionId, progress);
          this.updateProgressInTable(session.sessionId, progress);

          if (progress.completed >= progress.total) {
            clearInterval(this.pollInterval);
            await this.loadRecentSessions(); // 重新加载列表
          }
        } catch (error) {
          console.error(`Failed to poll progress:`, error);
        }
      }
    }, 5000); // 5秒轮询一次
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 智能工作台 - 最近项目列表（129-150行）
- `docs/technical/FEATURE_SPEC.md` - 智能工作台 - loadRecentSessions（131-264行）

**交付标准**:
- 最近10个会话正确显示
- 执行中任务的进度实时更新
- 快速操作按钮功能正常

---

### Week 3: 智能工作台开发（Part 2）+ 会话管理（Part 1）

#### 3.1 快速操作区 (1天)

**目标**: 提供常用操作的快捷入口

**任务**:
- [ ] 实现快速操作区
  ```javascript
  renderQuickActions() {
    return `
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <h2 class="card-title">快速操作</h2>
          <div class="flex flex-wrap gap-2">
            <button class="btn btn-primary gap-2" onclick="router.navigate('/create')">
              <i class="bi bi-plus-circle"></i>
              新建翻译
            </button>
            <button class="btn btn-ghost gap-2" onclick="router.navigate('/glossary')">
              <i class="bi bi-book"></i>
              术语库
            </button>
            <button class="btn btn-ghost gap-2" onclick="router.navigate('/analytics')">
              <i class="bi bi-bar-chart"></i>
              数据分析
            </button>
            <button class="btn btn-ghost gap-2" onclick="router.navigate('/settings')">
              <i class="bi bi-gear"></i>
              系统设置
            </button>
          </div>
        </div>
      </div>
    `;
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 智能工作台 - 快速操作区（152-161行）

---

#### 3.2 数据统计图表（可选）(1天)

**目标**: 展示7日翻译量趋势和语言分布

**任务**:
- [ ] 实现趋势图
  ```javascript
  async renderTrendChart() {
    const sessions = SessionManager.getAllSessions();
    const last7Days = this.getLast7DaysData(sessions);

    ChartHelper.createLineChart('trendChart', {
      labels: last7Days.map(d => d.date),
      datasets: [{
        label: '翻译量',
        data: last7Days.map(d => d.count),
        borderColor: '#4F46E5',
        backgroundColor: 'rgba(79, 70, 229, 0.1)'
      }]
    });
  }
  ```

- [ ] 实现语言分布饼图
  ```javascript
  async renderLanguageChart() {
    const sessions = SessionManager.getAllSessions();
    const langStats = this.calculateLanguageDistribution(sessions);

    ChartHelper.createPieChart('languageChart', {
      labels: Object.keys(langStats),
      datasets: [{
        data: Object.values(langStats),
        backgroundColor: ['#4F46E5', '#10B981', '#F59E0B']
      }]
    });
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 智能工作台 - 数据统计图表（162-169行）

**注意**: 此功能为可选，如果时间紧张可以跳过

---

#### 3.3 会话管理 - 筛选和搜索 (2天)

**目标**: 实现多维度筛选功能

**任务**:
- [ ] 创建sessions.js页面逻辑（升级现有代码）
  ```javascript
  // 文件: js/pages/sessions.js
  class SessionsPage {
    constructor() {
      this.allSessions = [];
      this.filteredSessions = [];
      this.filterState = {
        searchText: '',
        timeRange: 'all',
        status: 'all',
        project: 'all'
      };
    }

    async init() {
      await this.loadSessions();
      this.renderFilterBar();
      this.renderSessionTable();
    }

    async loadSessions() { /* ... */ }
    applyFilters() { /* ... */ }
    renderFilterBar() { /* ... */ }
    renderSessionTable() { /* ... */ }
  }
  ```

- [ ] 使用FilterBar组件
  ```javascript
  renderFilterBar() {
    const filterBar = new FilterBar({
      filters: [
        {
          type: 'search',
          placeholder: '搜索文件名...',
          value: this.filterState.searchText
        },
        {
          type: 'select',
          label: '时间范围',
          options: ['全部时间', '今天', '本周', '本月', '自定义'],
          value: this.filterState.timeRange
        },
        {
          type: 'select',
          label: '状态',
          options: ['全部状态', '待配置', '执行中', '已完成', '失败'],
          value: this.filterState.status
        }
      ],
      onSearch: (values) => {
        this.filterState = values;
        this.applyFilters();
      },
      onReset: () => {
        this.filterState = { searchText: '', timeRange: 'all', status: 'all' };
        this.applyFilters();
      }
    });

    document.getElementById('filterBar').innerHTML = filterBar.render();
  }
  ```

- [ ] 实现筛选逻辑
  ```javascript
  applyFilters() {
    let filtered = [...this.allSessions];

    // 搜索过滤
    if (this.filterState.searchText) {
      const searchLower = this.filterState.searchText.toLowerCase();
      filtered = filtered.filter(s =>
        s.filename.toLowerCase().includes(searchLower) ||
        s.sessionId.toLowerCase().includes(searchLower)
      );
    }

    // 时间范围过滤
    if (this.filterState.timeRange !== 'all') {
      filtered = this.filterByTimeRange(filtered, this.filterState.timeRange);
    }

    // 状态过滤
    if (this.filterState.status !== 'all') {
      filtered = filtered.filter(s => s.stage === this.filterState.status);
    }

    this.filteredSessions = filtered;
    this.renderSessionTable();
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 会话管理 - 筛选和搜索（175-195行）
- `docs/technical/FEATURE_SPEC.md` - 会话管理 - applyFilters（285-339行）

**交付标准**:
- 可以按文件名搜索
- 可以按时间范围筛选
- 可以按状态筛选
- 筛选结果实时更新

---

### Week 4: 会话管理（Part 2）+ 完善测试

#### 4.1 批量操作 (2天)

**目标**: 实现批量下载和批量删除

**任务**:
- [ ] 实现选择状态管理
  ```javascript
  class SelectionManager {
    constructor() {
      this.selectedIds = new Set();
    }

    toggleSelect(sessionId) { /* ... */ }
    selectAll(sessionIds) { /* ... */ }
    clearAll() { /* ... */ }
    getSelected() { return Array.from(this.selectedIds); }

    updateUI() {
      // 更新全选checkbox
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

- [ ] 实现批量下载
  ```javascript
  async batchDownload(sessionIds) {
    try {
      UIHelper.showLoading(true, `正在打包 ${sessionIds.length} 个文件...`);

      // 逐个下载并打包为ZIP
      const files = [];
      for (const sessionId of sessionIds) {
        const session = SessionManager.getSession(sessionId);
        const blob = await api.downloadSession(sessionId);
        files.push({
          name: session.filename,
          blob: blob
        });
      }

      // 使用ExportHelper打包ZIP
      const zipBlob = await ExportHelper.createZip(files);
      ExportHelper.download(zipBlob, `translations_${Date.now()}.zip`);

      UIHelper.showToast('批量下载成功', 'success');
    } catch (error) {
      UIHelper.showToast(`批量下载失败: ${error.message}`, 'error');
    } finally {
      UIHelper.showLoading(false);
    }
  }
  ```

- [ ] 实现批量删除
  ```javascript
  async batchDelete(sessionIds) {
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

              const results = await Promise.allSettled(
                sessionIds.map(id => api.deleteSession(id))
              );

              const successCount = results.filter(r => r.status === 'fulfilled').length;
              const failCount = results.filter(r => r.status === 'rejected').length;

              sessionIds.forEach(id => SessionManager.deleteSession(id));
              await this.loadSessions();
              this.selectionManager.clearAll();

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

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 会话管理 - 批量操作（226-242行）
- `docs/technical/FEATURE_SPEC.md` - 会话管理 - batchDownload、batchDelete（394-471行）

**交付标准**:
- 可以选择多个会话
- 批量下载打包为ZIP
- 批量删除有二次确认

---

#### 4.2 会话详情侧边栏 (2天)

**目标**: 实现抽屉式会话详情展示

**任务**:
- [ ] 实现SessionDetailDrawer组件
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
              ${Skeleton.card()}
            </div>
          </div>
        </div>
      `;

      document.body.appendChild(this.drawer);
      await this.loadDetails(sessionId);
    }

    async loadDetails(sessionId) { /* ... */ }
    renderContent(details) { /* ... */ }
    close() { /* ... */ }
  }
  ```

- [ ] 实现详情内容渲染
  ```javascript
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
            <code class="text-xs">${details.sessionId.substring(0, 16)}...</code>
          </div>
          <!-- 更多字段 -->
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
          <button class="btn btn-success flex-1" onclick="api.downloadSession('${details.sessionId}')">
            <i class="bi bi-download"></i>
            下载结果
          </button>
        ` : ''}
      </div>
    `;
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 会话管理 - 会话详情页（197-225行）
- `docs/technical/FEATURE_SPEC.md` - 会话管理 - SessionDetailDrawer（473-605行）
- `docs/design/UI_DESIGN.md` - 会话详情侧边栏（401-446行）

**交付标准**:
- 点击会话可以打开详情侧边栏
- 展示完整的会话信息
- 可以在侧边栏中执行操作

---

#### 4.3 功能完善与测试 (2天)

**任务**:
- [ ] Bug修复
  - 修复已知的Bug
  - 优化性能问题
- [ ] 响应式适配
  - 测试移动端显示
  - 优化平板端布局
- [ ] 集成测试
  - 测试完整的用户流程
  - 测试边界条件
- [ ] 文档完善
  - 更新使用文档
  - 补充注释

**交付标准**:
- 所有功能正常工作
- 无明显Bug
- 响应式布局正常

---

## 📚 参考文档清单

### 必读文档（按优先级）

1. **`docs/requirements/REQUIREMENTS.md`** ⭐⭐⭐
   - 核心功能模块 - 智能工作台（104-169行）
   - 核心功能模块 - 会话管理（171-242行）

2. **`docs/technical/FEATURE_SPEC.md`** ⭐⭐⭐
   - 功能模块详述 - 智能工作台（36-265行）
   - 功能模块详述 - 会话管理（267-605行）

3. **`docs/design/UI_DESIGN.md`** ⭐⭐⭐
   - 页面原型 - Dashboard（207-314行）
   - 页面原型 - Sessions（317-447行）

4. **`docs/API.md`** ⭐⭐
   - 会话管理API（406-500行）
   - 任务执行API（175-319行）

### 选读文档

5. **`TASK_ENGINEER_A.md`**
   - 了解工程师A提供的组件和工具

6. **工程师A提供的组件文档**
   - StatCard使用说明
   - FilterBar使用说明
   - DataTable使用说明

---

## 🎯 交付标准

### Week 2 交付

- [ ] ✅ Dashboard页面完成（指标卡片 + 最近项目列表）
- [ ] ✅ 实时数据更新功能正常
- [ ] ✅ 快速操作区完成

**验收方式**:
- 打开Dashboard页面，数据正确显示
- 执行中任务的进度自动更新
- 快速操作按钮可以跳转

---

### Week 3 交付

- [ ] ✅ 会话管理筛选功能完成
- [ ] ✅ 批量操作功能完成（至少批量下载）

**验收方式**:
- 可以按多个维度筛选会话
- 可以批量下载多个会话

---

### Week 4 交付

- [ ] ✅ 会话详情侧边栏完成
- [ ] ✅ 批量删除功能完成
- [ ] ✅ 所有功能测试通过

**验收方式**:
- 完整的用户流程测试通过
- 无明显Bug
- 符合设计规范

---

## 🤝 协作接口

### 依赖工程师A的接口

#### 1. 使用StatCard组件
```javascript
import StatCard from '../components/StatCard.js';
const card = new StatCard({ title: '今日待办', value: 3 });
```

#### 2. 使用FilterBar组件
```javascript
import FilterBar from '../components/FilterBar.js';
const filterBar = new FilterBar({ filters: [...], onSearch: (...) => {} });
```

#### 3. 使用DataTable组件
```javascript
import DataTable from '../components/DataTable.js';
const table = new DataTable({ columns: [...], data: [...] });
```

#### 4. 使用工具函数
```javascript
import { formatTimeAgo } from '../utils/date-helper.js';
const relativeTime = formatTimeAgo(timestamp);
```

### 提供给其他工程师的接口

**无** - 工程师B主要是业务功能开发，不需要提供接口给其他工程师

---

## 🚨 注意事项

### 开发优先级

1. **Week 2优先**：Dashboard是系统首页，优先级最高
2. **核心功能优先**：筛选、批量操作比详情侧边栏更重要
3. **可选功能延后**：图表功能如果时间紧张可以跳过

### 质量标准

- **数据准确性**：统计数据必须准确无误
- **实时性**：执行中任务的进度必须实时更新
- **用户体验**：加载状态、空状态、错误提示都要完善

### 沟通要点

- **及时反馈**：遇到组件问题及时反馈给工程师A
- **数据格式确认**：确认SessionManager的数据结构
- **集成测试**：Week 4与其他工程师一起做集成测试

---

## ✅ 自检清单

### Week 2结束前
- [ ] Dashboard页面可以正常打开
- [ ] 4个指标卡片数据正确
- [ ] 最近项目列表显示正常
- [ ] 执行中任务进度自动更新

### Week 3结束前
- [ ] 会话管理筛选功能正常
- [ ] 批量下载功能正常
- [ ] 批量操作工具栏显示正常

### Week 4结束前
- [ ] 会话详情侧边栏功能完整
- [ ] 批量删除功能正常
- [ ] 所有功能经过测试
- [ ] 响应式布局正常

---

**开始时间**: Week 2 Day 1（等待工程师A完成组件库）
**预计完成**: Week 4 Day 5
**总工作量**: 13天（104小时）

**祝开发顺利！有问题随时沟通。** 🚀
