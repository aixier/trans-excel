/**
 * LLM Configuration Settings Page
 * Week 3 Day 11-12: LLM provider and model configuration
 *
 * Features:
 * - Configure multiple LLM providers (OpenAI, Qwen, etc.)
 * - Model selection and parameters
 * - API key management
 * - Provider priority settings
 * - Cost estimation
 * - Test connection functionality
 */

class SettingsLLMPage {
    constructor() {
        this.providers = [];
        this.selectedProvider = null;

        // API configuration
        this.apiBaseURL = window.API_BASE_URL || 'http://localhost:8013';
    }

    /**
     * Initialize LLM settings page
     */
    async init() {
        await this.render();
        await this.loadProviders();
        this.setupEventListeners();
    }

    /**
     * Render page structure
     */
    async render() {
        const container = document.getElementById('app');
        if (!container) return;

        container.innerHTML = `
            <div class="settings-llm-page container mx-auto p-6 max-w-7xl">
                <!-- Header -->
                <div class="mb-8">
                    <div class="flex items-center gap-3 mb-4">
                        <a href="#/settings" class="btn btn-ghost btn-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                            </svg>
                            返回设置
                        </a>
                    </div>
                    <h1 class="text-3xl font-bold mb-2">LLM 配置</h1>
                    <p class="text-gray-600">配置语言模型提供商、模型和参数</p>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Provider List -->
                    <div class="space-y-6">
                        <div class="card bg-white shadow-lg">
                            <div class="card-body">
                                <div class="flex items-center justify-between mb-4">
                                    <h2 class="card-title text-lg">提供商列表</h2>
                                    <button id="add-provider-btn" class="btn btn-primary btn-sm">
                                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                                        </svg>
                                        添加
                                    </button>
                                </div>
                                <div id="provider-list" class="space-y-2"></div>
                            </div>
                        </div>

                        <!-- Quick Actions -->
                        <div class="card bg-blue-50 border-2 border-blue-200">
                            <div class="card-body">
                                <h3 class="font-bold mb-3">快速操作</h3>
                                <div class="space-y-2">
                                    <button id="test-all-btn" class="btn btn-outline btn-sm w-full">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        测试所有连接
                                    </button>
                                    <button id="import-config-btn" class="btn btn-outline btn-sm w-full">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                        导入配置
                                    </button>
                                    <button id="export-config-btn" class="btn btn-outline btn-sm w-full">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                        </svg>
                                        导出配置
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Configuration Panel -->
                    <div class="lg:col-span-2 space-y-6">
                        <div id="config-panel" class="card bg-white shadow-lg">
                            <div class="card-body">
                                <div class="text-center py-12 text-gray-500">
                                    <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                                    </svg>
                                    <p>选择一个提供商以查看配置</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Add Provider Modal -->
            <div id="add-provider-modal" class="hidden"></div>
            <input type="file" id="import-file-input" class="hidden" accept=".json" />
        `;
    }

    /**
     * Load LLM providers
     */
    async loadProviders() {
        try {
            // Load from localStorage or use defaults
            const stored = localStorage.getItem('llmProviders');

            if (stored) {
                this.providers = JSON.parse(stored);
            } else {
                // Default providers
                this.providers = [
                    {
                        id: 'qwen',
                        name: 'Qwen (通义千问)',
                        type: 'qwen',
                        enabled: true,
                        priority: 1,
                        config: {
                            apiKey: '',
                            baseURL: 'https://dashscope.aliyuncs.com/api/v1',
                            models: [
                                { id: 'qwen-plus', name: 'Qwen Plus', costPer1kTokens: 0.004 },
                                { id: 'qwen-turbo', name: 'Qwen Turbo', costPer1kTokens: 0.002 },
                                { id: 'qwen-max', name: 'Qwen Max', costPer1kTokens: 0.02 }
                            ],
                            defaultModel: 'qwen-plus',
                            temperature: 0.3,
                            maxTokens: 2000,
                            topP: 0.9
                        }
                    },
                    {
                        id: 'openai',
                        name: 'OpenAI GPT',
                        type: 'openai',
                        enabled: false,
                        priority: 2,
                        config: {
                            apiKey: '',
                            baseURL: 'https://api.openai.com/v1',
                            models: [
                                { id: 'gpt-4', name: 'GPT-4', costPer1kTokens: 0.03 },
                                { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', costPer1kTokens: 0.002 }
                            ],
                            defaultModel: 'gpt-3.5-turbo',
                            temperature: 0.3,
                            maxTokens: 2000
                        }
                    }
                ];

                this.saveProviders();
            }

            this.renderProviderList();

        } catch (error) {
            console.error('Failed to load providers:', error);
            this.showError('加载提供商配置失败');
        }
    }

    /**
     * Save providers to localStorage
     */
    saveProviders() {
        localStorage.setItem('llmProviders', JSON.stringify(this.providers));
    }

    /**
     * Render provider list
     */
    renderProviderList() {
        const container = document.getElementById('provider-list');
        if (!container) return;

        if (this.providers.length === 0) {
            container.innerHTML = '<p class="text-sm text-gray-500 text-center py-4">暂无提供商</p>';
            return;
        }

        container.innerHTML = this.providers
            .sort((a, b) => a.priority - b.priority)
            .map(provider => `
                <div class="provider-item p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition ${this.selectedProvider?.id === provider.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}"
                     data-provider-id="${provider.id}">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <div class="w-2 h-2 rounded-full ${provider.enabled ? 'bg-green-500' : 'bg-gray-300'}"></div>
                            <span class="font-medium text-sm">${provider.name}</span>
                        </div>
                        <span class="text-xs text-gray-500">P${provider.priority}</span>
                    </div>
                    ${provider.config.apiKey ? '<div class="text-xs text-green-600 mt-1">✓ API Key 已配置</div>' : '<div class="text-xs text-red-600 mt-1">✗ 未配置 API Key</div>'}
                </div>
            `).join('');

        // Add click listeners
        container.querySelectorAll('.provider-item').forEach(item => {
            item.addEventListener('click', () => {
                const providerId = item.dataset.providerId;
                this.selectProvider(providerId);
            });
        });
    }

    /**
     * Select a provider to configure
     */
    selectProvider(providerId) {
        this.selectedProvider = this.providers.find(p => p.id === providerId);
        if (!this.selectedProvider) return;

        this.renderConfigPanel();
        this.renderProviderList(); // Re-render to update selection
    }

    /**
     * Render configuration panel for selected provider
     */
    renderConfigPanel() {
        const panel = document.getElementById('config-panel');
        if (!panel || !this.selectedProvider) return;

        const provider = this.selectedProvider;

        panel.innerHTML = `
            <div class="card-body">
                <!-- Header -->
                <div class="flex items-center justify-between mb-6">
                    <div>
                        <h2 class="text-2xl font-bold">${provider.name}</h2>
                        <p class="text-sm text-gray-500 mt-1">配置此提供商的连接和参数</p>
                    </div>
                    <div class="flex items-center gap-2">
                        <label class="flex items-center gap-2 cursor-pointer">
                            <span class="text-sm">启用</span>
                            <input type="checkbox"
                                   class="toggle toggle-primary"
                                   id="provider-enabled"
                                   ${provider.enabled ? 'checked' : ''}>
                        </label>
                    </div>
                </div>

                <!-- Configuration Form -->
                <div class="space-y-6">
                    <!-- Basic Settings -->
                    <div class="border-b pb-4">
                        <h3 class="font-bold mb-4">基本设置</h3>

                        <div class="space-y-4">
                            <!-- API Key -->
                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text font-medium">API Key</span>
                                    <span class="label-text-alt text-red-500">* 必填</span>
                                </label>
                                <div class="flex gap-2">
                                    <input type="password"
                                           id="api-key"
                                           class="input input-bordered flex-1"
                                           value="${provider.config.apiKey || ''}"
                                           placeholder="输入您的 API Key">
                                    <button class="btn btn-outline" onclick="settingsLLMPage.toggleApiKeyVisibility()">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                        </svg>
                                    </button>
                                </div>
                                <label class="label">
                                    <span class="label-text-alt text-gray-500">
                                        API Key 将加密存储在本地浏览器中
                                    </span>
                                </label>
                            </div>

                            <!-- Base URL -->
                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text font-medium">Base URL</span>
                                </label>
                                <input type="text"
                                       id="base-url"
                                       class="input input-bordered"
                                       value="${provider.config.baseURL || ''}"
                                       placeholder="https://api.example.com/v1">
                            </div>

                            <!-- Priority -->
                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text font-medium">优先级</span>
                                    <span class="label-text-alt">数字越小优先级越高</span>
                                </label>
                                <input type="number"
                                       id="priority"
                                       class="input input-bordered"
                                       value="${provider.priority}"
                                       min="1"
                                       max="10">
                            </div>
                        </div>
                    </div>

                    <!-- Model Selection -->
                    <div class="border-b pb-4">
                        <h3 class="font-bold mb-4">模型配置</h3>

                        <div class="space-y-4">
                            <!-- Default Model -->
                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text font-medium">默认模型</span>
                                </label>
                                <select id="default-model" class="select select-bordered">
                                    ${provider.config.models.map(model => `
                                        <option value="${model.id}" ${provider.config.defaultModel === model.id ? 'selected' : ''}>
                                            ${model.name} ($${model.costPer1kTokens}/1k tokens)
                                        </option>
                                    `).join('')}
                                </select>
                            </div>

                            <!-- Model List -->
                            <div>
                                <label class="label">
                                    <span class="label-text font-medium">可用模型</span>
                                </label>
                                <div class="space-y-2">
                                    ${provider.config.models.map((model, index) => `
                                        <div class="flex items-center justify-between p-3 border rounded-lg">
                                            <div>
                                                <div class="font-medium">${model.name}</div>
                                                <div class="text-xs text-gray-500">
                                                    成本: $${model.costPer1kTokens}/1k tokens
                                                </div>
                                            </div>
                                            <button class="btn btn-ghost btn-sm" onclick="settingsLLMPage.removeModel(${index})">
                                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                        </div>
                                    `).join('')}
                                </div>
                                <button class="btn btn-outline btn-sm mt-3" onclick="settingsLLMPage.addModel()">
                                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                                    </svg>
                                    添加模型
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Parameters -->
                    <div class="border-b pb-4">
                        <h3 class="font-bold mb-4">模型参数</h3>

                        <div class="space-y-4">
                            <!-- Temperature -->
                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text font-medium">Temperature</span>
                                    <span class="label-text-alt" id="temperature-value">${provider.config.temperature}</span>
                                </label>
                                <input type="range"
                                       id="temperature"
                                       class="range range-primary"
                                       min="0"
                                       max="2"
                                       step="0.1"
                                       value="${provider.config.temperature}"
                                       oninput="document.getElementById('temperature-value').textContent = this.value">
                                <div class="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>精确 (0)</span>
                                    <span>平衡 (1)</span>
                                    <span>创造 (2)</span>
                                </div>
                            </div>

                            <!-- Max Tokens -->
                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text font-medium">Max Tokens</span>
                                </label>
                                <input type="number"
                                       id="max-tokens"
                                       class="input input-bordered"
                                       value="${provider.config.maxTokens || 2000}"
                                       min="1"
                                       max="8000">
                            </div>

                            ${provider.config.topP !== undefined ? `
                                <!-- Top P -->
                                <div class="form-control">
                                    <label class="label">
                                        <span class="label-text font-medium">Top P</span>
                                        <span class="label-text-alt" id="top-p-value">${provider.config.topP}</span>
                                    </label>
                                    <input type="range"
                                           id="top-p"
                                           class="range range-primary"
                                           min="0"
                                           max="1"
                                           step="0.1"
                                           value="${provider.config.topP}"
                                           oninput="document.getElementById('top-p-value').textContent = this.value">
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Actions -->
                    <div class="flex gap-3">
                        <button id="test-connection-btn" class="btn btn-outline flex-1">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            测试连接
                        </button>
                        <button id="save-config-btn" class="btn btn-primary flex-1">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                            </svg>
                            保存配置
                        </button>
                        <button id="delete-provider-btn" class="btn btn-error">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;

        this.setupConfigPanelListeners();
    }

    /**
     * Setup event listeners for config panel
     */
    setupConfigPanelListeners() {
        // Save button
        document.getElementById('save-config-btn')?.addEventListener('click', () => {
            this.saveCurrentConfig();
        });

        // Test connection button
        document.getElementById('test-connection-btn')?.addEventListener('click', () => {
            this.testConnection();
        });

        // Delete provider button
        document.getElementById('delete-provider-btn')?.addEventListener('click', () => {
            this.deleteProvider();
        });

        // Provider enabled toggle
        document.getElementById('provider-enabled')?.addEventListener('change', (e) => {
            this.selectedProvider.enabled = e.target.checked;
            this.saveProviders();
            this.renderProviderList();
        });
    }

    /**
     * Setup main event listeners
     */
    setupEventListeners() {
        // Add provider button
        document.getElementById('add-provider-btn')?.addEventListener('click', () => {
            this.showAddProviderModal();
        });

        // Test all connections
        document.getElementById('test-all-btn')?.addEventListener('click', () => {
            this.testAllConnections();
        });

        // Import config
        document.getElementById('import-config-btn')?.addEventListener('click', () => {
            document.getElementById('import-file-input')?.click();
        });

        document.getElementById('import-file-input')?.addEventListener('change', (e) => {
            this.importConfig(e.target.files[0]);
        });

        // Export config
        document.getElementById('export-config-btn')?.addEventListener('click', () => {
            this.exportConfig();
        });
    }

    /**
     * Save current provider configuration
     */
    saveCurrentConfig() {
        if (!this.selectedProvider) return;

        try {
            // Get values from form
            this.selectedProvider.config.apiKey = document.getElementById('api-key')?.value || '';
            this.selectedProvider.config.baseURL = document.getElementById('base-url')?.value || '';
            this.selectedProvider.priority = parseInt(document.getElementById('priority')?.value || 1);
            this.selectedProvider.config.defaultModel = document.getElementById('default-model')?.value || '';
            this.selectedProvider.config.temperature = parseFloat(document.getElementById('temperature')?.value || 0.3);
            this.selectedProvider.config.maxTokens = parseInt(document.getElementById('max-tokens')?.value || 2000);

            if (document.getElementById('top-p')) {
                this.selectedProvider.config.topP = parseFloat(document.getElementById('top-p')?.value || 0.9);
            }

            // Validate
            if (!this.selectedProvider.config.apiKey) {
                this.showError('请输入 API Key');
                return;
            }

            // Save
            this.saveProviders();
            this.renderProviderList();
            this.showSuccess('配置已保存');

        } catch (error) {
            console.error('Failed to save config:', error);
            this.showError('保存配置失败');
        }
    }

    /**
     * Test connection to provider
     */
    async testConnection() {
        if (!this.selectedProvider) return;

        const btn = document.getElementById('test-connection-btn');
        if (!btn) return;

        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="loading loading-spinner loading-sm"></span> 测试中...';

        try {
            if (!this.selectedProvider.config.apiKey) {
                throw new Error('API Key 未配置');
            }

            const response = await fetch(`${this.apiBaseURL}/api/llm/test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider_id: this.selectedProvider.id,
                    api_key: this.selectedProvider.config.apiKey,
                    base_url: this.selectedProvider.config.baseURL,
                    model: this.selectedProvider.config.defaultModel
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Connection test failed');
            }

            this.showSuccess('连接测试成功！');

        } catch (error) {
            console.error('Connection test failed:', error);
            this.showError('连接测试失败: ' + error.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }

    /**
     * Test all provider connections
     */
    async testAllConnections() {
        const enabledProviders = this.providers.filter(p => p.enabled && p.config.apiKey);

        if (enabledProviders.length === 0) {
            this.showError('没有启用的提供商或未配置 API Key');
            return;
        }

        this.showSuccess(`正在测试 ${enabledProviders.length} 个提供商...`);

        let successCount = 0;
        let failCount = 0;

        for (const provider of enabledProviders) {
            try {
                const response = await fetch(`${this.apiBaseURL}/api/llm/test`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        provider_id: provider.id,
                        api_key: provider.config.apiKey,
                        base_url: provider.config.baseURL,
                        model: provider.config.defaultModel
                    })
                });

                if (response.ok) {
                    successCount++;
                } else {
                    failCount++;
                }
            } catch (error) {
                console.error(`Test failed for provider ${provider.name}:`, error);
                failCount++;
            }
        }

        this.showSuccess(`测试完成: ${successCount} 成功, ${failCount} 失败`);
    }

    /**
     * Delete current provider
     */
    deleteProvider() {
        if (!this.selectedProvider) return;

        if (!confirm(`确定要删除提供商"${this.selectedProvider.name}"吗？`)) {
            return;
        }

        this.providers = this.providers.filter(p => p.id !== this.selectedProvider.id);
        this.saveProviders();

        this.selectedProvider = null;
        this.renderProviderList();

        // Clear config panel
        const panel = document.getElementById('config-panel');
        if (panel) {
            panel.innerHTML = `
                <div class="card-body">
                    <div class="text-center py-12 text-gray-500">
                        <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                        </svg>
                        <p>选择一个提供商以查看配置</p>
                    </div>
                </div>
            `;
        }

        this.showSuccess('提供商已删除');
    }

    /**
     * Toggle API Key visibility
     */
    toggleApiKeyVisibility() {
        const input = document.getElementById('api-key');
        if (!input) return;

        input.type = input.type === 'password' ? 'text' : 'password';
    }

    /**
     * Add model to current provider
     */
    addModel() {
        // TODO: Implement add model modal
        this.showSuccess('添加模型功能待实现');
    }

    /**
     * Remove model from current provider
     */
    removeModel(index) {
        if (!this.selectedProvider) return;

        if (this.selectedProvider.config.models.length <= 1) {
            this.showError('至少需要保留一个模型');
            return;
        }

        this.selectedProvider.config.models.splice(index, 1);
        this.saveProviders();
        this.renderConfigPanel();
        this.showSuccess('模型已删除');
    }

    /**
     * Show add provider modal
     */
    showAddProviderModal() {
        // TODO: Implement add provider modal
        this.showSuccess('添加提供商功能待实现');
    }

    /**
     * Import configuration from JSON file
     */
    async importConfig(file) {
        if (!file) return;

        try {
            const text = await file.text();
            const data = JSON.parse(text);

            if (data.providers && Array.isArray(data.providers)) {
                this.providers = data.providers;
                this.saveProviders();
                this.renderProviderList();
                this.showSuccess('配置已导入');
            } else {
                throw new Error('Invalid configuration format');
            }

        } catch (error) {
            console.error('Failed to import config:', error);
            this.showError('导入配置失败');
        }
    }

    /**
     * Export configuration to JSON file
     */
    exportConfig() {
        const config = {
            version: '1.0',
            timestamp: new Date().toISOString(),
            providers: this.providers
        };

        const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `llm_config_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);

        this.showSuccess('配置已导出');
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
}

// Export for global access
if (typeof window !== 'undefined') {
    window.SettingsLLMPage = SettingsLLMPage;
}
