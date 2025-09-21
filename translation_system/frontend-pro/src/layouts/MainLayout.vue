<template>
  <a-layout class="main-layout">
    <!-- 侧边栏 -->
    <a-layout-sider
      v-model:collapsed="collapsed"
      :trigger="null"
      collapsible
      class="layout-sider"
    >
      <div class="logo">
        <TranslationOutlined class="logo-icon" />
        <span v-if="!collapsed" class="logo-text">Translation Pro</span>
      </div>

      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        @click="handleMenuClick"
      >
        <a-menu-item key="dashboard">
          <DashboardOutlined />
          <span>仪表板</span>
        </a-menu-item>

        <a-menu-item key="quick-translate">
          <ThunderboltOutlined />
          <span>快速翻译</span>
        </a-menu-item>

        <a-menu-item key="workspace">
          <FileExcelOutlined />
          <span>翻译工作台</span>
        </a-menu-item>

        <a-menu-item key="tasks">
          <UnorderedListOutlined />
          <span>任务管理</span>
        </a-menu-item>

        <a-menu-item key="terminology">
          <BookOutlined />
          <span>术语管理</span>
        </a-menu-item>

        <a-menu-item key="maintenance">
          <SyncOutlined />
          <span>版本维护</span>
        </a-menu-item>

        <a-menu-item key="settings">
          <SettingOutlined />
          <span>系统设置</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <!-- 顶部导航 -->
      <a-layout-header class="layout-header">
        <div class="header-content">
          <div class="header-left">
            <a-button
              type="text"
              @click="() => (collapsed = !collapsed)"
              class="trigger-button"
            >
              <MenuUnfoldOutlined v-if="collapsed" />
              <MenuFoldOutlined v-else />
            </a-button>

            <a-breadcrumb>
              <a-breadcrumb-item>首页</a-breadcrumb-item>
              <a-breadcrumb-item>{{ currentPageName }}</a-breadcrumb-item>
            </a-breadcrumb>
          </div>

          <div class="header-right">
            <!-- 任务状态 -->
            <a-badge :count="runningTasks" :offset="[-5, 5]">
              <a-button type="text" @click="showTaskDrawer = true">
                <LoadingOutlined v-if="runningTasks > 0" spin />
                <CheckCircleOutlined v-else />
                <span class="header-text">{{ runningTasks }} 任务进行中</span>
              </a-button>
            </a-badge>

            <!-- 语言切换 -->
            <a-dropdown>
              <a-button type="text">
                <GlobalOutlined />
                <span class="header-text">中文</span>
              </a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item key="zh">中文</a-menu-item>
                  <a-menu-item key="en">English</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>

            <!-- 用户信息 -->
            <a-dropdown>
              <a-button type="text" class="user-button">
                <a-avatar size="small">
                  <template #icon><UserOutlined /></template>
                </a-avatar>
                <span class="header-text">管理员</span>
              </a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item key="profile">个人信息</a-menu-item>
                  <a-menu-item key="logout">退出登录</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </div>
      </a-layout-header>

      <!-- 主内容区 -->
      <a-layout-content class="layout-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </a-layout-content>

      <!-- 底部 -->
      <a-layout-footer class="layout-footer">
        <div class="footer-content">
          <span>Translation System Pro © 2024</span>
          <span>后端状态: <a-tag color="green">在线</a-tag></span>
        </div>
      </a-layout-footer>
    </a-layout>

    <!-- 任务抽屉 -->
    <a-drawer
      v-model:open="showTaskDrawer"
      title="进行中的任务"
      placement="right"
      :width="400"
    >
      <TaskList />
    </a-drawer>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  ThunderboltOutlined,
  FileExcelOutlined,
  UnorderedListOutlined,
  BookOutlined,
  SyncOutlined,
  SettingOutlined,
  TranslationOutlined,
  GlobalOutlined,
  UserOutlined,
  LoadingOutlined,
  CheckCircleOutlined
} from '@ant-design/icons-vue'
import TaskList from '@/components/common/TaskList.vue'

const router = useRouter()
const route = useRoute()

const collapsed = ref(false)
const selectedKeys = ref(['dashboard'])
const showTaskDrawer = ref(false)
const runningTasks = ref(0)

const pageNames = {
  dashboard: '仪表板',
  'quick-translate': '快速翻译',
  workspace: '翻译工作台',
  tasks: '任务管理',
  terminology: '术语管理',
  maintenance: '版本维护',
  settings: '系统设置'
}

const currentPageName = computed(() => {
  const key = route.name as string
  return pageNames[key] || '页面'
})

const handleMenuClick = ({ key }: { key: string }) => {
  router.push({ name: key })
}
</script>

<style scoped lang="scss">
.main-layout {
  min-height: 100vh;

  .layout-sider {
    background: #001529;

    .logo {
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 18px;
      font-weight: 600;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);

      .logo-icon {
        font-size: 24px;
        margin-right: 12px;
      }

      .logo-text {
        transition: all 0.3s;
      }
    }
  }

  .layout-header {
    background: #fff;
    padding: 0;
    box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
    position: sticky;
    top: 0;
    z-index: 10;

    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      height: 100%;
      padding-right: 24px;

      .header-left {
        display: flex;
        align-items: center;

        .trigger-button {
          font-size: 18px;
          width: 64px;
          height: 64px;
        }
      }

      .header-right {
        display: flex;
        align-items: center;
        gap: 16px;

        .header-text {
          margin-left: 8px;
        }

        .user-button {
          display: flex;
          align-items: center;
          gap: 8px;
        }
      }
    }
  }

  .layout-content {
    margin: 24px;
    min-height: calc(100vh - 64px - 48px - 48px);

    // 页面切换动画
    .fade-enter-active,
    .fade-leave-active {
      transition: all 0.3s;
    }

    .fade-enter-from {
      opacity: 0;
      transform: translateX(-20px);
    }

    .fade-leave-to {
      opacity: 0;
      transform: translateX(20px);
    }
  }

  .layout-footer {
    background: #f0f2f5;
    text-align: center;
    padding: 12px 50px;

    .footer-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: #666;
    }
  }
}

// 响应式
@media (max-width: 768px) {
  .header-text {
    display: none;
  }
}
</style>