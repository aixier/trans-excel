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
      <!-- 批量操作栏 -->
      <div class="batch-actions" v-if="selectedRowKeys.length > 0">
        <a-alert
          :message="`已选择 ${selectedRowKeys.length} 个任务`"
          type="info"
          show-icon
          style="margin-bottom: 16px"
        >
          <template #action>
            <a-space>
              <a-button size="small" @click="clearSelection">取消选择</a-button>
              <a-button size="small" type="primary" danger @click="batchCancel">
                批量取消
              </a-button>
              <a-popconfirm
                title="确定要删除选中的任务吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="batchDelete"
              >
                <a-button size="small" danger>批量删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </a-alert>
      </div>

      <!-- 任务筛选 -->
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="6">
          <a-select
            v-model:value="filterStatus"
            placeholder="筛选状态"
            style="width: 100%"
            allow-clear
            @change="filterTasks"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="pending">待处理</a-select-option>
            <a-select-option value="processing">处理中</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
            <a-select-option value="failed">失败</a-select-option>
            <a-select-option value="cancelled">已取消</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索文件名"
            @search="filterTasks"
            allow-clear
          />
        </a-col>
        <a-col :span="12" style="text-align: right">
          <a-button @click="refreshTasks">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-col>
      </a-row>

      <a-table
        :columns="columns"
        :data-source="filteredTaskList"
        :loading="loading"
        :row-selection="{
          selectedRowKeys: selectedRowKeys,
          onChange: onSelectChange,
          getCheckboxProps: getCheckboxProps
        }"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'file_name'">
            <a @click="viewTask(record)">{{ record.file_name }}</a>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'progress'">
            <a-progress :percent="record.progress" size="small" />
            <span class="progress-text">{{ record.progress }}%</span>
          </template>
          <template v-else-if="column.key === 'translation_count'">
            {{ record.translated_rows }}/{{ record.total_rows }}
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="viewTask(record)">查看</a-button>
              <a-button
                type="link"
                size="small"
                @click="downloadTask(record)"
                :disabled="record.status !== 'completed' && record.status !== 'failed'"
              >
                下载
              </a-button>
              <a-button
                type="link"
                danger
                size="small"
                @click="cancelTask(record)"
                :disabled="record.status === 'completed' || record.status === 'failed' || record.status === 'cancelled'"
              >
                取消
              </a-button>
              <a-popconfirm
                title="确定要永久删除这个任务吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="deleteTask(record)"
              >
                <a-button
                  type="link"
                  danger
                  size="small"
                >
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import { translationAPI } from '@/api/endpoints/translation'

const router = useRouter()
const loading = ref(false)

// 批量选择相关
const selectedRowKeys = ref<string[]>([])
const filterStatus = ref<string>('')
const searchText = ref<string>('')

const columns = [
  {
    title: '文件名',
    dataIndex: 'file_name',
    key: 'file_name'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 120
  },
  {
    title: '进度',
    dataIndex: 'progress',
    key: 'progress',
    width: 200
  },
  {
    title: '已翻译/总数',
    key: 'translation_count',
    width: 120
  },
  {
    title: '目标语言',
    dataIndex: 'languages',
    key: 'languages'
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 180
  },
  {
    title: '操作',
    key: 'action',
    width: 200
  }
]

const taskList = ref<any[]>([])
let refreshTimer: any = null

// 计算过滤后的任务列表
const filteredTaskList = computed(() => {
  let filtered = taskList.value

  // 状态过滤
  if (filterStatus.value) {
    filtered = filtered.filter(task => task.status === filterStatus.value)
  }

  // 文件名搜索
  if (searchText.value) {
    filtered = filtered.filter(task =>
      task.file_name.toLowerCase().includes(searchText.value.toLowerCase())
    )
  }

  return filtered
})

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/translation/tasks')
    const data = await response.json()

    // 处理错误响应
    if (data.error || !response.ok) {
      console.log('API返回错误，使用空列表:', data.message)
      taskList.value = []
    } else {
      // 处理任务列表数据
      taskList.value = (data.tasks || []).map((task: any) => ({
        ...task,
        id: task.task_id, // 映射task_id到id，用于表格row-key
        created_at: task.created_at ? new Date(task.created_at).toLocaleString('zh-CN') : '-',
        languages: task.languages?.join(', ') || '-'
      }))
    }
  } catch (error) {
    console.error('Failed to load tasks:', error)
    taskList.value = []
  } finally {
    loading.value = false
  }
}

// 移除自动刷新功能，改为事件驱动刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    uploading: 'blue',
    translating: 'processing',
    completed: 'success',
    failed: 'error',
    cancelled: 'default'
  }
  return colorMap[status] || 'default'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    uploading: '上传中',
    translating: '翻译中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return textMap[status] || status
}

const goToQuickTranslate = () => router.push('/quick-translate')

// 查看任务详情
const viewTask = async (task: any) => {
  try {
    const status = await translationAPI.getTaskStatus(task.task_id)
    Modal.info({
      title: '任务详情',
      content: `
        任务ID: ${task.task_id}
        文件名: ${task.file_name}
        状态: ${getStatusText(task.status)}
        进度: ${task.progress}%
        已翻译: ${task.translated_rows}/${task.total_rows}
        目标语言: ${task.languages}
        创建时间: ${task.created_at}
      `,
      width: 600
    })
  } catch (error) {
    console.error('获取任务详情失败:', error)
  }
}

// 下载任务结果
const downloadTask = async (task: any) => {
  try {
    message.loading(`正在下载 ${task.file_name}...`)
    await translationAPI.downloadResult(task.task_id)
    message.success('下载成功')
  } catch (error) {
    message.error('下载失败')
    console.error(error)
  }
}

// 取消任务
const cancelTask = async (task: any) => {
  Modal.confirm({
    title: '确认取消',
    content: `确定要取消任务 "${task.file_name}" 吗？`,
    async onOk() {
      try {
        await translationAPI.cancelTask(task.task_id)
        message.success('任务已取消')
        loadTasks() // 重新加载列表
      } catch (error) {
        message.error('取消失败')
        console.error(error)
      }
    }
  })
}

// 删除任务
const deleteTask = async (task: any) => {
  try {
    await translationAPI.deleteTask(task.task_id)
    message.success('任务已删除')
    loadTasks() // 重新加载列表
  } catch (error) {
    message.error('删除任务失败')
    console.error(error)
  }
}

// 选择变更处理
const onSelectChange = (selectedKeys: string[]) => {
  selectedRowKeys.value = selectedKeys
}

// 获取复选框属性
const getCheckboxProps = (record: any) => ({
  disabled: false // 可以根据条件禁用某些任务的选择
})

// 清除选择
const clearSelection = () => {
  selectedRowKeys.value = []
}

// 筛选任务
const filterTasks = () => {
  // filteredTaskList 是计算属性，会自动更新
}

// 刷新任务列表
const refreshTasks = () => {
  clearSelection()
  loadTasks()
}

// 批量取消任务
const batchCancel = async () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请选择要取消的任务')
    return
  }

  // 过滤掉空值
  const validTaskIds = selectedRowKeys.value.filter(id => id != null && id !== '')
  if (validTaskIds.length === 0) {
    message.warning('没有有效的任务ID')
    return
  }

  Modal.confirm({
    title: '批量取消任务',
    content: `确定要取消选中的 ${validTaskIds.length} 个任务吗？`,
    okText: '确定',
    cancelText: '取消',
    onOk: async () => {
      try {
        loading.value = true
        const result = await translationAPI.batchCancelTasks(validTaskIds)

        if (result.success_count > 0) {
          message.success(`成功取消 ${result.success_count} 个任务`)
        }

        if (result.failed_count > 0) {
          message.warning(`${result.failed_count} 个任务取消失败`)
          console.error('Failed tasks:', result.failed_tasks)
        }

        clearSelection()
        loadTasks()
      } catch (error) {
        message.error('批量取消失败')
        console.error(error)
      } finally {
        loading.value = false
      }
    }
  })
}

// 批量删除任务
const batchDelete = async () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请选择要删除的任务')
    return
  }

  // 过滤掉空值
  const validTaskIds = selectedRowKeys.value.filter(id => id != null && id !== '')
  if (validTaskIds.length === 0) {
    message.warning('没有有效的任务ID')
    return
  }

  try {
    loading.value = true
    const result = await translationAPI.batchDeleteTasks(validTaskIds)

    if (result.success_count > 0) {
      message.success(`成功删除 ${result.success_count} 个任务`)
    }

    if (result.failed_count > 0) {
      message.warning(`${result.failed_count} 个任务删除失败`)
      console.error('Failed tasks:', result.failed_tasks)
    }

    clearSelection()
    loadTasks()
  } catch (error) {
    message.error('批量删除失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  console.log('TaskManager mounted')
  loadTasks()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped lang="scss">
.task-manager {
  padding: 24px;

  .progress-text {
    margin-left: 8px;
    font-size: 12px;
    color: #666;
  }
}
</style>