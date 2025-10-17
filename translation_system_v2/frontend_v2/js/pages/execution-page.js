/**
 * Execution Page - Translation Execution with Advanced Controls
 * Week 2 Day 10: Batch task management, Pause/Resume, Progress tracking
 *
 * Features:
 * - Real-time progress monitoring via WebSocket
 * - Pause/Resume/Stop controls
 * - Batch task management
 * - Task flow visualization
 * - Performance metrics
 * - Error handling and retry
 */

class ExecutionPage {
    constructor() {
        this.sessionId = null;
        this.ws = null;
        this.executionStatus = 'idle'; // idle, running, paused, stopped, completed, failed
        this.stats = {
            total: 0,
            completed: 0,
            failed: 0,
            pending: 0,
            processing: 0
        };
        this.tasks = [];
        this.batches = [];
        this.startTime = null;
        this.pauseTime = null;

        // API configuration
        this.apiBaseURL = window.API_BASE_URL || 'http://localhost:8013';
        this.wsBaseURL = window.WS_BASE_URL || 'ws://localhost:8013';

        // Update intervals
        this.progressUpdateInterval = null;
        this.statsUpdateInterval = null;
    }

    /**
     * Initialize execution page
     */
    async init(sessionId) {
        this.sessionId = sessionId;

        await this.render();
        await this.loadSessionInfo();
        await this.setupWebSocket();
        this.setupControls();
        this.startMonitoring();
    }

    /**
     * Render page structure
     */
    async render() {
        const container = document.getElementById('app');
        if (!container) return;

        container.innerHTML = `
            <div class="execution-page container mx-auto p-6 max-w-7xl">
                <!-- Header -->
                <div class="mb-8">
                    <div class="flex items-center justify-between">
                        <div>
                            <h1 class="text-3xl font-bold mb-2">翻译执行</h1>
                            <p class="text-gray-600" id="session-info">Session: ${this.sessionId}</p>
                        </div>
                        <div class="flex items-center gap-3">
                            <div class="badge badge-lg" id="status-badge">准备中</div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Main Content -->
                    <div class="lg:col-span-2 space-y-6">
                        <!-- Progress Overview -->
                        <div class="card bg-white shadow-lg">
                            <div class="card-body">
                                <h2 class="card-title mb-4">执行进度</h2>

                                <!-- Overall Progress Bar -->
                                <div class="mb-6">
                                    <div class="flex justify-between text-sm mb-2">
                                        <span>总体进度</span>
                                        <span id="overall-progress-text">0%</span>
                                    </div>
                                    <div class="w-full bg-gray-200 rounded-full h-4">
                                        <div id="overall-progress-bar" class="bg-blue-500 h-4 rounded-full transition-all duration-500" style="width: 0%"></div>
                                    </div>
                                </div>

                                <!-- Stats Grid -->
                                <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                                    <div class="text-center p-4 bg-gray-50 rounded-lg">
                                        <div class="text-2xl font-bold text-gray-700" id="stat-total">0</div>
                                        <div class="text-xs text-gray-500 mt-1">总任务数</div>
                                    </div>
                                    <div class="text-center p-4 bg-green-50 rounded-lg">
                                        <div class="text-2xl font-bold text-green-600" id="stat-completed">0</div>
                                        <div class="text-xs text-gray-500 mt-1">已完成</div>
                                    </div>
                                    <div class="text-center p-4 bg-blue-50 rounded-lg">
                                        <div class="text-2xl font-bold text-blue-600" id="stat-processing">0</div>
                                        <div class="text-xs text-gray-500 mt-1">处理中</div>
                                    </div>
                                    <div class="text-center p-4 bg-yellow-50 rounded-lg">
                                        <div class="text-2xl font-bold text-yellow-600" id="stat-pending">0</div>
                                        <div class="text-xs text-gray-500 mt-1">待处理</div>
                                    </div>
                                    <div class="text-center p-4 bg-red-50 rounded-lg">
                                        <div class="text-2xl font-bold text-red-600" id="stat-failed">0</div>
                                        <div class="text-xs text-gray-500 mt-1">失败</div>
                                    </div>
                                </div>

                                <!-- Performance Metrics -->
                                <div class="mt-6 grid grid-cols-3 gap-4 text-sm">
                                    <div class="flex items-center gap-2">
                                        <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <span class="text-gray-600">耗时:</span>
                                        <span class="font-medium" id="elapsed-time">00:00:00</span>
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                        </svg>
                                        <span class="text-gray-600">速度:</span>
                                        <span class="font-medium" id="processing-speed">0 tasks/min</span>
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <span class="text-gray-600">预计剩余:</span>
                                        <span class="font-medium" id="estimated-remaining">--:--:--</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Control Panel -->
                        <div class="card bg-white shadow-lg">
                            <div class="card-body">
                                <h2 class="card-title mb-4">执行控制</h2>
                                <div class="flex flex-wrap gap-3" id="control-buttons">
                                    <button id="start-btn" class="btn btn-primary">
                                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        开始执行
                                    </button>
                                    <button id="pause-btn" class="btn btn-warning hidden">
                                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        暂停
                                    </button>
                                    <button id="resume-btn" class="btn btn-success hidden">
                                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                        </svg>
                                        继续
                                    </button>
                                    <button id="stop-btn" class="btn btn-error hidden">
                                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                                        </svg>
                                        停止
                                    </button>
                                    <button id="retry-failed-btn" class="btn btn-outline hidden">
                                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                        </svg>
                                        重试失败任务
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- Task Flow View -->
                        <div class="card bg-white shadow-lg">
                            <div class="card-body">
                                <div class="flex items-center justify-between mb-4">
                                    <h2 class="card-title">任务流</h2>
                                    <div class="flex gap-2">
                                        <button class="btn btn-sm btn-ghost" id="filter-all">全部</button>
                                        <button class="btn btn-sm btn-ghost" id="filter-processing">处理中</button>
                                        <button class="btn btn-sm btn-ghost" id="filter-failed">失败</button>
                                    </div>
                                </div>
                                <div id="task-flow" class="max-h-96 overflow-y-auto space-y-2"></div>
                            </div>
                        </div>
                    </div>

                    <!-- Sidebar -->
                    <div class="space-y-6">
                        <!-- Batch Information -->
                        <div class="card bg-white shadow-lg sticky top-6">
                            <div class="card-body">
                                <h2 class="card-title text-lg mb-4">批次信息</h2>
                                <div id="batch-info" class="space-y-3"></div>
                            </div>
                        </div>

                        <!-- Recent Errors -->
                        <div class="card bg-red-50 border-2 border-red-200">
                            <div class="card-body">
                                <h2 class="card-title text-lg mb-4 text-red-700">最近错误</h2>
                                <div id="recent-errors" class="space-y-2 text-sm max-h-48 overflow-y-auto"></div>
                            </div>
                        </div>

                        <!-- Actions -->
                        <div class="card bg-white shadow-lg">
                            <div class="card-body">
                                <h2 class="card-title text-lg mb-4">操作</h2>
                                <div class="space-y-2">
                                    <button id="download-results-btn" class="btn btn-outline btn-sm w-full" disabled>
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                        下载结果
                                    </button>
                                    <button id="view-summary-btn" class="btn btn-outline btn-sm w-full" disabled>
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                        </svg>
                                        查看摘要
                                    </button>
                                    <button id="export-log-btn" class="btn btn-outline btn-sm w-full">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                        </svg>
                                        导出日志
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- WebSocket Connection Status -->
            <div id="ws-status" class="fixed bottom-4 right-4 px-4 py-2 rounded-full text-white text-sm hidden">
                WebSocket 连接中...
            </div>
        `;
    }

    /**
     * Load session information
     */
    async loadSessionInfo() {
        try {
            const response = await fetch(`${this.apiBaseURL}/api/execute/status/${this.sessionId}`);
            const data = await response.json();

            this.stats = {
                total: data.total || 0,
                completed: data.completed || 0,
                failed: data.failed || 0,
                pending: data.pending || 0,
                processing: data.processing || 0
            };

            this.updateStats();
        } catch (error) {
            console.error('Failed to load session info:', error);
            this.showError('加载会话信息失败');
        }
    }

    /**
     * Setup WebSocket connection for real-time updates
     */
    async setupWebSocket() {
        if (this.ws) {
            this.ws.close();
        }

        try {
            this.ws = new WebSocket(`${this.wsBaseURL}/api/websocket/progress/${this.sessionId}`);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.showWSStatus('已连接', 'success');
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showWSStatus('连接错误', 'error');
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.showWSStatus('已断开', 'warning');

                // Attempt reconnect if execution is still running
                if (this.executionStatus === 'running') {
                    setTimeout(() => this.setupWebSocket(), 5000);
                }
            };

        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
            this.showError('WebSocket 连接失败');
        }
    }

    /**
     * Handle WebSocket messages
     */
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'progress':
                this.updateProgress(data.payload);
                break;

            case 'task_completed':
                this.onTaskCompleted(data.payload);
                break;

            case 'task_failed':
                this.onTaskFailed(data.payload);
                break;

            case 'batch_completed':
                this.onBatchCompleted(data.payload);
                break;

            case 'execution_completed':
                this.onExecutionCompleted(data.payload);
                break;

            case 'execution_failed':
                this.onExecutionFailed(data.payload);
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    }

    /**
     * Setup control buttons
     */
    setupControls() {
        // Start button
        document.getElementById('start-btn')?.addEventListener('click', () => {
            this.startExecution();
        });

        // Pause button
        document.getElementById('pause-btn')?.addEventListener('click', () => {
            this.pauseExecution();
        });

        // Resume button
        document.getElementById('resume-btn')?.addEventListener('click', () => {
            this.resumeExecution();
        });

        // Stop button
        document.getElementById('stop-btn')?.addEventListener('click', () => {
            this.stopExecution();
        });

        // Retry failed button
        document.getElementById('retry-failed-btn')?.addEventListener('click', () => {
            this.retryFailedTasks();
        });

        // Filter buttons
        document.getElementById('filter-all')?.addEventListener('click', () => {
            this.filterTasks('all');
        });
        document.getElementById('filter-processing')?.addEventListener('click', () => {
            this.filterTasks('processing');
        });
        document.getElementById('filter-failed')?.addEventListener('click', () => {
            this.filterTasks('failed');
        });

        // Download results
        document.getElementById('download-results-btn')?.addEventListener('click', () => {
            this.downloadResults();
        });

        // View summary
        document.getElementById('view-summary-btn')?.addEventListener('click', () => {
            this.viewSummary();
        });

        // Export log
        document.getElementById('export-log-btn')?.addEventListener('click', () => {
            this.exportLog();
        });
    }

    /**
     * Start execution
     */
    async startExecution() {
        try {
            const response = await fetch(`${this.apiBaseURL}/api/execute/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId })
            });

            if (!response.ok) {
                throw new Error('Failed to start execution');
            }

            this.executionStatus = 'running';
            this.startTime = Date.now();
            this.updateControlButtons();
            this.updateStatusBadge();
            this.showSuccess('执行已开始');

        } catch (error) {
            console.error('Failed to start execution:', error);
            this.showError('启动执行失败');
        }
    }

    /**
     * Pause execution
     */
    async pauseExecution() {
        try {
            const response = await fetch(`${this.apiBaseURL}/api/execute/pause/${this.sessionId}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error('Failed to pause execution');
            }

            this.executionStatus = 'paused';
            this.pauseTime = Date.now();
            this.updateControlButtons();
            this.updateStatusBadge();
            this.showSuccess('执行已暂停');

        } catch (error) {
            console.error('Failed to pause execution:', error);
            this.showError('暂停执行失败');
        }
    }

    /**
     * Resume execution
     */
    async resumeExecution() {
        try {
            const response = await fetch(`${this.apiBaseURL}/api/execute/resume/${this.sessionId}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error('Failed to resume execution');
            }

            this.executionStatus = 'running';
            this.pauseTime = null;
            this.updateControlButtons();
            this.updateStatusBadge();
            this.showSuccess('执行已继续');

        } catch (error) {
            console.error('Failed to resume execution:', error);
            this.showError('恢复执行失败');
        }
    }

    /**
     * Stop execution
     */
    async stopExecution() {
        if (!confirm('确定要停止执行吗？已完成的任务会保留，但未完成的任务将被取消。')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseURL}/api/execute/stop/${this.sessionId}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error('Failed to stop execution');
            }

            this.executionStatus = 'stopped';
            this.updateControlButtons();
            this.updateStatusBadge();
            this.showSuccess('执行已停止');

            if (this.ws) {
                this.ws.close();
            }

        } catch (error) {
            console.error('Failed to stop execution:', error);
            this.showError('停止执行失败');
        }
    }

    /**
     * Retry failed tasks
     */
    async retryFailedTasks() {
        try {
            const response = await fetch(`${this.apiBaseURL}/api/execute/retry/${this.sessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error('Failed to retry tasks');
            }

            this.showSuccess('正在重试失败的任务...');

        } catch (error) {
            console.error('Failed to retry tasks:', error);
            this.showError('重试失败');
        }
    }

    /**
     * Update progress
     */
    updateProgress(data) {
        this.stats = {
            total: data.total || this.stats.total,
            completed: data.completed || this.stats.completed,
            failed: data.failed || this.stats.failed,
            pending: data.pending || this.stats.pending,
            processing: data.processing || this.stats.processing
        };

        this.updateStats();
        this.updatePerformanceMetrics();
    }

    /**
     * Update statistics display
     */
    updateStats() {
        document.getElementById('stat-total').textContent = this.stats.total;
        document.getElementById('stat-completed').textContent = this.stats.completed;
        document.getElementById('stat-processing').textContent = this.stats.processing;
        document.getElementById('stat-pending').textContent = this.stats.pending;
        document.getElementById('stat-failed').textContent = this.stats.failed;

        // Update progress bar
        const progress = this.stats.total > 0 ? (this.stats.completed / this.stats.total) * 100 : 0;
        document.getElementById('overall-progress-bar').style.width = `${progress}%`;
        document.getElementById('overall-progress-text').textContent = `${Math.round(progress)}%`;

        // Show retry button if there are failed tasks
        if (this.stats.failed > 0) {
            document.getElementById('retry-failed-btn')?.classList.remove('hidden');
        }
    }

    /**
     * Update performance metrics
     */
    updatePerformanceMetrics() {
        if (!this.startTime) return;

        const elapsed = Date.now() - this.startTime;
        document.getElementById('elapsed-time').textContent = this.formatDuration(elapsed);

        // Calculate processing speed
        const minutes = elapsed / 60000;
        const speed = minutes > 0 ? Math.round(this.stats.completed / minutes) : 0;
        document.getElementById('processing-speed').textContent = `${speed} tasks/min`;

        // Estimate remaining time
        const remaining = this.stats.total - this.stats.completed;
        if (speed > 0 && remaining > 0) {
            const estimatedMinutes = remaining / speed;
            document.getElementById('estimated-remaining').textContent = this.formatDuration(estimatedMinutes * 60000);
        }
    }

    /**
     * Update control buttons based on execution status
     */
    updateControlButtons() {
        const startBtn = document.getElementById('start-btn');
        const pauseBtn = document.getElementById('pause-btn');
        const resumeBtn = document.getElementById('resume-btn');
        const stopBtn = document.getElementById('stop-btn');

        // Hide all first
        [startBtn, pauseBtn, resumeBtn, stopBtn].forEach(btn => btn?.classList.add('hidden'));

        switch (this.executionStatus) {
            case 'idle':
                startBtn?.classList.remove('hidden');
                break;

            case 'running':
                pauseBtn?.classList.remove('hidden');
                stopBtn?.classList.remove('hidden');
                break;

            case 'paused':
                resumeBtn?.classList.remove('hidden');
                stopBtn?.classList.remove('hidden');
                break;

            case 'stopped':
            case 'completed':
            case 'failed':
                // No control buttons for these states
                break;
        }
    }

    /**
     * Update status badge
     */
    updateStatusBadge() {
        const badge = document.getElementById('status-badge');
        if (!badge) return;

        const statusConfig = {
            idle: { text: '准备中', class: 'badge-info' },
            running: { text: '执行中', class: 'badge-primary' },
            paused: { text: '已暂停', class: 'badge-warning' },
            stopped: { text: '已停止', class: 'badge-error' },
            completed: { text: '已完成', class: 'badge-success' },
            failed: { text: '执行失败', class: 'badge-error' }
        };

        const config = statusConfig[this.executionStatus];
        if (config) {
            badge.textContent = config.text;
            badge.className = `badge badge-lg ${config.class}`;
        }
    }

    /**
     * Handle task completed event
     */
    onTaskCompleted(task) {
        console.log('Task completed:', task);
        // Update task in UI
        this.updateTaskInFlow(task);
    }

    /**
     * Handle task failed event
     */
    onTaskFailed(task) {
        console.log('Task failed:', task);
        this.updateTaskInFlow(task);
        this.addRecentError(task);
    }

    /**
     * Handle batch completed event
     */
    onBatchCompleted(batch) {
        console.log('Batch completed:', batch);
        this.updateBatchInfo();
    }

    /**
     * Handle execution completed event
     */
    onExecutionCompleted(data) {
        this.executionStatus = 'completed';
        this.updateControlButtons();
        this.updateStatusBadge();
        this.showSuccess('执行完成！');

        // Enable download buttons
        document.getElementById('download-results-btn')?.removeAttribute('disabled');
        document.getElementById('view-summary-btn')?.removeAttribute('disabled');

        if (this.ws) {
            this.ws.close();
        }
    }

    /**
     * Handle execution failed event
     */
    onExecutionFailed(data) {
        this.executionStatus = 'failed';
        this.updateControlButtons();
        this.updateStatusBadge();
        this.showError('执行失败：' + (data.error || '未知错误'));

        if (this.ws) {
            this.ws.close();
        }
    }

    /**
     * Update task in task flow view
     */
    updateTaskInFlow(task) {
        // TODO: Implement task flow visualization
    }

    /**
     * Filter tasks in task flow
     */
    filterTasks(filter) {
        // TODO: Implement task filtering
        console.log('Filter tasks:', filter);
    }

    /**
     * Update batch information
     */
    async updateBatchInfo() {
        const container = document.getElementById('batch-info');
        if (!container) return;

        try {
            const response = await fetch(`${this.apiBaseURL}/api/execute/batches/${this.sessionId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch batch info');
            }

            const data = await response.json();

            container.innerHTML = `
                <div class="text-sm space-y-2">
                    <div class="flex justify-between">
                        <span class="text-gray-600">总批次:</span>
                        <span class="font-medium">${data.total || 0}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">已完成:</span>
                        <span class="font-medium text-green-600">${data.completed || 0}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">处理中:</span>
                        <span class="font-medium text-blue-600">${data.processing || 0}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">待处理:</span>
                        <span class="font-medium">${data.pending || 0}</span>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Failed to update batch info:', error);
            container.innerHTML = `
                <div class="text-sm text-gray-500">
                    <p>无法加载批次信息</p>
                </div>
            `;
        }
    }

    /**
     * Add recent error to error list
     */
    addRecentError(task) {
        const container = document.getElementById('recent-errors');
        if (!container) return;

        const errorDiv = document.createElement('div');
        errorDiv.className = 'p-2 bg-white rounded border border-red-200 text-xs';
        errorDiv.innerHTML = `
            <div class="font-medium text-red-700">Task ${task.task_id}</div>
            <div class="text-gray-600 mt-1">${task.error || '未知错误'}</div>
        `;

        container.prepend(errorDiv);

        // Keep only last 5 errors
        while (container.children.length > 5) {
            container.removeChild(container.lastChild);
        }
    }

    /**
     * Download results
     */
    async downloadResults() {
        try {
            window.location.href = `${this.apiBaseURL}/api/download/${this.sessionId}`;
            this.showSuccess('开始下载结果文件');
        } catch (error) {
            console.error('Failed to download results:', error);
            this.showError('下载失败');
        }
    }

    /**
     * View summary
     */
    async viewSummary() {
        try {
            window.location.hash = `#/result?session=${this.sessionId}`;
        } catch (error) {
            console.error('Failed to view summary:', error);
            this.showError('查看摘要失败');
        }
    }

    /**
     * Export execution log
     */
    exportLog() {
        const log = {
            sessionId: this.sessionId,
            status: this.executionStatus,
            stats: this.stats,
            startTime: this.startTime,
            endTime: Date.now(),
            duration: Date.now() - this.startTime
        };

        const blob = new Blob([JSON.stringify(log, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `execution_log_${this.sessionId}_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);

        this.showSuccess('日志已导出');
    }

    /**
     * Start monitoring updates
     */
    startMonitoring() {
        // Update performance metrics every second
        this.statsUpdateInterval = setInterval(() => {
            if (this.executionStatus === 'running') {
                this.updatePerformanceMetrics();
            }
        }, 1000);
    }

    /**
     * Stop monitoring
     */
    stopMonitoring() {
        if (this.statsUpdateInterval) {
            clearInterval(this.statsUpdateInterval);
        }
    }

    /**
     * Show WebSocket status
     */
    showWSStatus(message, type) {
        const status = document.getElementById('ws-status');
        if (!status) return;

        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };

        status.className = `fixed bottom-4 right-4 px-4 py-2 rounded-full text-white text-sm ${colors[type] || colors.info}`;
        status.textContent = message;
        status.classList.remove('hidden');

        setTimeout(() => status.classList.add('hidden'), 3000);
    }

    /**
     * Utility: Format duration
     */
    formatDuration(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);

        const h = String(hours).padStart(2, '0');
        const m = String(minutes % 60).padStart(2, '0');
        const s = String(seconds % 60).padStart(2, '0');

        return `${h}:${m}:${s}`;
    }

    /**
     * Utility: Show success message
     */
    showSuccess(message) {
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 3000);
    }

    /**
     * Utility: Show error message
     */
    showError(message) {
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 5000);
    }

    /**
     * Cleanup on page leave
     */
    destroy() {
        this.stopMonitoring();

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Export for global access
if (typeof window !== 'undefined') {
    window.ExecutionPage = ExecutionPage;
}
