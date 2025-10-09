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
            },
            max_chars_per_batch: 2000  // Will be loaded from server config
        };
        this.splitting = false;
        this.splitProgress = 0;
        this.pollInterval = null;
    }

    // 获取源语言选项（只显示实际检测到的语言）
    getSourceLanguageOptions(session) {
        const detected = session.analysis?.language_detection?.detected?.source_languages || [];

        return detected.map(lang =>
            `<option value="${lang.code}">${lang.name} (${lang.abbr})</option>`
        ).join('');
    }

    // 获取目标语言选项（只显示实际检测到的语言）
    getTargetLanguageOptions(session) {
        const detected = session.analysis?.language_detection?.detected?.target_languages || [];

        if (detected.length === 0) {
            return '<p class="text-warning">Excel中未检测到目标语言列</p>';
        }

        return detected.map(lang => {
            const displayName = `${lang.name} (${lang.abbr})`;

            return `
                <label class="label cursor-pointer justify-start gap-2">
                    <input type="checkbox" class="checkbox checkbox-primary"
                           value="${lang.code}"
                           onchange="configPage.onTargetLangChange(this)"
                           data-detected="true">
                    <span class="label-text">${displayName}</span>
                    <span class="badge badge-xs badge-success">已有</span>
                </label>
            `;
        }).join('');
    }

    // 获取语言显示名称（从后端数据）
    getLanguageDisplayName(session, code) {
        // 尝试从available列表中查找
        const allLangs = [
            ...(session.analysis?.language_detection?.available?.source_languages || []),
            ...(session.analysis?.language_detection?.available?.target_languages || [])
        ];

        const lang = allLangs.find(l => l.code === code);
        if (lang) {
            return lang.abbr || lang.name;
        }

        return code;
    }

    render() {
        // 确保session从localStorage加载（防止页面刷新或路由切换导致的session丢失）
        if (!sessionManager.session) {
            const savedSession = Storage.getCurrentSession();
            if (savedSession && savedSession.sessionId) {
                console.log('Restoring session from localStorage:', savedSession.sessionId);
                sessionManager.session = savedSession;
            }
        }

        const session = sessionManager.session;
        if (!session || !session.sessionId) {
            UIHelper.showToast('会话不存在，请重新上传文件', 'warning');
            router.navigate('/create');
            return;
        }

        const html = `
            <div class="h-full flex flex-col">
                <!-- 页面标题 -->
                <div class="text-center mb-4">
                    <h1 class="text-2xl font-bold mb-1">配置翻译任务</h1>
                    <p class="text-sm text-base-content/70">${session.filename}</p>
                </div>

                <!-- 主内容区域 - 单栏布局 -->
                <div class="flex-1 overflow-y-auto">
                    <div class="max-w-6xl mx-auto">
                        <div class="card bg-base-100 shadow-xl">
                            <div class="card-body">
                                <!-- 语言设置和上下文提取 - 左右两栏 -->
                                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                    <!-- 左栏：语言设置 -->
                                    <div>
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
                                                <option value="auto">自动检测</option>
                                                ${this.getSourceLanguageOptions(session)}
                                            </select>
                                            <p class="text-xs text-base-content/50 mt-1">
                                                检测到 ${session.analysis?.language_detection?.detected?.source_languages?.length || 0} 种源语言
                                            </p>
                                        </div>

                                        <!-- 目标语言 -->
                                        <div class="form-control">
                                            <label class="label">
                                                <span class="label-text font-semibold">目标语言（至少选择1个）</span>
                                            </label>
                                            <div class="grid grid-cols-2 gap-2">
                                                ${this.getTargetLanguageOptions(session)}
                                            </div>
                                            <p class="text-xs text-base-content/50 mt-2">
                                                检测到 ${session.analysis?.language_detection?.detected?.target_languages?.length || 0} 种目标语言（建议全选）
                                            </p>
                                        </div>
                                    </div>

                                    <!-- 右栏：上下文提取 -->
                                    <div>
                                        <h2 class="card-title mb-4">
                                            <i class="bi bi-gear"></i>
                                            上下文提取
                                        </h2>

                                        <!-- 总开关 -->
                                        <div class="form-control mb-4">
                                            <label class="label cursor-pointer justify-start gap-3">
                                                <input type="checkbox" class="toggle toggle-primary"
                                                       id="extractContext"
                                                       checked
                                                       onchange="configPage.onContextToggle(this)">
                                                <span class="label-text">启用上下文提取（提高翻译质量）</span>
                                            </label>
                                        </div>

                                        <!-- 细粒度选项 -->
                                        <div id="contextOptions" class="space-y-2">
                                            <label class="label cursor-pointer justify-start gap-2">
                                                <input type="checkbox" class="checkbox checkbox-sm" id="ctxGameInfo" checked>
                                                <span class="label-text">游戏信息</span>
                                            </label>
                                            <label class="label cursor-pointer justify-start gap-2">
                                                <input type="checkbox" class="checkbox checkbox-sm" id="ctxComments" checked>
                                                <span class="label-text">单元格注释</span>
                                            </label>
                                            <label class="label cursor-pointer justify-start gap-2">
                                                <input type="checkbox" class="checkbox checkbox-sm" id="ctxNeighbors" checked>
                                                <span class="label-text">相邻单元格</span>
                                            </label>
                                            <label class="label cursor-pointer justify-start gap-2">
                                                <input type="checkbox" class="checkbox checkbox-sm" id="ctxAnalysis" checked>
                                                <span class="label-text">内容特征</span>
                                            </label>
                                            <label class="label cursor-pointer justify-start gap-2">
                                                <input type="checkbox" class="checkbox checkbox-sm" id="ctxSheetType" checked>
                                                <span class="label-text">表格类型</span>
                                            </label>
                                        </div>

                                        <!-- 批次大小设置 -->
                                        <div class="form-control mt-6">
                                            <label class="label">
                                                <span class="label-text font-semibold">批次大小（字符数）</span>
                                            </label>
                                            <input type="range"
                                                   id="maxCharsPerBatch"
                                                   min="1000"
                                                   max="2000"
                                                   value="2000"
                                                   step="100"
                                                   class="range range-primary range-sm"
                                                   oninput="configPage.onBatchSizeChange(this)">
                                            <div class="flex justify-between text-xs px-2 mt-1">
                                                <span>1000</span>
                                                <span>1500</span>
                                                <span>2000</span>
                                            </div>
                                            <div class="text-sm text-base-content/70 mt-2">
                                                当前: <span id="batchSizeValue" class="font-bold text-primary">2000</span> 字符/批次
                                            </div>
                                            <p class="text-xs text-base-content/50 mt-1">
                                                较小值：更细粒度拆分，批次更多<br>
                                                较大值：批次更少，单批任务更多
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <!-- 操作按钮 -->
                                <div class="card-actions justify-end mt-6">
                                    <button class="btn btn-ghost btn-sm" onclick="configPage.resetConfig()">
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
                                            <div class="stat-desc">需要翻译的单元格</div>
                                        </div>
                                        <div class="stat">
                                            <div class="stat-title">总批次数</div>
                                            <div class="stat-value text-secondary" id="totalBatches">--</div>
                                            <div class="stat-desc">LLM请求次数</div>
                                        </div>
                                        <div class="stat">
                                            <div class="stat-title">总字符数</div>
                                            <div class="stat-value" id="totalChars">--</div>
                                            <div class="stat-desc">待翻译文本量</div>
                                        </div>
                                    </div>

                                    <div id="langDistribution" class="mt-4">
                                        <h4 class="font-semibold mb-2">
                                            <i class="bi bi-translate"></i>
                                            语言分布
                                        </h4>
                                        <div class="space-y-2" id="langStats"></div>
                                    </div>

                                    <!-- 批次类型分布 -->
                                    <div id="batchTypeDistribution" class="mt-4">
                                        <h4 class="font-semibold mb-2">
                                            <i class="bi bi-box-seam"></i>
                                            批次类型分布
                                        </h4>
                                        <div class="flex gap-2 flex-wrap" id="typeStats"></div>
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
                </div>
            </div>
        `;

        document.getElementById('pageContent').innerHTML = html;
        this.loadServerConfig();  // Load default config from server
        this.loadLastConfig();
        this.updatePreview();
        this.validateConfig();  // 验证配置，确保按钮状态正确

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
    }

    onBatchSizeChange(range) {
        this.config.max_chars_per_batch = parseInt(range.value);
        const valueDisplay = document.getElementById('batchSizeValue');
        if (valueDisplay) {
            valueDisplay.textContent = range.value;
        }
    }

    updatePreview() {
        const session = sessionManager.session;
        if (!session) return;

        // 源语言
        const sourceLang = document.getElementById('sourceLang').value;
        this.config.source_lang = sourceLang || null;
    }

    validateConfig() {
        const splitBtn = document.getElementById('splitBtn');
        if (!splitBtn) return; // 防止DOM元素还未渲染

        // 检查所有必需参数
        const checks = {
            hasSession: !!(sessionManager.session && sessionManager.session.sessionId),
            hasSessionId: !!(sessionManager.session?.sessionId && sessionManager.session.sessionId.length > 0),
            hasTargetLangs: !!(this.config.target_langs && this.config.target_langs.length > 0),
            hasValidSourceLang: this.config.source_lang !== undefined // source_lang可以是null(auto)或具体语言
        };

        // 打印验证状态（调试用）
        console.log('Config validation:', checks);

        // 所有检查都通过才启用按钮
        const allValid = Object.values(checks).every(v => v === true);

        if (allValid) {
            splitBtn.disabled = false;
            splitBtn.title = '开始拆分任务';
        } else {
            splitBtn.disabled = true;
            // 提供具体的禁用原因
            const reasons = [];
            if (!checks.hasSession || !checks.hasSessionId) reasons.push('会话未建立');
            if (!checks.hasTargetLangs) reasons.push('请选择至少一个目标语言');
            splitBtn.title = reasons.join(', ');
        }
    }

    async startSplit() {
        if (this.splitting || this.config.target_langs.length === 0) return;

        // 验证 session 是否存在
        if (!sessionManager.session || !sessionManager.session.sessionId) {
            UIHelper.showToast('会话已失效，请重新上传文件', 'error');
            router.navigate('/create');
            return;
        }

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

        // 🔍 诊断日志：检查session数据
        console.log('=== Split Debug Info ===');
        console.log('sessionManager.session:', sessionManager.session);
        console.log('sessionId:', sessionManager.session?.sessionId);
        console.log('Config:', this.config);

        this.splitting = true;
        document.getElementById('splitBtn').disabled = true;
        document.getElementById('splitProgress').classList.remove('hidden');
        document.getElementById('splitResult').classList.add('hidden');

        try {
            // 保存配置
            Storage.saveTaskConfig(this.config);

            // 🔍 拆分请求前再次确认sessionId
            console.log('Sending Split Request with SessionID:', sessionManager.session.sessionId);

            // 开始拆分（带自动重试）
            let splitResult;
            try {
                splitResult = await API.splitTasks(sessionManager.session.sessionId, this.config);
            } catch (firstError) {
                // 如果是"Session not found"错误，等待1秒后重试一次
                if (firstError.message && firstError.message.includes('Session not found')) {
                    console.warn('⚠️ First split attempt failed (Session not found), retrying in 1s...');
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    splitResult = await API.splitTasks(sessionManager.session.sessionId, this.config);
                    console.log('✅ Split succeeded on retry');
                } else {
                    throw firstError; // 其他错误直接抛出
                }
            }

            console.log('Split Request Success!', splitResult);

            // 轮询进度
            this.startPolling();

        } catch (error) {
            console.error('Split Request Failed:', error);
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
                <div class="alert alert-info py-2">
                    <div class="flex justify-between items-center w-full">
                        <div>
                            <span class="font-bold text-lg">${APP_CONFIG.LANGUAGES.target[lang] || lang}</span>
                        </div>
                        <div class="flex gap-2">
                            <div class="badge badge-secondary badge-lg">
                                <i class="bi bi-boxes mr-1"></i>
                                ${info.batches} 批次
                            </div>
                            <div class="badge badge-primary badge-lg">
                                <i class="bi bi-file-text mr-1"></i>
                                ${info.tasks} 任务
                            </div>
                            <div class="badge badge-ghost badge-lg">
                                ${info.chars.toLocaleString()} 字符
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        // 批次类型分布
        if (status.type_batch_distribution) {
            const typeStats = document.getElementById('typeStats');
            const typeNames = {
                'blue': '蓝色(缩短)',
                'yellow': '黄色(重译)',
                'normal': '普通翻译'
            };
            const typeColors = {
                'blue': 'badge-info',
                'yellow': 'badge-warning',
                'normal': 'badge-success'
            };

            typeStats.innerHTML = Object.entries(status.type_batch_distribution).map(([type, count]) => `
                <div class="badge ${typeColors[type] || 'badge-neutral'} badge-lg gap-2">
                    <i class="bi bi-tag-fill"></i>
                    ${typeNames[type] || type}: ${count} 批次
                </div>
            `).join('');
        }

        UIHelper.showToast('任务拆分完成！', 'success');
        sessionManager.updateStage('configured');

        // 自动跳转到执行页面
        setTimeout(() => {
            this.startTranslation();
        }, 1500);
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

    async loadServerConfig() {
        try {
            const response = await fetch(`${APP_CONFIG.API_BASE_URL}/api/execute/config`);
            if (response.ok) {
                const serverConfig = await response.json();
                // Set default max_chars_per_batch from server
                if (serverConfig.max_chars_per_batch) {
                    this.config.max_chars_per_batch = serverConfig.max_chars_per_batch;
                    const rangeInput = document.getElementById('maxCharsPerBatch');
                    const valueDisplay = document.getElementById('batchSizeValue');
                    if (rangeInput) rangeInput.value = serverConfig.max_chars_per_batch;
                    if (valueDisplay) valueDisplay.textContent = serverConfig.max_chars_per_batch;
                }
            }
        } catch (error) {
            console.warn('Failed to load server config, using defaults:', error);
        }
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

            // 恢复批次大小
            if (lastConfig.max_chars_per_batch) {
                this.config.max_chars_per_batch = lastConfig.max_chars_per_batch;
                const rangeInput = document.getElementById('maxCharsPerBatch');
                const valueDisplay = document.getElementById('batchSizeValue');
                if (rangeInput) rangeInput.value = lastConfig.max_chars_per_batch;
                if (valueDisplay) valueDisplay.textContent = lastConfig.max_chars_per_batch;
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