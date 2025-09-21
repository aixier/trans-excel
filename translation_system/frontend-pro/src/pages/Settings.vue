<template>
  <div class="settings-page">
    <a-page-header title="系统设置" sub-title="配置系统参数和偏好设置" />
    <a-card>
      <a-tabs default-active-key="1">
        <a-tab-pane key="1" tab="基础设置">
          <a-form layout="vertical">
            <a-form-item label="API服务器地址">
              <a-input value="http://localhost:8000" disabled />
            </a-form-item>
            <a-form-item label="默认目标语言">
              <a-select
                mode="multiple"
                :default-value="['pt', 'th']"
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
          </a-form>
        </a-tab-pane>
        <a-tab-pane key="2" tab="高级设置">
          <a-empty description="高级设置开发中..." />
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  console.log('Settings mounted')
})
</script>

<style scoped lang="scss">
.settings-page {
  padding: 24px;
}
</style>