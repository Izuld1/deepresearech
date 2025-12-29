<template>
  <div class="chat-messages" ref="messagesContainer">
    <div 
      v-for="(msg, index) in messages" 
      :key="index"
      :class="['chat-row', msg.role]"
    >
      <div class="chat-bubble">
        <div v-if="msg.role === 'assistant'" v-html="parseMarkdown(msg.content)"></div>
        <div v-else>{{ msg.content }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  messages: {
    type: Array,
    required: true
  }
})

const messagesContainer = ref(null)

function parseMarkdown(content) {
  return content ? marked.parse(content) : ''
}

watch(() => props.messages, async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}, { deep: true })
</script>

<style scoped>
.chat-messages {
  flex: 1;
}

.chat-row {
  display: flex;
  margin-bottom: 16px;
}

.chat-row.user {
  justify-content: flex-end;
}

.chat-row.assistant {
  justify-content: flex-start;
}

.chat-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
}

.chat-row.user .chat-bubble {
  background-color: #4f46e5;
  color: white;
  border-bottom-right-radius: 4px;
}

.chat-row.assistant .chat-bubble {
  background-color: #f3f4f6;
  color: #111827;
  border-bottom-left-radius: 4px;
}
</style>
