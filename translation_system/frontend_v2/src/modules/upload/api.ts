import { apiClient } from '@core/api/client'
import type { UploadResponse, SessionStatus } from './types'

export const uploadApi = {
  upload: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    return apiClient.post('/analyze/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  getSessionStatus: (sessionId: string): Promise<SessionStatus> => {
    return apiClient.get(`/sessions/${sessionId}`)
  },

  validateFile: async (file: File): Promise<{ valid: boolean; message: string }> => {
    const formData = new FormData()
    formData.append('file', file)

    return apiClient.post('/analyze/upload/validate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}