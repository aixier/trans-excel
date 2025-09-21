import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: { title: '仪表板', icon: 'DashboardOutlined' }
      },
      {
        path: 'quick-translate',
        name: 'quick-translate',
        component: () => import('@/pages/QuickTranslate.vue'),
        meta: { title: '快速翻译', icon: 'ThunderboltOutlined' }
      },
      {
        path: 'workspace',
        name: 'workspace',
        component: () => import('@/pages/TranslationWorkspace.vue'),
        meta: { title: '翻译工作台', icon: 'FileExcelOutlined' }
      },
      {
        path: 'tasks',
        name: 'tasks',
        component: () => import('@/pages/TaskManager.vue'),
        meta: { title: '任务管理', icon: 'UnorderedListOutlined' }
      },
      {
        path: 'terminology',
        name: 'terminology',
        component: () => import('@/pages/TerminologyManager.vue'),
        meta: { title: '术语管理', icon: 'BookOutlined' }
      },
      {
        path: 'maintenance',
        name: 'maintenance',
        component: () => import('@/pages/VersionMaintenance.vue'),
        meta: { title: '版本维护', icon: 'SyncOutlined' }
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('@/pages/Settings.vue'),
        meta: { title: '系统设置', icon: 'SettingOutlined' }
      }
    ]
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/Login.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - Translation System Pro`
  }

  // 检查登录状态（暂时跳过）
  // if (to.path !== '/login' && !isAuthenticated()) {
  //   next('/login')
  // } else {
  //   next()
  // }

  next()
})

export default router