<template>
  <div class="dashboard-container">
    <!-- 顶部统计卡片 -->
    <a-row :gutter="[16, 16]" class="stats-row">
      <a-col :xs="24" :sm="12">
        <a-card hoverable>
          <a-statistic
            title="今日翻译量"
            :value="stats.todayTranslated"
            :prefix-icon="h(FileTextOutlined)"
            :value-style="{ color: '#3f8600' }"
          >
            <template #suffix>
              <span style="font-size: 14px">条</span>
            </template>
          </a-statistic>
          <div class="trend">
            <ArrowUpOutlined style="color: #52c41a" />
            <span>12.5%</span>
          </div>
        </a-card>
      </a-col>

      <a-col :xs="24" :sm="12">
        <a-card hoverable>
          <a-statistic
            title="进行中任务"
            :value="stats.runningTasks"
            :prefix-icon="h(LoadingOutlined)"
            :value-style="{ color: '#1890ff' }"
          />
          <a-progress :percent="runningTasksProgress" :show-info="false" status="active" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 快速操作区 -->
    <div class="quick-actions">
      <h3>快速操作</h3>
      <a-row :gutter="[16, 16]">
        <a-col :span="6">
          <a-card
            hoverable
            @click="goToQuickTranslate"
            class="action-card"
          >
            <div class="action-content">
              <ThunderboltOutlined class="action-icon" />
              <span>快速翻译</span>
            </div>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card
            hoverable
            @click="goToWorkspace"
            class="action-card"
          >
            <div class="action-content">
              <FileExcelOutlined class="action-icon" />
              <span>导入Excel</span>
            </div>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card
            hoverable
            @click="goToTasks"
            class="action-card"
          >
            <div class="action-content">
              <UnorderedListOutlined class="action-icon" />
              <span>查看任务</span>
            </div>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card
            hoverable
            @click="goToTerminology"
            class="action-card"
          >
            <div class="action-content">
              <BookOutlined class="action-icon" />
              <span>术语管理</span>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 主内容区 -->
    <a-row :gutter="[16, 16]" class="main-content">
      <!-- 最近任务 -->
      <a-col :xs="24" :lg="16">
        <a-card title="最近任务" :bordered="false">
          <template #extra>
            <a-button type="link" @click="goToTasks">查看全部</a-button>
          </template>

          <a-table
            :columns="taskColumns"
            :data-source="recentTasks"
            :pagination="false"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'name'">
                <a @click="viewTask(record)">{{ record.name }}</a>
              </template>
              <template v-else-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">
                  {{ getStatusText(record.status) }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'progress'">
                <a-progress :percent="record.progress" size="small" />
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-button type="link" size="small" @click="viewTask(record)">
                    查看
                  </a-button>
                  <a-button
                    type="link"
                    size="small"
                    @click="downloadTask(record)"
                    :disabled="record.status !== 'completed'"
                  >
                    下载
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>

      <!-- 翻译统计图表 -->
      <a-col :xs="24" :lg="8">
        <a-card title="语言分布" :bordered="false">
          <div class="chart-container">
            <div v-if="languageDistribution.length > 0" class="language-stats">
              <div v-for="lang in languageDistribution" :key="lang.code" class="lang-item">
                <div class="lang-header">
                  <span class="lang-name">{{ lang.name }}</span>
                  <span class="lang-percent">{{ lang.percent }}%</span>
                </div>
                <a-progress
                  :percent="lang.percent"
                  :show-info="false"
                  :stroke-color="lang.color"
                />
                <div class="lang-count">{{ lang.count }} 条</div>
              </div>
            </div>
            <a-empty v-else description="暂无语言统计数据" />
          </div>
        </a-card>

        <!-- 系统公告 -->
        <a-card title="系统公告" :bordered="false" style="margin-top: 16px">
          <a-list size="small" :data-source="announcements">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-badge status="processing" v-if="item.isNew" />
                <span class="announcement-title">{{ item.title }}</span>
                <div class="announcement-time">{{ item.time }}</div>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>

    <!-- 翻译趋势图 -->
    <a-card title="翻译趋势" :bordered="false" class="trend-card">
      <template #extra>
        <a-radio-group v-model:value="trendPeriod" button-style="solid" size="small">
          <a-radio-button value="week">本周</a-radio-button>
          <a-radio-button value="month">本月</a-radio-button>
          <a-radio-button value="year">本年</a-radio-button>
        </a-radio-group>
      </template>

      <div class="trend-chart">
        <!-- 这里可以集成图表组件，如ECharts -->
        <a-empty description="图表加载中..." />
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  FileTextOutlined,
  LoadingOutlined,
  ArrowUpOutlined,
  ThunderboltOutlined,
  FileExcelOutlined,
  UnorderedListOutlined,
  BookOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { apiClient } from '@/api/client'

const router = useRouter()

// 统计数据
const stats = ref({
  todayTranslated: 0,
  runningTasks: 0
})

// 进行中任务的进度
const runningTasksProgress = ref(0)

// 最近任务
const recentTasks = ref<any[]>([])
const loading = ref(false)

// 任务表格列
const taskColumns = [
  {
    title: '文件名',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '进度',
    dataIndex: 'progress',
    key: 'progress',
    width: 150
  },
  {
    title: '创建时间',
    dataIndex: 'createTime',
    key: 'createTime',
    width: 150
  },
  {
    title: '操作',
    key: 'action',
    width: 120
  }
]

// 语言分布
const languageDistribution = ref<any[]>([])

// 加载语言统计
const loadLanguageStats = async () => {
  try {
    // 使用模拟数据，后续可以实现真实API
    const mockData = [
      { code: 'pt', name: '葡萄牙语', percentage: 35, count: 1250 },
      { code: 'th', name: '泰语', percentage: 25, count: 890 },
      { code: 'ind', name: '印尼语', percentage: 20, count: 710 },
      { code: 'vn', name: '越南语', percentage: 20, count: 710 }
    ]

    languageDistribution.value = mockData.map((lang: any, index: number) => ({
      code: lang.code,
      name: lang.name,
      percent: lang.percentage || 0,
      count: lang.count || 0,
      color: ['#52c41a', '#1890ff', '#faad14', '#722ed1'][index % 4]
    }))
  } catch (error) {
    console.log('Failed to load language stats:', error)
    languageDistribution.value = []
  }
}

// 系统公告
const announcements = ref([
  { id: 1, title: '系统已就绪', time: new Date().toLocaleTimeString(), isNew: true }
])

// 趋势周期
const trendPeriod = ref('week')

// 获取状态颜色
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    pending: 'default',
    processing: 'processing',
    completed: 'success',
    failed: 'error'
  }
  return colorMap[status] || 'default'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return textMap[status] || status
}

// 路由跳转
const goToQuickTranslate = () => router.push('/quick-translate')
const goToWorkspace = () => router.push('/workspace')
const goToTasks = () => router.push('/tasks')
const goToTerminology = () => router.push('/terminology')

// 查看任务
const viewTask = (task: any) => {
  router.push(`/tasks?id=${task.id}`)
}

// 下载任务
const downloadTask = (task: any) => {
  message.success(`开始下载 ${task.name}`)
}

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    // 移除不支持的sort参数
    const response = await fetch('/api/translation/tasks?limit=5')
    if (response.ok) {
      const data = await response.json()
      // 处理任务数据，添加必要的字段
      recentTasks.value = (data.tasks || []).slice(0, 5).map((task: any) => ({
        id: task.task_id,
        name: task.file_name,
        status: task.status === 'translating' ? 'processing' : task.status,
        progress: task.progress || 0,
        createTime: task.created_at ? new Date(task.created_at).toLocaleString('zh-CN') : '-',
        completed_at: task.updated_at
      }))

      // 计算统计数据 - 修正进行中任务的计算
      const runningCount = (data.tasks || []).filter((t: any) =>
        t.status === 'translating' || t.status === 'uploading' || t.status === 'analyzing'
      ).length

      const completedToday = recentTasks.value.filter(t => {
        const today = new Date().toDateString()
        return t.status === 'completed' && t.completed_at && new Date(t.completed_at).toDateString() === today
      }).length

      // 设置正确的运行中任务数量
      stats.value.runningTasks = runningCount
      stats.value.todayTranslated = completedToday * 100 // 估算值

      // 如果有进行中的任务，计算整体进度
      if (runningCount > 0) {
        const runningTasks = (data.tasks || []).filter((t: any) =>
          t.status === 'translating' || t.status === 'uploading' || t.status === 'analyzing'
        )
        const totalProgress = runningTasks.reduce((sum: number, t: any) => sum + (t.progress || 0), 0)
        runningTasksProgress.value = Math.round(totalProgress / runningTasks.length)
      } else {
        runningTasksProgress.value = 0
      }
    } else {
      // API返回错误，使用空列表
      console.log('Tasks API returned error, using empty list')
      recentTasks.value = []
      stats.value.runningTasks = 0
    }
  } catch (error) {
    console.error('Failed to load tasks:', error)
    recentTasks.value = []
    stats.value.runningTasks = 0
  } finally {
    loading.value = false
  }
}

// 加载健康状态
const loadHealth = async () => {
  try {
    const response = await fetch('/api/health/status')
    if (response.ok) {
      const data = await response.json()
      console.log('Backend health:', data)
    }
  } catch (error) {
    message.warning('后端服务连接失败')
  }
}

// 生命周期
onMounted(() => {
  console.log('Dashboard mounted')
  loadHealth()
  loadTasks()
  loadLanguageStats()
})
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 24px;
  background: #f0f2f5;
  min-height: calc(100vh - 64px);

  .stats-row {
    margin-bottom: 24px;

    .trend {
      margin-top: 8px;
      font-size: 12px;
      color: #666;
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .quality-badge {
      margin-top: 8px;
    }
  }

  .quick-actions {
    margin-bottom: 24px;

    h3 {
      margin-bottom: 16px;
      font-size: 18px;
      font-weight: 600;
    }

    .action-card {
      text-align: center;
      transition: all 0.3s;

      &:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }

      .action-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        padding: 16px 0;

        .action-icon {
          font-size: 32px;
          color: #1890ff;
        }

        span {
          font-size: 14px;
          font-weight: 500;
        }
      }
    }
  }

  .main-content {
    margin-bottom: 24px;

    .language-stats {
      .lang-item {
        margin-bottom: 16px;

        .lang-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;

          .lang-name {
            font-weight: 500;
          }

          .lang-percent {
            color: #999;
            font-size: 12px;
          }
        }

        .lang-count {
          margin-top: 4px;
          font-size: 12px;
          color: #999;
        }
      }
    }

    .announcement-title {
      flex: 1;
      margin-left: 8px;
    }

    .announcement-time {
      font-size: 12px;
      color: #999;
    }
  }

  .trend-card {
    .trend-chart {
      min-height: 300px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}

// 响应式布局
@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;

    .quick-actions {
      .action-card {
        .action-content {
          padding: 8px 0;

          .action-icon {
            font-size: 24px;
          }

          span {
            font-size: 12px;
          }
        }
      }
    }
  }
}
</style>