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

    <div class="sidebar-footer">
      <a href="/knowledge" class="kb-link">知识库管理</a>
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
  display: flex;
  flex-direction: column;
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

.sidebar-footer {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid #374151;
}

.kb-link {
  display: block;
  padding: 10px;
  background-color: #374151;
  color: #d1d5db;
  text-align: center;
  text-decoration: none;
  border-radius: 6px;
  font-size: 14px;
  transition: background-color 0.2s;
}

.kb-link:hover {
  background-color: #4b5563;
  color: white;
}
</style>
