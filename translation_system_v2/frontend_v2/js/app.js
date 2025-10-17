/**
 * StringLock - Main Application Entry Point
 *
 * This is the main application file that initializes all modules,
 * sets up routing, and manages the application lifecycle.
 *
 * @version 1.0.0
 * @author Engineers A, B, C, D
 */

console.log('[app.js] Loading app.js file...');

class TranslationHubApp {
    constructor() {
        this.router = null;
        this.api = null;
        this.wsManager = null;
        this.sessionManager = null;
        this.currentPage = null;
        this.config = {
            appName: 'StringLock',
            version: '2.0.0',
            apiBaseURL: 'http://localhost:8013',
            wsBaseURL: 'ws://localhost:8013'
        };
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            console.log(`%c${this.config.appName} v${this.config.version}`,
                'color: #4F46E5; font-size: 16px; font-weight: bold');
            console.log('Initializing application...');

            // 1. Initialize core services
            await this.initServices();

            // 2. Initialize session manager
            this.initSessionManager();

            // 3. Setup routes
            this.setupRoutes();

            // 4. Initialize router
            this.router.init();

            // 5. Setup global error handler
            this.setupErrorHandler();

            // 6. Setup theme
            this.initTheme();

            // 7. Application ready
            this.onReady();

            console.log('✅ Application initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize application:', error);
            this.showFatalError(error);
        }
    }

    /**
     * Initialize core services
     */
    async initServices() {
        // Global API instance (from Engineer A)
        if (typeof API !== 'undefined') {
            this.api = new API();
            window.api = this.api;
            console.log('✅ API service initialized:', window.api);
        } else {
            console.error('❌ API class not found! Check if js/services/api.js is loaded.');
            throw new Error('API class not defined');
        }

        // Global WebSocket Manager (from Engineer A)
        if (typeof WebSocketManager !== 'undefined') {
            this.wsManager = new WebSocketManager();
            window.wsManager = this.wsManager;
            console.log('✅ WebSocket manager initialized');
        } else {
            console.warn('⚠️ WebSocketManager not found');
        }

        // Global Router (from Engineer A)
        if (typeof Router !== 'undefined') {
            this.router = new Router();
            window.router = this.router;
            console.log('✅ Router initialized');
        } else {
            console.error('❌ Router class not found! Check if js/core/router.js is loaded.');
            throw new Error('Router class not defined');
        }
    }

    /**
     * Initialize session manager for state persistence
     */
    initSessionManager() {
        this.sessionManager = new SessionManager();
        window.sessionManager = this.sessionManager;
        console.log('✅ Session manager initialized');
    }

    /**
     * Setup application routes
     */
    setupRoutes() {
        // Upload page as default - redirect / to /upload
        this.router.register('/', () => this.loadPage('upload'));
        this.router.register('/dashboard', () => this.loadPage('dashboard'));

        // Sessions page - Engineer B
        this.router.register('/sessions', () => this.loadPage('sessions'));

        // Upload page - Engineer D
        this.router.register('/upload', () => this.loadPage('upload'));
        this.router.register('/create', () => this.loadPage('upload')); // Alias for "New Translation"

        // Task Config page - Engineer D
        this.router.register('/config', () => this.loadPage('config'));

        // Execution page - Engineer D
        this.router.register('/execution', () => this.loadPage('execution'));

        // Glossary page - Engineer C
        this.router.register('/glossary', () => this.loadPage('glossary'));

        // Analytics page - Engineer C
        this.router.register('/analytics', () => this.loadPage('analytics'));

        // Settings pages - Engineer D
        this.router.register('/settings/llm', () => this.loadPage('settings-llm'));
        this.router.register('/settings/rules', () => this.loadPage('settings-rules'));
        this.router.register('/settings/preferences', () => this.loadPage('settings-preferences'));

        console.log('✅ Routes registered:', Object.keys(this.router.routes).length);
    }

    /**
     * Load a specific page
     */
    async loadPage(pageName) {
        const container = document.getElementById('app');
        if (!container) {
            console.error('App container not found');
            return;
        }

        // Show loading state
        this.showLoading();

        try {
            // Cleanup previous page
            if (this.currentPage && typeof this.currentPage.destroy === 'function') {
                this.currentPage.destroy();
            }

            // Create new page instance
            let pageInstance = null;

            switch (pageName) {
                case 'dashboard':
                    if (typeof DashboardPage !== 'undefined') {
                        pageInstance = new DashboardPage();
                        await pageInstance.init();
                    }
                    break;

                case 'sessions':
                    if (typeof SessionsPage !== 'undefined') {
                        pageInstance = new SessionsPage();
                        await pageInstance.init();
                    }
                    break;

                case 'upload':
                    // 使用统一工作流页面 (UnifiedWorkflowPage) - 整合三个测试页面
                    if (typeof UnifiedWorkflowPage !== 'undefined') {
                        pageInstance = new UnifiedWorkflowPage();
                        await pageInstance.init();
                    } else if (typeof SimpleUploadPage !== 'undefined') {
                        // 降级到极简上传页面
                        pageInstance = new SimpleUploadPage();
                        await pageInstance.init();
                    } else if (typeof UploadPage !== 'undefined') {
                        // 降级到旧版上传页面
                        pageInstance = new UploadPage();
                        await pageInstance.init();
                    }
                    break;

                case 'config':
                    if (typeof TaskConfigPage !== 'undefined') {
                        // Get session_id from sessionStorage (set by dashboard or other pages)
                        const sessionId = sessionStorage.getItem('current_session_id');
                        pageInstance = new TaskConfigPage();
                        await pageInstance.init(sessionId);
                    }
                    break;

                case 'execution':
                    if (typeof ExecutionPage !== 'undefined') {
                        pageInstance = new ExecutionPage();
                        await pageInstance.init();
                    }
                    break;

                case 'glossary':
                    if (typeof GlossaryPage !== 'undefined') {
                        pageInstance = new GlossaryPage();
                        await pageInstance.init();
                    }
                    break;

                case 'analytics':
                    if (typeof AnalyticsPage !== 'undefined') {
                        pageInstance = new AnalyticsPage();
                        await pageInstance.init();
                    }
                    break;

                case 'settings-llm':
                    if (typeof LLMSettingsPage !== 'undefined') {
                        pageInstance = new LLMSettingsPage();
                        await pageInstance.init();
                    }
                    break;

                case 'settings-rules':
                    // Simple placeholder page
                    container.innerHTML = `
                        <div class="p-8">
                            <h2 class="text-2xl font-bold mb-4">规则配置</h2>
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle"></i>
                                <span>规则配置功能即将上线</span>
                            </div>
                        </div>
                    `;
                    break;

                case 'settings-preferences':
                    // Simple placeholder page
                    container.innerHTML = `
                        <div class="p-8">
                            <h2 class="text-2xl font-bold mb-4">用户偏好设置</h2>
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle"></i>
                                <span>用户偏好设置功能即将上线</span>
                            </div>
                        </div>
                    `;
                    break;

                default:
                    container.innerHTML = '<div class="p-8 text-center"><p class="text-lg text-error">页面未找到</p></div>';
            }

            this.currentPage = pageInstance;
            this.hideLoading();

        } catch (error) {
            console.error(`Failed to load page: ${pageName}`, error);
            this.showError(`加载页面失败: ${error.message}`);
            this.hideLoading();
        }
    }

    /**
     * Show loading indicator
     */
    showLoading() {
        const container = document.getElementById('app');
        if (container) {
            container.innerHTML = `
                <div class="flex items-center justify-center min-h-screen">
                    <div class="text-center">
                        <span class="loading loading-spinner loading-lg"></span>
                        <p class="mt-4 text-sm opacity-70">加载中...</p>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Hide loading indicator
     */
    hideLoading() {
        // Loading will be replaced by page content
    }

    /**
     * Show error message
     */
    showError(message) {
        const container = document.getElementById('app');
        if (container) {
            container.innerHTML = `
                <div class="flex items-center justify-center min-h-screen p-8">
                    <div class="alert alert-error max-w-md">
                        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>${message}</span>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Setup global error handler
     */
    setupErrorHandler() {
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
        });
    }

    /**
     * Initialize theme from localStorage
     */
    initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        console.log(`✅ Theme initialized: ${savedTheme}`);
    }

    /**
     * Called when application is ready
     */
    onReady() {
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('app:ready', {
            detail: { app: this }
        }));

        // Update nav active state
        this.updateNavActiveState();

        // Setup navigation click handlers
        this.setupNavigation();
    }

    /**
     * Update navigation active state
     */
    updateNavActiveState() {
        const currentPath = window.location.hash.slice(1) || '/';
        document.querySelectorAll('.nav-link').forEach(link => {
            const href = link.getAttribute('href');
            if (href === `#${currentPath}`) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    /**
     * Setup navigation click handlers
     */
    setupNavigation() {
        // Update active state on route change
        window.addEventListener('hashchange', () => {
            this.updateNavActiveState();
        });

        // Handle navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                // Let router handle the navigation
                this.updateNavActiveState();
            });
        });
    }

    /**
     * Show fatal error screen
     */
    showFatalError(error) {
        document.body.innerHTML = `
            <div class="flex items-center justify-center min-h-screen bg-base-200 p-8">
                <div class="card bg-base-100 shadow-xl max-w-lg">
                    <div class="card-body">
                        <h2 class="card-title text-error">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            应用初始化失败
                        </h2>
                        <p class="opacity-70">很抱歉，应用无法正常启动。</p>
                        <div class="bg-base-200 p-4 rounded mt-4">
                            <p class="text-sm font-mono">${error.message}</p>
                        </div>
                        <div class="card-actions justify-end mt-4">
                            <button class="btn btn-primary" onclick="location.reload()">
                                重新加载
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * SessionManager - Manages session data and state
 */
class SessionManager {
    constructor() {
        this.sessions = this.loadSessions();
    }

    /**
     * Load sessions from localStorage
     */
    loadSessions() {
        try {
            const data = localStorage.getItem('translation_sessions');
            return data ? JSON.parse(data) : [];
        } catch (error) {
            console.error('Failed to load sessions:', error);
            return [];
        }
    }

    /**
     * Save sessions to localStorage
     */
    saveSessions() {
        try {
            localStorage.setItem('translation_sessions', JSON.stringify(this.sessions));
        } catch (error) {
            console.error('Failed to save sessions:', error);
        }
    }

    /**
     * Get all sessions
     */
    getAllSessions() {
        return this.sessions;
    }

    /**
     * Get session by ID
     */
    getSession(sessionId) {
        return this.sessions.find(s => s.id === sessionId);
    }

    /**
     * Add or update session
     */
    saveSession(session) {
        const index = this.sessions.findIndex(s => s.id === session.id);
        if (index >= 0) {
            this.sessions[index] = { ...this.sessions[index], ...session };
        } else {
            this.sessions.push(session);
        }
        this.saveSessions();
    }

    /**
     * Delete session
     */
    deleteSession(sessionId) {
        this.sessions = this.sessions.filter(s => s.id !== sessionId);
        this.saveSessions();
    }

    /**
     * Get sessions by stage
     */
    getSessionsByStage(stage) {
        return this.sessions.filter(s => s.stage === stage);
    }

    /**
     * Clear all sessions
     */
    clearAllSessions() {
        this.sessions = [];
        this.saveSessions();
    }

    /**
     * Export sessions as JSON
     */
    exportSessions() {
        return JSON.stringify(this.sessions, null, 2);
    }

    /**
     * Import sessions from JSON
     */
    importSessions(jsonData) {
        try {
            const imported = JSON.parse(jsonData);
            if (Array.isArray(imported)) {
                this.sessions = imported;
                this.saveSessions();
                return true;
            }
        } catch (error) {
            console.error('Failed to import sessions:', error);
        }
        return false;
    }
}

/**
 * Ensure API is ready before using it
 */
window.ensureAPIReady = function() {
    return new Promise((resolve, reject) => {
        if (window.api) {
            resolve(window.api);
            return;
        }

        // Wait for app:ready event
        const timeout = setTimeout(() => {
            reject(new Error('API初始化超时，请刷新页面重试'));
        }, 5000);

        window.addEventListener('app:ready', () => {
            clearTimeout(timeout);
            if (window.api) {
                resolve(window.api);
            } else {
                reject(new Error('API初始化失败'));
            }
        }, { once: true });
    });
};
console.log('[app.js] ✅ window.ensureAPIReady defined:', typeof window.ensureAPIReady);

/**
 * Global toast notification function
 */
window.showToast = function(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} fixed top-4 right-4 w-96 shadow-lg z-50`;
    toast.innerHTML = `
        <span>${message}</span>
        <button class="btn btn-sm btn-ghost" onclick="this.parentElement.remove()">
            ✕
        </button>
    `;
    document.body.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
};

/**
 * Initialize application when DOM is ready
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new TranslationHubApp();
        window.app.init();
    });
} else {
    window.app = new TranslationHubApp();
    window.app.init();
}
