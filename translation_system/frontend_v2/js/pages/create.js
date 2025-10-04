// 项目创建页
class CreatePage {
    constructor() {
        this.selectedFile = null;
        this.isUploading = false;
        this.dragCounter = 0;
    }

    render() {
        const html = `
            <div class="max-w-4xl mx-auto">
                <!-- 页面标题 -->
                <div class="text-center mb-8">
                    <h1 class="text-3xl font-bold mb-2">开始新的Excel翻译项目</h1>
                    <p class="text-base-content/70">上传您的Excel文件，我们将自动分析并准备翻译</p>
                </div>

                <!-- 检查未完成会话 -->
                <div id="unfinishedAlert" class="hidden mb-6">
                    <div class="alert alert-warning">
                        <i class="bi bi-exclamation-triangle-fill"></i>
                        <span>您有未完成的翻译任务</span>
                        <div>
                            <button class="btn btn-sm" onclick="createPage.resumeSession()">继续</button>
                            <button class="btn btn-sm btn-ghost" onclick="createPage.dismissAlert()">忽略</button>
                        </div>
                    </div>
                </div>

                <!-- 文件上传卡片 -->
                <div class="card bg-base-100 shadow-xl">
                    <div class="card-body">
                        <!-- 拖拽上传区域 -->
                        <div id="dropZone" class="border-2 border-dashed border-base-300 rounded-lg p-12 text-center drop-zone hover:border-primary transition-all">
                            <i class="bi bi-cloud-upload text-6xl text-base-content/30 mb-4"></i>
                            <p class="text-lg mb-2">拖拽Excel文件到这里</p>
                            <p class="text-base-content/70 mb-4">或</p>
                            <button class="btn btn-primary" onclick="createPage.selectFile()">
                                <i class="bi bi-folder2-open"></i>
                                选择文件
                            </button>
                            <p class="text-sm text-base-content/50 mt-4">
                                支持格式：.xlsx, .xls | 最大大小：100MB
                            </p>
                        </div>

                        <!-- 文件信息显示 -->
                        <div id="fileInfo" class="hidden mt-6">
                            <div class="bg-base-200 rounded-lg p-4">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center gap-3">
                                        <i class="bi bi-file-earmark-excel text-2xl text-success"></i>
                                        <div>
                                            <p class="font-semibold" id="fileName">--</p>
                                            <p class="text-sm text-base-content/70" id="fileSize">--</p>
                                        </div>
                                    </div>
                                    <button class="btn btn-sm btn-ghost" onclick="createPage.removeFile()">
                                        <i class="bi bi-x-lg"></i>
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- 游戏信息（可选） -->
                        <div class="divider">游戏信息（可选）</div>

                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text">游戏名称</span>
                                </label>
                                <input type="text" id="gameName" placeholder="例：原神" class="input input-bordered" />
                            </div>

                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text">版本号</span>
                                </label>
                                <input type="text" id="gameVersion" placeholder="例：1.0.0" class="input input-bordered" />
                            </div>

                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text">备注</span>
                                </label>
                                <input type="text" id="gameNotes" placeholder="可选" class="input input-bordered" />
                            </div>
                        </div>

                        <!-- 上传按钮 -->
                        <div class="card-actions justify-end mt-6">
                            <button id="uploadBtn" class="btn btn-primary btn-lg" onclick="createPage.uploadFile()" disabled>
                                <i class="bi bi-upload"></i>
                                上传并分析
                            </button>
                        </div>

                        <!-- 上传进度 -->
                        <div id="uploadProgress" class="hidden mt-6">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-sm">上传中...</span>
                                <span class="text-sm" id="uploadPercent">0%</span>
                            </div>
                            <progress class="progress progress-primary w-full" id="progressBar" value="0" max="100"></progress>
                        </div>
                    </div>
                </div>

                <!-- 分析结果卡片 -->
                <div id="analysisResult" class="hidden mt-6">
                    <div class="card bg-base-100 shadow-xl">
                        <div class="card-body">
                            <h2 class="card-title">
                                <i class="bi bi-check-circle-fill text-success"></i>
                                分析完成
                            </h2>

                            <div class="alert alert-info">
                                <i class="bi bi-info-circle-fill"></i>
                                <div>
                                    <p class="font-semibold">Session ID: <span id="sessionId" class="font-mono">--</span></p>
                                    <button class="btn btn-xs btn-ghost" onclick="createPage.copySessionId()">
                                        <i class="bi bi-clipboard"></i>
                                        复制
                                    </button>
                                </div>
                            </div>

                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                                <div class="stat bg-base-200 rounded-lg p-4">
                                    <div class="stat-title">Sheets</div>
                                    <div class="stat-value text-2xl" id="sheetCount">--</div>
                                </div>
                                <div class="stat bg-base-200 rounded-lg p-4">
                                    <div class="stat-title">单元格</div>
                                    <div class="stat-value text-2xl" id="cellCount">--</div>
                                </div>
                                <div class="stat bg-base-200 rounded-lg p-4">
                                    <div class="stat-title">预估任务</div>
                                    <div class="stat-value text-2xl" id="taskCount">--</div>
                                </div>
                                <div class="stat bg-base-200 rounded-lg p-4">
                                    <div class="stat-title">成功率</div>
                                    <div class="stat-value text-2xl text-success">98%</div>
                                </div>
                            </div>

                            <!-- 任务类型分布 -->
                            <div class="mt-4">
                                <h3 class="font-semibold mb-2">任务类型分布</h3>
                                <div class="grid grid-cols-3 gap-2">
                                    <div class="badge badge-lg badge-outline">
                                        <i class="bi bi-circle-fill text-info mr-1"></i>
                                        常规翻译: <span id="normalTasks">--</span>
                                    </div>
                                    <div class="badge badge-lg badge-outline">
                                        <i class="bi bi-circle-fill text-warning mr-1"></i>
                                        黄色重翻: <span id="yellowTasks">--</span>
                                    </div>
                                    <div class="badge badge-lg badge-outline">
                                        <i class="bi bi-circle-fill text-primary mr-1"></i>
                                        蓝色缩短: <span id="blueTasks">--</span>
                                    </div>
                                </div>
                            </div>

                            <div class="card-actions justify-end mt-6">
                                <button class="btn btn-primary" onclick="createPage.continueToConfig()">
                                    继续配置
                                    <i class="bi bi-arrow-right"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('pageContent').innerHTML = html;
        this.initEventListeners();
        this.checkUnfinishedSessions();
        this.loadUserPreferences();

        // 更新全局进度
        UIHelper.updateGlobalProgress(1);
    }

    initEventListeners() {
        const dropZone = document.getElementById('dropZone');

        // 拖拽事件
        dropZone.addEventListener('dragenter', (e) => this.handleDragEnter(e));
        dropZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
        dropZone.addEventListener('drop', (e) => this.handleDrop(e));
    }

    handleDragEnter(e) {
        e.preventDefault();
        this.dragCounter++;
        document.getElementById('dropZone').classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.dragCounter--;
        if (this.dragCounter === 0) {
            document.getElementById('dropZone').classList.remove('dragover');
        }
    }

    handleDragOver(e) {
        e.preventDefault();
    }

    handleDrop(e) {
        e.preventDefault();
        this.dragCounter = 0;
        document.getElementById('dropZone').classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files && files[0]) {
            this.handleFileSelect(files[0]);
        }
    }

    selectFile() {
        UIHelper.createFileInput('.xlsx,.xls', (file) => {
            this.handleFileSelect(file);
        });
    }

    handleFileSelect(file) {
        // 验证文件
        const validation = this.validateFile(file);
        if (!validation.valid) {
            UIHelper.showToast(validation.message, 'error');
            return;
        }

        this.selectedFile = file;
        this.displayFileInfo(file);
        document.getElementById('uploadBtn').disabled = false;
    }

    validateFile(file) {
        // 检查文件扩展名
        const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        if (!APP_CONFIG.ALLOWED_EXTENSIONS.includes(extension)) {
            return { valid: false, message: '请上传Excel文件（.xlsx或.xls）' };
        }

        // 检查文件大小
        if (file.size > APP_CONFIG.MAX_FILE_SIZE) {
            return { valid: false, message: '文件大小不能超过100MB' };
        }

        return { valid: true };
    }

    displayFileInfo(file) {
        document.getElementById('fileInfo').classList.remove('hidden');
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileSize').textContent = UIHelper.formatFileSize(file.size);
    }

    removeFile() {
        this.selectedFile = null;
        document.getElementById('fileInfo').classList.add('hidden');
        document.getElementById('uploadBtn').disabled = true;
    }

    async uploadFile() {
        if (!this.selectedFile || this.isUploading) return;

        this.isUploading = true;
        document.getElementById('uploadBtn').disabled = true;
        document.getElementById('uploadProgress').classList.remove('hidden');

        try {
            // 收集游戏信息
            const gameInfo = this.getGameInfo();

            // 模拟上传进度
            this.simulateProgress();

            // 上传文件
            const result = await API.uploadFile(this.selectedFile, gameInfo);

            // 创建会话
            sessionManager.createSession(
                result.session_id,
                this.selectedFile.name,
                result.analysis
            );

            // 显示分析结果
            this.displayAnalysisResult(result);

            // 保存用户偏好
            this.saveUserPreferences(gameInfo);

            UIHelper.showToast('文件上传成功！', 'success');

        } catch (error) {
            UIHelper.showToast(`上传失败：${error.message}`, 'error');
            document.getElementById('uploadProgress').classList.add('hidden');
            document.getElementById('uploadBtn').disabled = false;
        } finally {
            this.isUploading = false;
        }
    }

    simulateProgress() {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress > 95) {
                progress = 95;
                clearInterval(interval);
            }
            UIHelper.updateProgress('progressBar', progress);
            document.getElementById('uploadPercent').textContent = `${Math.round(progress)}%`;
        }, 500);
    }

    getGameInfo() {
        const gameName = document.getElementById('gameName').value.trim();
        const gameVersion = document.getElementById('gameVersion').value.trim();
        const gameNotes = document.getElementById('gameNotes').value.trim();

        if (gameName || gameVersion || gameNotes) {
            return {
                game_name: gameName,
                version: gameVersion,
                notes: gameNotes
            };
        }

        return null;
    }

    displayAnalysisResult(result) {
        document.getElementById('uploadProgress').classList.add('hidden');
        document.getElementById('analysisResult').classList.remove('hidden');

        // 基本信息
        document.getElementById('sessionId').textContent = result.session_id;
        document.getElementById('sheetCount').textContent = result.analysis.statistics.sheet_count;
        document.getElementById('cellCount').textContent = result.analysis.statistics.total_cells.toLocaleString();
        document.getElementById('taskCount').textContent = result.analysis.statistics.estimated_tasks.toLocaleString();

        // 任务类型分布
        const breakdown = result.analysis.statistics.task_breakdown || {};
        document.getElementById('normalTasks').textContent = breakdown.normal_tasks || 0;
        document.getElementById('yellowTasks').textContent = breakdown.yellow_tasks || 0;
        document.getElementById('blueTasks').textContent = breakdown.blue_tasks || 0;
    }

    copySessionId() {
        const sessionId = document.getElementById('sessionId').textContent;
        navigator.clipboard.writeText(sessionId);
        UIHelper.showToast('Session ID已复制到剪贴板', 'success');
    }

    continueToConfig() {
        window.location.hash = '#/config';
    }

    checkUnfinishedSessions() {
        const unfinished = SessionManager.checkUnfinishedSessions();
        if (unfinished && unfinished.length > 0) {
            this.showUnfinishedAlert(unfinished[0]);
        }
    }

    showUnfinishedAlert(session) {
        const alert = document.getElementById('unfinishedAlert');
        alert.classList.remove('hidden');
        alert.querySelector('span').textContent =
            `您有未完成的翻译任务：${session.filename}`;
        this.unfinishedSession = session;
    }

    resumeSession() {
        if (this.unfinishedSession) {
            sessionManager.loadSession(this.unfinishedSession.sessionId);

            // 根据阶段跳转
            const stageRoutes = {
                'created': '#/config',
                'configured': '#/execute',
                'executing': '#/execute',
                'completed': '#/complete'
            };

            window.location.hash = stageRoutes[this.unfinishedSession.stage] || '#/config';
        }
    }

    dismissAlert() {
        document.getElementById('unfinishedAlert').classList.add('hidden');
    }

    loadUserPreferences() {
        const prefs = Storage.getPreferences();
        if (prefs.lastGameName) {
            document.getElementById('gameName').value = prefs.lastGameName;
        }
        if (prefs.lastVersion) {
            document.getElementById('gameVersion').value = prefs.lastVersion;
        }
    }

    saveUserPreferences(gameInfo) {
        if (gameInfo) {
            const prefs = Storage.getPreferences();
            prefs.lastGameName = gameInfo.game_name || '';
            prefs.lastVersion = gameInfo.version || '';
            Storage.savePreferences(prefs);
        }
    }
}

// 创建页面实例
const createPage = new CreatePage();