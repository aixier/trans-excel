<template>
  <div class="terminology-container">
    <!-- 顶部操作栏 -->
    <div class="toolbar">
      <a-space>
        <a-button type="primary" @click="showAddModal">
          <PlusOutlined />
          添加术语
        </a-button>
        <a-upload
          :show-upload-list="false"
          :before-upload="handleFileUpload"
          accept=".json,.xlsx,.xls"
        >
          <a-button>
            <UploadOutlined />
            导入术语表
          </a-button>
        </a-upload>
        <a-button @click="exportTerminology">
          <DownloadOutlined />
          导出JSON
        </a-button>
        <a-button
          danger
          :disabled="selectedRowKeys.length === 0"
          @click="handleBatchDelete"
        >
          <DeleteOutlined />
          批量删除 ({{ selectedRowKeys.length }})
        </a-button>
      </a-space>

      <a-space style="margin-left: auto">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索术语..."
          style="width: 250px"
          @search="handleSearch"
          allow-clear
        />
        <a-select
          v-model:value="selectedCategory"
          placeholder="筛选分类"
          style="width: 150px"
          allow-clear
          @change="handleCategoryChange"
        >
          <a-select-option :value="null">全部分类</a-select-option>
          <a-select-option v-for="cat in categories" :key="cat" :value="cat">
            {{ cat }}
          </a-select-option>
        </a-select>
      </a-space>
    </div>

    <!-- 术语表格 -->
    <a-table
      :columns="columns"
      :data-source="terminologyList"
      :loading="loading"
      :pagination="pagination"
      :row-selection="rowSelection"
      :row-key="record => record.id"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'source'">
          <a-typography-text strong>{{ record.source }}</a-typography-text>
        </template>
        <template v-else-if="column.key === 'translations'">
          <div class="translations-cell">
            <a-tag v-for="(translation, lang) in record.target_translations" :key="lang">
              <span class="lang-code">{{ lang }}:</span> {{ translation }}
            </a-tag>
          </div>
        </template>
        <template v-else-if="column.key === 'category'">
          <a-tag :color="getCategoryColor(record.category)">
            {{ record.category || '未分类' }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'case_sensitive'">
          <a-tag :color="record.case_sensitive ? 'red' : 'default'">
            {{ record.case_sensitive ? '区分大小写' : '不区分' }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="editTerminology(record)">
              编辑
            </a-button>
            <a-popconfirm
              title="确定要删除这个术语吗？"
              @confirm="deleteTerminology(record.id)"
            >
              <a-button type="link" size="small" danger>
                删除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 添加/编辑术语弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑术语' : '添加术语'"
      :width="700"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
    >
      <a-form
        :model="formState"
        :label-col="{ span: 4 }"
        :wrapper-col="{ span: 20 }"
      >
        <a-form-item label="源语言" :rules="[{ required: true }]">
          <a-input
            v-model:value="formState.source"
            placeholder="输入源语言术语"
          />
        </a-form-item>

        <a-form-item label="目标翻译">
          <div class="translation-inputs">
            <div v-for="lang in targetLanguages" :key="lang.code" class="translation-input">
              <span class="lang-label">{{ lang.name }}:</span>
              <a-input
                v-model:value="formState.target_translations[lang.code]"
                :placeholder="`${lang.name}翻译`"
              />
            </div>
          </div>
        </a-form-item>

        <a-form-item label="分类">
          <a-auto-complete
            v-model:value="formState.category"
            :options="categoryOptions"
            placeholder="选择或输入分类"
          />
        </a-form-item>

        <a-form-item label="上下文">
          <a-textarea
            v-model:value="formState.context"
            placeholder="可选：提供术语使用的上下文信息"
            :rows="3"
          />
        </a-form-item>

        <a-form-item label="大小写">
          <a-switch v-model:checked="formState.case_sensitive" />
          <span style="margin-left: 8px">
            {{ formState.case_sensitive ? '区分大小写' : '不区分大小写' }}
          </span>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 导入结果弹窗 -->
    <a-modal
      v-model:open="importResultVisible"
      title="导入结果"
      :footer="null"
      width="600px"
    >
      <a-result
        :status="importResult.failed > 0 ? 'warning' : 'success'"
        :title="`成功导入 ${importResult.success} 条术语`"
        :sub-title="importResult.failed > 0 ? `失败 ${importResult.failed} 条` : ''"
      >
        <template #extra v-if="importResult.errors.length > 0">
          <div class="import-errors">
            <h4>错误详情:</h4>
            <a-list
              size="small"
              :data-source="importResult.errors"
            >
              <template #renderItem="{ item }">
                <a-list-item>{{ item }}</a-list-item>
              </template>
            </a-list>
          </div>
        </template>
      </a-result>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  UploadOutlined,
  DownloadOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { terminologyAPI, type TerminologyItem } from '@/api/endpoints/terminology'

// 目标语言配置
const targetLanguages = [
  { code: 'en', name: '英语' },
  { code: 'pt', name: '葡萄牙语' },
  { code: 'es', name: '西班牙语' },
  { code: 'th', name: '泰语' },
  { code: 'ind', name: '印尼语' },
  { code: 'vn', name: '越南语' },
  { code: 'tr', name: '土耳其语' }
]

// 状态
const loading = ref(false)
const terminologyList = ref<TerminologyItem[]>([])
const categories = ref<string[]>([])
const selectedCategory = ref<string | null>(null)
const searchText = ref('')
const selectedRowKeys = ref<string[]>([])

// 弹窗状态
const modalVisible = ref(false)
const isEdit = ref(false)
const currentEditId = ref<string>('')

// 导入结果
const importResultVisible = ref(false)
const importResult = ref({
  total: 0,
  success: 0,
  failed: 0,
  errors: [] as string[]
})

// 表单状态
const formState = reactive<any>({
  source: '',
  target_translations: {},
  category: 'general',
  context: '',
  case_sensitive: false
})

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100']
})

// 表格列配置
const columns = [
  {
    title: '源语言',
    dataIndex: 'source',
    key: 'source',
    width: 200,
    fixed: 'left'
  },
  {
    title: '目标翻译',
    key: 'translations',
    ellipsis: true
  },
  {
    title: '分类',
    dataIndex: 'category',
    key: 'category',
    width: 120
  },
  {
    title: '大小写',
    dataIndex: 'case_sensitive',
    key: 'case_sensitive',
    width: 120
  },
  {
    title: '操作',
    key: 'action',
    width: 120,
    fixed: 'right'
  }
]

// 行选择配置
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: string[]) => {
    selectedRowKeys.value = keys
  }
}))

// 分类选项
const categoryOptions = computed(() => {
  return categories.value.map(cat => ({ value: cat, label: cat }))
})

// 获取分类颜色
const getCategoryColor = (category?: string) => {
  const colorMap: Record<string, string> = {
    general: 'blue',
    ui: 'green',
    item: 'orange',
    skill: 'purple',
    character: 'cyan',
    imported: 'default'
  }
  return colorMap[category || ''] || 'default'
}

// 加载术语列表
const loadTerminology = async () => {
  loading.value = true
  try {
    const params = {
      limit: pagination.pageSize,
      offset: (pagination.current - 1) * pagination.pageSize,
      category: selectedCategory.value || undefined,
      search: searchText.value || undefined
    }
    const data = await terminologyAPI.list(params)
    terminologyList.value = data
    pagination.total = data.length // 实际应该从后端返回总数
  } catch (error) {
    message.error('加载术语列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 加载分类列表
const loadCategories = async () => {
  try {
    categories.value = await terminologyAPI.getCategories()
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
}

// 表格变化处理
const handleTableChange = (paginationConfig: any) => {
  pagination.current = paginationConfig.current
  pagination.pageSize = paginationConfig.pageSize
  loadTerminology()
}

// 搜索处理
const handleSearch = () => {
  pagination.current = 1
  loadTerminology()
}

// 分类筛选处理
const handleCategoryChange = () => {
  pagination.current = 1
  loadTerminology()
}

// 显示添加弹窗
const showAddModal = () => {
  isEdit.value = false
  currentEditId.value = ''
  Object.assign(formState, {
    source: '',
    target_translations: {},
    category: 'general',
    context: '',
    case_sensitive: false
  })
  modalVisible.value = true
}

// 编辑术语
const editTerminology = (record: TerminologyItem) => {
  isEdit.value = true
  currentEditId.value = record.id || ''
  Object.assign(formState, {
    source: record.source,
    target_translations: { ...record.target_translations },
    category: record.category || 'general',
    context: record.context || '',
    case_sensitive: record.case_sensitive || false
  })
  modalVisible.value = true
}

// 处理弹窗确认
const handleModalOk = async () => {
  try {
    if (!formState.source) {
      message.error('请输入源语言术语')
      return
    }

    // 过滤空的翻译
    const translations: Record<string, string> = {}
    Object.entries(formState.target_translations).forEach(([key, value]) => {
      if (value) translations[key] = value as string
    })

    if (Object.keys(translations).length === 0) {
      message.error('请至少输入一个目标翻译')
      return
    }

    const data = {
      source: formState.source,
      target_translations: translations,
      category: formState.category,
      context: formState.context,
      case_sensitive: formState.case_sensitive
    }

    if (isEdit.value) {
      await terminologyAPI.update(currentEditId.value, data)
      message.success('术语更新成功')
    } else {
      await terminologyAPI.create(data)
      message.success('术语添加成功')
    }

    modalVisible.value = false
    loadTerminology()
  } catch (error) {
    message.error('操作失败')
    console.error(error)
  }
}

// 处理弹窗取消
const handleModalCancel = () => {
  modalVisible.value = false
}

// 删除术语
const deleteTerminology = async (id?: string) => {
  if (!id) return

  try {
    await terminologyAPI.delete(id)
    message.success('删除成功')
    loadTerminology()
  } catch (error) {
    message.error('删除失败')
    console.error(error)
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedRowKeys.value.length === 0) return

  try {
    await terminologyAPI.batchDelete(selectedRowKeys.value)
    message.success(`成功删除 ${selectedRowKeys.value.length} 条术语`)
    selectedRowKeys.value = []
    loadTerminology()
  } catch (error) {
    message.error('批量删除失败')
    console.error(error)
  }
}

// 文件上传处理
const handleFileUpload = async (file: File) => {
  const isJson = file.name.endsWith('.json')
  const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls')

  if (!isJson && !isExcel) {
    message.error('只支持 JSON 或 Excel 格式文件')
    return false
  }

  try {
    loading.value = true
    let result

    if (isJson) {
      result = await terminologyAPI.importJson(file)
    } else {
      result = await terminologyAPI.importExcel(file)
    }

    importResult.value = result
    importResultVisible.value = true

    if (result.success > 0) {
      loadTerminology()
    }
  } catch (error) {
    message.error('导入失败')
    console.error(error)
  } finally {
    loading.value = false
  }

  return false
}

// 导出术语表
const exportTerminology = async () => {
  try {
    const data = await terminologyAPI.exportJson(
      undefined,
      selectedCategory.value || undefined
    )
    terminologyAPI.downloadJson(data, `terminology_${new Date().toISOString().split('T')[0]}.json`)
    message.success('导出成功')
  } catch (error) {
    message.error('导出失败')
    console.error(error)
  }
}

// 初始化
onMounted(() => {
  loadTerminology()
  loadCategories()
})
</script>

<style scoped lang="scss">
.terminology-container {
  padding: 24px;
  background: #fff;
  min-height: calc(100vh - 64px);

  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;
  }

  .translations-cell {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;

    .lang-code {
      font-weight: 600;
      text-transform: uppercase;
    }
  }

  .translation-inputs {
    display: flex;
    flex-direction: column;
    gap: 12px;

    .translation-input {
      display: flex;
      align-items: center;
      gap: 8px;

      .lang-label {
        min-width: 80px;
        font-weight: 500;
      }
    }
  }

  .import-errors {
    text-align: left;
    margin-top: 16px;

    h4 {
      margin-bottom: 8px;
    }
  }
}
</style>