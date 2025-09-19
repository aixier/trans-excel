// 翻译测试工具 JavaScript

class TranslationTester {
    constructor() {
        // 自动检测API地址，支持本地文件直接打开
        this.apiBase = this.detectApiBase();
        this.currentTaskId = null;
        this.progressInterval = null;
        this.startTime = null;

        this.init();
    }

    detectApiBase() {
        // 从输入框获取API地址，如果没有则使用默认值
        const apiInput = document.getElementById('apiAddress');
        if (apiInput && apiInput.value) {
            return apiInput.value.trim();
        }

        // 默认地址
        return 'http://localhost:8001';
    }

    init() {
        this.setupEventListeners();
        // 不自动连接，等待用户点击连接按钮
        this.log('系统初始化完成');
        this.log('请输入后端地址并点击连接按钮');
    }

    // 更新API地址
    updateApiBase() {
        const apiInput = document.getElementById('apiAddress');
        if (!apiInput || !apiInput.value) {
            alert('请输入后端 API 地址');
            return;
        }

        this.apiBase = apiInput.value.trim();
        this.log(`🔄 更新API地址为: ${this.apiBase}`);
        this.checkApiStatus();
    }

    setupEventListeners() {
        // 文件选择
        const fileInput = document.getElementById('fileInput');
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // 拖拽上传
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.addEventListener('dragover', this.handleDragOver);
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
    }

    // 检查API状态
    async checkApiStatus() {
        const statusElement = document.getElementById('apiStatus');
        try {
            const response = await fetch(`${this.apiBase}/api/health/status`);
            if (response.ok) {
                statusElement.innerHTML = '<span class="status-dot online"></span><span class="status-text">API服务正常</span>';
                this.log('✅ API服务连接正常');
            } else {
                throw new Error('API响应异常');
            }
        } catch (error) {
            statusElement.innerHTML = '<span class="status-dot offline"></span><span class="status-text">API服务离线</span>';
            this.log('❌ API服务连接失败: ' + error.message);
        }
    }

    // 处理文件拖拽
    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFile(files[0]);
        }
    }

    // 处理文件选择
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.handleFile(file);
        }
    }

    // 处理选择的文件
    handleFile(file) {
        this.log(`🔍 检查文件: ${file.name}`);
        this.log(`📝 文件类型: ${file.type}`);

        // 修复正则表达式，使用单个反斜杠
        if (!file.name.match(/\.(xlsx|xls)$/i)) {
            this.log('❌ 文件格式不正确，需要Excel文件');
            alert('请选择Excel文件 (.xlsx 或 .xls)');
            return;
        }

        this.selectedFile = file;
        this.log(`📄 选择文件: ${file.name} (${this.formatFileSize(file.size)})`);

        // 显示翻译选项
        document.getElementById('translationOptions').style.display = 'block';

        // 更新上传区域显示
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.innerHTML = `
            <div class="file-selected">
                <i class="fas fa-file-excel"></i>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${this.formatFileSize(file.size)}</div>
                </div>
                <button class="change-file-btn" onclick="document.getElementById('fileInput').click()">
                    <i class="fas fa-edit"></i> 更换文件
                </button>
            </div>
        `;
    }

    // 开始翻译
    async startTranslation() {
        if (!this.selectedFile) {
            alert('请先选择Excel文件');
            return;
        }

        this.log('🚀 开始翻译任务...');
        this.log(`📁 文件: ${this.selectedFile.name}`);
        this.log(`📏 文件大小: ${this.formatFileSize(this.selectedFile.size)}`);
        this.startTime = Date.now();

        // 获取翻译配置
        const targetLanguages = Array.from(document.getElementById('targetLanguages').selectedOptions)
            .map(option => option.value);
        const regionCode = document.getElementById('regionCode').value;
        const batchSize = document.getElementById('batchSize').value;
        const maxConcurrent = document.getElementById('maxConcurrent').value;

        this.log(`⚙️ 配置参数:`);
        this.log(`  - 目标语言: ${targetLanguages.join(', ')}`);
        this.log(`  - 地区代码: ${regionCode}`);
        this.log(`  - 批次大小: ${batchSize}`);
        this.log(`  - 最大并发: ${maxConcurrent}`);

        // 准备表单数据
        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('target_languages', targetLanguages.join(','));
        formData.append('region_code', regionCode);
        formData.append('batch_size', batchSize);
        formData.append('max_concurrent', maxConcurrent);

        // 打印FormData内容用于调试
        this.log('📤 FormData内容:');
        for (let [key, value] of formData.entries()) {
            if (key === 'file') {
                this.log(`  - ${key}: ${value.name} (${value.type})`);
            } else {
                this.log(`  - ${key}: ${value}`);
            }
        }

        try {
            const uploadUrl = `${this.apiBase}/api/translation/upload`;
            this.log(`📡 上传URL: ${uploadUrl}`);
            this.log('⏳ 正在上传文件...');

            // 上传文件并开始翻译
            const response = await fetch(uploadUrl, {
                method: 'POST',
                body: formData,
                // 不设置Content-Type，让浏览器自动设置multipart/form-data和boundary
            });

            this.log(`📨 响应状态: ${response.status} ${response.statusText}`);
            this.log(`📋 响应头:`);
            this.log(`  - Content-Type: ${response.headers.get('content-type')}`);
            this.log(`  - Content-Length: ${response.headers.get('content-length')}`);

            if (!response.ok) {
                // 尝试读取错误信息
                let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.text();
                    this.log(`❌ 错误响应内容: ${errorData}`);
                    // 尝试解析JSON错误
                    try {
                        const jsonError = JSON.parse(errorData);
                        errorMsg = jsonError.detail || jsonError.message || errorMsg;
                    } catch (e) {
                        // 不是JSON，使用原始文本
                        if (errorData) {
                            errorMsg = errorData;
                        }
                    }
                } catch (e) {
                    this.log(`⚠️ 无法读取错误响应: ${e.message}`);
                }
                throw new Error(errorMsg);
            }

            // 读取响应内容
            const responseText = await response.text();
            this.log(`📥 原始响应: ${responseText}`);

            // 尝试解析JSON
            let result;
            try {
                result = JSON.parse(responseText);
                this.log(`✅ JSON解析成功`);
            } catch (e) {
                this.log(`❌ JSON解析失败: ${e.message}`);
                throw new Error('服务器响应格式错误');
            }

            this.currentTaskId = result.task_id;

            this.log(`✅ 翻译任务创建成功!`);
            this.log(`📋 任务ID: ${this.currentTaskId}`);

            // 显示进度区域
            document.getElementById('progressSection').style.display = 'block';
            document.getElementById('taskId').textContent = this.currentTaskId;

            // 开始监控进度
            this.startProgressMonitoring();

        } catch (error) {
            this.log('❌ 翻译任务启动失败!');
            this.log(`❌ 错误类型: ${error.name}`);
            this.log(`❌ 错误消息: ${error.message}`);
            if (error.stack) {
                this.log(`❌ 错误堆栈: ${error.stack}`);
            }
            alert('翻译任务启动失败: ' + error.message);
        }
    }

    // 开始进度监控
    startProgressMonitoring() {
        this.progressInterval = setInterval(() => {
            this.checkTranslationProgress();
        }, 2000); // 每2秒检查一次进度
    }

    // 检查翻译进度
    async checkTranslationProgress() {
        if (!this.currentTaskId) return;

        try {
            // 修正为正确的API路径
            const response = await fetch(`${this.apiBase}/api/translation/tasks/${this.currentTaskId}/status`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const status = await response.json();
            this.updateProgressDisplay(status);

            // 检查是否完成
            if (status.status === 'completed') {
                this.onTranslationCompleted(status);
            } else if (status.status === 'failed') {
                this.onTranslationFailed(status);
            }

        } catch (error) {
            this.log('❌ 进度检查失败: ' + error.message);
        }
    }

    // 更新进度显示
    updateProgressDisplay(status) {
        // 适配新的API响应格式
        const progressData = status.progress || {};
        const progress = progressData.completion_percentage || 0;
        const processedRows = progressData.translated_rows || 0;
        const totalRows = progressData.total_rows || 0;
        const currentIteration = progressData.current_iteration || 0;
        const maxIterations = progressData.max_iterations || 5;
        const currentStep = `迭代 ${currentIteration}/${maxIterations}`;

        // 更新进度条
        document.getElementById('progressFill').style.width = `${progress}%`;
        document.getElementById('progressText').textContent = `${progress.toFixed(1)}%`;

        // 更新状态
        document.getElementById('taskStatus').textContent = this.getStatusText(status.status);
        document.getElementById('processedRows').textContent = processedRows;
        document.getElementById('totalRows').textContent = totalRows;
        document.getElementById('currentStep').textContent = currentStep;

        // 更新耗时
        if (this.startTime) {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            document.getElementById('elapsedTime').textContent = `${elapsed}s`;
        }

        // 记录进度日志
        if (processedRows > 0) {
            this.log(`📊 进度更新: ${processedRows}/${totalRows} 行 (${progress.toFixed(1)}%) - ${currentStep}`);
        }
    }

    // 翻译完成处理
    onTranslationCompleted(status) {
        clearInterval(this.progressInterval);

        this.log('✅ 翻译任务完成！');

        // 显示结果区域
        document.getElementById('resultSection').style.display = 'block';

        // 更新结果详情
        const resultDetails = document.getElementById('resultDetails');
        resultDetails.innerHTML = `
            <div class="result-item">
                <span>任务ID:</span>
                <span>${this.currentTaskId}</span>
            </div>
            <div class="result-item">
                <span>处理行数:</span>
                <span>${status.processed_rows || 0}/${status.total_rows || 0}</span>
            </div>
            <div class="result-item">
                <span>总耗时:</span>
                <span>${this.formatDuration(Date.now() - this.startTime)}</span>
            </div>
            <div class="result-item">
                <span>翻译状态:</span>
                <span class="status-success">完成</span>
            </div>
        `;

        // 启用下载按钮
        document.getElementById('downloadBtn').disabled = false;
    }

    // 翻译失败处理
    onTranslationFailed(status) {
        clearInterval(this.progressInterval);

        const errorMsg = status.error || '未知错误';
        this.log('❌ 翻译任务失败: ' + errorMsg);
        alert('翻译任务失败: ' + errorMsg);
    }

    // 下载结果
    async downloadResult() {
        if (!this.currentTaskId) return;

        try {
            this.log('📥 开始下载翻译结果...');

            // 修正为正确的下载路径
            const response = await fetch(`${this.apiBase}/api/translation/tasks/${this.currentTaskId}/download`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            // 创建下载链接
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `translation_result_${this.currentTaskId}.xlsx`;

            document.body.appendChild(a);
            a.click();

            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.log('✅ 翻译结果下载完成');

        } catch (error) {
            this.log('❌ 下载失败: ' + error.message);
            alert('下载失败: ' + error.message);
        }
    }

    // 重置表单
    resetForm() {
        // 清理状态
        this.currentTaskId = null;
        this.selectedFile = null;
        this.startTime = null;
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }

        // 隐藏区域
        document.getElementById('translationOptions').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultSection').style.display = 'none';

        // 重置上传区域
        document.getElementById('uploadArea').innerHTML = `
            <div class="upload-icon">
                <i class="fas fa-file-excel"></i>
            </div>
            <p>拖拽Excel文件到此处，或点击选择文件</p>
            <input type="file" id="fileInput" accept=".xlsx,.xls" hidden>
            <button class="upload-btn" onclick="document.getElementById('fileInput').click()">
                选择文件
            </button>
        `;

        // 重新绑定事件
        this.setupEventListeners();

        this.log('🔄 表单已重置');
    }

    // 工具方法
    getStatusText(status) {
        const statusMap = {
            'pending': '等待中',
            'processing': '翻译中',
            'completed': '已完成',
            'failed': '失败',
            'cancelled': '已取消'
        };
        return statusMap[status] || status;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDuration(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);

        if (hours > 0) {
            return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        } else {
            return `${seconds}s`;
        }
    }

    log(message) {
        const timestamp = new Date().toLocaleTimeString();
        const logContainer = document.getElementById('logContainer');
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;

        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;

        console.log(`[${timestamp}] ${message}`);
    }
}

// 全局方法
function startTranslation() {
    window.tester.startTranslation();
}

function downloadResult() {
    window.tester.downloadResult();
}

function resetForm() {
    window.tester.resetForm();
}

// 初始化
window.addEventListener('DOMContentLoaded', () => {
    window.tester = new TranslationTester();
});