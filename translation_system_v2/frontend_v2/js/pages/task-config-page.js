/**
 * Task Configuration Page
 * Week 2 Day 8-9: Dynamic rule selector, parameter configuration, template management
 *
 * Features:
 * - Dynamic rule selector with enable/disable
 * - Parameter configuration panel for each rule
 * - Configuration templates (presets)
 * - Configuration validation
 * - Export/Import configuration
 * - Real-time configuration preview
 */

class TaskConfigPage {
    constructor() {
        this.sessionId = null;
        this.availableRules = [];
        this.availableProcessors = [];
        this.currentConfig = {
            sessionId: null,
            ruleSet: 'translation', // Default rule set
            rules: [],
            processor: 'llm_qwen', // Default processor
            parameters: {},
            sourceLang: 'CH',
            targetLangs: ['EN']
        };
        this.configTemplates = [];

        // API configuration
        this.apiBaseURL = window.API_BASE_URL || 'http://localhost:8013';
    }

    /**
     * Initialize task config page
     */
    async init(sessionId) {
        this.sessionId = sessionId;
        this.currentConfig.sessionId = sessionId;

        await this.render();
        await this.loadAvailableOptions();
        await this.loadTemplates();
        await this.loadSessionInfo();

        this.setupRuleSelector();
        this.setupProcessorSelector();
        this.setupLanguageSelector();
        this.setupParameterPanel();
        this.setupTemplateManager();
        this.setupActions();
    }

    /**
     * Render page structure
     */
    async render() {
        const container = document.getElementById('app');
        if (!container) return;

        container.innerHTML = `
            <div class="task-config-page container mx-auto p-6 max-w-7xl">
                <!-- Header -->
                <div class="mb-8">
                    <div class="flex items-center justify-between">
                        <div>
                            <h1 class="text-3xl font-bold mb-2">任务配置</h1>
                            <p class="text-gray-600" id="session-info">Session ID: ${this.sessionId || '加载中...'}</p>
                        </div>
                        <div class="space-x-2">
                            <button id="load-template-btn" class="btn btn-outline">
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                                加载模板
                            </button>
                            <button id="save-template-btn" class="btn btn-outline">
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                                </svg>
                                保存为模板
                            </button>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Left Column: Configuration -->
                    <div class="lg:col-span-2 space-y-6">
                        <!-- Language Selection -->
                        <div class="card bg-white shadow-lg">
                            <div class="card-body">
                                <h2 class="card-title text-xl mb-4">语言配置</h2>
                                <div id="language-selector"></div>
                            </div>
                        </div>

                        <!-- Rule Selection -->
                        <div class="card bg-white shadow-lg">
                            <div class="card-body">
                                <h2 class="card-title text-xl mb-4">拆分规则</h2>
                                <div id="rule-selector" class="space-y-4"></div>
                            </div>
                        </div>

                        <!-- Processor Selection -->
                        <div class="card bg-white shadow-lg">
                            <div class="card-body">
                                <h2 class="card-title text-xl mb-4">处理器配置</h2>
                                <div id="processor-selector"></div>
                            </div>
                        </div>

                        <!-- Parameter Configuration -->
                        <div class="card bg-white shadow-lg" id="parameter-panel">
                            <div class="card-body">
                                <h2 class="card-title text-xl mb-4">参数配置</h2>
                                <div id="parameter-config"></div>
                            </div>
                        </div>
                    </div>

                    <!-- Right Column: Preview & Actions -->
                    <div class="space-y-6">
                        <!-- Configuration Preview -->
                        <div class="card bg-white shadow-lg sticky top-6">
                            <div class="card-body">
                                <h2 class="card-title text-lg mb-4">配置预览</h2>
                                <div id="config-preview" class="text-sm">
                                    <pre class="bg-gray-50 p-4 rounded overflow-auto max-h-96"></pre>
                                </div>
                            </div>
                        </div>

                        <!-- Actions -->
                        <div class="card bg-white shadow-lg">
                            <div class="card-body">
                                <h2 class="card-title text-lg mb-4">操作</h2>
                                <div class="space-y-3">
                                    <button id="validate-config-btn" class="btn btn-outline w-full">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        验证配置
                                    </button>
                                    <button id="export-config-btn" class="btn btn-outline w-full">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                        </svg>
                                        导出配置
                                    </button>
                                    <button id="import-config-btn" class="btn btn-outline w-full">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                        导入配置
                                    </button>
                                    <input type="file" id="config-file-input" class="hidden" accept=".json" />
                                    <div class="divider"></div>
                                    <button id="apply-config-btn" class="btn btn-primary w-full">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                        </svg>
                                        应用配置并开始
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- Estimation (if available) -->
                        <div class="card bg-blue-50 border-2 border-blue-200">
                            <div class="card-body">
                                <h2 class="card-title text-lg mb-4">预估</h2>
                                <div id="estimation-info" class="space-y-2 text-sm">
                                    <p class="text-gray-500">配置完成后将显示预估信息</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Template Modal (hidden by default) -->
            <div id="template-modal" class="hidden"></div>
        `;

        this.updateConfigPreview();
    }

    /**
     * Load available rules and processors from backend
     */
    async loadAvailableOptions() {
        try {
            const response = await fetch(`${this.apiBaseURL}/api/config/options`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            this.availableRules = data.rules || [];
            this.availableProcessors = data.processors || [];

        } catch (error) {
            console.error('Failed to load available options:', error);
            this.showError('加载配置选项失败: ' + error.message);
        }
    }

    /**
     * Load configuration templates from localStorage
     */
    async loadTemplates() {
        try {
            const response = await fetch(`${this.apiBaseURL}/api/config/templates`);
            if (response.ok) {
                const data = await response.json();
                this.configTemplates = data.templates || [];
            } else {
                const stored = localStorage.getItem('configTemplates');
                this.configTemplates = stored ? JSON.parse(stored) : [];
            }
        } catch (error) {
            console.error('Failed to load templates from API, using localStorage:', error);
            const stored = localStorage.getItem('configTemplates');
            this.configTemplates = stored ? JSON.parse(stored) : [];
        }
    }

    /**
     * Load session information
     */
    async loadSessionInfo() {
        try {
            const response = await fetch(`${this.apiBaseURL}/api/tasks/status/${this.sessionId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            const sessionInfo = document.getElementById('session-info');
            if (sessionInfo) {
                sessionInfo.innerHTML = `
                    Session ID: <code class="bg-gray-100 px-2 py-1 rounded">${this.sessionId}</code><br>
                    <span class="text-sm text-gray-500">状态: ${data.stage || 'Unknown'} • 任务数: ${data.tasks_count || 0}</span>
                `;
            }
        } catch (error) {
            console.error('Failed to load session info:', error);
            const sessionInfo = document.getElementById('session-info');
            if (sessionInfo) {
                sessionInfo.innerHTML = `
                    Session ID: <code class="bg-gray-100 px-2 py-1 rounded">${this.sessionId}</code>
                    <span class="text-sm text-red-500 ml-2">加载失败</span>
                `;
            }
        }
    }

    /**
     * Setup language selector
     */
    setupLanguageSelector() {
        const container = document.getElementById('language-selector');
        if (!container) return;

        const languages = ['CH', 'EN', 'JP', 'TH', 'PT', 'VN'];

        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- Source Language -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text font-medium">源语言</span>
                    </label>
                    <select id="source-lang-select" class="select select-bordered w-full">
                        ${languages.map(lang => `
                            <option value="${lang}" ${this.currentConfig.sourceLang === lang ? 'selected' : ''}>${lang}</option>
                        `).join('')}
                    </select>
                </div>

                <!-- Target Languages -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text font-medium">目标语言（可多选）</span>
                    </label>
                    <div class="space-y-2">
                        ${languages.map(lang => `
                            <label class="flex items-center space-x-2 cursor-pointer">
                                <input type="checkbox"
                                       class="checkbox checkbox-primary checkbox-sm target-lang-checkbox"
                                       value="${lang}"
                                       ${this.currentConfig.targetLangs.includes(lang) ? 'checked' : ''}>
                                <span class="text-sm">${lang}</span>
                            </label>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        // Event listeners
        document.getElementById('source-lang-select').addEventListener('change', (e) => {
            this.currentConfig.sourceLang = e.target.value;
            this.updateConfigPreview();
        });

        document.querySelectorAll('.target-lang-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.currentConfig.targetLangs = Array.from(
                    document.querySelectorAll('.target-lang-checkbox:checked')
                ).map(cb => cb.value);
                this.updateConfigPreview();
                this.updateEstimation();
            });
        });
    }

    /**
     * Setup rule selector
     */
    setupRuleSelector() {
        const container = document.getElementById('rule-selector');
        if (!container) return;

        container.innerHTML = this.availableRules.map(rule => `
            <div class="rule-item border-2 rounded-lg p-4 ${rule.enabled ? 'border-blue-200 bg-blue-50' : 'border-gray-200'}">
                <div class="flex items-start">
                    <input type="checkbox"
                           class="checkbox checkbox-primary mt-1 rule-checkbox"
                           data-rule-id="${rule.id}"
                           ${rule.enabled ? 'checked' : ''}>
                    <div class="ml-3 flex-1">
                        <div class="flex items-center gap-2">
                            <span class="font-medium text-lg">${rule.name}</span>
                            ${rule.requiresTranslationFirst ? '<span class="badge badge-warning badge-sm">需要先翻译</span>' : ''}
                        </div>
                        <p class="text-sm text-gray-600 mt-1">${rule.description}</p>
                        <div class="mt-2 flex items-center gap-3">
                            <span class="badge badge-outline">优先级: ${rule.priority}</span>
                            ${rule.parameters && Object.keys(rule.parameters).length > 0 ? `
                                <button class="text-blue-600 text-sm hover:underline configure-rule-btn"
                                        data-rule-id="${rule.id}">
                                    <svg class="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    </svg>
                                    配置参数
                                </button>
                            ` : ''}
                        </div>
                        <!-- Parameter Config (hidden by default) -->
                        <div class="rule-params mt-3 p-3 bg-white rounded border hidden" id="params-${rule.id}"></div>
                    </div>
                </div>
            </div>
        `).join('');

        // Event listeners
        document.querySelectorAll('.rule-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const ruleId = e.target.dataset.ruleId;
                const rule = this.availableRules.find(r => r.id === ruleId);

                if (e.target.checked) {
                    if (!this.currentConfig.rules.includes(ruleId)) {
                        this.currentConfig.rules.push(ruleId);
                    }
                    e.target.closest('.rule-item').classList.add('border-blue-200', 'bg-blue-50');
                    e.target.closest('.rule-item').classList.remove('border-gray-200');
                } else {
                    this.currentConfig.rules = this.currentConfig.rules.filter(r => r !== ruleId);
                    e.target.closest('.rule-item').classList.remove('border-blue-200', 'bg-blue-50');
                    e.target.closest('.rule-item').classList.add('border-gray-200');
                }

                this.updateConfigPreview();
                this.updateEstimation();
            });
        });

        // Configure rule buttons
        document.querySelectorAll('.configure-rule-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const ruleId = e.target.closest('.configure-rule-btn').dataset.ruleId;
                this.showRuleParameters(ruleId);
            });
        });
    }

    /**
     * Show rule parameters configuration
     */
    showRuleParameters(ruleId) {
        const rule = this.availableRules.find(r => r.id === ruleId);
        if (!rule) return;

        const container = document.getElementById(`params-${ruleId}`);
        if (!container) return;

        // Toggle visibility
        container.classList.toggle('hidden');

        if (!container.classList.contains('hidden')) {
            container.innerHTML = `
                <p class="text-sm font-medium mb-3">参数配置</p>
                ${Object.entries(rule.parameters).map(([key, param]) => {
                    return this.renderParameter(ruleId, key, param);
                }).join('')}
            `;

            // Setup parameter change listeners
            container.querySelectorAll('input, select').forEach(input => {
                input.addEventListener('change', (e) => {
                    if (!this.currentConfig.parameters[ruleId]) {
                        this.currentConfig.parameters[ruleId] = {};
                    }

                    const value = e.target.type === 'checkbox' ? e.target.checked :
                                 e.target.type === 'number' ? parseFloat(e.target.value) :
                                 e.target.value;

                    this.currentConfig.parameters[ruleId][e.target.name] = value;
                    this.updateConfigPreview();
                });
            });
        }
    }

    /**
     * Setup processor selector
     */
    setupProcessorSelector() {
        const container = document.getElementById('processor-selector');
        if (!container) return;

        container.innerHTML = `
            <div class="space-y-4">
                ${this.availableProcessors.map(processor => `
                    <label class="flex items-start p-4 border-2 rounded-lg cursor-pointer hover:bg-gray-50 ${this.currentConfig.processor === processor.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}">
                        <input type="radio"
                               name="processor"
                               class="radio radio-primary mt-1"
                               value="${processor.id}"
                               ${this.currentConfig.processor === processor.id ? 'checked' : ''}>
                        <div class="ml-3 flex-1">
                            <div class="font-medium text-lg">${processor.name}</div>
                            <p class="text-sm text-gray-600 mt-1">${processor.description}</p>
                            <div class="mt-2">
                                <span class="badge badge-outline">${processor.type}</span>
                                ${processor.requiresLLM === false ? '<span class="badge badge-success badge-sm ml-2">无需LLM</span>' : ''}
                            </div>
                        </div>
                    </label>
                `).join('')}
            </div>
        `;

        // Event listener
        document.querySelectorAll('input[name="processor"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentConfig.processor = e.target.value;

                // Update visual feedback
                document.querySelectorAll('label:has(input[name="processor"])').forEach(label => {
                    label.classList.remove('border-blue-500', 'bg-blue-50');
                    label.classList.add('border-gray-200');
                });
                e.target.closest('label').classList.add('border-blue-500', 'bg-blue-50');
                e.target.closest('label').classList.remove('border-gray-200');

                this.updateConfigPreview();
                this.setupParameterPanel();
            });
        });
    }

    /**
     * Setup parameter configuration panel
     */
    setupParameterPanel() {
        const container = document.getElementById('parameter-config');
        if (!container) return;

        const processor = this.availableProcessors.find(p => p.id === this.currentConfig.processor);
        if (!processor || !processor.parameters) {
            container.innerHTML = '<p class="text-gray-500">此处理器无需额外参数</p>';
            return;
        }

        container.innerHTML = `
            <div class="space-y-4">
                ${Object.entries(processor.parameters).map(([key, param]) => {
                    return this.renderParameter(processor.id, key, param);
                }).join('')}
            </div>
        `;

        // Setup parameter change listeners
        container.querySelectorAll('input, select').forEach(input => {
            input.addEventListener('change', (e) => {
                if (!this.currentConfig.parameters[processor.id]) {
                    this.currentConfig.parameters[processor.id] = {};
                }

                const value = e.target.type === 'checkbox' ? e.target.checked :
                             e.target.type === 'number' ? parseFloat(e.target.value) :
                             e.target.value;

                this.currentConfig.parameters[processor.id][e.target.name] = value;
                this.updateConfigPreview();
            });
        });
    }

    /**
     * Render a single parameter input
     */
    renderParameter(componentId, key, param) {
        const currentValue = this.currentConfig.parameters[componentId]?.[key] ?? param.default;

        switch (param.type) {
            case 'boolean':
                return `
                    <div class="form-control">
                        <label class="label cursor-pointer justify-start gap-3">
                            <input type="checkbox"
                                   name="${key}"
                                   class="checkbox checkbox-primary checkbox-sm"
                                   ${currentValue ? 'checked' : ''}>
                            <span class="label-text">${param.label}</span>
                        </label>
                    </div>
                `;

            case 'number':
                return `
                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">${param.label}</span>
                        </label>
                        <input type="number"
                               name="${key}"
                               class="input input-bordered input-sm"
                               min="${param.min}"
                               max="${param.max}"
                               step="${param.step}"
                               value="${currentValue}">
                    </div>
                `;

            case 'select':
                return `
                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">${param.label}</span>
                        </label>
                        <select name="${key}" class="select select-bordered select-sm">
                            ${param.options.map(opt => `
                                <option value="${opt}" ${currentValue === opt ? 'selected' : ''}>${opt}</option>
                            `).join('')}
                        </select>
                    </div>
                `;

            case 'text':
            default:
                return `
                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">${param.label}</span>
                        </label>
                        <input type="text"
                               name="${key}"
                               class="input input-bordered input-sm"
                               value="${currentValue}">
                    </div>
                `;
        }
    }

    /**
     * Setup template manager
     */
    setupTemplateManager() {
        const loadBtn = document.getElementById('load-template-btn');
        const saveBtn = document.getElementById('save-template-btn');

        if (loadBtn) {
            loadBtn.addEventListener('click', () => this.showTemplateModal('load'));
        }

        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.showTemplateModal('save'));
        }
    }

    /**
     * Show template modal
     */
    showTemplateModal(mode) {
        const modalContainer = document.getElementById('template-modal');
        if (!modalContainer) return;

        modalContainer.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50';

        if (mode === 'load') {
            modalContainer.innerHTML = `
                <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
                    <div class="p-6 border-b">
                        <h3 class="text-xl font-bold">加载配置模板</h3>
                    </div>
                    <div class="p-6">
                        <div class="space-y-3">
                            ${this.configTemplates.map(template => {
                                const ruleInfo = template.config && template.config.rules
                                    ? template.config.rules.join(', ')
                                    : template.config && template.config.rule_set
                                    ? template.config.rule_set
                                    : '未配置';
                                const processorInfo = template.config && template.config.processor
                                    ? template.config.processor
                                    : '未配置';
                                return `
                                <div class="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer template-item"
                                     data-template-id="${template.id}">
                                    <div class="font-medium">${template.name}</div>
                                    <p class="text-sm text-gray-600 mt-1">${template.description}</p>
                                    <div class="mt-2 text-xs text-gray-500">
                                        规则集: ${ruleInfo} • 处理器: ${processorInfo}
                                    </div>
                                </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                    <div class="p-6 border-t">
                        <button class="btn w-full" onclick="taskConfigPage.closeTemplateModal()">取消</button>
                    </div>
                </div>
            `;

            // Template click handlers
            modalContainer.querySelectorAll('.template-item').forEach(item => {
                item.addEventListener('click', () => {
                    const templateId = item.dataset.templateId;
                    this.loadTemplate(templateId);
                    this.closeTemplateModal();
                });
            });

        } else if (mode === 'save') {
            modalContainer.innerHTML = `
                <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
                    <div class="p-6 border-b">
                        <h3 class="text-xl font-bold">保存为模板</h3>
                    </div>
                    <div class="p-6 space-y-4">
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">模板名称</span>
                            </label>
                            <input type="text" id="template-name" class="input input-bordered" placeholder="例如：标准翻译流程">
                        </div>
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">描述</span>
                            </label>
                            <textarea id="template-description" class="textarea textarea-bordered" rows="3" placeholder="简要描述此模板的用途"></textarea>
                        </div>
                    </div>
                    <div class="p-6 border-t flex gap-3">
                        <button class="btn flex-1" onclick="taskConfigPage.closeTemplateModal()">取消</button>
                        <button class="btn btn-primary flex-1" onclick="taskConfigPage.saveCurrentAsTemplate()">保存</button>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Load template
     */
    loadTemplate(templateId) {
        const template = this.configTemplates.find(t => t.id === templateId);
        if (!template) return;

        // Apply template config
        this.currentConfig = {
            ...this.currentConfig,
            ...template.config
        };

        // Re-render all sections
        this.setupRuleSelector();
        this.setupProcessorSelector();
        this.setupLanguageSelector();
        this.setupParameterPanel();
        this.updateConfigPreview();

        this.showSuccess(`已加载模板: ${template.name}`);
    }

    /**
     * Save current config as template
     */
    saveCurrentAsTemplate() {
        const name = document.getElementById('template-name')?.value;
        const description = document.getElementById('template-description')?.value;

        if (!name) {
            this.showError('请输入模板名称');
            return;
        }

        const template = {
            id: `custom_${Date.now()}`,
            name,
            description: description || '自定义模板',
            config: {
                ruleSet: this.currentConfig.ruleSet,
                rules: [...this.currentConfig.rules],
                processor: this.currentConfig.processor,
                parameters: JSON.parse(JSON.stringify(this.currentConfig.parameters)),
                sourceLang: this.currentConfig.sourceLang,
                targetLangs: [...this.currentConfig.targetLangs]
            }
        };

        this.configTemplates.push(template);
        localStorage.setItem('configTemplates', JSON.stringify(this.configTemplates));

        this.closeTemplateModal();
        this.showSuccess('模板保存成功');
    }

    /**
     * Close template modal
     */
    closeTemplateModal() {
        const modal = document.getElementById('template-modal');
        if (modal) {
            modal.className = 'hidden';
            modal.innerHTML = '';
        }
    }

    /**
     * Setup action buttons
     */
    setupActions() {
        // Validate config
        document.getElementById('validate-config-btn')?.addEventListener('click', () => {
            this.validateConfiguration();
        });

        // Export config
        document.getElementById('export-config-btn')?.addEventListener('click', () => {
            this.exportConfiguration();
        });

        // Import config
        document.getElementById('import-config-btn')?.addEventListener('click', () => {
            document.getElementById('config-file-input')?.click();
        });

        document.getElementById('config-file-input')?.addEventListener('change', (e) => {
            this.importConfiguration(e.target.files[0]);
        });

        // Apply config and start
        document.getElementById('apply-config-btn')?.addEventListener('click', () => {
            this.applyConfiguration();
        });
    }

    /**
     * Validate configuration
     */
    validateConfiguration() {
        const errors = [];

        if (this.currentConfig.rules.length === 0) {
            errors.push('至少选择一个拆分规则');
        }

        if (!this.currentConfig.processor) {
            errors.push('必须选择一个处理器');
        }

        if (this.currentConfig.targetLangs.length === 0) {
            errors.push('至少选择一个目标语言');
        }

        // Check if CAPS rule requires translation first
        if (this.currentConfig.rules.includes('caps')) {
            const hasTranslationRules = this.currentConfig.rules.some(r => ['empty', 'yellow', 'blue'].includes(r));
            if (!hasTranslationRules && this.currentConfig.processor !== 'llm_qwen' && this.currentConfig.processor !== 'llm_openai') {
                errors.push('CAPS规则需要先执行翻译，请添加翻译规则或使用LLM处理器');
            }
        }

        if (errors.length > 0) {
            this.showValidationErrors(errors);
        } else {
            this.showSuccess('配置验证通过');
        }

        return errors.length === 0;
    }

    /**
     * Show validation errors
     */
    showValidationErrors(errors) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
                <div class="p-6 border-b">
                    <h3 class="text-xl font-bold text-red-600">配置验证失败</h3>
                </div>
                <div class="p-6">
                    <ul class="list-disc list-inside space-y-2 text-red-600">
                        ${errors.map(err => `<li>${err}</li>`).join('')}
                    </ul>
                </div>
                <div class="p-6 border-t">
                    <button class="btn btn-primary w-full" onclick="this.closest('.fixed').remove()">确定</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    /**
     * Export configuration as JSON
     */
    exportConfiguration() {
        const config = {
            version: '1.0',
            timestamp: new Date().toISOString(),
            config: this.currentConfig
        };

        const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `config_${this.sessionId}_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);

        this.showSuccess('配置已导出');
    }

    /**
     * Import configuration from JSON file
     */
    async importConfiguration(file) {
        if (!file) return;

        try {
            const text = await file.text();
            const data = JSON.parse(text);

            if (data.config) {
                this.currentConfig = {
                    ...this.currentConfig,
                    ...data.config
                };

                // Re-render
                this.setupRuleSelector();
                this.setupProcessorSelector();
                this.setupLanguageSelector();
                this.setupParameterPanel();
                this.updateConfigPreview();

                this.showSuccess('配置已导入');
            }
        } catch (error) {
            this.showError('配置文件格式错误');
        }
    }

    /**
     * Apply configuration and start processing
     */
    async applyConfiguration() {
        if (!this.validateConfiguration()) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseURL}/api/execute/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    processor: this.currentConfig.processor,
                    parameters: this.currentConfig.parameters,
                    max_workers: this.currentConfig.parameters[this.currentConfig.processor]?.maxWorkers || 10
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.showSuccess('配置已应用，即将开始处理');

            setTimeout(() => {
                window.location.hash = `#/execute?session=${this.sessionId}`;
            }, 1500);

        } catch (error) {
            console.error('Failed to apply configuration:', error);
            this.showError('应用配置失败: ' + error.message);
        }
    }

    /**
     * Update configuration preview
     */
    updateConfigPreview() {
        const preview = document.querySelector('#config-preview pre');
        if (!preview) return;

        preview.textContent = JSON.stringify(this.currentConfig, null, 2);
    }

    /**
     * Update estimation based on config
     */
    async updateEstimation() {
        const container = document.getElementById('estimation-info');
        if (!container) return;

        try {
            const response = await fetch(`${this.apiBaseURL}/api/tasks/estimate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    rules: this.currentConfig.rules,
                    target_langs: this.currentConfig.targetLangs
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            container.innerHTML = `
                <div class="space-y-2">
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">预估任务数:</span>
                        <span class="font-medium">${data.task_count || 0}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">预估耗时:</span>
                        <span class="font-medium">${data.estimated_time || '计算中...'}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">预估成本:</span>
                        <span class="font-medium">${data.estimated_cost || '计算中...'}</span>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Failed to get estimation:', error);
            container.innerHTML = `<p class="text-gray-500 text-sm">预估信息加载失败</p>`;
        }
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

        setTimeout(() => toast.remove(), 3000);
    }
}

// Export for global access
if (typeof window !== 'undefined') {
    window.TaskConfigPage = TaskConfigPage;
}
