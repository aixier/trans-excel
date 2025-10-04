// LocalStorage工具类
class Storage {
    static setItem(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            logger.error('Storage setItem failed:', error);
            return false;
        }
    }

    static getItem(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            logger.error('Storage getItem failed:', error);
            return defaultValue;
        }
    }

    static removeItem(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            logger.error('Storage removeItem failed:', error);
            return false;
        }
    }

    static clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            logger.error('Storage clear failed:', error);
            return false;
        }
    }

    // 会话相关
    static saveSession(sessionData) {
        const now = Date.now();
        const session = {
            ...sessionData,
            createdAt: sessionData.createdAt || now,
            expiresAt: sessionData.expiresAt || (now + APP_CONFIG.SESSION_TIMEOUT),
            lastAccess: now
        };

        this.setItem('currentSession', session);

        // 添加到会话历史
        const history = this.getItem('sessionHistory', []);
        const existingIndex = history.findIndex(s => s.sessionId === session.sessionId);

        if (existingIndex >= 0) {
            history[existingIndex] = session;
        } else {
            history.unshift(session);
            // 只保留最近10个会话
            if (history.length > 10) {
                history.pop();
            }
        }

        this.setItem('sessionHistory', history);
        return session;
    }

    static getCurrentSession() {
        const session = this.getItem('currentSession');

        if (!session) {
            return null;
        }

        // 检查是否过期
        if (Date.now() > session.expiresAt) {
            this.removeItem('currentSession');
            return null;
        }

        return session;
    }

    static getSessionHistory() {
        const history = this.getItem('sessionHistory', []);
        const now = Date.now();

        // 过滤掉过期的会话
        return history.filter(session => {
            return (now - session.createdAt) < APP_CONFIG.SESSION_TIMEOUT;
        });
    }

    static clearSession(sessionId) {
        const currentSession = this.getCurrentSession();

        if (currentSession && currentSession.sessionId === sessionId) {
            this.removeItem('currentSession');
        }

        const history = this.getSessionHistory();
        const filtered = history.filter(s => s.sessionId !== sessionId);
        this.setItem('sessionHistory', filtered);
    }

    // 配置相关
    static saveTaskConfig(config) {
        this.setItem('lastTaskConfig', config);
    }

    static getLastTaskConfig() {
        return this.getItem('lastTaskConfig', APP_CONFIG.DEFAULT_CONFIG);
    }

    // 用户偏好
    static savePreferences(prefs) {
        this.setItem('userPreferences', prefs);
    }

    static getPreferences() {
        return this.getItem('userPreferences', {
            theme: 'light',
            lastGameName: '',
            lastVersion: ''
        });
    }

    // 缓存管理
    static setCacheItem(key, data, ttl = 3600000) { // 默认1小时
        const cacheData = {
            data,
            timestamp: Date.now(),
            expires: Date.now() + ttl
        };
        this.setItem(`cache_${key}`, cacheData);
    }

    static getCacheItem(key) {
        const cached = this.getItem(`cache_${key}`);

        if (!cached) {
            return null;
        }

        if (Date.now() > cached.expires) {
            this.removeItem(`cache_${key}`);
            return null;
        }

        return cached.data;
    }

    static clearCache() {
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.startsWith('cache_')) {
                localStorage.removeItem(key);
            }
        });
    }
}