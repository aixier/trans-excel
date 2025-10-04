// 任务配置页
class ConfigPage {
    constructor() {
        this.config = {
            source_lang: null,
            target_langs: [],
            extract_context: true,
            context_options: {
                game_info: true,
                comments: true,
                neighbors: true,
                content_analysis: true,
                sheet_type: true
            }
        };
        this.splitting = false;
        this.splitProgress = 0;
        this.pollInterval = null;
    }

    render() {
        const session = sessionManager.session;
        if (!session) {
            router.navigate('/create');
            return;
        }

        const html = `
            <div class="max-w-6xl mx-auto">
                <!-- 页面标题 -->
                <div class="text-center mb-6">
                    <h1 class="text-3xl font-bold mb-2">配置翻译任务</h1>
                    <p class="text-base-content/70">Session: ${session.sessionId}</p>
                    <p class="text-sm text-base-content/50">${session.filename}</p>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- 左侧配置区 -->
                    <div class="lg:col-span-2">
                        <div class="card bg-base-100 shadow-xl">
                            <div class="card-body">
                                <!-- 语言设置 -->
                                <h2 class="card-title mb-4">
                                    <i class="bi bi-translate"></i>
                                    语言设置
                                </h2>

                                <!-- 源语言 -->
                                <div class="form-control mb-4">
                                    <label class="label">
                                        <span class="label-text font-semibold">源语言</span>
                                    </label>
                                    <select id="sourceLang" class="select select-bordered" onchange="configPage.updatePreview()">
                                        <option value="">自动检测</option>
                                        <option value="CH">中文</option>
                                        <option value="EN">英文</option>
                                    </select>
                                </div>

                                <!-- 目标语言 -->
                                <div class="form-control mb-4">
                                    <label class="label">
                                        <span class="label-text font-semibold">目标语言（至少选择1个）</span>
                                    </label>
                                    <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
                                        ${Object.entries(APP_CONFIG.LANGUAGES.target).map(([code, name]) => `
                                            <label class="label cursor-pointer justify-start gap-2">
                                                <input type="checkbox" class="checkbox checkbox-primary"
                                                       value="${code}"
                                                       onchange="configPage.onTargetLangChange(this)">
                                                <span class="label-text">${name}</span>
                                            </label>
                                        `).join('')}
                                    </div>
                                </div>

                                <div class="divider"></div>

                                <!-- 上下文提取设置 -->
                                <h2 class="card-title mb-4">
                                    <i class="bi bi-gear"></i>
                                    上下文提取
                                </h2>

                                <!-- 总开关 -->
                                <div class="form-control mb-4">
                                    <label class="label cursor-pointer justify-start gap-4">
                                        <input type="checkbox" class="toggle toggle-primary toggle-lg"
                                               id="extractContext"
                                               checked
                                               onchange="configPage.onContextToggle(this)">
                                        <span class="label-text font-semibold">启用上下文提取</span>
                                    </label>
                                    <p class="text-sm text-base-content/70 ml-16">
                                        开启后翻译质量更高，但速度会降低
                                    </p>
                                </div>

                                <!-- 细粒度选项 -->
                                <div id="contextOptions" class="space-y-2 ml-4">
                                    <label class="label cursor-pointer justify-start gap-2">
                                        <input type="checkbox" class="checkbox checkbox-sm"
                                               id="ctxGameInfo" checked>
                                        <span class="label-text">游戏信息</span>
                                        <span class="text-xs text-base-content/50">使用游戏背景信息</span>
                                    </label>

                                    <label class="label cursor-pointer justify-start gap-2">
                                        <input type="checkbox" class="checkbox checkbox-sm"
                                               id="ctxComments" checked>
                                        <span class="label-text">单元格注释</span>
                                        <span class="text-xs text-base-content/50">提取Excel注释</span>
                                    </label>

                                    <label class="label cursor-pointer justify-start gap-2">
                                        <input type="checkbox" class="checkbox checkbox-sm"
                                               id="ctxNeighbors" checked>
                                        <span class="label-text">相邻单元格</span>
                                        <span class="text-xs text-base-content/50">参考周围内容</span>
                                    </label>

                                    <label class="label cursor-pointer justify-start gap-2">
                                        <input type="checkbox" class="checkbox checkbox-sm"
                                               id="ctxAnalysis" checked>
                                        <span class="label-text">内容特征</span>
                                        <span class="text-xs text-base-content/50">分析文本类型</span>
                                    </label>

                                    <label class="label cursor-pointer justify-start gap-2">
                                        <input type="checkbox" class="checkbox checkbox-sm"
                                               id="ctxSheetType" checked>
                                        <span class="label-text">表格类型</span>
                                        <span class="text-xs text-base-content/50">识别表格用途</span>
                                    </label>
                                </div>

                                <!-- 操作按钮 -->
                                <div class="card-actions justify-end mt-6">
                                    <button class="btn btn-ghost" onclick="configPage.resetConfig()">
                                        <i class="bi bi-arrow-clockwise"></i>
                                        重置
                                    </button>
                                    <button id="splitBtn" class="btn btn-primary" onclick="configPage.startSplit()" disabled>
                                        <i class="bi bi-scissors"></i>
                                        开始拆分任务
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- 拆分进度 -->
                        <div id="splitProgress" class="hidden mt-6">
                            <div class="card bg-base-100 shadow-xl">
                                <div class="card-body">
                                    <h3 class="card-title">
                                        <span class="loading loading-spinner loading-sm"></span>
                                        拆分进度
                                    </h3>
                                    <progress class="progress progress-primary w-full" id="splitProgressBar" value="0" max="100"></progress>
                                    <p class="text-sm text-base-content/70" id="splitMessage">正在准备...</p>
                                </div>
                            </div>
                        </div>

                        <!-- 拆分结果 -->
                        <div id="splitResult" class="hidden mt-6">
                            <div class="card bg-base-100 shadow-xl">
                                <div class="card-body">
                                    <h3 class="card-title">
                                        <i class="bi bi-check-circle-fill text-success"></i>
                                        拆分完成
                                    </h3>

                                    <div class="stats stats-vertical lg:stats-horizontal shadow">
                                        <div class="stat">
                                            <div class="stat-title">总任务数</div>
                                            <div class="stat-value text-primary" id="totalTasks">--</div>
                                        </div>
                                        <div class="stat">
                                            <div class="stat-title">总批次数</div>
                                            <div class="stat-value" id="totalBatches">--</div>
                                        </div>
                                        <div class="stat">
                                            <div class="stat-title">总字符数</div>
                                            <div class="stat-value" id="totalChars">--</div>
                                        </div>
                                    </div>

                                    <div id="langDistribution" class="mt-4">
                                        <h4 class="font-semibold mb-2">语言分布</h4>
                                        <div class="space-y-2" id="langStats"></div>
                                    </div>

                                    <div class="card-actions justify-end mt-4">
                                        <button class="btn btn-ghost" onclick="configPage.exportTasks()">
                                            <i class="bi bi-download"></i>
                                            导出Excel
                                        </button>
                                        <button class="btn btn-primary btn-lg" onclick="configPage.startTranslation()">
                                            <i class="bi bi-play-fill"></i>
                                            开始翻译
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 右侧预览区 -->
                    <div class="lg:col-span-1">
                        <div class="card bg-base-100 shadow-xl sticky top-24">
                            <div class="card-body">
                                <h3 class="card-title">
                                    <i class="bi bi-eye"></i>
                                    配置预览
                                </h3>

                                <div class="space-y-4">
                                    <!-- 当前配置 -->
                                    <div>
                                        <h4 class="font-semibold mb-2">当前配置</h4>
                                        <div class="text-sm space-y-1">
                                            <p>• 源语言: <span id="previewSource" class="font-mono">自动检测</span></p>
                                            <p>• 目标语言: <span id="previewTargets" class="font-mono">未选择</span></p>
                                            <p>• 上下文: <span id="previewContext" class="font-mono">已启用</span></p>
                                        </div>
                                    </div>

                                    <!-- 预估影响 -->
                                    <div>
                                        <h4 class="font-semibold mb-2">预估影响</h4>
                                        <div class="text-sm space-y-1">
                                            <p>• 任务数: <span id="estimateTasks" class="font-mono">--</span></p>
                                            <p>• 批次数: <span id="estimateBatches" class="font-mono">--</span></p>
                                        </div>
                                    </div>

                                    <!-- 性能提示 -->
                                    <div>
                                        <h4 class="font-semibold mb-2">性能提示</h4>
                                        <div id="performanceHint">
                                            <div class="alert alert-info">
                                                <i class="bi bi-info-circle"></i>
                                                <div>
                                                    <p class="font-semibold">开启上下文</p>
                                                    <p class="text-sm">质量 ⭐⭐⭐⭐⭐</p>
                                                    <p class="text-sm">速度 ⭐⭐⭐</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- 建议 -->
                                    <div class="alert alert-warning">
                                        <i class="bi bi-lightbulb"></i>
                                        <p class="text-sm">小文件建议开启所有上下文选项以获得最佳质量</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('pageContent').innerHTML = html;
        this.loadLastConfig();
        this.updatePreview();

        // 更新全局进度
        UIHelper.updateGlobalProgress(2);
        sessionManager.updateStage('configuring');
    }

    onTargetLangChange(checkbox) {
        if (checkbox.checked) {
            if (!this.config.target_langs.includes(checkbox.value)) {
                this.config.target_langs.push(checkbox.value);
            }
        } else {
            const index = this.config.target_langs.indexOf(checkbox.value);
            if (index > -1) {
                this.config.target_langs.splice(index, 1);
            }
        }

        this.updatePreview();
        this.validateConfig();
    }

    onContextToggle(toggle) {
        this.config.extract_context = toggle.checked;
        const optionsContainer = document.getElementById('contextOptions');

        if (toggle.checked) {
            optionsContainer.classList.remove('opacity-50', 'pointer-events-none');
        } else {
            optionsContainer.classList.add('opacity-50', 'pointer-events-none');
        }

        this.updatePreview();
        this.updatePerformanceHint();
    }

    updatePreview() {
        // 源语言
        const sourceLang = document.getElementById('sourceLang').value;
        this.config.source_lang = sourceLang || null;
        document.getElementById('previewSource').textContent =
            sourceLang ? APP_CONFIG.LANGUAGES.source[sourceLang] : '自动检测';

        // 目标语言
        const targetNames = this.config.target_langs.map(code =>
            APP_CONFIG.LANGUAGES.target[code]
        );
        document.getElementById('previewTargets').textContent =
            targetNames.length > 0 ? targetNames.join(', ') : '未选择';

        // 上下文
        document.getElementById('previewContext').textContent =
            this.config.extract_context ? '已启用' : '已关闭';

        // 预估
        this.updateEstimation();
        this.updatePerformanceHint();
    }

    updateEstimation() {
        const session = sessionManager.session;
        if (!session || !session.analysis) return;

        const estimatedTasks = session.analysis.statistics.estimated_tasks || 0;
        const langCount = this.config.target_langs.length || 1;
        const totalTasks = estimatedTasks * langCount;
        const batchSize = 35; // 估算值
        const totalBatches = Math.ceil(totalTasks / batchSize);

        document.getElementById('estimateTasks').textContent = totalTasks.toLocaleString();
        document.getElementById('estimateBatches').textContent = `~${totalBatches}`;
    }

    updatePerformanceHint() {
        const hint = document.getElementById('performanceHint');

        if (this.config.extract_context) {
            hint.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i>
                    <div>
                        <p class="font-semibold">开启上下文</p>
                        <p class="text-sm">质量 ⭐⭐⭐⭐⭐</p>
                        <p class="text-sm">速度 ⭐⭐⭐</p>
                    </div>
                </div>
            `;
        } else {
            hint.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-speedometer2"></i>
                    <div>
                        <p class="font-semibold">关闭上下文</p>
                        <p class="text-sm">质量 ⭐⭐⭐</p>
                        <p class="text-sm">速度 ⭐⭐⭐⭐⭐</p>
                    </div>
                </div>
            `;
        }
    }

    validateConfig() {
        const splitBtn = document.getElementById('splitBtn');
        if (this.config.target_langs.length > 0) {
            splitBtn.disabled = false;
        } else {
            splitBtn.disabled = true;
        }
    }

    async startSplit() {
        if (this.splitting || this.config.target_langs.length === 0) return;

        // 收集上下文选项
        if (this.config.extract_context) {
            this.config.context_options = {
                game_info: document.getElementById('ctxGameInfo').checked,
                comments: document.getElementById('ctxComments').checked,
                neighbors: document.getElementById('ctxNeighbors').checked,
                content_analysis: document.getElementById('ctxAnalysis').checked,
                sheet_type: document.getElementById('ctxSheetType').checked
            };
        }

        this.splitting = true;
        document.getElementById('splitBtn').disabled = true;
        document.getElementById('splitProgress').classList.remove('hidden');
        document.getElementById('splitResult').classList.add('hidden');

        try {
            // 保存配置
            Storage.saveTaskConfig(this.config);

            // 开始拆分
            await API.splitTasks(sessionManager.session.sessionId, this.config);

            // 轮询进度
            this.startPolling();

        } catch (error) {
            UIHelper.showToast(`拆分失败：${error.message}`, 'error');
            this.splitting = false;
            document.getElementById('splitBtn').disabled = false;
            document.getElementById('splitProgress').classList.add('hidden');
        }
    }

    startPolling() {
        this.pollInterval = setInterval(async () => {
            try {
                const status = await API.getSplitStatus(sessionManager.session.sessionId);

                // 更新进度
                UIHelper.updateProgress('splitProgressBar', status.progress || 0);
                document.getElementById('splitMessage').textContent =
                    status.message || `处理中... ${status.processed_sheets}/${status.total_sheets} sheets`;

                if (status.status === 'completed') {
                    this.handleSplitComplete(status);
                } else if (status.status === 'failed') {
                    throw new Error(status.message || 'Split failed');
                }

            } catch (error) {
                clearInterval(this.pollInterval);
                UIHelper.showToast(`拆分失败：${error.message}`, 'error');
                this.splitting = false;
                document.getElementById('splitBtn').disabled = false;
                document.getElementById('splitProgress').classList.add('hidden');
            }
        }, APP_CONFIG.SPLIT_POLL_INTERVAL);
    }

    handleSplitComplete(status) {
        clearInterval(this.pollInterval);
        this.splitting = false;

        document.getElementById('splitProgress').classList.add('hidden');
        document.getElementById('splitResult').classList.remove('hidden');

        // 显示结果
        document.getElementById('totalTasks').textContent =
            (status.task_count || 0).toLocaleString();
        document.getElementById('totalBatches').textContent =
            status.batch_count || 0;
        document.getElementById('totalChars').textContent =
            (status.total_chars || 0).toLocaleString();

        // 语言分布
        if (status.batch_distribution) {
            const langStats = document.getElementById('langStats');
            langStats.innerHTML = Object.entries(status.batch_distribution).map(([lang, info]) => `
                <div class="flex justify-between items-center">
                    <span class="font-semibold">${APP_CONFIG.LANGUAGES.target[lang] || lang}:</span>
                    <span class="badge badge-primary badge-lg">
                        ${info.batches}批次，${info.tasks}任务
                    </span>
                </div>
            `).join('');
        }

        UIHelper.showToast('任务拆分完成！', 'success');
        sessionManager.updateStage('configured');
    }

    async exportTasks() {
        try {
            const blob = await API.exportTasks(sessionManager.session.sessionId);
            UIHelper.downloadFile(blob, `tasks_${sessionManager.session.sessionId}.xlsx`);
            UIHelper.showToast('任务列表已导出', 'success');
        } catch (error) {
            UIHelper.showToast(`导出失败：${error.message}`, 'error');
        }
    }

    startTranslation() {
        window.location.hash = `#/execute/${sessionManager.session.sessionId}`;
    }

    resetConfig() {
        this.config = JSON.parse(JSON.stringify(APP_CONFIG.DEFAULT_CONFIG));

        // 重置UI
        document.getElementById('sourceLang').value = '';
        document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            if (cb.id === 'extractContext' || cb.id.startsWith('ctx')) {
                cb.checked = true;
            } else {
                cb.checked = false;
            }
        });

        this.config.target_langs = [];
        this.updatePreview();
        this.validateConfig();
    }

    loadLastConfig() {
        const lastConfig = Storage.getLastTaskConfig();
        if (lastConfig) {
            this.config = lastConfig;

            // 恢复UI状态
            document.getElementById('sourceLang').value = lastConfig.source_lang || '';
            document.getElementById('extractContext').checked = lastConfig.extract_context;

            // 恢复目标语言
            lastConfig.target_langs.forEach(lang => {
                const checkbox = document.querySelector(`input[type="checkbox"][value="${lang}"]`);
                if (checkbox) checkbox.checked = true;
            });

            // 恢复上下文选项
            if (lastConfig.context_options) {
                Object.entries(lastConfig.context_options).forEach(([key, value]) => {
                    const id = 'ctx' + key.charAt(0).toUpperCase() + key.slice(1).replace(/_([a-z])/g, (g) => g[1].toUpperCase());
                    const checkbox = document.getElementById(id);
                    if (checkbox) checkbox.checked = value;
                });
            }

            this.validateConfig();
        }
    }

    cleanup() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
    }
}

// 创建页面实例
const configPage = new ConfigPage();