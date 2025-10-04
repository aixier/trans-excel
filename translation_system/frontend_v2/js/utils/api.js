// API工具类
class API {
    static async request(url, options = {}) {
        const defaultOptions = {
            headers: {
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

        try {
            const response = await fetch(`${APP_CONFIG.API_BASE_URL}${url}`, config);

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
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
            headers: {}, // FormData不需要Content-Type
            body: formData
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

    static async getGlobalExecutionStatus() {
        try {
            return await this.request('/api/execute/status');
        } catch (error) {
            // 如果API不存在，返回默认值
            return { is_executing: false };
        }
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

    static async getExportStatus(sessionId) {
        return this.request(`/api/download/status/${sessionId}`);
    }
}