/**
 * 极简上传页面 - 集成自动化工作流
 *
 * 用户只需两步：
 * 1. 上传文件
 * 2. 选择术语库并确认
 *
 * @author 工程师B
 * @date 2025-10-17
 */

class SimpleUploadPage {
  constructor() {
    this.file = null;
    this.analysis = null;
    this.sessionId = null;
    this.workflowController = null;  // 使用新的顺序控制器
    this.isProcessing = false;  // 防止重复处理的标志

    // 最近项目列表状态
    this.currentPage = 1;
    this.pageSize = 10;
    this.totalSessions = 0;
    this.selectedSessions = new Set();
  }

  /**
   * 初始化页面
   */
  async init() {
    // 初始化组件
    await configConfirmModal.init();

    // 使用新的顺序工作流控制器
    this.workflowController = new SequentialWorkflowController();

    // 设置回调
    this.workflowController.onProgress((progress) => {
      this.updateProgress(progress);
    });

    this.workflowController.onCompletion((result) => {
      this.showCompletion(result);
    });

    this.workflowController.onError((error) => {
      this.handleWorkflowError(error);
    });

    // 新增：阶段完成回调
    this.workflowController.onPhaseComplete((phaseInfo) => {
      this.addPhaseDownloadButton(phaseInfo);
    });

    this.render();
    this.setupEventListeners();
  }

  /**
   * 渲染页面
   */
  render() {
    const container = document.getElementById('app');

    container.innerHTML = `
      <!-- 上传区域 -->
      <div id="upload-section" class="container mx-auto p-6 max-w-3xl">
        <div class="text-center mb-8">
          <h1 class="text-4xl font-bold mb-3">Translation Hub</h1>
          <p class="text-base-content/70">上传Excel文件开始翻译</p>
        </div>

        <!-- 拖拽上传区 -->
        <div id="dropZone"
             class="border-4 border-dashed border-base-300 rounded-2xl p-16 text-center cursor-pointer hover:border-primary hover:bg-primary/5 transition-all duration-300">
          <div class="text-6xl mb-4">📤</div>
          <p class="text-xl font-medium mb-2">拖拽Excel文件到此处</p>
          <p class="text-sm text-base-content/60 mb-4">或</p>
          <button class="btn btn-primary btn-lg gap-2" id="selectFileBtn">
            <i class="bi bi-folder2-open"></i>
            选择文件
          </button>
          <input type="file" id="fileInput" accept=".xlsx,.xls" class="hidden" />
          <p class="text-xs text-base-content/50 mt-4">支持 .xlsx, .xls 格式，最大50MB</p>
        </div>

        <!-- 最近项目 -->
        <div id="recentSection" class="mt-12">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold">最近项目</h2>
            <div class="flex items-center gap-2">
              <button class="btn btn-sm btn-error btn-outline gap-2 hidden" id="batchDeleteBtn" onclick="simpleUploadPage.batchDeleteSessions()">
                <i class="bi bi-trash"></i>
                删除选中 (<span id="selectedCount">0</span>)
              </button>
              <button class="btn btn-sm btn-ghost gap-2" onclick="router.navigate('/sessions')">
                查看全部
                <i class="bi bi-arrow-right"></i>
              </button>
            </div>
          </div>

          <!-- 批量操作工具栏 -->
          <div class="flex items-center gap-2 mb-3 p-2 bg-base-200 rounded-lg">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" class="checkbox checkbox-sm" id="selectAllCheckbox" onchange="simpleUploadPage.toggleSelectAll(this.checked)" />
              <span class="text-sm">全选</span>
            </label>
            <div class="divider divider-horizontal mx-0"></div>
            <span class="text-sm text-base-content/60">共 <span id="totalCount">0</span> 个项目</span>
          </div>

          <div id="recentList" class="space-y-2">
            <!-- 动态填充 -->
          </div>

          <!-- 分页 -->
          <div class="flex justify-center mt-6" id="pagination">
            <!-- 动态填充 -->
          </div>
        </div>
      </div>

      <!-- 配置确认对话框 -->
      <dialog id="configModal" class="modal">
        <div class="modal-box max-w-md">
          <h3 class="font-bold text-lg mb-4">开始翻译</h3>

          <div id="configModalContent">
            <!-- 由 ConfigConfirmModal 渲染 -->
          </div>

          <div class="modal-action">
            <form method="dialog">
              <button class="btn">取消</button>
            </form>
            <button class="btn btn-primary gap-2" id="startProcessBtn">
              <i class="bi bi-rocket-takeoff"></i>
              开始翻译
            </button>
          </div>
        </div>
      </dialog>

      <!-- 进度显示区域 -->
      <div id="progress-section" class="container mx-auto p-6 max-w-4xl hidden">
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title mb-4">
              <span id="progressTitle">处理中...</span>
            </h2>

            <!-- 总体进度 -->
            <div class="mb-6">
              <div class="flex justify-between text-sm mb-2">
                <span id="progressMessage">准备中...</span>
                <span id="progressPercent">0%</span>
              </div>
              <progress id="progressBar" class="progress progress-primary w-full" value="0" max="100"></progress>
            </div>

            <!-- 详细信息 -->
            <div id="progressDetails" class="bg-base-200 rounded-lg p-4 text-sm space-y-2">
              <!-- 动态填充 -->
            </div>

            <!-- 阶段结果下载区域 -->
            <div id="phaseDownloads" class="mt-4 space-y-2">
              <!-- 动态添加各阶段的下载按钮 -->
            </div>

            <!-- 操作按钮 -->
            <div class="card-actions justify-end mt-4">
              <button class="btn btn-sm btn-ghost" id="pauseBtn" disabled>
                <i class="bi bi-pause"></i>
                暂停
              </button>
              <button class="btn btn-sm btn-error" id="cancelBtn">
                <i class="bi bi-x-circle"></i>
                取消
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 完成页面 -->
      <div id="completion-section" class="container mx-auto p-6 max-w-3xl hidden">
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body text-center">
            <div class="text-6xl mb-4">🎉</div>
            <h2 class="card-title text-3xl justify-center mb-2">翻译完成！</h2>

            <div id="completionStats" class="stats shadow mt-6">
              <!-- 动态填充统计信息 -->
            </div>

            <div class="card-actions justify-center mt-8 gap-4">
              <button class="btn btn-primary btn-lg gap-2" id="downloadBtn">
                <i class="bi bi-download"></i>
                立即下载
              </button>
              <button class="btn btn-outline btn-lg gap-2" onclick="location.reload()">
                <i class="bi bi-arrow-repeat"></i>
                处理新文件
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    this.loadRecentProjects();
  }

  /**
   * 设置事件监听
   */
  setupEventListeners() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const selectBtn = document.getElementById('selectFileBtn');

    // 点击选择文件
    selectBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });

    dropZone.addEventListener('click', (e) => {
      if (e.target === dropZone || e.target.closest('.text-6xl')) {
        fileInput.click();
      }
    });

    // 文件选择
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        this.handleFileSelect(e.target.files[0]);
      }
    });

    // 拖拽事件
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
    });

    dropZone.addEventListener('dragenter', () => {
      dropZone.classList.add('border-primary', 'bg-primary/10');
    });

    dropZone.addEventListener('dragleave', (e) => {
      if (e.target === dropZone) {
        dropZone.classList.remove('border-primary', 'bg-primary/10');
      }
    });

    dropZone.addEventListener('drop', (e) => {
      dropZone.classList.remove('border-primary', 'bg-primary/10');
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        this.handleFileSelect(files[0]);
      }
    });
  }

  /**
   * 处理文件选择
   */
  async handleFileSelect(file) {
    // 防止重复处理
    if (this.isProcessing) {
      console.warn('Already processing a file, ignoring duplicate request');
      return;
    }

    // 验证文件
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      alert('仅支持 .xlsx 或 .xls 格式文件');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      alert('文件大小超过50MB限制');
      return;
    }

    this.file = file;
    this.isProcessing = true;  // 设置处理标志

    try {
      // 显示加载状态
      this.showLoading('正在分析文件...');

      // 使用Excel分析器进行本地分析
      // 注意：这里我们使用一个简化的方式 - 直接传递文件给工作流
      // 工作流会在执行时上传并分析

      // 创建一个简化的配置对象供用户确认
      // 注意：实际的文件分析会在工作流上传时由后端自动完成
      // 这里不对CAPS或其他内容做任何假设，完全由后端动态检测
      this.analysis = {
        file_info: {
          filename: file.name,
          sheets: []  // 空数组，不做任何假设
        },
        language_detection: {
          suggested_config: {
            source_lang: 'CH',  // 默认值，用户可在modal中调整
            target_langs: ['EN']  // 默认值，用户可在modal中调整
          }
        },
        statistics: {
          estimated_tasks: 0,  // 未知，显示为"待检测"
          total_cells: 0,
          non_empty_cells: 0
        }
      };

      // 隐藏加载
      this.hideLoading();

      // 显示配置确认对话框
      await configConfirmModal.show(
        this.file,
        this.analysis,
        (config) => this.startWorkflow(config)
      );

    } catch (error) {
      console.error('File preparation failed:', error);
      this.hideLoading();
      this.isProcessing = false;  // 重置处理标志
      alert('准备失败: ' + error.message);
    }
  }

  /**
   * 等待分析完成
   */
  async waitForAnalysis(sessionId) {
    const maxAttempts = 60;
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise(resolve => setTimeout(resolve, 500));

      try {
        const session = await window.api.getSessionDetail(sessionId);
        if (session.metadata && session.metadata.analysis) {
          return;
        }
      } catch (error) {
        // 继续等待
      }
    }
    throw new Error('分析超时');
  }

  /**
   * 开始工作流
   */
  async startWorkflow(config) {
    // 检查是否已在运行
    if (this.workflowController.isRunning()) {
      console.warn('Workflow already running, ignoring duplicate request');
      return;
    }

    // 隐藏上传区，显示进度区
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('progress-section').classList.remove('hidden');

    // 禁用开始按钮（防止重复点击）
    const startBtn = document.getElementById('startProcessBtn');
    if (startBtn) {
      startBtn.disabled = true;
    }

    try {
      // 使用新的顺序控制器执行工作流
      await this.workflowController.execute(this.file, config);

    } catch (error) {
      console.error('Workflow failed:', error);
      this.handleWorkflowError(error);
    } finally {
      // 重置处理标志
      this.isProcessing = false;

      // 重新启用按钮
      if (startBtn) {
        startBtn.disabled = false;
      }
    }
  }

  /**
   * 更新进度
   */
  updateProgress(progress) {
    // 解析进度阶段信息
    const phaseInfo = this.parseProgressPhase(progress);

    // 更新标题显示当前阶段
    document.getElementById('progressTitle').textContent = `${phaseInfo.icon} ${phaseInfo.stageName}`;

    // 更新进度消息
    document.getElementById('progressMessage').textContent = progress.message;
    document.getElementById('progressPercent').textContent = `${progress.percent}%`;
    document.getElementById('progressBar').value = progress.percent;

    // 更新详细信息区域 - 显示阶段信息
    const details = document.getElementById('progressDetails');
    details.innerHTML = this.renderProgressDetails(phaseInfo, progress);
  }

  /**
   * 解析进度阶段信息
   */
  parseProgressPhase(progress) {
    const message = progress.message.toLowerCase();

    // 根据消息内容判断当前阶段
    if (message.includes('上传') || message.includes('upload')) {
      return {
        phase: 1,
        totalPhases: 2,
        stage: '上传文件',
        stageName: '文件上传与分析',
        icon: '📤',
        color: 'text-info'
      };
    } else if (message.includes('拆分') || message.includes('split')) {
      return {
        phase: 1,
        totalPhases: 2,
        stage: '拆分任务',
        stageName: '任务拆分',
        icon: '✂️',
        color: 'text-info'
      };
    } else if (message.includes('翻译') || message.includes('translat') || message.includes('llm')) {
      return {
        phase: 1,
        totalPhases: 2,
        stage: 'AI翻译',
        stageName: 'LLM翻译执行',
        icon: '🤖',
        color: 'text-primary'
      };
    } else if (message.includes('验证') || message.includes('等待完成') || message.includes('wait')) {
      return {
        phase: 1,
        totalPhases: 2,
        stage: '验证完成',
        stageName: '验证翻译完成状态',
        icon: '✓',
        color: 'text-success'
      };
    } else if (message.includes('检测') || message.includes('caps') && message.includes('检')) {
      return {
        phase: '1→2',
        totalPhases: 2,
        stage: 'CAPS检测',
        stageName: '检测是否需要CAPS处理',
        icon: '🔍',
        color: 'text-warning'
      };
    } else if (message.includes('caps') && (message.includes('拆分') || message.includes('split'))) {
      return {
        phase: 2,
        totalPhases: 2,
        stage: 'CAPS拆分',
        stageName: 'CAPS任务拆分',
        icon: '✂️',
        color: 'text-info'
      };
    } else if (message.includes('caps') || message.includes('大写') || message.includes('uppercase')) {
      return {
        phase: 2,
        totalPhases: 2,
        stage: 'CAPS转换',
        stageName: 'CAPS大写转换',
        icon: '🔠',
        color: 'text-primary'
      };
    } else if (message.includes('完成') || message.includes('complete')) {
      return {
        phase: 2,
        totalPhases: 2,
        stage: '完成',
        stageName: '处理完成',
        icon: '🎉',
        color: 'text-success'
      };
    } else {
      return {
        phase: '?',
        totalPhases: 2,
        stage: '处理中',
        stageName: '处理中',
        icon: '⏳',
        color: 'text-base-content'
      };
    }
  }

  /**
   * 渲染进度详细信息
   */
  renderProgressDetails(phaseInfo, progress) {
    let html = '';

    // 阶段标识
    html += `
      <div class="flex items-center gap-3 mb-3 pb-3 border-b border-base-300">
        <span class="text-2xl">${phaseInfo.icon}</span>
        <div class="flex-1">
          <div class="font-semibold ${phaseInfo.color}">
            阶段 ${phaseInfo.phase}/${phaseInfo.totalPhases}: ${phaseInfo.stageName}
          </div>
          <div class="text-xs text-base-content/60 mt-1">
            ${phaseInfo.stage}
          </div>
        </div>
      </div>
    `;

    // 任务详情（如果有）
    if (progress.details) {
      if (progress.details.completed !== undefined) {
        const completionRate = progress.details.total > 0
          ? Math.round((progress.details.completed / progress.details.total) * 100)
          : 0;

        html += `
          <div class="space-y-2">
            <div class="flex justify-between items-center">
              <span class="text-sm">任务进度:</span>
              <span class="font-medium">
                ${progress.details.completed}/${progress.details.total || '--'}
                <span class="text-xs text-base-content/60 ml-1">(${completionRate}%)</span>
              </span>
            </div>
        `;

        if (progress.details.failed > 0) {
          html += `
            <div class="flex justify-between items-center text-error">
              <span class="text-sm">失败任务:</span>
              <span class="font-medium">${progress.details.failed}</span>
            </div>
          `;
        }

        if (progress.details.pending !== undefined) {
          html += `
            <div class="flex justify-between items-center text-base-content/60">
              <span class="text-sm">待处理:</span>
              <span class="font-medium">${progress.details.pending}</span>
            </div>
          `;
        }

        html += `</div>`;
      }

      // Session ID 信息
      if (progress.details.sessionId) {
        html += `
          <div class="mt-3 pt-3 border-t border-base-300">
            <div class="text-xs text-base-content/50">
              Session: ${progress.details.sessionId.substring(0, 12)}...
            </div>
          </div>
        `;
      }
    }

    return html;
  }

  /**
   * 添加阶段下载按钮
   */
  addPhaseDownloadButton(phaseInfo) {
    const container = document.getElementById('phaseDownloads');

    // 检查是否已存在该阶段的按钮
    const existingBtn = container.querySelector(`[data-session-id="${phaseInfo.sessionId}"]`);
    if (existingBtn) {
      return; // 已存在，不重复添加
    }

    // 创建下载按钮组
    const buttonGroup = document.createElement('div');
    buttonGroup.className = 'alert alert-success shadow-sm';
    buttonGroup.setAttribute('data-session-id', phaseInfo.sessionId);

    buttonGroup.innerHTML = `
      <div class="flex-1">
        <h4 class="font-semibold">${phaseInfo.icon} ${phaseInfo.name} - 已完成</h4>
        <p class="text-xs mt-1">Session: ${phaseInfo.sessionId.substring(0, 12)}...</p>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-success" onclick="simpleUploadPage.downloadPhaseResult('${phaseInfo.sessionId}', 'output')">
          <i class="bi bi-download"></i>
          下载结果Excel
        </button>
        <button class="btn btn-sm btn-outline btn-success" onclick="simpleUploadPage.downloadPhaseResult('${phaseInfo.sessionId}', 'dataframe')">
          <i class="bi bi-file-earmark-spreadsheet"></i>
          下载DataFrame
        </button>
      </div>
    `;

    container.appendChild(buttonGroup);
  }

  /**
   * 下载阶段结果
   */
  async downloadPhaseResult(sessionId, type = 'output') {
    try {
      let url, filename;

      if (type === 'output') {
        // 下载转换结果Excel
        url = `${window.API_BASE_URL}/api/download/${sessionId}`;
        filename = `phase_result_${sessionId.substring(0, 8)}.xlsx`;
      } else if (type === 'dataframe') {
        // 下载DataFrame格式
        url = `${window.API_BASE_URL}/api/tasks/export/${sessionId}?export_type=dataframe`;
        filename = `phase_dataframe_${sessionId.substring(0, 8)}.xlsx`;
      }

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`下载失败: ${response.statusText}`);
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);

      this.showToast(`${type === 'output' ? '结果Excel' : 'DataFrame'}下载成功`, 'success');
    } catch (error) {
      console.error('Download failed:', error);
      this.showToast('下载失败: ' + error.message, 'error');
    }
  }

  /**
   * 处理工作流错误
   */
  handleWorkflowError(error) {
    console.error('Workflow error:', error);

    // 显示错误消息
    alert('处理失败: ' + error.message);

    // 返回上传页面
    document.getElementById('upload-section').classList.remove('hidden');
    document.getElementById('progress-section').classList.add('hidden');
    document.getElementById('completion-section').classList.add('hidden');

    // 重置处理标志
    this.isProcessing = false;
  }

  /**
   * 显示完成页面
   */
  async showCompletion(result) {
    document.getElementById('progress-section').classList.add('hidden');
    document.getElementById('completion-section').classList.remove('hidden');

    // 获取最终统计
    try {
      const summary = await window.api.getSummary(result.sessionId);

      document.getElementById('completionStats').innerHTML = `
        <div class="stat">
          <div class="stat-title">总任务</div>
          <div class="stat-value">${summary.total_tasks || 0}</div>
        </div>
        <div class="stat">
          <div class="stat-title">成功</div>
          <div class="stat-value text-success">${summary.successful_tasks || 0}</div>
        </div>
        <div class="stat">
          <div class="stat-title">失败</div>
          <div class="stat-value text-error">${summary.failed_tasks || 0}</div>
        </div>
        <div class="stat">
          <div class="stat-title">耗时</div>
          <div class="stat-value text-sm">${summary.duration || '--'}</div>
        </div>
      `;
    } catch (error) {
      console.warn('Failed to get summary:', error);
    }

    // 设置下载按钮
    document.getElementById('downloadBtn').onclick = () => {
      this.downloadResult(result.sessionId);
    };
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
      a.download = info.filename || `translation_${sessionId.substring(0, 8)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      alert('下载失败: ' + error.message);
    }
  }

  /**
   * 加载最近项目（支持分页）
   */
  async loadRecentProjects() {
    try {
      // 获取所有sessions
      const allSessions = await window.api.getSessions();
      this.totalSessions = allSessions.length;

      // 更新总数显示
      document.getElementById('totalCount').textContent = this.totalSessions;

      // 分页
      const startIndex = (this.currentPage - 1) * this.pageSize;
      const endIndex = startIndex + this.pageSize;
      const sessions = allSessions.slice(startIndex, endIndex);

      const listContainer = document.getElementById('recentList');

      if (this.totalSessions === 0) {
        listContainer.innerHTML = '<p class="text-center text-base-content/50 py-8">暂无最近项目</p>';
        document.getElementById('pagination').innerHTML = '';
        return;
      }

      // 渲染会话列表
      listContainer.innerHTML = sessions.map(session => `
        <div class="flex items-center gap-3 p-3 rounded-lg hover:bg-base-200 transition-colors border border-base-300">
          <!-- 复选框 -->
          <input type="checkbox"
                 class="checkbox checkbox-sm session-checkbox"
                 data-session-id="${session.sessionId}"
                 ${this.selectedSessions.has(session.sessionId) ? 'checked' : ''}
                 onchange="simpleUploadPage.toggleSession('${session.sessionId}', this.checked)" />

          <!-- 文件图标和信息 -->
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <i class="bi bi-file-earmark-excel text-success text-xl flex-shrink-0"></i>
            <div class="flex-1 min-w-0">
              <p class="font-medium text-sm truncate">${session.filename}</p>
              <div class="flex items-center gap-3 text-xs text-base-content/60">
                <span>${this.formatTimeAgo(session.createdAt)}</span>
                <span>•</span>
                <span class="badge badge-sm ${this.getStatusBadgeClass(session.stage)}">${this.getStatusText(session.stage)}</span>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex items-center gap-2 flex-shrink-0">
            ${this.renderSessionActions(session)}
          </div>
        </div>
      `).join('');

      // 渲染分页
      this.renderPagination();

      // 更新选中计数
      this.updateSelectedCount();

    } catch (error) {
      console.error('Failed to load recent projects:', error);
      document.getElementById('recentList').innerHTML =
        '<p class="text-center text-error py-8">加载失败: ' + error.message + '</p>';
    }
  }

  /**
   * 渲染会话操作按钮
   */
  renderSessionActions(session) {
    if (session.stage === 'executing') {
      return `
        <button class="btn btn-sm btn-ghost" onclick="simpleUploadPage.viewSession('${session.sessionId}')">
          <i class="bi bi-eye"></i>
        </button>
      `;
    } else if (session.stage === 'completed') {
      return `
        <button class="btn btn-sm btn-success btn-outline" onclick="simpleUploadPage.downloadSession('${session.sessionId}')">
          <i class="bi bi-download"></i>
        </button>
        <button class="btn btn-sm btn-error btn-ghost" onclick="simpleUploadPage.deleteSingleSession('${session.sessionId}', '${session.filename}')">
          <i class="bi bi-trash"></i>
        </button>
      `;
    } else {
      return `
        <button class="btn btn-sm btn-primary btn-outline" onclick="simpleUploadPage.continueSession('${session.sessionId}')">
          <i class="bi bi-play-fill"></i>
          继续
        </button>
        <button class="btn btn-sm btn-error btn-ghost" onclick="simpleUploadPage.deleteSingleSession('${session.sessionId}', '${session.filename}')">
          <i class="bi bi-trash"></i>
        </button>
      `;
    }
  }

  /**
   * 渲染分页
   */
  renderPagination() {
    const totalPages = Math.ceil(this.totalSessions / this.pageSize);

    if (totalPages <= 1) {
      document.getElementById('pagination').innerHTML = '';
      return;
    }

    const maxVisiblePages = 5;
    let startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    let paginationHTML = '<div class="join">';

    // 上一页
    paginationHTML += `
      <button class="join-item btn btn-sm ${this.currentPage === 1 ? 'btn-disabled' : ''}"
              onclick="simpleUploadPage.goToPage(${this.currentPage - 1})"
              ${this.currentPage === 1 ? 'disabled' : ''}>
        <i class="bi bi-chevron-left"></i>
      </button>
    `;

    // 第一页
    if (startPage > 1) {
      paginationHTML += `
        <button class="join-item btn btn-sm" onclick="simpleUploadPage.goToPage(1)">1</button>
      `;
      if (startPage > 2) {
        paginationHTML += '<button class="join-item btn btn-sm btn-disabled">...</button>';
      }
    }

    // 页码
    for (let i = startPage; i <= endPage; i++) {
      paginationHTML += `
        <button class="join-item btn btn-sm ${i === this.currentPage ? 'btn-active' : ''}"
                onclick="simpleUploadPage.goToPage(${i})">
          ${i}
        </button>
      `;
    }

    // 最后一页
    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        paginationHTML += '<button class="join-item btn btn-sm btn-disabled">...</button>';
      }
      paginationHTML += `
        <button class="join-item btn btn-sm" onclick="simpleUploadPage.goToPage(${totalPages})">${totalPages}</button>
      `;
    }

    // 下一页
    paginationHTML += `
      <button class="join-item btn btn-sm ${this.currentPage === totalPages ? 'btn-disabled' : ''}"
              onclick="simpleUploadPage.goToPage(${this.currentPage + 1})"
              ${this.currentPage === totalPages ? 'disabled' : ''}>
        <i class="bi bi-chevron-right"></i>
      </button>
    `;

    paginationHTML += '</div>';

    document.getElementById('pagination').innerHTML = paginationHTML;
  }

  /**
   * 跳转到指定页
   */
  async goToPage(page) {
    const totalPages = Math.ceil(this.totalSessions / this.pageSize);
    if (page < 1 || page > totalPages) return;

    this.currentPage = page;
    await this.loadRecentProjects();
  }

  /**
   * 切换单个会话的选中状态
   */
  toggleSession(sessionId, checked) {
    if (checked) {
      this.selectedSessions.add(sessionId);
    } else {
      this.selectedSessions.delete(sessionId);
    }
    this.updateSelectedCount();
  }

  /**
   * 全选/取消全选
   */
  toggleSelectAll(checked) {
    const checkboxes = document.querySelectorAll('.session-checkbox');
    checkboxes.forEach(checkbox => {
      const sessionId = checkbox.dataset.sessionId;
      checkbox.checked = checked;
      if (checked) {
        this.selectedSessions.add(sessionId);
      } else {
        this.selectedSessions.delete(sessionId);
      }
    });
    this.updateSelectedCount();
  }

  /**
   * 更新选中计数
   */
  updateSelectedCount() {
    const count = this.selectedSessions.size;
    document.getElementById('selectedCount').textContent = count;

    // 显示/隐藏批量删除按钮
    const batchDeleteBtn = document.getElementById('batchDeleteBtn');
    if (count > 0) {
      batchDeleteBtn.classList.remove('hidden');
    } else {
      batchDeleteBtn.classList.add('hidden');
    }

    // 更新全选复选框状态
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const checkboxes = document.querySelectorAll('.session-checkbox');
    if (checkboxes.length > 0) {
      selectAllCheckbox.checked = checkboxes.length === count;
      selectAllCheckbox.indeterminate = count > 0 && count < checkboxes.length;
    }
  }

  /**
   * 删除单个会话
   */
  async deleteSingleSession(sessionId, filename) {
    const confirmed = confirm(`确认删除项目 "${filename}"？\n\n此操作不可恢复。`);
    if (!confirmed) return;

    try {
      await window.api.deleteSession(sessionId);
      window.api.clearCache();

      this.selectedSessions.delete(sessionId);
      this.showToast('删除成功', 'success');

      // 重新加载列表
      await this.loadRecentProjects();
    } catch (error) {
      console.error('Delete failed:', error);
      this.showToast('删除失败: ' + error.message, 'error');
    }
  }

  /**
   * 批量删除会话
   */
  async batchDeleteSessions() {
    const count = this.selectedSessions.size;
    if (count === 0) return;

    const confirmed = confirm(`确认删除选中的 ${count} 个项目？\n\n此操作不可恢复。`);
    if (!confirmed) return;

    const sessionIds = Array.from(this.selectedSessions);
    let successCount = 0;
    let failCount = 0;

    this.showLoading(`正在删除 ${count} 个项目...`);

    for (const sessionId of sessionIds) {
      try {
        await window.api.deleteSession(sessionId);
        successCount++;
      } catch (error) {
        console.error(`Failed to delete ${sessionId}:`, error);
        failCount++;
      }
    }

    this.hideLoading();
    window.api.clearCache();

    // 清空选中
    this.selectedSessions.clear();

    // 显示结果
    if (failCount === 0) {
      this.showToast(`成功删除 ${successCount} 个项目`, 'success');
    } else {
      this.showToast(`删除完成：成功 ${successCount} 个，失败 ${failCount} 个`, 'warning');
    }

    // 重新加载列表
    await this.loadRecentProjects();
  }

  /**
   * 继续会话
   */
  continueSession(sessionId) {
    console.log('Continue session:', sessionId);
    sessionStorage.setItem('current_session_id', sessionId);
    router.navigate('/config');
  }

  /**
   * 查看会话
   */
  viewSession(sessionId) {
    console.log('View session:', sessionId);
    router.navigate(`/execute/${sessionId}`);
  }

  /**
   * 下载会话结果
   */
  async downloadSession(sessionId) {
    try {
      const blob = await window.api.downloadSession(sessionId);
      const info = await window.api.getDownloadInfo(sessionId);

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = info.filename || `session_${sessionId.substring(0, 8)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      this.showToast('下载成功', 'success');
    } catch (error) {
      console.error('Download failed:', error);
      this.showToast('下载失败: ' + error.message, 'error');
    }
  }

  /**
   * 获取状态徽章样式
   */
  getStatusBadgeClass(stage) {
    const classMap = {
      'created': 'badge-info',
      'split_complete': 'badge-info',
      'executing': 'badge-warning',
      'completed': 'badge-success',
      'failed': 'badge-error'
    };
    return classMap[stage] || 'badge-ghost';
  }

  /**
   * 获取状态文本
   */
  getStatusText(stage) {
    const textMap = {
      'created': '待配置',
      'split_complete': '已配置',
      'executing': '执行中',
      'completed': '已完成',
      'failed': '失败'
    };
    return textMap[stage] || stage;
  }

  /**
   * 显示Toast提示
   */
  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} shadow-lg fixed top-4 right-4 w-auto max-w-md z-50 animate-fade-in`;
    toast.innerHTML = `
      <div>
        <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info-circle'}"></i>
        <span>${message}</span>
      </div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.transition = 'opacity 0.3s';
      toast.style.opacity = '0';
      setTimeout(() => {
        if (toast.parentNode) {
          document.body.removeChild(toast);
        }
      }, 300);
    }, 3000);
  }

  /**
   * 格式化相对时间
   */
  formatTimeAgo(timestamp) {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return '刚刚';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟前`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时前`;
    return `${Math.floor(seconds / 86400)}天前`;
  }

  /**
   * 显示加载状态
   */
  showLoading(message) {
    const toast = document.createElement('div');
    toast.id = 'loading-toast';
    toast.className = 'toast toast-center';
    toast.innerHTML = `
      <div class="alert">
        <span class="loading loading-spinner"></span>
        <span>${message}</span>
      </div>
    `;
    document.body.appendChild(toast);
  }

  /**
   * 隐藏加载状态
   */
  hideLoading() {
    const toast = document.getElementById('loading-toast');
    if (toast) {
      toast.remove();
    }
  }
}

// 创建全局实例
const simpleUploadPage = new SimpleUploadPage();

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SimpleUploadPage;
}
