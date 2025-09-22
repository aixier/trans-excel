/**
 * 术语管理 API
 */
import { apiClient } from '../client'

export interface TerminologyItem {
  id?: string
  source: string
  target_translations: Record<string, string>
  category?: string
  context?: string
  case_sensitive?: boolean
  created_at?: string
  updated_at?: string
}

export interface TerminologyCreateRequest {
  source: string
  target_translations: Record<string, string>
  category?: string
  context?: string
  case_sensitive?: boolean
  project_id?: string
}

export interface TerminologyUpdateRequest {
  source?: string
  target_translations?: Record<string, string>
  category?: string
  context?: string
  case_sensitive?: boolean
}

export interface TerminologyBatchImportResponse {
  total: number
  success: number
  failed: number
  errors: string[]
}

export interface TerminologyListParams {
  project_id?: string
  category?: string
  search?: string
  limit?: number
  offset?: number
}

class TerminologyAPI {
  /**
   * 获取术语列表
   */
  async list(params?: TerminologyListParams): Promise<TerminologyItem[]> {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString())
        }
      })
    }

    const response = await fetch(`/api/terminology/list?${queryParams}`)
    if (!response.ok) {
      throw new Error(`Failed to fetch terminology list: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 获取单个术语
   */
  async get(termId: string): Promise<TerminologyItem> {
    const response = await fetch(`/api/terminology/${termId}`)
    if (!response.ok) {
      throw new Error(`Failed to fetch terminology: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 创建术语
   */
  async create(data: TerminologyCreateRequest): Promise<TerminologyItem> {
    const response = await fetch('/api/terminology/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })

    if (!response.ok) {
      throw new Error(`Failed to create terminology: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 更新术语
   */
  async update(termId: string, data: TerminologyUpdateRequest): Promise<TerminologyItem> {
    const response = await fetch(`/api/terminology/${termId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })

    if (!response.ok) {
      throw new Error(`Failed to update terminology: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 删除术语
   */
  async delete(termId: string): Promise<void> {
    const response = await fetch(`/api/terminology/${termId}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      throw new Error(`Failed to delete terminology: ${response.statusText}`)
    }
  }

  /**
   * 批量删除术语
   */
  async batchDelete(termIds: string[]): Promise<void> {
    const response = await fetch('/api/terminology/batch-delete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(termIds)
    })

    if (!response.ok) {
      throw new Error(`Failed to batch delete terminology: ${response.statusText}`)
    }
  }

  /**
   * 导入JSON格式术语表
   */
  async importJson(file: File, projectId?: string, category?: string): Promise<TerminologyBatchImportResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (projectId) formData.append('project_id', projectId)
    if (category) formData.append('category', category)

    const response = await fetch('/api/terminology/import/json', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`Failed to import JSON terminology: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 导入Excel格式术语表
   */
  async importExcel(file: File, projectId?: string, category?: string): Promise<TerminologyBatchImportResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (projectId) formData.append('project_id', projectId)
    if (category) formData.append('category', category)

    const response = await fetch('/api/terminology/import/excel', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`Failed to import Excel terminology: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 导出术语表为JSON格式
   */
  async exportJson(projectId?: string, category?: string): Promise<Record<string, any>> {
    const queryParams = new URLSearchParams()
    if (projectId) queryParams.append('project_id', projectId)
    if (category) queryParams.append('category', category)

    const response = await fetch(`/api/terminology/export/json?${queryParams}`)
    if (!response.ok) {
      throw new Error(`Failed to export terminology: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 获取所有分类
   */
  async getCategories(): Promise<string[]> {
    const response = await fetch('/api/terminology/categories')
    if (!response.ok) {
      throw new Error(`Failed to fetch categories: ${response.statusText}`)
    }
    const data = await response.json()
    return data.categories || []
  }

  /**
   * 下载导出的JSON文件
   */
  downloadJson(data: Record<string, any>, filename: string = 'terminology.json') {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }
}

export const terminologyAPI = new TerminologyAPI()