import { create } from 'zustand'
import { uploadApi } from './api'
import type { UploadState } from './types'
import { message } from 'antd'

interface UploadStore extends UploadState {
  upload: (file: File, navigate: (path: string) => void) => Promise<void>
  reset: () => void
  setProgress: (progress: number) => void
}

export const useUploadStore = create<UploadStore>((set, get) => ({
  file: null,
  sessionId: null,
  uploading: false,
  progress: 0,
  error: null,

  upload: async (file: File, navigate: (path: string) => void) => {
    set({ uploading: true, progress: 0, error: null, file })

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        const currentProgress = get().progress
        if (currentProgress < 90) {
          set({ progress: currentProgress + 10 })
        }
      }, 200)

      const response = await uploadApi.upload(file)

      clearInterval(progressInterval)

      set({
        sessionId: response.session_id,
        uploading: false,
        progress: 100
      })

      message.success('文件上传成功！')

      // Navigate to analysis page after successful upload using React Router
      setTimeout(() => {
        navigate(`/analysis/${response.session_id}`)
      }, 1000)
      
    } catch (error: any) {
      set({
        error: error.message || '上传失败',
        uploading: false,
        progress: 0
      })
      message.error(error.message || '上传失败')
    }
  },

  setProgress: (progress: number) => set({ progress }),

  reset: () => set({
    file: null,
    sessionId: null,
    uploading: false,
    progress: 0,
    error: null
  })
}))