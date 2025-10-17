/**
 * Hash Router - 基于Hash的单页应用路由系统
 *
 * @class Router
 * @description
 * 实现Hash路由，支持页面切换动画、404处理、路由守卫
 *
 * @example
 * const router = new Router();
 * router.register('/', homePage);
 * router.register('/about', aboutPage);
 * router.init();
 * router.navigate('/about');
 */
class Router {
  /**
   * 创建Router实例
   */
  constructor() {
    /** @type {Object<string, Function>} 路由映射表 */
    this.routes = {};

    /** @type {string|null} 当前路由路径 */
    this.currentRoute = null;

    /** @type {string} 页面容器ID */
    this.containerId = 'app';

    /** @type {Function|null} 路由守卫函数 */
    this.beforeEach = null;

    /** @type {boolean} 是否启用页面切换动画 */
    this.enableAnimation = true;

    /** @type {number} 动画持续时间(ms) */
    this.animationDuration = 300;
  }

  /**
   * 注册路由
   *
   * @param {string} path - 路由路径（如 '/' 或 '/about'）
   * @param {Function} handler - 路由处理函数，返回HTML字符串或渲染函数
   *
   * @example
   * router.register('/dashboard', () => {
   *   return '<div>Dashboard Page</div>';
   * });
   */
  register(path, handler) {
    this.routes[path] = handler;
  }

  /**
   * 设置路由守卫
   *
   * @param {Function} guard - 守卫函数，接收 (to, from, next) 参数
   *
   * @example
   * router.setGuard((to, from, next) => {
   *   if (to === '/admin' && !isAdmin()) {
   *     next('/login');
   *   } else {
   *     next();
   *   }
   * });
   */
  setGuard(guard) {
    this.beforeEach = guard;
  }

  /**
   * 初始化路由系统
   * 监听hash变化，加载初始页面
   */
  init() {
    // 监听hash变化
    window.addEventListener('hashchange', () => {
      this.loadRoute();
    });

    // 监听浏览器前进/后退
    window.addEventListener('popstate', () => {
      this.loadRoute();
    });

    // 加载初始路由
    this.loadRoute();
  }

  /**
   * 导航到指定路径
   *
   * @param {string} path - 目标路径
   * @param {boolean} replace - 是否替换历史记录（默认false）
   *
   * @example
   * router.navigate('/dashboard');
   * router.navigate('/login', true); // 替换当前历史记录
   */
  navigate(path, replace = false) {
    if (replace) {
      window.location.replace(`#${path}`);
    } else {
      window.location.hash = path;
    }
  }

  /**
   * 加载当前路由对应的页面
   * @private
   */
  async loadRoute() {
    const hash = window.location.hash.slice(1) || '/';
    const path = hash.split('?')[0]; // 去除查询参数

    // 如果路由未改变，不重复加载
    if (path === this.currentRoute) {
      return;
    }

    // 执行路由守卫
    if (this.beforeEach) {
      let allowed = true;
      let redirectPath = null;

      const next = (path) => {
        if (path) {
          redirectPath = path;
          allowed = false;
        }
      };

      this.beforeEach(path, this.currentRoute, next);

      if (!allowed && redirectPath) {
        this.navigate(redirectPath);
        return;
      }
    }

    // 查找路由处理函数
    const handler = this.routes[path] || this.routes['/404'];

    if (!handler) {
      console.error(`Route not found: ${path}`);
      this.render404();
      return;
    }

    // 获取页面容器
    const container = document.getElementById(this.containerId);
    if (!container) {
      console.error(`Container #${this.containerId} not found`);
      return;
    }

    // 执行页面切换动画
    if (this.enableAnimation) {
      await this.exitAnimation(container);
    }

    // 执行路由处理函数
    try {
      const content = await handler();

      // 渲染新页面
      if (typeof content === 'string') {
        container.innerHTML = content;
      } else if (content instanceof HTMLElement) {
        container.innerHTML = '';
        container.appendChild(content);
      }

      // 更新当前路由
      this.currentRoute = path;

      // 执行进入动画
      if (this.enableAnimation) {
        await this.enterAnimation(container);
      }

      // 触发路由变化事件
      this.triggerRouteChange(path);
    } catch (error) {
      console.error('Route handler error:', error);
      this.renderError(error);
    }
  }

  /**
   * 页面退出动画
   * @private
   */
  exitAnimation(container) {
    return new Promise((resolve) => {
      container.style.opacity = '1';
      container.style.transform = 'translateY(0)';
      container.style.transition = `all ${this.animationDuration}ms ease-in`;

      // 触发动画
      requestAnimationFrame(() => {
        container.style.opacity = '0';
        container.style.transform = 'translateY(-20px)';
      });

      setTimeout(resolve, this.animationDuration);
    });
  }

  /**
   * 页面进入动画
   * @private
   */
  enterAnimation(container) {
    return new Promise((resolve) => {
      container.style.opacity = '0';
      container.style.transform = 'translateY(20px)';
      container.style.transition = `all ${this.animationDuration}ms ease-out`;

      // 触发动画
      requestAnimationFrame(() => {
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
      });

      setTimeout(resolve, this.animationDuration);
    });
  }

  /**
   * 渲染404页面
   * @private
   */
  render404() {
    const container = document.getElementById(this.containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center min-h-screen">
        <i class="bi bi-exclamation-triangle text-6xl text-warning mb-4"></i>
        <h1 class="text-4xl font-bold mb-2">404</h1>
        <p class="text-lg text-base-content/60 mb-6">页面未找到</p>
        <button class="btn btn-primary" onclick="router.navigate('/')">
          <i class="bi bi-house"></i>
          返回首页
        </button>
      </div>
    `;
  }

  /**
   * 渲染错误页面
   * @private
   */
  renderError(error) {
    const container = document.getElementById(this.containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center min-h-screen">
        <i class="bi bi-x-circle text-6xl text-error mb-4"></i>
        <h1 class="text-4xl font-bold mb-2">页面加载失败</h1>
        <p class="text-lg text-base-content/60 mb-2">${error.message}</p>
        <p class="text-sm text-base-content/40 mb-6">请刷新页面重试</p>
        <button class="btn btn-primary" onclick="location.reload()">
          <i class="bi bi-arrow-clockwise"></i>
          刷新页面
        </button>
      </div>
    `;
  }

  /**
   * 触发路由变化事件
   * @private
   */
  triggerRouteChange(path) {
    const event = new CustomEvent('routechange', {
      detail: {
        path: path,
        params: this.getQueryParams()
      }
    });
    window.dispatchEvent(event);
  }

  /**
   * 获取当前路由路径
   *
   * @returns {string} 当前路由路径
   */
  getCurrentPath() {
    return this.currentRoute || '/';
  }

  /**
   * 获取查询参数
   *
   * @returns {Object} 查询参数对象
   *
   * @example
   * // URL: #/dashboard?id=123&tab=settings
   * router.getQueryParams(); // { id: '123', tab: 'settings' }
   */
  getQueryParams() {
    const hash = window.location.hash.slice(1);
    const queryString = hash.split('?')[1];

    if (!queryString) {
      return {};
    }

    const params = {};
    queryString.split('&').forEach(param => {
      const [key, value] = param.split('=');
      params[decodeURIComponent(key)] = decodeURIComponent(value || '');
    });

    return params;
  }

  /**
   * 设置页面容器ID
   *
   * @param {string} id - 容器元素ID
   */
  setContainer(id) {
    this.containerId = id;
  }

  /**
   * 启用/禁用页面切换动画
   *
   * @param {boolean} enabled - 是否启用
   */
  setAnimation(enabled) {
    this.enableAnimation = enabled;
  }

  /**
   * 返回上一页
   */
  back() {
    window.history.back();
  }

  /**
   * 前进到下一页
   */
  forward() {
    window.history.forward();
  }
}

// 导出全局实例
const router = new Router();

// ES6 模块导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Router;
  module.exports.router = router;
}
