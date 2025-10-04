// 应用主入口
class App {
    constructor() {
        this.init();
    }

    init() {
        logger.log('Initializing application...');

        // 初始化主题
        UIHelper.initTheme();

        // 检查未完成的会话
        this.checkAndRestoreSessions();

        // 初始化路由
        // 路由器会自动处理当前URL

        logger.log('Application initialized');
    }

    checkAndRestoreSessions() {
        const unfinished = SessionManager.checkUnfinishedSessions();

        if (unfinished && unfinished.length > 0) {
            logger.log('Found unfinished sessions:', unfinished);

            // 如果当前没有指定路由，显示恢复提示
            if (!window.location.hash || window.location.hash === '#/' || window.location.hash === '#/create') {
                // 将在create页面显示恢复提示
            }
        }
    }
}

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});