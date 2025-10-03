import axios, { AxiosInstance, AxiosError } from 'axios'
import { message } from 'antd'

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if exists
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error: AxiosError) => {
    const errorMsg = error.response?.data?.message || error.message || '请求失败'
    
    // Handle specific error codes
    switch (error.response?.status) {
      case 401:
        message.error('未授权，请重新登录')
        // Redirect to login if needed
        break
      case 403:
        message.error('没有权限访问')
        break
      case 404:
        message.error('请求的资源不存在')
        break
      case 500:
        message.error('服务器错误')
        break
      default:
        message.error(errorMsg)
    }
    
    return Promise.reject(error)
  }
)

export default apiClient