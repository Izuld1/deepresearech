/************************************************
 * DeepResearch UI - app.js
 * 原生 HTML / CSS / JS
 * 支持多轮澄清的 FastAPI + SSE 对接版本
 ************************************************/

/***********************
 * 1. 全局状态
 ***********************/
const state = {
  messages: [],
  phase: "idle",
  retrievals: [],
  finalReport: "",

  // 🔑 新增：但不算“新功能”，只是状态补全
  sessionId: null,
  awaitingClarification: false
};

/***********************
 * 2. DOM 引用
 ***********************/
const chatMessagesEl = document.getElementById("chatMessages");
const phaseDisplayEl = document.getElementById("phaseDisplay");
const retrievalListEl = document.getElementById("retrievalList");
const userInputEl = document.getElementById("userInput");
const sendBtnEl = document.getElementById("sendBtn");
const finalReportEl = document.getElementById("finalReportContent");
const finalReportWrapper = document.getElementById("finalReport");

/***********************
 * 3. 渲染入口
 ***********************/
function render() {
  renderMessages();
  renderPhase();
  renderRetrievals();
  renderFinalReport();
}

function renderFinalReport() {
  if (!state.finalReport) return;
  finalReportEl.innerHTML = marked.parse(state.finalReport);
}

/***********************
 * 4. 聊天消息渲染
 ***********************/
function renderMessages() {
  chatMessagesEl.innerHTML = "";

  state.messages.forEach((msg) => {
    const wrapper = document.createElement("div");
    wrapper.className =
      msg.role === "user" ? "chat-row user" : "chat-row assistant";

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";

    if (msg.role === "assistant") {
      bubble.innerHTML = marked.parse(msg.content || "");
    } else {
      bubble.textContent = msg.content;
    }

    wrapper.appendChild(bubble);
    chatMessagesEl.appendChild(wrapper);
  });

  chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
}

/***********************
 * 5. Phase 渲染
 ***********************/
function renderPhase() {
  phaseDisplayEl.textContent = state.phase;
}

/***********************
 * 6. Retrievals 渲染
 ***********************/
function renderRetrievals() {
  retrievalListEl.innerHTML = "";

  state.retrievals.forEach((title) => {
    const card = document.createElement("div");
    card.className = "trace-card";
    card.innerHTML = `
      <div class="trace-card-title">${title}</div>
      <div class="trace-card-meta">来源：PubMed</div>
    `;
    retrievalListEl.appendChild(card);
  });
}

/***********************
 * 7. SSE 连接
 ***********************/
function connectToSSE(sessionId) {
  const sseUrl = `http://localhost:8000/api/research/stream?session_id=${sessionId}`;
  const es = new EventSource(sseUrl);

  es.addEventListener("phase_changed", (event) => {
    const data = JSON.parse(event.data);
    state.phase = data.payload.phase;
    render();
  });

  es.addEventListener("retrieval_finished", (event) => {
    const data = JSON.parse(event.data);
    state.retrievals.push(data.payload.title);
    render();
  });

  es.addEventListener("assistant_chunk", (event) => {
    const data = JSON.parse(event.data);
    const chunk = data.payload.content;

    const lastMsg = state.messages[state.messages.length - 1];
    if (lastMsg && lastMsg.role === "assistant") {
      lastMsg.content += chunk;
    } else {
      state.messages.push({ role: "assistant", content: chunk });
    }
    render();
  });

  // 🔑 澄清问题（关键）
  es.addEventListener("clarification_prompt", (event) => {
    const data = JSON.parse(event.data);

    state.awaitingClarification = true;

    state.messages.push({
      role: "assistant",
      content: data.payload.question
    });

    render();
  });

  es.addEventListener("final_output", (event) => {
    const data = JSON.parse(event.data);
    state.finalReport = data.payload.content;

    finalReportWrapper.classList.remove("hidden");
    finalReportEl.innerHTML = marked.parse(state.finalReport);

    es.close();
  });

  es.onerror = (err) => {
    console.error("SSE error:", err);
    es.close();
  };
}

/***********************
 * 8. 用户发送消息（核心调度逻辑）
 ***********************/
sendBtnEl.addEventListener("click", async () => {
  const text = userInputEl.value.trim();
  if (!text) return;

  userInputEl.value = "";

  // 显示用户输入
  state.messages.push({ role: "user", content: text });
  render();

  // ===============================
  // 情况 1：首次输入 → start
  // ===============================
  if (!state.sessionId) {
    // 重置状态
    state.phase = "idle";
    state.retrievals = [];
    state.finalReport = "";
    state.awaitingClarification = false;
    finalReportWrapper.classList.add("hidden");

    const resp = await fetch("http://localhost:8000/api/research/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: text })
    });

    const data = await resp.json();
    state.sessionId = data.session_id;

    connectToSSE(state.sessionId);
    return;
  }

  // ===============================
  // 情况 2：澄清阶段 → clarification
  // ===============================
  if (state.awaitingClarification) {
    state.awaitingClarification = false;

    await fetch("http://localhost:8000/api/research/clarification", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.sessionId,
        answer: text
      })
    });

    return;
  }

  // ===============================
  // 情况 3：其余阶段（忽略输入）
  // ===============================
  console.warn("Research in progress, input ignored.");
});

/***********************
 * 9. 初始化
 ***********************/
render();
