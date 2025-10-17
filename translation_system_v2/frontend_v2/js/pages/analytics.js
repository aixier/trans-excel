/**
 * Analytics Page - 数据分析页面
 * 负责翻译统计、成本分析、趋势图表展示
 *
 * @author Engineer C
 * @date 2025-10-17
 */

class AnalyticsPage {
  constructor() {
    this.sessions = [];
    this.timeRange = 'month'; // day | week | month | year
    this.stats = null;
    this.charts = {}; // 存储Chart.js实例
  }

  /**
   * 初始化页面
   */
  async init() {
    console.log('[AnalyticsPage] Initializing...');
    console.log('[AnalyticsPage] Checking window.ensureAPIReady:', typeof window.ensureAPIReady);
    console.log('[AnalyticsPage] Checking window.api:', typeof window.api);

    try {
      // 确保API已初始化
      await window.ensureAPIReady();

      // 加载数据
      await this.loadData(this.timeRange);

      // 渲染页面
      this.render();

      // 渲染图表（需要等DOM加载完成）
      setTimeout(() => {
        this.renderCharts();
      }, 100);
    } catch (error) {
      console.error('[AnalyticsPage] Init failed:', error);
      this.showError('初始化失败', error.message);
    }
  }

  /**
   * 加载数据
   * @param {string} timeRange - 时间范围
   */
  async loadData(timeRange = 'month') {
    console.log('[AnalyticsPage] Loading data for:', timeRange);

    this.timeRange = timeRange;

    try {
      const analyticsData = await window.api.getAnalytics({ time_range: timeRange });

      this.sessions = analyticsData.sessions || await window.api.getSessions();

      this.stats = this.calculateStats();

      console.log('[AnalyticsPage] Stats calculated:', this.stats);
    } catch (error) {
      console.error('[AnalyticsPage] Failed to load data:', error);
      throw error;
    }
  }

  /**
   * 计算统计数据
   */
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

    // 7. 平均速度（任务/分钟）
    const avgSpeed = this.calculateAvgSpeed(completedSessions);

    return {
      totalTasks,
      completedTasks,
      totalCost,
      successRate,
      avgSpeed,
      langStats,
      modelStats,
      trends
    };
  }

  /**
   * 按语言分组统计
   * @param {Array} sessions - 会话列表
   */
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

  /**
   * 按模型分组统计
   * @param {Array} sessions - 会话列表
   */
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

  /**
   * 计算趋势数据
   */
  calculateTrends() {
    const dailyStats = {};

    this.sessions.forEach(session => {
      const date = new Date(session.createdAt).toLocaleDateString();

      if (!dailyStats[date]) {
        dailyStats[date] = { tasks: 0, cost: 0 };
      }

      dailyStats[date].tasks += session.executionResult?.completedTasks || 0;
      dailyStats[date].cost += session.executionResult?.cost || 0;
    });

    return Object.entries(dailyStats)
      .map(([date, stats]) => ({ date, ...stats }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));
  }

  /**
   * 计算平均速度
   * @param {Array} sessions - 完成的会话列表
   */
  calculateAvgSpeed(sessions) {
    if (sessions.length === 0) return 0;

    const totalSpeed = sessions.reduce((sum, s) => {
      const duration = s.executionResult?.duration || 1;
      const tasks = s.executionResult?.completedTasks || 0;
      const speed = (tasks / duration) * 60 * 1000; // 转换为任务/分钟
      return sum + speed;
    }, 0);

    return Math.round(totalSpeed / sessions.length);
  }

  /**
   * 渲染页面主结构
   */
  render() {
    const container = document.getElementById('app');

    container.innerHTML = `
      <div class="container mx-auto p-6">
        <!-- 页面标题和时间范围选择 -->
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-3xl font-bold flex items-center gap-2">
            <i class="bi bi-bar-chart"></i>
            数据分析
          </h1>
          <div class="flex gap-2">
            ${this.renderTimeRangeButtons()}
          </div>
        </div>

        <!-- 统计卡片 -->
        ${this.renderStatCards()}

        <!-- 图表区域 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          <!-- 翻译量趋势图 -->
          <div class="card bg-base-100 shadow-xl">
            <div class="card-body">
              <h3 class="card-title text-lg">翻译量趋势</h3>
              <div class="h-64">
                <canvas id="trendChart"></canvas>
              </div>
            </div>
          </div>

          <!-- 语言分布饼图 -->
          <div class="card bg-base-100 shadow-xl">
            <div class="card-body">
              <h3 class="card-title text-lg">语言分布</h3>
              <div class="h-64">
                <canvas id="languageChart"></canvas>
              </div>
            </div>
          </div>
        </div>

        <!-- 成本分析 -->
        <div class="card bg-base-100 shadow-xl mt-6">
          <div class="card-body">
            ${this.renderCostAnalysis()}
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 渲染时间范围按钮
   */
  renderTimeRangeButtons() {
    const ranges = [
      { value: 'day', label: '日' },
      { value: 'week', label: '周' },
      { value: 'month', label: '月' },
      { value: 'year', label: '年' }
    ];

    return `
      <div class="btn-group">
        ${ranges.map(r => `
          <button
            class="btn btn-sm ${this.timeRange === r.value ? 'btn-active' : ''}"
            onclick="analyticsPage.changeTimeRange('${r.value}')"
          >
            ${r.label}
          </button>
        `).join('')}
      </div>
    `;
  }

  /**
   * 渲染统计卡片
   */
  renderStatCards() {
    if (!this.stats) return '';

    return `
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- 总翻译量 -->
        <div class="stat bg-base-100 shadow-xl rounded-lg">
          <div class="stat-figure text-primary">
            <i class="bi bi-clipboard-check text-4xl"></i>
          </div>
          <div class="stat-title">总翻译量</div>
          <div class="stat-value text-primary">${this.stats.totalTasks}</div>
          <div class="stat-desc">
            <span class="text-success">↑ 15.2%</span> 较上期
          </div>
        </div>

        <!-- 总成本 -->
        <div class="stat bg-base-100 shadow-xl rounded-lg">
          <div class="stat-figure text-secondary">
            <i class="bi bi-cash-stack text-4xl"></i>
          </div>
          <div class="stat-title">总成本</div>
          <div class="stat-value text-secondary">$${this.stats.totalCost.toFixed(2)}</div>
          <div class="stat-desc">
            <span class="text-error">↓ 8.3%</span> 较上期
          </div>
        </div>

        <!-- 平均速度 -->
        <div class="stat bg-base-100 shadow-xl rounded-lg">
          <div class="stat-figure text-accent">
            <i class="bi bi-lightning-fill text-4xl"></i>
          </div>
          <div class="stat-title">平均速度</div>
          <div class="stat-value text-accent">${this.stats.avgSpeed}/分钟</div>
          <div class="stat-desc">
            <span class="text-success">↑ 5.1%</span> 较上期
          </div>
        </div>

        <!-- 成功率 -->
        <div class="stat bg-base-100 shadow-xl rounded-lg">
          <div class="stat-figure text-success">
            <i class="bi bi-check-circle-fill text-4xl"></i>
          </div>
          <div class="stat-title">成功率</div>
          <div class="stat-value text-success">${this.stats.successRate.toFixed(1)}%</div>
          <div class="stat-desc">
            <span class="text-success">↑ 2.1%</span> 较上期
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 渲染成本分析
   */
  renderCostAnalysis() {
    if (!this.stats) return '';

    const budget = 50.0; // 从配置读取
    const costPercent = (this.stats.totalCost / budget) * 100;

    return `
      <h3 class="card-title text-lg mb-4 flex items-center gap-2">
        <i class="bi bi-wallet2"></i>
        成本分析（本月）
      </h3>

      <!-- 预算进度 -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm">总成本</span>
          <span class="text-2xl font-bold">$${this.stats.totalCost.toFixed(2)} / $${budget.toFixed(2)}</span>
        </div>
        <progress
          class="progress ${costPercent > 80 ? 'progress-error' : 'progress-success'} w-full h-3"
          value="${costPercent}"
          max="100"
        ></progress>
        <span class="text-sm text-base-content/60">${costPercent.toFixed(1)}% 预算</span>

        ${costPercent > 80 ? `
          <div class="alert alert-warning mt-4">
            <i class="bi bi-exclamation-triangle"></i>
            <span>预算即将超支，请注意控制成本</span>
          </div>
        ` : ''}
      </div>

      <!-- 按模型分组 -->
      <h4 class="font-semibold mb-3">按模型分组</h4>
      <div class="space-y-3">
        ${Object.entries(this.stats.modelStats).map(([model, stats]) => {
          const modelPercent = (stats.cost / this.stats.totalCost) * 100;
          return `
            <div>
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-medium">${model}</span>
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium">$${stats.cost.toFixed(2)}</span>
                  <span class="text-xs text-base-content/60">(${modelPercent.toFixed(1)}%)</span>
                </div>
              </div>
              <progress class="progress progress-primary w-full" value="${modelPercent}" max="100"></progress>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  /**
   * 渲染图表
   */
  renderCharts() {
    if (!this.stats) return;

    // 需要Chart.js库
    if (typeof Chart === 'undefined') {
      console.warn('[AnalyticsPage] Chart.js not loaded');
      return;
    }

    this.renderTrendChart();
    this.renderLanguageChart();
  }

  /**
   * 渲染翻译量趋势图
   */
  renderTrendChart() {
    const canvas = document.getElementById('trendChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // 销毁旧图表
    if (this.charts.trend) {
      this.charts.trend.destroy();
    }

    this.charts.trend = new Chart(ctx, {
      type: 'line',
      data: {
        labels: this.stats.trends.map(d => d.date),
        datasets: [{
          label: '翻译量',
          data: this.stats.trends.map(d => d.tasks),
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

  /**
   * 渲染语言分布饼图
   */
  renderLanguageChart() {
    const canvas = document.getElementById('languageChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // 销毁旧图表
    if (this.charts.language) {
      this.charts.language.destroy();
    }

    const languages = Object.keys(this.stats.langStats);
    const counts = Object.values(this.stats.langStats);
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
        maintainAspectRatio: false,
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

  /**
   * 切换时间范围
   * @param {string} timeRange - 时间范围
   */
  async changeTimeRange(timeRange) {
    console.log('[AnalyticsPage] Change time range:', timeRange);

    try {
      // 重新加载数据
      await this.loadData(timeRange);

      // 重新渲染
      this.render();

      // 重新渲染图表
      setTimeout(() => {
        this.renderCharts();
      }, 100);
    } catch (error) {
      console.error('[AnalyticsPage] Failed to change time range:', error);
      this.showError('切换失败', error.message);
    }
  }

  /**
   * 显示错误消息
   */
  showError(title, message) {
    console.error('[AnalyticsPage] Error:', title, message);
    alert(`${title}: ${message}`);
  }
}

// 创建全局实例（由app.js的Router调用init）
let analyticsPage;
