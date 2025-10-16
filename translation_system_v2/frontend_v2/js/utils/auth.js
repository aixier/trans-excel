/**
 * 认证工具 - Token管理
 */

const AUTH_CONFIG = {
    TOKEN_KEY: 'translation_auth_token',
    USER_KEY: 'translation_auth_user',
    TOKEN_EXPIRE_TIME: 24 * 60 * 60 * 1000 // 24小时
}

class AuthManager {
    constructor() {
        this.token = this.getToken()
        this.user = this.getUser()
    }

    /**
     * 保存token
     */
    setToken(token) {
        if (!token) return false

        try {
            localStorage.setItem(AUTH_CONFIG.TOKEN_KEY, token)
            localStorage.setItem(`${AUTH_CONFIG.TOKEN_KEY}_time`, Date.now().toString())
            this.token = token
            return true
        } catch (error) {
            console.error('[Auth] Failed to save token:', error)
            return false
        }
    }

    /**
     * 获取token
     */
    getToken() {
        try {
            const token = localStorage.getItem(AUTH_CONFIG.TOKEN_KEY)
            const tokenTime = localStorage.getItem(`${AUTH_CONFIG.TOKEN_KEY}_time`)

            // 检查token是否过期
            if (token && tokenTime) {
                const elapsed = Date.now() - parseInt(tokenTime)
                if (elapsed > AUTH_CONFIG.TOKEN_EXPIRE_TIME) {
                    console.log('[Auth] Token expired, clearing...')
                    this.clearToken()
                    return null
                }
            }

            return token
        } catch (error) {
            console.error('[Auth] Failed to get token:', error)
            return null
        }
    }

    /**
     * 清除token
     */
    clearToken() {
        try {
            localStorage.removeItem(AUTH_CONFIG.TOKEN_KEY)
            localStorage.removeItem(`${AUTH_CONFIG.TOKEN_KEY}_time`)
            this.token = null
            return true
        } catch (error) {
            console.error('[Auth] Failed to clear token:', error)
            return false
        }
    }

    /**
     * 保存用户信息
     */
    setUser(user) {
        if (!user) return false

        try {
            localStorage.setItem(AUTH_CONFIG.USER_KEY, JSON.stringify(user))
            this.user = user
            return true
        } catch (error) {
            console.error('[Auth] Failed to save user:', error)
            return false
        }
    }

    /**
     * 获取用户信息
     */
    getUser() {
        try {
            const userStr = localStorage.getItem(AUTH_CONFIG.USER_KEY)
            if (!userStr) return null

            return JSON.parse(userStr)
        } catch (error) {
            console.error('[Auth] Failed to get user:', error)
            return null
        }
    }

    /**
     * 清除用户信息
     */
    clearUser() {
        try {
            localStorage.removeItem(AUTH_CONFIG.USER_KEY)
            this.user = null
            return true
        } catch (error) {
            console.error('[Auth] Failed to clear user:', error)
            return false
        }
    }

    /**
     * 登录
     */
    async login(username, password) {
        try {
            const response = await fetch(`${window.location.origin}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            })

            const data = await response.json()

            if (!response.ok || !data.success) {
                throw new Error(data.message || '登录失败')
            }

            // 保存token和用户信息
            this.setToken(data.data.token)
            this.setUser(data.data.user)

            console.log('[Auth] Login successful:', data.data.user.username)
            return {
                success: true,
                user: data.data.user,
                token: data.data.token
            }

        } catch (error) {
            console.error('[Auth] Login error:', error)
            return {
                success: false,
                error: error.message
            }
        }
    }

    /**
     * 验证token
     */
    async verifyToken() {
        const token = this.getToken()
        if (!token) {
            return { valid: false, error: '未登录' }
        }

        try {
            const response = await fetch(`${window.location.origin}/api/auth/verify`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })

            const data = await response.json()

            if (!response.ok || !data.success) {
                this.clearToken()
                this.clearUser()
                return { valid: false, error: data.message || 'Token无效' }
            }

            // 更新用户信息
            this.setUser(data.data.user)

            return {
                valid: true,
                user: data.data.user
            }

        } catch (error) {
            console.error('[Auth] Verify token error:', error)
            this.clearToken()
            this.clearUser()
            return { valid: false, error: error.message }
        }
    }

    /**
     * 登出
     */
    async logout() {
        const token = this.getToken()

        if (token) {
            try {
                // 调用后端登出API
                await fetch(`${window.location.origin}/api/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                })
            } catch (error) {
                console.error('[Auth] Logout API error:', error)
            }
        }

        // 清除本地数据
        this.clearToken()
        this.clearUser()

        console.log('[Auth] Logged out')
        return { success: true }
    }

    /**
     * 检查是否已登录
     */
    isAuthenticated() {
        return !!this.getToken()
    }

    /**
     * 获取Authorization header
     */
    getAuthHeader() {
        const token = this.getToken()
        return token ? { 'Authorization': `Bearer ${token}` } : {}
    }
}

// 导出单例
const authManager = new AuthManager()
