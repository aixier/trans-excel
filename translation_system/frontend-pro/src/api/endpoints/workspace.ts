/**
 * 翻译工作台 API
 * 专业翻译工作流：上传 → 分析 → 配置 → 翻译 → 跟踪
 */
import { apiClient } from '../client'

export interface FileAnalysis {
  total_sheets: number
  sheets: Array<{
    name: string
    total_rows: number
    total_columns: number
    translatable_rows: number
    is_terminology: boolean
    columns: Array<{
      index: number
      name: string
      type: string
      language?: string
      sample_data: string[]
    }>
    language_columns: string[]
    source_columns: string[]
    target_columns: string[]
  }>
}

export interface UploadedFile {
  file_id: string
  file_name: string
  file_size: number
  analysis: FileAnalysis
  status: string
  created_at: string
}

export interface StartTranslationParams {
  target_languages: string[]
  sheet_names?: string[]
  batch_size?: number
  max_concurrent?: number
  region_code?: string
  game_background?: string
  selected_ranges?: string[]
}

export interface TranslationStartResponse {
  task_id: string
  file_id: string
  status: string
  estimated_tasks: number
  message: string
}

class WorkspaceAPI {
  /**
   * 上传文件（仅保存，不翻译）
   */
  async uploadFile(file: File, projectId?: string): Promise<UploadedFile> {
    const formData = new FormData()
    formData.append('file', file)
    if (projectId) formData.append('project_id', projectId)

    const response = await fetch('/api/workspace/files/upload', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`Failed to upload file: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 基于已上传文件开始翻译
   */
  async startTranslation(fileId: string, params: StartTranslationParams): Promise<TranslationStartResponse> {
    const formData = new FormData()
    formData.append('target_languages', params.target_languages.join(','))

    if (params.sheet_names) {
      formData.append('sheet_names', params.sheet_names.join(','))
    }
    if (params.batch_size) {
      formData.append('batch_size', params.batch_size.toString())
    }
    if (params.max_concurrent) {
      formData.append('max_concurrent', params.max_concurrent.toString())
    }
    if (params.region_code) {
      formData.append('region_code', params.region_code)
    }
    if (params.game_background) {
      formData.append('game_background', params.game_background)
    }
    if (params.selected_ranges) {
      formData.append('selected_ranges', params.selected_ranges.join(','))
    }

    const response = await fetch(`/api/workspace/files/${fileId}/start-translation`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`Failed to start translation: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 获取文件信息和分析结果
   */
  async getFileInfo(fileId: string): Promise<UploadedFile> {
    const response = await fetch(`/api/workspace/files/${fileId}`)
    if (!response.ok) {
      throw new Error(`Failed to get file info: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 获取已上传文件列表
   */
  async listFiles(projectId?: string, limit: number = 50, offset: number = 0): Promise<{
    files: Array<{
      file_id: string
      file_name: string
      file_size: number
      status: string
      created_at: string
      analysis_summary: {
        total_sheets: number
        translatable_rows: number
      }
    }>
    total: number
    limit: number
    offset: number
  }> {
    const params = new URLSearchParams()
    if (projectId) params.append('project_id', projectId)
    params.append('limit', limit.toString())
    params.append('offset', offset.toString())

    const response = await fetch(`/api/workspace/files?${params}`)
    if (!response.ok) {
      throw new Error(`Failed to list files: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 删除上传的文件
   */
  async deleteFile(fileId: string): Promise<void> {
    const response = await fetch(`/api/workspace/files/${fileId}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      throw new Error(`Failed to delete file: ${response.statusText}`)
    }
  }

  /**
   * 预览文件分析结果
   */
  async previewFileAnalysis(fileId: string): Promise<{
    file_name: string
    analysis: FileAnalysis
    recommendations: {
      suggested_source_columns: string[]
      suggested_target_languages: string[]
      translation_complexity: 'simple' | 'moderate' | 'complex'
      estimated_time: number
    }
  }> {
    const response = await fetch(`/api/workspace/files/${fileId}/preview`)
    if (!response.ok) {
      throw new Error(`Failed to preview file: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 验证翻译配置
   */
  async validateTranslationConfig(fileId: string, params: StartTranslationParams): Promise<{
    valid: boolean
    warnings: string[]
    estimated_tasks: number
    estimated_cost: number
    estimated_time: number
  }> {
    const response = await fetch(`/api/workspace/files/${fileId}/validate-config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(params)
    })

    if (!response.ok) {
      throw new Error(`Failed to validate config: ${response.statusText}`)
    }
    return response.json()
  }
}

export const workspaceAPI = new WorkspaceAPI()