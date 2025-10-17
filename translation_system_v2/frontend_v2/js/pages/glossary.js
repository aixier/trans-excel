/**
 * Glossary Page - 术语库管理页面
 * 负责术语库的CRUD操作、导入导出、搜索筛选
 *
 * @author Engineer C
 * @date 2025-10-17
 */

class GlossaryPage {
  constructor() {
    this.glossaries = [];
    this.currentGlossaryId = null;
    this.terms = [];
    this.termSearcher = null;
    this.dataTable = null;
  }

  /**
   * 初始化页面
   */
  async init() {
    console.log('[GlossaryPage] Initializing...');
    console.log('[GlossaryPage] Checking window.ensureAPIReady:', typeof window.ensureAPIReady);
    console.log('[GlossaryPage] Checking window.api:', typeof window.api);

    try {
      // 确保API已初始化
      await window.ensureAPIReady();

      // 加载术语库列表
      await this.loadGlossaries();

      // 渲染页面布局
      this.render();

      // 如果有术语库，选择第一个
      if (this.glossaries.length > 0) {
        await this.selectGlossary(this.glossaries[0].id);
      }
    } catch (error) {
      console.error('[GlossaryPage] Init failed:', error);
      this.showError('初始化失败', error.message);
    }
  }

  /**
   * 从后端加载术语库列表
   */
  async loadGlossaries() {
    try {
      this.glossaries = await window.api.getGlossaries();

      console.log('[GlossaryPage] Loaded glossaries:', this.glossaries.length);
    } catch (error) {
      console.error('[GlossaryPage] Failed to load glossaries:', error);
      throw error;
    }
  }

  /**
   * 选择术语库
   * @param {string} glossaryId - 术语库ID
   */
  async selectGlossary(glossaryId) {
    console.log('[GlossaryPage] Selecting glossary:', glossaryId);

    this.currentGlossaryId = glossaryId;

    // 加载术语
    await this.loadTerms(glossaryId);

    // 重新渲染
    this.renderGlossaryList();
    this.renderTermSection();
  }

  /**
   * 加载术语列表
   * @param {string} glossaryId - 术语库ID
   */
  async loadTerms(glossaryId) {
    try {
      const response = await window.api.getTerms(glossaryId);
      this.terms = response.terms || response;

      console.log('[GlossaryPage] Loaded terms:', this.terms.length);
    } catch (error) {
      console.error('[GlossaryPage] Failed to load terms:', error);
      throw error;
    }
  }

  /**
   * 渲染页面主结构
   */
  render() {
    const container = document.getElementById('app');

    container.innerHTML = `
      <div class="container mx-auto p-6">
        <!-- 页面标题 -->
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-3xl font-bold flex items-center gap-2">
            <i class="bi bi-book"></i>
            术语库管理
          </h1>
        </div>

        <!-- 左右分栏布局 -->
        <div class="grid grid-cols-12 gap-6">
          <!-- 左侧：术语库列表 -->
          <div class="col-span-3">
            <div id="glossaryListContainer"></div>
          </div>

          <!-- 右侧：术语条目 -->
          <div class="col-span-9">
            <div id="termSectionContainer"></div>
          </div>
        </div>
      </div>
    `;

    // 渲染术语库列表
    this.renderGlossaryList();

    // 渲染术语区域
    this.renderTermSection();
  }

  /**
   * 渲染术语库列表
   */
  renderGlossaryList() {
    const container = document.getElementById('glossaryListContainer');

    if (!container) return;

    const listHtml = this.glossaries.map(glossary => {
      const isActive = glossary.id === this.currentGlossaryId;

      return `
        <div
          class="p-4 cursor-pointer hover:bg-base-200 rounded-lg transition-colors ${
            isActive ? 'bg-base-200 border-l-4 border-primary' : ''
          }"
          onclick="glossaryPage.selectGlossary('${glossary.id}')"
        >
          <div class="flex items-center gap-2 mb-1">
            <span class="text-lg">${glossary.active ? '●' : '○'}</span>
            <span class="font-semibold">${glossary.name}</span>
          </div>
          <div class="text-sm text-base-content/60 ml-6">
            ${glossary.termCount} 条术语
            ${glossary.active ? '· <span class="text-success">激活中</span>' : ''}
          </div>
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body p-4">
          <button class="btn btn-primary btn-sm mb-4 w-full" onclick="glossaryPage.createGlossary()">
            <i class="bi bi-plus-circle"></i>
            新建术语库
          </button>
          <div class="space-y-2">
            ${listHtml}
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 渲染术语区域
   */
  renderTermSection() {
    const container = document.getElementById('termSectionContainer');

    if (!container) return;

    // 如果没有选中术语库，显示空状态
    if (!this.currentGlossaryId) {
      container.innerHTML = this.renderEmptyState(
        'first-time',
        '请选择或创建术语库',
        '点击左侧术语库或新建一个'
      );
      return;
    }

    const glossary = this.glossaries.find(g => g.id === this.currentGlossaryId);

    container.innerHTML = `
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <!-- 表格头部 -->
          ${this.renderTableHeader(glossary)}

          <!-- 搜索栏 -->
          ${this.renderSearchBar()}

          <!-- 术语表格 -->
          <div id="termTableContainer" class="mt-4"></div>
        </div>
      </div>
    `;

    // 渲染术语表格
    this.renderTermTable();
  }

  /**
   * 渲染表格头部
   * @param {Object} glossary - 术语库对象
   */
  renderTableHeader(glossary) {
    if (!glossary) return '';

    return `
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-xl font-bold">${glossary.name}</h2>
          <p class="text-sm text-base-content/60">${glossary.termCount} 条术语</p>
        </div>
        <div class="flex gap-2">
          <!-- 导入下拉菜单 -->
          <div class="dropdown dropdown-end">
            <button class="btn btn-sm btn-ghost">
              <i class="bi bi-download"></i> 导入
            </button>
            <ul class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
              <li><a onclick="glossaryPage.importFromExcel()">
                <i class="bi bi-file-earmark-excel"></i> 从Excel导入
              </a></li>
              <li><a onclick="glossaryPage.importFromCSV()">
                <i class="bi bi-filetype-csv"></i> 从CSV导入
              </a></li>
            </ul>
          </div>

          <!-- 导出按钮 -->
          <button class="btn btn-sm btn-ghost" onclick="glossaryPage.exportGlossary()">
            <i class="bi bi-upload"></i> 导出
          </button>

          <!-- 新增术语按钮 -->
          <button class="btn btn-sm btn-primary" onclick="glossaryPage.createTerm()">
            <i class="bi bi-plus"></i> 新增术语
          </button>
        </div>
      </div>
    `;
  }

  /**
   * 渲染搜索栏
   */
  renderSearchBar() {
    return `
      <div class="flex gap-2 mb-4">
        <div class="form-control flex-1">
          <div class="input-group">
            <span><i class="bi bi-search"></i></span>
            <input
              type="text"
              placeholder="搜索术语..."
              class="input input-bordered input-sm w-full"
              id="termSearchInput"
              oninput="glossaryPage.handleSearch(this.value)"
            />
          </div>
        </div>
        <select
          class="select select-bordered select-sm"
          id="langFilterSelect"
          onchange="glossaryPage.handleLangFilter(this.value)"
        >
          <option value="all">全部语言</option>
          <option value="EN">English</option>
          <option value="JP">日本語</option>
          <option value="TH">ไทย</option>
          <option value="PT">Português</option>
        </select>
      </div>
    `;
  }

  /**
   * 渲染术语表格
   */
  renderTermTable() {
    const container = document.getElementById('termTableContainer');

    if (!container) return;

    // 如果没有术语，显示空状态
    if (this.terms.length === 0) {
      container.innerHTML = this.renderEmptyState(
        'no-data',
        '暂无术语',
        '点击"新增术语"按钮添加第一条术语'
      );
      return;
    }

    // 使用原生表格实现（TODO: 后续可替换为DataTable组件）
    const tableHtml = `
      <div class="overflow-x-auto">
        <table class="table table-zebra w-full">
          <thead>
            <tr>
              <th>源术语</th>
              <th>English</th>
              <th>日本語</th>
              <th>ไทย</th>
              <th>Português</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            ${this.terms.map(term => this.renderTermRow(term)).join('')}
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="flex justify-center mt-4">
        <div class="btn-group">
          <button class="btn btn-sm">«</button>
          <button class="btn btn-sm btn-active">1</button>
          <button class="btn btn-sm">2</button>
          <button class="btn btn-sm">3</button>
          <button class="btn btn-sm">»</button>
        </div>
      </div>
    `;

    container.innerHTML = tableHtml;
  }

  /**
   * 渲染术语行
   * @param {Object} term - 术语对象
   */
  renderTermRow(term) {
    return `
      <tr class="hover">
        <td><span class="font-medium">${term.source}</span></td>
        <td>${term.translations.EN || '-'}</td>
        <td>${term.translations.JP || '-'}</td>
        <td>${term.translations.TH || '-'}</td>
        <td>${term.translations.PT || '-'}</td>
        <td>
          <div class="flex gap-1">
            <button
              class="btn btn-xs btn-ghost"
              onclick="glossaryPage.editTerm('${term.id}')"
              title="编辑"
            >
              <i class="bi bi-pencil"></i>
            </button>
            <button
              class="btn btn-xs btn-ghost text-error"
              onclick="glossaryPage.deleteTerm('${term.id}')"
              title="删除"
            >
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }

  /**
   * 渲染空状态
   * @param {string} type - 类型：first-time | no-data | no-results
   * @param {string} title - 标题
   * @param {string} message - 消息
   */
  renderEmptyState(type, title, message) {
    const icons = {
      'first-time': 'bi-inbox',
      'no-data': 'bi-file-earmark-text',
      'no-results': 'bi-search'
    };

    return `
      <div class="flex flex-col items-center justify-center py-16">
        <i class="${icons[type] || 'bi-inbox'} text-6xl text-base-content/30"></i>
        <h3 class="text-xl font-semibold mt-4">${title}</h3>
        <p class="text-base-content/60 mt-2">${message}</p>
      </div>
    `;
  }

  /**
   * 处理搜索
   * @param {string} searchText - 搜索文本
   */
  async handleSearch(searchText) {
    console.log('[GlossaryPage] Search:', searchText);

    if (!this.currentGlossaryId) return;

    try {
      const response = await window.api.getTerms(this.currentGlossaryId, 1, 20);
      let terms = response.terms || response;

      if (searchText && searchText.trim()) {
        const searchLower = searchText.toLowerCase();
        terms = terms.filter(term =>
          term.source?.toLowerCase().includes(searchLower) ||
          Object.values(term.translations || {}).some(val =>
            val?.toLowerCase().includes(searchLower)
          )
        );
      }

      this.terms = terms;
      this.renderTermTable();
    } catch (error) {
      console.error('[GlossaryPage] Search failed:', error);
    }
  }

  /**
   * 处理语言筛选
   * @param {string} lang - 语言代码
   */
  async handleLangFilter(lang) {
    console.log('[GlossaryPage] Filter by lang:', lang);

    if (!this.currentGlossaryId) return;

    try {
      const response = await window.api.getTerms(this.currentGlossaryId, 1, 20);
      let terms = response.terms || response;

      if (lang !== 'all') {
        terms = terms.filter(term => term.translations && term.translations[lang]);
      }

      this.terms = terms;
      this.renderTermTable();
    } catch (error) {
      console.error('[GlossaryPage] Filter failed:', error);
    }
  }

  /**
   * 新建术语库
   */
  async createGlossary() {
    console.log('[GlossaryPage] Create glossary');

    const name = prompt('请输入术语库名称：');

    if (!name || !name.trim()) {
      return;
    }

    try {
      const newGlossary = await window.api.createGlossary({
        name: name.trim(),
        description: '',
        active: false
      });

      this.glossaries.push(newGlossary);

      this.renderGlossaryList();
      await this.selectGlossary(newGlossary.id);

      this.showSuccess('术语库创建成功');
    } catch (error) {
      console.error('[GlossaryPage] Failed to create glossary:', error);
      this.showError('创建失败', error.message);
    }
  }

  /**
   * 新增术语
   */
  createTerm() {
    console.log('[GlossaryPage] Create term');
    // TODO: 显示术语编辑Modal
    alert('新增术语功能开发中...');
  }

  /**
   * 编辑术语
   * @param {string} termId - 术语ID
   */
  editTerm(termId) {
    console.log('[GlossaryPage] Edit term:', termId);
    // TODO: 显示术语编辑Modal
    alert('编辑术语功能开发中...');
  }

  /**
   * 删除术语
   * @param {string} termId - 术语ID
   */
  async deleteTerm(termId) {
    console.log('[GlossaryPage] Delete term:', termId);

    const confirmed = confirm('确定要删除这条术语吗？');

    if (!confirmed) {
      return;
    }

    try {
      await window.api.delete(`/api/glossaries/${this.currentGlossaryId}/terms/${termId}`);

      this.terms = this.terms.filter(t => t.id !== termId);

      this.renderTermTable();

      this.showSuccess('删除成功');
    } catch (error) {
      console.error('[GlossaryPage] Failed to delete term:', error);
      this.showError('删除失败', error.message);
    }
  }

  /**
   * 从Excel导入
   */
  importFromExcel() {
    console.log('[GlossaryPage] Import from Excel');
    // TODO: 实现Excel导入功能
    alert('Excel导入功能开发中...');
  }

  /**
   * 从CSV导入
   */
  importFromCSV() {
    console.log('[GlossaryPage] Import from CSV');
    // TODO: 实现CSV导入功能
    alert('CSV导入功能开发中...');
  }

  /**
   * 导出术语库
   */
  exportGlossary() {
    console.log('[GlossaryPage] Export glossary');

    if (this.terms.length === 0) {
      this.showWarning('没有术语可导出');
      return;
    }

    // TODO: 实现Excel导出功能
    alert('导出功能开发中...');
  }

  /**
   * 显示成功消息
   * @param {string} message - 消息内容
   */
  showSuccess(message) {
    console.log('[GlossaryPage] Success:', message);
    // TODO: 使用Toast组件
    alert(message);
  }

  /**
   * 显示警告消息
   * @param {string} message - 消息内容
   */
  showWarning(message) {
    console.log('[GlossaryPage] Warning:', message);
    // TODO: 使用Toast组件
    alert(message);
  }

  /**
   * 显示错误消息
   * @param {string} title - 标题
   * @param {string} message - 消息内容
   */
  showError(title, message) {
    console.error('[GlossaryPage] Error:', title, message);
    alert(`${title}: ${message}`);
  }
}

// 创建全局实例（由app.js的Router调用init）
let glossaryPage;
