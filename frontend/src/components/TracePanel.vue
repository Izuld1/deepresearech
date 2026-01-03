<template>
  <aside class="trace-panel">
    <h2>研究过程</h2>

    <div class="trace-section">
      <div class="trace-label">当前阶段</div>
      <div class="phase-badge">{{ phase }}</div>
    </div>

    <div class="trace-section">
      <div class="trace-label">检索结果</div>
      <div class="trace-cards">
        <div 
          v-for="(retrieval, index) in retrievals" 
          :key="index"
          class="trace-card"
        >
          <div class="trace-card-title">{{ retrieval.title }}</div>
          <div class="trace-card-meta">来源：{{ retrieval.source }}</div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  phase: {
    type: String,
    required: true
  },
  retrievals: {
    type: Array,
    required: true
  }
})
</script>

<style scoped>
.trace-panel {
  width: 300px;
  padding: 16px;
  flex-shrink: 0;
  overflow-y: auto;
  background-color: #f3f4f6;
  border-left: 1px solid #e5e7eb;
  box-shadow: inset 8px 0 12px -12px rgba(0, 0, 0, 0.12);
}

.trace-panel h2 {
  margin-bottom: 12px;
}

.trace-section {
  margin-bottom: 16px;
}

.trace-label {
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 14px;
}

.phase-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background-color: #e0e7ff;
  color: #3730a3;
  font-size: 12px;
}

.trace-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trace-card {
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  font-size: 13px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.trace-card-title {
  font-weight: 600;
  margin-bottom: 6px;
}

.trace-card-meta {
  color: #6b7280;
  font-size: 12px;
}
</style>
