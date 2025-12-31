import { createRouter, createWebHistory } from 'vue-router'
import { authUtils } from '../utils/auth.js'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Research from '../views/Research.vue'
import KnowledgeBase from '../views/KnowledgeBase.vue'

const routes = [
  {
    path: '/',
    name: 'Research',
    component: Research
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/knowledge',
    name: 'KnowledgeBase',
    component: KnowledgeBase
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
