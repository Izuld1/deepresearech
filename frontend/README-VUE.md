# DeepResearch UI - Vue 3 版本

## 项目说明

本项目已从原生 HTML+CSS+JS 架构迁移到 Vue 3 + Vite 架构。

## 项目结构

```
deepresearch-UI/
├── src/
│   ├── components/
│   │   ├── Sidebar.vue          # 左侧历史对话面板
│   │   ├── ChatMessages.vue     # 中间聊天消息区域
│   │   ├── TracePanel.vue       # 右侧研究过程面板
│   │   └── InputBar.vue         # 底部输入框
│   ├── App.vue                  # 主应用组件
│   ├── main.js                  # 应用入口
│   └── style.css                # 全局样式
├── index-vue.html               # Vue 版本的 HTML 入口
├── package.json                 # 项目依赖
├── vite.config.js              # Vite 配置
└── main.py                      # FastAPI 后端服务

# 旧文件（保留作为参考）
├── index.html                   # 原生版本 HTML
├── app.js                       # 原生版本 JS
└── style.css                    # 原生版本 CSS
```

## 安装依赖

```bash
npm install
```

## 启动开发服务器

### 1. 启动后端 API（FastAPI）

```bash
python main.py
```

后端将运行在 `http://localhost:8000`

### 2. 启动前端开发服务器（Vue + Vite）

```bash
npm run dev
```

前端将运行在 `http://localhost:5173`

## 构建生产版本

```bash
npm run build
```

构建后的文件将输出到 `dist/` 目录。

## 主要改进

### 1. **组件化架构**
- 将 UI 拆分为独立的 Vue 组件
- 每个组件负责自己的模板、逻辑和样式
- 提高代码可维护性和复用性

### 2. **响应式状态管理**
- 使用 Vue 3 Composition API 的 `reactive` 管理全局状态
- 自动追踪依赖，无需手动调用 `render()`
- 状态变化自动触发 UI 更新

### 3. **更好的开发体验**
- Vite 提供快速的热模块替换（HMR）
- 组件级别的样式隔离（scoped styles）
- 更好的代码组织和类型提示

### 4. **保持原有功能**
- SSE（Server-Sent Events）实时通信
- 多轮澄清对话支持
- Markdown 渲染
- 所有原有业务逻辑完整保留

## 技术栈

- **Vue 3**: 渐进式 JavaScript 框架
- **Vite**: 下一代前端构建工具
- **Marked**: Markdown 解析库
- **FastAPI**: Python 后端框架（保持不变）

## 开发说明

### 组件说明

- **App.vue**: 主应用组件，管理全局状态和 SSE 连接
- **Sidebar.vue**: 左侧历史对话列表
- **ChatMessages.vue**: 聊天消息展示，支持 Markdown 渲染和自动滚动
- **TracePanel.vue**: 右侧研究过程追踪面板
- **InputBar.vue**: 底部输入框，支持回车发送

### 状态管理

全局状态在 `App.vue` 中使用 `reactive` 管理：

```javascript
const state = reactive({
  messages: [],           // 聊天消息列表
  phase: 'idle',         // 当前研究阶段
  retrievals: [],        // 检索结果列表
  finalReport: '',       // 最终报告
  sessionId: null,       // 会话 ID
  awaitingClarification: false  // 是否等待澄清
})
```

### 事件流

1. 用户输入 → `InputBar` 组件 emit `send` 事件
2. `App.vue` 接收事件，调用 `handleSend` 方法
3. 根据状态判断是启动新会话、回答澄清问题还是忽略输入
4. 建立 SSE 连接，接收后端推送的事件
5. 更新 `state`，Vue 自动更新 UI

## 注意事项

- 确保后端服务（`main.py`）在前端启动前已运行
- 开发时前端运行在 5173 端口，后端运行在 8000 端口
- CORS 已在后端配置，允许跨域请求
