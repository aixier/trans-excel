/**
 * 配置确认对话框组件 - 极简版
 *
 * 显示分析结果并让用户选择术语库
 *
 * @author 工程师B
 * @date 2025-10-17
 */

class ConfigConfirmModal {
  constructor() {
    this.analysis = null;
    this.file = null;
    this.glossaries = [];
    this.selectedGlossaryId = null;
    this.onConfirmCallback = null;
  }

  /**
   * 初始化模态框
   */
  async init() {
    await this.loadGlossaries();
    this.setupEventListeners();
  }

  /**
   * 加载术语库列表
   */
  async loadGlossaries() {
    try {
      this.glossaries = await window.api.getGlossaries();
    } catch (error) {
      console.error('Failed to load glossaries:', error);
      this.glossaries = [];
    }
  }

  /**
   * 设置事件监听
   */
  setupEventListeners() {
    // 术语库选项切换
    const radioNone = document.getElementById('glossaryNone');
    const radioExisting = document.getElementById('glossaryExisting');
    const radioUpload = document.getElementById('glossaryUpload');
    const selectGlossary = document.getElementById('glossarySelect');
    const fileInput = document.getElementById('glossaryFile');

    if (radioNone) {
      radioNone.addEventListener('change', () => {
        selectGlossary.classList.add('hidden');
        fileInput.classList.add('hidden');
        this.selectedGlossaryId = null;
      });
    }

    if (radioExisting) {
      radioExisting.addEventListener('change', () => {
        selectGlossary.classList.remove('hidden');
        fileInput.classList.add('hidden');
      });
    }

    if (radioUpload) {
      radioUpload.addEventListener('change', () => {
        selectGlossary.classList.add('hidden');
        fileInput.classList.remove('hidden');
      });
    }

    // 术语库选择
    if (selectGlossary) {
      selectGlossary.addEventListener('change', (e) => {
        this.selectedGlossaryId = e.target.value;
      });
    }

    // 开始处理按钮
    const startBtn = document.getElementById('startProcessBtn');
    if (startBtn) {
      startBtn.addEventListener('click', () => this.handleConfirm());
    }
  }

  /**
   * 显示模态框
   */
  async show(file, analysis, onConfirm) {
    this.file = file;
    this.analysis = analysis;
    this.onConfirmCallback = onConfirm;

    // 渲染模态框内容
    this.render();

    // 显示模态框
    const modal = document.getElementById('configModal');
    if (modal) {
      modal.showModal();
    }
  }

  /**
   * 渲染模态框内容
   */
  render() {
    const container = document.getElementById('configModalContent');
    if (!container) return;

    const analysis = this.analysis;
    const suggested = analysis.language_detection.suggested_config;
    const stats = analysis.statistics;

    // 检查是否有CAPS
    const hasCaps = analysis.file_info.sheets.some(
      sheet => sheet.toLowerCase().includes('caps')
    );

    // 计算预估时间
    const totalTasks = stats.estimated_tasks;
    const estimatedMinutes = Math.ceil(totalTasks / 15 / 60); // 假设15条/秒

    // 格式化目标语言
    const targetLangs = suggested.target_langs.join(', ');

    container.innerHTML = `
      <!-- 文件信息 -->
      <div class="p-4 bg-base-200 rounded-lg">
        <div class="flex items-center gap-2 mb-2">
          <i class="bi bi-file-earmark-excel text-success text-xl"></i>
          <span class="font-medium">${this.file.name}</span>
        </div>

        <div class="text-sm text-base-content/70 space-y-1">
          <div>${suggested.source_lang} → ${targetLangs}</div>
          <div>${totalTasks.toLocaleString()} 条任务 · 约 ${estimatedMinutes} 分钟</div>
          ${hasCaps ? `
            <div class="text-warning flex items-center gap-1">
              <i class="bi bi-exclamation-triangle"></i>
              包含 CAPS 工作表，将自动两阶段处理
            </div>
          ` : ''}
        </div>
      </div>

      <!-- 术语库选择 -->
      <div class="mt-4">
        <label class="label">
          <span class="label-text font-medium">📚 术语库（可选，提升翻译质量）</span>
        </label>

        <!-- 选项1: 不使用 -->
        <label class="label cursor-pointer justify-start gap-2">
          <input type="radio" name="glossary" value="none" id="glossaryNone" class="radio" checked />
          <span class="label-text">不使用术语库</span>
        </label>

        <!-- 选项2: 选择已有 -->
        <label class="label cursor-pointer justify-start gap-2">
          <input type="radio" name="glossary" value="existing" id="glossaryExisting" class="radio" />
          <span class="label-text">选择已有术语库</span>
        </label>

        <select id="glossarySelect" class="select select-bordered w-full mt-2 hidden">
          <option value="">选择术语库</option>
          ${this.glossaries.map(g => `
            <option value="${g.id}">${g.name} (${g.term_count || 0}条)</option>
          `).join('')}
        </select>

        <!-- 选项3: 上传新的 -->
        <label class="label cursor-pointer justify-start gap-2">
          <input type="radio" name="glossary" value="upload" id="glossaryUpload" class="radio" />
          <span class="label-text">上传新术语库</span>
        </label>

        <input type="file" id="glossaryFile" accept=".xlsx"
               class="file-input file-input-bordered w-full mt-2 hidden" />
      </div>
    `;

    // 重新绑定事件（因为DOM被重新创建）
    this.setupEventListeners();
  }

  /**
   * 处理确认
   */
  async handleConfirm() {
    try {
      // 检查术语库选择
      const glossaryOption = document.querySelector('input[name="glossary"]:checked')?.value;

      let glossaryId = null;
      let glossaryFile = null;

      if (glossaryOption === 'upload') {
        const fileInput = document.getElementById('glossaryFile');
        if (fileInput && fileInput.files.length > 0) {
          glossaryFile = fileInput.files[0];
        }
      } else if (glossaryOption === 'existing') {
        glossaryId = document.getElementById('glossarySelect')?.value;
      }

      // 关闭模态框
      const modal = document.getElementById('configModal');
      if (modal) {
        modal.close();
      }

      // 调用回调
      if (this.onConfirmCallback) {
        await this.onConfirmCallback({
          glossaryId,
          glossaryFile,
          analysis: this.analysis
        });
      }

    } catch (error) {
      console.error('Confirm failed:', error);
      alert('确认失败: ' + error.message);
    }
  }
}

// 创建全局实例
const configConfirmModal = new ConfigConfirmModal();

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ConfigConfirmModal;
}
