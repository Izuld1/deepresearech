const TOKEN_KEY = 'auth_token'
const USER_KEY = 'user_info'

export const authUtils = {
  getToken() {
    return localStorage.getItem(TOKEN_KEY)
  },

  setToken(token) {
    localStorage.setItem(TOKEN_KEY, token)
  },

  removeToken() {
    localStorage.removeItem(TOKEN_KEY)
  },

  getUser() {
    const userStr = localStorage.getItem(USER_KEY)
    return userStr ? JSON.parse(userStr) : null
  },

  setUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },

  removeUser() {
    localStorage.removeItem(USER_KEY)
  },

  isAuthenticated() {
    return !!this.getToken()
  },

  logout() {
    this.removeToken()
    this.removeUser()
  }
}

export async function apiRequest(url, options = {}) {
  const token = authUtils.getToken()
  
  const headers = {
    ...options.headers
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(url, {
    ...options,
    headers
  })

  if (response.status === 401) {
    authUtils.logout()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  return response
}
