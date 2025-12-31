<template>
  <div class="kb-page">
    <header class="top-bar">
      <h1>知识库管理</h1>
      <button @click="goBack" class="back-btn">返回主页</button>
      <UserMenu />
    </header>

    <main class="kb-container">
      <aside class="kb-sidebar">
        <div class="kb-sidebar-header">
          <h2>知识库列表</h2>
          <button @click="showCreateDialog = true" class="btn-create">新建知识库</button>
        </div>

        <div class="kb-list">
          <div 
            v-for="kb in knowledgeSpaces" 
            :key="kb.id"
            :class="['kb-item', { active: selectedKbId === kb.id }]"
            @click="selectKnowledgeBase(kb.id)"
          >
            <div class="kb-item-content">
              <div class="kb-name">{{ kb.name }}</div>
              <div class="kb-desc">{{ kb.description }}</div>
            </div>
            <button @click.stop="toggleKbMenu(kb.id)" class="kb-menu-btn">⋮</button>
            
            <div v-if="activeKbMenu === kb.id" class="kb-dropdown">
              <button @click="deleteKnowledgeBase(kb.id)" class="dropdown-item danger">
                删除知识库
              </button>
            </div>
          </div>

          <div v-if="knowledgeSpaces.length === 0" class="empty-state">
            暂无知识库
          </div>
        </div>
      </aside>

      <section class="kb-content">
        <div v-if="!selectedKbId" class="empty-state">
          请选择一个知识库查看文件
        </div>

        <div v-else class="file-section">
          <div class="file-header">
            <h3>文件列表</h3>
            <button @click="showUploadDialog = true" class="btn-upload">上传文件</button>
          </div>

          <div v-if="documents.length === 0" class="empty-state">
            该知识库暂无文件
          </div>

          <table v-else class="file-table">
            <thead>
              <tr>
                <th>文件名</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="doc in documents" :key="doc.id">
                <td>{{ doc.filename }}</td>
                <td>
                  <span :class="['status-badge', doc.status]">
                    {{ getStatusText(doc.status) }}
                  </span>
                </td>
                <td>{{ formatDate(doc.created_at) }}</td>
                <td>
                  <button @click="deleteDocument(doc.id)" class="btn-delete">删除</button>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-if="totalPages > 1" class="pagination">
            <button 
              @click="changePage(currentPage - 1)" 
              :disabled="currentPage === 1"
              class="page-btn"
            >
              上一页
            </button>
            <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
            <button 
              @click="changePage(currentPage + 1)" 
              :disabled="currentPage === totalPages"
              class="page-btn"
            >
              下一页
            </button>
          </div>
        </div>
      </section>
    </main>

    <div v-if="showCreateDialog" class="modal-overlay" @click="showCreateDialog = false">
      <div class="modal-content" @click.stop>
        <h3>新建知识库</h3>
        <form @submit.prevent="createKnowledgeBase">
          <div class="form-group">
            <label>名称</label>
            <input v-model="newKb.name" type="text" required class="form-input" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="newKb.description" class="form-input" rows="3"></textarea>
          </div>
          <div v-if="errorMsg" class="error-message">{{ errorMsg }}</div>
          <div class="modal-actions">
            <button type="button" @click="showCreateDialog = false" class="btn-cancel">取消</button>
            <button type="submit" class="btn-primary">创建</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showUploadDialog" class="modal-overlay" @click="closeUploadDialog">
      <div class="modal-content" @click.stop>
        <h3>上传文件</h3>
        <form @submit.prevent="uploadDocument">
          <div class="form-group">
            <label>选择文件</label>
            <input 
              ref="fileInput"
              type="file" 
              @change="handleFileSelect"
              required 
              class="form-input"
              accept=".pdf,.txt,.docx,.doc,.md"
            />
            <div class="file-hint">支持的文件类型：PDF, TXT, DOCX, Markdown（最大 20MB）</div>
          </div>
          <div v-if="selectedFile" class="file-info">
            <div><strong>文件名：</strong>{{ selectedFile.name }}</div>
            <div><strong>大小：</strong>{{ formatFileSize(selectedFile.size) }}</div>
          </div>
          <div v-if="errorMsg" class="error-message">{{ errorMsg }}</div>
          <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
            </div>
            <div class="progress-text">上传中... {{ uploadProgress }}%</div>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeUploadDialog" class="btn-cancel" :disabled="isUploading">取消</button>
            <button type="submit" class="btn-primary" :disabled="!selectedFile || isUploading">
              {{ isUploading ? '上传中...' : '上传' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest, authUtils } from '../utils/auth.js'
import UserMenu from '../components/UserMenu.vue'

const router = useRouter()

const knowledgeSpaces = ref([])
const selectedKbId = ref(null)
const documents = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const activeKbMenu = ref(null)

const showCreateDialog = ref(false)
const showUploadDialog = ref(false)
const errorMsg = ref('')
const selectedFile = ref(null)
const isUploading = ref(false)
const uploadProgress = ref(0)

const newKb = ref({
  name: '',
  description: ''
})

function goBack() {
  router.push('/')
}

async function loadKnowledgeSpaces() {
  try {
    const response = await apiRequest('http://localhost:8000/api/knowledge_spaces')
    const data = await response.json()
    knowledgeSpaces.value = data
  } catch (error) {
    console.error('Failed to load knowledge spaces:', error)
  }
}

async function createKnowledgeBase() {
  errorMsg.value = ''
  try {
    const response = await apiRequest('http://localhost:8000/api/knowledge_spaces', {
      method: 'POST',
      body: JSON.stringify(newKb.value)
    })

    if (!response.ok) {
      const data = await response.json()
      errorMsg.value = data.detail || '创建失败'
      return
    }

    showCreateDialog.value = false
    newKb.value = { name: '', description: '' }
    await loadKnowledgeSpaces()
  } catch (error) {
    errorMsg.value = '网络错误'
  }
}

async function deleteKnowledgeBase(kbId) {
  if (!confirm('确定要删除该知识库吗？')) return

  try {
    const response = await apiRequest(`http://localhost:8000/api/knowledge_spaces/${kbId}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      const data = await response.json()
      alert(data.detail || '删除失败。如果知识库下仍有文件，请先删除所有文件。')
      return
    }

    if (selectedKbId.value === kbId) {
      selectedKbId.value = null
      documents.value = []
    }
    await loadKnowledgeSpaces()
  } catch (error) {
    alert('删除失败')
  }
  activeKbMenu.value = null
}

function selectKnowledgeBase(kbId) {
  selectedKbId.value = kbId
  currentPage.value = 1
  loadDocuments()
}

async function loadDocuments() {
  if (!selectedKbId.value) return

  try {
    const response = await apiRequest(
      `http://localhost:8000/api/documents?knowledge_space_id=${selectedKbId.value}&page=${currentPage.value}`
    )
    const data = await response.json()
    documents.value = data.items || []
    totalPages.value = data.total_pages || 1
  } catch (error) {
    console.error('Failed to load documents:', error)
  }
}

function handleFileSelect(event) {
  const file = event.target.files[0]
  if (!file) {
    selectedFile.value = null
    return
  }

  const maxSize = 20 * 1024 * 1024
  if (file.size > maxSize) {
    errorMsg.value = '文件大小超过 20MB 限制'
    selectedFile.value = null
    event.target.value = ''
    return
  }

  selectedFile.value = file
  errorMsg.value = ''
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

function closeUploadDialog() {
  if (isUploading.value) return
  showUploadDialog.value = false
  selectedFile.value = null
  errorMsg.value = ''
  uploadProgress.value = 0
}

async function uploadDocument() {
  if (!selectedFile.value) {
    errorMsg.value = '请选择文件'
    return
  }

  if (!selectedKbId.value) {
    errorMsg.value = '请先选择知识库'
    return
  }

  errorMsg.value = ''
  isUploading.value = true
  uploadProgress.value = 0

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('knowledge_space_id', selectedKbId.value)

    uploadProgress.value = 50

    const response = await apiRequest('http://localhost:8000/api/documents/upload', {
      method: 'POST',
      body: formData
    })

    uploadProgress.value = 90

    if (!response.ok) {
      const data = await response.json()
      errorMsg.value = data.detail || '上传失败'
      return
    }

    uploadProgress.value = 100
    
    setTimeout(() => {
      showUploadDialog.value = false
      selectedFile.value = null
      uploadProgress.value = 0
      loadDocuments()
    }, 500)
  } catch (error) {
    errorMsg.value = error.message || '网络错误'
  } finally {
    isUploading.value = false
  }
}

async function deleteDocument(docId) {
  if (!confirm('确定要删除该文件吗？')) return

  try {
    const response = await apiRequest(
      `http://localhost:8000/api/documents/${docId}?knowledge_space_id=${selectedKbId.value}`,
      { method: 'DELETE' }
    )

    if (!response.ok) {
      alert('删除失败')
      return
    }

    await loadDocuments()
  } catch (error) {
    alert('删除失败')
  }
}

function changePage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadDocuments()
}

function toggleKbMenu(kbId) {
  activeKbMenu.value = activeKbMenu.value === kbId ? null : kbId
}

function getStatusText(status) {
  const statusMap = {
    uploaded: '已上传',
    parsed: '已解析',
    indexed: '已索引',
    failed: '失败'
  }
  return statusMap[status] || status
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

function handleClickOutside(event) {
  if (!event.target.closest('.kb-item')) {
    activeKbMenu.value = null
  }
}

onMounted(() => {
  loadKnowledgeSpaces()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.kb-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.back-btn {
  margin-left: 16px;
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.kb-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.kb-sidebar {
  width: 280px;
  background-color: #f9fafb;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
}

.kb-sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.kb-sidebar-header h2 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.btn-create {
  width: 100%;
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-create:hover {
  background: #5568d3;
}

.kb-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.kb-item {
  position: relative;
  padding: 12px;
  margin-bottom: 8px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.kb-item:hover {
  background: #f3f4f6;
}

.kb-item.active {
  background: #ede9fe;
  border-color: #667eea;
}

.kb-item-content {
  flex: 1;
  min-width: 0;
}

.kb-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.kb-desc {
  font-size: 12px;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-menu-btn {
  padding: 4px 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 18px;
  color: #6b7280;
}

.kb-menu-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.kb-dropdown {
  position: absolute;
  top: 100%;
  right: 8px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10;
  min-width: 120px;
}

.kb-dropdown .dropdown-item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.kb-dropdown .dropdown-item:hover {
  background: #f3f4f6;
}

.kb-dropdown .dropdown-item.danger {
  color: #dc2626;
}

.kb-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.file-section {
  max-width: 1200px;
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.file-header h3 {
  font-size: 18px;
  font-weight: 600;
}

.btn-upload {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-upload:hover {
  background: #5568d3;
}

.file-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.file-table th {
  background: #f9fafb;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

.file-table td {
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
}

.file-table tr:last-child td {
  border-bottom: none;
}

.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.uploaded {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.parsed {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.indexed {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.failed {
  background: #fee2e2;
  color: #991b1b;
}

.btn-delete {
  padding: 4px 12px;
  background: transparent;
  border: 1px solid #dc2626;
  color: #dc2626;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.btn-delete:hover {
  background: #fef2f2;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

.page-btn {
  padding: 6px 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.page-btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #6b7280;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #6b7280;
  font-size: 14px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 500px;
}

.modal-content h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.btn-cancel {
  padding: 8px 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-cancel:hover {
  background: #f3f4f6;
}

.file-hint {
  font-size: 12px;
  color: #6b7280;
  margin-top: 6px;
}

.file-info {
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 12px;
}

.file-info div {
  margin-bottom: 6px;
}

.file-info div:last-child {
  margin-bottom: 0;
}

.upload-progress {
  margin-top: 12px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}
</style>
