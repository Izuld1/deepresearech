<template>
  <aside class="sidebar">
    <div class="sidebar-title">历史对话</div>

    <div class="chat-history-item active">
      腕骨骨折
    </div>
    <div class="chat-history-item">
      炎症机制综述
    </div>
    <div class="chat-history-item">
      HPA 轴相关研究
    </div>
  </aside>
</template>

<script setup>
</script>

<style scoped>
.sidebar {
  width: 220px;
  background-color: #111827;
  color: #d1d5db;
  padding: 12px;
  flex-shrink: 0;
}

.sidebar-title {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 12px;
}

.chat-history-item {
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 6px;
  cursor: pointer;
}

.chat-history-item:hover {
  background-color: #1f2937;
}

.chat-history-item.active {
  background-color: #374151;
  color: white;
}
</style>
