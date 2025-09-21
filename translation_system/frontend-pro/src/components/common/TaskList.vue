<template>
  <div class="task-list">
    <a-list :data-source="tasks" size="small">
      <template #renderItem="{ item }">
        <a-list-item>
          <a-list-item-meta>
            <template #title>
              {{ item.name }}
            </template>
            <template #description>
              <a-progress :percent="item.progress" size="small" />
            </template>
          </a-list-item-meta>
        </a-list-item>
      </template>
    </a-list>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const tasks = ref<any[]>([])

// 加载运行中的任务
const loadRunningTasks = async () => {
  try {
    const response = await fetch('/api/translation/tasks?status=processing&limit=5')
    if (response.ok) {
      const data = await response.json()
      tasks.value = data.tasks || []
    }
  } catch (error) {
    console.error('Failed to load running tasks:', error)
  }
}

// 定期刷新
onMounted(() => {
  loadRunningTasks()
  const timer = setInterval(loadRunningTasks, 5000) // 每5秒刷新

  onUnmounted(() => {
    clearInterval(timer)
  })
})
</script>

<style scoped lang="scss">
.task-list {
  padding: 8px;
}
</style>