<template>
  <div class="user-menu">
    <div v-if="!isAuthenticated" class="user-menu-trigger">
      <a href="/login" class="auth-link-btn">登录 / 注册</a>
    </div>

    <div v-else class="user-menu-wrapper">
      <button @click="toggleDropdown" class="user-menu-trigger">
        {{ user?.username || '用户' }}
        <span class="dropdown-icon">▼</span>
      </button>

      <div v-if="showDropdown" class="user-dropdown">
        <div class="user-info">
          <div class="user-info-item">
            <span class="label">用户名：</span>
            <span class="value">{{ user?.username }}</span>
          </div>
          <div class="user-info-item">
            <span class="label">邮箱：</span>
            <span class="value">{{ user?.email }}</span>
          </div>
        </div>

        <div class="dropdown-divider"></div>

        <button @click="handleLogout" class="dropdown-item logout-btn">
          退出登录
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { authUtils } from '../utils/auth.js'

const isAuthenticated = ref(false)
const user = ref(null)
const showDropdown = ref(false)

function checkAuth() {
  isAuthenticated.value = authUtils.isAuthenticated()
  user.value = authUtils.getUser()
}

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

function handleLogout() {
  authUtils.logout()
  window.location.href = '/login'
}

function handleClickOutside(event) {
  const userMenu = event.target.closest('.user-menu-wrapper')
  if (!userMenu && showDropdown.value) {
    showDropdown.value = false
  }
}

onMounted(() => {
  checkAuth()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.user-menu {
  margin-left: auto;
}

.user-menu-wrapper {
  position: relative;
}

.user-menu-trigger {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 6px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.user-menu-trigger:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

.auth-link-btn {
  color: white;
  text-decoration: none;
}

.dropdown-icon {
  font-size: 10px;
  transition: transform 0.2s;
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 240px;
  z-index: 1000;
}

.user-info {
  padding: 12px 16px;
}

.user-info-item {
  display: flex;
  margin-bottom: 8px;
  font-size: 14px;
}

.user-info-item:last-child {
  margin-bottom: 0;
}

.user-info-item .label {
  color: #6b7280;
  min-width: 60px;
}

.user-info-item .value {
  color: #1f2937;
  font-weight: 500;
}

.dropdown-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 8px 0;
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 10px 16px;
  text-align: left;
  background: none;
  border: none;
  color: #374151;
  font-size: 14px;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.2s;
}

.dropdown-item:hover {
  background: #f3f4f6;
}

.logout-btn {
  color: #dc2626;
  border-top: 1px solid #e5e7eb;
  border-radius: 0 0 8px 8px;
}

.logout-btn:hover {
  background: #fef2f2;
}
</style>
