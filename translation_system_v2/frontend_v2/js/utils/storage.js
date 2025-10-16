// Storage工具类
// 会话数据使用sessionStorage（标签页关闭即清除）
// 用户偏好使用localStorage（永久保存）
class Storage {
    static setItem(key, value, permanent = false) {
        try {
            const storage = permanent ? localStorage : sessionStorage;
            storage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            logger.error('Storage setItem failed:', error);
            return false;
        }
    }

    static getItem(key, defaultValue = null, permanent = false) {
        try {
            const storage = permanent ? localStorage : sessionStorage;
            const item = storage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            logger.error('Storage getItem failed:', error);
            return defaultValue;
        }
    }

    static removeItem(key, permanent = false) {
        try {
            const storage = permanent ? localStorage : sessionStorage;
            storage.removeItem(key);
            return true;
        } catch (error) {
            logger.error('Storage removeItem failed:', error);
            return false;
        }
    }

    static clear(permanent = false) {
        try {
            const storage = permanent ? localStorage : sessionStorage;
            storage.clear();
            return true;
        } catch (error) {
            logger.error('Storage clear failed:', error);
            return false;
        }
    }

    // 会话相关 - 使用sessionStorage（标签页关闭即清除）
    static saveSession(sessionData) {
        const now = Date.now();
        const session = {
            ...sessionData,
            createdAt: sessionData.createdAt || now,
            expiresAt: sessionData.expiresAt || (now + APP_CONFIG.SESSION_TIMEOUT),
            lastAccess: now
        };

        // 只保存当前会话到sessionStorage，不保存历史
        this.setItem('currentSession', session, false);
        return session;
    }

    static getCurrentSession() {
        const session = this.getItem('currentSession', null, false);

        if (!session) {
            return null;
        }

        // 检查是否过期
        if (Date.now() > session.expiresAt) {
            this.removeItem('currentSession', false);
            return null;
        }

        return session;
    }

    static getSessionHistory() {
        // sessionStorage不保存历史，关闭标签页即清除
        // 返回空数组，不显示"未完成的会话"提示
        return [];
    }

    static clearSession(sessionId) {
        const currentSession = this.getCurrentSession();

        if (currentSession && currentSession.sessionId === sessionId) {
            this.removeItem('currentSession', false);
        }
    }

    // 配置相关 - 使用localStorage（永久保存）
    static saveTaskConfig(config) {
        this.setItem('lastTaskConfig', config, true);
    }

    static getLastTaskConfig() {
        return this.getItem('lastTaskConfig', APP_CONFIG.DEFAULT_CONFIG, true);
    }

    // 用户偏好 - 使用localStorage（永久保存）
    static savePreferences(prefs) {
        this.setItem('userPreferences', prefs, true);
    }

    static getPreferences() {
        return this.getItem('userPreferences', {
            theme: 'light',
            lastGameName: '',
            lastVersion: ''
        }, true);
    }

    // 缓存管理 - 使用localStorage（永久保存）
    static setCacheItem(key, data, ttl = 3600000) { // 默认1小时
        const cacheData = {
            data,
            timestamp: Date.now(),
            expires: Date.now() + ttl
        };
        this.setItem(`cache_${key}`, cacheData, true);
    }

    static getCacheItem(key) {
        const cached = this.getItem(`cache_${key}`, null, true);

        if (!cached) {
            return null;
        }

        if (Date.now() > cached.expires) {
            this.removeItem(`cache_${key}`, true);
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