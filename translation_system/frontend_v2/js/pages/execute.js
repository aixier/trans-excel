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
        this.performance = {
            startTime: null,
            elapsedTime: 0,
            averageSpeed: 0,
            currentSpeed: 0,
            estimatedTime: 0
        };
        this.updateInterval = null;
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

                        <div class="mb-4">
                            <div class="flex justify-between mb-2">
                                <span class="text-2xl font-bold" id="progressPercent">0%</span>
                                <span class="text-sm text-base-content/70">
                                    <span id="completedCount">0</span> / <span id="totalCount">0</span>
                                </span>
                            </div>
                            <progress class="progress progress-primary h-6" id="mainProgress" value="0" max="100"></progress>
                        </div>

                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                                <i class="bi bi-clock"></i>
                                预计剩余: <span id="etaTime" class="font-mono">--:--</span>
                            </div>
                            <div>
                                <i class="bi bi-speedometer2"></i>
                                速度: <span id="speed" class="font-mono">-- 任务/秒</span>
                            </div>
                            <div>
                                <i class="bi bi-hourglass-split"></i>
                                已用时: <span id="elapsedTime" class="font-mono">--:--</span>
                            </div>
                            <div>
                                <i class="bi bi-percent"></i>
                                成功率: <span id="successRate" class="font-mono">--%</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 控制面板 -->
                <div class="card bg-base-100 shadow-xl mb-6">
                    <div class="card-body">
                        <h2 class="card-title mb-4">控制面板</h2>

                        <div class="flex flex-wrap gap-4 mb-4">
                            <button id="startBtn" class="btn btn-primary" onclick="executePage.startExecution()">
                                <i class="bi bi-play-fill"></i>
                                开始执行
                            </button>
                            <button id="pauseBtn" class="btn btn-warning" onclick="executePage.pauseExecution()" disabled>
                                <i class="bi bi-pause-fill"></i>
                                暂停
                            </button>
                            <button id="resumeBtn" class="btn btn-info hidden" onclick="executePage.resumeExecution()">
                                <i class="bi bi-play-fill"></i>
                                继续
                            </button>
                            <button id="stopBtn" class="btn btn-error" onclick="executePage.stopExecution()" disabled>
                                <i class="bi bi-stop-fill"></i>
                                停止
                            </button>

                            <div class="flex-1"></div>

                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text">并发数</span>
                                </label>
                                <select id="maxWorkers" class="select select-bordered select-sm">
                                    <option value="4">4</option>
                                    <option value="8" selected>8</option>
                                    <option value="12">12</option>
                                    <option value="16">16</option>
                                </select>
                            </div>

                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- 实时状态 -->
                    <div class="card bg-base-100 shadow-xl">
                        <div class="card-body">
                            <h3 class="card-title">实时状态</h3>

                            <div class="space-y-3">
                                <div class="flex items-center justify-between">
                                    <span class="flex items-center gap-2">
                                        <span class="badge badge-success badge-lg">✓</span>
                                        完成
                                    </span>
                                    <span class="text-2xl font-bold" id="statusCompleted">0</span>
                                </div>

                                <div class="flex items-center justify-between">
                                    <span class="flex items-center gap-2">
                                        <span class="badge badge-info badge-lg animate-pulse">●</span>
                                        处理中
                                    </span>
                                    <span class="text-2xl font-bold" id="statusProcessing">0</span>
                                </div>

                                <div class="flex items-center justify-between">
                                    <span class="flex items-center gap-2">
                                        <span class="badge badge-lg">○</span>
                                        待处理
                                    </span>
                                    <span class="text-2xl font-bold" id="statusPending">0</span>
                                </div>

                                <div class="flex items-center justify-between">
                                    <span class="flex items-center gap-2">
                                        <span class="badge badge-error badge-lg">✕</span>
                                        失败
                                    </span>
                                    <span class="text-2xl font-bold" id="statusFailed">0</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 性能指标 -->
                    <div class="card bg-base-100 shadow-xl">
                        <div class="card-body">
                            <h3 class="card-title">性能指标</h3>

                            <div class="space-y-3">
                                <div class="flex items-center justify-between">
                                    <span><i class="bi bi-speedometer2"></i> 当前速度</span>
                                    <span class="font-mono" id="currentSpeed">-- 任务/秒</span>
                                </div>

                                <div class="flex items-center justify-between">
                                    <span><i class="bi bi-graph-up"></i> 平均速度</span>
                                    <span class="font-mono" id="avgSpeed">-- 任务/秒</span>
                                </div>

                                <div class="flex items-center justify-between">
                                    <span><i class="bi bi-percent"></i> 成功率</span>
                                    <span class="font-mono" id="perfSuccessRate">--%</span>
                                </div>

                                <div class="flex items-center justify-between">
                                    <span><i class="bi bi-coin"></i> Token消耗</span>
                                    <span class="font-mono" id="tokenUsage">--</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 当前处理任务 -->
                <div class="card bg-base-100 shadow-xl mt-6">
                    <div class="card-body">
                        <h3 class="card-title">
                            当前处理任务
                            <span class="badge badge-primary" id="processingCount">0</span>
                        </h3>

                        <div id="currentTasks" class="space-y-2 max-h-64 overflow-y-auto">
                            <div class="text-center text-base-content/50 py-8">
                                暂无正在处理的任务
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 最近完成 -->
                <div class="card bg-base-100 shadow-xl mt-6">
                    <div class="card-body">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="card-title">最近完成（最新10个）</h3>
                            <button class="btn btn-sm btn-ghost" onclick="executePage.toggleCompletedTasks()">
                                <i class="bi bi-chevron-expand"></i>
                            </button>
                        </div>

                        <div id="recentCompletions" class="space-y-2">
                            <div class="text-center text-base-content/50 py-8">
                                暂无完成的任务
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 失败任务 -->
                <div id="failedSection" class="hidden">
                    <div class="alert alert-error mt-6">
                        <i class="bi bi-exclamation-triangle-fill"></i>
                        <div>
                            <h3 class="font-bold">检测到失败任务</h3>
                            <p>有 <span id="failedCount">0</span> 个任务执行失败</p>
                        </div>
                        <button class="btn btn-sm" onclick="executePage.showFailedTasks()">查看详情</button>
                        <button class="btn btn-sm btn-primary" onclick="executePage.retryFailed()">重试失败任务</button>
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
            // 检查全局执行状态
            let globalStatus;
            try {
                globalStatus = await API.getGlobalExecutionStatus();
            } catch (globalError) {
                // 404 表示没有任何执行记录，这是正常的（第一次使用系统）
                if (globalError.message.includes('Not Found') || globalError.message.includes('404')) {
                    console.log('ℹ️ [checkExecutionStatus] No global execution history - first time use');
                    // 只有在有 sessionId 时才启用开始按钮
                    if (this.sessionId) {
                        document.getElementById('startBtn').disabled = false;
                    }
                    return;
                } else {
                    throw globalError;
                }
            }

            if (globalStatus.is_executing) {
                if (globalStatus.current_session_id === this.sessionId) {
                    // 当前会话正在执行，恢复监控
                    this.resumeMonitoring();
                } else {
                    // 其他会话正在执行
                    this.showExecutionConflict(globalStatus.current_session_id);
                }
            } else {
                // 无任务执行，且有 sessionId，可以开始
                if (this.sessionId) {
                    document.getElementById('startBtn').disabled = false;
                }
            }

            // 获取当前会话状态（可能不存在，这是正常的）
            // 如果刚从拆分页面跳转过来，task_manager可能还在后台保存中，需要重试
            let retryCount = 0;
            const maxRetries = 3;

            while (retryCount < maxRetries) {
                try {
                    const sessionStatus = await API.getExecutionProgress(this.sessionId);
                    this.updateUIFromStatus(sessionStatus);
                    console.log('✅ [checkExecutionStatus] Session status retrieved successfully');
                    break; // 成功获取，退出循环
                } catch (statusError) {
                    // 404 表示还没有执行记录，这是正常的（任务还未开始执行）
                    if (statusError.message.includes('Not Found') || statusError.message.includes('404')) {
                        retryCount++;
                        if (retryCount < maxRetries) {
                            console.log(`ℹ️ [checkExecutionStatus] Session not ready, retrying... (${retryCount}/${maxRetries})`);
                            await new Promise(resolve => setTimeout(resolve, 1000)); // 等待1秒后重试
                        } else {
                            console.log('ℹ️ [checkExecutionStatus] No execution history for this session - not started yet');
                        }
                    } else {
                        throw statusError;  // 其他错误继续抛出
                    }
                }
            }

        } catch (error) {
            console.warn('⚠️ [checkExecutionStatus] Check failed:', error.message);
            // 即使检查失败，也允许用户启动翻译（前提是有 sessionId）
            if (this.sessionId) {
                const startBtn = document.getElementById('startBtn');
                if (startBtn) {
                    startBtn.disabled = false;
                }
            }
        }
    }

    showExecutionConflict(currentSessionId) {
        UIHelper.showDialog({
            type: 'warning',
            title: '无法启动翻译',
            message: '系统当前正在执行其他翻译任务，请等待完成后再试',
            details: `正在执行的会话: ${currentSessionId}`,
            actions: [
                {
                    label: '查看当前任务',
                    className: 'btn-warning',
                    action: () => {
                        window.location.hash = `#/execute/${currentSessionId}`;
                    }
                },
                {
                    label: '等待完成',
                    className: 'btn-primary',
                    action: () => {
                        this.waitForCompletion();
                    }
                }
            ]
        });
    }

    async waitForCompletion() {
        UIHelper.showLoading(true);
        UIHelper.showToast('等待当前任务完成...', 'info', 10000);

        const checkInterval = setInterval(async () => {
            const status = await API.getGlobalExecutionStatus();
            if (!status.is_executing) {
                clearInterval(checkInterval);
                UIHelper.showLoading(false);
                UIHelper.showToast('可以开始执行了！', 'success');
                document.getElementById('startBtn').disabled = false;
            }
        }, 5000);
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
            // 检查全局状态
            const globalStatus = await API.getGlobalExecutionStatus();
            if (globalStatus.is_executing && globalStatus.current_session_id !== this.sessionId) {
                this.showExecutionConflict(globalStatus.current_session_id);
                return;
            }

            // 获取配置
            const options = {
                max_workers: parseInt(document.getElementById('maxWorkers').value),
                provider: 'qwen-plus'  // 固定使用通义千问 qwen-plus
            };

            // 开始执行
            UIHelper.showLoading(true);
            const result = await API.startExecution(this.sessionId, options);

            if (result.status === 'started') {
                this.isExecuting = true;
                this.executionStatus = 'running';
                this.performance.startTime = Date.now();

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

        // 立即执行一次
        this.pollExecutionStatus();

        // 每2秒轮询一次
        this.pollingInterval = setInterval(() => {
            this.pollExecutionStatus();
        }, 2000);
    }

    // 轮询执行状态
    async pollExecutionStatus() {
        try {
            const data = await API.getExecutionProgress(this.sessionId);
            console.log('🔄 [pollExecutionStatus] Received data:', data);

            if (data && data.progress) {
                // 模拟WebSocket消息格式
                this.handleProgressUpdate({
                    type: 'progress',
                    data: data.progress
                });

                // 如果完成，停止轮询
                if (data.progress.completed >= data.progress.total && data.progress.total > 0) {
                    console.log('🔄 [pollExecutionStatus] Task completed, stopping polling');
                    this.stopPolling();
                }
            }
        } catch (error) {
            console.error('🔄 [pollExecutionStatus] Error:', error);
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
            data: message.data,
            hasProgress: !!message.progress,
            progress: message.progress,
            fullMessage: message
        });

        // 处理不同类型的消息
        let progressData = null;

        if (message.type === 'progress' && message.data) {
            // 标准进度更新消息
            progressData = message.data;
        } else if (message.type === 'initial_status' && message.progress) {
            // 初始状态消息
            progressData = message.progress;
            console.log('📥 [handleProgressUpdate] Received initial_status');
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
        // 计算百分比
        const percentage = this.progress.total > 0
            ? Math.round((this.progress.completed / this.progress.total) * 100)
            : 0;

        console.log('🎨 [updateProgressUI] Updating UI:', {
            percentage,
            completed: this.progress.completed,
            total: this.progress.total,
            progress: this.progress
        });

        // 更新主进度
        const progressPercentEl = document.getElementById('progressPercent');
        const mainProgressEl = document.getElementById('mainProgress');
        const completedCountEl = document.getElementById('completedCount');
        const totalCountEl = document.getElementById('totalCount');

        if (progressPercentEl) progressPercentEl.textContent = `${percentage}%`;
        if (mainProgressEl) mainProgressEl.value = percentage;
        if (completedCountEl) completedCountEl.textContent = this.progress.completed;
        if (totalCountEl) totalCountEl.textContent = this.progress.total;

        console.log('🎨 [updateProgressUI] DOM elements:', {
            progressPercent: progressPercentEl?.textContent,
            mainProgress: mainProgressEl?.value,
            completedCount: completedCountEl?.textContent,
            totalCount: totalCountEl?.textContent
        });

        // 更新状态
        document.getElementById('statusCompleted').textContent = this.progress.completed;
        document.getElementById('statusProcessing').textContent = this.progress.processing;
        document.getElementById('statusPending').textContent = this.progress.pending;
        document.getElementById('statusFailed').textContent = this.progress.failed;

        // 更新性能
        const successRate = this.progress.completed > 0
            ? Math.round((this.progress.completed / (this.progress.completed + this.progress.failed)) * 100)
            : 100;

        document.getElementById('successRate').textContent = `${successRate}%`;
        document.getElementById('perfSuccessRate').textContent = `${successRate}%`;

        // 更新速度
        document.getElementById('speed').textContent = `${this.performance.currentSpeed.toFixed(1)} 任务/秒`;
        document.getElementById('currentSpeed').textContent = `${this.performance.currentSpeed.toFixed(1)} 任务/秒`;

        // 更新预计剩余时间
        if (this.performance.estimatedTime > 0) {
            document.getElementById('etaTime').textContent = UIHelper.formatTime(this.performance.estimatedTime);
        }

        // 显示失败任务提示
        if (this.progress.failed > 0) {
            document.getElementById('failedSection').classList.remove('hidden');
            document.getElementById('failedCount').textContent = this.progress.failed;
        }
    }

    startUpdateTimer() {
        this.updateInterval = setInterval(() => {
            if (this.performance.startTime) {
                const elapsed = Math.floor((Date.now() - this.performance.startTime) / 1000);
                document.getElementById('elapsedTime').textContent = UIHelper.formatTime(elapsed);

                // 计算平均速度
                if (elapsed > 0 && this.progress.completed > 0) {
                    const avgSpeed = this.progress.completed / elapsed;
                    document.getElementById('avgSpeed').textContent = `${avgSpeed.toFixed(1)} 任务/秒`;
                }
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

        // 断开WebSocket
        if (this.wsManager) {
            this.wsManager.disconnect();
        }

        // 停止定时器
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        this.updateControlButtons('completed');
        sessionManager.updateStage('completed');

        UIHelper.showDialog({
            type: 'success',
            title: '翻译完成！',
            message: `成功完成 ${this.progress.completed} 个任务，失败 ${this.progress.failed} 个`,
            actions: [
                {
                    label: '查看结果',
                    className: 'btn-primary',
                    action: () => {
                        window.location.hash = `#/complete/${this.sessionId}`;
                    }
                },
                {
                    label: '留在此页',
                    className: 'btn-ghost'
                }
            ]
        });
    }

    updateControlButtons(status) {
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const resumeBtn = document.getElementById('resumeBtn');
        const stopBtn = document.getElementById('stopBtn');

        switch (status) {
            case 'running':
                startBtn.disabled = true;
                pauseBtn.disabled = false;
                resumeBtn.classList.add('hidden');
                pauseBtn.classList.remove('hidden');
                stopBtn.disabled = false;
                break;

            case 'paused':
                startBtn.disabled = true;
                pauseBtn.classList.add('hidden');
                resumeBtn.classList.remove('hidden');
                stopBtn.disabled = false;
                break;

            case 'stopped':
            case 'completed':
                startBtn.disabled = false;
                pauseBtn.disabled = true;
                resumeBtn.classList.add('hidden');
                pauseBtn.classList.remove('hidden');
                stopBtn.disabled = true;
                break;

            default:
                startBtn.disabled = false;
                pauseBtn.disabled = true;
                stopBtn.disabled = true;
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
        const container = document.getElementById('currentTasks');
        document.getElementById('processingCount').textContent = tasks.length;

        if (tasks.length === 0) {
            container.innerHTML = '<div class="text-center text-base-content/50 py-8">暂无正在处理的任务</div>';
            return;
        }

        container.innerHTML = tasks.map(task => `
            <div class="alert alert-info">
                <div class="flex-1">
                    <p class="font-semibold">任务 #${task.task_id} - ${task.target_lang}</p>
                    <p class="text-sm">${task.source_text}</p>
                </div>
                <span class="loading loading-spinner loading-sm"></span>
            </div>
        `).join('');
    }

    updateRecentCompletions(completions) {
        const container = document.getElementById('recentCompletions');

        if (completions.length === 0) {
            container.innerHTML = '<div class="text-center text-base-content/50 py-8">暂无完成的任务</div>';
            return;
        }

        container.innerHTML = completions.map(task => `
            <div class="alert alert-success">
                <i class="bi bi-check-circle-fill"></i>
                <div class="flex-1">
                    <p class="font-semibold">✓ #${task.task_id}</p>
                    <p class="text-sm">"${task.source_text}" → "${task.result}"</p>
                    <p class="text-xs text-base-content/70">
                        置信度: ${task.confidence}% | 耗时: ${(task.duration_ms / 1000).toFixed(1)}秒
                    </p>
                </div>
            </div>
        `).join('');
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
        const container = document.getElementById('recentCompletions');
        container.classList.toggle('max-h-64');
        container.classList.toggle('overflow-y-auto');
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