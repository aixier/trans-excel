// API工具类
class API {
    static async request(url, options = {}) {
        // 检查是否是FormData，如果是则不设置Content-Type
        const isFormData = options.body instanceof FormData;

        const defaultOptions = {
            headers: isFormData ? {} : {
                'Content-Type': 'application/json'
            }
        };

        const config = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...(options.headers || {})
            }
        };

        // 🔧 添加认证token（如果存在）
        // 跳过登录和验证API（避免循环依赖）
        if (typeof authManager !== 'undefined' && !url.includes('/api/auth/login') && !url.includes('/api/auth/verify')) {
            const token = authManager.getToken();
            if (token) {
                config.headers['Authorization'] = `Bearer ${token}`;
            }
        }

        // 如果headers为空对象且是FormData，完全移除headers让浏览器自动设置
        if (isFormData && Object.keys(config.headers).length === 0) {
            delete config.headers;
        }

        try {
            const response = await fetch(`${APP_CONFIG.API_BASE_URL}${url}`, config);

            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}`;
                try {
                    const error = await response.json();
                    if (error.detail) {
                        // 处理FastAPI的验证错误
                        if (Array.isArray(error.detail)) {
                            errorMessage = error.detail.map(e => e.msg).join(', ');
                        } else {
                            errorMessage = error.detail;
                        }
                    }
                } catch (e) {
                    // 如果不能解析为JSON，使用默认错误消息
                }
                throw new Error(errorMessage);
            }

            // 如果是下载文件，返回blob
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/vnd.openxmlformats')) {
                return await response.blob();
            }

            return await response.json();
        } catch (error) {
            logger.error('API request failed:', error);
            throw error;
        }
    }

    // 分析相关API
    static async uploadFile(file, gameInfo = null) {
        const formData = new FormData();
        formData.append('file', file);

        if (gameInfo) {
            formData.append('game_info', JSON.stringify(gameInfo));
        }

        return this.request('/api/analyze/upload', {
            method: 'POST',
            body: formData
            // 不设置headers，让request方法自动处理
        });
    }

    static async getAnalysisStatus(sessionId) {
        return this.request(`/api/analyze/status/${sessionId}`);
    }

    // 任务相关API
    static async splitTasks(sessionId, config) {
        return this.request('/api/tasks/split', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                source_lang: config.source_lang,
                target_langs: config.target_langs,
                extract_context: config.extract_context,
                context_options: config.extract_context ? config.context_options : null
            })
        });
    }

    static async getSplitStatus(sessionId) {
        return this.request(`/api/tasks/split/status/${sessionId}`);
    }

    static async getTaskStatus(sessionId) {
        return this.request(`/api/tasks/status/${sessionId}`);
    }

    static async exportTasks(sessionId) {
        return this.request(`/api/tasks/export/${sessionId}`, {
            headers: {
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        });
    }

    // 执行相关API
    static async startExecution(sessionId, options = {}) {
        return this.request('/api/execute/start', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                provider: options.provider,
                max_workers: options.max_workers
            })
        });
    }

    static async stopExecution(sessionId) {
        return this.request(`/api/execute/stop/${sessionId}`, {
            method: 'POST'
        });
    }

    static async pauseExecution(sessionId) {
        return this.request(`/api/execute/pause/${sessionId}`, {
            method: 'POST'
        });
    }

    static async resumeExecution(sessionId) {
        return this.request(`/api/execute/resume/${sessionId}`, {
            method: 'POST'
        });
    }

    // 监控相关API
    static async getExecutionProgress(sessionId) {
        return this.request(`/api/monitor/status/${sessionId}`);
    }

    static async getCompletionSummary(sessionId) {
        return this.request(`/api/monitor/summary/${sessionId}`);
    }

    // 下载相关API
    static async downloadResult(sessionId) {
        return this.request(`/api/download/${sessionId}`, {
            headers: {
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        });
    }

    static async getDownloadInfo(sessionId) {
        return this.request(`/api/download/${sessionId}/info`);
    }

    static async getExportStatus(sessionId) {
        return this.request(`/api/download/status/${sessionId}`);
    }
}