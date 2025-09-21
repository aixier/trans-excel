<template>
  <div class="version-maintenance">
    <a-page-header title="版本维护" sub-title="管理翻译版本和历史记录" />
    <a-card>
      <a-empty description="版本维护功能开发中..." />
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  console.log('VersionMaintenance mounted')
})
</script>

<style scoped lang="scss">
.version-maintenance {
  padding: 24px;
}
</style>