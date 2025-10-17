# 工程师D任务文档 - 流程优化与系统设置

## 一、角色定位与职责

### 1.1 角色定位
- **岗位**：流程优化与系统配置工程师
- **重点**：优化现有工作流程，实现系统配置管理
- **特点**：专注于用户体验提升和系统灵活性

### 1.2 核心职责
1. **工作流程优化**
   - 文件上传优化（拖拽、批量、预览）
   - 任务配置升级（规则选择、参数调整）
   - 翻译执行优化（批量处理、暂停恢复）
   - 结果下载升级（格式选择、批量导出）

2. **系统设置功能**
   - LLM配置管理（提供商、模型、参数）
   - 规则配置管理（启用/禁用、优先级）
   - 用户偏好设置（主题、语言、快捷键）
   - 系统监控面板（性能、日志、调试）

3. **集成测试**
   - 端到端测试编写
   - 浏览器兼容性测试
   - 性能测试与优化
   - 错误处理完善

### 1.3 工作量评估
- **总工作量**：13天（104小时）
- **每日工作时间**：8小时
- **并行开发**：从Week 2开始，不依赖Engineer A的基础组件

## 二、任务目标与成功标准

### 2.1 核心目标
1. **提升用户体验**
   - 文件上传成功率 > 99%
   - 任务配置错误率 < 1%
   - 翻译流程完成率 > 95%
   - 页面加载时间 < 2秒

2. **增强系统灵活性**
   - 支持3+种LLM提供商
   - 支持10+种翻译规则
   - 支持主题切换
   - 支持配置导入/导出

3. **保证系统质量**
   - 单元测试覆盖率 > 80%
   - E2E测试覆盖核心流程
   - 兼容Chrome/Firefox/Safari
   - 移动端基本可用

### 2.2 成功标准
- [ ] 工作流程页面全部优化完成
- [ ] 系统设置功能全部实现
- [ ] E2E测试覆盖所有核心流程
- [ ] 性能指标达到预期要求
- [ ] 通过UAT用户验收测试

## 三、详细任务清单

### 3.1 Week 2（第6-10天）- 工作流程优化

#### Day 6-7：文件上传优化
**任务ID**: D-W2-01
**预计工时**: 16小时
**依赖**: 无（可独立开发）

**任务内容**：
1. 实现拖拽上传功能
2. 支持批量文件上传
3. 文件预览功能
4. 上传进度显示
5. 文件验证增强

**核心代码实现**：

```javascript
// js/pages/upload-page.js
class UploadPage {
    constructor() {
        this.currentFiles = [];
        this.uploadZone = null;
        this.previewModal = null;
        this.validationRules = {
            maxSize: 50 * 1024 * 1024, // 50MB
            allowedTypes: ['.xlsx', '.xls'],
            maxSheets: 20,
            maxRows: 100000
        };
    }

    init() {
        this.setupUploadZone();
        this.setupBatchUpload();
        this.setupPreview();
        this.setupValidation();
    }

    setupUploadZone() {
        this.uploadZone = document.getElementById('upload-zone');

        // 拖拽事件
        this.uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadZone.classList.add('drag-over');
        });

        this.uploadZone.addEventListener('dragleave', () => {
            this.uploadZone.classList.remove('drag-over');
        });

        this.uploadZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            this.uploadZone.classList.remove('drag-over');

            const files = Array.from(e.dataTransfer.files);
            await this.handleFiles(files);
        });
    }

    async handleFiles(files) {
        // 批量文件处理
        const validFiles = [];
        const errors = [];

        for (const file of files) {
            const validation = await this.validateFile(file);
            if (validation.valid) {
                validFiles.push(file);
            } else {
                errors.push({
                    file: file.name,
                    errors: validation.errors
                });
            }
        }

        // 显示验证结果
        if (errors.length > 0) {
            this.showValidationErrors(errors);
        }

        // 处理有效文件
        if (validFiles.length > 0) {
            await this.processValidFiles(validFiles);
        }
    }

    async validateFile(file) {
        const errors = [];

        // 大小检查
        if (file.size > this.validationRules.maxSize) {
            errors.push(`文件大小超过限制（最大${this.validationRules.maxSize / 1024 / 1024}MB）`);
        }

        // 类型检查
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!this.validationRules.allowedTypes.includes(ext)) {
            errors.push(`不支持的文件类型（仅支持${this.validationRules.allowedTypes.join(', ')}）`);
        }

        // Excel内容检查
        if (errors.length === 0) {
            try {
                const content = await this.readExcelFile(file);
                if (content.sheets.length > this.validationRules.maxSheets) {
                    errors.push(`Sheet数量超过限制（最大${this.validationRules.maxSheets}个）`);
                }

                const totalRows = content.sheets.reduce((sum, sheet) => sum + sheet.rows, 0);
                if (totalRows > this.validationRules.maxRows) {
                    errors.push(`总行数超过限制（最大${this.validationRules.maxRows}行）`);
                }
            } catch (error) {
                errors.push('文件读取失败：' + error.message);
            }
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    async readExcelFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const data = new Uint8Array(e.target.result);
                    const workbook = XLSX.read(data, { type: 'array' });

                    const sheets = workbook.SheetNames.map(name => {
                        const sheet = workbook.Sheets[name];
                        const range = XLSX.utils.decode_range(sheet['!ref']);
                        return {
                            name,
                            rows: range.e.r - range.s.r + 1,
                            cols: range.e.c - range.s.c + 1
                        };
                    });

                    resolve({ sheets });
                } catch (error) {
                    reject(error);
                }
            };
            reader.onerror = reject;
            reader.readAsArrayBuffer(file);
        });
    }

    async processValidFiles(files) {
        // 显示上传进度
        const progressModal = this.showProgressModal(files);

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            progressModal.updateProgress(i, 0);

            try {
                // 创建FormData
                const formData = new FormData();
                formData.append('file', file);

                // 上传文件
                const response = await this.uploadWithProgress(
                    formData,
                    (progress) => progressModal.updateProgress(i, progress)
                );

                // 保存结果
                this.currentFiles.push({
                    file: file.name,
                    sessionId: response.session_id,
                    status: 'uploaded'
                });

                progressModal.updateProgress(i, 100);
            } catch (error) {
                progressModal.showError(i, error.message);
            }
        }

        // 显示批量上传结果
        this.showBatchResults();
    }

    async uploadWithProgress(formData, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const progress = (e.loaded / e.total) * 100;
                    onProgress(progress);
                }
            };

            xhr.onload = () => {
                if (xhr.status === 200) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(xhr.statusText));
                }
            };

            xhr.onerror = () => reject(new Error('网络错误'));

            xhr.open('POST', `${API.baseURL}/api/tasks/split`);
            xhr.send(formData);
        });
    }

    showProgressModal(files) {
        const modal = document.createElement('div');
        modal.className = 'modal modal-open';
        modal.innerHTML = `
            <div class="modal-box max-w-3xl">
                <h3 class="font-bold text-lg mb-4">上传进度</h3>
                <div class="space-y-4">
                    ${files.map((file, i) => `
                        <div class="upload-item" data-index="${i}">
                            <div class="flex justify-between mb-2">
                                <span class="text-sm">${file.name}</span>
                                <span class="progress-text">0%</span>
                            </div>
                            <progress class="progress progress-primary w-full" value="0" max="100"></progress>
                            <div class="error-message text-error text-sm mt-1 hidden"></div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        return {
            updateProgress(index, progress) {
                const item = modal.querySelector(`[data-index="${index}"]`);
                item.querySelector('.progress').value = progress;
                item.querySelector('.progress-text').textContent = `${Math.round(progress)}%`;
            },
            showError(index, message) {
                const item = modal.querySelector(`[data-index="${index}"]`);
                const errorDiv = item.querySelector('.error-message');
                errorDiv.textContent = message;
                errorDiv.classList.remove('hidden');
            },
            close() {
                modal.remove();
            }
        };
    }

    setupPreview() {
        // Excel预览功能
        this.previewModal = new ExcelPreviewModal();

        document.addEventListener('click', async (e) => {
            if (e.target.classList.contains('preview-btn')) {
                const sessionId = e.target.dataset.sessionId;
                await this.previewModal.show(sessionId);
            }
        });
    }
}

// Excel预览组件
class ExcelPreviewModal {
    async show(sessionId) {
        // 获取Excel数据
        const data = await API.getSessionData(sessionId);

        const modal = document.createElement('div');
        modal.className = 'modal modal-open';
        modal.innerHTML = `
            <div class="modal-box max-w-6xl">
                <h3 class="font-bold text-lg mb-4">文件预览</h3>
                <div class="tabs">
                    ${data.sheets.map((sheet, i) => `
                        <a class="tab ${i === 0 ? 'tab-active' : ''}"
                           data-sheet="${i}">${sheet.name}</a>
                    `).join('')}
                </div>
                <div class="preview-content mt-4">
                    <div class="overflow-x-auto">
                        <table class="table table-sm">
                            <!-- 动态渲染表格内容 -->
                        </table>
                    </div>
                </div>
                <div class="modal-action">
                    <button class="btn" onclick="this.closest('.modal').remove()">关闭</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.renderSheet(modal, data.sheets[0]);

        // Tab切换
        modal.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const index = parseInt(tab.dataset.sheet);
                this.renderSheet(modal, data.sheets[index]);
            });
        });
    }

    renderSheet(modal, sheet) {
        const table = modal.querySelector('table');
        // 渲染前20行作为预览
        const previewRows = sheet.data.slice(0, 20);
        table.innerHTML = `
            <thead>
                <tr>
                    ${sheet.columns.map(col => `<th>${col}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                ${previewRows.map(row => `
                    <tr>
                        ${sheet.columns.map(col => `<td>${row[col] || ''}</td>`).join('')}
                    </tr>
                `).join('')}
            </tbody>
        `;

        if (sheet.data.length > 20) {
            table.innerHTML += `
                <tfoot>
                    <tr>
                        <td colspan="${sheet.columns.length}" class="text-center text-sm opacity-70">
                            ... 还有 ${sheet.data.length - 20} 行未显示
                        </td>
                    </tr>
                </tfoot>
            `;
        }
    }
}
```

#### Day 8-9：任务配置升级
**任务ID**: D-W2-02
**预计工时**: 16小时
**依赖**: 无

**任务内容**：
1. 动态规则选择器
2. 参数配置面板
3. 配置模板管理
4. 配置验证逻辑
5. 配置预设功能

**核心代码实现**：

```javascript
// js/pages/task-config-page.js
class TaskConfigPage {
    constructor() {
        this.availableRules = [];
        this.availableProcessors = [];
        this.currentConfig = {
            rules: [],
            processor: null,
            parameters: {}
        };
        this.configTemplates = [];
    }

    async init() {
        await this.loadAvailableOptions();
        await this.loadTemplates();
        this.setupRuleSelector();
        this.setupProcessorSelector();
        this.setupParameterPanel();
        this.setupTemplateManager();
    }

    async loadAvailableOptions() {
        // 从后端获取可用规则和处理器
        const [rules, processors] = await Promise.all([
            API.getAvailableRules(),
            API.getAvailableProcessors()
        ]);

        this.availableRules = rules;
        this.availableProcessors = processors;
    }

    setupRuleSelector() {
        const container = document.getElementById('rule-selector');

        container.innerHTML = `
            <div class="form-control">
                <label class="label">
                    <span class="label-text">选择拆分规则</span>
                    <span class="label-text-alt">可多选，按优先级执行</span>
                </label>
                <div class="space-y-2">
                    ${this.availableRules.map(rule => `
                        <div class="rule-item p-3 border rounded-lg">
                            <div class="flex items-start">
                                <input type="checkbox"
                                       class="checkbox checkbox-primary"
                                       value="${rule.id}"
                                       ${rule.enabled ? 'checked' : ''}>
                                <div class="ml-3 flex-1">
                                    <div class="font-medium">${rule.name}</div>
                                    <div class="text-sm opacity-70">${rule.description}</div>
                                    <div class="mt-2 flex items-center gap-4">
                                        <span class="badge badge-outline">
                                            优先级: ${rule.priority}
                                        </span>
                                        ${rule.requires_translation_first ?
                                            '<span class="badge badge-warning">需要先翻译</span>' :
                                            ''}
                                    </div>
                                </div>
                                <button class="btn btn-sm btn-ghost"
                                        onclick="configPage.configureRule('${rule.id}')">
                                    <i class="fas fa-cog"></i>
                                </button>
                            </div>
                            <div class="rule-config mt-3 hidden" id="config-${rule.id}">
                                <!-- 动态配置参数 -->
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // 监听规则选择变化
        container.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateSelectedRules();
            });
        });
    }

    configureRule(ruleId) {
        const rule = this.availableRules.find(r => r.id === ruleId);
        const configDiv = document.getElementById(`config-${ruleId}`);

        if (configDiv.classList.contains('hidden')) {
            // 显示配置面板
            configDiv.classList.remove('hidden');
            configDiv.innerHTML = this.generateRuleConfigForm(rule);
        } else {
            // 隐藏配置面板
            configDiv.classList.add('hidden');
        }
    }

    generateRuleConfigForm(rule) {
        if (!rule.parameters) return '';

        return `
            <div class="space-y-3 p-3 bg-base-200 rounded">
                ${Object.entries(rule.parameters).map(([key, param]) => `
                    <div class="form-control">
                        <label class="label">
                            <span class="label-text text-sm">${param.label}</span>
                            ${param.required ?
                                '<span class="label-text-alt text-error">*必填</span>' :
                                ''}
                        </label>
                        ${this.generateParameterInput(key, param)}
                        ${param.description ?
                            `<label class="label">
                                <span class="label-text-alt">${param.description}</span>
                            </label>` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    generateParameterInput(key, param) {
        switch (param.type) {
            case 'number':
                return `
                    <input type="number"
                           name="${key}"
                           class="input input-sm input-bordered"
                           value="${param.default || ''}"
                           ${param.min !== undefined ? `min="${param.min}"` : ''}
                           ${param.max !== undefined ? `max="${param.max}"` : ''}
                           ${param.required ? 'required' : ''}>
                `;

            case 'select':
                return `
                    <select name="${key}"
                            class="select select-sm select-bordered"
                            ${param.required ? 'required' : ''}>
                        ${param.options.map(opt => `
                            <option value="${opt.value}"
                                    ${opt.value === param.default ? 'selected' : ''}>
                                ${opt.label}
                            </option>
                        `).join('')}
                    </select>
                `;

            case 'boolean':
                return `
                    <input type="checkbox"
                           name="${key}"
                           class="toggle toggle-primary"
                           ${param.default ? 'checked' : ''}>
                `;

            case 'text':
            default:
                return `
                    <input type="text"
                           name="${key}"
                           class="input input-sm input-bordered"
                           value="${param.default || ''}"
                           ${param.required ? 'required' : ''}>
                `;
        }
    }

    setupProcessorSelector() {
        const container = document.getElementById('processor-selector');

        container.innerHTML = `
            <div class="form-control">
                <label class="label">
                    <span class="label-text">选择处理器</span>
                </label>
                <div class="grid grid-cols-2 gap-3">
                    ${this.availableProcessors.map(proc => `
                        <div class="card bg-base-200 cursor-pointer processor-card"
                             data-processor="${proc.id}">
                            <div class="card-body p-4">
                                <h4 class="card-title text-base">${proc.name}</h4>
                                <p class="text-sm opacity-70">${proc.description}</p>
                                <div class="mt-2">
                                    <span class="badge badge-sm ${proc.type === 'llm' ?
                                        'badge-primary' : 'badge-secondary'}">
                                        ${proc.type}
                                    </span>
                                    ${proc.cost ?
                                        `<span class="badge badge-sm badge-outline">
                                            ¥${proc.cost}/1K tokens
                                        </span>` : ''}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // 处理器选择
        container.querySelectorAll('.processor-card').forEach(card => {
            card.addEventListener('click', () => {
                // 移除其他选中状态
                container.querySelectorAll('.processor-card').forEach(c => {
                    c.classList.remove('ring-2', 'ring-primary');
                });

                // 添加选中状态
                card.classList.add('ring-2', 'ring-primary');

                // 更新配置
                const processorId = card.dataset.processor;
                this.selectProcessor(processorId);
            });
        });
    }

    selectProcessor(processorId) {
        const processor = this.availableProcessors.find(p => p.id === processorId);
        this.currentConfig.processor = processor;

        // 显示处理器特定参数
        if (processor.parameters) {
            this.showProcessorParameters(processor);
        }
    }

    setupTemplateManager() {
        const container = document.getElementById('template-manager');

        container.innerHTML = `
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold">配置模板</h3>
                <button class="btn btn-sm btn-primary" onclick="configPage.saveAsTemplate()">
                    <i class="fas fa-save mr-1"></i> 保存当前配置
                </button>
            </div>
            <div class="grid grid-cols-1 gap-3">
                ${this.configTemplates.map(template => `
                    <div class="card bg-base-200">
                        <div class="card-body p-3">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h4 class="font-medium">${template.name}</h4>
                                    <p class="text-sm opacity-70">${template.description}</p>
                                    <div class="mt-2 flex gap-2">
                                        <span class="badge badge-sm">
                                            ${template.rules.length} 个规则
                                        </span>
                                        <span class="badge badge-sm">
                                            ${template.processor}
                                        </span>
                                    </div>
                                </div>
                                <div class="flex gap-2">
                                    <button class="btn btn-sm btn-ghost"
                                            onclick="configPage.loadTemplate('${template.id}')">
                                        应用
                                    </button>
                                    <button class="btn btn-sm btn-ghost text-error"
                                            onclick="configPage.deleteTemplate('${template.id}')">
                                        删除
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async saveAsTemplate() {
        // 显示保存对话框
        const modal = document.createElement('div');
        modal.className = 'modal modal-open';
        modal.innerHTML = `
            <div class="modal-box">
                <h3 class="font-bold text-lg mb-4">保存配置模板</h3>
                <form onsubmit="return configPage.handleTemplateSave(event)">
                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">模板名称</span>
                        </label>
                        <input type="text" name="name"
                               class="input input-bordered"
                               required>
                    </div>
                    <div class="form-control mt-3">
                        <label class="label">
                            <span class="label-text">描述</span>
                        </label>
                        <textarea name="description"
                                  class="textarea textarea-bordered"
                                  rows="3"></textarea>
                    </div>
                    <div class="modal-action">
                        <button type="submit" class="btn btn-primary">保存</button>
                        <button type="button" class="btn"
                                onclick="this.closest('.modal').remove()">取消</button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);
    }

    handleTemplateSave(event) {
        event.preventDefault();
        const formData = new FormData(event.target);

        const template = {
            id: Date.now().toString(),
            name: formData.get('name'),
            description: formData.get('description'),
            rules: this.currentConfig.rules,
            processor: this.currentConfig.processor?.id,
            parameters: this.currentConfig.parameters,
            createdAt: new Date().toISOString()
        };

        // 保存到LocalStorage
        this.configTemplates.push(template);
        localStorage.setItem('configTemplates', JSON.stringify(this.configTemplates));

        // 刷新模板列表
        this.setupTemplateManager();

        // 关闭对话框
        event.target.closest('.modal').remove();

        // 显示成功消息
        showToast('模板保存成功', 'success');

        return false;
    }

    async validateConfig() {
        const errors = [];

        // 验证规则选择
        if (this.currentConfig.rules.length === 0) {
            errors.push('请至少选择一个拆分规则');
        }

        // 验证处理器选择
        if (!this.currentConfig.processor) {
            errors.push('请选择处理器');
        }

        // 验证参数完整性
        if (this.currentConfig.processor?.parameters) {
            for (const [key, param] of Object.entries(this.currentConfig.processor.parameters)) {
                if (param.required && !this.currentConfig.parameters[key]) {
                    errors.push(`缺少必填参数: ${param.label}`);
                }
            }
        }

        // 验证规则依赖关系
        const hasTranslationRule = this.currentConfig.rules.some(r =>
            !this.availableRules.find(ar => ar.id === r)?.requires_translation_first
        );
        const hasCapsRule = this.currentConfig.rules.some(r =>
            this.availableRules.find(ar => ar.id === r)?.requires_translation_first
        );

        if (hasCapsRule && !hasTranslationRule) {
            errors.push('CAPS规则需要先执行翻译规则');
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }
}
```

#### Day 10：翻译执行优化
**任务ID**: D-W2-03
**预计工时**: 8小时
**依赖**: 无

**任务内容**：
1. 批量任务管理
2. 暂停/恢复功能
3. 失败重试机制
4. 实时进度优化
5. 任务优先级调整

**核心代码实现**：

```javascript
// js/pages/execution-page.js
class ExecutionPage {
    constructor() {
        this.activeSessions = new Map();
        this.pausedSessions = new Set();
        this.retryQueue = [];
        this.progressTrackers = new Map();
    }

    init() {
        this.setupBatchManager();
        this.setupControlPanel();
        this.setupProgressView();
        this.setupRetryMechanism();
        this.startMonitoring();
    }

    setupBatchManager() {
        const container = document.getElementById('batch-manager');

        container.innerHTML = `
            <div class="card bg-base-200">
                <div class="card-body">
                    <h3 class="card-title">批量任务管理</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="label">
                                <span class="label-text">待执行任务</span>
                            </label>
                            <select multiple class="select select-bordered w-full"
                                    size="5" id="pending-sessions">
                                <!-- 动态填充 -->
                            </select>
                        </div>
                        <div>
                            <label class="label">
                                <span class="label-text">执行队列</span>
                            </label>
                            <div class="space-y-2" id="execution-queue">
                                <!-- 动态填充 -->
                            </div>
                        </div>
                    </div>
                    <div class="flex gap-2 mt-4">
                        <button class="btn btn-primary" onclick="executionPage.startBatch()">
                            <i class="fas fa-play"></i> 开始批量执行
                        </button>
                        <button class="btn btn-outline" onclick="executionPage.configBatch()">
                            <i class="fas fa-cog"></i> 批量配置
                        </button>
                    </div>
                </div>
            </div>
        `;

        this.loadPendingSessions();
    }

    async loadPendingSessions() {
        const sessions = await SessionManager.getSessionsByStage('split_completed');
        const select = document.getElementById('pending-sessions');

        select.innerHTML = sessions.map(session => `
            <option value="${session.id}">
                ${session.filename} (${session.taskCount} 任务)
            </option>
        `).join('');
    }

    async startBatch() {
        const select = document.getElementById('pending-sessions');
        const selectedSessions = Array.from(select.selectedOptions).map(opt => opt.value);

        if (selectedSessions.length === 0) {
            showToast('请选择要执行的任务', 'warning');
            return;
        }

        // 批量配置
        const config = await this.getBatchConfig();

        // 添加到执行队列
        for (const sessionId of selectedSessions) {
            await this.addToQueue(sessionId, config);
        }

        // 开始执行
        this.processingQueue();
    }

    async addToQueue(sessionId, config) {
        const session = await SessionManager.getSession(sessionId);

        const tracker = new ProgressTracker(sessionId);
        this.progressTrackers.set(sessionId, tracker);

        const queueItem = {
            sessionId,
            config,
            status: 'queued',
            priority: config.priority || 5,
            createdAt: Date.now(),
            tracker
        };

        this.activeSessions.set(sessionId, queueItem);
        this.renderQueueItem(queueItem);
    }

    async processingQueue() {
        // 按优先级排序
        const queue = Array.from(this.activeSessions.values())
            .filter(item => item.status === 'queued')
            .sort((a, b) => b.priority - a.priority);

        // 并发执行限制
        const maxConcurrent = 3;
        const running = Array.from(this.activeSessions.values())
            .filter(item => item.status === 'running').length;

        const toStart = Math.min(maxConcurrent - running, queue.length);

        for (let i = 0; i < toStart; i++) {
            await this.executeSession(queue[i]);
        }
    }

    async executeSession(queueItem) {
        queueItem.status = 'running';
        this.updateQueueItemUI(queueItem);

        try {
            // 启动执行
            const response = await API.startExecution(queueItem.sessionId, {
                processor: queueItem.config.processor,
                max_workers: queueItem.config.maxWorkers,
                retry_failed: queueItem.config.retryFailed
            });

            // 监控进度
            await this.monitorProgress(queueItem);

            queueItem.status = 'completed';
            this.updateQueueItemUI(queueItem);

        } catch (error) {
            queueItem.status = 'failed';
            queueItem.error = error.message;
            this.updateQueueItemUI(queueItem);

            // 添加到重试队列
            if (queueItem.config.autoRetry) {
                this.addToRetryQueue(queueItem);
            }
        } finally {
            // 继续处理队列
            this.processingQueue();
        }
    }

    setupControlPanel() {
        const container = document.getElementById('control-panel');

        container.innerHTML = `
            <div class="flex gap-2">
                <button class="btn btn-sm" id="pause-all-btn">
                    <i class="fas fa-pause"></i> 全部暂停
                </button>
                <button class="btn btn-sm" id="resume-all-btn" disabled>
                    <i class="fas fa-play"></i> 全部恢复
                </button>
                <button class="btn btn-sm btn-error" id="stop-all-btn">
                    <i class="fas fa-stop"></i> 全部停止
                </button>
                <div class="divider divider-horizontal"></div>
                <button class="btn btn-sm btn-outline" id="retry-failed-btn">
                    <i class="fas fa-redo"></i> 重试失败
                </button>
            </div>
        `;

        // 绑定事件
        document.getElementById('pause-all-btn').addEventListener('click', () => {
            this.pauseAll();
        });

        document.getElementById('resume-all-btn').addEventListener('click', () => {
            this.resumeAll();
        });

        document.getElementById('stop-all-btn').addEventListener('click', () => {
            if (confirm('确定要停止所有任务吗？')) {
                this.stopAll();
            }
        });

        document.getElementById('retry-failed-btn').addEventListener('click', () => {
            this.retryFailed();
        });
    }

    async pauseAll() {
        for (const [sessionId, item] of this.activeSessions) {
            if (item.status === 'running') {
                await this.pauseSession(sessionId);
            }
        }

        document.getElementById('pause-all-btn').disabled = true;
        document.getElementById('resume-all-btn').disabled = false;
    }

    async pauseSession(sessionId) {
        // 发送暂停请求
        await API.pauseExecution(sessionId);

        this.pausedSessions.add(sessionId);
        const item = this.activeSessions.get(sessionId);
        item.status = 'paused';
        this.updateQueueItemUI(item);
    }

    async resumeAll() {
        for (const sessionId of this.pausedSessions) {
            await this.resumeSession(sessionId);
        }

        document.getElementById('pause-all-btn').disabled = false;
        document.getElementById('resume-all-btn').disabled = true;
    }

    async resumeSession(sessionId) {
        // 发送恢复请求
        await API.resumeExecution(sessionId);

        this.pausedSessions.delete(sessionId);
        const item = this.activeSessions.get(sessionId);
        item.status = 'running';
        this.updateQueueItemUI(item);

        // 继续监控
        this.monitorProgress(item);
    }

    setupRetryMechanism() {
        // 自动重试机制
        setInterval(() => {
            this.processRetryQueue();
        }, 30000); // 每30秒检查一次
    }

    addToRetryQueue(queueItem) {
        queueItem.retryCount = (queueItem.retryCount || 0) + 1;
        queueItem.nextRetryTime = Date.now() + (queueItem.retryCount * 60000); // 指数退避

        this.retryQueue.push(queueItem);

        showToast(`任务 ${queueItem.sessionId} 将在 ${queueItem.retryCount} 分钟后重试`, 'info');
    }

    async processRetryQueue() {
        const now = Date.now();
        const toRetry = this.retryQueue.filter(item => item.nextRetryTime <= now);

        for (const item of toRetry) {
            if (item.retryCount < 3) { // 最多重试3次
                // 从重试队列移除
                this.retryQueue = this.retryQueue.filter(i => i !== item);

                // 重新加入执行队列
                item.status = 'queued';
                await this.executeSession(item);
            } else {
                // 超过重试次数，标记为失败
                item.status = 'failed';
                item.error = '超过最大重试次数';
                this.updateQueueItemUI(item);

                this.retryQueue = this.retryQueue.filter(i => i !== item);
            }
        }
    }

    async monitorProgress(queueItem) {
        const { sessionId, tracker } = queueItem;

        // WebSocket连接监控进度
        const ws = new WebSocket(`ws://localhost:8013/api/websocket/progress/${sessionId}`);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            // 更新进度追踪器
            tracker.update(data);

            // 更新UI
            this.updateProgressUI(sessionId, data);

            // 检查是否暂停
            if (this.pausedSessions.has(sessionId)) {
                ws.close();
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            tracker.setError(error);
        };

        ws.onclose = () => {
            console.log('WebSocket closed for session:', sessionId);
        };

        // 保存WebSocket连接
        queueItem.ws = ws;
    }

    updateProgressUI(sessionId, progressData) {
        const progressBar = document.querySelector(`#progress-${sessionId}`);
        if (!progressBar) return;

        const { completed, total, percentage, estimatedTime } = progressData;

        progressBar.querySelector('.progress').value = percentage;
        progressBar.querySelector('.progress-text').textContent =
            `${completed}/${total} (${percentage}%)`;

        if (estimatedTime) {
            progressBar.querySelector('.eta').textContent =
                `预计剩余: ${this.formatTime(estimatedTime)}`;
        }
    }

    formatTime(seconds) {
        if (seconds < 60) return `${seconds}秒`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`;
        return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分钟`;
    }
}

// 进度追踪器
class ProgressTracker {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.startTime = Date.now();
        this.updates = [];
        this.currentProgress = 0;
        this.totalTasks = 0;
        this.completedTasks = 0;
        this.failedTasks = 0;
    }

    update(data) {
        this.updates.push({
            timestamp: Date.now(),
            ...data
        });

        this.currentProgress = data.percentage || 0;
        this.totalTasks = data.total || this.totalTasks;
        this.completedTasks = data.completed || this.completedTasks;
        this.failedTasks = data.failed || this.failedTasks;

        this.calculateStats();
    }

    calculateStats() {
        if (this.updates.length < 2) return;

        // 计算速度
        const elapsed = (Date.now() - this.startTime) / 1000;
        this.speed = this.completedTasks / elapsed;

        // 预估剩余时间
        const remaining = this.totalTasks - this.completedTasks;
        this.estimatedTime = remaining / this.speed;

        // 成功率
        this.successRate = (this.completedTasks / (this.completedTasks + this.failedTasks)) * 100;
    }

    getStats() {
        return {
            progress: this.currentProgress,
            speed: this.speed,
            estimatedTime: this.estimatedTime,
            successRate: this.successRate,
            elapsed: (Date.now() - this.startTime) / 1000
        };
    }
}
```

### 3.2 Week 3（第11-15天）- 系统设置

#### Day 11-12：LLM配置管理
**任务ID**: D-W3-01
**预计工时**: 16小时
**依赖**: 无

**任务内容**：
1. LLM提供商管理
2. 模型选择器
3. 参数配置
4. API密钥管理
5. 配额监控

**核心代码实现**：

```javascript
// js/pages/settings-llm-page.js
class LLMSettingsPage {
    constructor() {
        this.providers = [];
        this.models = {};
        this.currentProvider = null;
        this.apiKeys = {};
        this.quotaInfo = {};
    }

    async init() {
        await this.loadProviders();
        await this.loadAPIKeys();
        this.setupProviderSelector();
        this.setupModelConfig();
        this.setupAPIKeyManager();
        this.setupQuotaMonitor();
    }

    async loadProviders() {
        // 获取支持的LLM提供商
        this.providers = await API.getLLMProviders();

        // 加载每个提供商的模型
        for (const provider of this.providers) {
            this.models[provider.id] = await API.getLLMModels(provider.id);
        }
    }

    setupProviderSelector() {
        const container = document.getElementById('provider-selector');

        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                ${this.providers.map(provider => `
                    <div class="card bg-base-200 cursor-pointer provider-card"
                         data-provider="${provider.id}">
                        <div class="card-body">
                            <div class="flex items-start">
                                <img src="${provider.logo}" alt="${provider.name}"
                                     class="w-12 h-12 mr-3">
                                <div class="flex-1">
                                    <h4 class="font-bold">${provider.name}</h4>
                                    <p class="text-sm opacity-70">${provider.description}</p>
                                </div>
                            </div>
                            <div class="mt-3 space-y-1">
                                <div class="flex justify-between text-sm">
                                    <span>支持模型:</span>
                                    <span>${this.models[provider.id]?.length || 0}个</span>
                                </div>
                                <div class="flex justify-between text-sm">
                                    <span>状态:</span>
                                    <span class="badge badge-sm ${
                                        this.apiKeys[provider.id] ?
                                        'badge-success' : 'badge-warning'
                                    }">
                                        ${this.apiKeys[provider.id] ? '已配置' : '未配置'}
                                    </span>
                                </div>
                            </div>
                            <div class="card-actions justify-end mt-3">
                                <button class="btn btn-sm btn-primary"
                                        onclick="llmSettings.configureProvider('${provider.id}')">
                                    配置
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    configureProvider(providerId) {
        const provider = this.providers.find(p => p.id === providerId);
        this.currentProvider = provider;

        // 显示配置面板
        this.showProviderConfig(provider);
    }

    showProviderConfig(provider) {
        const modal = document.createElement('div');
        modal.className = 'modal modal-open';
        modal.innerHTML = `
            <div class="modal-box max-w-3xl">
                <h3 class="font-bold text-lg mb-4">
                    配置 ${provider.name}
                </h3>

                <div class="space-y-4">
                    <!-- API密钥配置 -->
                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">API密钥</span>
                            <a href="${provider.apiKeyUrl}" target="_blank"
                               class="link link-primary text-sm">
                                获取密钥
                            </a>
                        </label>
                        <input type="password"
                               id="api-key-input"
                               class="input input-bordered"
                               value="${this.apiKeys[provider.id] || ''}"
                               placeholder="请输入API密钥">
                        <label class="label">
                            <span class="label-text-alt">密钥将安全存储在本地</span>
                        </label>
                    </div>

                    <!-- 模型选择 -->
                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">选择模型</span>
                        </label>
                        <div class="space-y-2">
                            ${this.models[provider.id].map(model => `
                                <label class="cursor-pointer">
                                    <div class="card bg-base-100">
                                        <div class="card-body p-3">
                                            <div class="flex items-start">
                                                <input type="radio"
                                                       name="model"
                                                       value="${model.id}"
                                                       class="radio radio-primary"
                                                       ${model.id === provider.defaultModel ?
                                                         'checked' : ''}>
                                                <div class="ml-3 flex-1">
                                                    <div class="font-medium">${model.name}</div>
                                                    <div class="text-sm opacity-70">
                                                        ${model.description}
                                                    </div>
                                                    <div class="mt-2 flex gap-2">
                                                        <span class="badge badge-sm">
                                                            ${model.contextLength} tokens
                                                        </span>
                                                        <span class="badge badge-sm badge-outline">
                                                            ¥${model.pricing.input}/1K input
                                                        </span>
                                                        <span class="badge badge-sm badge-outline">
                                                            ¥${model.pricing.output}/1K output
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </label>
                            `).join('')}
                        </div>
                    </div>

                    <!-- 高级参数 -->
                    <div class="collapse collapse-arrow bg-base-200">
                        <input type="checkbox">
                        <div class="collapse-title font-medium">
                            高级参数设置
                        </div>
                        <div class="collapse-content">
                            <div class="space-y-3 pt-3">
                                <div class="form-control">
                                    <label class="label">
                                        <span class="label-text">Temperature (0-2)</span>
                                        <span class="label-text-alt">创造性</span>
                                    </label>
                                    <input type="range"
                                           name="temperature"
                                           min="0" max="2" step="0.1"
                                           value="${provider.parameters?.temperature || 0.7}"
                                           class="range range-primary">
                                    <div class="flex justify-between text-xs opacity-70">
                                        <span>保守</span>
                                        <span>平衡</span>
                                        <span>创造</span>
                                    </div>
                                </div>

                                <div class="form-control">
                                    <label class="label">
                                        <span class="label-text">Max Tokens</span>
                                        <span class="label-text-alt">最大输出长度</span>
                                    </label>
                                    <input type="number"
                                           name="max_tokens"
                                           class="input input-bordered input-sm"
                                           value="${provider.parameters?.max_tokens || 2000}">
                                </div>

                                <div class="form-control">
                                    <label class="label">
                                        <span class="label-text">请求超时 (秒)</span>
                                    </label>
                                    <input type="number"
                                           name="timeout"
                                           class="input input-bordered input-sm"
                                           value="${provider.parameters?.timeout || 30}">
                                </div>

                                <div class="form-control">
                                    <label class="label">
                                        <span class="label-text">重试次数</span>
                                    </label>
                                    <input type="number"
                                           name="max_retries"
                                           class="input input-bordered input-sm"
                                           value="${provider.parameters?.max_retries || 3}">
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 测试连接 -->
                    <div class="alert alert-info" id="test-result" style="display:none;">
                        <span></span>
                    </div>
                </div>

                <div class="modal-action">
                    <button class="btn btn-outline"
                            onclick="llmSettings.testConnection('${provider.id}')">
                        测试连接
                    </button>
                    <button class="btn btn-primary"
                            onclick="llmSettings.saveProviderConfig('${provider.id}')">
                        保存配置
                    </button>
                    <button class="btn" onclick="this.closest('.modal').remove()">
                        取消
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    async testConnection(providerId) {
        const modal = document.querySelector('.modal-open');
        const apiKey = modal.querySelector('#api-key-input').value;
        const model = modal.querySelector('input[name="model"]:checked')?.value;

        if (!apiKey) {
            showToast('请输入API密钥', 'warning');
            return;
        }

        const resultDiv = modal.querySelector('#test-result');
        resultDiv.style.display = 'block';
        resultDiv.className = 'alert alert-info';
        resultDiv.textContent = '测试中...';

        try {
            const result = await API.testLLMConnection({
                provider: providerId,
                apiKey,
                model
            });

            resultDiv.className = 'alert alert-success';
            resultDiv.innerHTML = `
                <i class="fas fa-check-circle"></i>
                连接成功！响应时间: ${result.responseTime}ms
            `;
        } catch (error) {
            resultDiv.className = 'alert alert-error';
            resultDiv.innerHTML = `
                <i class="fas fa-times-circle"></i>
                连接失败: ${error.message}
            `;
        }
    }

    setupQuotaMonitor() {
        const container = document.getElementById('quota-monitor');

        // 定期更新配额信息
        this.updateQuotaInfo();
        setInterval(() => this.updateQuotaInfo(), 60000); // 每分钟更新

        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                ${this.providers.filter(p => this.apiKeys[p.id]).map(provider => `
                    <div class="card bg-base-200">
                        <div class="card-body">
                            <h4 class="card-title text-base">
                                ${provider.name} 配额使用情况
                            </h4>
                            <div class="space-y-2" id="quota-${provider.id}">
                                <div class="skeleton h-4 w-full"></div>
                                <div class="skeleton h-4 w-full"></div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async updateQuotaInfo() {
        for (const provider of this.providers) {
            if (!this.apiKeys[provider.id]) continue;

            try {
                const quota = await API.getLLMQuota(provider.id);
                this.quotaInfo[provider.id] = quota;
                this.renderQuotaInfo(provider.id, quota);
            } catch (error) {
                console.error(`Failed to get quota for ${provider.id}:`, error);
            }
        }
    }

    renderQuotaInfo(providerId, quota) {
        const container = document.getElementById(`quota-${providerId}`);
        if (!container) return;

        const usagePercent = (quota.used / quota.limit) * 100;
        const remainingDays = Math.floor(
            (new Date(quota.resetDate) - new Date()) / (1000 * 60 * 60 * 24)
        );

        container.innerHTML = `
            <div>
                <div class="flex justify-between mb-1">
                    <span class="text-sm">使用量</span>
                    <span class="text-sm">
                        ¥${quota.used.toFixed(2)} / ¥${quota.limit.toFixed(2)}
                    </span>
                </div>
                <progress class="progress ${
                    usagePercent > 80 ? 'progress-error' :
                    usagePercent > 50 ? 'progress-warning' :
                    'progress-success'
                }" value="${usagePercent}" max="100"></progress>
            </div>
            <div class="text-sm opacity-70">
                <div>本月请求: ${quota.requests.toLocaleString()} 次</div>
                <div>重置时间: ${remainingDays} 天后</div>
            </div>
        `;
    }
}
```

#### Day 13：规则配置管理
**任务ID**: D-W3-02
**预计工时**: 8小时
**依赖**: 无

**任务内容**：
1. 规则列表管理
2. 启用/禁用控制
3. 优先级调整
4. 规则参数配置
5. 规则测试工具

**核心代码实现**：

```javascript
// js/pages/settings-rules-page.js
class RulesSettingsPage {
    constructor() {
        this.rules = [];
        this.ruleSets = [];
        this.testResults = new Map();
    }

    async init() {
        await this.loadRules();
        await this.loadRuleSets();
        this.setupRuleManager();
        this.setupRuleSetEditor();
        this.setupTestTool();
    }

    async loadRules() {
        this.rules = await API.getRules();
    }

    async loadRuleSets() {
        this.ruleSets = await API.getRuleSets();
    }

    setupRuleManager() {
        const container = document.getElementById('rule-manager');

        container.innerHTML = `
            <div class="space-y-4">
                <div class="flex justify-between items-center">
                    <h3 class="text-lg font-bold">规则管理</h3>
                    <div class="flex gap-2">
                        <button class="btn btn-sm btn-primary"
                                onclick="rulesSettings.createRule()">
                            <i class="fas fa-plus"></i> 新建规则
                        </button>
                        <button class="btn btn-sm btn-outline"
                                onclick="rulesSettings.importRules()">
                            <i class="fas fa-upload"></i> 导入
                        </button>
                    </div>
                </div>

                <div class="overflow-x-auto">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>状态</th>
                                <th>规则名称</th>
                                <th>类型</th>
                                <th>优先级</th>
                                <th>描述</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="rules-tbody">
                            ${this.rules.map(rule => this.renderRuleRow(rule)).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        // 使表格可拖拽排序
        this.setupDragSort();
    }

    renderRuleRow(rule) {
        return `
            <tr draggable="true" data-rule-id="${rule.id}">
                <td>
                    <input type="checkbox"
                           class="toggle toggle-success toggle-sm"
                           ${rule.enabled ? 'checked' : ''}
                           onchange="rulesSettings.toggleRule('${rule.id}', this.checked)">
                </td>
                <td>
                    <div class="flex items-center gap-2">
                        <i class="fas fa-grip-vertical opacity-50 cursor-move"></i>
                        <span class="font-medium">${rule.name}</span>
                        ${rule.custom ? '<span class="badge badge-sm">自定义</span>' : ''}
                    </div>
                </td>
                <td>
                    <span class="badge badge-outline">${rule.type}</span>
                </td>
                <td>
                    <input type="number"
                           class="input input-xs input-bordered w-16"
                           value="${rule.priority}"
                           onchange="rulesSettings.updatePriority('${rule.id}', this.value)">
                </td>
                <td class="max-w-xs">
                    <span class="text-sm opacity-80">${rule.description}</span>
                </td>
                <td>
                    <div class="flex gap-1">
                        <button class="btn btn-xs btn-ghost"
                                onclick="rulesSettings.editRule('${rule.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-xs btn-ghost"
                                onclick="rulesSettings.testRule('${rule.id}')">
                            <i class="fas fa-flask"></i>
                        </button>
                        ${rule.custom ? `
                            <button class="btn btn-xs btn-ghost text-error"
                                    onclick="rulesSettings.deleteRule('${rule.id}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }

    setupDragSort() {
        const tbody = document.getElementById('rules-tbody');
        let draggedRow = null;

        tbody.addEventListener('dragstart', (e) => {
            if (e.target.tagName === 'TR') {
                draggedRow = e.target;
                e.target.classList.add('opacity-50');
            }
        });

        tbody.addEventListener('dragend', (e) => {
            if (e.target.tagName === 'TR') {
                e.target.classList.remove('opacity-50');
            }
        });

        tbody.addEventListener('dragover', (e) => {
            e.preventDefault();
            const afterElement = this.getDragAfterElement(tbody, e.clientY);
            if (afterElement == null) {
                tbody.appendChild(draggedRow);
            } else {
                tbody.insertBefore(draggedRow, afterElement);
            }
        });

        tbody.addEventListener('drop', (e) => {
            e.preventDefault();
            this.saveRuleOrder();
        });
    }

    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('tr:not(.opacity-50)')];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;

            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    async saveRuleOrder() {
        const tbody = document.getElementById('rules-tbody');
        const rows = tbody.querySelectorAll('tr');

        const order = Array.from(rows).map((row, index) => ({
            id: row.dataset.ruleId,
            priority: rows.length - index
        }));

        await API.updateRuleOrder(order);
        showToast('规则顺序已更新', 'success');
    }

    editRule(ruleId) {
        const rule = this.rules.find(r => r.id === ruleId);

        const modal = document.createElement('div');
        modal.className = 'modal modal-open';
        modal.innerHTML = `
            <div class="modal-box max-w-3xl">
                <h3 class="font-bold text-lg mb-4">编辑规则 - ${rule.name}</h3>

                <form onsubmit="return rulesSettings.saveRule(event, '${ruleId}')">
                    <div class="grid grid-cols-2 gap-4">
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">规则名称</span>
                            </label>
                            <input type="text" name="name"
                                   class="input input-bordered"
                                   value="${rule.name}"
                                   ${!rule.custom ? 'disabled' : 'required'}>
                        </div>

                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">类型</span>
                            </label>
                            <select name="type" class="select select-bordered"
                                    ${!rule.custom ? 'disabled' : ''}>
                                <option value="cell_color" ${rule.type === 'cell_color' ? 'selected' : ''}>
                                    单元格颜色
                                </option>
                                <option value="cell_content" ${rule.type === 'cell_content' ? 'selected' : ''}>
                                    单元格内容
                                </option>
                                <option value="sheet_name" ${rule.type === 'sheet_name' ? 'selected' : ''}>
                                    Sheet名称
                                </option>
                                <option value="custom" ${rule.type === 'custom' ? 'selected' : ''}>
                                    自定义
                                </option>
                            </select>
                        </div>
                    </div>

                    <div class="form-control mt-3">
                        <label class="label">
                            <span class="label-text">描述</span>
                        </label>
                        <textarea name="description"
                                  class="textarea textarea-bordered"
                                  rows="2">${rule.description}</textarea>
                    </div>

                    <div class="form-control mt-3">
                        <label class="label">
                            <span class="label-text">匹配条件 (JSON)</span>
                        </label>
                        <textarea name="condition"
                                  class="textarea textarea-bordered font-mono text-sm"
                                  rows="6">${JSON.stringify(rule.condition, null, 2)}</textarea>
                    </div>

                    <div class="form-control mt-3">
                        <label class="label">
                            <span class="label-text">参数配置</span>
                        </label>
                        <div class="space-y-2">
                            ${Object.entries(rule.parameters || {}).map(([key, param]) => `
                                <div class="flex gap-2 items-center">
                                    <input type="text"
                                           class="input input-sm input-bordered"
                                           value="${key}" disabled>
                                    <input type="text"
                                           name="param_${key}"
                                           class="input input-sm input-bordered flex-1"
                                           value="${param.value}"
                                           placeholder="${param.description}">
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <div class="modal-action">
                        <button type="submit" class="btn btn-primary">保存</button>
                        <button type="button" class="btn"
                                onclick="this.closest('.modal').remove()">取消</button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);
    }

    setupTestTool() {
        const container = document.getElementById('rule-test-tool');

        container.innerHTML = `
            <div class="card bg-base-200">
                <div class="card-body">
                    <h4 class="card-title">规则测试工具</h4>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="label">
                                <span class="label-text">测试数据</span>
                            </label>
                            <textarea id="test-data"
                                      class="textarea textarea-bordered font-mono text-sm"
                                      rows="10"
                                      placeholder='输入测试数据 (JSON格式)&#10;例如:&#10;{&#10;  "sheet": "Sheet1",&#10;  "row": 0,&#10;  "col": "EN",&#10;  "value": "example",&#10;  "color": "#FFFF00"&#10;}'></textarea>
                        </div>

                        <div>
                            <label class="label">
                                <span class="label-text">测试结果</span>
                            </label>
                            <div id="test-results"
                                 class="bg-base-100 rounded-lg p-4 h-64 overflow-y-auto">
                                <div class="text-sm opacity-70">等待测试...</div>
                            </div>
                        </div>
                    </div>

                    <div class="flex gap-2 mt-4">
                        <select id="test-rule-select" class="select select-bordered flex-1">
                            <option value="">选择要测试的规则</option>
                            ${this.rules.map(rule => `
                                <option value="${rule.id}">${rule.name}</option>
                            `).join('')}
                        </select>
                        <button class="btn btn-primary" onclick="rulesSettings.runTest()">
                            运行测试
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    async runTest() {
        const ruleId = document.getElementById('test-rule-select').value;
        const testData = document.getElementById('test-data').value;
        const resultsDiv = document.getElementById('test-results');

        if (!ruleId) {
            showToast('请选择要测试的规则', 'warning');
            return;
        }

        try {
            const data = JSON.parse(testData);
            const result = await API.testRule(ruleId, data);

            resultsDiv.innerHTML = `
                <div class="space-y-2">
                    <div class="alert ${result.matched ? 'alert-success' : 'alert-warning'}">
                        <i class="fas ${result.matched ? 'fa-check' : 'fa-times'}"></i>
                        <span>${result.matched ? '规则匹配' : '规则不匹配'}</span>
                    </div>

                    ${result.matched ? `
                        <div class="p-3 bg-base-200 rounded">
                            <div class="text-sm font-bold mb-2">提取的任务:</div>
                            <pre class="text-xs">${JSON.stringify(result.task, null, 2)}</pre>
                        </div>
                    ` : ''}

                    <div class="p-3 bg-base-200 rounded">
                        <div class="text-sm font-bold mb-2">匹配详情:</div>
                        <ul class="text-sm space-y-1">
                            ${result.details.map(detail => `
                                <li class="flex items-center gap-2">
                                    <i class="fas fa-${detail.passed ? 'check text-success' :
                                        'times text-error'} text-xs"></i>
                                    ${detail.condition}: ${detail.message}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `;

            // 保存测试结果
            this.testResults.set(ruleId, result);

        } catch (error) {
            resultsDiv.innerHTML = `
                <div class="alert alert-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>测试失败: ${error.message}</span>
                </div>
            `;
        }
    }
}
```

#### Day 14：用户偏好设置
**任务ID**: D-W3-03
**预计工时**: 8小时
**依赖**: Engineer A的主题系统

**任务内容**：
1. 主题切换
2. 语言设置
3. 快捷键配置
4. 界面布局调整
5. 导出设置

**核心代码实现**：

```javascript
// js/pages/settings-preferences-page.js
class PreferencesPage {
    constructor() {
        this.preferences = {
            theme: 'light',
            language: 'zh-CN',
            shortcuts: {},
            layout: {},
            export: {}
        };
        this.themes = [];
        this.languages = [];
    }

    async init() {
        await this.loadPreferences();
        await this.loadAvailableOptions();
        this.setupThemeSelector();
        this.setupLanguageSelector();
        this.setupShortcutConfig();
        this.setupLayoutConfig();
        this.setupExportConfig();
    }

    async loadPreferences() {
        // 从LocalStorage加载用户偏好
        const saved = localStorage.getItem('userPreferences');
        if (saved) {
            this.preferences = JSON.parse(saved);
        }

        // 应用偏好设置
        this.applyPreferences();
    }

    applyPreferences() {
        // 应用主题
        document.documentElement.setAttribute('data-theme', this.preferences.theme);

        // 应用语言
        i18n.setLanguage(this.preferences.language);

        // 应用快捷键
        ShortcutManager.loadShortcuts(this.preferences.shortcuts);

        // 应用布局
        LayoutManager.applyLayout(this.preferences.layout);
    }

    setupThemeSelector() {
        const container = document.getElementById('theme-selector');

        const themes = [
            { id: 'light', name: '浅色', icon: 'fa-sun', colors: ['#ffffff', '#f5f5f5'] },
            { id: 'dark', name: '深色', icon: 'fa-moon', colors: ['#1a1a1a', '#2d2d2d'] },
            { id: 'cupcake', name: '纸杯蛋糕', icon: 'fa-cookie', colors: ['#fae5e5', '#f5d5d5'] },
            { id: 'forest', name: '森林', icon: 'fa-tree', colors: ['#1e3a2f', '#2d5a3d'] },
            { id: 'corporate', name: '企业', icon: 'fa-building', colors: ['#4b6584', '#57606f'] }
        ];

        container.innerHTML = `
            <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                ${themes.map(theme => `
                    <div class="card bg-base-200 cursor-pointer theme-card ${
                        this.preferences.theme === theme.id ? 'ring-2 ring-primary' : ''
                    }" data-theme-id="${theme.id}">
                        <div class="card-body p-3">
                            <div class="flex items-center gap-2 mb-2">
                                <i class="fas ${theme.icon}"></i>
                                <span class="font-medium">${theme.name}</span>
                            </div>
                            <div class="flex gap-1">
                                ${theme.colors.map(color => `
                                    <div class="w-8 h-8 rounded"
                                         style="background-color: ${color}"></div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // 主题切换事件
        container.querySelectorAll('.theme-card').forEach(card => {
            card.addEventListener('click', () => {
                const themeId = card.dataset.themeId;
                this.setTheme(themeId);
            });
        });
    }

    setTheme(themeId) {
        // 更新UI
        document.querySelectorAll('.theme-card').forEach(card => {
            card.classList.remove('ring-2', 'ring-primary');
        });
        document.querySelector(`[data-theme-id="${themeId}"]`)
            .classList.add('ring-2', 'ring-primary');

        // 应用主题
        document.documentElement.setAttribute('data-theme', themeId);

        // 保存偏好
        this.preferences.theme = themeId;
        this.savePreferences();
    }

    setupShortcutConfig() {
        const container = document.getElementById('shortcut-config');

        const shortcuts = [
            { id: 'new_file', name: '新建文件', default: 'Ctrl+N', action: 'newFile' },
            { id: 'save', name: '保存', default: 'Ctrl+S', action: 'save' },
            { id: 'execute', name: '执行翻译', default: 'F5', action: 'execute' },
            { id: 'export', name: '导出结果', default: 'Ctrl+E', action: 'export' },
            { id: 'search', name: '搜索', default: 'Ctrl+F', action: 'search' },
            { id: 'settings', name: '设置', default: 'Ctrl+,', action: 'openSettings' }
        ];

        container.innerHTML = `
            <div class="space-y-3">
                ${shortcuts.map(shortcut => `
                    <div class="flex items-center justify-between">
                        <div>
                            <span class="font-medium">${shortcut.name}</span>
                            <span class="text-sm opacity-70 ml-2">${shortcut.action}()</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <kbd class="kbd kbd-sm current-key" data-shortcut="${shortcut.id}">
                                ${this.preferences.shortcuts[shortcut.id] || shortcut.default}
                            </kbd>
                            <button class="btn btn-xs btn-ghost"
                                    onclick="preferences.recordShortcut('${shortcut.id}')">
                                修改
                            </button>
                            <button class="btn btn-xs btn-ghost"
                                    onclick="preferences.resetShortcut('${shortcut.id}', '${shortcut.default}')">
                                重置
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>

            <div class="alert alert-info mt-4" id="shortcut-recorder" style="display:none;">
                <i class="fas fa-keyboard"></i>
                <span>请按下新的快捷键组合...</span>
                <button class="btn btn-sm" onclick="preferences.cancelRecording()">取消</button>
            </div>
        `;
    }

    recordShortcut(shortcutId) {
        const recorder = document.getElementById('shortcut-recorder');
        recorder.style.display = 'flex';
        recorder.dataset.shortcutId = shortcutId;

        // 监听按键
        const handler = (e) => {
            e.preventDefault();

            const keys = [];
            if (e.ctrlKey) keys.push('Ctrl');
            if (e.altKey) keys.push('Alt');
            if (e.shiftKey) keys.push('Shift');
            if (e.metaKey) keys.push('Cmd');

            if (e.key && !['Control', 'Alt', 'Shift', 'Meta'].includes(e.key)) {
                keys.push(e.key.toUpperCase());
            }

            if (keys.length > 0) {
                const shortcut = keys.join('+');
                this.setShortcut(shortcutId, shortcut);

                // 清理
                document.removeEventListener('keydown', handler);
                recorder.style.display = 'none';
            }
        };

        document.addEventListener('keydown', handler);
    }

    setShortcut(shortcutId, keys) {
        // 检查冲突
        const conflict = Object.entries(this.preferences.shortcuts)
            .find(([id, shortcut]) => id !== shortcutId && shortcut === keys);

        if (conflict) {
            if (!confirm(`快捷键 ${keys} 已被 "${conflict[0]}" 使用，是否替换？`)) {
                return;
            }
            delete this.preferences.shortcuts[conflict[0]];
        }

        // 更新快捷键
        this.preferences.shortcuts[shortcutId] = keys;
        document.querySelector(`[data-shortcut="${shortcutId}"]`).textContent = keys;

        // 应用并保存
        ShortcutManager.setShortcut(shortcutId, keys);
        this.savePreferences();
    }

    setupLayoutConfig() {
        const container = document.getElementById('layout-config');

        container.innerHTML = `
            <div class="space-y-4">
                <!-- 侧边栏位置 -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">侧边栏位置</span>
                    </label>
                    <div class="btn-group">
                        <button class="btn btn-sm ${this.preferences.layout.sidebar === 'left' ?
                            'btn-active' : ''}"
                                onclick="preferences.setLayout('sidebar', 'left')">
                            <i class="fas fa-align-left"></i> 左侧
                        </button>
                        <button class="btn btn-sm ${this.preferences.layout.sidebar === 'right' ?
                            'btn-active' : ''}"
                                onclick="preferences.setLayout('sidebar', 'right')">
                            <i class="fas fa-align-right"></i> 右侧
                        </button>
                        <button class="btn btn-sm ${this.preferences.layout.sidebar === 'hidden' ?
                            'btn-active' : ''}"
                                onclick="preferences.setLayout('sidebar', 'hidden')">
                            <i class="fas fa-eye-slash"></i> 隐藏
                        </button>
                    </div>
                </div>

                <!-- 紧凑模式 -->
                <div class="form-control">
                    <label class="label cursor-pointer">
                        <span class="label-text">紧凑模式</span>
                        <input type="checkbox"
                               class="toggle toggle-primary"
                               ${this.preferences.layout.compact ? 'checked' : ''}
                               onchange="preferences.setLayout('compact', this.checked)">
                    </label>
                </div>

                <!-- 显示行号 -->
                <div class="form-control">
                    <label class="label cursor-pointer">
                        <span class="label-text">显示表格行号</span>
                        <input type="checkbox"
                               class="toggle toggle-primary"
                               ${this.preferences.layout.showLineNumbers ? 'checked' : ''}
                               onchange="preferences.setLayout('showLineNumbers', this.checked)">
                    </label>
                </div>

                <!-- 固定表头 -->
                <div class="form-control">
                    <label class="label cursor-pointer">
                        <span class="label-text">固定表格头部</span>
                        <input type="checkbox"
                               class="toggle toggle-primary"
                               ${this.preferences.layout.stickyHeader ? 'checked' : ''}
                               onchange="preferences.setLayout('stickyHeader', this.checked)">
                    </label>
                </div>
            </div>
        `;
    }

    setupExportConfig() {
        const container = document.getElementById('export-config');

        container.innerHTML = `
            <div class="space-y-4">
                <!-- 默认格式 -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">默认导出格式</span>
                    </label>
                    <select class="select select-bordered"
                            onchange="preferences.setExportOption('format', this.value)">
                        <option value="xlsx" ${this.preferences.export.format === 'xlsx' ?
                            'selected' : ''}>Excel (.xlsx)</option>
                        <option value="csv" ${this.preferences.export.format === 'csv' ?
                            'selected' : ''}>CSV (.csv)</option>
                        <option value="json" ${this.preferences.export.format === 'json' ?
                            'selected' : ''}>JSON (.json)</option>
                    </select>
                </div>

                <!-- 包含颜色 -->
                <div class="form-control">
                    <label class="label cursor-pointer">
                        <span class="label-text">导出时包含单元格颜色</span>
                        <input type="checkbox"
                               class="toggle toggle-primary"
                               ${this.preferences.export.includeColors ? 'checked' : ''}
                               onchange="preferences.setExportOption('includeColors', this.checked)">
                    </label>
                </div>

                <!-- 包含注释 -->
                <div class="form-control">
                    <label class="label cursor-pointer">
                        <span class="label-text">导出时包含注释</span>
                        <input type="checkbox"
                               class="toggle toggle-primary"
                               ${this.preferences.export.includeComments ? 'checked' : ''}
                               onchange="preferences.setExportOption('includeComments', this.checked)">
                    </label>
                </div>

                <!-- 自动下载 -->
                <div class="form-control">
                    <label class="label cursor-pointer">
                        <span class="label-text">完成后自动下载</span>
                        <input type="checkbox"
                               class="toggle toggle-primary"
                               ${this.preferences.export.autoDownload ? 'checked' : ''}
                               onchange="preferences.setExportOption('autoDownload', this.checked)">
                    </label>
                </div>

                <!-- 文件命名 -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">文件命名规则</span>
                    </label>
                    <input type="text"
                           class="input input-bordered"
                           value="${this.preferences.export.namePattern || '{name}_translated_{date}'}"
                           onchange="preferences.setExportOption('namePattern', this.value)"
                           placeholder="{name}_translated_{date}">
                    <label class="label">
                        <span class="label-text-alt">
                            可用变量: {name}, {date}, {time}, {lang}
                        </span>
                    </label>
                </div>
            </div>
        `;
    }

    setLayout(key, value) {
        this.preferences.layout[key] = value;
        LayoutManager.setOption(key, value);
        this.savePreferences();
    }

    setExportOption(key, value) {
        this.preferences.export[key] = value;
        this.savePreferences();
    }

    savePreferences() {
        localStorage.setItem('userPreferences', JSON.stringify(this.preferences));
        showToast('偏好设置已保存', 'success');
    }

    async exportSettings() {
        const data = {
            preferences: this.preferences,
            templates: JSON.parse(localStorage.getItem('configTemplates') || '[]'),
            sessions: SessionManager.exportSessions(),
            exportDate: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(data, null, 2)],
            { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `translation-hub-settings-${Date.now()}.json`;
        a.click();

        URL.revokeObjectURL(url);
    }

    async importSettings() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';

        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            try {
                const text = await file.text();
                const data = JSON.parse(text);

                if (confirm('导入设置将覆盖当前设置，是否继续？')) {
                    this.preferences = data.preferences;
                    localStorage.setItem('configTemplates',
                        JSON.stringify(data.templates || []));

                    if (data.sessions) {
                        SessionManager.importSessions(data.sessions);
                    }

                    this.savePreferences();
                    this.applyPreferences();
                    location.reload();
                }
            } catch (error) {
                showToast('导入失败: ' + error.message, 'error');
            }
        };

        input.click();
    }
}
```

### 3.3 Week 4（第16-18天）- 集成测试与优化

#### Day 15-16：端到端测试
**任务ID**: D-W4-01
**预计工时**: 16小时
**依赖**: 所有功能完成

**任务内容**：
1. 编写E2E测试用例
2. 自动化测试脚本
3. 测试报告生成
4. 回归测试套件

**核心代码实现**：

```javascript
// tests/e2e/test-suite.js
class E2ETestSuite {
    constructor() {
        this.testResults = [];
        this.currentTest = null;
    }

    async runAllTests() {
        console.log('Starting E2E Test Suite...');

        const tests = [
            this.testFileUpload,
            this.testTaskConfiguration,
            this.testTranslationExecution,
            this.testResultDownload,
            this.testGlossaryManagement,
            this.testAnalyticsDashboard,
            this.testSystemSettings,
            this.testErrorHandling,
            this.testPerformance
        ];

        for (const test of tests) {
            await this.runTest(test);
        }

        this.generateReport();
    }

    async runTest(testFunc) {
        const testName = testFunc.name;
        const startTime = Date.now();

        this.currentTest = {
            name: testName,
            status: 'running',
            steps: []
        };

        try {
            await testFunc.call(this);
            this.currentTest.status = 'passed';
        } catch (error) {
            this.currentTest.status = 'failed';
            this.currentTest.error = error.message;
            this.currentTest.stack = error.stack;
        }

        this.currentTest.duration = Date.now() - startTime;
        this.testResults.push(this.currentTest);
    }

    async testFileUpload() {
        // 文件上传完整流程测试
        await this.step('Navigate to upload page', async () => {
            await this.navigateTo('#/upload');
            await this.waitForElement('#upload-zone');
        });

        await this.step('Upload single file', async () => {
            const file = await this.createTestFile('test1.xlsx');
            await this.uploadFile(file);
            await this.waitForElement('.upload-success');
        });

        await this.step('Upload multiple files', async () => {
            const files = [
                await this.createTestFile('test2.xlsx'),
                await this.createTestFile('test3.xlsx')
            ];
            await this.uploadFiles(files);
            await this.waitForElement('.batch-upload-complete');
        });

        await this.step('Test drag and drop', async () => {
            const file = await this.createTestFile('test4.xlsx');
            await this.dragAndDrop(file, '#upload-zone');
            await this.waitForElement('.upload-success');
        });

        await this.step('Test file validation', async () => {
            const invalidFile = await this.createTestFile('invalid.txt');
            await this.uploadFile(invalidFile);
            await this.waitForElement('.validation-error');
        });
    }

    async testTranslationExecution() {
        // 翻译执行完整流程测试
        await this.step('Start translation', async () => {
            await this.click('#start-execution-btn');
            await this.waitForElement('.execution-started');
        });

        await this.step('Monitor progress', async () => {
            await this.waitForElement('.progress-bar');
            const progress = await this.getProgress();
            assert(progress >= 0 && progress <= 100);
        });

        await this.step('Test pause/resume', async () => {
            await this.click('#pause-btn');
            await this.waitForElement('.execution-paused');
            await this.wait(1000);
            await this.click('#resume-btn');
            await this.waitForElement('.execution-running');
        });

        await this.step('Wait for completion', async () => {
            await this.waitForElement('.execution-completed', 60000);
            const results = await this.getExecutionResults();
            assert(results.successRate > 0.95);
        });
    }

    // Helper methods
    async step(description, func) {
        const step = {
            description,
            status: 'running',
            startTime: Date.now()
        };

        try {
            await func();
            step.status = 'passed';
        } catch (error) {
            step.status = 'failed';
            step.error = error.message;
            throw error;
        } finally {
            step.duration = Date.now() - step.startTime;
            this.currentTest.steps.push(step);
        }
    }

    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                total: this.testResults.length,
                passed: this.testResults.filter(t => t.status === 'passed').length,
                failed: this.testResults.filter(t => t.status === 'failed').length,
                duration: this.testResults.reduce((sum, t) => sum + t.duration, 0)
            },
            tests: this.testResults
        };

        // 生成HTML报告
        const html = this.generateHTMLReport(report);
        this.saveReport(html, 'e2e-test-report.html');

        // 生成JSON报告
        this.saveReport(JSON.stringify(report, null, 2), 'e2e-test-report.json');

        console.log('Test Report Generated');
        console.log(`Passed: ${report.summary.passed}/${report.summary.total}`);
    }

    generateHTMLReport(report) {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>E2E Test Report</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    .summary { background: #f0f0f0; padding: 15px; border-radius: 5px; }
                    .test { margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }
                    .test-header { padding: 10px; background: #f8f8f8; }
                    .passed { border-left: 4px solid #4CAF50; }
                    .failed { border-left: 4px solid #f44336; }
                    .step { padding: 5px 20px; border-bottom: 1px solid #eee; }
                    .step.failed { background: #ffebee; }
                </style>
            </head>
            <body>
                <h1>E2E Test Report</h1>
                <div class="summary">
                    <h2>Summary</h2>
                    <p>Total: ${report.summary.total}</p>
                    <p>Passed: ${report.summary.passed}</p>
                    <p>Failed: ${report.summary.failed}</p>
                    <p>Duration: ${(report.summary.duration / 1000).toFixed(2)}s</p>
                </div>

                <h2>Test Results</h2>
                ${report.tests.map(test => `
                    <div class="test ${test.status}">
                        <div class="test-header">
                            <h3>${test.name} - ${test.status.toUpperCase()}</h3>
                            <p>Duration: ${test.duration}ms</p>
                            ${test.error ? `<p style="color:red">${test.error}</p>` : ''}
                        </div>
                        <div class="steps">
                            ${test.steps.map(step => `
                                <div class="step ${step.status}">
                                    ${step.description} - ${step.status} (${step.duration}ms)
                                    ${step.error ? `<br><small>${step.error}</small>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </body>
            </html>
        `;
    }
}

// 运行测试
const testSuite = new E2ETestSuite();
testSuite.runAllTests();
```

#### Day 17-18：性能优化与发布准备
**任务ID**: D-W4-02
**预计工时**: 16小时
**依赖**: 所有测试通过

**任务内容**：
1. 性能分析与优化
2. 代码压缩与打包
3. 文档完善
4. 发布检查清单

## 四、开发规范

### 4.1 代码规范
- 使用ES6+语法
- 遵循JSDoc注释规范
- 保持函数单一职责
- 避免深层嵌套
- 使用async/await处理异步

### 4.2 文件组织
```
frontend_v2/
├── js/
│   ├── pages/          # 页面逻辑
│   ├── components/      # 可复用组件
│   ├── utils/          # 工具函数
│   └── services/       # 服务层
├── css/
│   └── styles.css      # 样式文件
├── tests/
│   ├── unit/          # 单元测试
│   └── e2e/           # 端到端测试
└── docs/              # 文档
```

### 4.3 Git提交规范
- feat: 新功能
- fix: 修复bug
- refactor: 重构
- style: 样式调整
- test: 添加测试
- docs: 文档更新

## 五、参考文档

### 5.1 依赖的文档
1. **需求文档**
   - `docs/requirements/REQUIREMENTS.md`: 第4部分-工作流程优化、第5部分-系统设置

2. **技术规格**
   - `docs/technical/FEATURE_SPEC.md`: 第8节-流程优化规格、第9节-系统配置规格

3. **UI设计**
   - `docs/design/UI_DESIGN.md`: 上传优化界面、配置界面原型

### 5.2 协作接口
需要使用Engineer A提供的：
- Router类
- API封装
- WebSocket管理器
- 主题系统
- 工具函数库

## 六、交付标准

### 6.1 功能完整性
- [ ] 所有工作流程优化功能正常运行
- [ ] 系统设置功能全部实现
- [ ] E2E测试覆盖核心流程
- [ ] 性能指标达标

### 6.2 代码质量
- [ ] 代码符合规范
- [ ] 注释完整清晰
- [ ] 无控制台错误
- [ ] 测试覆盖率>80%

### 6.3 文档完善
- [ ] 功能使用说明
- [ ] 配置指南
- [ ] 测试报告
- [ ] 性能分析报告

## 七、自检清单

### Week 2完成检查
- [ ] 文件上传优化完成
- [ ] 任务配置升级完成
- [ ] 翻译执行优化完成
- [ ] 所有功能可独立测试

### Week 3完成检查
- [ ] LLM配置管理完成
- [ ] 规则配置管理完成
- [ ] 用户偏好设置完成
- [ ] 所有设置可持久化

### Week 4完成检查
- [ ] E2E测试全部通过
- [ ] 性能优化完成
- [ ] 文档全部完善
- [ ] 准备发布

## 八、风险与应对

### 8.1 技术风险
1. **WebSocket连接不稳定**
   - 方案：实现重连机制和降级方案

2. **大文件上传超时**
   - 方案：分片上传、断点续传

3. **配置复杂度高**
   - 方案：提供预设模板、向导式配置

### 8.2 进度风险
1. **依赖延期**
   - 方案：先用mock数据开发，后期集成

2. **测试发现重大问题**
   - 方案：预留缓冲时间，及时沟通

---

**文档版本**: v1.0
**创建日期**: 2024-12-19
**最后更新**: 2024-12-19
**负责人**: 工程师D