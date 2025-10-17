/**
 * Dashboard Page - 智能工作台
 *
 * 负责展示系统首页的核心指标和最近项目列表
 *
 * 依赖:
 * - StatCard 组件 (工程师A)
 * - DataTable 组件 (工程师A)
 * - SessionManager (工程师A)
 * - API (工程师A)
 *
 * @author 工程师B
 * @date 2025-10-17
 */

class DashboardPage {
  constructor() {
    this.stats = null;
    this.recentSessions = [];
    this.pollInterval = null;
    this.AUTO_REFRESH_INTERVAL = 30000; // 30秒刷新一次
  }

  /**
   * 初始化页面
   */
  async init() {
    console.log('[DashboardPage] Checking window.ensureAPIReady:', typeof window.ensureAPIReady);
    console.log('[DashboardPage] Checking window.api:', typeof window.api);

    try {
      // 确保API已初始化
      await window.ensureAPIReady();

      // 加载统计数据
      await this.loadDashboardStats();

      // 加载最近会话
      await this.loadRecentSessions(10);

      // 渲染页面
      this.render();

      // 设置自动刷新
      this.setupAutoRefresh();
    } catch (error) {
      console.error('Failed to initialize dashboard:', error);
      this.showError('加载失败: ' + error.message);
    }
  }

  /**
   * 加载工作台统计数据
   */
  async loadDashboardStats() {
    try {
      const sessions = await window.api.getSessions();

      // 今日待办
      const today = new Date().toDateString();
      const todaySessions = sessions.filter(s =>
        new Date(s.createdAt).toDateString() === today
      );
      const todayPending = todaySessions.filter(s =>
        s.stage !== 'completed' && s.stage !== 'failed'
      ).length;

      // 执行中任务
      const runningSessions = sessions.filter(s => s.stage === 'executing');
      const running = runningSessions.length;
      const runningProgress = running > 0
        ? Math.round((runningSessions[0].progress?.completed / runningSessions[0].progress?.total) * 100) || 0
        : 0;

      // 本月完成
      const monthStart = new Date();
      monthStart.setDate(1);
      monthStart.setHours(0, 0, 0, 0);

      const completedThisMonth = sessions.filter(s =>
        s.stage === 'completed' &&
        new Date(s.completedAt) >= monthStart
      );

      // 本月成本
      const monthlyCost = completedThisMonth.reduce((sum, s) => {
        return sum + (s.executionResult?.cost || 0);
      }, 0);

      // 计算趋势 (与上月对比)
      const lastMonthStart = new Date(monthStart);
      lastMonthStart.setMonth(lastMonthStart.getMonth() - 1);
      const lastMonthCompleted = sessions.filter(s =>
        s.stage === 'completed' &&
        new Date(s.completedAt) >= lastMonthStart &&
        new Date(s.completedAt) < monthStart
      ).length;

      const completedTrend = lastMonthCompleted > 0
        ? Math.round(((completedThisMonth.length - lastMonthCompleted) / lastMonthCompleted) * 100)
        : 0;

      this.stats = {
        todayPending,
        running,
        runningProgress,
        monthlyCompleted: completedThisMonth.length,
        completedTrend,
        monthlyCost,
        budget: 50.0  // 从配置读取
      };

      return this.stats;
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
      throw error;
    }
  }

  /**
   * 加载最近项目列表
   * @param {number} limit - 显示条数，默认10
   */
  async loadRecentSessions(limit = 10) {
    try {
      const sessions = await window.api.getSessions();

      // 按更新时间排序
      sessions.sort((a, b) => b.updatedAt - a.updatedAt);

      // 取前N条
      this.recentSessions = sessions.slice(0, limit);

      // 对于执行中的会话，启动轮询更新进度
      const runningSessions = this.recentSessions.filter(s => s.stage === 'executing');
      if (runningSessions.length > 0) {
        this.startProgressPolling(runningSessions);
      }

      return this.recentSessions;
    } catch (error) {
      console.error('Failed to load recent sessions:', error);
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
            <h1 class="text-3xl font-bold">智能工作台</h1>
            <p class="text-base-content/60 mt-1">欢迎回来，让我们开始翻译吧</p>
          </div>
          <button class="btn btn-primary gap-2" onclick="router.navigate('/create')">
            <i class="bi bi-plus-circle"></i>
            新建翻译
          </button>
        </div>

        <!-- 核心指标卡片 -->
        <div id="statCards">
          ${this.renderStatCards()}
        </div>

        <!-- 最近项目列表 -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <div class="flex justify-between items-center mb-4">
              <h2 class="card-title">最近项目</h2>
              <button class="btn btn-ghost btn-sm" onclick="router.navigate('/sessions')">
                查看全部 <i class="bi bi-arrow-right"></i>
              </button>
            </div>

            <div id="recentSessionsTable">
              ${this.renderSessionTable()}
            </div>
          </div>
        </div>

        <!-- 快速操作区 -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title mb-4">快速操作</h2>
            ${this.renderQuickActions()}
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 渲染统计卡片
   */
  renderStatCards() {
    if (!this.stats) return '<div class="loading loading-spinner loading-lg"></div>';

    const budgetPercent = (this.stats.monthlyCost / this.stats.budget) * 100;
    const budgetWarning = budgetPercent > 80;

    return `
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- 今日待办 -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <div class="flex items-center gap-2">
              <i class="bi bi-clipboard-check text-2xl text-info"></i>
              <div>
                <p class="text-sm text-base-content/60">今日待办</p>
                <p class="text-3xl font-bold">${this.stats.todayPending}</p>
                <p class="text-xs text-base-content/50 mt-1">个任务</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 执行中任务 -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <div class="flex items-center gap-2">
              <i class="bi bi-lightning-fill text-2xl text-warning"></i>
              <div class="flex-1">
                <p class="text-sm text-base-content/60">执行中任务</p>
                <p class="text-3xl font-bold">${this.stats.running}</p>
                ${this.stats.running > 0 ? `
                  <div class="flex items-center gap-2 mt-2">
                    <progress class="progress progress-warning w-20" value="${this.stats.runningProgress}" max="100"></progress>
                    <span class="text-xs">${this.stats.runningProgress}%</span>
                  </div>
                ` : '<p class="text-xs text-base-content/50 mt-1">暂无执行中</p>'}
              </div>
            </div>
          </div>
        </div>

        <!-- 本月完成 -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <div class="flex items-center gap-2">
              <i class="bi bi-check-circle-fill text-2xl text-success"></i>
              <div>
                <p class="text-sm text-base-content/60">本月完成</p>
                <p class="text-3xl font-bold">${this.stats.monthlyCompleted}</p>
                <p class="text-xs ${this.stats.completedTrend >= 0 ? 'text-success' : 'text-error'} mt-1">
                  <i class="bi bi-arrow-${this.stats.completedTrend >= 0 ? 'up' : 'down'}"></i>
                  ${Math.abs(this.stats.completedTrend)}% vs 上月
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- 本月成本 -->
        <div class="card bg-base-100 shadow-xl ${budgetWarning ? 'border-2 border-warning' : ''}">
          <div class="card-body">
            <div class="flex items-center gap-2">
              <i class="bi bi-cash-stack text-2xl ${budgetWarning ? 'text-warning' : 'text-primary'}"></i>
              <div class="flex-1">
                <p class="text-sm text-base-content/60">本月成本</p>
                <p class="text-3xl font-bold">$${this.stats.monthlyCost.toFixed(2)}</p>
                <div class="mt-2">
                  <progress class="progress ${budgetWarning ? 'progress-warning' : 'progress-primary'} w-full"
                            value="${budgetPercent}" max="100"></progress>
                  <p class="text-xs text-base-content/50 mt-1">
                    预算: $${this.stats.budget.toFixed(2)} (${Math.round(budgetPercent)}%)
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 渲染会话表格
   */
  renderSessionTable() {
    if (this.recentSessions.length === 0) {
      return this.renderEmptyState();
    }

    return `
      <div class="overflow-x-auto">
        <table class="table table-zebra">
          <thead>
            <tr>
              <th>文件名</th>
              <th>状态</th>
              <th>进度</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            ${this.recentSessions.map(session => this.renderSessionRow(session)).join('')}
          </tbody>
        </table>
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
          <div class="flex items-center gap-2">
            <i class="bi bi-file-earmark-excel text-success"></i>
            <span class="font-medium">${session.filename}</span>
          </div>
        </td>
        <td>${this.renderStatusBadge(session.stage)}</td>
        <td>${this.renderProgress(session)}</td>
        <td>${this.formatTimeAgo(session.updatedAt)}</td>
        <td>${this.renderActions(session)}</td>
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
   * 渲染操作按钮
   */
  renderActions(session) {
    let primaryAction = '';

    if (session.stage === 'executing') {
      primaryAction = `
        <button class="btn btn-sm btn-ghost" onclick="dashboardPage.viewSession('${session.sessionId}')">
          <i class="bi bi-eye"></i> 查看
        </button>
      `;
    } else if (session.stage === 'completed') {
      primaryAction = `
        <button class="btn btn-sm btn-success" onclick="dashboardPage.downloadResult('${session.sessionId}')">
          <i class="bi bi-download"></i> 下载
        </button>
      `;
    } else {
      primaryAction = `
        <button class="btn btn-sm btn-primary" onclick="dashboardPage.continueSession('${session.sessionId}')">
          <i class="bi bi-play-fill"></i> 继续
        </button>
      `;
    }

    // Add delete button for all sessions
    const deleteButton = `
      <button class="btn btn-sm btn-error btn-outline" onclick="dashboardPage.deleteSession('${session.sessionId}', '${session.filename}')" title="删除">
        <i class="bi bi-trash"></i>
      </button>
    `;

    return `
      <div class="flex gap-2">
        ${primaryAction}
        ${deleteButton}
      </div>
    `;
  }

  /**
   * 渲染空状态
   */
  renderEmptyState() {
    return `
      <div class="text-center py-12">
        <i class="bi bi-inbox text-6xl text-base-content/30"></i>
        <p class="text-lg mt-4">暂无翻译记录</p>
        <p class="text-sm text-base-content/60 mt-2">上传Excel文件开始翻译吧</p>
        <button class="btn btn-primary mt-4" onclick="router.navigate('/create')">
          <i class="bi bi-plus-circle"></i>
          新建翻译
        </button>
      </div>
    `;
  }

  /**
   * 渲染快速操作区
   */
  renderQuickActions() {
    return `
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
    `;
  }

  /**
   * 设置自动刷新
   */
  setupAutoRefresh() {
    // 清除旧的定时器
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }

    // 每30秒刷新一次执行中任务的进度
    this.pollInterval = setInterval(async () => {
      const runningSessions = this.recentSessions.filter(s => s.stage === 'executing');

      if (runningSessions.length === 0) {
        return;
      }

      for (const session of runningSessions) {
        try {
          const progress = await window.api.getExecutionProgress(session.sessionId);

          if (progress) {
            session.progress = progress;

            if (progress.completed >= progress.total) {
              session.stage = 'completed';
              session.completedAt = Date.now();
            }
          }

          this.updateProgressInTable(session.sessionId, session.progress);
        } catch (error) {
          console.error(`Failed to refresh progress:`, error);
        }
      }

      // 如果所有任务都完成，停止轮询
      const stillRunning = this.recentSessions.some(s => s.stage === 'executing');
      if (!stillRunning) {
        clearInterval(this.pollInterval);
        // 重新加载列表
        await this.loadRecentSessions(10);
        this.renderSessionTable();
      }
    }, this.AUTO_REFRESH_INTERVAL);
  }

  /**
   * 启动进度轮询（用于执行中的会话）
   */
  startProgressPolling(sessions) {
    // 已在 setupAutoRefresh 中实现
    console.log('Progress polling started for', sessions.length, 'sessions');
  }

  /**
   * 更新表格中的进度
   */
  updateProgressInTable(sessionId, progress) {
    const row = document.querySelector(`tr[data-session-id="${sessionId}"]`);
    if (!row || !progress) return;

    const progressCell = row.cells[2];
    const percent = Math.round((progress.completed / progress.total) * 100);

    progressCell.innerHTML = `
      <div class="flex items-center gap-2">
        <progress class="progress progress-warning w-20" value="${percent}" max="100"></progress>
        <span class="text-sm">${percent}%</span>
      </div>
    `;
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
   * 查看会话详情
   */
  viewSession(sessionId) {
    // TODO: 导航到执行页面
    console.log('View session:', sessionId);
    // router.navigate(`/execute/${sessionId}`);
  }

  /**
   * 继续会话
   */
  continueSession(sessionId) {
    console.log('Continue session:', sessionId);
    // 跳转到配置页面，并传递session_id
    router.navigate('/config');
    // 存储当前session_id供config页面使用
    sessionStorage.setItem('current_session_id', sessionId);
  }

  /**
   * 下载结果
   */
  async downloadResult(sessionId) {
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
  async deleteSession(sessionId, filename) {
    // Confirm deletion
    const confirmed = confirm(`确认删除项目 "${filename}"？\n\n此操作不可恢复。`);
    if (!confirmed) {
      return;
    }

    try {
      // Call API to delete session
      await window.api.deleteSession(sessionId);

      // Clear API cache to force reload
      window.api.clearCache();

      // Show success message
      this.showToast('删除成功', 'success');

      // Reload dashboard data
      await this.loadDashboardStats();
      await this.loadRecentSessions(10);

      // Re-render the table
      const tableContainer = document.getElementById('recentSessionsTable');
      if (tableContainer) {
        tableContainer.innerHTML = this.renderSessionTable();
      }

      // Re-render stats cards
      const statsContainer = document.getElementById('statCards');
      if (statsContainer) {
        statsContainer.innerHTML = this.renderStatCards();
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      this.showToast('删除失败: ' + error.message, 'error');
    }
  }

  /**
   * 显示Toast提示
   */
  showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} shadow-lg fixed top-4 right-4 w-auto max-w-md z-50`;
    toast.innerHTML = `
      <div>
        <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info-circle'}"></i>
        <span>${message}</span>
      </div>
    `;

    document.body.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
      toast.style.transition = 'opacity 0.3s';
      toast.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(toast);
      }, 300);
    }, 3000);
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
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }
}

// 创建全局实例
const dashboardPage = new DashboardPage();

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DashboardPage;
}
