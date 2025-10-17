/**
 * Sessions Page - 会话管理
 *
 * 负责管理所有翻译会话，支持多维度筛选和批量操作
 *
 * 依赖:
 * - FilterBar 组件 (工程师A)
 * - DataTable 组件 (工程师A)
 * - SelectionManager (本地实现)
 * - SessionManager (工程师A)
 * - API (工程师A)
 *
 * @author 工程师B
 * @date 2025-10-17
 */

class SessionsPage {
  constructor() {
    this.allSessions = [];
    this.filteredSessions = [];
    this.filterState = {
      searchText: '',
      timeRange: 'all',
      customStart: null,
      customEnd: null,
      status: 'all',
      project: 'all'
    };
    this.selectionManager = new SelectionManager();
    this.detailDrawer = new SessionDetailDrawer();
  }

  /**
   * 初始化页面
   */
  async init() {
    console.log('[SessionsPage] Checking window.ensureAPIReady:', typeof window.ensureAPIReady);
    console.log('[SessionsPage] Checking window.api:', typeof window.api);

    try {
      // 确保API已初始化
      await window.ensureAPIReady();

      // 加载会话列表
      await this.loadSessions();

      // 渲染页面
      this.render();

      // 初始化事件监听
      this.setupEventListeners();
    } catch (error) {
      console.error('Failed to initialize sessions page:', error);
      this.showError('加载失败: ' + error.message);
    }
  }

  /**
   * 加载会话列表
   */
  async loadSessions() {
    try {
      this.allSessions = await window.api.getSessions();
      this.filteredSessions = [...this.allSessions];

      return this.allSessions;
    } catch (error) {
      console.error('Failed to load sessions:', error);
      throw error;
    }
  }

  /**
   * 渲染页面
   */
  render() {
    const container = document.getElementById('app');

    container.innerHTML = `
      <div class="p-6 space-y-6">
        <!-- 页面标题 -->
        <div class="flex justify-between items-center">
          <div>
            <h1 class="text-3xl font-bold">会话管理</h1>
            <p class="text-base-content/60 mt-1">管理所有翻译会话</p>
          </div>
          <button class="btn btn-primary gap-2" onclick="router.navigate('/create')">
            <i class="bi bi-plus-circle"></i>
            新建翻译
          </button>
        </div>

        <!-- 筛选栏 -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            ${this.renderFilterBar()}
          </div>
        </div>

        <!-- 批量操作工具栏 -->
        <div id="batchToolbar" class="hidden">
          ${this.renderBatchToolbar()}
        </div>

        <!-- 会话表格 -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <div id="sessionsTable">
              ${this.renderSessionTable()}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 渲染筛选栏
   */
  renderFilterBar() {
    return `
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <!-- 搜索框 -->
        <div class="form-control">
          <div class="input-group">
            <span><i class="bi bi-search"></i></span>
            <input type="text" placeholder="搜索文件名..."
                   class="input input-bordered w-full"
                   id="searchInput"
                   value="${this.filterState.searchText}">
          </div>
        </div>

        <!-- 时间范围 -->
        <div class="form-control">
          <select class="select select-bordered w-full" id="timeRangeSelect">
            <option value="all">全部时间</option>
            <option value="today">今天</option>
            <option value="week">本周</option>
            <option value="month">本月</option>
            <option value="custom">自定义</option>
          </select>
        </div>

        <!-- 状态 -->
        <div class="form-control">
          <select class="select select-bordered w-full" id="statusSelect">
            <option value="all">全部状态</option>
            <option value="created">待配置</option>
            <option value="split_complete">已配置</option>
            <option value="executing">执行中</option>
            <option value="completed">已完成</option>
            <option value="failed">失败</option>
          </select>
        </div>

        <!-- 操作按钮 -->
        <div class="flex gap-2">
          <button class="btn btn-primary flex-1" onclick="sessionsPage.applyFilters()">
            <i class="bi bi-funnel"></i>
            搜索
          </button>
          <button class="btn btn-ghost" onclick="sessionsPage.resetFilters()">
            重置
          </button>
        </div>
      </div>
    `;
  }

  /**
   * 渲染批量操作工具栏
   */
  renderBatchToolbar() {
    return `
      <div class="alert alert-info">
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center gap-2">
            <i class="bi bi-check-circle"></i>
            <span>已选 <span id="selectedCount">0</span> 个</span>
          </div>
          <div class="flex gap-2">
            <button class="btn btn-sm btn-success gap-2" onclick="sessionsPage.batchDownload()">
              <i class="bi bi-download"></i>
              批量下载
            </button>
            <button class="btn btn-sm btn-error gap-2" onclick="sessionsPage.batchDelete()">
              <i class="bi bi-trash"></i>
              批量删除
            </button>
            <button class="btn btn-sm btn-ghost" onclick="sessionsPage.clearSelection()">
              取消选择
            </button>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 渲染会话表格
   */
  renderSessionTable() {
    if (this.filteredSessions.length === 0) {
      return this.renderEmptyState();
    }

    return `
      <div class="overflow-x-auto">
        <table class="table table-zebra">
          <thead>
            <tr>
              <th>
                <input type="checkbox" class="checkbox" id="selectAll" onchange="sessionsPage.toggleSelectAll(this.checked)">
              </th>
              <th>文件名</th>
              <th>状态</th>
              <th>进度</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            ${this.filteredSessions.map(session => this.renderSessionRow(session)).join('')}
          </tbody>
        </table>

        <!-- 分页 (暂未实现) -->
        <div class="flex justify-center mt-4">
          <div class="btn-group">
            <button class="btn btn-sm">«</button>
            <button class="btn btn-sm btn-active">1</button>
            <button class="btn btn-sm">»</button>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 渲染会话行
   */
  renderSessionRow(session) {
    return `
      <tr class="hover" data-session-id="${session.sessionId}">
        <td>
          <input type="checkbox" class="checkbox" data-session-id="${session.sessionId}"
                 onchange="sessionsPage.toggleSelectSession('${session.sessionId}', this.checked)">
        </td>
        <td>
          <div class="flex items-center gap-2">
            <i class="bi bi-file-earmark-excel text-success"></i>
            <span class="font-medium cursor-pointer hover:text-primary"
                  onclick="sessionsPage.showDetail('${session.sessionId}')">
              ${session.filename}
            </span>
          </div>
        </td>
        <td>${this.renderStatusBadge(session.stage)}</td>
        <td>${this.renderProgress(session)}</td>
        <td>${this.formatTimeAgo(session.updatedAt)}</td>
        <td>
          <div class="dropdown dropdown-end">
            <label tabindex="0" class="btn btn-ghost btn-sm">
              <i class="bi bi-three-dots-vertical"></i>
            </label>
            <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
              <li><a onclick="sessionsPage.showDetail('${session.sessionId}')">
                <i class="bi bi-eye"></i> 查看详情
              </a></li>
              ${session.stage === 'completed' ? `
                <li><a onclick="sessionsPage.downloadSession('${session.sessionId}')">
                  <i class="bi bi-download"></i> 下载结果
                </a></li>
              ` : ''}
              ${session.stage !== 'completed' && session.stage !== 'executing' ? `
                <li><a onclick="sessionsPage.continueSession('${session.sessionId}')">
                  <i class="bi bi-play-fill"></i> 继续
                </a></li>
              ` : ''}
              <li><a class="text-error" onclick="sessionsPage.deleteSession('${session.sessionId}')">
                <i class="bi bi-trash"></i> 删除
              </a></li>
            </ul>
          </div>
        </td>
      </tr>
    `;
  }

  /**
   * 渲染状态Badge
   */
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

  /**
   * 渲染进度条
   */
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

  /**
   * 渲染空状态
   */
  renderEmptyState() {
    return `
      <div class="text-center py-12">
        <i class="bi bi-inbox text-6xl text-base-content/30"></i>
        <p class="text-lg mt-4">没有找到匹配的会话</p>
        <p class="text-sm text-base-content/60 mt-2">尝试调整筛选条件或创建新的翻译</p>
        <button class="btn btn-ghost mt-4" onclick="sessionsPage.resetFilters()">
          <i class="bi bi-arrow-clockwise"></i>
          重置筛选
        </button>
      </div>
    `;
  }

  /**
   * 设置事件监听
   */
  setupEventListeners() {
    // 搜索框实时搜索
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.filterState.searchText = e.target.value;
        this.applyFilters();
      });
    }
  }

  /**
   * 应用筛选
   */
  applyFilters() {
    // 读取筛选值
    const searchInput = document.getElementById('searchInput');
    const timeRangeSelect = document.getElementById('timeRangeSelect');
    const statusSelect = document.getElementById('statusSelect');

    if (searchInput) this.filterState.searchText = searchInput.value;
    if (timeRangeSelect) this.filterState.timeRange = timeRangeSelect.value;
    if (statusSelect) this.filterState.status = statusSelect.value;

    // 执行筛选
    this.filteredSessions = [...this.allSessions];

    // 搜索过滤
    if (this.filterState.searchText) {
      const searchLower = this.filterState.searchText.toLowerCase();
      this.filteredSessions = this.filteredSessions.filter(s =>
        s.filename.toLowerCase().includes(searchLower) ||
        s.sessionId.toLowerCase().includes(searchLower)
      );
    }

    // 时间范围过滤
    if (this.filterState.timeRange !== 'all') {
      this.filteredSessions = this.filterByTimeRange(
        this.filteredSessions,
        this.filterState.timeRange
      );
    }

    // 状态过滤
    if (this.filterState.status !== 'all') {
      this.filteredSessions = this.filteredSessions.filter(s =>
        s.stage === this.filterState.status
      );
    }

    // 重新渲染表格
    const tableContainer = document.getElementById('sessionsTable');
    if (tableContainer) {
      tableContainer.innerHTML = this.renderSessionTable();
    }
  }

  /**
   * 按时间范围过滤
   */
  filterByTimeRange(sessions, range) {
    const now = new Date();
    let startDate;

    switch (range) {
      case 'today':
        startDate = new Date(now.setHours(0, 0, 0, 0));
        break;
      case 'week':
        startDate = new Date(now.setDate(now.getDate() - 7));
        break;
      case 'month':
        startDate = new Date(now.setMonth(now.getMonth() - 1));
        break;
      default:
        return sessions;
    }

    return sessions.filter(s => new Date(s.createdAt) >= startDate);
  }

  /**
   * 重置筛选
   */
  resetFilters() {
    this.filterState = {
      searchText: '',
      timeRange: 'all',
      status: 'all',
      project: 'all'
    };

    // 重置表单
    const searchInput = document.getElementById('searchInput');
    const timeRangeSelect = document.getElementById('timeRangeSelect');
    const statusSelect = document.getElementById('statusSelect');

    if (searchInput) searchInput.value = '';
    if (timeRangeSelect) timeRangeSelect.value = 'all';
    if (statusSelect) statusSelect.value = 'all';

    // 应用筛选
    this.applyFilters();
  }

  /**
   * 切换全选
   */
  toggleSelectAll(checked) {
    if (checked) {
      const sessionIds = this.filteredSessions.map(s => s.sessionId);
      this.selectionManager.selectAll(sessionIds);
    } else {
      this.selectionManager.clearAll();
    }

    // 更新checkbox状态
    document.querySelectorAll('input[data-session-id]').forEach(cb => {
      cb.checked = checked;
    });
  }

  /**
   * 切换选择单个会话
   */
  toggleSelectSession(sessionId, checked) {
    this.selectionManager.toggleSelect(sessionId, checked);
  }

  /**
   * 清除选择
   */
  clearSelection() {
    this.selectionManager.clearAll();

    // 更新checkbox状态
    document.querySelectorAll('input[data-session-id]').forEach(cb => {
      cb.checked = false;
    });
    document.getElementById('selectAll').checked = false;
  }

  /**
   * 批量下载
   */
  async batchDownload() {
    const selectedIds = this.selectionManager.getSelected();
    if (selectedIds.length === 0) {
      alert('请先选择要下载的会话');
      return;
    }

    try {
      for (const sessionId of selectedIds) {
        const blob = await window.api.downloadSession(sessionId);
        const info = await window.api.getDownloadInfo(sessionId);

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = info.filename || `session_${sessionId}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
      alert(`成功下载 ${selectedIds.length} 个会话`);
    } catch (error) {
      console.error('Failed to batch download:', error);
      alert('批量下载失败: ' + error.message);
    }
  }

  /**
   * 批量删除
   */
  async batchDelete() {
    const selectedIds = this.selectionManager.getSelected();
    if (selectedIds.length === 0) {
      alert('请先选择要删除的会话');
      return;
    }

    const confirmed = confirm(`确定要删除这 ${selectedIds.length} 个会话吗？删除后无法恢复。`);
    if (!confirmed) return;

    try {
      for (const sessionId of selectedIds) {
        await window.api.deleteSession(sessionId);
      }

      this.allSessions = this.allSessions.filter(s => !selectedIds.includes(s.sessionId));
      this.clearSelection();
      this.applyFilters();

      alert(`成功删除 ${selectedIds.length} 个会话`);
    } catch (error) {
      console.error('Failed to batch delete:', error);
      alert('批量删除失败: ' + error.message);
    }
  }

  /**
   * 显示会话详情
   */
  showDetail(sessionId) {
    const session = this.allSessions.find(s => s.sessionId === sessionId);
    if (!session) return;

    this.detailDrawer.open(session);
  }

  /**
   * 继续会话
   */
  continueSession(sessionId) {
    console.log('Continue session:', sessionId);
    // router.navigate(`/config/${sessionId}`);
  }

  /**
   * 下载会话
   */
  async downloadSession(sessionId) {
    try {
      const blob = await window.api.downloadSession(sessionId);
      const info = await window.api.getDownloadInfo(sessionId);

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = info.filename || `session_${sessionId}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download:', error);
      alert('下载失败: ' + error.message);
    }
  }

  /**
   * 删除会话
   */
  async deleteSession(sessionId) {
    const confirmed = confirm('确定要删除这个会话吗？删除后无法恢复。');
    if (!confirmed) return;

    try {
      await window.api.deleteSession(sessionId);

      this.allSessions = this.allSessions.filter(s => s.sessionId !== sessionId);
      this.applyFilters();

      alert('删除成功');
    } catch (error) {
      console.error('Failed to delete:', error);
      alert('删除失败: ' + error.message);
    }
  }

  /**
   * 格式化相对时间
   */
  formatTimeAgo(timestamp) {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);

    if (seconds < 60) return '刚刚';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟前`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时前`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}天前`;

    return new Date(timestamp).toLocaleDateString();
  }

  /**
   * 显示错误信息
   */
  showError(message) {
    const container = document.getElementById('app');
    container.innerHTML = `
      <div class="p-6">
        <div class="alert alert-error">
          <i class="bi bi-exclamation-triangle"></i>
          <span>${message}</span>
        </div>
      </div>
    `;
  }

  /**
   * 清理资源
   */
  destroy() {
    this.selectionManager = null;
    this.detailDrawer = null;
  }
}

/**
 * SelectionManager - 选择状态管理
 */
class SelectionManager {
  constructor() {
    this.selectedIds = new Set();
  }

  toggleSelect(sessionId, checked) {
    if (checked) {
      this.selectedIds.add(sessionId);
    } else {
      this.selectedIds.delete(sessionId);
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
    // 更新批量操作工具栏
    const batchToolbar = document.getElementById('batchToolbar');
    const selectedCount = document.getElementById('selectedCount');

    if (batchToolbar) {
      if (this.selectedIds.size > 0) {
        batchToolbar.classList.remove('hidden');
        if (selectedCount) {
          selectedCount.textContent = this.selectedIds.size;
        }
      } else {
        batchToolbar.classList.add('hidden');
      }
    }
  }
}

/**
 * SessionDetailDrawer - 会话详情侧边栏
 */
class SessionDetailDrawer {
  constructor() {
    this.drawer = null;
    this.sessionId = null;
  }

  async open(session) {
    this.sessionId = session.sessionId;

    // 创建抽屉DOM
    this.drawer = document.createElement('div');
    this.drawer.className = 'fixed inset-0 z-50';
    this.drawer.innerHTML = `
      <!-- 遮罩 -->
      <div class="fixed inset-0 bg-black/50" onclick="sessionsPage.detailDrawer.close()"></div>

      <!-- 侧边栏 -->
      <div class="fixed right-0 top-0 h-full w-96 bg-base-100 shadow-xl overflow-y-auto">
        <div class="p-6">
          <!-- 标题栏 -->
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold">会话详情</h2>
            <button class="btn btn-sm btn-ghost btn-circle" onclick="sessionsPage.detailDrawer.close()">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>

          <!-- 内容 -->
          <div class="space-y-6">
            ${this.renderContent(session)}
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(this.drawer);
  }

  renderContent(session) {
    return `
      <!-- 基本信息 -->
      <div>
        <h3 class="font-semibold mb-2 flex items-center gap-2">
          <i class="bi bi-file-earmark-excel"></i>
          基本信息
        </h3>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-base-content/60">文件名</span>
            <span class="font-medium">${session.filename}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-base-content/60">Session ID</span>
            <code class="text-xs">${session.sessionId}</code>
          </div>
          <div class="flex justify-between">
            <span class="text-base-content/60">创建时间</span>
            <span>${new Date(session.createdAt).toLocaleString()}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-base-content/60">状态</span>
            ${this.renderStatusBadge(session.stage)}
          </div>
        </div>
      </div>

      <!-- 配置信息 -->
      ${session.config ? this.renderConfig(session.config) : ''}

      <!-- 执行统计 -->
      ${session.executionResult ? this.renderExecutionStats(session.executionResult) : ''}

      <!-- 操作按钮 -->
      <div class="flex gap-2 mt-6">
        ${session.stage === 'completed' ? `
          <button class="btn btn-success flex-1" onclick="sessionsPage.downloadSession('${session.sessionId}')">
            <i class="bi bi-download"></i>
            下载结果
          </button>
        ` : session.stage !== 'executing' ? `
          <button class="btn btn-primary flex-1" onclick="sessionsPage.continueSession('${session.sessionId}')">
            <i class="bi bi-play-fill"></i>
            继续
          </button>
        ` : ''}
      </div>
    `;
  }

  renderStatusBadge(stage) {
    const statusMap = {
      'created': { label: '待配置', class: 'badge-info' },
      'split_complete': { label: '已配置', class: 'badge-info' },
      'executing': { label: '执行中', class: 'badge-warning' },
      'completed': { label: '已完成', class: 'badge-success' },
      'failed': { label: '失败', class: 'badge-error' }
    };

    const status = statusMap[stage] || statusMap.created;
    return `<span class="badge ${status.class}">${status.label}</span>`;
  }

  renderConfig(config) {
    return `
      <div>
        <h3 class="font-semibold mb-2 flex items-center gap-2">
          <i class="bi bi-gear"></i>
          配置信息
        </h3>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-base-content/60">源语言</span>
            <span>${config.source_lang}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-base-content/60">目标语言</span>
            <span>${config.target_langs.join(', ')}</span>
          </div>
        </div>
      </div>
    `;
  }

  renderExecutionStats(result) {
    return `
      <div>
        <h3 class="font-semibold mb-2 flex items-center gap-2">
          <i class="bi bi-bar-chart"></i>
          执行统计
        </h3>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-base-content/60">成本</span>
            <span class="font-medium">$${result.cost}</span>
          </div>
        </div>
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

// 创建全局实例
const sessionsPage = new SessionsPage();

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SessionsPage;
}
