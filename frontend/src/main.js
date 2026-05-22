import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Toast, { useToast, POSITION } from 'vue-toastification'
import 'vue-toastification/dist/index.css'

import App from './App.vue'
import { router } from './router'
import { configureApi } from './plugins/axios'
import { useAuthStore } from './stores/auth'

import './assets/styles/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(Toast, {
  position: POSITION.TOP_RIGHT,
  timeout: 3500,
  closeOnClick: true,
  hideProgressBar: false,
  transition: 'Vue-Toastification__fade',
})

// configure axios *after* pinia so we can read the auth store
const auth = useAuthStore()
const toast = useToast()
configureApi({
  getToken: () => auth.token,
  onUnauthorized: () => {
    auth.logout()
    if (router.currentRoute.value.name !== 'login') {
      router.push({ name: 'login' })
    }
  },
  onError: (err) => {
    if (err._code === 422 && err._fieldErrors) return // form-level handled inline
    toast.error(err._message || 'เกิดข้อผิดพลาด', { timeout: 5500 })
  },
})

app.mount('#app')
