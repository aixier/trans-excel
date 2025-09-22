<template>
  <div class="quick-translate-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>快速翻译</h2>
      <p>上传Excel文件，快速获取AI翻译结果</p>
    </div>

    <!-- 上传区域 -->
    <a-card class="upload-card" v-if="!currentTask">
      <a-upload-dragger
        v-model:fileList="fileList"
        :multiple="false"
        :before-upload="beforeUpload"
        accept=".xlsx,.xls"
        @drop="handleDrop"
      >
        <p class="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p class="ant-upload-hint">
          支持 Excel 文件（.xlsx, .xls），文件大小不超过 100MB
        </p>
      </a-upload-dragger>

      <!-- 翻译配置 -->
      <div class="config-section" v-if="fileList.length > 0">
        <a-divider />
        <h3>翻译配置</h3>

        <a-form :model="translationConfig" layout="vertical">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="目标语言" required>
                <a-select
                  v-model:value="translationConfig.targetLanguages"
                  mode="multiple"
                  placeholder="请选择目标语言"
                  style="width: 100%"
                >
                  <a-select-option value="pt">葡萄牙语</a-select-option>
                  <a-select-option value="th">泰语</a-select-option>
                  <a-select-option value="ind">印尼语</a-select-option>
                  <a-select-option value="es">西班牙语</a-select-option>
                  <a-select-option value="vn">越南语</a-select-option>
                  <a-select-option value="tr">土耳其语</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>

            <a-col :span="12">
              <a-form-item label="目标地区">
                <a-select
                  v-model:value="translationConfig.region"
                  placeholder="选择目标地区（可选）"
                  style="width: 100%"
                >
                  <a-select-option value="na">北美</a-select-option>
                  <a-select-option value="sa">南美</a-select-option>
                  <a-select-option value="eu">欧洲</a-select-option>
                  <a-select-option value="me">中东</a-select-option>
                  <a-select-option value="as">东南亚</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="游戏背景描述">
            <a-textarea
              v-model:value="translationConfig.gameBackground"
              placeholder="请描述游戏类型、世界观、角色背景等信息，帮助AI更准确地翻译"
              :rows="3"
            />
          </a-form-item>

          <a-form-item label="高级设置">
            <a-collapse>
              <a-collapse-panel key="1" header="查看高级选项">
                <a-row :gutter="16">
                  <a-col :span="8">
                    <a-form-item label="批次大小">
                      <a-input-number
                        v-model:value="translationConfig.batchSize"
                        :min="1"
                        :max="30"
                        style="width: 100%"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="8">
                    <a-form-item label="并发数">
                      <a-input-number
                        v-model:value="translationConfig.maxConcurrent"
                        :min="1"
                        :max="20"
                        style="width: 100%"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="8">
                    <a-form-item label="重试次数">
                      <a-input-number
                        v-model:value="translationConfig.retryCount"
                        :min="0"
                        :max="5"
                        style="width: 100%"
                      />
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-space direction="vertical" style="width: 100%">
                  <a-checkbox v-model:checked="translationConfig.preservePlaceholders">
                    保护占位符（%s, %d, {num}, \n, 标签等）
                  </a-checkbox>
                  <a-checkbox v-model:checked="translationConfig.useTerminology">
                    使用术语库进行一致性检查
                  </a-checkbox>
                  <a-checkbox v-model:checked="translationConfig.enableIterative">
                    启用迭代翻译（自动检测并翻译新出现的文本）
                  </a-checkbox>
                  <a-checkbox v-model:checked="translationConfig.twoStepTranslation">
                    使用两步翻译策略（中文→英文→目标语言）
                  </a-checkbox>
                </a-space>
              </a-collapse-panel>
            </a-collapse>
          </a-form-item>

          <a-form-item>
            <a-space>
              <a-button type="primary" @click="startTranslation" :loading="uploading">
                <template #icon><CloudUploadOutlined /></template>
                开始翻译
              </a-button>
              <a-button @click="resetForm">重置</a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </div>
    </a-card>

    <!-- 翻译进度 -->
    <a-card class="progress-card" v-if="currentTask">
      <div class="progress-header">
        <h3>翻译进度</h3>
        <a-space>
          <a-button @click="pauseTask" v-if="!currentTask.paused">
            <template #icon><PauseCircleOutlined /></template>
            暂停
          </a-button>
          <a-button @click="resumeTask" v-else>
            <template #icon><PlayCircleOutlined /></template>
            继续
          </a-button>
          <a-button danger @click="cancelTask">
            <template #icon><CloseCircleOutlined /></template>
            取消
          </a-button>
        </a-space>
      </div>

      <!-- 总体进度 -->
      <div class="overall-progress">
        <div class="progress-info">
          <span>总进度</span>
          <span>{{ currentTask.progress }}%</span>
        </div>
        <a-progress
          :percent="currentTask.progress"
          :status="currentTask.status"
        />
        <div class="progress-detail">
          已翻译 {{ currentTask.translated }} / {{ currentTask.total }} 条
        </div>
      </div>

      <!-- 迭代进度 -->
      <div class="iteration-progress" v-if="currentTask.iterations">
        <h4>迭代进度</h4>
        <a-timeline>
          <a-timeline-item
            v-for="iter in currentTask.iterations"
            :key="iter.round"
            :color="iter.status === 'completed' ? 'green' : iter.status === 'processing' ? 'blue' : 'gray'"
          >
            <div class="iteration-item">
              <div class="iter-header">
                <span>第 {{ iter.round }} 轮迭代</span>
                <a-tag :color="iter.status === 'completed' ? 'success' : 'processing'">
                  {{ iter.status === 'completed' ? '已完成' : '处理中' }}
                </a-tag>
              </div>
              <div class="iter-stats">
                发现 {{ iter.found }} 条新文本，已翻译 {{ iter.translated }} 条
              </div>
              <a-progress
                :percent="iter.progress"
                size="small"
                :show-info="false"
              />
            </div>
          </a-timeline-item>
        </a-timeline>
      </div>

      <!-- 实时日志 -->
      <div class="log-section">
        <h4>
          实时日志
          <a-switch
            v-model:checked="autoScroll"
            checked-children="自动滚动"
            un-checked-children="手动"
            size="small"
          />
        </h4>
        <div class="log-container" ref="logContainer">
          <div v-for="log in logs" :key="log.id" class="log-item" :class="`log-${log.level}`">
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons" v-if="currentTask.status === 'completed'">
        <a-space>
          <a-button type="primary" @click="downloadResult">
            <template #icon><DownloadOutlined /></template>
            下载翻译结果
          </a-button>
          <a-button @click="viewDetails">查看详情</a-button>
          <a-button @click="startNew">开始新任务</a-button>
        </a-space>
      </div>
    </a-card>

    <!-- 历史记录 -->
    <a-card class="history-card" title="最近翻译记录">
      <a-table
        :columns="historyColumns"
        :data-source="historyData"
        :pagination="{ pageSize: 5 }"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="downloadHistory(record)">
                下载
              </a-button>
              <a-button type="link" size="small" @click="viewHistory(record)">
                详情
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  InboxOutlined,
  CloudUploadOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  CloseCircleOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue'
import { translationAPI } from '@/api/endpoints/translation'

// 文件列表
const fileList = ref<any[]>([])

// 翻译配置
const translationConfig = ref({
  targetLanguages: ['pt', 'th'],
  region: 'as',
  gameBackground: '',
  batchSize: 10,
  maxConcurrent: 5,
  retryCount: 3,
  preservePlaceholders: true,
  useTerminology: true,
  enableIterative: true,
  twoStepTranslation: false
})

// 当前任务
const currentTask = ref<any>(null)

// 日志
const logs = ref<any[]>([])
const autoScroll = ref(true)
const logContainer = ref<HTMLElement>()

// 上传状态
const uploading = ref(false)

// 轮询定时器
let pollTimer: any = null

// 历史记录列
const historyColumns = [
  {
    title: '文件名',
    dataIndex: 'fileName',
    key: 'fileName'
  },
  {
    title: '语言',
    dataIndex: 'languages',
    key: 'languages',
    render: (languages: string[]) => languages.join(', ')
  },
  {
    title: '状态',
    key: 'status',
    dataIndex: 'status'
  },
  {
    title: '完成时间',
    dataIndex: 'completedTime',
    key: 'completedTime'
  },
  {
    title: '操作',
    key: 'action'
  }
]

// 历史数据
const historyData = ref<any[]>([])

// 加载历史记录
const loadHistory = async () => {
  try {
    const response = await fetch('/api/translation/tasks?status=completed&limit=10')
    if (response.ok) {
      const data = await response.json()
      historyData.value = data.tasks || []
    }
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

// 文件上传前处理
const beforeUpload = (file: File) => {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                  file.type === 'application/vnd.ms-excel'
  if (!isExcel) {
    message.error('只能上传Excel文件！')
    return false
  }

  const isLt100M = file.size / 1024 / 1024 < 100
  if (!isLt100M) {
    message.error('文件大小不能超过100MB！')
    return false
  }

  fileList.value = [file]
  return false // 阻止自动上传
}

// 处理拖放
const handleDrop = (e: DragEvent) => {
  console.log('Dropped files', e.dataTransfer?.files)
}

// 开始翻译
const startTranslation = async () => {
  if (fileList.value.length === 0) {
    message.warning('请先选择文件')
    return
  }

  if (translationConfig.value.targetLanguages.length === 0) {
    message.warning('请选择至少一种目标语言')
    return
  }

  uploading.value = true
  try {
    // 获取实际的File对象
    // Ant Design Vue的Upload组件可能会包装File对象
    const fileObj = fileList.value[0].originFileObj || fileList.value[0]

    // 确保是File对象
    if (!(fileObj instanceof File)) {
      throw new Error('Invalid file object')
    }

    // 调用真实API
    const response = await translationAPI.uploadFile({
      file: fileObj,
      config: {
        ...translationConfig.value,
        regionCode: translationConfig.value.region,
        autoDetect: true
      }
    })

    // 创建任务 - 适配后端返回的数据结构
    currentTask.value = {
      id: response.task_id || response.id,
      fileName: fileObj.name,
      status: response.status || 'uploading',
      progress: 0,
      total: response.totalRows || 100, // 如果没有totalRows，默认100
      translated: 0,
      paused: false,
      iterations: []
    }

    // 开始轮询进度
    startPolling()

    // 添加日志
    addLog('info', `任务创建成功，任务ID: ${response.task_id || response.id}`)
    addLog('info', response.message || '翻译任务已启动')
    addLog('info', `文件: ${fileObj.name}`)
    addLog('info', `目标语言: ${translationConfig.value.targetLanguages.join(', ')}`)
  } catch (error) {
    message.error('上传失败，请重试')
    console.error(error)
  } finally {
    uploading.value = false
  }
}

// 开始轮询
const startPolling = () => {
  pollTimer = setInterval(async () => {
    try {
      const response = await translationAPI.getTaskProgress(currentTask.value.id)

      // 更新任务状态 - 适配后端返回的数据结构
      if (response.progress) {
        currentTask.value.progress = Math.round((response.progress.translated_rows / response.progress.total_rows) * 100) || 0
        currentTask.value.translated = response.progress.translated_rows || 0
        currentTask.value.total = response.progress.total_rows || currentTask.value.total

        // 更新迭代信息
        if (response.progress.current_iteration) {
          const iterIndex = response.progress.current_iteration - 1
          if (!currentTask.value.iterations[iterIndex]) {
            currentTask.value.iterations[iterIndex] = {
              round: response.progress.current_iteration,
              status: 'processing',
              found: 0,
              translated: 0,
              progress: 0
            }
          }
          currentTask.value.iterations[iterIndex].translated = response.progress.translated_rows
          currentTask.value.iterations[iterIndex].progress = currentTask.value.progress
        }
      }

      currentTask.value.status = response.status

      // 添加日志
      if (response.progress && response.progress.translated_rows > 0) {
        const percentage = currentTask.value.progress
        // 每10%或每翻译10条记录一次
        if (percentage > 0 && (percentage % 10 === 0 || response.progress.translated_rows % 10 === 0)) {
          addLog('info', `翻译进度: ${percentage}% (${response.progress.translated_rows}/${response.progress.total_rows})，当前迭代: ${response.progress.current_iteration}/${response.progress.max_iterations}`)
        }
      }

      // 检查是否完成
      if (response.status === 'completed' || response.status === 'failed') {
        stopPolling()
        if (response.status === 'completed') {
          message.success('翻译完成！')
          addLog('success', '所有翻译任务已完成')
        } else {
          message.error('翻译失败')
          addLog('error', response.errorMessage || '翻译任务失败')
        }
      }
    } catch (error: any) {
      console.error('轮询失败', error)
      // 如果是超时或网络错误，继续轮询
      if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
        // 网络超时，继续轮询
        return
      }
      // 其他错误停止轮询
      if (error.response?.status === 404) {
        addLog('warning', '任务不存在或已完成')
        stopPolling()
      }
    }
  }, 5000) // 每5秒轮询一次，避免过于频繁
}

// 停止轮询
const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 添加日志
const addLog = (level: string, message: string) => {
  logs.value.push({
    id: Date.now(),
    level,
    time: new Date().toLocaleTimeString(),
    message
  })

  // 自动滚动
  if (autoScroll.value && logContainer.value) {
    setTimeout(() => {
      logContainer.value!.scrollTop = logContainer.value!.scrollHeight
    }, 100)
  }
}

// 暂停任务
const pauseTask = () => {
  currentTask.value.paused = true
  stopPolling()
  addLog('warning', '任务已暂停')
}

// 恢复任务
const resumeTask = () => {
  currentTask.value.paused = false
  startPolling()
  addLog('info', '任务已恢复')
}

// 取消任务
const cancelTask = async () => {
  try {
    await translationAPI.cancelTask(currentTask.value.id)
    stopPolling()
    currentTask.value = null
    message.success('任务已取消')
  } catch (error) {
    message.error('取消失败')
  }
}

// 下载结果
const downloadResult = async () => {
  try {
    await translationAPI.downloadResult(currentTask.value.id)
    message.success('开始下载')
  } catch (error) {
    message.error('下载失败')
  }
}

// 查看详情
const viewDetails = () => {
  // 跳转到任务详情页
  console.log('View details')
}

// 开始新任务
const startNew = () => {
  currentTask.value = null
  fileList.value = []
  logs.value = []
}

// 重置表单
const resetForm = () => {
  fileList.value = []
  translationConfig.value = {
    targetLanguages: ['pt', 'th'],
    region: 'as',
    gameBackground: '',
    batchSize: 10,
    maxConcurrent: 5,
    retryCount: 3,
    preservePlaceholders: true,
    useTerminology: true,
    enableIterative: true,
    twoStepTranslation: false
  }
}

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

// 下载历史记录
const downloadHistory = (record: any) => {
  message.success(`开始下载 ${record.fileName}`)
}

// 查看历史记录
const viewHistory = (record: any) => {
  console.log('View history', record)
}

// 生命周期
onMounted(() => {
  console.log('QuickTranslate mounted')
  loadHistory()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="scss">
.quick-translate-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;

  .page-header {
    margin-bottom: 24px;

    h2 {
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: 600;
    }

    p {
      margin: 0;
      color: #666;
    }
  }

  .upload-card {
    margin-bottom: 24px;

    .config-section {
      margin-top: 24px;

      h3 {
        margin-bottom: 16px;
        font-size: 16px;
        font-weight: 500;
      }
    }
  }

  .progress-card {
    margin-bottom: 24px;

    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;

      h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
      }
    }

    .overall-progress {
      margin-bottom: 32px;

      .progress-info {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 14px;
      }

      .progress-detail {
        margin-top: 8px;
        font-size: 12px;
        color: #666;
      }
    }

    .iteration-progress {
      margin-bottom: 32px;

      h4 {
        margin-bottom: 16px;
        font-size: 14px;
        font-weight: 500;
      }

      .iteration-item {
        .iter-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .iter-stats {
          margin-bottom: 8px;
          font-size: 12px;
          color: #666;
        }
      }
    }

    .log-section {
      margin-bottom: 24px;

      h4 {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-size: 14px;
        font-weight: 500;
      }

      .log-container {
        height: 200px;
        overflow-y: auto;
        background: #f5f5f5;
        border-radius: 4px;
        padding: 12px;

        .log-item {
          margin-bottom: 8px;
          font-size: 12px;
          font-family: monospace;

          .log-time {
            margin-right: 8px;
            color: #999;
          }

          &.log-info {
            color: #333;
          }

          &.log-success {
            color: #52c41a;
          }

          &.log-warning {
            color: #faad14;
          }

          &.log-error {
            color: #f5222d;
          }
        }
      }
    }

    .action-buttons {
      text-align: center;
      padding-top: 24px;
      border-top: 1px solid #f0f0f0;
    }
  }

  .history-card {
    // 历史记录卡片样式
  }
}

// 响应式布局
@media (max-width: 768px) {
  .quick-translate-container {
    padding: 16px;
  }
}
</style>