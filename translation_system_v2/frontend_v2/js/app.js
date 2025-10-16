// 应用主入口
class App {
    constructor() {
        this.init();
    }

    init() {
        logger.log('Initializing application...');

        // 初始化主题
        UIHelper.initTheme();

        // 初始化用户信息显示
        this.initUserInfo();

        // 检查未完成的会话
        this.checkAndRestoreSessions();

        // 初始化路由
        // 路由器会自动处理当前URL

        logger.log('Application initialized');
    }

    /**
     * 初始化用户信息显示
     */
    initUserInfo() {
        const userInfoDiv = document.getElementById('userInfo')
        const userAvatar = document.getElementById('userAvatar')
        const userDisplayName = document.getElementById('userDisplayName')
        const logoutBtn = document.getElementById('logoutBtn')

        // 如果已登录，显示用户信息
        if (authManager.isAuthenticated()) {
            const user = authManager.getUser()
            if (user) {
                // 显示用户信息
                userInfoDiv.classList.remove('hidden')

                // 设置头像（用户名首字母）
                userAvatar.textContent = user.displayName ? user.displayName[0].toUpperCase() : user.username[0].toUpperCase()

                // 设置显示名称
                userDisplayName.textContent = user.displayName || user.username

                logger.log('User info displayed:', user.username)
            }
        } else {
            // 未登录，隐藏用户信息
            userInfoDiv.classList.add('hidden')
        }

        // 绑定登出按钮
        logoutBtn.addEventListener('click', async () => {
            if (confirm('确定要登出吗？')) {
                await this.handleLogout()
            }
        })
    }

    /**
     * 处理登出
     */
    async handleLogout() {
        try {
            await authManager.logout()

            // 清除会话数据
            sessionManager.clearSession()

            UIHelper.showToast('已登出', 'info')

            // 跳转到登录页
            window.location.hash = '#/login'

            // 重新加载页面以清除状态
            setTimeout(() => {
                window.location.reload()
            }, 500)

        } catch (error) {
            console.error('[App] Logout error:', error)
            UIHelper.showToast('登出失败', 'error')
        }
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