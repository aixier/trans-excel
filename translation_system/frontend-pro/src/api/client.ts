import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'ant-design-vue'
import router from '@/router'

// API响应格式
export interface ApiResponse<T = any> {
  code: number
  data: T
  message: string
  timestamp: number
}

// 错误响应格式
export interface ApiError {
  code: number
  message: string
  details?: any
}

class ApiClient {
  private instance: AxiosInstance
  private refreshing: boolean = false
  private refreshQueue: Array<() => void> = []

  constructor() {
    this.instance = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
      timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        // 添加认证token
        const token = localStorage.getItem('access_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // 添加请求ID用于追踪
        config.headers['X-Request-Id'] = this.generateRequestId()

        // 添加时间戳防止缓存
        if (config.method === 'get') {
          config.params = {
            ...config.params,
            _t: Date.now()
          }
        }

        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        const { data } = response

        // 处理下载文件的情况
        if (response.config.responseType === 'blob') {
          return response
        }

        // 统一成功响应格式
        if (data.code === 200 || data.code === 0) {
          return data.data
        }

        // 业务错误
        this.handleBusinessError(data)
        return Promise.reject(new Error(data.message))
      },
      async (error) => {
        // 处理HTTP错误
        return this.handleHttpError(error)
      }
    )
  }

  private handleBusinessError(response: ApiResponse) {
    switch (response.code) {
      case 4001: // 未认证
        this.handleUnauthorized()
        break
      case 4003: // 无权限
        message.error('您没有权限执行此操作')
        break
      default:
        message.error(response.message || '操作失败')
    }
  }

  private async handleHttpError(error: any) {
    const { response } = error

    if (!response) {
      // 网络错误
      message.error('网络连接失败，请检查您的网络')
      return Promise.reject(error)
    }

    switch (response.status) {
      case 401:
        await this.handleUnauthorized()
        break
      case 403:
        message.error('访问被拒绝')
        router.push('/403')
        break
      case 404:
        message.error('请求的资源不存在')
        break
      case 429:
        message.error('请求过于频繁，请稍后重试')
        break
      case 500:
      case 502:
      case 503:
        message.error('服务器错误，请稍后重试')
        break
      default:
        message.error(`请求失败: ${response.status}`)
    }

    return Promise.reject(error)
  }

  private async handleUnauthorized() {
    // 清除token
    localStorage.removeItem('access_token')

    // 跳转到登录页
    message.warning('登录已过期，请重新登录')
    router.push({
      path: '/login',
      query: { redirect: router.currentRoute.value.fullPath }
    })
  }

  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  // ========== Public Methods ==========

  /**
   * GET请求
   */
  async get<T = any>(url: string, params?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.get(url, { ...config, params })
  }

  /**
   * POST请求
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.post(url, data, config)
  }

  /**
   * PUT请求
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.put(url, data, config)
  }

  /**
   * DELETE请求
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.delete(url, config)
  }

  /**
   * PATCH请求
   */
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.patch(url, data, config)
  }

  /**
   * 上传文件
   */
  async upload<T = any>(url: string, file: File, data?: Record<string, any>, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData()
    formData.append('file', file)

    // 添加其他数据
    if (data) {
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          formData.append(key, String(value))
        }
      })
    }

    return this.instance.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
  }

  /**
   * 下载文件
   */
  async download(url: string, filename?: string): Promise<void> {
    const response = await this.instance.get(url, {
      responseType: 'blob'
    })

    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }

  /**
   * 获取Axios实例（用于特殊配置）
   */
  getInstance(): AxiosInstance {
    return this.instance
  }
}

// 导出单例
export const apiClient = new ApiClient()

// 导出类型
export type { ApiResponse, ApiError }