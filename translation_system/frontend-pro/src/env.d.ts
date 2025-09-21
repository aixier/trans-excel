/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_VERSION: string
  readonly VITE_API_BASE_URL: string
  readonly VITE_API_TIMEOUT: string
  readonly VITE_WS_URL: string
  readonly VITE_WS_RECONNECT_ATTEMPTS: string
  readonly VITE_WS_RECONNECT_DELAY: string
  readonly VITE_STORAGE_PREFIX: string
  readonly VITE_STORAGE_EXPIRE_TIME: string
  readonly VITE_FEATURE_REAL_TIME_COLLAB: string
  readonly VITE_FEATURE_AI_SUGGESTIONS: string
  readonly VITE_FEATURE_ANALYTICS: string
  readonly VITE_DEV_PORT: string
  readonly VITE_DEV_HOST: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}