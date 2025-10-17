/**
 * 筛选栏组件
 *
 * @class FilterBar
 * @description
 * 通用的筛选栏组件，支持搜索、下拉选择、日期范围等多种筛选类型
 *
 * @example
 * const filterBar = new FilterBar({
 *   filters: [
 *     { type: 'search', placeholder: '搜索文件名...' },
 *     { type: 'select', label: '状态', options: ['全部', '执行中', '已完成'] }
 *   ],
 *   onSearch: (values) => console.log(values),
 *   onReset: () => console.log('Reset')
 * });
 * container.innerHTML = filterBar.render();
 */
class FilterBar {
  /**
   * 创建FilterBar实例
   *
   * @param {Object} config - 配置对象
   * @param {Array} config.filters - 筛选项配置
   * @param {Function} config.onSearch - 搜索回调
   * @param {Function} config.onReset - 重置回调
   * @param {string} [config.containerId] - 容器ID
   * @param {boolean} [config.showResetButton] - 是否显示重置按钮（默认true）
   */
  constructor(config) {
    this.filters = config.filters || [];
    this.onSearch = config.onSearch || null;
    this.onReset = config.onReset || null;
    this.containerId = config.containerId || `filter-bar-${Date.now()}`;
    this.showResetButton = config.showResetButton !== false;
    this.values = {};

    // 为每个筛选项生成唯一ID
    this.filters.forEach((filter, index) => {
      filter.id = filter.id || `filter-${this.containerId}-${index}`;
      this.values[filter.id] = filter.defaultValue || '';
    });
  }

  /**
   * 渲染筛选栏HTML
   *
   * @returns {string} HTML字符串
   */
  render() {
    return `
      <div class="card bg-base-100 shadow-md mb-4" id="${this.containerId}">
        <div class="card-body p-4">
          <div class="flex flex-wrap gap-2 items-center">
            ${this._renderFilters()}
            ${this._renderButtons()}
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 渲染筛选项
   * @private
   */
  _renderFilters() {
    return this.filters.map(filter => {
      switch (filter.type) {
        case 'search':
          return this._renderSearchFilter(filter);
        case 'select':
          return this._renderSelectFilter(filter);
        case 'dateRange':
          return this._renderDateRangeFilter(filter);
        case 'custom':
          return this._renderCustomFilter(filter);
        default:
          console.warn(`Unknown filter type: ${filter.type}`);
          return '';
      }
    }).join('');
  }

  /**
   * 渲染搜索框
   * @private
   */
  _renderSearchFilter(filter) {
    const placeholder = filter.placeholder || '搜索...';
    const width = filter.width || 'flex-1 min-w-[200px]';

    return `
      <div class="form-control ${width}">
        <div class="input-group">
          <span class="bg-base-200">
            <i class="bi bi-search"></i>
          </span>
          <input
            type="text"
            id="${filter.id}"
            placeholder="${placeholder}"
            class="input input-bordered input-sm w-full"
            value="${this.values[filter.id] || ''}"
          />
        </div>
      </div>
    `;
  }

  /**
   * 渲染下拉选择
   * @private
   */
  _renderSelectFilter(filter) {
    const label = filter.label || '';
    const options = filter.options || [];
    const width = filter.width || '';

    return `
      <div class="form-control ${width}">
        ${label ? `<label class="label py-0 px-1"><span class="label-text text-xs">${label}</span></label>` : ''}
        <select id="${filter.id}" class="select select-bordered select-sm">
          ${options.map((opt, idx) => {
            const value = typeof opt === 'object' ? opt.value : opt;
            const text = typeof opt === 'object' ? opt.label : opt;
            const selected = this.values[filter.id] === value ? 'selected' : '';
            return `<option value="${value}" ${selected}>${text}</option>`;
          }).join('')}
        </select>
      </div>
    `;
  }

  /**
   * 渲染日期范围选择
   * @private
   */
  _renderDateRangeFilter(filter) {
    const label = filter.label || '日期范围';
    const width = filter.width || '';

    return `
      <div class="form-control ${width}">
        ${label ? `<label class="label py-0 px-1"><span class="label-text text-xs">${label}</span></label>` : ''}
        <div class="flex gap-1 items-center">
          <input
            type="date"
            id="${filter.id}-start"
            class="input input-bordered input-sm w-32"
          />
          <span class="text-xs">至</span>
          <input
            type="date"
            id="${filter.id}-end"
            class="input input-bordered input-sm w-32"
          />
        </div>
      </div>
    `;
  }

  /**
   * 渲染自定义筛选
   * @private
   */
  _renderCustomFilter(filter) {
    if (typeof filter.render === 'function') {
      return filter.render(filter);
    }
    return filter.html || '';
  }

  /**
   * 渲染操作按钮
   * @private
   */
  _renderButtons() {
    return `
      <button class="btn btn-primary btn-sm" onclick="filterBar_${this.containerId}_search()">
        <i class="bi bi-search"></i>
        搜索
      </button>
      ${this.showResetButton ? `
        <button class="btn btn-ghost btn-sm" onclick="filterBar_${this.containerId}_reset()">
          <i class="bi bi-arrow-clockwise"></i>
          重置
        </button>
      ` : ''}
    `;
  }

  /**
   * 获取当前筛选值
   *
   * @returns {Object} 筛选值对象
   */
  getValues() {
    const values = {};

    this.filters.forEach(filter => {
      const element = document.getElementById(filter.id);

      if (!element) {
        return;
      }

      switch (filter.type) {
        case 'search':
        case 'select':
          values[filter.id] = element.value;
          break;

        case 'dateRange':
          const startElement = document.getElementById(`${filter.id}-start`);
          const endElement = document.getElementById(`${filter.id}-end`);
          values[filter.id] = {
            start: startElement ? startElement.value : '',
            end: endElement ? endElement.value : ''
          };
          break;

        case 'custom':
          if (filter.getValue) {
            values[filter.id] = filter.getValue(filter);
          }
          break;
      }
    });

    return values;
  }

  /**
   * 设置筛选值
   *
   * @param {Object} values - 筛选值对象
   */
  setValues(values) {
    Object.keys(values).forEach(id => {
      const filter = this.filters.find(f => f.id === id);
      if (!filter) return;

      const element = document.getElementById(id);
      if (!element) return;

      switch (filter.type) {
        case 'search':
        case 'select':
          element.value = values[id];
          break;

        case 'dateRange':
          if (values[id].start) {
            const startElement = document.getElementById(`${id}-start`);
            if (startElement) startElement.value = values[id].start;
          }
          if (values[id].end) {
            const endElement = document.getElementById(`${id}-end`);
            if (endElement) endElement.value = values[id].end;
          }
          break;

        case 'custom':
          if (filter.setValue) {
            filter.setValue(filter, values[id]);
          }
          break;
      }
    });

    this.values = values;
  }

  /**
   * 重置筛选
   */
  reset() {
    this.filters.forEach(filter => {
      const defaultValue = filter.defaultValue || '';
      const element = document.getElementById(filter.id);

      if (!element) return;

      switch (filter.type) {
        case 'search':
          element.value = '';
          break;

        case 'select':
          element.selectedIndex = 0;
          break;

        case 'dateRange':
          const startElement = document.getElementById(`${filter.id}-start`);
          const endElement = document.getElementById(`${filter.id}-end`);
          if (startElement) startElement.value = '';
          if (endElement) endElement.value = '';
          break;

        case 'custom':
          if (filter.reset) {
            filter.reset(filter);
          }
          break;
      }

      this.values[filter.id] = defaultValue;
    });

    if (this.onReset) {
      this.onReset();
    }
  }

  /**
   * 执行搜索
   */
  search() {
    const values = this.getValues();
    this.values = values;

    if (this.onSearch) {
      this.onSearch(values);
    }
  }

  /**
   * 初始化（绑定事件）
   * 在render()后调用
   */
  init() {
    // 创建全局搜索和重置函数
    window[`filterBar_${this.containerId}_search`] = () => this.search();
    window[`filterBar_${this.containerId}_reset`] = () => this.reset();

    // 绑定回车搜索
    this.filters.forEach(filter => {
      if (filter.type === 'search') {
        const element = document.getElementById(filter.id);
        if (element) {
          element.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
              this.search();
            }
          });
        }
      }
    });
  }

  /**
   * 销毁（清理全局函数）
   */
  destroy() {
    delete window[`filterBar_${this.containerId}_search`];
    delete window[`filterBar_${this.containerId}_reset`];
  }
}

// ES6 模块导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FilterBar;
}
