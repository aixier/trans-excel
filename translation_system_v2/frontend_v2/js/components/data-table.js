/**
 * 数据表格组件
 *
 * @class DataTable
 * @description
 * 功能完整的数据表格，支持全选/单选、排序、分页、行操作
 *
 * @example
 * const table = new DataTable({
 *   columns: [
 *     { key: 'filename', label: '文件名', sortable: true },
 *     { key: 'status', label: '状态', render: (val) => `<span class="badge">${val}</span>` }
 *   ],
 *   data: sessions,
 *   selectable: true,
 *   pagination: { pageSize: 10 }
 * });
 * container.innerHTML = table.render();
 */
class DataTable {
  /**
   * 创建DataTable实例
   *
   * @param {Object} config - 配置对象
   * @param {Array} config.columns - 列配置
   * @param {Array} config.data - 数据数组
   * @param {boolean} [config.selectable] - 是否可选（默认false）
   * @param {boolean} [config.sortable] - 是否可排序（默认false）
   * @param {Object} [config.pagination] - 分页配置
   * @param {Function} [config.onRowClick] - 行点击回调
   * @param {Function} [config.onSelectionChange] - 选择变化回调
   * @param {string} [config.containerId] - 容器ID
   * @param {boolean} [config.striped] - 是否斑马纹（默认true）
   * @param {boolean} [config.hover] - 是否悬浮效果（默认true）
   */
  constructor(config) {
    this.columns = config.columns || [];
    this.data = config.data || [];
    this.selectable = config.selectable || false;
    this.sortable = config.sortable || false;
    this.pagination = config.pagination || null;
    this.onRowClick = config.onRowClick || null;
    this.onSelectionChange = config.onSelectionChange || null;
    this.containerId = config.containerId || `data-table-${Date.now()}`;
    this.striped = config.striped !== false;
    this.hover = config.hover !== false;

    // 内部状态
    this.selectedRows = new Set();
    this.sortColumn = null;
    this.sortDirection = 'asc';
    this.currentPage = 1;
    this.pageSize = this.pagination ? (this.pagination.pageSize || 10) : this.data.length;
  }

  /**
   * 渲染表格HTML
   *
   * @returns {string} HTML字符串
   */
  render() {
    const displayData = this._getDisplayData();

    return `
      <div id="${this.containerId}">
        <div class="overflow-x-auto">
          <table class="table w-full ${this.striped ? 'table-zebra' : ''} ${this.hover ? 'table-hover' : ''}">
            ${this._renderHeader()}
            ${this._renderBody(displayData)}
          </table>
        </div>
        ${this.pagination ? this._renderPagination() : ''}
      </div>
    `;
  }

  /**
   * 渲染表头
   * @private
   */
  _renderHeader() {
    return `
      <thead>
        <tr>
          ${this.selectable ? this._renderSelectAllCell() : ''}
          ${this.columns.map(col => this._renderHeaderCell(col)).join('')}
        </tr>
      </thead>
    `;
  }

  /**
   * 渲染全选单元格
   * @private
   */
  _renderSelectAllCell() {
    const allSelected = this.selectedRows.size === this.data.length && this.data.length > 0;
    return `
      <th class="w-12">
        <input
          type="checkbox"
          class="checkbox checkbox-sm"
          id="${this.containerId}-select-all"
          ${allSelected ? 'checked' : ''}
          onchange="dataTable_${this.containerId}_toggleAll(this.checked)"
        />
      </th>
    `;
  }

  /**
   * 渲染表头单元格
   * @private
   */
  _renderHeaderCell(column) {
    const isSortable = this.sortable && column.sortable !== false;
    const isSorted = this.sortColumn === column.key;
    const sortIcon = isSorted ? (this.sortDirection === 'asc' ? 'bi-arrow-up' : 'bi-arrow-down') : 'bi-arrow-down-up';

    const width = column.width ? `style="width: ${column.width}"` : '';
    const align = column.align || 'left';

    return `
      <th ${width} class="text-${align}">
        <div class="flex items-center gap-1 ${isSortable ? 'cursor-pointer' : ''}"
             ${isSortable ? `onclick="dataTable_${this.containerId}_sort('${column.key}')"` : ''}>
          ${column.label}
          ${isSortable ? `<i class="bi ${sortIcon} text-xs ${isSorted ? 'text-primary' : 'text-base-content/40'}"></i>` : ''}
        </div>
      </th>
    `;
  }

  /**
   * 渲染表体
   * @private
   */
  _renderBody(displayData) {
    if (displayData.length === 0) {
      return this._renderEmptyState();
    }

    return `
      <tbody>
        ${displayData.map((row, index) => this._renderRow(row, index)).join('')}
      </tbody>
    `;
  }

  /**
   * 渲染行
   * @private
   */
  _renderRow(row, index) {
    const isSelected = this.selectedRows.has(index);
    const clickHandler = this.onRowClick ? `onclick="dataTable_${this.containerId}_rowClick(${index})"` : '';

    return `
      <tr class="${this.onRowClick ? 'cursor-pointer' : ''}" ${clickHandler}>
        ${this.selectable ? this._renderSelectCell(row, index, isSelected) : ''}
        ${this.columns.map(col => this._renderCell(row, col)).join('')}
      </tr>
    `;
  }

  /**
   * 渲染选择单元格
   * @private
   */
  _renderSelectCell(row, index, isSelected) {
    return `
      <td>
        <input
          type="checkbox"
          class="checkbox checkbox-sm"
          ${isSelected ? 'checked' : ''}
          onchange="dataTable_${this.containerId}_toggleRow(${index}, this.checked)"
          onclick="event.stopPropagation()"
        />
      </td>
    `;
  }

  /**
   * 渲染单元格
   * @private
   */
  _renderCell(row, column) {
    const value = this._getCellValue(row, column.key);
    const align = column.align || 'left';

    let content;
    if (column.render && typeof column.render === 'function') {
      content = column.render(value, row);
    } else {
      content = value ?? '-';
    }

    return `<td class="text-${align}">${content}</td>`;
  }

  /**
   * 渲染空状态
   * @private
   */
  _renderEmptyState() {
    const colspan = this.columns.length + (this.selectable ? 1 : 0);
    return `
      <tbody>
        <tr>
          <td colspan="${colspan}" class="text-center py-8">
            <div class="flex flex-col items-center text-base-content/40">
              <i class="bi bi-inbox text-4xl mb-2"></i>
              <p>暂无数据</p>
            </div>
          </td>
        </tr>
      </tbody>
    `;
  }

  /**
   * 渲染分页
   * @private
   */
  _renderPagination() {
    const totalPages = Math.ceil(this.data.length / this.pageSize);
    if (totalPages <= 1) return '';

    const maxButtons = 5;
    const startPage = Math.max(1, this.currentPage - Math.floor(maxButtons / 2));
    const endPage = Math.min(totalPages, startPage + maxButtons - 1);

    const pages = [];
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    return `
      <div class="flex justify-center items-center gap-2 mt-4">
        <button
          class="btn btn-sm ${this.currentPage === 1 ? 'btn-disabled' : ''}"
          onclick="dataTable_${this.containerId}_goToPage(${this.currentPage - 1})"
          ${this.currentPage === 1 ? 'disabled' : ''}
        >
          <i class="bi bi-chevron-left"></i>
        </button>

        <div class="btn-group">
          ${pages.map(page => `
            <button
              class="btn btn-sm ${page === this.currentPage ? 'btn-active' : ''}"
              onclick="dataTable_${this.containerId}_goToPage(${page})"
            >
              ${page}
            </button>
          `).join('')}
        </div>

        <button
          class="btn btn-sm ${this.currentPage === totalPages ? 'btn-disabled' : ''}"
          onclick="dataTable_${this.containerId}_goToPage(${this.currentPage + 1})"
          ${this.currentPage === totalPages ? 'disabled' : ''}
        >
          <i class="bi bi-chevron-right"></i>
        </button>

        <span class="text-sm text-base-content/60 ml-2">
          共 ${totalPages} 页 / ${this.data.length} 条
        </span>
      </div>
    `;
  }

  /**
   * 获取单元格值
   * @private
   */
  _getCellValue(row, key) {
    if (key.includes('.')) {
      // 支持嵌套属性 如 'user.name'
      return key.split('.').reduce((obj, k) => obj?.[k], row);
    }
    return row[key];
  }

  /**
   * 获取显示数据（应用排序和分页）
   * @private
   */
  _getDisplayData() {
    let data = [...this.data];

    // 排序
    if (this.sortColumn) {
      data.sort((a, b) => {
        const aVal = this._getCellValue(a, this.sortColumn);
        const bVal = this._getCellValue(b, this.sortColumn);

        let result = 0;
        if (aVal < bVal) result = -1;
        if (aVal > bVal) result = 1;

        return this.sortDirection === 'asc' ? result : -result;
      });
    }

    // 分页
    if (this.pagination) {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      data = data.slice(start, end);
    }

    return data;
  }

  /**
   * 更新数据
   *
   * @param {Array} newData - 新数据
   */
  updateData(newData) {
    this.data = newData;
    this.selectedRows.clear();
    this.currentPage = 1;
    this._refresh();
  }

  /**
   * 获取选中的行
   *
   * @returns {Array} 选中的行数据
   */
  getSelectedRows() {
    return Array.from(this.selectedRows).map(index => this.data[index]);
  }

  /**
   * 排序
   *
   * @param {string} columnKey - 列键
   */
  sort(columnKey) {
    if (this.sortColumn === columnKey) {
      // 切换排序方向
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortColumn = columnKey;
      this.sortDirection = 'asc';
    }
    this._refresh();
  }

  /**
   * 跳转到指定页
   *
   * @param {number} page - 页码
   */
  goToPage(page) {
    const totalPages = Math.ceil(this.data.length / this.pageSize);
    if (page < 1 || page > totalPages) return;

    this.currentPage = page;
    this._refresh();
  }

  /**
   * 切换行选择
   *
   * @param {number} index - 行索引
   * @param {boolean} checked - 是否选中
   */
  toggleRow(index, checked) {
    if (checked) {
      this.selectedRows.add(index);
    } else {
      this.selectedRows.delete(index);
    }

    if (this.onSelectionChange) {
      this.onSelectionChange(this.getSelectedRows());
    }

    this._updateSelectAllCheckbox();
  }

  /**
   * 切换全选
   *
   * @param {boolean} checked - 是否全选
   */
  toggleAll(checked) {
    if (checked) {
      this.data.forEach((_, index) => this.selectedRows.add(index));
    } else {
      this.selectedRows.clear();
    }

    if (this.onSelectionChange) {
      this.onSelectionChange(this.getSelectedRows());
    }

    this._refresh();
  }

  /**
   * 行点击
   *
   * @param {number} index - 行索引
   */
  rowClick(index) {
    if (this.onRowClick) {
      this.onRowClick(this.data[index], index);
    }
  }

  /**
   * 更新全选复选框状态
   * @private
   */
  _updateSelectAllCheckbox() {
    const checkbox = document.getElementById(`${this.containerId}-select-all`);
    if (checkbox) {
      checkbox.checked = this.selectedRows.size === this.data.length && this.data.length > 0;
    }
  }

  /**
   * 刷新表格
   * @private
   */
  _refresh() {
    const container = document.getElementById(this.containerId);
    if (container) {
      container.outerHTML = this.render();
      this.init();
    }
  }

  /**
   * 初始化（绑定事件）
   * 在render()后调用
   */
  init() {
    // 创建全局函数
    window[`dataTable_${this.containerId}_sort`] = (key) => this.sort(key);
    window[`dataTable_${this.containerId}_goToPage`] = (page) => this.goToPage(page);
    window[`dataTable_${this.containerId}_toggleRow`] = (index, checked) => this.toggleRow(index, checked);
    window[`dataTable_${this.containerId}_toggleAll`] = (checked) => this.toggleAll(checked);
    window[`dataTable_${this.containerId}_rowClick`] = (index) => this.rowClick(index);
  }

  /**
   * 销毁（清理全局函数）
   */
  destroy() {
    delete window[`dataTable_${this.containerId}_sort`];
    delete window[`dataTable_${this.containerId}_goToPage`];
    delete window[`dataTable_${this.containerId}_toggleRow`];
    delete window[`dataTable_${this.containerId}_toggleAll`];
    delete window[`dataTable_${this.containerId}_rowClick`];
  }
}

// ES6 模块导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DataTable;
}
