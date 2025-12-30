<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <h2 class="auth-title">登录</h2>
        
        <form @submit.prevent="handleLogin" class="auth-form">
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

          <button type="submit" class="btn-primary" :disabled="isLoading">
            {{ isLoading ? '登录中...' : '登录' }}
          </button>
        </form>

        <div class="auth-footer">
          还没有账号？
          <a href="/register" class="auth-link">立即注册</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { authUtils } from '../utils/auth.js'

const formData = reactive({
  username: '',
  password: ''
})

const errorMessage = ref('')
const isLoading = ref(false)

async function handleLogin() {
  errorMessage.value = ''
  isLoading.value = true

  try {
    const response = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    })

    const data = await response.json()

    if (!response.ok) {
      errorMessage.value = data.detail || '登录失败'
      return
    }

    authUtils.setToken(data.token)
    authUtils.setUser(data.user)

    window.location.href = '/'
  } catch (error) {
    errorMessage.value = '网络错误，请稍后重试'
  } finally {
    isLoading.value = false
  }
}
</script>
