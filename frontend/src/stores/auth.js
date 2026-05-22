import { defineStore } from 'pinia'
import { api } from '../plugins/axios'

const TOKEN_KEY = 'debttrack.token'
const USER_KEY = 'debttrack.user'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
    loading: false,
  }),
  getters: {
    isAuthenticated: (s) => !!s.token,
  },
  actions: {
    async login(email, password) {
      this.loading = true
      try {
        const { data } = await api.post('/auth/login', { email, password })
        this.token = data.access_token
        this.user = data.user
        localStorage.setItem(TOKEN_KEY, this.token)
        localStorage.setItem(USER_KEY, JSON.stringify(this.user))
        return data
      } finally {
        this.loading = false
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
    async fetchMe() {
      const { data } = await api.get('/auth/me')
      this.user = data
      localStorage.setItem(USER_KEY, JSON.stringify(data))
    },
  },
})
