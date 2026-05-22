import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

let _handlers = { onUnauthorized: null, onError: null }

export function configureApi({ getToken, onUnauthorized, onError } = {}) {
  api.interceptors.request.use((config) => {
    const t = getToken?.()
    if (t) config.headers.Authorization = `Bearer ${t}`
    return config
  })

  api.interceptors.response.use(
    (r) => r,
    (err) => {
      const code = err?.response?.status
      const data = err?.response?.data
      const detail = typeof data?.detail === 'string' ? data.detail : null
      const fieldErrors = Array.isArray(data?.detail) ? data.detail : null

      let message = detail || 'เกิดข้อผิดพลาด'
      if (!err.response) message = 'ไม่สามารถเชื่อมต่อได้ กรุณาตรวจสอบอินเทอร์เน็ต'
      else if (code === 400) message = detail || 'ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง'
      else if (code === 401) { message = 'Session หมดอายุ กรุณาเข้าสู่ระบบใหม่'; onUnauthorized?.() }
      else if (code === 403) message = 'ไม่มีสิทธิ์ดำเนินการนี้'
      else if (code === 404) message = detail || 'ไม่พบข้อมูลที่ต้องการ'
      else if (code === 409) message = 'ข้อมูลซ้ำในระบบ'
      else if (code === 422) message = fieldErrors ? 'ข้อมูลไม่ครบหรือไม่ถูกต้อง' : (detail || 'ข้อมูลไม่ถูกต้อง')
      else if (code === 429) message = 'คำขอมากเกินไป กรุณารอสักครู่'
      else if (code >= 500) message = 'เกิดข้อผิดพลาดในระบบ กรุณาลองใหม่'

      err._message = message
      err._code = code
      err._fieldErrors = fieldErrors
      onError?.(err)
      return Promise.reject(err)
    }
  )

  _handlers = { onUnauthorized, onError }
}
