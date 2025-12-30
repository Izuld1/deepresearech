<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <h2 class="auth-title">注册</h2>
        
        <form @submit.prevent="handleRegister" class="auth-form">
          <div class="form-group">
            <label for="username">用户名</label>
            <input
              id="username"
              v-model="formData.username"
              type="text"
              required
              placeholder="请输入用户名"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="email">邮箱</label>
            <input
              id="email"
              v-model="formData.email"
              type="email"
              required
              placeholder="请输入邮箱"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="password">密码</label>
            <input
              id="password"
              v-model="formData.password"
              type="password"
              required
              placeholder="请输入密码"
              class="form-input"
            />
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>

          <div v-if="successMessage" class="success-message">
            {{ successMessage }}
          </div>

          <button type="submit" class="btn-primary" :disabled="isLoading">
            {{ isLoading ? '注册中...' : '注册' }}
          </button>
        </form>

        <div class="auth-footer">
          已有账号？
          <a href="/login" class="auth-link">立即登录</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'

const formData = reactive({
  username: '',
  email: '',
  password: ''
})

const errorMessage = ref('')
const successMessage = ref('')
const isLoading = ref(false)

async function handleRegister() {
  errorMessage.value = ''
  successMessage.value = ''
  isLoading.value = true

  try {
    const response = await fetch('http://localhost:8000/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    })

    const data = await response.json()

    if (!response.ok) {
      errorMessage.value = data.detail || '注册失败'
      return
    }

    successMessage.value = '注册成功！3秒后跳转到登录页面...'
    
    setTimeout(() => {
      window.location.href = '/login'
    }, 3000)
  } catch (error) {
    errorMessage.value = '网络错误，请稍后重试'
  } finally {
    isLoading.value = false
  }
}
</script>
