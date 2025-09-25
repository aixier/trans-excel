import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    vue(),
    vueJsx()
    // vueDevTools() // 暂时禁用以避免模板解析错误
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@api': fileURLToPath(new URL('./src/api', import.meta.url)),
      '@components': fileURLToPath(new URL('./src/components', import.meta.url)),
      '@modules': fileURLToPath(new URL('./src/modules', import.meta.url)),
      '@stores': fileURLToPath(new URL('./src/stores', import.meta.url)),
      '@types': fileURLToPath(new URL('./src/types', import.meta.url)),
      '@utils': fileURLToPath(new URL('./src/utils', import.meta.url))
    }
  },
  server: {
    port: 5174,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8101',
        changeOrigin: true,
        secure: false
      },
      '/sse': {
        target: 'http://localhost:8101',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'ui-vendor': ['ant-design-vue', '@ant-design/icons-vue'],
          'utils-vendor': ['axios', 'lodash-es', 'dayjs'],
          'luckysheet': ['luckysheet', 'luckyexcel'],
          'excel': ['exceljs', 'file-saver']
        }
      },
      // 外部化Luckysheet（通过CDN加载）
      external: [],
    },
    chunkSizeWarningLimit: 2000
  },
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'axios',
      'ant-design-vue',
      'dayjs',
      'lodash-es'
    ],
    exclude: [
      'luckysheet' // Luckysheet通过CDN加载
    ]
  },
  // 定义全局变量
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV)
  }
})