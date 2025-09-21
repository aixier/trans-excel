<template>
  <div class="translation-workspace">
    <!-- 头部操作栏 -->
    <div class="workspace-header">
      <div class="header-left">
        <h2>翻译工作台</h2>
        <a-breadcrumb>
          <a-breadcrumb-item>首页</a-breadcrumb-item>
          <a-breadcrumb-item>翻译管理</a-breadcrumb-item>
          <a-breadcrumb-item>工作台</a-breadcrumb-item>
        </a-breadcrumb>
      </div>
      <div class="header-right">
        <a-space>
          <a-upload
            :show-upload-list="false"
            :before-upload="handleFileUpload"
            accept=".xlsx,.xls"
          >
            <a-button type="primary">
              <template #icon><UploadOutlined /></template>
              上传Excel
            </a-button>
          </a-upload>
          <a-button @click="showSettings">
            <template #icon><SettingOutlined /></template>
            翻译设置
          </a-button>
        </a-space>
      </div>
    </div>

    <!-- 主工作区 -->
    <div class="workspace-body">
      <!-- Luckysheet编辑器 -->
      <LuckysheetWrapper
        ref="luckysheetRef"
        :data="sheetData"
        :config="luckysheetConfig"
        :show-toolbar="true"
        :auto-save="true"
        :translation-api="handleTranslateCell"
        @save="handleSave"
        @change="handleCellChange"
        @cellSelected="handleCellSelected"
      />

      <!-- 右侧辅助面板 -->
      <div class="assist-panel" v-if="showAssistPanel">
        <a-tabs v-model:activeKey="activeTab">
          <!-- 翻译历史 -->
          <a-tab-pane key="history" tab="翻译历史">
            <div class="history-list">
              <a-timeline>
                <a-timeline-item v-for="item in translationHistory" :key="item.id">
                  <template #dot>
                    <CheckCircleOutlined style="color: #52c41a" />
                  </template>
                  <div class="history-item">
                    <div class="history-text">{{ item.original }} → {{ item.translation }}</div>
                    <div class="history-meta">{{ item.time }} · {{ item.language }}</div>
                  </div>
                </a-timeline-item>
              </a-timeline>
            </div>
          </a-tab-pane>

          <!-- 术语库 -->
          <a-tab-pane key="glossary" tab="术语库">
            <div class="glossary-list">
              <a-input-search
                v-model:value="glossarySearch"
                placeholder="搜索术语"
                style="margin-bottom: 16px"
              />
              <a-list :data-source="filteredGlossary" size="small">
                <template #renderItem="{ item }">
                  <a-list-item>
                    <a-list-item-meta>
                      <template #title>{{ item.source }}</template>
                      <template #description>
                        <a-tag v-for="(trans, lang) in item.translations" :key="lang">
                          {{ lang }}: {{ trans }}
                        </a-tag>
                      </template>
                    </a-list-item-meta>
                  </a-list-item>
                </template>
              </a-list>
            </div>
          </a-tab-pane>

          <!-- 进度统计 -->
          <a-tab-pane key="stats" tab="统计">
            <div class="stats-panel">
              <a-statistic-group>
                <a-statistic title="总单元格" :value="statistics.total" />
                <a-statistic title="已翻译" :value="statistics.translated" :value-style="{ color: '#3f8600' }" />
                <a-statistic title="待翻译" :value="statistics.pending" :value-style="{ color: '#cf1322' }" />
              </a-statistic-group>

              <a-divider />

              <div class="progress-section">
                <h4>翻译进度</h4>
                <a-progress :percent="translationProgress" status="active" />
              </div>

              <a-divider />

              <div class="language-stats">
                <h4>语言分布</h4>
                <a-space direction="vertical" style="width: 100%">
                  <div v-for="lang in languageStats" :key="lang.code">
                    <span>{{ lang.name }}</span>
                    <a-progress :percent="lang.progress" size="small" />
                  </div>
                </a-space>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>

    <!-- 翻译设置弹窗 -->
    <a-modal
      v-model:open="settingsVisible"
      title="翻译设置"
      width="600px"
      @ok="handleSettingsOk"
    >
      <a-form :model="translationSettings" layout="vertical">
        <a-form-item label="目标语言">
          <a-checkbox-group v-model:value="translationSettings.targetLanguages">
            <a-checkbox value="pt">葡萄牙语</a-checkbox>
            <a-checkbox value="th">泰语</a-checkbox>
            <a-checkbox value="ind">印尼语</a-checkbox>
            <a-checkbox value="es">西班牙语</a-checkbox>
            <a-checkbox value="vn">越南语</a-checkbox>
            <a-checkbox value="tr">土耳其语</a-checkbox>
          </a-checkbox-group>
        </a-form-item>

        <a-form-item label="地区设置">
          <a-select v-model:value="translationSettings.region" placeholder="选择目标地区">
            <a-select-option value="na">北美</a-select-option>
            <a-select-option value="sa">南美</a-select-option>
            <a-select-option value="eu">欧洲</a-select-option>
            <a-select-option value="me">中东</a-select-option>
            <a-select-option value="as">东南亚</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="游戏背景">
          <a-textarea
            v-model:value="translationSettings.gameBackground"
            placeholder="描述游戏类型和背景，帮助AI更准确翻译"
            :rows="3"
          />
        </a-form-item>

        <a-form-item label="高级选项">
          <a-space direction="vertical" style="width: 100%">
            <a-row :gutter="16">
              <a-col :span="12">
                <label>批次大小</label>
                <a-input-number
                  v-model:value="translationSettings.batchSize"
                  :min="1"
                  :max="30"
                  style="width: 100%"
                />
              </a-col>
              <a-col :span="12">
                <label>并发数</label>
                <a-input-number
                  v-model:value="translationSettings.maxConcurrent"
                  :min="1"
                  :max="20"
                  style="width: 100%"
                />
              </a-col>
            </a-row>
            <a-switch v-model:checked="translationSettings.preservePlaceholders">
              保护占位符
            </a-switch>
            <a-switch v-model:checked="translationSettings.useGlossary">
              使用术语库
            </a-switch>
          </a-space>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  UploadOutlined,
  SettingOutlined,
  CheckCircleOutlined
} from '@ant-design/icons-vue'
import LuckysheetWrapper from '@/components/luckysheet/LuckysheetWrapper.vue'
import { translationAPI } from '@/api/endpoints/translation'
import * as ExcelJS from 'exceljs'

// Refs
const luckysheetRef = ref()
const settingsVisible = ref(false)
const showAssistPanel = ref(true)
const activeTab = ref('history')
const glossarySearch = ref('')

// 数据
const sheetData = ref<any[]>([])
const translationHistory = ref<any[]>([
  { id: 1, original: 'Attack', translation: '攻击', time: '10:30', language: 'pt' },
  { id: 2, original: 'Defense', translation: '防御', time: '10:31', language: 'pt' },
])

const glossary = ref([
  { source: 'HP', translations: { pt: 'PV', th: 'พลังชีวิต', ind: 'HP' } },
  { source: 'MP', translations: { pt: 'PM', th: 'พลังเวทย์', ind: 'MP' } },
  { source: 'Attack', translations: { pt: 'Ataque', th: 'โจมตี', ind: 'Serangan' } },
])

const statistics = ref({
  total: 1000,
  translated: 650,
  pending: 350
})

const languageStats = ref([
  { code: 'pt', name: '葡萄牙语', progress: 75 },
  { code: 'th', name: '泰语', progress: 60 },
  { code: 'ind', name: '印尼语', progress: 45 },
])

// 翻译设置
const translationSettings = ref({
  targetLanguages: ['pt', 'th', 'ind'],
  region: 'as',
  gameBackground: '',
  batchSize: 10,
  maxConcurrent: 5,
  preservePlaceholders: true,
  useGlossary: true
})

// Luckysheet配置
const luckysheetConfig = {
  lang: 'zh',
  allowEdit: true,
  showtoolbar: true,
  showinfobar: true,
  showsheetbar: true,
  enableAddRow: true,
  enableAddCol: true,
  // 自定义工具栏
  functionButton: `
    <div class="luckysheet-toolbar-button-outer-box">
      <div class="luckysheet-toolbar-button-inner-box">
        批量翻译
      </div>
    </div>
  `,
}

// 计算属性
const translationProgress = computed(() => {
  const { total, translated } = statistics.value
  return total > 0 ? Math.round((translated / total) * 100) : 0
})

const filteredGlossary = computed(() => {
  if (!glossarySearch.value) return glossary.value
  return glossary.value.filter(item =>
    item.source.toLowerCase().includes(glossarySearch.value.toLowerCase())
  )
})

// 文件上传处理
const handleFileUpload = async (file: File) => {
  try {
    message.loading('正在解析Excel文件...', 0)

    // 使用ExcelJS读取文件
    const workbook = new ExcelJS.Workbook()
    const arrayBuffer = await file.arrayBuffer()
    await workbook.xlsx.load(arrayBuffer)

    // 转换为Luckysheet格式
    const sheets: any[] = []
    workbook.eachSheet((worksheet, sheetId) => {
      const sheetData = {
        name: worksheet.name,
        index: sheetId - 1,
        status: 1,
        order: sheetId - 1,
        celldata: [] as any[]
      }

      worksheet.eachRow((row, rowNumber) => {
        row.eachCell((cell, colNumber) => {
          sheetData.celldata.push({
            r: rowNumber - 1,
            c: colNumber - 1,
            v: {
              v: cell.value,
              m: cell.text || cell.value
            }
          })
        })
      })

      sheets.push(sheetData)
    })

    // 加载到Luckysheet
    sheetData.value = sheets
    if (luckysheetRef.value) {
      luckysheetRef.value.setData(sheets)
    }

    message.destroy()
    message.success('文件加载成功')

    // 更新统计
    updateStatistics()
  } catch (error) {
    message.destroy()
    message.error('文件解析失败')
    console.error('File parse error:', error)
  }

  return false // 阻止默认上传
}

// 翻译单元格
const handleTranslateCell = async (text: string) => {
  try {
    // 调用翻译API
    const result = await translationAPI.translateCell({
      text,
      targetLanguage: translationSettings.value.targetLanguages[0],
      context: {
        gameBackground: translationSettings.value.gameBackground
      }
    })

    // 添加到历史
    translationHistory.value.unshift({
      id: Date.now(),
      original: text,
      translation: result.translation,
      time: new Date().toLocaleTimeString(),
      language: translationSettings.value.targetLanguages[0]
    })

    return result
  } catch (error) {
    console.error('Translation error:', error)
    throw error
  }
}

// 保存处理
const handleSave = (data: any) => {
  console.log('Saving data:', data)
  message.success('保存成功')
}

// 单元格变化
const handleCellChange = (change: any) => {
  console.log('Cell changed:', change)
  updateStatistics()
}

// 单元格选中
const handleCellSelected = (cell: any) => {
  console.log('Cell selected:', cell)
}

// 显示设置
const showSettings = () => {
  settingsVisible.value = true
}

// 设置确认
const handleSettingsOk = () => {
  settingsVisible.value = false
  message.success('设置已保存')
}

// 更新统计
const updateStatistics = () => {
  // TODO: 根据实际数据更新统计
  const total = 1000
  const translated = Math.floor(Math.random() * total)
  statistics.value = {
    total,
    translated,
    pending: total - translated
  }
}

// 生命周期
onMounted(() => {
  console.log('Translation workspace mounted')
})
</script>

<style scoped lang="scss">
.translation-workspace {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;

  .workspace-header {
    background: white;
    padding: 16px 24px;
    border-bottom: 1px solid #e8e8e8;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-left {
      h2 {
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 600;
      }
    }
  }

  .workspace-body {
    flex: 1;
    display: flex;
    overflow: hidden;
    padding: 16px;
    gap: 16px;

    .luckysheet-wrapper {
      flex: 1;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      overflow: hidden;
    }

    .assist-panel {
      width: 360px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      padding: 16px;

      .history-list {
        max-height: 400px;
        overflow-y: auto;

        .history-item {
          .history-text {
            font-size: 14px;
            margin-bottom: 4px;
          }

          .history-meta {
            font-size: 12px;
            color: #999;
          }
        }
      }

      .glossary-list {
        max-height: 400px;
        overflow-y: auto;
      }

      .stats-panel {
        .progress-section {
          margin: 16px 0;

          h4 {
            margin-bottom: 8px;
            font-size: 14px;
            font-weight: 500;
          }
        }

        .language-stats {
          h4 {
            margin-bottom: 12px;
            font-size: 14px;
            font-weight: 500;
          }
        }
      }
    }
  }
}

// 响应式布局
@media (max-width: 1200px) {
  .translation-workspace {
    .workspace-body {
      .assist-panel {
        display: none;
      }
    }
  }
}
</style>