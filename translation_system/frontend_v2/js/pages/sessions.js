// Session列表管理页
class SessionsPage {
    constructor() {
        this.sessions = [];
        this.refreshInterval = null;
    }

    async render() {
        const html = `
            <div class="max-w-7xl mx-auto">
                <!-- 页面标题 -->
                <div class="flex justify-between items-center mb-6">
                    <div>
                        <h1 class="text-3xl font-bold">我的翻译任务</h1>
                        <p class="text-base-content/70 mt-1">管理所有翻译会话</p>
                    </div>
                    <div class="flex gap-2">
                        <button class="btn btn-ghost" onclick="router.navigate('/glossary')">
                            <i class="bi bi-book"></i>
                            术语管理
                        </button>
                        <button class="btn btn-primary" onclick="router.navigate('/create')">
                            <i class="bi bi-plus-circle"></i>
                            新建翻译
                        </button>
                    </div>
                </div>

                <!-- 筛选和刷新 -->
                <div class="flex gap-4 mb-6">
                    <div class="tabs tabs-boxed">
                        <a class="tab tab-active" onclick="sessionsPage.filterSessions('all')">全部</a>
                        <a class="tab" onclick="sessionsPage.filterSessions('running')">
                            <i class="bi bi-play-circle-fill text-success"></i>
                            运行中
                        </a>
                        <a class="tab" onclick="sessionsPage.filterSessions('completed')">
                            <i class="bi bi-check-circle-fill text-primary"></i>
                            已完成
                        </a>
                        <a class="tab" onclick="sessionsPage.filterSessions('stopped')">
                            <i class="bi bi-pause-circle-fill text-warning"></i>
                            已停止
                        </a>
                    </div>

                    <div class="flex-1"></div>

                    <button class="btn btn-ghost btn-sm" onclick="sessionsPage.refreshList()">
                        <i class="bi bi-arrow-clockwise"></i>
                        刷新
                    </button>
                </div>

                <!-- Session列表 -->
                <div id="sessionsList" class="space-y-4 max-h-[calc(100vh-280px)] overflow-y-auto pr-2">
                    <div class="text-center py-12">
                        <span class="loading loading-spinner loading-lg"></span>
                        <p class="mt-4 text-base-content/70">加载中...</p>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('pageContent').innerHTML = html;

        // 加载sessions
        await this.loadSessions();

        // 启动自动刷新（每5秒）
        this.startAutoRefresh();
    }

    async loadSessions(filter = 'all') {
        try {
            const response = await fetch(
                `${APP_CONFIG.API_BASE_URL}/api/sessions/list?status=${filter}`,
                {
                    headers: {
                        'Authorization': `Bearer ${authManager.getToken()}`
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to load sessions');
            }

            const data = await response.json();
            this.sessions = data.sessions || [];
            this.displaySessions();

        } catch (error) {
            logger.error('Failed to load sessions:', error);
            UIHelper.showToast('加载会话列表失败', 'error');
            this.displayError();
        }
    }

    displaySessions() {
        const container = document.getElementById('sessionsList');

        if (this.sessions.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <i class="bi bi-inbox text-6xl text-base-content/30"></i>
                    <p class="mt-4 text-base-content/70">暂无翻译任务</p>
                    <button class="btn btn-primary mt-4" onclick="router.navigate('/create')">
                        <i class="bi bi-plus-circle"></i>
                        创建新任务
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = this.sessions.map(session => this.renderSessionCard(session)).join('');
    }

    renderSessionCard(session) {
        const statusBadge = this.getStatusBadge(session.status);
        const progressPercent = session.progress?.percentage || 0;
        const isRunning = session.is_running;

        return `
            <div class="card bg-base-100 shadow-xl ${isRunning ? 'border-2 border-success' : ''}">
                <div class="card-body">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <h3 class="card-title">
                                ${session.filename}
                                ${isRunning ? '<span class="loading loading-spinner loading-xs ml-2"></span>' : ''}
                            </h3>
                            <p class="text-sm text-base-content/50 mt-1">
                                会话ID: ${session.session_id.substring(0, 8)}...
                            </p>
                        </div>
                        <div>
                            ${statusBadge}
                        </div>
                    </div>

                    <!-- 进度条 -->
                    ${session.has_tasks ? `
                        <div class="mt-4">
                            <div class="flex justify-between text-sm mb-2">
                                <span>翻译进度</span>
                                <span class="font-mono">
                                    ${session.progress.completed} / ${session.progress.total}
                                    (${progressPercent.toFixed(1)}%)
                                </span>
                            </div>
                            <progress class="progress progress-primary" value="${progressPercent}" max="100"></progress>

                            <!-- 状态统计 -->
                            <div class="flex gap-4 mt-2 text-xs">
                                <span class="text-success">✓ 完成: ${session.progress.completed}</span>
                                ${session.progress.processing > 0 ?
                                    `<span class="text-info">⏳ 处理中: ${session.progress.processing}</span>` : ''}
                                ${session.progress.failed > 0 ?
                                    `<span class="text-error">✗ 失败: ${session.progress.failed}</span>` : ''}
                                <span class="text-base-content/50">○ 待处理: ${session.progress.pending}</span>
                            </div>
                        </div>
                    ` : `
                        <div class="alert alert-warning mt-4">
                            <i class="bi bi-exclamation-triangle"></i>
                            <span>任务尚未拆分</span>
                        </div>
                    `}

                    <!-- 操作按钮 -->
                    <div class="card-actions justify-end mt-4">
                        ${this.renderActionButtons(session)}
                    </div>

                    <!-- 时间信息 -->
                    <div class="text-xs text-base-content/50 mt-2">
                        创建时间: ${this.formatTime(session.created_at)} |
                        最后访问: ${this.formatTime(session.last_accessed)}
                    </div>
                </div>
            </div>
        `;
    }

    getStatusBadge(status) {
        const badges = {
            'running': '<span class="badge badge-success badge-lg gap-2"><i class="bi bi-play-circle-fill"></i>运行中</span>',
            'completed': '<span class="badge badge-primary badge-lg gap-2"><i class="bi bi-check-circle-fill"></i>已完成</span>',
            'stopped': '<span class="badge badge-warning badge-lg gap-2"><i class="bi bi-pause-circle-fill"></i>已停止</span>',
            'ready': '<span class="badge badge-info badge-lg gap-2"><i class="bi bi-clock"></i>待执行</span>',
            'unknown': '<span class="badge badge-ghost badge-lg">未知</span>'
        };
        return badges[status] || badges['unknown'];
    }

    renderActionButtons(session) {
        let buttons = '';

        // 查看进度按钮（正在运行）
        if (session.is_running) {
            buttons += `
                <button class="btn btn-sm btn-info" onclick="sessionsPage.viewProgress('${session.session_id}')">
                    <i class="bi bi-graph-up"></i>
                    查看进度
                </button>
            `;
        }

        // 恢复执行按钮（已停止且有待处理任务）
        if (session.can_resume && session.progress.pending > 0) {
            buttons += `
                <button class="btn btn-sm btn-warning" onclick="sessionsPage.resumeExecution('${session.session_id}')">
                    <i class="bi bi-play-fill"></i>
                    恢复执行
                </button>
            `;
        }

        // 下载按钮（已完成）
        if (session.can_download) {
            buttons += `
                <button class="btn btn-sm btn-success" onclick="sessionsPage.downloadResult('${session.session_id}')">
                    <i class="bi bi-download"></i>
                    下载结果
                </button>
            `;
        }

        // 继续配置按钮（已拆分但未执行）
        if (session.has_tasks && session.progress.total > 0 && session.progress.completed === 0 && !session.is_running) {
            buttons += `
                <button class="btn btn-sm btn-primary" onclick="sessionsPage.continueExecution('${session.session_id}')">
                    <i class="bi bi-play-circle"></i>
                    开始翻译
                </button>
            `;
        }

        // 删除按钮
        buttons += `
            <button class="btn btn-sm btn-ghost text-error" onclick="sessionsPage.deleteSession('${session.session_id}')">
                <i class="bi bi-trash"></i>
            </button>
        `;

        return buttons;
    }

    formatTime(isoString) {
        if (!isoString) return '未知';
        try {
            const date = new Date(isoString);
            const now = new Date();
            const diff = now - date;

            // 小于1分钟
            if (diff < 60000) return '刚刚';
            // 小于1小时
            if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
            // 小于1天
            if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
            // 超过1天
            return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'});
        } catch (e) {
            return isoString;
        }
    }

    async filterSessions(status) {
        // 更新tab样式
        document.querySelectorAll('.tabs .tab').forEach(tab => {
            tab.classList.remove('tab-active');
        });
        event.target.classList.add('tab-active');

        // 重新加载
        await this.loadSessions(status);
    }

    async refreshList() {
        await this.loadSessions();
        UIHelper.showToast('列表已刷新', 'success');
    }

    viewProgress(sessionId) {
        // 跳转到执行页面查看实时进度
        router.navigate(`/execute/${sessionId}`);
    }

    async resumeExecution(sessionId) {
        // 恢复到执行页面
        router.navigate(`/execute/${sessionId}`);
    }

    async continueExecution(sessionId) {
        // 继续执行
        router.navigate(`/execute/${sessionId}`);
    }

    async downloadResult(sessionId) {
        try {
            UIHelper.showLoading(true);

            const blob = await API.downloadResult(sessionId);
            const filename = `translated_${sessionId}_${Date.now()}.xlsx`;

            UIHelper.downloadFile(blob, filename);
            UIHelper.showToast('下载成功！', 'success');

        } catch (error) {
            UIHelper.showToast(`下载失败：${error.message}`, 'error');
        } finally {
            UIHelper.showLoading(false);
        }
    }

    async deleteSession(sessionId) {
        const confirmed = await UIHelper.showDialog({
            type: 'warning',
            title: '确认删除',
            message: '删除后将无法恢复该会话的数据，确定要删除吗？',
            confirmText: '确认删除',
            cancelText: '取消'
        });

        if (!confirmed) return;

        try {
            UIHelper.showLoading(true);

            const response = await fetch(
                `${APP_CONFIG.API_BASE_URL}/api/sessions/${sessionId}`,
                {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${authManager.getToken()}`
                    }
                }
            );

            if (!response.ok) {
                throw new Error('删除失败');
            }

            UIHelper.showToast('会话已删除', 'success');
            await this.refreshList();

        } catch (error) {
            UIHelper.showToast(`删除失败：${error.message}`, 'error');
        } finally {
            UIHelper.showLoading(false);
        }
    }

    displayError() {
        const container = document.getElementById('sessionsList');
        container.innerHTML = `
            <div class="alert alert-error">
                <i class="bi bi-exclamation-triangle-fill"></i>
                <div>
                    <h3 class="font-bold">加载失败</h3>
                    <p>无法获取会话列表，请刷新页面重试</p>
                </div>
                <button class="btn btn-sm" onclick="sessionsPage.refreshList()">重试</button>
            </div>
        `;
    }

    startAutoRefresh() {
        // 每5秒自动刷新（用于更新运行中的session进度）
        this.refreshInterval = setInterval(() => {
            // 只有当前有运行中的session时才自动刷新
            const hasRunning = this.sessions.some(s => s.is_running);
            if (hasRunning) {
                this.loadSessions();
            }
        }, 5000);
    }

    cleanup() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// 创建页面实例
const sessionsPage = new SessionsPage();
