import { apiClient } from '../client'
import type {
  TranslationTask,
  TranslationConfig,
  TranslationProgress,
  TranslationResult,
  Translation,
  TranslationSuggestion,
  Cell,
  QualityScore
} from '@/types/models'

export interface UploadFileParams {
  file: File
  config: TranslationConfig
  projectId?: string
}

export interface BatchTranslateParams {
  texts: string[]
  sourceLanguage?: string
  targetLanguages: string[]
  gameContext?: string
  regionCode?: string
  options?: {
    preservePlaceholders?: boolean
    useTerminology?: boolean
    maxIterations?: number
    qualityThreshold?: number
  }
}

export interface CellTranslateParams {
  text: string
  sourceLanguage?: string
  targetLanguage: string
  context?: {
    previousText?: string
    nextText?: string
    columnName?: string
    sheetName?: string
    gameBackground?: string
  }
  suggestionsCount?: number
}

export interface TranslationAnalysis {
  sheets: Array<{
    name: string
    rows: number
    columns: number
    translatableColumns: string[]
    detectedLanguages: string[]
  }>
  totalCells: number
  translatableCells: number
  estimatedCost: number
  estimatedTime: number
}

export class TranslationAPI {
  /**
   * 上传文件并创建翻译任务
   */
  async uploadFile(params: UploadFileParams): Promise<TranslationTask> {
    return apiClient.upload<TranslationTask>(
      '/api/translation/upload',
      params.file,
      {
        target_languages: params.config.targetLanguages.join(','),
        batch_size: params.config.batchSize || 10,
        max_concurrent: params.config.maxConcurrent || 20,
        region_code: params.config.regionCode || 'cn-hangzhou',
        game_background: params.config.gameBackground || '',
        auto_detect: params.config.autoDetect !== false ? 'true' : 'false',
        project_id: params.projectId || ''
      }
    )
  }

  /**
   * 分析文件结构
   */
  async analyzeFile(file: File): Promise<TranslationAnalysis> {
    return apiClient.upload<TranslationAnalysis>(
      '/api/translation/analyze',
      file
    )
  }

  /**
   * 批量翻译文本
   */
  async batchTranslate(params: BatchTranslateParams): Promise<Translation[]> {
    return apiClient.post<Translation[]>('/api/translation/batch', params)
  }

  /**
   * 单元格翻译（带建议）
   */
  async translateCell(params: CellTranslateParams): Promise<{
    translation: string
    suggestions: TranslationSuggestion[]
    quality: QualityScore
  }> {
    return apiClient.post('/api/translation/cell', params)
  }

  /**
   * 获取任务状态
   */
  async getTaskStatus(taskId: string): Promise<TranslationTask> {
    return apiClient.get(`/api/translation/tasks/${taskId}/status`)
  }

  /**
   * 获取任务进度
   */
  async getTaskProgress(taskId: string): Promise<TranslationProgress> {
    return apiClient.get(`/api/translation/tasks/${taskId}/progress`)
  }

  /**
   * 取消翻译任务
   */
  async cancelTask(taskId: string): Promise<void> {
    return apiClient.delete(`/api/translation/tasks/${taskId}`)
  }

  /**
   * 永久删除翻译任务
   */
  async deleteTask(taskId: string): Promise<void> {
    return apiClient.delete(`/api/translation/tasks/${taskId}/permanent`)
  }

  /**
   * 下载翻译结果
   */
  async downloadResult(taskId: string): Promise<void> {
    return apiClient.download(
      `/api/translation/tasks/${taskId}/download`,
      `translation_${taskId}.xlsx`
    )
  }

  /**
   * 获取翻译建议
   */
  async getSuggestions(text: string, context?: any): Promise<TranslationSuggestion[]> {
    return apiClient.post<TranslationSuggestion[]>('/api/translation/suggestions', {
      text,
      context
    })
  }

  /**
   * 提交人工修正
   */
  async submitCorrection(cellId: string, correction: string, reason?: string): Promise<void> {
    return apiClient.post(`/api/translation/corrections`, {
      cell_id: cellId,
      correction,
      reason
    })
  }

  /**
   * 批量更新翻译
   */
  async batchUpdate(updates: Array<{ cellId: string; translation: string }>): Promise<void> {
    return apiClient.post('/api/translation/batch-update', { updates })
  }

  /**
   * 获取翻译历史
   */
  async getTranslationHistory(cellId: string): Promise<Translation[]> {
    return apiClient.get(`/api/translation/cells/${cellId}/history`)
  }

  /**
   * 评估翻译质量
   */
  async evaluateQuality(translations: Translation[]): Promise<QualityScore[]> {
    return apiClient.post<QualityScore[]>('/api/translation/evaluate', {
      translations
    })
  }

  /**
   * 批量取消任务
   */
  async batchCancelTasks(taskIds: string[]): Promise<{
    success_count: number
    failed_count: number
    failed_tasks: Array<{ task_id: string; reason: string }>
    message: string
  }> {
    return apiClient.post('/api/translation/tasks/batch/cancel', { task_ids: taskIds })
  }

  /**
   * 批量删除任务
   */
  async batchDeleteTasks(taskIds: string[]): Promise<{
    success_count: number
    failed_count: number
    failed_tasks: Array<{ task_id: string; reason: string }>
    message: string
  }> {
    return apiClient.post('/api/translation/tasks/batch-delete', { task_ids: taskIds })
  }

  /**
   * 导出翻译记忆库
   */
  async exportTranslationMemory(projectId: string): Promise<void> {
    return apiClient.download(
      `/api/projects/${projectId}/translation-memory/export`,
      `tm_${projectId}.tmx`
    )
  }

  /**
   * 导入翻译记忆库
   */
  async importTranslationMemory(projectId: string, file: File): Promise<{
    imported: number
    skipped: number
    failed: number
  }> {
    return apiClient.upload(
      `/api/projects/${projectId}/translation-memory/import`,
      file
    )
  }

  /**
   * 获取翻译统计
   */
  async getStatistics(projectId: string, dateRange?: { start: Date; end: Date }): Promise<{
    totalWords: number
    translatedWords: number
    reviewedWords: number
    totalCost: number
    averageQuality: number
    languageBreakdown: Record<string, number>
  }> {
    return apiClient.get(`/api/projects/${projectId}/statistics`, {
      start_date: dateRange?.start.toISOString(),
      end_date: dateRange?.end.toISOString()
    })
  }

  /**
   * 检查一致性
   */
  async checkConsistency(projectId: string, sheetId?: string): Promise<Array<{
    source: string
    translations: Array<{ text: string; count: number }>
    suggestion: string
  }>> {
    return apiClient.post(`/api/translation/consistency-check`, {
      project_id: projectId,
      sheet_id: sheetId
    })
  }

  /**
   * 验证占位符
   */
  async validatePlaceholders(cells: Cell[]): Promise<Array<{
    cellId: string
    issues: Array<{
      type: 'missing' | 'extra' | 'modified'
      placeholder: string
    }>
  }>> {
    return apiClient.post('/api/translation/validate-placeholders', { cells })
  }

  /**
   * 获取支持的语言列表
   */
  async getSupportedLanguages(): Promise<Array<{
    code: string
    name: string
    nativeName: string
  }>> {
    return apiClient.get('/api/translation/languages')
  }

  /**
   * 获取地区配置
   */
  async getRegionConfigs(): Promise<Array<{
    code: string
    name: string
    description: string
    guidelines: string
  }>> {
    return apiClient.get('/api/translation/regions')
  }
}

// 导出单例
export const translationAPI = new TranslationAPI()