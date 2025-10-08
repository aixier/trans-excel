/**
 * 登录页面
 */
class LoginPage {
    constructor() {
        this.isLogging = false
    }

    render() {
        // 隐藏导航栏，登录页面全屏显示
        const navbar = document.querySelector('.navbar')
        if (navbar) navbar.style.display = 'none'

        const html = `
            <div class="fixed inset-0 flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
                <div class="max-w-md w-full mx-4">
                    <!-- 登录卡片 -->
                    <div class="bg-white rounded-2xl shadow-2xl p-8">
                        <!-- Logo和标题 -->
                        <div class="text-center mb-8">
                            <div class="mx-auto w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center mb-4">
                                <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                          d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"></path>
                                </svg>
                            </div>
                            <h1 class="text-3xl font-bold text-gray-900">游戏翻译系统</h1>
                            <p class="text-gray-600 mt-2">请登录以继续使用</p>
                        </div>

                        <!-- 登录表单 -->
                        <form id="loginForm" class="space-y-6">
                            <!-- 用户名 -->
                            <div>
                                <label for="username" class="block text-sm font-medium text-gray-700 mb-2">
                                    用户名
                                </label>
                                <input
                                    type="text"
                                    id="username"
                                    name="username"
                                    required
                                    autocomplete="username"
                                    class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                                    placeholder="请输入用户名"
                                />
                            </div>

                            <!-- 密码 -->
                            <div>
                                <label for="password" class="block text-sm font-medium text-gray-700 mb-2">
                                    密码
                                </label>
                                <input
                                    type="password"
                                    id="password"
                                    name="password"
                                    required
                                    autocomplete="current-password"
                                    class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                                    placeholder="请输入密码"
                                />
                            </div>

                            <!-- 错误提示 -->
                            <div id="loginError" class="hidden">
                                <div class="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
                                    <svg class="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                                    </svg>
                                    <span id="loginErrorText" class="text-sm text-red-800"></span>
                                </div>
                            </div>

                            <!-- 登录按钮 -->
                            <button
                                type="submit"
                                id="loginButton"
                                class="w-full bg-indigo-600 text-white font-semibold py-3 rounded-lg hover:bg-indigo-700 transition-colors shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <span id="loginButtonText">登录</span>
                            </button>
                        </form>

                        <!-- 演示账号提示 -->
                        <div class="mt-8 p-4 bg-gray-50 rounded-lg">
                            <p class="text-sm text-gray-600 text-center font-medium mb-2">演示账号</p>
                            <div class="space-y-1 text-xs text-gray-500">
                                <p>管理员：<code class="bg-white px-2 py-1 rounded">admin / admin123</code></p>
                                <p>普通用户：<code class="bg-white px-2 py-1 rounded">demo / demo123</code></p>
                            </div>
                        </div>
                    </div>

                    <!-- 底部信息 -->
                    <div class="text-center mt-6 text-sm text-gray-600">
                        <p>© 2025 游戏翻译系统 v2.0</p>
                    </div>
                </div>
            </div>
        `

        document.getElementById('pageContent').innerHTML = html

        // 绑定表单提交事件
        this.attachEventListeners()
    }

    attachEventListeners() {
        const form = document.getElementById('loginForm')
        form.addEventListener('submit', (e) => this.handleLogin(e))

        // 回车提交
        document.getElementById('password').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.isLogging) {
                form.dispatchEvent(new Event('submit'))
            }
        })
    }

    async handleLogin(event) {
        event.preventDefault()

        if (this.isLogging) return

        const username = document.getElementById('username').value.trim()
        const password = document.getElementById('password').value

        if (!username || !password) {
            this.showError('请输入用户名和密码')
            return
        }

        // 开始登录
        this.isLogging = true
        this.setLoading(true)
        this.hideError()

        try {
            const result = await authManager.login(username, password)

            if (result.success) {
                // 登录成功
                UIHelper.showToast('登录成功！', 'success')

                // 等待一下让用户看到成功提示
                await new Promise(resolve => setTimeout(resolve, 500))

                // 跳转到首页
                router.navigate('/create')
            } else {
                // 登录失败
                this.showError(result.error || '登录失败，请检查用户名和密码')
            }

        } catch (error) {
            console.error('[Login] Error:', error)
            this.showError('登录过程中发生错误，请稍后重试')
        } finally {
            this.isLogging = false
            this.setLoading(false)
        }
    }

    setLoading(loading) {
        const button = document.getElementById('loginButton')
        const buttonText = document.getElementById('loginButtonText')

        if (loading) {
            button.disabled = true
            buttonText.innerHTML = `
                <span class="inline-flex items-center">
                    <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    登录中...
                </span>
            `
        } else {
            button.disabled = false
            buttonText.textContent = '登录'
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('loginError')
        const errorText = document.getElementById('loginErrorText')

        errorText.textContent = message
        errorDiv.classList.remove('hidden')
    }

    hideError() {
        const errorDiv = document.getElementById('loginError')
        errorDiv.classList.add('hidden')
    }

    cleanup() {
        // 恢复导航栏显示
        const navbar = document.querySelector('.navbar')
        if (navbar) navbar.style.display = ''

        // 清理资源
        this.isLogging = false
    }
}

// 创建全局实例
const loginPage = new LoginPage()
