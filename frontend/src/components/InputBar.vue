<template>
  <footer class="input-bar">
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
import { ref } from 'vue'

defineProps({
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send'])

const inputText = ref('')

function handleSend() {
  if (!inputText.value.trim()) return
  
  emit('send', inputText.value)
  inputText.value = ''
}
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
