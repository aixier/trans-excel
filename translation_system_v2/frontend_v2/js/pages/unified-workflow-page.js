/**
 * 统一工作流页面 - 整合三个测试页面的进度条
 *
 * 功能：
 * - 阶段1: 上传文件并拆分任务 (来自 1_upload_and_split.html)
 * - 阶段2: 执行翻译 (来自 2_execute_transformation.html)
 * - 阶段3: CAPS转换 (来自 4_caps_transformation.html，可选)
 *
 * @author Claude
 * @date 2025-10-17
 */

class UnifiedWorkflowPage {
  constructor() {
    this.apiUrl = window.API_BASE_URL || 'http://localhost:8013';
    this.file = null;
    this.sessionIds = [];  // 存储各阶段的session ID
    this.pollIntervals = [];  // 存储轮询定时器
  }

  async init() {
    this.render();
    this.setupEventListeners();
  }

  render() {
    const container = document.getElementById('app');

    container.innerHTML = `
      <style>
        /* 复用测试页面的样式 */
        .phase-container {
          background: white;
          border-radius: 8px;
          padding: 25px;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
          margin-bottom: 20px;
        }
        .phase-header {
          border-bottom: 2px solid #667eea;
          padding-bottom: 10px;
          margin-bottom: 20px;
        }
        .phase-1 .phase-header { border-color: #667eea; color: #667eea; }
        .phase-2 .phase-header { border-color: #ff6b6b; color: #ff6b6b; }
        .phase-3 .phase-header { border-color: #f093fb; color: #f093fb; }

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
      <div class="container mx-auto p-6 max-w-5xl">
        <div class="text-center mb-8">
          <h1 class="text-4xl font-bold mb-3">🚀 统一工作流</h1>
          <p class="text-base-content/70">上传Excel文件，自动完成翻译和CAPS转换</p>
        </div>

        <!-- 文件上传 -->
        <div class="phase-container phase-1">
          <h2 class="phase-header text-xl font-bold">📤 文件上传</h2>

          <div class="form-control mb-4">
            <label class="label"><span class="label-text font-semibold">选择Excel文件</span></label>
            <input type="file" id="fileInput" accept=".xlsx,.xls" class="file-input file-input-bordered w-full" />
          </div>

          <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="form-control">
              <label class="label"><span class="label-text">Source Language</span></label>
              <select id="sourceLang" class="select select-bordered">
                <option value="CH">中文 (CH)</option>
                <option value="EN">英文 (EN)</option>
              </select>
            </div>
            <div class="form-control">
              <label class="label"><span class="label-text">Target Languages</span></label>
              <input type="text" id="targetLangs" value="EN" placeholder="EN,JP,PT" class="input input-bordered" />
            </div>
          </div>

          <button id="startBtn" class="btn btn-primary w-full" onclick="unifiedWorkflowPage.startWorkflow()">
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

          <div id="phase1Exports" style="display: none;">
            <button class="export-btn" onclick="unifiedWorkflowPage.exportPhase1Input()">
              📄 导出拆分前Excel
            </button>
            <button class="export-btn" onclick="unifiedWorkflowPage.exportPhase1Tasks()">
              📋 导出任务表
            </button>
          </div>
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
            <button class="export-btn" onclick="unifiedWorkflowPage.exportPhase2DataFrame()">
              📊 导出DataFrame
            </button>
          </div>
        </div>

        <!-- 阶段3: CAPS转换 (可选) -->
        <div id="phase3Container" class="phase-container phase-3" style="display: none;">
          <h2 class="phase-header text-xl font-bold">🔠 阶段3: CAPS转换</h2>

          <div class="progress-bar-container">
            <div id="phase3Progress" class="progress-fill" style="width: 0%">0%</div>
          </div>
          <div id="phase3Text" class="text-sm text-gray-600 mb-2"></div>

          <div id="phase3Status" class="status-box pending">检测中...</div>

          <div id="phase3SessionId" class="session-id-display" style="display: none;" onclick="unifiedWorkflowPage.copySessionId(2)">
            Session ID: <span id="phase3SessionValue"></span>
          </div>

          <div id="phase3Exports" style="display: none;">
            <button class="export-btn" onclick="unifiedWorkflowPage.exportPhase3Output()">
              📄 导出最终结果Excel
            </button>
            <button class="export-btn" onclick="unifiedWorkflowPage.exportPhase3DataFrame()">
              📊 导出DataFrame
            </button>
          </div>
        </div>

        <!-- 完成页面 -->
        <div id="completionContainer" class="phase-container" style="display: none; text-align: center;">
          <div class="text-6xl mb-4">🎉</div>
          <h2 class="text-3xl font-bold mb-2">工作流完成！</h2>
          <p class="text-gray-600 mb-4">所有阶段已成功完成</p>
          <button class="btn btn-primary btn-lg" onclick="location.reload()">
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
   * 开始工作流
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
      // 显示阶段1和阶段2容器
      document.getElementById('phase1Container').style.display = 'block';
      document.getElementById('phase2Container').style.display = 'block';

      // 执行阶段1: 上传并拆分
      await this.executePhase1();

      // 执行阶段2: 翻译
      await this.executePhase2();

      // 检测并执行阶段3: CAPS (可选)
      await this.checkAndExecutePhase3();

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
   * 阶段1: 上传并拆分任务 (来自 1_upload_and_split.html)
   */
  async executePhase1() {
    this.updatePhaseStatus(1, 'processing', '⏳ 正在上传文件并拆分任务...');

    // 验证并获取目标语言
    const targetLangsInput = document.getElementById('targetLangs').value.trim();
    if (!targetLangsInput) {
      throw new Error('请输入目标语言（例如：EN 或 EN,TH,TW）');
    }
    const targetLangs = targetLangsInput.split(',').map(s => s.trim()).filter(s => s.length > 0);
    if (targetLangs.length === 0) {
      throw new Error('请输入有效的目标语言代码');
    }

    const formData = new FormData();
    formData.append('file', this.file);
    formData.append('target_langs', JSON.stringify(targetLangs));
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

    // 轮询拆分状态
    await this.pollSplitStatus(sessionId);

    this.updatePhaseStatus(1, 'success', `✅ 拆分完成！任务数: ${data.task_count || 0}`);
    document.getElementById('phase1Exports').style.display = 'block';
  }

  /**
   * 阶段2: 执行翻译 (来自 2_execute_transformation.html)
   */
  async executePhase2() {
    const sessionId = this.sessionIds[0];
    this.updatePhaseStatus(2, 'processing', '⏳ 正在执行AI翻译...');

    const response = await fetch(`${this.apiUrl}/api/execute/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        processor: 'llm_qwen',
        max_workers: 10
      })
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
   * 检测并执行阶段3: CAPS转换 (来自 4_caps_transformation.html)
   */
  async checkAndExecutePhase3() {
    const parentSessionId = this.sessionIds[0];

    // 检测是否需要CAPS
    this.updatePhaseStatus(3, 'processing', '🔍 检测是否需要CAPS转换...');
    document.getElementById('phase3Container').style.display = 'block';

    const sessionResponse = await fetch(`${this.apiUrl}/api/sessions/detail/${parentSessionId}`);
    const session = await sessionResponse.json();
    const sheets = session.metadata?.analysis?.file_info?.sheets || [];
    const hasCaps = sheets.some(sheet => sheet.toLowerCase().includes('caps'));

    if (!hasCaps) {
      this.updatePhaseStatus(3, 'success', '✅ 无需CAPS转换，工作流完成');
      return;
    }

    // 执行CAPS转换
    this.updatePhaseStatus(3, 'processing', '⏳ 正在拆分CAPS任务...');

    // 拆分CAPS任务 - 需要包含 target_langs
    const targetLangsInput = document.getElementById('targetLangs').value.trim();
    if (!targetLangsInput) {
      throw new Error('请输入目标语言（CAPS阶段需要）');
    }
    const targetLangs = targetLangsInput.split(',').map(s => s.trim()).filter(s => s.length > 0);
    if (targetLangs.length === 0) {
      throw new Error('请输入有效的目标语言代码');
    }

    const splitFormData = new FormData();
    splitFormData.append('parent_session_id', parentSessionId);
    splitFormData.append('target_langs', JSON.stringify(targetLangs));  // ✅ 添加 target_langs
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

    // 等待拆分完成
    await this.pollSplitStatus(capsSessionId);

    // 执行CAPS转换
    this.updatePhaseStatus(3, 'processing', '⏳ 正在执行CAPS大写转换...');

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
    await this.pollExecutionStatus(capsSessionId, 3);

    this.updatePhaseStatus(3, 'success', `✅ CAPS转换完成！`);
    document.getElementById('phase3Exports').style.display = 'block';
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
          return;
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

        const stats = data.statistics || {};
        const byStatus = stats.by_status || {};
        const total = stats.total || 0;
        const completed = byStatus.completed || 0;
        const processing = byStatus.processing || 0;
        const failed = byStatus.failed || 0;
        const progress = total > 0 ? Math.round((completed / total) * 100) : 0;

        // 更新进度条
        document.getElementById(`phase${phaseNum}Progress`).style.width = `${progress}%`;
        document.getElementById(`phase${phaseNum}Progress`).textContent = `${progress}%`;
        document.getElementById(`phase${phaseNum}Text`).textContent =
          `已完成 ${completed}/${total} | 处理中: ${processing} | 失败: ${failed}`;

        // 更新状态
        if (data.status === 'completed') {
          this.updatePhaseStatus(phaseNum, 'success', `✅ 已完成 ${completed}/${total} 任务`);
          return;
        } else if (data.status === 'failed') {
          this.updatePhaseStatus(phaseNum, 'error', `❌ 执行失败 (${failed} 个任务失败)`);
          throw new Error('执行失败');
        } else if (data.status === 'running' || data.status === 'processing') {
          this.updatePhaseStatus(phaseNum, 'processing', `⚡ 正在处理... ${completed}/${total}`);
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

  async exportPhase2DataFrame() {
    await this.downloadFile(
      `${this.apiUrl}/api/tasks/export/${this.sessionIds[1]}?export_type=dataframe`,
      `dataframe_${this.sessionIds[1].substring(0, 8)}.xlsx`
    );
  }

  /**
   * 导出方法 - 阶段3
   */
  async exportPhase3Output() {
    await this.downloadFile(
      `${this.apiUrl}/api/download/${this.sessionIds[2]}`,
      `final_result_${this.sessionIds[2].substring(0, 8)}.xlsx`
    );
  }

  async exportPhase3DataFrame() {
    await this.downloadFile(
      `${this.apiUrl}/api/tasks/export/${this.sessionIds[2]}?export_type=dataframe`,
      `caps_dataframe_${this.sessionIds[2].substring(0, 8)}.xlsx`
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
