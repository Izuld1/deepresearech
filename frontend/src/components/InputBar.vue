<template>
  <footer class="input-bar">
    <button 
      @click="toggleKbSelector" 
      :disabled="kbSelectorDisabled"
      :class="['kb-toggle-btn', { disabled: kbSelectorDisabled }]"
      title="选择知识库"
    >
      +
    </button>

    <div v-if="showKbSelector" class="kb-selector-dropdown">
      <div class="kb-selector-header">
        <span>选择知识库</span>
        <button @click="showKbSelector = false" class="close-btn">×</button>
      </div>
      <div class="kb-list">
        <div v-if="knowledgeBases.length === 0" class="empty-state">
          暂无知识库
        </div>
        <label 
          v-for="kb in knowledgeBases" 
          :key="kb.id" 
          class="kb-item"
        >
          <input 
            type="checkbox" 
            :value="kb.id" 
            v-model="selectedKbIds"
          />
          <span class="kb-name">{{ kb.name }}</span>
          <span class="kb-desc">{{ kb.description }}</span>
        </label>
      </div>
      <div class="kb-selector-footer">
        <span class="selected-count">已选择 {{ selectedKbIds.length }} 个</span>
      </div>
    </div>

    <input
      v-model="inputText"
      type="text"
      placeholder="请输入你的研究问题,例如:腕骨骨折的原因?"
      @keyup.enter="handleSend"
      :disabled="disabled"
    />
    <button @click="handleSend" :disabled="disabled">发送</button>
  </footer>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiRequest } from '../utils/auth.js'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  },
  kbSelectorDisabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send'])

const inputText = ref('')
const showKbSelector = ref(false)
const knowledgeBases = ref([])
const selectedKbIds = ref([])

async function loadKnowledgeBases() {
  try {
    const response = await apiRequest('http://localhost:8000/api/knowledge_spaces')
    const data = await response.json()
    knowledgeBases.value = data
  } catch (error) {
    console.error('Failed to load knowledge bases:', error)
  }
}

function toggleKbSelector() {
  if (props.kbSelectorDisabled) return
  showKbSelector.value = !showKbSelector.value
  if (showKbSelector.value && knowledgeBases.value.length === 0) {
    loadKnowledgeBases()
  }
}

function handleSend() {
  if (!inputText.value.trim()) return
  
  emit('send', {
    text: inputText.value,
    selectedKbIds: selectedKbIds.value
  })
  inputText.value = ''
  showKbSelector.value = false
}

onMounted(() => {
  loadKnowledgeBases()
})
</script>

<style scoped>
.input-bar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 760px;
  max-width: calc(100% - 32px);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background-color: #ffffff;
  border-top: 1px solid #e5e7eb;
  z-index: 10;
}

.kb-toggle-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #3b82f6;
  color: white;
  border: none;
  font-size: 32px;
  font-weight: 300;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
  line-height: 1;
}

.kb-toggle-btn:hover:not(.disabled) {
  background-color: #2563eb;
  transform: scale(1.05);
}

.kb-toggle-btn.disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
  opacity: 0.6;
}

.kb-selector-dropdown {
  position: absolute;
  bottom: 60px;
  left: 16px;
  width: 320px;
  max-height: 400px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  z-index: 20;
}

.kb-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  font-size: 14px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 40px;
  font-weight: 300;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.close-btn:hover {
  color: #374151;
}

.kb-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  max-height: 300px;
}

.kb-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.kb-item:hover {
  background-color: #f3f4f6;
}

.kb-item input[type="checkbox"] {
  order: 3;
  cursor: pointer;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.kb-name {
  order: 1;
  font-weight: 600;
  font-size: 14px;
  color: #111827;
  flex-shrink: 0;
  min-width: 80px;
}

.kb-desc {
  order: 2;
  font-size: 12px;
  color: #6b7280;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-selector-footer {
  padding: 10px 16px;
  border-top: 1px solid #e5e7eb;
  font-size: 13px;
  color: #6b7280;
}

.selected-count {
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: #9ca3af;
  font-size: 14px;
}

.input-bar input {
  flex: 1;
  padding: 12px 16px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  font-size: 14px;
  outline: none;
}

.input-bar input:focus {
  border-color: #4f46e5;
}

.input-bar input:disabled {
  background-color: #f3f4f6;
  cursor: not-allowed;
}

.input-bar button {
  padding: 10px 18px;
  border-radius: 999px;
  background-color: #4f46e5;
  color: white;
  border: none;
  font-size: 14px;
  cursor: pointer;
}

.input-bar button:hover:not(:disabled) {
  background-color: #4338ca;
}

.input-bar button:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}
</style>
