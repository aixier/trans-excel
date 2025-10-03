export interface UploadState {
  file: File | null
  sessionId: string | null
  uploading: boolean
  progress: number
  error: string | null
}

export interface UploadResponse {
  session_id: string
  filename: string
  status: string
  message?: string
}

export interface SessionStatus {
  session_id: string
  filename: string
  status: string
  created_at: string
  updated_at: string
  metadata?: Record<string, any>
}