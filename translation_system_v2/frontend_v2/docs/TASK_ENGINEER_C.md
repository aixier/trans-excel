# 工程师C - 术语库管理 + 数据分析开发任务

> **角色**: 数据功能开发工程师
> **工期**: Week 2-4
> **工作量**: 14天（112小时）
> **依赖**: 等待工程师A完成组件库（Week 2）

---

## 🎯 任务目标

### 核心目标

1. **Week 2-3**: 开发术语库管理功能（CRUD + 导入导出）
2. **Week 3-4**: 开发数据分析功能（统计 + 图表可视化）
3. **Week 4**: 功能完善、Bug修复、集成测试

### 成功标准

- ✅ 术语库可以增删改查，支持搜索和筛选
- ✅ 术语可以通过Excel导入导出
- ✅ 数据分析展示完整的统计数据
- ✅ 图表可视化清晰美观
- ✅ 所有功能符合设计规范和需求文档

---

## 📋 详细任务清单

### Week 1: 准备阶段

#### 1.1 环境搭建和学习 (1天)

**任务**:
- [ ] 克隆代码仓库，搭建开发环境
- [ ] 阅读必读文档（见下方参考文档清单）
- [ ] 理解术语库数据结构
- [ ] 学习Chart.js基础（用于数据分析）
- [ ] 等待工程师A完成基础架构（Week 1结束）

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 术语库管理、数据分析
- `docs/design/UI_DESIGN.md` - Glossary、Analytics页面原型
- Chart.js官方文档

---

### Week 2: 术语库管理开发（Part 1）

#### 2.1 术语库列表 (1.5天)

**目标**: 实现左右分栏布局，左侧术语库列表，右侧术语条目

**任务**:
- [ ] 创建glossary.js页面逻辑
  ```javascript
  // 文件: js/pages/glossary.js
  class GlossaryPage {
    constructor() {
      this.glossaries = [];
      this.currentGlossaryId = null;
      this.terms = [];
    }

    async init() {
      await this.loadGlossaries();
      this.renderGlossaryList();
      if (this.glossaries.length > 0) {
        await this.selectGlossary(this.glossaries[0].id);
      }
    }

    async loadGlossaries() {
      // 从API或LocalStorage加载术语库列表
      this.glossaries = await api.getGlossaries();
    }

    async selectGlossary(glossaryId) {
      this.currentGlossaryId = glossaryId;
      await this.loadTerms(glossaryId);
      this.renderTermTable();
    }

    async loadTerms(glossaryId) {
      this.terms = await api.getTerms(glossaryId);
    }
  }
  ```

- [ ] 实现术语库列表渲染
  ```javascript
  renderGlossaryList() {
    const listHtml = this.glossaries.map(glossary => `
      <div class="p-4 cursor-pointer hover:bg-base-200 ${
        glossary.id === this.currentGlossaryId ? 'bg-base-200' : ''
      }"
      onclick="glossaryPage.selectGlossary('${glossary.id}')">
        <div class="flex items-center gap-2">
          ${glossary.active ? '●' : '○'}
          <span class="font-medium">${glossary.name}</span>
        </div>
        <div class="text-sm text-base-content/60">
          ${glossary.termCount} 条
          ${glossary.active ? '✓ 激活中' : ''}
        </div>
      </div>
    `).join('');

    document.getElementById('glossaryList').innerHTML = `
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body p-4">
          <button class="btn btn-primary btn-sm mb-2" onclick="glossaryPage.createGlossary()">
            <i class="bi bi-plus"></i> 新建术语库
          </button>
          <div class="space-y-2">
            ${listHtml}
          </div>
        </div>
      </div>
    `;
  }
  ```

- [ ] 实现新建术语库
  ```javascript
  async createGlossary() {
    const name = await UIHelper.showPrompt('请输入术语库名称');
    if (!name) return;

    try {
      UIHelper.showLoading(true);

      const result = await api.createGlossary({
        name: name,
        description: '',
        terms: []
      });

      await this.loadGlossaries();
      await this.selectGlossary(result.id);

      UIHelper.showToast('术语库创建成功', 'success');
    } catch (error) {
      UIHelper.showToast(`创建失败: ${error.message}`, 'error');
    } finally {
      UIHelper.showLoading(false);
    }
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 术语库管理 - 术语库列表（249-267行）
- `docs/technical/FEATURE_SPEC.md` - 术语库管理 - createGlossary（645-679行）

**交付标准**:
- 左侧显示术语库列表
- 点击术语库可以切换
- 可以新建术语库

---

#### 2.2 术语条目表格 (2天)

**目标**: 使用DataTable组件展示术语条目

**任务**:
- [ ] 使用DataTable组件渲染术语表格
  ```javascript
  renderTermTable() {
    if (!this.currentGlossaryId) {
      document.getElementById('termTable').innerHTML = `
        ${EmptyState.render({
          type: 'first-time',
          title: '请选择或创建术语库',
          message: '点击左侧术语库或新建一个'
        })}
      `;
      return;
    }

    const table = new DataTable({
      columns: [
        {
          key: 'source',
          label: '源术语',
          sortable: true
        },
        {
          key: 'translations.EN',
          label: 'English',
          render: (val) => val || '-'
        },
        {
          key: 'translations.JP',
          label: '日本語',
          render: (val) => val || '-'
        },
        {
          key: 'translations.TH',
          label: 'ไทย',
          render: (val) => val || '-'
        },
        {
          key: 'actions',
          label: '操作',
          render: (val, row) => `
            <button class="btn btn-xs btn-ghost" onclick="glossaryPage.editTerm('${row.id}')">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-xs btn-ghost text-error" onclick="glossaryPage.deleteTerm('${row.id}')">
              <i class="bi bi-trash"></i>
            </button>
          `
        }
      ],
      data: this.terms,
      selectable: true,
      sortable: true,
      pagination: { pageSize: 20 }
    });

    document.getElementById('termTable').innerHTML = table.render();
  }
  ```

- [ ] 实现表格头部（搜索+操作）
  ```javascript
  renderTableHeader() {
    const glossary = this.glossaries.find(g => g.id === this.currentGlossaryId);
    if (!glossary) return '';

    return `
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-xl font-bold">${glossary.name}</h2>
          <p class="text-sm text-base-content/60">${glossary.termCount} 条术语</p>
        </div>
        <div class="flex gap-2">
          <div class="dropdown dropdown-end">
            <button class="btn btn-sm btn-ghost">
              <i class="bi bi-download"></i> 导入
            </button>
            <ul class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
              <li><a onclick="glossaryPage.importFromExcel()">从Excel导入</a></li>
              <li><a onclick="glossaryPage.importFromCSV()">从CSV导入</a></li>
            </ul>
          </div>
          <button class="btn btn-sm btn-ghost" onclick="glossaryPage.exportGlossary()">
            <i class="bi bi-upload"></i> 导出
          </button>
          <button class="btn btn-sm btn-primary" onclick="glossaryPage.createTerm()">
            <i class="bi bi-plus"></i> 新增术语
          </button>
        </div>
      </div>
    `;
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 术语库管理 - 术语库列表（269-277行）
- `docs/design/UI_DESIGN.md` - 术语库管理（451-478行）

**交付标准**:
- 术语表格正确显示
- 支持排序和分页
- 表格头部操作按钮正常

---

#### 2.3 术语搜索和筛选 (1.5天)

**目标**: 实现术语搜索功能

**任务**:
- [ ] 创建TermSearcher类
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
      this.allTerms = await api.getTerms(this.glossaryId);
      this.filteredTerms = [...this.allTerms];
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
            t && t.toLowerCase().includes(this.searchText)
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
    }

    getResults() {
      return this.filteredTerms;
    }
  }
  ```

- [ ] 添加搜索框
  ```javascript
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
              oninput="termSearcher.search(this.value)"
            />
          </div>
        </div>
        <select class="select select-bordered select-sm" onchange="termSearcher.filterByLanguage(this.value)">
          <option value="all">全部语言</option>
          <option value="EN">English</option>
          <option value="JP">日本語</option>
          <option value="TH">ไทย</option>
          <option value="PT">Português</option>
        </select>
      </div>
    `;
  }
  ```

**参考文档**:
- `docs/technical/FEATURE_SPEC.md` - 术语库管理 - TermSearcher（786-899行）

**交付标准**:
- 可以搜索源术语和译文
- 可以按语言筛选
- 搜索结果实时更新

---

### Week 3: 术语库管理开发（Part 2）

#### 3.1 术语CRUD (2天)

**目标**: 实现术语的新增、编辑、删除

**任务**:
- [ ] 实现术语编辑Modal
  ```javascript
  async editTerm(termId) {
    const term = this.terms.find(t => t.id === termId);
    if (!term) return;

    const modalHtml = `
      <div class="modal modal-open">
        <div class="modal-box w-11/12 max-w-3xl">
          <h3 class="font-bold text-lg mb-4">
            <i class="bi bi-pencil"></i>
            ${termId ? '编辑术语' : '新增术语'}
          </h3>

          <div class="grid grid-cols-1 gap-4">
            <!-- 源术语 -->
            <div class="form-control">
              <label class="label">
                <span class="label-text">源术语 (中文) <span class="text-error">*</span></span>
              </label>
              <input
                type="text"
                id="termSource"
                placeholder="例如：攻击力"
                class="input input-bordered"
                value="${term.source}"
              />
            </div>

            <!-- 目标语言（多语言标签页） -->
            <div class="form-control">
              <label class="label">
                <span class="label-text">目标语言翻译</span>
              </label>

              <div class="tabs tabs-boxed mb-2">
                <a class="tab tab-active" onclick="showLangTab('EN')">English</a>
                <a class="tab" onclick="showLangTab('JP')">日本語</a>
                <a class="tab" onclick="showLangTab('TH')">ไทย</a>
                <a class="tab" onclick="showLangTab('PT')">Português</a>
              </div>

              <div id="langTab-EN">
                <input type="text" id="termEN" placeholder="英文翻译" class="input input-bordered" value="${term.translations.EN || ''}" />
              </div>
              <div id="langTab-JP" class="hidden">
                <input type="text" id="termJP" placeholder="日文翻译" class="input input-bordered" value="${term.translations.JP || ''}" />
              </div>
              <div id="langTab-TH" class="hidden">
                <input type="text" id="termTH" placeholder="泰文翻译" class="input input-bordered" value="${term.translations.TH || ''}" />
              </div>
              <div id="langTab-PT" class="hidden">
                <input type="text" id="termPT" placeholder="葡文翻译" class="input input-bordered" value="${term.translations.PT || ''}" />
              </div>
            </div>

            <!-- 备注 -->
            <div class="form-control">
              <label class="label">
                <span class="label-text">备注</span>
              </label>
              <textarea
                id="termNotes"
                class="textarea textarea-bordered"
                placeholder="使用说明、注意事项等"
              >${term.notes || ''}</textarea>
            </div>
          </div>

          <div class="modal-action">
            <button class="btn btn-ghost" onclick="closeTermModal()">取消</button>
            <button class="btn btn-primary" onclick="glossaryPage.saveTerm('${termId}')">保存</button>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
  }
  ```

- [ ] 实现保存术语
  ```javascript
  async saveTerm(termId) {
    const termData = {
      source: document.getElementById('termSource').value,
      translations: {
        EN: document.getElementById('termEN').value,
        JP: document.getElementById('termJP').value,
        TH: document.getElementById('termTH').value,
        PT: document.getElementById('termPT').value
      },
      notes: document.getElementById('termNotes').value
    };

    // 验证
    if (!termData.source) {
      UIHelper.showToast('请输入源术语', 'error');
      return;
    }

    const hasTranslation = Object.values(termData.translations).some(t => t);
    if (!hasTranslation) {
      UIHelper.showToast('请至少提供一个翻译', 'error');
      return;
    }

    try {
      UIHelper.showLoading(true);

      if (termId) {
        await api.updateTerm(this.currentGlossaryId, termId, termData);
      } else {
        await api.createTerm(this.currentGlossaryId, termData);
      }

      await this.loadTerms(this.currentGlossaryId);
      this.renderTermTable();
      closeTermModal();

      UIHelper.showToast('保存成功', 'success');
    } catch (error) {
      UIHelper.showToast(`保存失败: ${error.message}`, 'error');
    } finally {
      UIHelper.showLoading(false);
    }
  }
  ```

- [ ] 实现删除术语
  ```javascript
  async deleteTerm(termId) {
    const confirmed = await UIHelper.confirm('确定要删除这条术语吗？');
    if (!confirmed) return;

    try {
      await api.deleteTerm(this.currentGlossaryId, termId);
      await this.loadTerms(this.currentGlossaryId);
      this.renderTermTable();
      UIHelper.showToast('删除成功', 'success');
    } catch (error) {
      UIHelper.showToast(`删除失败: ${error.message}`, 'error');
    }
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 术语库管理 - 在线编辑术语（297-312行）
- `docs/design/UI_DESIGN.md` - 术语编辑Modal（481-557行）

**交付标准**:
- 可以新增术语
- 可以编辑术语（多语言标签页）
- 可以删除术语（有二次确认）

---

#### 3.2 导入/导出功能 (2天)

**目标**: 实现Excel导入导出功能

**任务**:
- [ ] 实现Excel导入
  ```javascript
  async importFromExcel() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.xlsx,.xls';
    fileInput.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      try {
        UIHelper.showLoading(true, '解析文件中...');

        // 使用SheetJS解析Excel
        const data = await this.parseExcelFile(file);

        // 验证数据
        const validation = this.validateGlossaryData(data);
        if (!validation.valid) {
          UIHelper.showToast(validation.message, 'error');
          return;
        }

        // 预览导入数据（前10条）
        const confirmed = await this.showImportPreview(data.slice(0, 10));
        if (!confirmed) return;

        UIHelper.showLoading(true, '导入中...');

        // 调用API导入
        const result = await api.importTerms(this.currentGlossaryId, data);

        await this.loadTerms(this.currentGlossaryId);
        this.renderTermTable();

        UIHelper.showToast(
          `导入成功: ${result.successCount} 条，失败: ${result.failCount} 条`,
          result.failCount > 0 ? 'warning' : 'success'
        );
      } catch (error) {
        UIHelper.showToast(`导入失败: ${error.message}`, 'error');
      } finally {
        UIHelper.showLoading(false);
      }
    };

    fileInput.click();
  }
  ```

- [ ] 实现Excel解析
  ```javascript
  async parseExcelFile(file) {
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
  ```

- [ ] 实现数据验证
  ```javascript
  validateGlossaryData(data) {
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

- [ ] 实现导出功能
  ```javascript
  async exportGlossary() {
    try {
      const terms = this.terms;
      if (terms.length === 0) {
        UIHelper.showToast('没有术语可导出', 'warning');
        return;
      }

      // 准备导出数据
      const exportData = terms.map(term => ({
        '源术语': term.source,
        'EN': term.translations.EN || '',
        'JP': term.translations.JP || '',
        'TH': term.translations.TH || '',
        'PT': term.translations.PT || '',
        '备注': term.notes || ''
      }));

      // 使用ExportHelper导出
      const glossary = this.glossaries.find(g => g.id === this.currentGlossaryId);
      ExportHelper.exportToExcel(exportData, `${glossary.name}_${Date.now()}.xlsx`);

      UIHelper.showToast('导出成功', 'success');
    } catch (error) {
      UIHelper.showToast(`导出失败: ${error.message}`, 'error');
    }
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 术语库管理 - 导入术语库（279-295行）
- `docs/technical/FEATURE_SPEC.md` - 术语库管理 - importGlossary（681-783行）
- SheetJS文档

**交付标准**:
- 可以导入Excel文件
- 导入前有数据预览和验证
- 可以导出Excel文件

---

### Week 3-4: 数据分析开发

#### 4.1 翻译统计 (2天)

**目标**: 实现翻译量统计和展示

**任务**:
- [ ] 创建analytics.js页面逻辑
  ```javascript
  // 文件: js/pages/analytics.js
  class AnalyticsPage {
    constructor() {
      this.sessions = [];
      this.timeRange = 'month';
      this.stats = null;
    }

    async init() {
      await this.loadData(this.timeRange);
      this.render();
    }

    async loadData(timeRange) {
      this.timeRange = timeRange;
      this.sessions = await this.fetchSessionsInRange(timeRange);
      this.stats = this.calculateStats();
    }

    async fetchSessionsInRange(range) { /* ... */ }
    calculateStats() { /* ... */ }
    render() { /* ... */ }
  }
  ```

- [ ] 实现统计引擎
  ```javascript
  class AnalyticsEngine {
    constructor(sessions) {
      this.sessions = sessions;
    }

    calculateStats() {
      // 1. 翻译量统计
      const totalTasks = this.sessions.reduce((sum, s) =>
        sum + (s.executionResult?.totalTasks || 0), 0
      );

      const completedTasks = this.sessions
        .filter(s => s.stage === 'completed')
        .reduce((sum, s) => sum + (s.executionResult?.completedTasks || 0), 0);

      // 2. 成本统计
      const totalCost = this.sessions
        .filter(s => s.stage === 'completed')
        .reduce((sum, s) => sum + (s.executionResult?.cost || 0), 0);

      // 3. 按语言分组
      const langStats = this.groupByLanguage(this.sessions);

      // 4. 按模型分组
      const modelStats = this.groupByModel(this.sessions);

      // 5. 成功率
      const successRate = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

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
          if (!stats[lang]) stats[lang] = 0;
          stats[lang] += avgCount;
        });
      });

      return stats;
    }

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
  }
  ```

- [ ] 渲染统计卡片
  ```javascript
  renderStatCards() {
    return `
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        ${new StatCard({
          title: '总翻译量',
          value: this.stats.totalTasks,
          icon: 'bi-clipboard-check',
          trend: { value: 15.2, direction: 'up', unit: '%' }
        }).render()}

        ${new StatCard({
          title: '总成本',
          value: `$${this.stats.totalCost.toFixed(2)}`,
          icon: 'bi-cash-stack',
          trend: { value: 8.3, direction: 'down', unit: '%' }
        }).render()}

        ${new StatCard({
          title: '平均速度',
          value: '120/分钟',
          icon: 'bi-lightning-fill',
          trend: { value: 5.1, direction: 'up', unit: '%' }
        }).render()}

        ${new StatCard({
          title: '成功率',
          value: `${this.stats.successRate.toFixed(1)}%`,
          icon: 'bi-check-circle-fill',
          trend: { value: 2.1, direction: 'up', unit: '%' }
        }).render()}
      </div>
    `;
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 数据分析 - 翻译统计（334-362行）
- `docs/technical/FEATURE_SPEC.md` - 数据分析 - AnalyticsEngine（906-1044行）

**交付标准**:
- 4个统计卡片正确显示数据
- 可以切换时间范围（日/周/月）
- 统计数据准确

---

#### 4.2 成本分析 (1.5天)

**目标**: 展示成本统计和预算预警

**任务**:
- [ ] 实现成本分析卡片
  ```javascript
  renderCostAnalysis() {
    const budget = 50.0; // 从配置读取
    const costPercent = (this.stats.totalCost / budget) * 100;

    return `
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <h3 class="card-title">💰 成本分析（本月）</h3>

          <div class="mb-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm">总成本</span>
              <span class="text-2xl font-bold">$${this.stats.totalCost.toFixed(2)} / $${budget.toFixed(2)}</span>
            </div>
            <progress class="progress ${costPercent > 80 ? 'progress-error' : 'progress-success'} w-full" value="${costPercent}" max="100"></progress>
            <span class="text-sm text-base-content/60">${costPercent.toFixed(1)}% 预算</span>

            ${costPercent > 80 ? `
              <div class="alert alert-warning mt-2">
                <i class="bi bi-exclamation-triangle"></i>
                <span>预算即将超支，请注意控制成本</span>
              </div>
            ` : ''}
          </div>

          <h4 class="font-semibold mb-2">按模型分组</h4>
          <div class="space-y-2">
            ${Object.entries(this.stats.modelStats).map(([model, stats]) => {
              const modelPercent = (stats.cost / this.stats.totalCost) * 100;
              return `
                <div class="flex items-center justify-between">
                  <span class="text-sm">${model}</span>
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium">$${stats.cost.toFixed(2)}</span>
                    <span class="text-xs text-base-content/60">(${modelPercent.toFixed(1)}%)</span>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      </div>
    `;
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 数据分析 - 成本分析（364-392行）

**交付标准**:
- 成本统计准确
- 预算占比正确显示
- 超过80%显示预警

---

#### 4.3 趋势图表 (2天)

**目标**: 使用Chart.js渲染趋势图和分布图

**任务**:
- [ ] 实现翻译量趋势图
  ```javascript
  renderTrendChart() {
    const chartData = this.stats.trends;

    ChartHelper.createLineChart('trendChart', {
      labels: chartData.map(d => d.date),
      datasets: [{
        label: '翻译量',
        data: chartData.map(d => d.tasks),
        borderColor: '#4F46E5',
        backgroundColor: 'rgba(79, 70, 229, 0.1)',
        tension: 0.4,
        fill: true
      }]
    }, {
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
    });
  }
  ```

- [ ] 实现语言分布饼图
  ```javascript
  renderLanguageChart() {
    const languages = Object.keys(this.stats.langStats);
    const counts = Object.values(this.stats.langStats);
    const total = counts.reduce((a, b) => a + b, 0);

    ChartHelper.createPieChart('languageChart', {
      labels: languages,
      datasets: [{
        data: counts,
        backgroundColor: ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
      }]
    }, {
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
    });
  }
  ```

- [ ] 实现成本趋势图（可选）
  ```javascript
  renderCostTrendChart() {
    const chartData = this.stats.trends;

    ChartHelper.createLineChart('costTrendChart', {
      labels: chartData.map(d => d.date),
      datasets: [{
        label: '成本 ($)',
        data: chartData.map(d => d.cost),
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        fill: true
      }]
    });
  }
  ```

**参考文档**:
- `docs/design/UI_DESIGN.md` - 图表组件（600-651行）
- `docs/technical/FEATURE_SPEC.md` - ChartRenderer（1048-1145行）
- Chart.js官方文档

**交付标准**:
- 趋势图正确渲染
- 饼图正确渲染
- 图表样式符合设计规范

---

#### 4.4 导出报告 (1天)

**目标**: 导出统计报表为Excel

**任务**:
- [ ] 实现报表导出
  ```javascript
  async exportReport() {
    try {
      const reportData = [
        // 汇总数据
        {
          '统计项': '总翻译量',
          '数值': this.stats.totalTasks,
          '单位': '任务'
        },
        {
          '统计项': '总成本',
          '数值': this.stats.totalCost.toFixed(2),
          '单位': 'USD'
        },
        {
          '统计项': '成功率',
          '数值': this.stats.successRate.toFixed(1),
          '单位': '%'
        },
        {},
        // 按语言分组
        { '语言': '语言分布', '翻译量': '' },
        ...Object.entries(this.stats.langStats).map(([lang, count]) => ({
          '语言': lang,
          '翻译量': count
        })),
        {},
        // 趋势数据
        { '日期': '趋势数据', '翻译量': '', '成本': '' },
        ...this.stats.trends.map(trend => ({
          '日期': trend.date,
          '翻译量': trend.tasks,
          '成本': trend.cost.toFixed(2)
        }))
      ];

      ExportHelper.exportToExcel(
        reportData,
        `统计报告_${this.timeRange}_${Date.now()}.xlsx`
      );

      UIHelper.showToast('导出成功', 'success');
    } catch (error) {
      UIHelper.showToast(`导出失败: ${error.message}`, 'error');
    }
  }
  ```

**参考文档**:
- `docs/requirements/REQUIREMENTS.md` - 会话管理 - 批量导出报告（239-242行）

**交付标准**:
- 可以导出Excel报表
- 报表包含完整的统计数据
- 格式清晰易读

---

### Week 4: 完善与测试

#### 功能完善 (1天)
- [ ] Bug修复
- [ ] 性能优化
- [ ] 响应式适配

#### 集成测试 (1天)
- [ ] 术语库完整流程测试
- [ ] 数据分析准确性测试
- [ ] 浏览器兼容性测试

---

## 📚 参考文档清单

### 必读文档（按优先级）

1. **`docs/requirements/REQUIREMENTS.md`** ⭐⭐⭐
   - 核心功能模块 - 术语库管理（245-327行）
   - 核心功能模块 - 数据分析（330-413行）

2. **`docs/technical/FEATURE_SPEC.md`** ⭐⭐⭐
   - 功能模块详述 - 术语库管理（607-899行）
   - 功能模块详述 - 数据分析（902-1145行）

3. **`docs/design/UI_DESIGN.md`** ⭐⭐⭐
   - 页面原型 - Glossary（451-558行）
   - 页面原型 - Analytics（561-652行）

4. **`docs/API.md`** ⭐⭐
   - 术语表管理API（502-643行）

### 外部文档

5. **SheetJS文档** ⭐⭐
   - https://docs.sheetjs.com/

6. **Chart.js文档** ⭐⭐
   - https://www.chartjs.org/

---

## 🎯 交付标准

### Week 2 交付
- [ ] ✅ 术语库列表完成
- [ ] ✅ 术语条目表格完成
- [ ] ✅ 术语搜索功能完成

### Week 3 交付
- [ ] ✅ 术语CRUD完成
- [ ] ✅ 导入导出功能完成
- [ ] ✅ 翻译统计完成

### Week 4 交付
- [ ] ✅ 成本分析完成
- [ ] ✅ 趋势图表完成
- [ ] ✅ 报表导出完成
- [ ] ✅ 所有功能测试通过

---

## 🤝 协作接口

### 依赖工程师A的接口

#### 使用组件
```javascript
import DataTable from '../components/DataTable.js';
import StatCard from '../components/StatCard.js';
import EmptyState from '../components/EmptyState.js';
```

#### 使用工具函数
```javascript
import ChartHelper from '../utils/chart-helper.js';
import ExportHelper from '../utils/export-helper.js';
```

---

## ✅ 自检清单

### Week 2结束前
- [ ] 术语库列表可以切换
- [ ] 术语表格正确显示
- [ ] 搜索功能正常

### Week 3结束前
- [ ] CRUD功能完整
- [ ] 导入导出功能正常
- [ ] 翻译统计数据准确

### Week 4结束前
- [ ] 所有图表正确渲染
- [ ] 报表导出功能正常
- [ ] 所有功能测试通过

---

**开始时间**: Week 2 Day 1
**预计完成**: Week 4 Day 5
**总工作量**: 14天（112小时）

**祝开发顺利！** 🚀
