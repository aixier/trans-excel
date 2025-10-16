// 结果导出页
class CompletePage {
    constructor() {
        this.sessionId = null;
        this.summary = null;
        this.hasDownloaded = false;
        this.urgencyTimer = null;
    }

    render(sessionId) {
        this.sessionId = sessionId;

        if (!sessionManager.loadSession(sessionId)) {
            UIHelper.showToast('会话不存在或已过期', 'error');
            router.navigate('/create');
            return;
        }

        const html = `
            <div class="max-w-5xl mx-auto">
                <!-- 页面标题 -->
                <div class="text-center mb-8">
                    <div class="inline-flex items-center justify-center w-20 h-20 bg-success/20 rounded-full mb-4">
                        <i class="bi bi-check-circle-fill text-4xl text-success"></i>
                    </div>
                    <h1 class="text-3xl font-bold mb-2">翻译完成</h1>
                    <p class="text-base-content/70">您的翻译任务已成功完成！</p>
                </div>

                <!-- 紧急下载提醒 -->
                <div id="urgentWarning" class="hidden mb-6">
                    <div class="alert alert-warning pulse-animation">
                        <i class="bi bi-exclamation-triangle-fill"></i>
                        <div>
                            <h3 class="font-bold">⚠️ 数据即将清除</h3>
                            <p>您的翻译结果将在 <span id="urgentTime" class="font-bold">--</span> 分钟后永久删除，请立即下载！</p>
                        </div>
                        <button class="btn btn-warning" onclick="completePage.downloadResult()">
                            立即下载
                        </button>
                    </div>
                </div>

                <!-- 主要完成信息 -->
                <div class="card bg-base-100 shadow-xl mb-6">
                    <div class="card-body text-center">
                        <h2 class="text-2xl font-semibold mb-4">
                            ${sessionManager.session.filename}
                        </h2>

                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div class="stat bg-base-200 rounded-lg">
                                <div class="stat-title">耗时</div>
                                <div class="stat-value text-xl" id="totalTime">--</div>
                            </div>
                            <div class="stat bg-base-200 rounded-lg">
                                <div class="stat-title">完成率</div>
                                <div class="stat-value text-xl text-success" id="completionRate">--%</div>
                            </div>
                            <div class="stat bg-base-200 rounded-lg">
                                <div class="stat-title">任务数</div>
                                <div class="stat-value text-xl" id="totalTasks">--</div>
                            </div>
                            <div class="stat bg-base-200 rounded-lg">
                                <div class="stat-title">置信度</div>
                                <div class="stat-value text-xl" id="avgConfidence">--%</div>
                            </div>
                        </div>

                        <button id="downloadBtn" class="btn btn-primary btn-lg" onclick="completePage.downloadResult()">
                            <i class="bi bi-download"></i>
                            下载结果
                        </button>

                        <p class="text-sm text-base-content/50 mt-2">
                            提示：服务器数据将在会话过期后自动清除
                        </p>
                    </div>
                </div>

                <!-- 质量概览 -->
                <div class="card bg-base-100 shadow-xl mb-6">
                    <div class="card-body">
                        <h3 class="card-title mb-4">质量概览</h3>

                        <div class="mb-4">
                            <div class="flex justify-between mb-2">
                                <span>整体置信度</span>
                                <span class="font-bold" id="overallConfidence">--%</span>
                            </div>
                            <progress class="progress progress-primary" id="confidenceBar" value="0" max="100"></progress>
                        </div>

                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div class="text-center p-4 bg-success/10 rounded-lg cursor-pointer hover:bg-success/20"
                                 onclick="completePage.showQualityDetails('high')">
                                <i class="bi bi-star-fill text-2xl text-success"></i>
                                <p class="font-bold text-lg" id="highQuality">--</p>
                                <p class="text-sm text-base-content/70">高质量 (>90%)</p>
                                <p class="text-xs" id="highPercent">--%</p>
                            </div>

                            <div class="text-center p-4 bg-warning/10 rounded-lg cursor-pointer hover:bg-warning/20"
                                 onclick="completePage.showQualityDetails('medium')">
                                <i class="bi bi-star-half text-2xl text-warning"></i>
                                <p class="font-bold text-lg" id="mediumQuality">--</p>
                                <p class="text-sm text-base-content/70">中等 (70-90%)</p>
                                <p class="text-xs" id="mediumPercent">--%</p>
                            </div>

                            <div class="text-center p-4 bg-error/10 rounded-lg cursor-pointer hover:bg-error/20"
                                 onclick="completePage.showQualityDetails('low')">
                                <i class="bi bi-star text-2xl text-error"></i>
                                <p class="font-bold text-lg" id="lowQuality">--</p>
                                <p class="text-sm text-base-content/70">低质量 (<70%)</p>
                                <p class="text-xs" id="lowPercent">--%</p>
                            </div>

                            <div class="text-center p-4 bg-base-300 rounded-lg cursor-pointer hover:bg-base-content/20"
                                 onclick="completePage.showFailedTasks()">
                                <i class="bi bi-x-circle text-2xl text-base-content/50"></i>
                                <p class="font-bold text-lg" id="failedCount">--</p>
                                <p class="text-sm text-base-content/70">失败</p>
                                <p class="text-xs" id="failedPercent">--%</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- 语言统计 -->
                    <div class="card bg-base-100 shadow-xl">
                        <div class="card-body">
                            <h3 class="card-title mb-4">语言统计</h3>
                            <div id="langStats" class="space-y-3">
                                <div class="text-center text-base-content/50 py-4">
                                    加载中...
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 性能指标 -->
                    <div class="card bg-base-100 shadow-xl">
                        <div class="card-body">
                            <h3 class="card-title mb-4">性能指标</h3>
                            <div class="space-y-3">
                                <div class="flex justify-between">
                                    <span><i class="bi bi-check-circle"></i> 总任务</span>
                                    <span class="font-mono" id="perfTotal">--</span>
                                </div>
                                <div class="flex justify-between">
                                    <span><i class="bi bi-check2-all"></i> 成功</span>
                                    <span class="font-mono text-success" id="perfSuccess">--</span>
                                </div>
                                <div class="flex justify-between">
                                    <span><i class="bi bi-x-circle"></i> 失败</span>
                                    <span class="font-mono text-error" id="perfFailed">--</span>
                                </div>
                                <div class="flex justify-between">
                                    <span><i class="bi bi-clock"></i> 总耗时</span>
                                    <span class="font-mono" id="perfTime">--</span>
                                </div>
                                <div class="flex justify-between">
                                    <span><i class="bi bi-speedometer2"></i> 平均速度</span>
                                    <span class="font-mono" id="perfSpeed">--/秒</span>
                                </div>
                                <div class="flex justify-between">
                                    <span><i class="bi bi-coin"></i> Token用量</span>
                                    <span class="font-mono" id="perfToken">--</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 失败任务详情 -->
                <div id="failedTasksSection" class="hidden">
                    <div class="card bg-base-100 shadow-xl mt-6 border-2 border-error">
                        <div class="card-body">
                            <h3 class="card-title text-error">
                                <i class="bi bi-exclamation-triangle-fill"></i>
                                失败任务 (<span id="failedTaskCount">0</span>个)
                            </h3>
                            <div id="failedTasksList" class="space-y-2 max-h-64 overflow-y-auto">
                                <!-- 动态加载失败任务 -->
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 后续操作 -->
                <div class="card bg-base-100 shadow-xl mt-6">
                    <div class="card-body">
                        <h3 class="card-title mb-4">后续操作</h3>
                        <div class="flex flex-wrap gap-4">
                            <button class="btn btn-outline" onclick="completePage.retryFailedTasks()">
                                <i class="bi bi-arrow-clockwise"></i>
                                重新翻译失败任务
                            </button>
                            <button class="btn btn-outline" onclick="completePage.startNewProject()">
                                <i class="bi bi-plus-circle"></i>
                                开始新项目
                            </button>
                            <button class="btn btn-outline" onclick="completePage.viewDetailedReport()">
                                <i class="bi bi-file-text"></i>
                                查看详细报告
                            </button>
                            <button class="btn btn-outline" onclick="completePage.exportLog()">
                                <i class="bi bi-journal-text"></i>
                                导出日志
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('pageContent').innerHTML = html;

        // 更新全局进度
        UIHelper.updateGlobalProgress(4);

        // 加载数据
        this.loadSummary();
        this.startUrgencyMonitoring();
    }

    async loadSummary() {
        try {
            // 尝试从缓存获取
            let summary = Storage.getCacheItem(`summary_${this.sessionId}`);

            if (!summary) {
                // 从API获取
                summary = await API.getCompletionSummary(this.sessionId);
                Storage.setCacheItem(`summary_${this.sessionId}`, summary);
            }

            this.summary = summary;
            this.displaySummary(summary);

        } catch (error) {
            logger.error('Failed to load summary:', error);

            // 显示基本信息
            this.displayBasicInfo();
        }
    }

    displaySummary(summary) {
        // 基本统计
        document.getElementById('totalTasks').textContent = summary.summary.total_tasks.toLocaleString();
        document.getElementById('completionRate').textContent =
            `${summary.summary.success_rate.toFixed(1)}%`;
        document.getElementById('totalTime').textContent =
            UIHelper.formatTime(summary.summary.total_time);
        document.getElementById('avgConfidence').textContent =
            `${summary.summary.average_confidence.toFixed(1)}%`;

        // 质量分布
        const quality = summary.quality_distribution || {};
        const total = summary.summary.total_tasks;

        document.getElementById('highQuality').textContent = quality.high || 0;
        document.getElementById('highPercent').textContent =
            `${((quality.high / total) * 100).toFixed(1)}%`;

        document.getElementById('mediumQuality').textContent = quality.medium || 0;
        document.getElementById('mediumPercent').textContent =
            `${((quality.medium / total) * 100).toFixed(1)}%`;

        document.getElementById('lowQuality').textContent = quality.low || 0;
        document.getElementById('lowPercent').textContent =
            `${((quality.low / total) * 100).toFixed(1)}%`;

        const failed = summary.summary.total_tasks - summary.summary.completed;
        document.getElementById('failedCount').textContent = failed;
        document.getElementById('failedPercent').textContent =
            `${((failed / total) * 100).toFixed(1)}%`;

        // 整体置信度
        document.getElementById('overallConfidence').textContent =
            `${summary.summary.average_confidence.toFixed(1)}%`;
        document.getElementById('confidenceBar').value = summary.summary.average_confidence;

        // 语言统计
        if (summary.language_stats) {
            this.displayLanguageStats(summary.language_stats);
        }

        // 性能指标
        document.getElementById('perfTotal').textContent = summary.summary.total_tasks;
        document.getElementById('perfSuccess').textContent = summary.summary.completed;
        document.getElementById('perfFailed').textContent = failed;
        document.getElementById('perfTime').textContent = UIHelper.formatTime(summary.summary.total_time);

        if (summary.summary.total_time > 0) {
            const speed = summary.summary.completed / summary.summary.total_time;
            document.getElementById('perfSpeed').textContent = `${speed.toFixed(1)}/秒`;
        }

        document.getElementById('perfToken').textContent =
            summary.token_usage ? `${(summary.token_usage / 1000).toFixed(1)}K` : '--';

        // 显示失败任务
        if (failed > 0) {
            document.getElementById('failedTasksSection').classList.remove('hidden');
            document.getElementById('failedTaskCount').textContent = failed;
        }
    }

    displayLanguageStats(langStats) {
        const container = document.getElementById('langStats');

        if (!langStats || Object.keys(langStats).length === 0) {
            container.innerHTML = '<div class="text-center text-base-content/50 py-4">无语言统计数据</div>';
            return;
        }

        container.innerHTML = Object.entries(langStats).map(([lang, stats]) => `
            <div class="flex justify-between items-center">
                <span class="font-semibold">
                    ${APP_CONFIG.LANGUAGES.target[lang] || lang}
                </span>
                <div class="text-right">
                    <span class="badge badge-primary">${stats.count} 任务</span>
                    <span class="text-sm text-base-content/70 ml-2">
                        置信度: ${stats.avg_confidence.toFixed(1)}%
                    </span>
                </div>
            </div>
        `).join('');
    }

    displayBasicInfo() {
        // 显示基本信息（无统计数据时）
        document.getElementById('totalTasks').textContent = '--';
        document.getElementById('completionRate').textContent = '--';
        document.getElementById('totalTime').textContent = '--';
        document.getElementById('avgConfidence').textContent = '--';
    }

    startUrgencyMonitoring() {
        // 监控会话剩余时间
        const checkUrgency = () => {
            const remaining = sessionManager.getRemainingTime();

            if (remaining <= APP_CONFIG.SESSION_WARNING_TIME && !this.hasDownloaded) {
                this.showUrgentWarning(remaining);
            }

            // 更新下载按钮样式
            if (remaining <= APP_CONFIG.SESSION_WARNING_TIME) {
                document.getElementById('downloadBtn').classList.add('pulse-animation');
            }
        };

        // 每分钟检查一次
        this.urgencyTimer = setInterval(checkUrgency, 60000);
        checkUrgency(); // 立即检查一次
    }

    showUrgentWarning(remaining) {
        const minutes = Math.floor(remaining / 60000);
        const warningDiv = document.getElementById('urgentWarning');

        warningDiv.classList.remove('hidden');
        document.getElementById('urgentTime').textContent = minutes;

        // 添加紧急样式
        document.body.classList.add('urgent-warning');
    }

    async downloadResult() {
        try {
            UIHelper.showLoading(true);

            const blob = await API.downloadResult(this.sessionId);
            const filename = `translated_${this.sessionId}_${Date.now()}.xlsx`;

            UIHelper.downloadFile(blob, filename);

            this.hasDownloaded = true;
            document.getElementById('downloadBtn').classList.remove('pulse-animation');
            document.getElementById('urgentWarning').classList.add('hidden');
            document.body.classList.remove('urgent-warning');

            UIHelper.showToast('下载成功！文件已保存到本地。', 'success');

            // 更新按钮文本
            document.getElementById('downloadBtn').innerHTML = `
                <i class="bi bi-check-circle"></i>
                已下载（可再次下载）
            `;

        } catch (error) {
            UIHelper.showToast(`下载失败：${error.message}`, 'error');
        } finally {
            UIHelper.showLoading(false);
        }
    }

    showQualityDetails(level) {
        // TODO: 显示特定质量等级的任务详情
        UIHelper.showToast(`查看${level}质量任务详情功能开发中...`, 'info');
    }

    showFailedTasks() {
        const section = document.getElementById('failedTasksSection');

        if (section.classList.contains('hidden')) {
            section.classList.remove('hidden');
            // TODO: 加载失败任务列表
            document.getElementById('failedTasksList').innerHTML = `
                <div class="alert alert-error">
                    <i class="bi bi-x-circle"></i>
                    <div>
                        <p class="font-semibold">Task #234</p>
                        <p class="text-sm">原文: "Complex technical term..."</p>
                        <p class="text-sm">原因: API超时</p>
                    </div>
                </div>
            `;
        } else {
            section.classList.add('hidden');
        }
    }

    retryFailedTasks() {
        UIHelper.showDialog({
            type: 'warning',
            title: '重新翻译失败任务',
            message: '此功能将创建新的翻译任务，仅包含之前失败的内容。',
            actions: [
                {
                    label: '确认',
                    className: 'btn-primary',
                    action: () => {
                        UIHelper.showToast('功能开发中...', 'info');
                    }
                },
                {
                    label: '取消',
                    className: 'btn-ghost'
                }
            ]
        });
    }

    startNewProject() {
        // 清除当前会话
        sessionManager.clearSession();
        router.navigate('/create');
    }

    viewDetailedReport() {
        UIHelper.showToast('详细报告功能开发中...', 'info');
    }

    exportLog() {
        UIHelper.showToast('日志导出功能开发中...', 'info');
    }

    cleanup() {
        if (this.urgencyTimer) {
            clearInterval(this.urgencyTimer);
        }
    }
}

// 创建页面实例
const completePage = new CompletePage();