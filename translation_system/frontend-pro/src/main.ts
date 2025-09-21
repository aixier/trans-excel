import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import router from './router'
import App from './App.vue'
import 'ant-design-vue/dist/reset.css'

// 创建Vue应用
const app = createApp(App)

// 使用Pinia状态管理
const pinia = createPinia()
app.use(pinia)

// 使用Ant Design Vue
app.use(Antd)

// 使用路由
app.use(router)

// 全局错误处理
app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue Error]', err, info)
}

// 性能监控（开发环境）
if (import.meta.env.DEV) {
  app.config.performance = true
}

// 挂载应用
app.mount('#app')

// 导出app实例供调试使用
if (import.meta.env.DEV) {
  (window as any).__APP__ = app;
  (window as any).__ROUTER__ = router;
  (window as any).__PINIA__ = pinia;
}

export { app, router, pinia }