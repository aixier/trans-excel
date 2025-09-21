<template>
  <div class="task-manager">
    <a-page-header title="任务管理" sub-title="查看和管理所有翻译任务">
      <template #extra>
        <a-button type="primary" @click="goToQuickTranslate">
          <template #icon><PlusOutlined /></template>
          新建任务
        </a-button>
      </template>
    </a-page-header>

    <a-card>
      <a-table
        :columns="columns"
        :data-source="taskList"
        :loading="loading"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'fileName'">
            <a @click="viewTask(record)">{{ record.fileName }}</a>
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
              <a-button type="link" size="small" @click="viewTask(record)">查看</a-button>
              <a-button
                type="link"
                size="small"
                @click="downloadTask(record)"
                :disabled="record.status !== 'completed'"
              >
                下载
              </a-button>
              <a-button
                type="link"
                danger
                size="small"
                @click="cancelTask(record)"
                :disabled="record.status === 'completed'"
              >
                取消
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

const router = useRouter()
const loading = ref(false)

const columns = [
  {
    title: '文件名',
    dataIndex: 'fileName',
    key: 'fileName'
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
    title: '目标语言',
    dataIndex: 'languages',
    key: 'languages',
    render: (languages: string[]) => languages.join(', ')
  },
  {
    title: '创建时间',
    dataIndex: 'createTime',
    key: 'createTime'
  },
  {
    title: '操作',
    key: 'action',
    width: 200
  }
]

const taskList = ref<any[]>([])

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/translation/tasks')
    if (response.ok) {
      const data = await response.json()
      taskList.value = data.tasks || []
    }
  } catch (error) {
    console.error('Failed to load tasks:', error)
  } finally {
    loading.value = false
  }
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    pending: 'default',
    processing: 'processing',
    completed: 'success',
    failed: 'error'
  }
  return colorMap[status] || 'default'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return textMap[status] || status
}

const goToQuickTranslate = () => router.push('/quick-translate')
const viewTask = (task: any) => console.log('View task', task)
const downloadTask = (task: any) => message.success(`开始下载 ${task.fileName}`)
const cancelTask = (task: any) => message.warning(`取消任务 ${task.fileName}`)

onMounted(() => {
  console.log('TaskManager mounted')
  loadTasks()
})
</script>

<style scoped lang="scss">
.task-manager {
  padding: 24px;
}
</style>