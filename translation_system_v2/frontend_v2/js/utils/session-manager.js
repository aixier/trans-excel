// 会话生命周期管理器
class SessionManager {
    constructor() {
        this.session = null;
        this.expiryTimer = null;
        this.warningShown = false;
    }

    // 创建新会话
    createSession(sessionId, filename, analysis) {
        const now = Date.now();
        this.session = {
            sessionId,
            filename,
            analysis,
            createdAt: now,
            expiresAt: now + APP_CONFIG.SESSION_TIMEOUT,
            stage: 'created'
        };

        Storage.saveSession(this.session);
        this.startMonitoring();

        logger.log('Session created:', this.session);
        return this.session;
    }

    // 加载现有会话
    loadSession(sessionId) {
        const session = Storage.getCurrentSession();

        if (session && session.sessionId === sessionId) {
            this.session = session;
            this.startMonitoring();
            return true;
        }

        // 从历史中查找
        const history = Storage.getSessionHistory();
        const found = history.find(s => s.sessionId === sessionId);

        if (found) {
            this.session = found;
            Storage.saveSession(found);
            this.startMonitoring();
            return true;
        }

        return false;
    }

    // 开始监控会话超时
    startMonitoring() {
        if (this.expiryTimer) {
            clearInterval(this.expiryTimer);
        }

        this.expiryTimer = setInterval(() => {
            this.checkExpiry();
        }, 60000); // 每分钟检查

        // 立即检查一次
        this.checkExpiry();
    }

    // 检查会话过期
    checkExpiry() {
        if (!this.session) return;

        const remaining = this.session.expiresAt - Date.now();

        if (remaining <= 0) {
            this.handleExpired();
        } else if (remaining <= APP_CONFIG.SESSION_WARNING_TIME && !this.warningShown) {
            this.showExpiryWarning(remaining);
            this.warningShown = true;
        }

        this.updateTimerDisplay(remaining);
    }

    // 更新计时器显示
    updateTimerDisplay(remaining) {
        const timerElement = document.getElementById('sessionTimer');
        const timerText = document.getElementById('sessionTimerText');
        const timerBadge = document.getElementById('sessionTimerBadge');

        if (!timerElement) return;

        if (remaining > 0) {
            timerElement.classList.remove('hidden');

            const hours = Math.floor(remaining / 3600000);
            const minutes = Math.floor((remaining % 3600000) / 60000);

            timerText.textContent = `${hours}:${minutes.toString().padStart(2, '0')}`;

            // 根据剩余时间改变样式
            if (remaining < APP_CONFIG.SESSION_WARNING_TIME) {
                timerBadge.className = 'badge badge-warning badge-lg session-warning';
            } else {
                timerBadge.className = 'badge badge-lg';
            }
        } else {
            timerElement.classList.add('hidden');
        }
    }

    // 显示过期警告
    showExpiryWarning(remaining) {
        const minutes = Math.floor(remaining / 60000);

        UIHelper.showDialog({
            type: 'warning',
            title: '会话即将过期',
            message: `您的翻译会话将在 ${minutes} 分钟后过期，请尽快完成操作`,
            actions: [
                {
                    label: '知道了',
                    className: 'btn-warning',
                    action: () => {}
                }
            ]
        });

        // 如果在完成页，特别强调
        if (window.location.hash.includes('complete')) {
            document.body.classList.add('urgent-warning');
            const downloadBtn = document.getElementById('downloadBtn');
            if (downloadBtn) {
                downloadBtn.classList.add('pulse-animation');
            }
        }
    }

    // 处理会话过期
    handleExpired() {
        clearInterval(this.expiryTimer);

        UIHelper.showDialog({
            type: 'error',
            title: '会话已过期',
            message: '您的翻译数据已被清除，请重新上传文件',
            blocking: true,
            actions: [
                {
                    label: '重新开始',
                    className: 'btn-primary',
                    action: () => {
                        Storage.clearSession(this.session.sessionId);
                        window.location.hash = '#/create';
                    }
                }
            ]
        });
    }

    // 更新会话阶段
    updateStage(stage) {
        if (this.session) {
            this.session.stage = stage;
            this.session.lastAccess = Date.now();
            Storage.saveSession(this.session);
        }
    }

    // 获取剩余时间
    getRemainingTime() {
        if (!this.session) return 0;
        return Math.max(0, this.session.expiresAt - Date.now());
    }

    // 清除会话
    clearSession() {
        if (this.expiryTimer) {
            clearInterval(this.expiryTimer);
        }
        if (this.session) {
            Storage.clearSession(this.session.sessionId);
        }
        this.session = null;
        this.warningShown = false;
    }

    // 检查未完成的会话
    static checkUnfinishedSessions() {
        const history = Storage.getSessionHistory();
        const unfinished = history.filter(s => s.stage !== 'completed');

        if (unfinished.length > 0) {
            return unfinished;
        }

        return null;
    }

    // 删除指定会话
    static deleteSession(sessionId) {
        if (!sessionId) return false;

        // 从 localStorage 中删除会话数据
        Storage.clearSession(sessionId);

        logger.log('Session deleted:', sessionId);
        return true;
    }
}

// 全局会话管理器实例
const sessionManager = new SessionManager();