// 翻译执行页
class ExecutePage {
    constructor() {
        this.sessionId = null;
        this.wsManager = null;
        this.isExecuting = false;
        this.executionStatus = 'idle';
        this.progress = {
            total: 0,
            completed: 0,
            processing: 0,
            pending: 0,
            failed: 0
        };
        this.batches = {
            total: 0,
            completed: 0,
            failed: 0
        };
        this.performance = {
            startTime: null,
            elapsedTime: 0,
            averageSpeed: 0,
            currentSpeed: 0,
            estimatedTime: 0
        };
        this.updateInterval = null;
        this.pollingInterval = null;
        this.polling404Count = 0;
    }

    render(sessionId) {
        // 验证 sessionId 参数
        if (!sessionId) {
            UIHelper.showToast('缺少会话ID，请重新上传文件', 'error');
            router.navigate('/create');
            return;
        }

        this.sessionId = sessionId;

        if (!sessionManager.loadSession(sessionId)) {
            UIHelper.showToast('会话不存在或已过期', 'error');
            router.navigate('/create');
            return;
        }

        const html = `
            <div class="max-w-7xl mx-auto">
                <!-- 页面标题 -->
                <div class="text-center mb-6">
                    <h1 class="text-3xl font-bold mb-2">翻译执行中心</h1>
                    <p class="text-base-content/70">Session: ${sessionId}</p>
                    <p class="text-sm text-base-content/50">${sessionManager.session.filename}</p>
                </div>

                <!-- 总体进度 -->
                <div class="card bg-base-100 shadow-xl mb-6">
                    <div class="card-body">
                        <h2 class="card-title mb-4">总体进度</h2>

                        <!-- 任务进度 -->
                        <div class="mb-4">
                            <div class="flex justify-between mb-2">
                                <div>
                                    <span class="text-sm text-base-content/50">任务进度</span>
                                    <span class="text-2xl font-bold ml-2" id="progressPercent">0%</span>
                                </div>
                                <span class="text-sm text-base-content/70">
                                    <span id="completedCount">0</span> / <span id="totalCount">0</span> 任务
                                </span>
                            </div>
                            <progress class="progress progress-primary h-4" id="mainProgress" value="0" max="100"></progress>
                        </div>

                        <!-- 批次进度 -->
                        <div class="mb-4">
                            <div class="flex justify-between mb-2">
                                <div>
                                    <span class="text-sm text-base-content/50">批次进度</span>
                                    <span class="text-2xl font-bold ml-2 text-secondary" id="batchPercent">0%</span>
                                </div>
                                <span class="text-sm text-base-content/70">
                                    <span id="batchCompleted">0</span> / <span id="batchTotal">0</span> 批次
                                    <span class="ml-2 text-xs badge badge-ghost">LLM请求</span>
                                </span>
                            </div>
                            <progress class="progress progress-secondary h-4" id="batchProgress" value="0" max="100"></progress>
                        </div>

                        <!-- 控制按钮 -->
                        <div class="flex flex-wrap gap-3">
                            <button id="startBtn" class="btn btn-primary btn-sm" onclick="executePage.startExecution()">
                                <i class="bi bi-play-fill"></i>
                                开始执行
                            </button>
                            <button id="pauseBtn" class="btn btn-warning btn-sm" onclick="executePage.pauseExecution()" disabled>
                                <i class="bi bi-pause-fill"></i>
                                暂停
                            </button>
                            <button id="resumeBtn" class="btn btn-info btn-sm hidden" onclick="executePage.resumeExecution()">
                                <i class="bi bi-play-fill"></i>
                                继续
                            </button>
                            <button id="stopBtn" class="btn btn-error btn-sm" onclick="executePage.stopExecution()" disabled>
                                <i class="bi bi-stop-fill"></i>
                                停止
                            </button>
                            <button id="downloadBtn" class="btn btn-success btn-sm hidden" onclick="executePage.downloadResult()">
                                <i class="bi bi-download"></i>
                                下载结果
                            </button>
                            <button id="newTaskBtn" class="btn btn-outline btn-sm hidden" onclick="executePage.startNewTask()">
                                <i class="bi bi-plus-circle"></i>
                                翻译新文件
                            </button>

                            <div class="flex-1"></div>

                            <div class="form-control">
                                <label class="label py-0">
                                    <span class="label-text text-xs">并发数</span>
                                </label>
                                <select id="maxWorkers" class="select select-bordered select-xs">
                                    <option value="4">4</option>
                                    <option value="8" selected>8</option>
                                    <option value="12">12</option>
                                    <option value="16">16</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 进度统计 - 简洁显示 -->
                <div class="flex items-center justify-center gap-8 py-4">
                    <div class="text-center">
                        <div class="text-3xl font-bold text-success" id="statusCompleted">0</div>
                        <div class="text-sm text-base-content/70">已完成</div>
                    </div>
                    <div class="divider divider-horizontal"></div>
                    <div class="text-center">
                        <div class="text-3xl font-bold text-base-content/50" id="statusPending">0</div>
                        <div class="text-sm text-base-content/70">待处理</div>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('pageContent').innerHTML = html;

        // 更新全局进度
        UIHelper.updateGlobalProgress(3);
        sessionManager.updateStage('executing');

        // 初始化
        this.checkExecutionStatus();
    }

    async checkExecutionStatus() {
        try {
            // 首先获取任务统计，包含批次总数
            try {
                const taskStatus = await API.getTaskStatus(this.sessionId);
                console.log('📊 [checkExecutionStatus] Task status:', taskStatus);

                // 更新批次总数
                if (taskStatus.batch_count) {
                    this.batches.total = taskStatus.batch_count;
                    console.log('📦 [checkExecutionStatus] Batch total:', this.batches.total);
                }

                // 更新任务统计（从任务状态中恢复）
                if (taskStatus.statistics && taskStatus.statistics.total) {
                    this.progress.total = taskStatus.statistics.total;
                    this.progress.pending = taskStatus.statistics.by_status?.pending || 0;
                    this.progress.completed = taskStatus.statistics.by_status?.completed || 0;
                    this.progress.failed = taskStatus.statistics.by_status?.failed || 0;
                    this.progress.processing = taskStatus.statistics.by_status?.processing || 0;
                    this.updateProgressUI();
                }
            } catch (taskError) {
                console.warn('⚠️ [checkExecutionStatus] Failed to get task status:', taskError);
            }

            // 尝试获取执行进度，如果404说明任务未开始
            try {
                const sessionStatus = await API.getExecutionProgress(this.sessionId);

                // 如果成功获取到状态，说明任务已经开始过
                this.updateUIFromStatus(sessionStatus);
                console.log('✅ [checkExecutionStatus] Session has execution history');

                // 根据状态决定按钮状态
                if (sessionStatus.status === 'running' || sessionStatus.status === 'initializing') {
                    // 正在执行，恢复监控，禁用开始按钮
                    this.isExecuting = true;
                    this.executionStatus = sessionStatus.status;
                    this.updateControlButtons(sessionStatus.status);
                    this.startPolling();  // ✅ 修复：调用startPolling而不是startMonitoring
                    this.connectWebSocket();  // 同时连接WebSocket
                    console.log('🔄 [checkExecutionStatus] Resumed monitoring for running session');
                } else if (sessionStatus.status === 'completed' || sessionStatus.status === 'stopped') {
                    // ✅ FIX: 已完成或已停止，保持进度显示100%
                    this.isExecuting = false;
                    this.executionStatus = sessionStatus.status;

                    // 如果是completed状态，确保批次进度也是100%
                    if (sessionStatus.status === 'completed' && this.batches.total > 0) {
                        this.batches.completed = this.batches.total;
                    }

                    this.updateProgressUI();  // ✅ 更新UI显示100%
                    this.updateControlButtons(sessionStatus.status);
                    document.getElementById('startBtn').disabled = false;
                } else {
                    // 其他状态，启用开始按钮
                    document.getElementById('startBtn').disabled = false;
                }
            } catch (statusError) {
                // 404 表示任务从未执行过，这是正常的
                if (statusError.message.includes('Not Found') || statusError.message.includes('404') || statusError.message.includes('not found')) {
                    console.log('ℹ️ [checkExecutionStatus] No execution history - task not started yet');

                    // 任务未开始，直接启用开始按钮
                    if (this.sessionId) {
                        document.getElementById('startBtn').disabled = false;
                    }
                } else {
                    // 其他错误，也允许用户尝试开始
                    console.warn('⚠️ [checkExecutionStatus] Error checking status:', statusError.message);
                    if (this.sessionId) {
                        document.getElementById('startBtn').disabled = false;
                    }
                }
            }

        } catch (error) {
            console.warn('⚠️ [checkExecutionStatus] Unexpected error:', error.message);
            // 即使检查失败，也允许用户启动翻译
            if (this.sessionId) {
                const startBtn = document.getElementById('startBtn');
                if (startBtn) {
                    startBtn.disabled = false;
                }
            }
        }
    }

    async startExecution() {
        if (this.isExecuting) return;

        // 验证 sessionId 是否存在
        if (!this.sessionId) {
            UIHelper.showToast('会话ID不存在，请重新上传文件', 'error');
            router.navigate('/create');
            return;
        }

        try {
            // 获取配置
            const options = {
                max_workers: parseInt(document.getElementById('maxWorkers').value),
                provider: 'qwen-plus'  // 固定使用通义千问 qwen-plus
            };

            // 开始执行
            UIHelper.showLoading(true);
            const result = await API.startExecution(this.sessionId, options);

            // ✅ 支持两种状态：'started'（旧版）和'running'（新版）
            if (result.status === 'started' || result.status === 'running') {
                this.isExecuting = true;
                this.executionStatus = 'running';
                this.performance.startTime = Date.now();

                // 如果响应包含progress，立即更新UI
                if (result.progress) {
                    this.handleProgressUpdate({
                        type: 'progress',
                        data: result.progress
                    });
                    console.log('✅ [startExecution] Initial progress:', result.progress);
                }

                // 更新UI
                this.updateControlButtons('running');

                // 🔄 像测试页面一样：先启动HTTP轮询，确保进度更新
                console.log('🔄 [startExecution] Starting HTTP polling first');
                this.startPolling();

                // 然后尝试WebSocket连接（成功后会停止轮询）
                this.connectWebSocket();

                // 开始定时更新
                this.startUpdateTimer();

                UIHelper.showToast('翻译执行已启动', 'success');
            }

        } catch (error) {
            UIHelper.showToast(`启动失败：${error.message}`, 'error');
        } finally {
            UIHelper.showLoading(false);
        }
    }

    // 🔄 启动HTTP轮询（参考测试页面实现）
    startPolling() {
        // 清除旧的轮询
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        console.log('🔄 [startPolling] Starting HTTP polling every 2 seconds');

        // ⏱️ 延迟500ms后开始轮询，给后端时间初始化 ProgressTracker
        setTimeout(() => {
            this.pollExecutionStatus();

            // 每2秒轮询一次
            this.pollingInterval = setInterval(() => {
                this.pollExecutionStatus();
            }, 2000);
        }, 500);
    }

    // 轮询执行状态
    async pollExecutionStatus() {
        try {
            const data = await API.getExecutionProgress(this.sessionId);
            console.log('🔄 [pollExecutionStatus] Received data:', data);

            // 重置404计数器（成功获取数据）
            this.polling404Count = 0;

            if (data && data.progress) {
                // 模拟WebSocket消息格式，传递完整数据（包括batches）
                this.handleProgressUpdate({
                    type: 'progress',
                    data: data  // ✅ 传递完整data，包含progress和batches
                });

                // 如果完成，停止轮询
                if (data.progress.completed >= data.progress.total && data.progress.total > 0) {
                    console.log('🔄 [pollExecutionStatus] Task completed, stopping polling');
                    this.stopPolling();
                }
            }
        } catch (error) {
            // 🔧 增强错误容错 - 处理后端初始化延迟
            if (error.message && (error.message.includes('Session not found') || error.message.includes('404') || error.message.includes('Not Found'))) {
                // 初始化404计数器
                if (!this.polling404Count) {
                    this.polling404Count = 0;
                }
                this.polling404Count++;

                console.log(`ℹ️ [pollExecutionStatus] Session not found (${this.polling404Count}/5) - backend may be initializing`);

                // 如果WebSocket正常工作，忽略HTTP 404
                if (this.wsManager && this.wsManager.ws?.readyState === WebSocket.OPEN) {
                    console.log('ℹ️ [pollExecutionStatus] WebSocket active, continuing to poll');
                    return;
                }

                // 连续5次404才停止轮询（给后端足够初始化时间）
                if (this.polling404Count >= 5) {
                    console.error('❌ [pollExecutionStatus] Session not found after 5 attempts, stopping polling');
                    this.stopPolling();
                    UIHelper.showToast('会话已过期，请刷新页面', 'error');
                }
            } else {
                console.error('🔄 [pollExecutionStatus] Error:', error);
            }
        }
    }

    // 停止轮询
    stopPolling() {
        if (this.pollingInterval) {
            console.log('🔄 [stopPolling] Stopping HTTP polling');
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    connectWebSocket() {
        console.log('🔌 [connectWebSocket] Connecting for session:', this.sessionId);

        if (this.wsManager) {
            this.wsManager.disconnect();
        }

        this.wsManager = new WebSocketManager(this.sessionId);
        this.wsManager.connect((message) => {
            console.log('🔌 [connectWebSocket] Message callback triggered');

            // WebSocket成功接收消息，可以停止HTTP轮询
            if (message.type === 'progress') {
                console.log('🔌 [connectWebSocket] WebSocket is working, stopping HTTP polling');
                this.stopPolling();
            }

            this.handleProgressUpdate(message);
        });
    }

    handleProgressUpdate(message) {
        // 🔍 添加调试日志
        console.log('🔍 [handleProgressUpdate] Received message:', {
            type: message.type,
            hasData: !!message.data,
            fullMessage: message
        });

        // 🔧 FIX: 统一处理消息格式，支持两种数据结构
        let progressData = null;
        let fullData = null;

        if (message.type === 'progress' && message.data) {
            // 标准进度更新消息
            fullData = message.data;
            // 检查是否是嵌套结构 {progress: {...}, batches: {...}}
            progressData = message.data.progress || message.data;
        } else if (message.type === 'initial_status' && message.data) {
            // 初始状态消息（已统一为 'data' 键）
            fullData = message.data;
            progressData = message.data.progress || message.data;
            console.log('📥 [handleProgressUpdate] Received initial_status');
        } else if (message.type === 'initial_status' && message.progress) {
            // 兼容旧格式（可在后续版本移除）
            progressData = message.progress;
            fullData = message;
            console.warn('⚠️ [handleProgressUpdate] Received old format initial_status');
        }

        if (progressData) {
            console.log('✅ [handleProgressUpdate] Progress data:', {
                completed: progressData.completed,
                total: progressData.total,
                completion_rate: progressData.completion_rate,
                processing: progressData.processing,
                pending: progressData.pending,
                failed: progressData.failed
            });

            // 更新进度数据
            this.progress = {
                total: progressData.total || this.progress.total,
                completed: progressData.completed || 0,
                processing: progressData.processing || 0,
                pending: progressData.pending || 0,
                failed: progressData.failed || 0
            };

            // 更新批次数据（支持两种来源）
            if (fullData && fullData.batches) {
                this.batches = {
                    total: fullData.batches.total || this.batches.total,
                    completed: fullData.batches.completed || 0,
                    failed: fullData.batches.failed || 0
                };
                console.log('📦 [handleProgressUpdate] Updated batches:', this.batches);
            }

            console.log('📊 [handleProgressUpdate] Updated this.progress:', this.progress);

            // 更新性能数据
            if (progressData.rate) {
                this.performance.currentSpeed = progressData.rate;
            }
            if (progressData.eta_seconds) {
                this.performance.estimatedTime = progressData.eta_seconds;
            }

            // 更新UI
            this.updateProgressUI();

            // 检查是否完成
            if (this.progress.completed + this.progress.failed >= this.progress.total && this.progress.total > 0) {
                console.log('🎉 [handleProgressUpdate] Execution complete!');
                this.handleExecutionComplete();
            }
        } else {
            console.warn('⚠️ [handleProgressUpdate] Message ignored:', {
                type: message.type,
                hasData: !!message.data,
                hasProgress: !!message.progress,
                reason: 'No progress data found'
            });
        }
    }

    updateProgressUI() {
        // 计算任务百分比
        const percentage = this.progress.total > 0
            ? Math.round((this.progress.completed / this.progress.total) * 100)
            : 0;

        // 计算批次百分比
        const batchPercentage = this.batches.total > 0
            ? Math.round((this.batches.completed / this.batches.total) * 100)
            : 0;

        console.log('🎨 [updateProgressUI] Updating UI:', {
            taskPercentage: percentage,
            batchPercentage: batchPercentage,
            completed: this.progress.completed,
            total: this.progress.total,
            batches: this.batches
        });

        // 更新任务进度
        const progressPercentEl = document.getElementById('progressPercent');
        const mainProgressEl = document.getElementById('mainProgress');
        const completedCountEl = document.getElementById('completedCount');
        const totalCountEl = document.getElementById('totalCount');

        if (progressPercentEl) progressPercentEl.textContent = `${percentage}%`;
        if (mainProgressEl) mainProgressEl.value = percentage;
        if (completedCountEl) completedCountEl.textContent = this.progress.completed;
        if (totalCountEl) totalCountEl.textContent = this.progress.total;

        // 更新批次进度
        const batchPercentEl = document.getElementById('batchPercent');
        const batchProgressEl = document.getElementById('batchProgress');
        const batchCompletedEl = document.getElementById('batchCompleted');
        const batchTotalEl = document.getElementById('batchTotal');

        if (batchPercentEl) batchPercentEl.textContent = `${batchPercentage}%`;
        if (batchProgressEl) batchProgressEl.value = batchPercentage;
        if (batchCompletedEl) batchCompletedEl.textContent = this.batches.completed;
        if (batchTotalEl) batchTotalEl.textContent = this.batches.total;

        console.log('🎨 [updateProgressUI] DOM elements:', {
            progressPercent: progressPercentEl?.textContent,
            mainProgress: mainProgressEl?.value,
            completedCount: completedCountEl?.textContent,
            totalCount: totalCountEl?.textContent,
            batchPercent: batchPercentEl?.textContent,
            batchProgress: batchProgressEl?.value
        });

        // 更新状态 - 只更新已完成和待处理
        const completedEl = document.getElementById('statusCompleted');
        const pendingEl = document.getElementById('statusPending');

        if (completedEl) completedEl.textContent = this.progress.completed;
        if (pendingEl) pendingEl.textContent = this.progress.pending;
    }

    startUpdateTimer() {
        this.updateInterval = setInterval(() => {
            if (this.performance.startTime) {
                // 定时器保留用于其他可能的更新需求
            }
        }, 1000);
    }

    async pauseExecution() {
        if (!this.isExecuting) return;

        try {
            await API.pauseExecution(this.sessionId);
            this.executionStatus = 'paused';
            this.updateControlButtons('paused');
            UIHelper.showToast('执行已暂停', 'warning');
        } catch (error) {
            UIHelper.showToast(`暂停失败：${error.message}`, 'error');
        }
    }

    async resumeExecution() {
        if (this.executionStatus !== 'paused') return;

        try {
            await API.resumeExecution(this.sessionId);
            this.executionStatus = 'running';
            this.updateControlButtons('running');
            UIHelper.showToast('执行已继续', 'success');
        } catch (error) {
            UIHelper.showToast(`继续失败：${error.message}`, 'error');
        }
    }

    async stopExecution() {
        if (!this.isExecuting) return;

        UIHelper.showDialog({
            type: 'warning',
            title: '确认停止',
            message: '确定要停止翻译执行吗？当前进度将保留。',
            actions: [
                {
                    label: '确定停止',
                    className: 'btn-error',
                    action: async () => {
                        try {
                            await API.stopExecution(this.sessionId);
                            this.handleExecutionStop();
                        } catch (error) {
                            UIHelper.showToast(`停止失败：${error.message}`, 'error');
                        }
                    }
                },
                {
                    label: '取消',
                    className: 'btn-ghost'
                }
            ]
        });
    }

    handleExecutionStop() {
        this.isExecuting = false;
        this.executionStatus = 'stopped';

        // 断开WebSocket
        if (this.wsManager) {
            this.wsManager.disconnect();
        }

        // 停止定时器
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        this.updateControlButtons('stopped');
        UIHelper.showToast('执行已停止', 'warning');
    }

    handleExecutionComplete() {
        this.isExecuting = false;
        this.executionStatus = 'completed';

        // ✅ FIX: 确保批次进度显示100%
        if (this.batches.total > 0) {
            this.batches.completed = this.batches.total;
        }

        // 最后更新一次UI，确保显示100%
        this.updateProgressUI();

        // 断开WebSocket
        if (this.wsManager) {
            this.wsManager.disconnect();
        }

        // 停止定时器
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        // 停止轮询
        this.stopPolling();

        this.updateControlButtons('completed');
        sessionManager.updateStage('completed');

        // 翻译完成 - 不显示弹窗，用户可以从UI上看到完成状态
        console.log(`✅ 翻译完成: 成功 ${this.progress.completed} 个，失败 ${this.progress.failed} 个`);
        console.log(`📦 批次完成: ${this.batches.completed} / ${this.batches.total}`);
    }

    updateControlButtons(status) {
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const resumeBtn = document.getElementById('resumeBtn');
        const stopBtn = document.getElementById('stopBtn');
        const downloadBtn = document.getElementById('downloadBtn');
        const newTaskBtn = document.getElementById('newTaskBtn');

        switch (status) {
            case 'running':
                if (startBtn) startBtn.disabled = true;
                if (pauseBtn) pauseBtn.disabled = false;
                if (resumeBtn) resumeBtn.classList.add('hidden');
                if (pauseBtn) pauseBtn.classList.remove('hidden');
                if (stopBtn) stopBtn.disabled = false;
                if (downloadBtn) downloadBtn.classList.add('hidden');
                if (newTaskBtn) newTaskBtn.classList.add('hidden');
                break;

            case 'paused':
                if (startBtn) startBtn.disabled = true;
                if (pauseBtn) pauseBtn.classList.add('hidden');
                if (resumeBtn) resumeBtn.classList.remove('hidden');
                if (stopBtn) stopBtn.disabled = false;
                if (downloadBtn) downloadBtn.classList.add('hidden');
                if (newTaskBtn) newTaskBtn.classList.add('hidden');
                break;

            case 'stopped':
                if (startBtn) startBtn.disabled = false;
                if (pauseBtn) pauseBtn.disabled = true;
                if (resumeBtn) resumeBtn.classList.add('hidden');
                if (pauseBtn) pauseBtn.classList.remove('hidden');
                if (stopBtn) stopBtn.disabled = true;
                if (downloadBtn) downloadBtn.classList.add('hidden');
                if (newTaskBtn) newTaskBtn.classList.add('hidden');
                break;

            case 'completed':
                // ✅ 完成后：开始执行变灰色，显示下载和新任务按钮
                if (startBtn) {
                    startBtn.disabled = true;
                    startBtn.classList.add('btn-disabled');
                }
                if (pauseBtn) pauseBtn.disabled = true;
                if (resumeBtn) resumeBtn.classList.add('hidden');
                if (pauseBtn) pauseBtn.classList.remove('hidden');
                if (stopBtn) stopBtn.disabled = true;
                if (downloadBtn) downloadBtn.classList.remove('hidden');
                if (newTaskBtn) newTaskBtn.classList.remove('hidden');
                break;

            default:
                if (startBtn) startBtn.disabled = false;
                if (pauseBtn) pauseBtn.disabled = true;
                if (stopBtn) stopBtn.disabled = true;
                if (downloadBtn) downloadBtn.classList.add('hidden');
                if (newTaskBtn) newTaskBtn.classList.add('hidden');
        }
    }

    async resumeMonitoring() {
        this.isExecuting = true;
        this.executionStatus = 'running';

        // 获取当前状态
        const status = await API.getExecutionProgress(this.sessionId);
        this.updateUIFromStatus(status);

        // 建立WebSocket连接
        this.connectWebSocket();

        // 开始定时更新
        this.startUpdateTimer();

        this.updateControlButtons('running');
    }

    updateUIFromStatus(status) {
        if (status.progress) {
            this.progress = status.progress;
        }

        // 更新批次数据
        if (status.batches) {
            this.batches = {
                total: status.batches.total || 0,
                completed: status.batches.completed || 0,
                failed: status.batches.failed || 0
            };
        }

        // 统一更新UI
        if (status.progress || status.batches) {
            this.updateProgressUI();
        }

        // 更新当前任务
        if (status.current_tasks && status.current_tasks.length > 0) {
            this.updateCurrentTasks(status.current_tasks);
        }

        // 更新最近完成
        if (status.recent_completions && status.recent_completions.length > 0) {
            this.updateRecentCompletions(status.recent_completions);
        }
    }

    updateCurrentTasks(tasks) {
        // 已简化：不再显示当前处理任务详情
        // UI已优化为只显示统计数字
    }

    updateRecentCompletions(completions) {
        // 已简化：不再显示最近完成任务详情
        // UI已优化为只显示统计数字
    }

    showFailedTasks() {
        // TODO: 显示失败任务详情
        UIHelper.showToast('失败任务详情功能开发中...', 'info');
    }

    async retryFailed() {
        // TODO: 重试失败任务
        UIHelper.showToast('重试功能开发中...', 'info');
    }

    toggleCompletedTasks() {
        // 已简化：不再显示最近完成任务列表
    }

    async downloadResult() {
        if (!this.sessionId) {
            UIHelper.showToast('会话ID不存在', 'error');
            return;
        }

        try {
            UIHelper.showLoading(true, '正在生成下载文件...');

            // 调用下载API
            const headers = {};
            // 添加认证token（如果存在）
            if (typeof authManager !== 'undefined') {
                const token = authManager.getToken();
                if (token) {
                    headers['Authorization'] = `Bearer ${token}`;
                }
            }

            const response = await fetch(`/api/download/${this.sessionId}`, {
                method: 'GET',
                headers: headers
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '下载失败');
            }

            // 获取文件名
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'translated.xlsx';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                    // 解码URL编码的文件名
                    filename = decodeURIComponent(filename);
                }
            }

            // 下载文件
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            UIHelper.showToast('下载成功！', 'success');
            console.log(`✅ Downloaded: ${filename}`);

        } catch (error) {
            console.error('Download error:', error);
            UIHelper.showToast(`下载失败：${error.message}`, 'error');
        } finally {
            UIHelper.showLoading(false);
        }
    }

    startNewTask() {
        // ✅ FIX: 重置进度状态（新翻译时清零）
        this.progress = {
            total: 0,
            completed: 0,
            processing: 0,
            pending: 0,
            failed: 0
        };
        this.batches = {
            total: 0,
            completed: 0,
            failed: 0
        };
        this.isExecuting = false;
        this.executionStatus = 'idle';

        // 清理当前会话
        sessionManager.clearSession();
        // 跳转到上传页面
        router.navigate('/create');
        UIHelper.showToast('开始新的翻译任务', 'info');
    }

    cleanup() {
        if (this.wsManager) {
            this.wsManager.disconnect();
        }
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        // 停止HTTP轮询
        this.stopPolling();
    }
}

// 创建页面实例
const executePage = new ExecutePage();