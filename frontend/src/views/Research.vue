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
      :kbSelectorDisabled="kbSelectorDisabled"
    />
  </div>
</template>

<script setup>
import { reactive, computed, ref } from 'vue'
import { marked } from 'marked'
import { apiRequest, authUtils } from '../utils/auth.js'
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

const kbSelectorDisabled = ref(false)

const parsedFinalReport = computed(() => {
  return state.finalReport ? marked.parse(state.finalReport) : ''
})

const isProcessing = computed(() => {
  return state.sessionId && !state.awaitingClarification && state.phase !== 'idle'
})

function connectToSSE(sessionId) {
  const token = authUtils.getToken()
  const sseUrl = `http://localhost:8000/api/research/stream?session_id=${sessionId}`
  
  // EventSource 不支持自定义 headers，需要通过 URL 传递 token 或使用 fetch + ReadableStream
  // 这里使用 fetch 实现 SSE 连接以支持 Authorization header
  const connectSSE = async () => {
    try {
      const response = await fetch(sseUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream'
        }
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let i = 0
        while (i < lines.length) {
          const line = lines[i]
          if (line.startsWith('event:')) {
            const eventType = line.slice(6).trim()
            if (i + 1 < lines.length && lines[i + 1].startsWith('data:')) {
              const eventData = lines[i + 1].slice(5).trim()
              handleSSEEvent(eventType, eventData)
              i += 2
              continue
            }
          }
          i++
        }
      }
    } catch (error) {
      console.error('SSE connection error:', error)
    }
  }

  connectSSE()
}

function handleSSEEvent(eventType, eventData) {
  try {
    const data = JSON.parse(eventData)
    
    switch(eventType) {
      case 'phase_changed':
        state.phase = data.payload.phase
        break
        
      case 'retrieval_finished':
        console.log('📥 收到检索结果:', {
          title: data.payload.title,
          source: data.payload.source,
          sub_goal_id: data.payload.sub_goal_id
        })
        state.retrievals.push({
          title: data.payload.title,
          source: data.payload.source || 'Unknown',
          sub_goal_id: data.payload.sub_goal_id
        })
        console.log('📊 当前检索列表数量:', state.retrievals.length)
        break
        
      case 'assistant_chunk':
        const chunk = data.payload.content
        const lastMsg = state.messages[state.messages.length - 1]
        if (lastMsg && lastMsg.role === 'assistant') {
          lastMsg.content += chunk
        } else {
          state.messages.push({ role: 'assistant', content: chunk })
        }
        break
        
      case 'clarification_prompt':
        console.log('🔔 收到澄清问题，设置 awaitingClarification = true')
        state.awaitingClarification = true
        state.messages.push({
          role: 'assistant',
          content: data.payload.question
        })
        console.log('当前状态:', { awaitingClarification: state.awaitingClarification, phase: state.phase })
        break
        
      case 'final_output':
        state.finalReport = data.payload.content
        break
    }
  } catch (error) {
    console.error('Error handling SSE event:', error)
  }
}

async function handleSend(payload) {
  const text = typeof payload === 'string' ? payload : payload.text
  const selectedKbIds = typeof payload === 'object' ? payload.selectedKbIds : []

  if (!text.trim()) return

  console.log('📤 发送消息:', text)
  console.log('📋 选中的知识库:', selectedKbIds)
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

    const resp = await apiRequest('http://localhost:8000/api/research/start', {
      method: 'POST',
      body: JSON.stringify({ 
        user_input: text,
        search_list: selectedKbIds
      })
    })

    const data = await resp.json()
    state.sessionId = data.session_id

    kbSelectorDisabled.value = true

    connectToSSE(state.sessionId)
    return
  }

  if (state.awaitingClarification) {
    console.log('✅ 进入澄清分支，发送澄清答案')
    state.awaitingClarification = false

    await apiRequest('http://localhost:8000/api/research/clarification', {
      method: 'POST',
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
