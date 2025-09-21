<template>
  <div class="luckysheet-wrapper">
    <!-- 工具栏 -->
    <div class="toolbar" v-if="showToolbar">
      <div class="toolbar-left">
        <a-button type="primary" @click="handleTranslate" :loading="isTranslating">
          <template #icon><TranslationOutlined /></template>
          翻译选中内容
        </a-button>
        <a-button @click="handleSave">
          <template #icon><SaveOutlined /></template>
          保存
        </a-button>
        <a-button @click="handleExport">
          <template #icon><DownloadOutlined /></template>
          导出
        </a-button>
      </div>
      <div class="toolbar-right">
        <a-tag color="blue">{{ stats.totalCells }} 单元格</a-tag>
        <a-tag color="green">{{ stats.translatedCells }} 已翻译</a-tag>
        <a-tag color="orange">{{ stats.pendingCells }} 待翻译</a-tag>
      </div>
    </div>

    <!-- Luckysheet容器 -->
    <div :id="containerId" class="luckysheet-container"></div>

    <!-- 翻译浮层 -->
    <div v-if="showTranslationPopup" class="translation-popup" :style="popupStyle">
      <div class="popup-header">
        <span>AI翻译建议</span>
        <CloseOutlined @click="closeTranslationPopup" />
      </div>
      <div class="popup-content">
        <div class="original-text">
          <label>原文：</label>
          <div>{{ currentCell.original }}</div>
        </div>
        <div class="translation-suggestions">
          <label>翻译建议：</label>
          <a-radio-group v-model:value="selectedTranslation" direction="vertical">
            <a-radio v-for="(suggestion, index) in currentCell.suggestions" :key="index" :value="suggestion.text">
              <div class="suggestion-item">
                <span>{{ suggestion.text }}</span>
                <a-tag size="small" :color="getConfidenceColor(suggestion.confidence)">
                  {{ (suggestion.confidence * 100).toFixed(0) }}%
                </a-tag>
              </div>
            </a-radio>
          </a-radio-group>
        </div>
        <div class="popup-actions">
          <a-button size="small" @click="applyTranslation">应用</a-button>
          <a-button size="small" @click="closeTranslationPopup">取消</a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { TranslationOutlined, SaveOutlined, DownloadOutlined, CloseOutlined } from '@ant-design/icons-vue'
import type { LuckysheetConfig, CellData } from './types'

// Props
const props = defineProps<{
  data?: any[]
  config?: Partial<LuckysheetConfig>
  showToolbar?: boolean
  autoSave?: boolean
  translationApi?: (text: string) => Promise<any>
}>()

// Emits
const emit = defineEmits<{
  save: [data: any]
  change: [data: any]
  cellSelected: [cell: CellData]
}>()

// State
const containerId = ref(`luckysheet-${Date.now()}`)
const isTranslating = ref(false)
const showTranslationPopup = ref(false)
const selectedTranslation = ref('')
const currentCell = ref<any>({})
const popupStyle = ref({})

// 统计数据
const stats = ref({
  totalCells: 0,
  translatedCells: 0,
  pendingCells: 0
})

// Luckysheet实例
let luckysheetInstance: any = null

// 初始化Luckysheet
const initLuckysheet = () => {
  // 等待Luckysheet全局对象加载
  if (typeof window.luckysheet === 'undefined') {
    console.error('Luckysheet not loaded')
    return
  }

  const defaultConfig: LuckysheetConfig = {
    container: containerId.value,
    title: 'Translation Workbench',
    lang: 'zh',
    allowEdit: true,
    showtoolbar: true,
    showinfobar: true,
    showsheetbar: true,
    data: props.data || getDefaultData(),
    // 钩子函数
    hook: {
      // 单元格编辑前
      cellEditBefore: (range: any) => {
        console.log('Cell edit before:', range)
        return true
      },
      // 单元格更新后
      cellUpdated: (r: number, c: number, oldValue: any, newValue: any) => {
        console.log('Cell updated:', { r, c, oldValue, newValue })
        updateStats()
        emit('change', { row: r, col: c, value: newValue })

        // 自动保存
        if (props.autoSave) {
          saveData()
        }
      },
      // 选区变化
      rangeSelect: (range: any) => {
        console.log('Range selected:', range)
        const cell = getCellData(range.row[0], range.column[0])
        emit('cellSelected', cell)
      }
    },
    // 自定义配置
    ...props.config
  }

  // 创建Luckysheet实例
  window.luckysheet.create(defaultConfig)
  luckysheetInstance = window.luckysheet

  // 更新统计
  updateStats()

  // 添加右键菜单
  addCustomContextMenu()
}

// 获取默认数据
const getDefaultData = () => {
  return [{
    name: 'Sheet1',
    color: '',
    index: 0,
    status: 1,
    order: 0,
    celldata: [],
    config: {
      merge: {},
      rowlen: {},
      columnlen: {},
      rowhidden: {},
      colhidden: {}
    }
  }]
}

// 获取单元格数据
const getCellData = (r: number, c: number) => {
  const data = window.luckysheet.getCellValue(r, c)
  return {
    row: r,
    col: c,
    value: data?.v || '',
    display: data?.m || data?.v || ''
  }
}

// 更新统计信息
const updateStats = () => {
  if (!window.luckysheet) return

  const allData = window.luckysheet.getAllSheets()
  let total = 0
  let translated = 0
  let pending = 0

  allData.forEach((sheet: any) => {
    if (sheet.celldata) {
      sheet.celldata.forEach((cell: any) => {
        total++
        // 根据单元格样式或标记判断翻译状态
        if (cell.v && cell.v.includes('[已翻译]')) {
          translated++
        } else if (cell.v && cell.v.includes('[待翻译]')) {
          pending++
        }
      })
    }
  })

  stats.value = { totalCells: total, translatedCells: translated, pendingCells: pending }
}

// 翻译选中内容
const handleTranslate = async () => {
  if (!window.luckysheet) return

  const range = window.luckysheet.getRange()
  if (!range || range.length === 0) {
    message.warning('请先选择要翻译的单元格')
    return
  }

  isTranslating.value = true

  try {
    // 获取选中的单元格
    const cells = []
    for (let r = range[0].row[0]; r <= range[0].row[1]; r++) {
      for (let c = range[0].column[0]; c <= range[0].column[1]; c++) {
        const cellValue = window.luckysheet.getCellValue(r, c)
        if (cellValue?.v) {
          cells.push({ row: r, col: c, text: cellValue.v })
        }
      }
    }

    // 批量翻译
    for (const cell of cells) {
      if (props.translationApi) {
        const result = await props.translationApi(cell.text)
        // 更新单元格（保留原文，添加翻译）
        window.luckysheet.setCellValue(cell.row, cell.col + 1, result.translation)

        // 设置翻译状态样式
        window.luckysheet.setCellFormat(cell.row, cell.col + 1, 'bg', '#e6f7ff')
      }
    }

    message.success(`成功翻译 ${cells.length} 个单元格`)
    updateStats()
  } catch (error) {
    console.error('Translation error:', error)
    message.error('翻译失败')
  } finally {
    isTranslating.value = false
  }
}

// 保存数据
const saveData = () => {
  if (!window.luckysheet) return

  const data = window.luckysheet.getAllSheets()
  emit('save', data)
  message.success('保存成功')
}

// 处理保存
const handleSave = () => {
  saveData()
}

// 导出Excel
const handleExport = () => {
  if (!window.luckysheet) return

  // 使用luckyexcel导出
  window.luckysheet.exportExcel({
    filename: `translation_${Date.now()}`,
    sheetName: 'Sheet1'
  })
}

// 添加自定义右键菜单
const addCustomContextMenu = () => {
  if (!window.luckysheet) return

  // 扩展右键菜单
  const customMenus = [
    {
      text: '翻译此单元格',
      onclick: () => {
        showCellTranslation()
      }
    },
    {
      text: '标记为已翻译',
      onclick: () => {
        markAsTranslated()
      }
    },
    {
      text: '查看翻译历史',
      onclick: () => {
        showTranslationHistory()
      }
    }
  ]

  // 注入自定义菜单（需要修改Luckysheet源码或使用插件机制）
  console.log('Custom menus ready:', customMenus)
}

// 显示单元格翻译
const showCellTranslation = async () => {
  const range = window.luckysheet.getRange()
  if (!range || range.length === 0) return

  const r = range[0].row[0]
  const c = range[0].column[0]
  const cellValue = window.luckysheet.getCellValue(r, c)

  if (!cellValue?.v) {
    message.warning('单元格为空')
    return
  }

  // 获取翻译建议
  if (props.translationApi) {
    const result = await props.translationApi(cellValue.v)

    currentCell.value = {
      row: r,
      col: c,
      original: cellValue.v,
      suggestions: result.suggestions || [
        { text: result.translation, confidence: 0.95 }
      ]
    }

    // 显示浮层
    showTranslationPopup.value = true

    // 计算浮层位置
    const cellPos = window.luckysheet.getCellPosition(r, c)
    popupStyle.value = {
      top: `${cellPos.top + 30}px`,
      left: `${cellPos.left}px`
    }
  }
}

// 标记为已翻译
const markAsTranslated = () => {
  const range = window.luckysheet.getRange()
  if (!range || range.length === 0) return

  for (let r = range[0].row[0]; r <= range[0].row[1]; r++) {
    for (let c = range[0].column[0]; c <= range[0].column[1]; c++) {
      window.luckysheet.setCellFormat(r, c, 'bg', '#f6ffed')
    }
  }

  updateStats()
  message.success('已标记为翻译完成')
}

// 显示翻译历史
const showTranslationHistory = () => {
  // TODO: 实现翻译历史功能
  message.info('翻译历史功能开发中')
}

// 应用翻译
const applyTranslation = () => {
  if (!selectedTranslation.value) {
    message.warning('请选择一个翻译')
    return
  }

  window.luckysheet.setCellValue(
    currentCell.value.row,
    currentCell.value.col + 1,
    selectedTranslation.value
  )

  closeTranslationPopup()
  message.success('翻译已应用')
}

// 关闭翻译浮层
const closeTranslationPopup = () => {
  showTranslationPopup.value = false
  selectedTranslation.value = ''
  currentCell.value = {}
}

// 获取置信度颜色
const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.9) return 'green'
  if (confidence >= 0.7) return 'orange'
  return 'red'
}

// 生命周期
onMounted(() => {
  // 加载Luckysheet CSS和JS
  loadLuckysheetResources().then(() => {
    initLuckysheet()
  })
})

onUnmounted(() => {
  // 清理Luckysheet实例
  if (window.luckysheet) {
    window.luckysheet.destroy()
  }
})

// 加载Luckysheet资源
const loadLuckysheetResources = async () => {
  return new Promise((resolve) => {
    // 检查是否已加载
    if (window.luckysheet) {
      resolve(true)
      return
    }

    // 加载CSS
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/plugins/css/pluginsCss.min.css'
    document.head.appendChild(link)

    const link2 = document.createElement('link')
    link2.rel = 'stylesheet'
    link2.href = 'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/css/luckysheet.min.css'
    document.head.appendChild(link2)

    // 加载JS
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/luckysheet.umd.min.js'
    script.onload = () => {
      console.log('Luckysheet loaded successfully')
      resolve(true)
    }
    document.body.appendChild(script)
  })
}

// 暴露方法
defineExpose({
  refresh: () => {
    if (window.luckysheet) {
      window.luckysheet.refresh()
    }
  },
  getData: () => {
    if (window.luckysheet) {
      return window.luckysheet.getAllSheets()
    }
    return null
  },
  setData: (data: any) => {
    if (window.luckysheet) {
      window.luckysheet.loadData(data)
    }
  }
})
</script>

<style scoped lang="scss">
.luckysheet-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

  .toolbar {
    height: 56px;
    padding: 0 16px;
    background: #fff;
    border-bottom: 1px solid #e8e8e8;
    display: flex;
    align-items: center;
    justify-content: space-between;

    .toolbar-left {
      display: flex;
      gap: 8px;
    }

    .toolbar-right {
      display: flex;
      gap: 8px;
    }
  }

  .luckysheet-container {
    flex: 1;
    width: 100%;
    position: relative;
  }

  .translation-popup {
    position: absolute;
    z-index: 10000;
    background: white;
    border: 1px solid #d9d9d9;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    width: 400px;
    padding: 0;

    .popup-header {
      padding: 12px 16px;
      border-bottom: 1px solid #f0f0f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 500;
    }

    .popup-content {
      padding: 16px;

      .original-text {
        margin-bottom: 16px;

        label {
          font-weight: 500;
          display: block;
          margin-bottom: 8px;
        }

        div {
          padding: 8px;
          background: #f5f5f5;
          border-radius: 4px;
        }
      }

      .translation-suggestions {
        margin-bottom: 16px;

        label {
          font-weight: 500;
          display: block;
          margin-bottom: 8px;
        }

        .suggestion-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 4px 0;
        }
      }

      .popup-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        padding-top: 8px;
        border-top: 1px solid #f0f0f0;
      }
    }
  }
}

// 全局Luckysheet样式覆盖
:global(.luckysheet) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

:global(.luckysheet-cell-selected) {
  border-color: #1890ff !important;
}
</style>