<template>
  <div class="terminology-manager">
    <a-page-header title="术语管理" sub-title="维护游戏术语和翻译一致性" />
    <a-card>
      <a-empty description="术语管理功能开发中..." />
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  console.log('TerminologyManager mounted')
})
</script>

<style scoped lang="scss">
.terminology-manager {
  padding: 24px;
}
</style>