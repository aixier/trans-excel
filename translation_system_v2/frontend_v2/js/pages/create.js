// 项目创建页
class CreatePage {
    constructor() {
        this.selectedFile = null;
        this.isUploading = false;
        this.dragCounter = 0;
    }

    render() {
        const html = `
            <div class="h-full flex flex-col">
                <!-- 页面标题 -->
                <div class="mb-3">
                    <h1 class="text-lg font-bold">
                        <i class="bi bi-cloud-upload text-primary"></i>
                        开始新的翻译项目
                    </h1>
                </div>

                <!-- 未完成会话列表 -->
                <div id="unfinishedSessions"></div>

                <!-- 主内容区域 - 左右分栏 -->
                <div class="flex-1 flex gap-4 overflow-hidden">
                    <!-- 左侧：文件上传 -->
                    <div class="flex-1">
                        <div class="card bg-base-100 shadow-xl h-full">
                            <div class="card-body">
                        <!-- 拖拽上传区域 -->
                        <div id="dropZone" class="border-2 border-dashed border-base-300 rounded-lg p-6 text-center drop-zone hover:border-primary transition-all">
                            <i class="bi bi-cloud-upload text-3xl text-base-content/30 mb-2"></i>
                            <p class="mb-2">拖拽Excel文件到这里</p>
                            <div class="flex items-center justify-center gap-2">
                                <span class="text-sm text-base-content/70">或</span>
                                <button class="btn btn-primary btn-sm" onclick="createPage.selectFile()">
                                    <i class="bi bi-folder2-open"></i>
                                    选择文件
                                </button>
                            </div>
                            <p class="text-xs text-base-content/50 mt-2">
                                支持格式：.xlsx, .xls | 最大：100MB
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
                        <div class="divider my-2 text-sm">游戏信息（可选）</div>

                        <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
                            <div class="form-control">
                                <input type="text" id="gameName" placeholder="游戏名称" class="input input-bordered input-sm" />
                            </div>
                            <div class="form-control">
                                <input type="text" id="gameVersion" placeholder="版本号" class="input input-bordered input-sm" />
                            </div>
                            <div class="form-control">
                                <input type="text" id="gameNotes" placeholder="备注" class="input input-bordered input-sm" />
                            </div>
                        </div>

                        <!-- 上传按钮 -->
                        <div class="card-actions justify-end mt-3">
                            <button id="uploadBtn" class="btn btn-primary btn-lg" onclick="createPage.uploadFile()" disabled>
                                <i class="bi bi-upload"></i>
                                上传并分析
                            </button>
                        </div>

                                <!-- 上传进度 -->
                                <div id="uploadProgress" class="hidden mt-4">
                                    <div class="flex items-center justify-between mb-2">
                                        <span class="text-sm">上传中...</span>
                                        <span class="text-sm" id="uploadPercent">0%</span>
                                    </div>
                                    <progress class="progress progress-primary w-full" id="progressBar" value="0" max="100"></progress>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 右侧：分析结果 -->
                    <div id="analysisResult" class="hidden flex-1">
                        <div class="card bg-base-100 shadow-xl h-full">
                            <div class="card-body">
                            <h2 class="card-title">
                                <i class="bi bi-check-circle-fill text-success"></i>
                                分析完成
                            </h2>

                            <div class="grid grid-cols-2 gap-2 mt-3">
                                <div class="stat bg-base-200 rounded-lg p-2">
                                    <div class="stat-title text-xs">Sheets</div>
                                    <div class="stat-value text-lg" id="sheetCount">--</div>
                                </div>
                                <div class="stat bg-base-200 rounded-lg p-2">
                                    <div class="stat-title text-xs">单元格</div>
                                    <div class="stat-value text-lg" id="cellCount">--</div>
                                </div>
                                <div class="stat bg-base-200 rounded-lg p-2">
                                    <div class="stat-title text-xs">预估任务</div>
                                    <div class="stat-value text-lg" id="taskCount">--</div>
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
                <!-- 结束主内容区域 -->
            </div>
        `;

        document.getElementById('pageContent').innerHTML = html;
        this.initEventListeners();
        this.loadUserPreferences();
        this.renderUnfinishedSessions();

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

            // 检查元素是否存在（页面可能已跳转）
            const progressBar = document.getElementById('progressBar');
            const uploadPercent = document.getElementById('uploadPercent');

            if (progressBar && uploadPercent) {
                UIHelper.updateProgress('progressBar', progress);
                uploadPercent.textContent = `${Math.round(progress)}%`;
            } else {
                // 元素不存在，停止定时器
                clearInterval(interval);
            }
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

        // 显示右侧分析结果面板
        const resultPanel = document.getElementById('analysisResult');
        resultPanel.classList.remove('hidden');
        resultPanel.style.display = 'block';

        // 基本信息
        document.getElementById('sheetCount').textContent = result.analysis.statistics.sheet_count;
        document.getElementById('cellCount').textContent = result.analysis.statistics.total_cells.toLocaleString();
        document.getElementById('taskCount').textContent = result.analysis.statistics.estimated_tasks.toLocaleString();

        // 任务类型分布
        const breakdown = result.analysis.statistics.task_breakdown || {};
        document.getElementById('normalTasks').textContent = breakdown.normal_tasks || 0;
        document.getElementById('yellowTasks').textContent = breakdown.yellow_tasks || 0;
        document.getElementById('blueTasks').textContent = breakdown.blue_tasks || 0;

        // 显示成功提示
        UIHelper.showToast('分析完成！', 'success');

        // 添加倒计时提示（可取消）
        let countdown = 10;
        const countdownElement = document.createElement('div');
        countdownElement.className = 'alert alert-info mt-3';
        countdownElement.innerHTML = `
            <i class="bi bi-info-circle"></i>
            <span><span id="countdown">${countdown}</span>秒后自动跳转到配置页</span>
            <button class="btn btn-sm btn-ghost" onclick="createPage.cancelAutoRedirect()">留在此页</button>
        `;
        document.querySelector('#analysisResult .card-body').appendChild(countdownElement);

        this.redirectTimer = setInterval(() => {
            countdown--;
            const elem = document.getElementById('countdown');
            if (elem) elem.textContent = countdown;

            if (countdown <= 0) {
                clearInterval(this.redirectTimer);
                this.continueToConfig();
            }
        }, 1000);
    }

    cancelAutoRedirect() {
        if (this.redirectTimer) {
            clearInterval(this.redirectTimer);
            this.redirectTimer = null;
            const countdownElement = document.querySelector('.alert-info');
            if (countdownElement) {
                countdownElement.remove();
            }
            UIHelper.showToast('已取消自动跳转', 'info');
        }
    }


    continueToConfig() {
        // 清理定时器
        if (this.redirectTimer) {
            clearInterval(this.redirectTimer);
            this.redirectTimer = null;
        }
        window.location.hash = '#/config';
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

    // ========== 未完成会话管理 ==========

    /**
     * 渲染未完成会话列表
     */
    renderUnfinishedSessions() {
        const unfinishedSessions = SessionManager.checkUnfinishedSessions();
        const container = document.getElementById('unfinishedSessions');

        if (!container) return;

        // 没有未完成会话
        if (!unfinishedSessions || unfinishedSessions.length === 0) {
            container.innerHTML = '';
            return;
        }

        // 构建会话列表HTML
        const sessionsHTML = unfinishedSessions.map(session => {
            const stage = this.getSessionStage(session);
            const timeAgo = this.formatTimeAgo(session.createdAt);
            const progress = stage.progress;

            return `
                <div class="card bg-base-100 shadow-sm border border-base-300 mb-3">
                    <div class="card-body p-4">
                        <div class="flex items-start justify-between">
                            <!-- 左侧信息 -->
                            <div class="flex-1">
                                <div class="flex items-center gap-2 mb-2">
                                    <i class="bi bi-file-earmark-excel text-xl text-success"></i>
                                    <h3 class="font-semibold">${session.filename}</h3>
                                    <span class="badge badge-sm">${timeAgo}</span>
                                </div>

                                <!-- 进度条 -->
                                <div class="mb-2">
                                    <div class="flex items-center justify-between text-xs mb-1">
                                        <span class="text-base-content/70">${stage.label}</span>
                                        <span class="font-semibold">${progress}%</span>
                                    </div>
                                    <progress class="progress progress-primary w-full h-2" value="${progress}" max="100"></progress>
                                </div>

                                <!-- 会话信息 -->
                                <div class="text-xs text-base-content/60">
                                    Session ID: ${session.sessionId.substring(0, 8)}...
                                </div>
                            </div>

                            <!-- 右侧操作按钮 -->
                            <div class="flex gap-2 ml-4">
                                <button
                                    class="btn btn-primary btn-sm"
                                    onclick="createPage.continueSession('${session.sessionId}')"
                                    title="继续翻译">
                                    <i class="bi bi-play-fill"></i>
                                    继续
                                </button>
                                <button
                                    class="btn btn-ghost btn-sm text-error"
                                    onclick="createPage.deleteSession('${session.sessionId}')"
                                    title="删除会话">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // 构建完整的UI
        container.innerHTML = `
            <div class="alert alert-info mb-4">
                <i class="bi bi-info-circle"></i>
                <div class="flex-1">
                    <h3 class="font-bold">发现 ${unfinishedSessions.length} 个未完成的会话</h3>
                    <div class="text-sm">你可以继续之前的翻译工作，或者上传新文件</div>
                </div>
            </div>
            ${sessionsHTML}
            <div class="divider text-sm">或者上传新文件</div>
        `;
    }

    /**
     * 继续会话
     */
    async continueSession(sessionId) {
        logger.log('Continuing session:', sessionId);

        // 加载会话
        const success = sessionManager.loadSession(sessionId);

        if (!success) {
            UIHelper.showToast('会话加载失败', 'error');
            return;
        }

        // 根据会话状态跳转到对应页面
        const session = sessionManager.session;

        if (!session) {
            UIHelper.showToast('会话数据异常', 'error');
            return;
        }

        // 验证后端会话是否还存在
        try {
            UIHelper.showLoading(true);

            // 尝试获取分析状态（所有会话都应该有）
            await API.getAnalysisStatus(sessionId);

            UIHelper.showLoading(false);

            // 判断会话阶段
            if (session.executionResult || session.taskData) {
                // 已经拆分任务或有执行结果，跳转到执行页（执行页支持下载）
                router.navigate(`/execute/${sessionId}`);
            } else if (session.analysis) {
                // 已经分析，跳转到配置页
                router.navigate('/config');
            } else {
                UIHelper.showToast('会话状态异常', 'error');
            }
        } catch (error) {
            UIHelper.showLoading(false);

            // 会话已过期或不存在
            if (error.message.includes('not found') || error.message.includes('404')) {
                logger.warn('Session expired or not found:', sessionId);

                // 从localStorage删除过期会话
                SessionManager.deleteSession(sessionId);

                // 重新渲染会话列表
                this.renderUnfinishedSessions();

                UIHelper.showToast('会话已过期或已完成，已从列表中移除', 'warning');
            } else {
                UIHelper.showToast(`验证会话失败: ${error.message}`, 'error');
            }
        }
    }

    /**
     * 删除会话
     */
    deleteSession(sessionId) {
        if (!confirm('确定要删除这个会话吗？删除后无法恢复。')) {
            return;
        }

        logger.log('Deleting session:', sessionId);

        // 删除会话
        SessionManager.deleteSession(sessionId);

        UIHelper.showToast('会话已删除', 'success');

        // 重新渲染列表
        this.renderUnfinishedSessions();
    }

    /**
     * 获取会话阶段信息
     */
    getSessionStage(session) {
        if (session.executionResult) {
            return {
                label: '已完成',
                progress: 100,
                icon: '🎉'
            };
        } else if (session.taskData) {
            return {
                label: '执行中',
                progress: 60,
                icon: '⚡'
            };
        } else if (session.analysis) {
            return {
                label: '等待配置',
                progress: 20,
                icon: '⚙️'
            };
        } else {
            return {
                label: '分析中',
                progress: 10,
                icon: '🔍'
            };
        }
    }

    /**
     * 格式化时间（相对时间）
     */
    formatTimeAgo(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;
        const minutes = Math.floor(diff / 60000);

        if (minutes < 1) return '刚刚';
        if (minutes < 60) return `${minutes}分钟前`;

        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}小时前`;

        const days = Math.floor(hours / 24);
        return `${days}天前`;
    }
}

// 创建页面实例
const createPage = new CreatePage();