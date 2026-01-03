<template>
  <div class="research-page">
    <header class="top-bar">
      <h1>DeepResearch</h1>
      <UserMenu />
    </header>

    <main class="main-container">
      <Sidebar />
      
      <section class="chat-container">
        <ChatMessages :messages="state.messages" />
        
        <div v-if="state.finalReport" class="final-report">
          <div class="final-report-header">研究报告</div>
          <div v-html="parsedFinalReport"></div>
        </div>
      </section>

      <TracePanel 
        :phase="state.phase" 
        :retrievals="state.retrievals" 
      />
    </main>

    <InputBar 
      @send="handleSend"
      :disabled="isProcessing"
    />
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { marked } from 'marked'
import Sidebar from '../components/Sidebar.vue'
import ChatMessages from '../components/ChatMessages.vue'
import TracePanel from '../components/TracePanel.vue'
import InputBar from '../components/InputBar.vue'
import UserMenu from '../components/UserMenu.vue'

const state = reactive({
  messages: [],
  phase: 'idle',
  retrievals: [],
  finalReport: '',
  sessionId: null,
  awaitingClarification: false
})

const parsedFinalReport = computed(() => {
  return state.finalReport ? marked.parse(state.finalReport) : ''
})

const isProcessing = computed(() => {
  return state.sessionId && !state.awaitingClarification && state.phase !== 'idle'
})

function connectToSSE(sessionId) {
  const sseUrl = `http://localhost:8000/api/research/stream?session_id=${sessionId}`
  const es = new EventSource(sseUrl)

  es.addEventListener('phase_changed', (event) => {
    const data = JSON.parse(event.data)
    state.phase = data.payload.phase
  })

  es.addEventListener('retrieval_finished', (event) => {
    const data = JSON.parse(event.data)
    state.retrievals.push({
      title: data.payload.title,
      source: data.payload.source || 'Unknown',
      sub_goal_id: data.payload.sub_goal_id
    })
  })

  es.addEventListener('assistant_chunk', (event) => {
    const data = JSON.parse(event.data)
    const chunk = data.payload.content

    const lastMsg = state.messages[state.messages.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.content += chunk
    } else {
      state.messages.push({ role: 'assistant', content: chunk })
    }
  })

  es.addEventListener('clarification_prompt', (event) => {
    const data = JSON.parse(event.data)
    console.log('🔔 收到澄清问题，设置 awaitingClarification = true')
    state.awaitingClarification = true
    state.messages.push({
      role: 'assistant',
      content: data.payload.question
    })
    console.log('当前状态:', { awaitingClarification: state.awaitingClarification, phase: state.phase })
  })

  es.addEventListener('final_output', (event) => {
    const data = JSON.parse(event.data)
    state.finalReport = data.payload.content
    es.close()
  })

  es.onerror = (err) => {
    console.error('SSE error:', err)
    es.close()
  }
}

async function handleSend(text) {
  if (!text.trim()) return

  console.log('📤 发送消息:', text)
  console.log('当前状态:', { 
    sessionId: state.sessionId, 
    awaitingClarification: state.awaitingClarification,
    phase: state.phase 
  })

  state.messages.push({ role: 'user', content: text })

  if (!state.sessionId) {
    state.phase = 'idle'
    state.retrievals = []
    state.finalReport = ''
    state.awaitingClarification = false

    const resp = await fetch('http://localhost:8000/api/research/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: text })
    })

    const data = await resp.json()
    state.sessionId = data.session_id

    connectToSSE(state.sessionId)
    return
  }

  if (state.awaitingClarification) {
    console.log('✅ 进入澄清分支，发送澄清答案')
    state.awaitingClarification = false

    await fetch('http://localhost:8000/api/research/clarification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: state.sessionId,
        answer: text
      })
    })

    console.log('澄清答案已发送，等待后端响应')
    return
  }

  console.warn('❌ Research in progress, input ignored.')
  console.warn('状态检查:', { 
    sessionId: state.sessionId, 
    awaitingClarification: state.awaitingClarification,
    phase: state.phase 
  })
}
</script>

<style scoped>
.research-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
</style>
