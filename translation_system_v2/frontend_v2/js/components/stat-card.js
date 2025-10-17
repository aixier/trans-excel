/**
 * 统计卡片组件
 *
 * @class StatCard
 * @description
 * 显示关键指标的卡片组件，支持4种变体：基础、带图标、带趋势、带进度条
 *
 * @example
 * const card = new StatCard({
 *   title: '今日待办',
 *   value: 3,
 *   icon: 'bi-clipboard-check',
 *   trend: { value: 2, direction: 'up' }
 * });
 * container.innerHTML = card.render();
 */
class StatCard {
  /**
   * 创建StatCard实例
   *
   * @param {Object} config - 配置对象
   * @param {string} config.title - 标题
   * @param {number|string} config.value - 值
   * @param {string} [config.icon] - Bootstrap Icon类名（如 'bi-clipboard-check'）
   * @param {Object} [config.trend] - 趋势数据
   * @param {number} config.trend.value - 趋势值
   * @param {string} config.trend.direction - 趋势方向 ('up' | 'down')
   * @param {string} [config.trend.label] - 趋势标签（如 '较昨日'）
   * @param {Object} [config.progress] - 进度数据
   * @param {number} config.progress.value - 进度值（0-100）
   * @param {string} [config.progress.label] - 进度标签
   * @param {string} [config.color] - 主题色 ('primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info')
   * @param {string} [config.size] - 尺寸 ('sm' | 'md' | 'lg')
   * @param {Function} [config.onClick] - 点击回调
   */
  constructor(config) {
    this.title = config.title || '';
    this.value = config.value ?? 0;
    this.icon = config.icon || null;
    this.trend = config.trend || null;
    this.progress = config.progress || null;
    this.color = config.color || 'primary';
    this.size = config.size || 'md';
    this.onClick = config.onClick || null;
    this.containerId = config.containerId || null;
  }

  /**
   * 渲染卡片HTML
   *
   * @returns {string} HTML字符串
   */
  render() {
    const sizeClasses = {
      sm: 'p-3',
      md: 'p-4',
      lg: 'p-6'
    };

    const valueSizes = {
      sm: 'text-2xl',
      md: 'text-3xl',
      lg: 'text-4xl'
    };

    const clickableClass = this.onClick ? 'cursor-pointer hover:shadow-lg transition-shadow' : '';

    return `
      <div class="stat bg-base-100 rounded-lg shadow-md ${sizeClasses[this.size]} ${clickableClass}"
           ${this.containerId ? `id="${this.containerId}"` : ''}
           ${this.onClick ? `onclick="${this.onClick.name}()"` : ''}>
        <div class="flex items-center justify-between">
          <div class="flex-1">
            ${this._renderTitle()}
            ${this._renderValue()}
            ${this._renderTrend()}
            ${this._renderProgress()}
          </div>
          ${this._renderIcon()}
        </div>
      </div>
    `;
  }

  /**
   * 渲染标题
   * @private
   */
  _renderTitle() {
    const sizeClasses = {
      sm: 'text-xs',
      md: 'text-sm',
      lg: 'text-base'
    };

    return `
      <div class="stat-title ${sizeClasses[this.size]} text-base-content/60">
        ${this.title}
      </div>
    `;
  }

  /**
   * 渲染数值
   * @private
   */
  _renderValue() {
    const sizeClasses = {
      sm: 'text-2xl',
      md: 'text-3xl',
      lg: 'text-4xl'
    };

    return `
      <div class="stat-value ${sizeClasses[this.size]} text-${this.color} font-bold mt-1"
           data-stat-value="${this.value}">
        ${this.value}
      </div>
    `;
  }

  /**
   * 渲染趋势
   * @private
   */
  _renderTrend() {
    if (!this.trend) return '';

    const isUp = this.trend.direction === 'up';
    const color = isUp ? 'success' : 'error';
    const icon = isUp ? 'bi-arrow-up' : 'bi-arrow-down';
    const label = this.trend.label || (isUp ? '增长' : '下降');

    return `
      <div class="stat-desc mt-1">
        <span class="text-${color} font-semibold">
          <i class="bi ${icon}"></i>
          ${this.trend.value}
        </span>
        <span class="text-base-content/60 ml-1">${label}</span>
      </div>
    `;
  }

  /**
   * 渲染进度条
   * @private
   */
  _renderProgress() {
    if (!this.progress) return '';

    const progressValue = Math.min(100, Math.max(0, this.progress.value || 0));
    const label = this.progress.label || `${progressValue}% 完成`;

    return `
      <div class="mt-2">
        <progress class="progress progress-${this.color} w-full h-2"
                  value="${progressValue}" max="100"></progress>
        <span class="text-xs text-base-content/60">${label}</span>
      </div>
    `;
  }

  /**
   * 渲染图标
   * @private
   */
  _renderIcon() {
    if (!this.icon) return '';

    const iconSizes = {
      sm: 'text-2xl',
      md: 'text-3xl',
      lg: 'text-4xl'
    };

    return `
      <div class="stat-figure text-${this.color}">
        <i class="bi ${this.icon} ${iconSizes[this.size]}"></i>
      </div>
    `;
  }

  /**
   * 更新卡片数值（带动画）
   *
   * @param {number} newValue - 新数值
   * @param {number} duration - 动画时长(ms)
   */
  update(newValue, duration = 1000) {
    const container = this.containerId ? document.getElementById(this.containerId) : null;
    if (!container) {
      console.warn('StatCard: Container not found for update');
      return;
    }

    const valueElement = container.querySelector('[data-stat-value]');
    if (!valueElement) {
      console.warn('StatCard: Value element not found');
      return;
    }

    const oldValue = parseFloat(valueElement.getAttribute('data-stat-value')) || 0;
    this._animateValue(valueElement, oldValue, newValue, duration);

    this.value = newValue;
  }

  /**
   * 数字滚动动画
   *
   * @param {HTMLElement} element - 目标元素
   * @param {number} start - 起始值
   * @param {number} end - 结束值
   * @param {number} duration - 动画时长(ms)
   *
   * @private
   */
  _animateValue(element, start, end, duration) {
    let startTimestamp = null;

    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);

      // 使用easeOutQuart缓动函数
      const easeProgress = 1 - Math.pow(1 - progress, 4);
      const currentValue = Math.floor(easeProgress * (end - start) + start);

      element.textContent = currentValue;
      element.setAttribute('data-stat-value', currentValue);

      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        element.textContent = end;
        element.setAttribute('data-stat-value', end);
      }
    };

    window.requestAnimationFrame(step);
  }

  /**
   * 静态方法：创建基础卡片
   */
  static basic(title, value, color = 'primary') {
    return new StatCard({ title, value, color });
  }

  /**
   * 静态方法：创建带图标卡片
   */
  static withIcon(title, value, icon, color = 'primary') {
    return new StatCard({ title, value, icon, color });
  }

  /**
   * 静态方法：创建带趋势卡片
   */
  static withTrend(title, value, trendValue, direction, color = 'primary') {
    return new StatCard({
      title,
      value,
      trend: { value: trendValue, direction },
      color
    });
  }

  /**
   * 静态方法：创建带进度条卡片
   */
  static withProgress(title, value, progressValue, color = 'primary') {
    return new StatCard({
      title,
      value,
      progress: { value: progressValue },
      color
    });
  }
}

// ES6 模块导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = StatCard;
}
