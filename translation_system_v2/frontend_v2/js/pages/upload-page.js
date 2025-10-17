/**
 * Upload Page - File Upload Optimization
 * Week 2 Day 6-7: Drag-and-drop, Batch Upload, Preview, Progress Tracking
 *
 * Features:
 * - Drag-and-drop upload zone
 * - Batch file upload support
 * - Excel file preview with SheetJS
 * - Upload progress tracking with XHR
 * - Enhanced file validation
 * - Multiple file management
 */

class UploadPage {
    constructor() {
        this.currentFiles = [];
        this.uploadZone = null;
        this.previewModal = null;
        this.validationRules = {
            maxSize: 50 * 1024 * 1024, // 50MB
            allowedTypes: ['.xlsx', '.xls'],
            maxSheets: 20,
            maxRows: 100000,
            maxBatchSize: 10 // Maximum files per batch
        };

        // API configuration
        this.apiBaseURL = window.API_BASE_URL || 'http://localhost:8013';
    }

    /**
     * Initialize upload page
     */
    init() {
        this.render();
        this.setupUploadZone();
        this.setupFileInput();
        this.setupBatchUpload();
        this.setupPreview();
        this.loadPreviousUploads();
    }

    /**
     * Render page structure
     */
    render() {
        const container = document.getElementById('app');
        if (!container) {
            console.error('App container not found');
            return;
        }

        container.innerHTML = `
            <div class="upload-page container mx-auto p-6 max-w-6xl">
                <!-- Header -->
                <div class="mb-8">
                    <h1 class="text-3xl font-bold mb-2">上传文件</h1>
                    <p class="text-gray-600">支持拖拽上传或点击选择文件，最多同时上传 ${this.validationRules.maxBatchSize} 个文件</p>
                </div>

                <!-- Upload Zone -->
                <div id="upload-zone" class="upload-zone border-4 border-dashed border-gray-300 rounded-xl p-12 text-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-all duration-300 mb-8">
                    <div class="upload-icon mb-4">
                        <svg class="w-16 h-16 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                    </div>
                    <p class="text-xl font-medium mb-2">拖拽文件到此处或点击上传</p>
                    <p class="text-sm text-gray-500">支持 .xlsx、.xls 格式，单个文件最大 50MB</p>
                    <input type="file" id="file-input" class="hidden" accept=".xlsx,.xls" multiple />
                    <button class="btn btn-primary mt-4" onclick="document.getElementById('file-input').click()">
                        选择文件
                    </button>
                </div>

                <!-- File List -->
                <div id="file-list-section" class="hidden mb-8">
                    <div class="flex items-center justify-between mb-4">
                        <h2 class="text-xl font-bold">待上传文件</h2>
                        <div class="space-x-2">
                            <button id="clear-files-btn" class="btn btn-outline btn-sm">清空列表</button>
                            <button id="upload-all-btn" class="btn btn-primary btn-sm">开始上传</button>
                        </div>
                    </div>
                    <div id="file-list" class="space-y-3"></div>
                </div>

                <!-- Upload Progress Modal (hidden by default) -->
                <div id="progress-modal" class="hidden"></div>

                <!-- Uploaded Files -->
                <div id="uploaded-files-section" class="hidden">
                    <h2 class="text-xl font-bold mb-4">已上传文件</h2>
                    <div id="uploaded-files-list" class="space-y-3"></div>
                </div>

                <!-- Validation Errors Modal (hidden by default) -->
                <div id="validation-errors-modal" class="hidden"></div>
            </div>
        `;
    }

    /**
     * Setup drag-and-drop upload zone
     */
    setupUploadZone() {
        this.uploadZone = document.getElementById('upload-zone');
        if (!this.uploadZone) return;

        // Prevent default drag behaviors on document
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            document.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        // Drag over event - highlight upload zone
        this.uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadZone.classList.add('border-blue-500', 'bg-blue-50');
            this.uploadZone.classList.remove('border-gray-300');
        });

        // Drag leave event - remove highlight
        this.uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            if (e.target === this.uploadZone) {
                this.uploadZone.classList.remove('border-blue-500', 'bg-blue-50');
                this.uploadZone.classList.add('border-gray-300');
            }
        });

        // Drop event - handle files
        this.uploadZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            this.uploadZone.classList.remove('border-blue-500', 'bg-blue-50');
            this.uploadZone.classList.add('border-gray-300');

            const files = Array.from(e.dataTransfer.files);
            await this.handleFiles(files);
        });

        // Click to upload
        this.uploadZone.addEventListener('click', (e) => {
            if (e.target === this.uploadZone || e.target.closest('.upload-icon') || e.target.tagName === 'P') {
                document.getElementById('file-input').click();
            }
        });
    }

    /**
     * Setup file input change handler
     */
    setupFileInput() {
        const fileInput = document.getElementById('file-input');
        if (!fileInput) return;

        fileInput.addEventListener('change', async (e) => {
            const files = Array.from(e.target.files);
            await this.handleFiles(files);
            // Clear input to allow re-selecting same file
            e.target.value = '';
        });
    }

    /**
     * Setup batch upload controls
     */
    setupBatchUpload() {
        // Clear files button
        const clearBtn = document.getElementById('clear-files-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.currentFiles = [];
                this.updateFileList();
            });
        }

        // Upload all button
        const uploadBtn = document.getElementById('upload-all-btn');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', async () => {
                await this.uploadAllFiles();
            });
        }
    }

    /**
     * Setup preview functionality
     */
    setupPreview() {
        this.previewModal = new ExcelPreviewModal();

        // Delegate preview clicks
        document.addEventListener('click', async (e) => {
            if (e.target.classList.contains('preview-btn') || e.target.closest('.preview-btn')) {
                const btn = e.target.classList.contains('preview-btn') ? e.target : e.target.closest('.preview-btn');
                const fileData = btn.dataset.fileData;
                if (fileData) {
                    const data = JSON.parse(fileData);
                    await this.previewModal.show(data);
                }
            }
        });
    }

    /**
     * Handle multiple files
     */
    async handleFiles(files) {
        if (files.length === 0) return;

        // Check batch size limit
        if (this.currentFiles.length + files.length > this.validationRules.maxBatchSize) {
            this.showError(`批量上传最多支持 ${this.validationRules.maxBatchSize} 个文件`);
            return;
        }

        // Validate and add files
        const validFiles = [];
        const errors = [];

        for (const file of files) {
            const validation = await this.validateFile(file);
            if (validation.valid) {
                validFiles.push({
                    file: file,
                    id: this.generateFileId(),
                    name: file.name,
                    size: file.size,
                    status: 'pending',
                    previewData: validation.previewData
                });
            } else {
                errors.push({
                    file: file.name,
                    errors: validation.errors
                });
            }
        }

        // Show validation errors if any
        if (errors.length > 0) {
            this.showValidationErrors(errors);
        }

        // Add valid files to current list
        if (validFiles.length > 0) {
            this.currentFiles.push(...validFiles);
            this.updateFileList();
        }
    }

    /**
     * Validate a single file
     */
    async validateFile(file) {
        const errors = [];

        // Size check
        if (file.size > this.validationRules.maxSize) {
            errors.push(`文件大小超过限制（最大 ${this.formatFileSize(this.validationRules.maxSize)}）`);
        }

        // Type check
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!this.validationRules.allowedTypes.includes(ext)) {
            errors.push(`不支持的文件类型（仅支持 ${this.validationRules.allowedTypes.join(', ')}）`);
        }

        // Excel content check
        let previewData = null;
        if (errors.length === 0) {
            try {
                previewData = await this.readExcelFile(file);

                if (previewData.sheets.length > this.validationRules.maxSheets) {
                    errors.push(`Sheet 数量超过限制（最大 ${this.validationRules.maxSheets} 个）`);
                }

                const totalRows = previewData.sheets.reduce((sum, sheet) => sum + sheet.rowCount, 0);
                if (totalRows > this.validationRules.maxRows) {
                    errors.push(`总行数超过限制（最大 ${this.validationRules.maxRows} 行）`);
                }
            } catch (error) {
                errors.push('文件读取失败：' + error.message);
            }
        }

        return {
            valid: errors.length === 0,
            errors,
            previewData
        };
    }

    /**
     * Read Excel file using SheetJS
     */
    async readExcelFile(file) {
        return new Promise((resolve, reject) => {
            // Check if SheetJS is loaded
            if (typeof XLSX === 'undefined') {
                reject(new Error('SheetJS library not loaded. Please include xlsx.js'));
                return;
            }

            const reader = new FileReader();

            reader.onload = (e) => {
                try {
                    const data = new Uint8Array(e.target.result);
                    const workbook = XLSX.read(data, { type: 'array' });

                    const sheets = workbook.SheetNames.map(name => {
                        const sheet = workbook.Sheets[name];
                        const range = sheet['!ref'] ? XLSX.utils.decode_range(sheet['!ref']) : { s: { r: 0, c: 0 }, e: { r: 0, c: 0 } };
                        const jsonData = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });

                        return {
                            name,
                            rowCount: range.e.r - range.s.r + 1,
                            colCount: range.e.c - range.s.c + 1,
                            data: jsonData.slice(0, 20), // Preview first 20 rows
                            hasMore: jsonData.length > 20
                        };
                    });

                    resolve({
                        sheets,
                        filename: file.name
                    });
                } catch (error) {
                    reject(error);
                }
            };

            reader.onerror = () => reject(new Error('文件读取失败'));
            reader.readAsArrayBuffer(file);
        });
    }

    /**
     * Update file list display
     */
    updateFileList() {
        const fileListSection = document.getElementById('file-list-section');
        const fileList = document.getElementById('file-list');

        if (this.currentFiles.length === 0) {
            fileListSection.classList.add('hidden');
            return;
        }

        fileListSection.classList.remove('hidden');
        fileList.innerHTML = this.currentFiles.map(fileData => `
            <div class="file-item border rounded-lg p-4 flex items-center gap-4 hover:shadow-md transition-shadow" data-file-id="${fileData.id}">
                <div class="file-icon text-blue-500">
                    <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                </div>
                <div class="flex-1">
                    <p class="font-medium">${fileData.name}</p>
                    <p class="text-sm text-gray-500">
                        ${this.formatFileSize(fileData.size)} •
                        ${fileData.previewData ? fileData.previewData.sheets.length + ' sheets' : ''}
                    </p>
                </div>
                <div class="file-actions space-x-2">
                    <button class="btn btn-sm btn-outline preview-btn" data-file-data='${JSON.stringify(fileData.previewData)}'>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        预览
                    </button>
                    <button class="btn btn-sm btn-ghost remove-file-btn" onclick="uploadPage.removeFile('${fileData.id}')">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * Remove file from list
     */
    removeFile(fileId) {
        this.currentFiles = this.currentFiles.filter(f => f.id !== fileId);
        this.updateFileList();
    }

    /**
     * Upload all files in batch
     */
    async uploadAllFiles() {
        if (this.currentFiles.length === 0) return;

        // Show progress modal
        const progressModal = this.showProgressModal(this.currentFiles);

        for (let i = 0; i < this.currentFiles.length; i++) {
            const fileData = this.currentFiles[i];
            progressModal.updateProgress(i, 0, 'uploading');

            try {
                // Create FormData
                const formData = new FormData();
                formData.append('file', fileData.file);

                // Upload with progress tracking
                const response = await this.uploadWithProgress(
                    formData,
                    (progress) => progressModal.updateProgress(i, progress, 'uploading')
                );

                // Save result
                fileData.sessionId = response.session_id;
                fileData.status = 'uploaded';
                progressModal.updateProgress(i, 100, 'completed');

            } catch (error) {
                fileData.status = 'failed';
                progressModal.showError(i, error.message);
            }
        }

        // Show results and update UI
        setTimeout(() => {
            progressModal.close();
            this.showUploadResults();
            this.currentFiles = []; // Clear pending files
            this.updateFileList();
        }, 2000);
    }

    /**
     * Upload single file with progress tracking
     */
    async uploadWithProgress(formData, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            // Upload progress
            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const progress = (e.loaded / e.total) * 100;
                    onProgress(progress);
                }
            };

            // Success
            xhr.onload = () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (error) {
                        reject(new Error('Invalid server response'));
                    }
                } else {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            };

            // Error
            xhr.onerror = () => reject(new Error('Network error'));
            xhr.ontimeout = () => reject(new Error('Upload timeout'));

            // Configure and send
            xhr.open('POST', `${this.apiBaseURL}/api/tasks/split`);
            xhr.timeout = 120000; // 2 minutes timeout
            xhr.send(formData);
        });
    }

    /**
     * Show upload progress modal
     */
    showProgressModal(files) {
        const modal = document.createElement('div');
        modal.id = 'upload-progress-modal';
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
                <div class="p-6 border-b">
                    <h3 class="text-xl font-bold">上传进度</h3>
                </div>
                <div class="p-6 overflow-y-auto flex-1">
                    <div class="space-y-4">
                        ${files.map((fileData, i) => `
                            <div class="upload-item border rounded-lg p-4" data-index="${i}">
                                <div class="flex justify-between items-center mb-2">
                                    <span class="text-sm font-medium">${fileData.name}</span>
                                    <span class="progress-text text-sm text-gray-500">0%</span>
                                </div>
                                <div class="progress-bar-container w-full bg-gray-200 rounded-full h-2.5">
                                    <div class="progress-bar bg-blue-500 h-2.5 rounded-full transition-all duration-300" style="width: 0%"></div>
                                </div>
                                <div class="error-message text-red-500 text-sm mt-2 hidden"></div>
                                <div class="success-message text-green-500 text-sm mt-2 hidden">
                                    <svg class="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                                    </svg>
                                    上传成功
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="p-6 border-t">
                    <button class="btn btn-primary w-full hidden" id="close-progress-modal">完成</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        return {
            updateProgress(index, progress, status) {
                const item = modal.querySelector(`[data-index="${index}"]`);
                if (!item) return;

                const progressBar = item.querySelector('.progress-bar');
                const progressText = item.querySelector('.progress-text');

                progressBar.style.width = `${progress}%`;
                progressText.textContent = `${Math.round(progress)}%`;

                if (status === 'completed') {
                    progressBar.classList.remove('bg-blue-500');
                    progressBar.classList.add('bg-green-500');
                    item.querySelector('.success-message').classList.remove('hidden');
                }
            },

            showError(index, message) {
                const item = modal.querySelector(`[data-index="${index}"]`);
                if (!item) return;

                const progressBar = item.querySelector('.progress-bar');
                const errorDiv = item.querySelector('.error-message');

                progressBar.classList.remove('bg-blue-500');
                progressBar.classList.add('bg-red-500');
                errorDiv.textContent = message;
                errorDiv.classList.remove('hidden');
            },

            close() {
                modal.remove();
            }
        };
    }

    /**
     * Show validation errors modal
     */
    showValidationErrors(errors) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
                <div class="p-6 border-b">
                    <h3 class="text-xl font-bold text-red-600">文件验证失败</h3>
                </div>
                <div class="p-6">
                    <div class="space-y-4">
                        ${errors.map(error => `
                            <div class="border-l-4 border-red-500 pl-4 py-2">
                                <p class="font-medium">${error.file}</p>
                                <ul class="list-disc list-inside text-sm text-gray-600 mt-1">
                                    ${error.errors.map(err => `<li>${err}</li>`).join('')}
                                </ul>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="p-6 border-t">
                    <button class="btn btn-primary w-full" onclick="this.closest('.fixed').remove()">关闭</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    /**
     * Show upload results and move to uploaded files section
     */
    showUploadResults() {
        const uploadedFiles = this.currentFiles.filter(f => f.status === 'uploaded');

        if (uploadedFiles.length === 0) return;

        // Save to localStorage for persistence
        const stored = JSON.parse(localStorage.getItem('uploadedFiles') || '[]');
        uploadedFiles.forEach(file => {
            stored.push({
                id: file.id,
                name: file.name,
                sessionId: file.sessionId,
                uploadTime: new Date().toISOString()
            });
        });
        localStorage.setItem('uploadedFiles', JSON.stringify(stored));

        // Update UI
        this.loadPreviousUploads();
    }

    /**
     * Load previously uploaded files from localStorage
     */
    loadPreviousUploads() {
        const stored = JSON.parse(localStorage.getItem('uploadedFiles') || '[]');

        if (stored.length === 0) {
            document.getElementById('uploaded-files-section').classList.add('hidden');
            return;
        }

        const section = document.getElementById('uploaded-files-section');
        const list = document.getElementById('uploaded-files-list');

        section.classList.remove('hidden');
        list.innerHTML = stored.map(file => `
            <div class="border rounded-lg p-4 flex items-center justify-between hover:shadow-md transition-shadow">
                <div class="flex items-center gap-4">
                    <div class="text-green-500">
                        <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <div>
                        <p class="font-medium">${file.name}</p>
                        <p class="text-sm text-gray-500">
                            Session ID: ${file.sessionId} •
                            上传时间: ${new Date(file.uploadTime).toLocaleString('zh-CN')}
                        </p>
                    </div>
                </div>
                <div class="space-x-2">
                    <a href="#/config?session=${file.sessionId}" class="btn btn-sm btn-primary">配置任务</a>
                    <button class="btn btn-sm btn-ghost" onclick="uploadPage.removeUploadedFile('${file.id}')">删除</button>
                </div>
            </div>
        `).join('');
    }

    /**
     * Remove uploaded file from history
     */
    removeUploadedFile(fileId) {
        const stored = JSON.parse(localStorage.getItem('uploadedFiles') || '[]');
        const filtered = stored.filter(f => f.id !== fileId);
        localStorage.setItem('uploadedFiles', JSON.stringify(filtered));
        this.loadPreviousUploads();
    }

    /**
     * Utility: Generate unique file ID
     */
    generateFileId() {
        return `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Utility: Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    /**
     * Utility: Show error message
     */
    showError(message) {
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('animate-fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

/**
 * Excel Preview Modal Component
 * Displays Excel file content with sheet tabs and table view
 */
class ExcelPreviewModal {
    /**
     * Show preview modal for Excel file
     */
    async show(previewData) {
        if (!previewData || !previewData.sheets) {
            console.error('Invalid preview data');
            return;
        }

        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] flex flex-col">
                <div class="p-6 border-b flex items-center justify-between">
                    <h3 class="text-xl font-bold">文件预览: ${previewData.filename}</h3>
                    <button class="text-gray-500 hover:text-gray-700" onclick="this.closest('.fixed').remove()">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <!-- Sheet Tabs -->
                <div class="border-b overflow-x-auto">
                    <div class="flex px-6">
                        ${previewData.sheets.map((sheet, i) => `
                            <button class="sheet-tab px-4 py-3 border-b-2 ${i === 0 ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-600'} hover:text-blue-600 transition-colors whitespace-nowrap"
                                    data-sheet="${i}">
                                ${sheet.name} (${sheet.rowCount} rows)
                            </button>
                        `).join('')}
                    </div>
                </div>

                <!-- Preview Content -->
                <div class="p-6 overflow-auto flex-1">
                    <div id="preview-table-container"></div>
                </div>

                <div class="p-6 border-t">
                    <button class="btn btn-primary w-full" onclick="this.closest('.fixed').remove()">关闭</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Render first sheet
        this.renderSheet(modal, previewData.sheets[0]);

        // Setup tab switching
        modal.querySelectorAll('.sheet-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                // Update active tab
                modal.querySelectorAll('.sheet-tab').forEach(t => {
                    t.classList.remove('border-blue-500', 'text-blue-600');
                    t.classList.add('border-transparent', 'text-gray-600');
                });
                tab.classList.remove('border-transparent', 'text-gray-600');
                tab.classList.add('border-blue-500', 'text-blue-600');

                // Render selected sheet
                const index = parseInt(tab.dataset.sheet);
                this.renderSheet(modal, previewData.sheets[index]);
            });
        });
    }

    /**
     * Render sheet data as table
     */
    renderSheet(modal, sheet) {
        const container = modal.querySelector('#preview-table-container');

        if (!sheet.data || sheet.data.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-8">此 Sheet 为空</p>';
            return;
        }

        // Build table HTML
        const maxCols = Math.max(...sheet.data.map(row => row.length));
        const headers = Array.from({ length: maxCols }, (_, i) => this.getColumnLabel(i));

        container.innerHTML = `
            <div class="overflow-x-auto">
                <table class="table-auto border-collapse border border-gray-300 w-full text-sm">
                    <thead class="bg-gray-100">
                        <tr>
                            <th class="border border-gray-300 px-3 py-2 font-medium text-gray-700">#</th>
                            ${headers.map(header => `
                                <th class="border border-gray-300 px-3 py-2 font-medium text-gray-700">${header}</th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${sheet.data.map((row, rowIndex) => `
                            <tr class="${rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}">
                                <td class="border border-gray-300 px-3 py-2 text-gray-500 font-medium">${rowIndex + 1}</td>
                                ${headers.map((_, colIndex) => `
                                    <td class="border border-gray-300 px-3 py-2">${this.escapeHtml(row[colIndex] || '')}</td>
                                `).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            ${sheet.hasMore ? `
                <p class="text-center text-sm text-gray-500 mt-4">
                    ... 还有 ${sheet.rowCount - 20} 行未显示（仅预览前 20 行）
                </p>
            ` : ''}
        `;
    }

    /**
     * Get Excel column label (A, B, C, ... Z, AA, AB, ...)
     */
    getColumnLabel(index) {
        let label = '';
        index++;
        while (index > 0) {
            const rem = (index - 1) % 26;
            label = String.fromCharCode(65 + rem) + label;
            index = Math.floor((index - 1) / 26);
        }
        return label;
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for global access
if (typeof window !== 'undefined') {
    window.UploadPage = UploadPage;
    window.ExcelPreviewModal = ExcelPreviewModal;
}
