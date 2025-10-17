/**
 * 统一工作流页面 - 整合三个测试页面的进度条
 *
 * 功能（4阶段工作流）：
 * - 阶段1: 上传文件并拆分翻译任务 (来自 1_upload_and_split.html)
 * - 阶段2: 执行翻译 (来自 2_execute_transformation.html)
 * - 阶段3: CAPS任务拆分 (来自 4_caps_transformation.html，可选)
 * - 阶段4: CAPS大写转换执行 (可选)
 *
 * @author Claude
 * @date 2025-10-17
 */

class UnifiedWorkflowPage {
  constructor() {
    this.apiUrl = window.API_BASE_URL || 'http://localhost:8013';
    this.file = null;
    this.glossaryFile = null;
    this.glossaryId = null;  // 存储上传的术语库ID
    this.glossarySource = null;  // 'upload' or 'select'
    this.sessionIds = [];  // 存储各阶段的session ID
    this.pollIntervals = [];  // 存储轮询定时器
  }

  async init() {
    this.render();
    this.setupEventListeners();
    await this.loadAvailableGlossaries();
  }

  render() {
    const container = document.getElementById('app');

    container.innerHTML = `
      <style>
        /* 复用测试页面的样式 - 紧凑布局 */
        .phase-container {
          background: white;
          border-radius: 6px;
          padding: 15px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          margin-bottom: 12px;
        }
        .phase-header {
          border-bottom: 2px solid #667eea;
          padding-bottom: 10px;
          margin-bottom: 20px;
        }
        .phase-1 .phase-header { border-color: #667eea; color: #667eea; }
        .phase-2 .phase-header { border-color: #ff6b6b; color: #ff6b6b; }
        .phase-3 .phase-header { border-color: #f093fb; color: #f093fb; }
        .phase-4 .phase-header { border-color: #4ade80; color: #4ade80; }

        .progress-bar-container {
          width: 100%;
          height: 30px;
          background: #e9ecef;
          border-radius: 15px;
          overflow: hidden;
          margin: 15px 0;
        }
        .progress-fill {
          height: 100%;
          transition: width 0.3s;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
        }
        .phase-1 .progress-fill { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); }
        .phase-2 .progress-fill { background: linear-gradient(90deg, #ff6b6b 0%, #ff8e53 100%); }
        .phase-3 .progress-fill { background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%); }
        .phase-4 .progress-fill { background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%); }

        .status-box {
          padding: 15px;
          border-radius: 6px;
          margin: 15px 0;
          font-weight: bold;
        }
        .status-box.success {
          background: #d4edda;
          color: #155724;
          border-left: 4px solid #28a745;
        }
        .status-box.error {
          background: #f8d7da;
          color: #721c24;
          border-left: 4px solid #dc3545;
        }
        .status-box.processing {
          background: #d1ecf1;
          color: #0c5460;
          border-left: 4px solid #17a2b8;
        }
        .status-box.pending {
          background: #f8f9fa;
          color: #6c757d;
          border-left: 4px solid #6c757d;
        }

        .export-btn {
          margin: 5px;
          padding: 8px 16px;
          background: #28a745;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }
        .export-btn:hover {
          background: #218838;
        }
        .export-btn:disabled {
          background: #6c757d;
          cursor: not-allowed;
        }

        .session-id-display {
          background: #28a745;
          color: white;
          padding: 10px;
          border-radius: 6px;
          font-family: monospace;
          font-size: 14px;
          text-align: center;
          margin: 10px 0;
          cursor: pointer;
        }
        .session-id-display:hover {
          background: #218838;
        }
      </style>

      <!-- 上传区域 -->
      <div class="container mx-auto p-4 max-w-5xl">
        <div class="text-center mb-4">
          <h1 class="text-3xl font-bold mb-2">🚀 统一工作流</h1>
          <p class="text-base-content/70 text-sm">上传Excel文件和术语库，自动完成翻译和CAPS转换</p>
        </div>

        <!-- 文件上传 -->
        <div class="phase-container phase-1">
          <h2 class="phase-header text-lg font-bold">📤 文件上传</h2>

          <div class="form-control mb-3">
            <label class="label py-1"><span class="label-text font-semibold text-sm">Excel文件</span></label>
            <input type="file" id="fileInput" accept=".xlsx,.xls" class="file-input file-input-bordered file-input-sm w-full" />
          </div>

          <!-- 术语库选择 -->
          <div class="form-control mb-3">
            <label class="label py-1"><span class="label-text font-semibold text-sm">术语库 (可选)</span></label>
            <div class="grid grid-cols-2 gap-2">
              <select id="glossarySelect" class="select select-bordered select-sm w-full" onchange="unifiedWorkflowPage.onGlossarySelectChange()">
                <option value="">选择已有术语库...</option>
              </select>
              <label class="btn btn-sm btn-outline">
                <input type="file" id="glossaryFileInput" accept=".json,.xlsx,.xls" class="hidden" onchange="unifiedWorkflowPage.onGlossaryFileChange()" />
                📤 上传新术语库
              </label>
            </div>
            <div id="glossaryStatus" class="text-xs mt-1 text-gray-600" style="display: none;"></div>
          </div>

          <!-- 隐藏Source和Target Languages输入框 -->
          <input type="hidden" id="sourceLang" value="CH" />
          <input type="hidden" id="targetLangs" value="" />

          <button id="startBtn" class="btn btn-primary btn-sm w-full" onclick="unifiedWorkflowPage.startWorkflow()">
            🚀 开始工作流
          </button>
        </div>

        <!-- 阶段1: 上传并拆分 -->
        <div id="phase1Container" class="phase-container phase-1" style="display: none;">
          <h2 class="phase-header text-xl font-bold">🎯 阶段1: 任务拆分</h2>

          <div class="progress-bar-container">
            <div id="phase1Progress" class="progress-fill" style="width: 0%">0%</div>
          </div>
          <div id="phase1Text" class="text-sm text-gray-600 mb-2"></div>

          <div id="phase1Status" class="status-box pending">等待开始...</div>

          <div id="phase1SessionId" class="session-id-display" style="display: none;" onclick="unifiedWorkflowPage.copySessionId(0)">
            Session ID: <span id="phase1SessionValue"></span>
          </div>

          <!-- 阶段1导出按钮已隐藏 -->
          <div id="phase1Exports" style="display: none;"></div>
        </div>

        <!-- 阶段2: 执行翻译 -->
        <div id="phase2Container" class="phase-container phase-2" style="display: none;">
          <h2 class="phase-header text-xl font-bold">⚡ 阶段2: 执行翻译</h2>

          <div class="progress-bar-container">
            <div id="phase2Progress" class="progress-fill" style="width: 0%">0%</div>
          </div>
          <div id="phase2Text" class="text-sm text-gray-600 mb-2"></div>

          <div id="phase2Status" class="status-box pending">等待阶段1完成...</div>

          <div id="phase2SessionId" class="session-id-display" style="display: none;" onclick="unifiedWorkflowPage.copySessionId(1)">
            Session ID: <span id="phase2SessionValue"></span>
          </div>

          <div id="phase2Exports" style="display: none;">
            <button class="export-btn" onclick="unifiedWorkflowPage.exportPhase2Output()">
              📄 导出翻译结果Excel
            </button>
          </div>
        </div>

        <!-- 阶段3: CAPS任务拆分 (可选) -->
        <div id="phase3Container" class="phase-container phase-3" style="display: none;">
          <h2 class="phase-header text-xl font-bold">🔠 阶段3: CAPS任务拆分</h2>

          <div class="progress-bar-container">
            <div id="phase3Progress" class="progress-fill" style="width: 0%">0%</div>
          </div>
          <div id="phase3Text" class="text-sm text-gray-600 mb-2"></div>

          <div id="phase3Status" class="status-box pending">检测中...</div>

          <div id="phase3SessionId" class="session-id-display" style="display: none;" onclick="unifiedWorkflowPage.copySessionId(2)">
            Session ID: <span id="phase3SessionValue"></span>
          </div>

          <!-- 阶段3导出按钮已隐藏 -->
          <div id="phase3Exports" style="display: none;"></div>
        </div>

        <!-- 阶段4: CAPS大写转换执行 (可选) -->
        <div id="phase4Container" class="phase-container phase-4" style="display: none;">
          <h2 class="phase-header text-xl font-bold">✨ 阶段4: CAPS大写转换</h2>

          <div class="progress-bar-container">
            <div id="phase4Progress" class="progress-fill" style="width: 0%">0%</div>
          </div>
          <div id="phase4Text" class="text-sm text-gray-600 mb-2"></div>

          <div id="phase4Status" class="status-box pending">等待阶段3完成...</div>

          <div id="phase4SessionId" class="session-id-display" style="display: none;" onclick="unifiedWorkflowPage.copySessionId(3)">
            Session ID: <span id="phase4SessionValue"></span>
          </div>

          <div id="phase4Exports" style="display: none;">
            <button class="export-btn" onclick="unifiedWorkflowPage.exportPhase4Output()">
              📄 导出最终结果Excel
            </button>
          </div>
        </div>

        <!-- 完成页面 -->
        <div id="completionContainer" class="phase-container" style="display: none; text-align: center;">
          <div class="text-6xl mb-4">🎉</div>
          <h2 class="text-3xl font-bold mb-2">工作流完成！</h2>
          <p class="text-gray-600 mb-4">所有阶段已成功完成</p>
          <button class="btn btn-primary btn-lg" onclick="unifiedWorkflowPage.resetForNewFile()">
            <i class="bi bi-arrow-repeat"></i>
            处理新文件
          </button>
        </div>
      </div>
    `;
  }

  setupEventListeners() {
    // 事件监听已在HTML中通过onclick绑定
  }

  /**
   * 加载可用的术语库列表
   */
  async loadAvailableGlossaries() {
    try {
      const response = await fetch(`${this.apiUrl}/api/glossaries/list`);
      if (!response.ok) {
        console.error('Failed to load glossaries');
        return;
      }

      const data = await response.json();
      const glossaries = data.glossaries || [];

      const select = document.getElementById('glossarySelect');
      if (!select) return;

      // 清空现有选项（保留第一个默认选项）
      while (select.options.length > 1) {
        select.remove(1);
      }

      // 添加术语库选项
      glossaries.forEach(glossary => {
        const option = document.createElement('option');
        option.value = glossary.id;
        option.textContent = `${glossary.name} (${glossary.term_count} 条术语)`;
        select.appendChild(option);
      });

      console.log(`✅ Loaded ${glossaries.length} available glossaries`);
    } catch (error) {
      console.error('Error loading glossaries:', error);
    }
  }

  /**
   * 术语库下拉选择变化处理
   */
  onGlossarySelectChange() {
    const select = document.getElementById('glossarySelect');
    const selectedId = select.value;
    const statusEl = document.getElementById('glossaryStatus');

    if (selectedId) {
      // 用户选择了已有术语库
      this.glossaryId = selectedId;
      this.glossarySource = 'select';
      this.glossaryFile = null;

      // 显示状态
      statusEl.textContent = `✅ 已选择: ${select.options[select.selectedIndex].text}`;
      statusEl.style.display = 'block';
      statusEl.className = 'text-xs mt-1 text-success';

      console.log(`Selected glossary: ${selectedId}`);
    } else {
      // 用户清除选择
      if (this.glossarySource === 'select') {
        this.glossaryId = null;
        this.glossarySource = null;
      }
      statusEl.style.display = 'none';
    }
  }

  /**
   * 术语库文件上传变化处理
   */
  async onGlossaryFileChange() {
    const fileInput = document.getElementById('glossaryFileInput');
    const file = fileInput.files[0];
    const statusEl = document.getElementById('glossaryStatus');

    if (!file) return;

    // 验证文件类型
    const isJson = file.name.endsWith('.json');
    const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls');

    if (!isJson && !isExcel) {
      statusEl.textContent = '❌ 只支持 .json, .xlsx, .xls 格式';
      statusEl.style.display = 'block';
      statusEl.className = 'text-xs mt-1 text-error';
      fileInput.value = '';
      return;
    }

    // 存储文件，稍后上传
    this.glossaryFile = file;
    this.glossarySource = 'upload';

    // 清除下拉选择
    const select = document.getElementById('glossarySelect');
    select.value = '';

    // 显示状态
    statusEl.textContent = `📄 待上传: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    statusEl.style.display = 'block';
    statusEl.className = 'text-xs mt-1 text-info';

    console.log(`Glossary file selected: ${file.name}`);
  }

  /**
   * 重置所有阶段显示状态
   */
  resetAllPhases() {
    // 重置数据
    this.sessionIds = [];
    this.glossaryId = null;

    // 隐藏所有阶段容器
    document.getElementById('phase1Container').style.display = 'none';
    document.getElementById('phase2Container').style.display = 'none';
    document.getElementById('phase3Container').style.display = 'none';
    document.getElementById('phase4Container').style.display = 'none';
    document.getElementById('completionContainer').style.display = 'none';

    // 重置所有进度条
    for (let i = 1; i <= 4; i++) {
      const progressBar = document.getElementById(`phase${i}Progress`);
      if (progressBar) {
        progressBar.style.width = '0%';
        progressBar.textContent = '0%';
      }

      const progressText = document.getElementById(`phase${i}Text`);
      if (progressText) {
        progressText.textContent = '';
      }

      const status = document.getElementById(`phase${i}Status`);
      if (status) {
        status.className = 'status-box pending';
        status.textContent = '等待开始...';
      }

      const sessionId = document.getElementById(`phase${i}SessionId`);
      if (sessionId) {
        sessionId.style.display = 'none';
      }

      const exports = document.getElementById(`phase${i}Exports`);
      if (exports) {
        exports.style.display = 'none';
      }
    }

    console.log('✅ All phases reset');
  }

  /**
   * 重置并准备处理新文件
   * 由"处理新文件"按钮调用
   */
  resetForNewFile() {
    // 重置所有阶段
    this.resetAllPhases();

    // 清除文件输入
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
      fileInput.value = '';
    }

    const glossaryFileInput = document.getElementById('glossaryFileInput');
    if (glossaryFileInput) {
      glossaryFileInput.value = '';
    }

    // 清除术语库选择
    const glossarySelect = document.getElementById('glossarySelect');
    if (glossarySelect) {
      glossarySelect.value = '';
    }

    // 隐藏术语库状态
    const glossaryStatus = document.getElementById('glossaryStatus');
    if (glossaryStatus) {
      glossaryStatus.style.display = 'none';
    }

    // 重置文件引用
    this.file = null;
    this.glossaryFile = null;
    this.glossarySource = null;

    // 滚动到页面顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });

    console.log('✅ Ready for new file');
  }

  /**
   * 开始工作流（4阶段）
   */
  async startWorkflow() {
    const fileInput = document.getElementById('fileInput');
    this.file = fileInput.files[0];

    if (!this.file) {
      alert('请选择Excel文件');
      return;
    }

    const startBtn = document.getElementById('startBtn');
    startBtn.disabled = true;

    try {
      // 🔥 保存术语库信息（resetAllPhases会清除它）
      const savedGlossaryId = this.glossaryId;
      const savedGlossaryFile = this.glossaryFile;
      const savedGlossarySource = this.glossarySource;

      // 🔄 重置所有阶段显示状态
      this.resetAllPhases();

      // 🔥 恢复术语库信息
      this.glossaryId = savedGlossaryId;
      this.glossaryFile = savedGlossaryFile;
      this.glossarySource = savedGlossarySource;

      // 处理术语库（上传或使用已有）
      if (this.glossaryId || this.glossaryFile) {
        await this.handleGlossary();
      }

      // 显示阶段1和阶段2容器
      document.getElementById('phase1Container').style.display = 'block';
      document.getElementById('phase2Container').style.display = 'block';

      // 执行阶段1: 上传并拆分翻译任务
      await this.executePhase1();

      // 执行阶段2: 执行翻译
      await this.executePhase2();

      // 检测是否需要CAPS
      const hasCaps = await this.detectCapsSheets();

      if (hasCaps) {
        // 显示阶段3和阶段4容器
        document.getElementById('phase3Container').style.display = 'block';
        document.getElementById('phase4Container').style.display = 'block';

        // 执行阶段3: CAPS任务拆分
        await this.executePhase3();

        // 执行阶段4: CAPS大写转换
        await this.executePhase4();
      } else {
        // 无需CAPS，显示提示
        document.getElementById('phase3Container').style.display = 'block';
        this.updatePhaseStatus(3, 'success', '✅ 无需CAPS转换，工作流完成');
      }

      // 显示完成页面
      document.getElementById('completionContainer').style.display = 'block';

    } catch (error) {
      console.error('Workflow error:', error);
      alert('工作流执行失败: ' + error.message);
    } finally {
      startBtn.disabled = false;
    }
  }

  /**
   * 处理术语库（上传或使用已有）
   */
  async handleGlossary() {
    try {
      // 如果已经通过下拉选择了术语库，直接使用
      if (this.glossarySource === 'select' && this.glossaryId) {
        this.updatePhaseStatus(1, 'success', `✅ 使用术语库: ${this.glossaryId}`);
        console.log(`Using existing glossary: ${this.glossaryId}`);
        return;
      }

      // 如果选择了文件，上传新术语库
      if (this.glossarySource === 'upload' && this.glossaryFile) {
        await this.uploadGlossary();
        return;
      }

      // 没有术语库
      console.log('No glossary selected');
    } catch (error) {
      console.error('Glossary handling error:', error);
      // 术语库处理失败不应该阻止工作流继续
      this.updatePhaseStatus(1, 'error', `⚠️ 术语库处理失败: ${error.message}，将继续翻译流程`);
      await this.delay(2000);
    }
  }

  /**
   * 上传新术语库文件
   */
  async uploadGlossary() {
    this.updatePhaseStatus(1, 'processing', '⏳ 正在上传术语库...');

    const formData = new FormData();
    formData.append('file', this.glossaryFile);

    // 生成术语库ID（使用文件名，去掉扩展名和特殊字符）
    const glossaryId = this.glossaryFile.name
      .replace(/\.[^/.]+$/, '')
      .replace(/[^a-zA-Z0-9_\-]/g, '_')
      .toLowerCase();

    formData.append('glossary_id', glossaryId);

    const response = await fetch(`${this.apiUrl}/api/glossaries/upload`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`术语库上传失败: ${error.detail || '未知错误'}`);
    }

    const data = await response.json();
    this.glossaryId = data.glossary_id;

    console.log(`Glossary uploaded successfully: ${this.glossaryId} (${data.term_count} terms)`);
    this.updatePhaseStatus(1, 'success', `✅ 术语库上传成功 (${data.term_count} 条术语)`);

    // 刷新术语库列表
    await this.loadAvailableGlossaries();
  }

  /**
   * 阶段1: 上传并拆分任务 (来自 1_upload_and_split.html)
   */
  async executePhase1() {
    this.updatePhaseStatus(1, 'processing', '⏳ 正在上传文件并拆分任务...');

    // 获取目标语言（可选，如果为空则自动检测所有空白列）
    const targetLangsInput = document.getElementById('targetLangs').value.trim();
    const formData = new FormData();
    formData.append('file', this.file);

    // 只有当用户填写了目标语言时才传递该参数
    if (targetLangsInput) {
      const targetLangs = targetLangsInput.split(',').map(s => s.trim()).filter(s => s.length > 0);
      if (targetLangs.length > 0) {
        formData.append('target_langs', JSON.stringify(targetLangs));
      }
    }
    // 如果不传 target_langs，后端会自动检测所有空白列

    formData.append('rule_set', 'translation');
    formData.append('extract_context', 'true');

    const response = await fetch(`${this.apiUrl}/api/tasks/split`, {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(`拆分失败: ${data.detail || '未知错误'}`);
    }

    const sessionId = data.session_id;
    this.sessionIds[0] = sessionId;

    // 显示Session ID
    document.getElementById('phase1SessionValue').textContent = sessionId;
    document.getElementById('phase1SessionId').style.display = 'block';

    // 轮询拆分状态并获取任务数
    const splitResult = await this.pollSplitStatus(sessionId);

    this.updatePhaseStatus(1, 'success', `✅ 拆分完成！任务数: ${splitResult.task_count || 0}`);
    document.getElementById('phase1Exports').style.display = 'block';
  }

  /**
   * 阶段2: 执行翻译 (来自 2_execute_transformation.html)
   */
  async executePhase2() {
    const sessionId = this.sessionIds[0];
    this.updatePhaseStatus(2, 'processing', '⏳ 正在执行AI翻译...');

    // 构建请求体，如果有术语库ID则传递
    const requestBody = {
      session_id: sessionId,
      processor: 'llm_qwen',
      max_workers: 10
    };

    // 如果上传了术语库，添加术语库ID
    if (this.glossaryId) {
      requestBody.glossary_id = this.glossaryId;
      console.log(`Using glossary: ${this.glossaryId}`);
    }

    const response = await fetch(`${this.apiUrl}/api/execute/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(`执行失败: ${data.detail || '未知错误'}`);
    }

    // 使用相同的session ID (翻译不创建新session)
    this.sessionIds[1] = sessionId;
    document.getElementById('phase2SessionValue').textContent = sessionId;
    document.getElementById('phase2SessionId').style.display = 'block';

    // 轮询执行状态
    await this.pollExecutionStatus(sessionId, 2);

    this.updatePhaseStatus(2, 'success', `✅ 翻译完成！`);
    document.getElementById('phase2Exports').style.display = 'block';
  }

  /**
   * 检测是否需要CAPS转换
   */
  async detectCapsSheets() {
    const parentSessionId = this.sessionIds[0];

    this.updatePhaseStatus(3, 'processing', '🔍 检测是否需要CAPS转换...');

    const sessionResponse = await fetch(`${this.apiUrl}/api/sessions/detail/${parentSessionId}`);
    const session = await sessionResponse.json();
    const sheets = session.metadata?.analysis?.file_info?.sheets || [];
    const hasCaps = sheets.some(sheet => sheet.toLowerCase().includes('caps'));

    console.log(`CAPS detection: ${hasCaps ? 'Found CAPS sheets' : 'No CAPS sheets'}`);
    return hasCaps;
  }

  /**
   * 阶段3: CAPS任务拆分 (来自 4_caps_transformation.html - Split部分)
   */
  async executePhase3() {
    const parentSessionId = this.sessionIds[0];

    this.updatePhaseStatus(3, 'processing', '⏳ 正在拆分CAPS任务...');

    // 拆分CAPS任务 - 目标语言可选（如果不传则自动继承父Session）
    const splitFormData = new FormData();
    splitFormData.append('parent_session_id', parentSessionId);

    // 只有当用户填写了目标语言时才传递该参数
    const targetLangsInput = document.getElementById('targetLangs').value.trim();
    if (targetLangsInput) {
      const targetLangs = targetLangsInput.split(',').map(s => s.trim()).filter(s => s.length > 0);
      if (targetLangs.length > 0) {
        splitFormData.append('target_langs', JSON.stringify(targetLangs));
      }
    }
    // 如果不传 target_langs，后端会自动从父Session继承

    splitFormData.append('rule_set', 'caps_only');
    splitFormData.append('extract_context', 'false');

    const splitResponse = await fetch(`${this.apiUrl}/api/tasks/split`, {
      method: 'POST',
      body: splitFormData
    });

    const splitData = await splitResponse.json();
    if (!splitResponse.ok) {
      throw new Error(`CAPS拆分失败: ${splitData.detail}`);
    }

    const capsSessionId = splitData.session_id;
    this.sessionIds[2] = capsSessionId;
    document.getElementById('phase3SessionValue').textContent = capsSessionId;
    document.getElementById('phase3SessionId').style.display = 'block';

    // 等待拆分完成并获取任务数
    const capsResult = await this.pollSplitStatus(capsSessionId);

    this.updatePhaseStatus(3, 'success', `✅ CAPS任务拆分完成！任务数: ${capsResult.task_count || 0}`);
    document.getElementById('phase3Exports').style.display = 'block';
  }

  /**
   * 阶段4: CAPS大写转换执行 (来自 4_caps_transformation.html - Execute部分)
   */
  async executePhase4() {
    const capsSessionId = this.sessionIds[2];

    this.updatePhaseStatus(4, 'processing', '⏳ 正在执行CAPS大写转换...');

    // 使用相同的session ID执行CAPS转换
    this.sessionIds[3] = capsSessionId;
    document.getElementById('phase4SessionValue').textContent = capsSessionId;
    document.getElementById('phase4SessionId').style.display = 'block';

    const execResponse = await fetch(`${this.apiUrl}/api/execute/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: capsSessionId,
        processor: 'uppercase',
        max_workers: 20
      })
    });

    const execData = await execResponse.json();
    if (!execResponse.ok) {
      throw new Error(`CAPS执行失败: ${execData.detail}`);
    }

    // 轮询执行状态
    await this.pollExecutionStatus(capsSessionId, 4);

    this.updatePhaseStatus(4, 'success', `✅ CAPS大写转换完成！`);
    document.getElementById('phase4Exports').style.display = 'block';
  }

  /**
   * 轮询拆分状态
   */
  async pollSplitStatus(sessionId) {
    let attemptCount = 0;
    const maxAttempts = 60; // 最多等待1分钟

    while (attemptCount < maxAttempts) {
      attemptCount++;

      try {
        const response = await fetch(`${this.apiUrl}/api/tasks/split/status/${sessionId}`);
        const data = await response.json();

        // 显示拆分进度（如果有）
        if (data.progress !== undefined) {
          const progress = Math.round(data.progress);
          console.log(`Split progress: ${progress}%`);
        }

        if (data.status === 'completed') {
          console.log(`Split completed: ${data.task_count || 0} tasks`);
          return data; // Return the complete status data with task_count
        } else if (data.status === 'failed') {
          throw new Error(data.message || '拆分失败');
        }

      } catch (error) {
        console.error(`Poll split error (attempt ${attemptCount}):`, error);
        if (attemptCount >= maxAttempts) {
          throw error;
        }
      }

      await this.delay(1000);
    }

    throw new Error('拆分超时');
  }

  /**
   * 轮询执行状态
   */
  async pollExecutionStatus(sessionId, phaseNum) {
    let attemptCount = 0;
    const maxAttempts = 300; // 最多轮询10分钟

    while (attemptCount < maxAttempts) {
      attemptCount++;

      try {
        const response = await fetch(`${this.apiUrl}/api/execute/status/${sessionId}`);
        const data = await response.json();

        // Handle both data formats: worker_pool format (progress) and idle format (statistics)
        let total, completed, processing, failed;

        if (data.progress) {
          // Running status from worker_pool - uses progress object
          total = data.progress.total || 0;
          completed = data.progress.completed || 0;
          processing = data.progress.pending || 0;  // pending = processing in worker_pool
          failed = data.progress.failed || 0;
        } else if (data.statistics) {
          // Idle/stopped status - uses statistics object
          const stats = data.statistics;
          const byStatus = stats.by_status || {};
          total = stats.total || 0;
          completed = byStatus.completed || 0;
          processing = byStatus.processing || 0;
          failed = byStatus.failed || 0;
        } else {
          // No data available
          total = completed = processing = failed = 0;
        }

        const progress = total > 0 ? Math.round((completed / total) * 100) : 0;

        // 更新进度条
        document.getElementById(`phase${phaseNum}Progress`).style.width = `${progress}%`;
        document.getElementById(`phase${phaseNum}Progress`).textContent = `${progress}%`;
        document.getElementById(`phase${phaseNum}Text`).textContent =
          `已完成 ${completed}/${total} | 处理中: ${processing} | 失败: ${failed}`;

        // 更新状态 - 智能判断完成状态
        // 如果所有任务都完成了（completed == total 且 total > 0），即使status不是'completed'也认为完成了
        const isActuallyCompleted = (total > 0 && completed >= total && processing === 0);

        if (data.status === 'completed' || isActuallyCompleted) {
          this.updatePhaseStatus(phaseNum, 'success', `✅ 已完成 ${completed}/${total} 任务`);
          console.log(`Phase ${phaseNum} completed: ${completed}/${total} tasks`);
          return;
        } else if (data.status === 'failed') {
          this.updatePhaseStatus(phaseNum, 'error', `❌ 执行失败 (${failed} 个任务失败)`);
          throw new Error('执行失败');
        } else if (data.status === 'running' || data.status === 'processing') {
          this.updatePhaseStatus(phaseNum, 'processing', `⚡ 正在处理... ${completed}/${total}`);
        } else if (data.status === 'idle') {
          // Idle status with tasks - show waiting
          this.updatePhaseStatus(phaseNum, 'processing', `⏳ 准备开始... 0/${total}`);
        }

      } catch (error) {
        console.error(`Poll error (attempt ${attemptCount}):`, error);
        if (attemptCount >= maxAttempts) {
          throw error;
        }
      }

      await this.delay(2000);
    }

    throw new Error('执行超时');
  }

  /**
   * 更新阶段状态
   */
  updatePhaseStatus(phaseNum, type, message) {
    const statusEl = document.getElementById(`phase${phaseNum}Status`);
    statusEl.className = `status-box ${type}`;
    statusEl.textContent = message;
  }

  /**
   * 复制Session ID
   */
  copySessionId(index) {
    const sessionId = this.sessionIds[index];
    navigator.clipboard.writeText(sessionId).then(() => {
      alert(`Session ID已复制: ${sessionId}`);
    });
  }

  /**
   * 导出方法 - 阶段1
   */
  async exportPhase1Input() {
    await this.downloadFile(
      `${this.apiUrl}/api/download/${this.sessionIds[0]}/input`,
      `input_state_${this.sessionIds[0].substring(0, 8)}.xlsx`
    );
  }

  async exportPhase1Tasks() {
    await this.downloadFile(
      `${this.apiUrl}/api/tasks/export/${this.sessionIds[0]}?export_type=tasks`,
      `tasks_${this.sessionIds[0].substring(0, 8)}.xlsx`
    );
  }

  /**
   * 导出方法 - 阶段2
   */
  async exportPhase2Output() {
    await this.downloadFile(
      `${this.apiUrl}/api/download/${this.sessionIds[1]}`,
      `translation_result_${this.sessionIds[1].substring(0, 8)}.xlsx`
    );
  }

  /**
   * 导出方法 - 阶段3 (CAPS Split)
   */
  async exportPhase3Tasks() {
    await this.downloadFile(
      `${this.apiUrl}/api/tasks/export/${this.sessionIds[2]}?export_type=tasks`,
      `caps_tasks_${this.sessionIds[2].substring(0, 8)}.xlsx`
    );
  }

  /**
   * 导出方法 - 阶段4 (CAPS Execute)
   */
  async exportPhase4Output() {
    await this.downloadFile(
      `${this.apiUrl}/api/download/${this.sessionIds[3]}`,
      `final_result_${this.sessionIds[3].substring(0, 8)}.xlsx`
    );
  }

  /**
   * 通用下载方法
   */
  async downloadFile(url, filename) {
    const response = await fetch(url);
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  }

  /**
   * 延迟工具
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// 创建全局实例
const unifiedWorkflowPage = new UnifiedWorkflowPage();
