// 路由器
class Router {
    constructor() {
        this.routes = {
            '/': 'create',
            '/login': 'login',
            '/create': 'create',
            '/config': 'config',
            '/execute': 'execute',
            '/complete': 'complete'
        };

        // 公开路由（不需要登录）
        this.publicRoutes = ['/login'];

        this.currentPage = null;
        this.init();
    }

    init() {
        // 监听hash变化
        window.addEventListener('hashchange', () => this.handleRoute());
        window.addEventListener('load', () => this.handleRoute());
    }

    handleRoute() {
        const hash = window.location.hash.slice(1) || '/';
        const [path, params] = hash.split('?');
        const routePath = path.split('/').slice(0, 2).join('/'); // 获取基础路径

        logger.log('Routing to:', routePath, 'Params:', params);

        // 🔧 认证检查
        const isPublicRoute = this.publicRoutes.includes(routePath);
        const isAuthenticated = typeof authManager !== 'undefined' && authManager.isAuthenticated();

        // 如果不是公开路由且未登录，重定向到登录页
        if (!isPublicRoute && !isAuthenticated) {
            logger.warn('Not authenticated, redirecting to login');
            if (routePath !== '/login') {
                window.location.hash = '#/login';
                return;
            }
        }

        // 如果已登录且访问登录页，重定向到首页
        if (isAuthenticated && routePath === '/login') {
            logger.log('Already authenticated, redirecting to home');
            window.location.hash = '#/create';
            return;
        }

        // 获取页面名称
        let pageName = this.routes[routePath];

        // 处理带参数的路由（如 /execute/:sessionId）
        if (!pageName) {
            const segments = routePath.split('/');
            if (segments[1] === 'execute' || segments[1] === 'complete') {
                pageName = segments[1];
            }
        }

        if (pageName) {
            this.loadPage(pageName, this.parseParams(path, params));
        } else {
            this.loadPage('create');
        }
    }

    parseParams(path, queryString) {
        const params = {};

        // 解析路径参数（如 /execute/xxx-xxx-xxx）
        const segments = path.split('/');
        if (segments.length > 2) {
            params.sessionId = segments[2];
        }

        // 解析查询参数
        if (queryString) {
            const urlParams = new URLSearchParams(queryString);
            for (const [key, value] of urlParams) {
                params[key] = value;
            }
        }

        return params;
    }

    loadPage(pageName, params = {}) {
        logger.log('Loading page:', pageName, 'with params:', params);

        // 页面切换动画
        const content = document.getElementById('pageContent');
        content.style.opacity = '0';

        setTimeout(() => {
            try {
                // 清理之前的页面
                if (this.currentPage && this.currentPage.cleanup) {
                    this.currentPage.cleanup();
                }

                // 加载新页面
                switch (pageName) {
                    case 'login':
                        this.currentPage = loginPage;
                        loginPage.render();
                        break;

                    case 'create':
                        this.currentPage = createPage;
                        createPage.render();
                        break;

                    case 'config':
                        // 检查会话
                        if (!this.checkSession()) {
                            this.navigate('/create');
                            return;
                        }
                        this.currentPage = configPage;
                        configPage.render();
                        break;

                    case 'execute':
                        // 检查会话和参数
                        if (!params.sessionId || !this.checkSession(params.sessionId)) {
                            this.navigate('/create');
                            return;
                        }
                        this.currentPage = executePage;
                        executePage.render(params.sessionId);
                        break;

                    case 'complete':
                        // 检查会话和参数
                        if (!params.sessionId || !this.checkSession(params.sessionId)) {
                            this.navigate('/create');
                            return;
                        }
                        this.currentPage = completePage;
                        completePage.render(params.sessionId);
                        break;

                    default:
                        this.navigate('/create');
                }

                content.style.opacity = '1';

            } catch (error) {
                logger.error('Failed to load page:', error);
                UIHelper.showToast('页面加载失败', 'error');
                this.navigate('/create');
            }
        }, 300);
    }

    checkSession(sessionId = null) {
        if (sessionId) {
            // 尝试加载指定会话
            return sessionManager.loadSession(sessionId);
        } else {
            // 检查当前会话
            const session = sessionManager.session || Storage.getCurrentSession();
            if (session) {
                if (!sessionManager.session) {
                    sessionManager.loadSession(session.sessionId);
                }
                return true;
            }
            return false;
        }
    }

    navigate(path) {
        window.location.hash = path;
    }

    // 获取当前路由信息
    getCurrentRoute() {
        const hash = window.location.hash.slice(1) || '/';
        const [path, params] = hash.split('?');
        return {
            path,
            params: this.parseParams(path, params),
            pageName: this.routes[path.split('/').slice(0, 2).join('/')] || null
        };
    }

    // 返回上一页
    back() {
        window.history.back();
    }

    // 前进
    forward() {
        window.history.forward();
    }
}

// 创建全局路由器实例
const router = new Router();