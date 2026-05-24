<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import { useAuthStore } from '../stores/auth'
import { loginSchema } from '../utils/validators'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToast()

const username = ref('admin')
const password = ref('admin')
const errors = ref({})
const shake = ref(false)
const submitting = ref(false)

async function submit() {
  errors.value = {}
  try {
    await loginSchema.validate({ username: username.value, password: password.value }, { abortEarly: false })
  } catch (e) {
    errors.value = Object.fromEntries((e.inner || []).map(x => [x.path, x.message]))
    shake.value = true
    setTimeout(() => (shake.value = false), 450)
    return
  }
  submitting.value = true
  try {
    await auth.login(username.value, password.value)
    toast.success('ยินดีต้อนรับสู่ DebtTrack')
    router.push(route.query.redirect || '/')
  } catch (e) {
    shake.value = true
    setTimeout(() => (shake.value = false), 450)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-ink-50 p-4 relative overflow-hidden">
    <!-- ambient gradient blobs -->
    <div class="absolute -top-32 -left-32 w-96 h-96 rounded-full opacity-40 blur-3xl"
      style="background: radial-gradient(circle, #B3D4FB 0%, transparent 70%);" />
    <div class="absolute -bottom-32 -right-32 w-[28rem] h-[28rem] rounded-full opacity-30 blur-3xl"
      style="background: radial-gradient(circle, #C9E2FB 0%, transparent 70%);" />

    <div class="relative w-full max-w-md page-enter">
      <div class="glass rounded-xl p-8 sm:p-10" :class="shake ? 'animate-shake' : ''">
        <div class="text-center mb-8">
          <div class="w-14 h-14 rounded-xl bg-brand grid place-items-center mx-auto mb-4 shadow-md-soft">
            <span class="text-white font-bold text-[24px]">฿</span>
          </div>
          <h1 class="t-h1 text-ink-900 mb-1">DebtTrack</h1>
          <p class="t-small text-ink-400">ระบบจัดการลูกหนี้ส่วนบุคคล</p>
        </div>

        <form @submit.prevent="submit" class="space-y-4">
          <BaseInput v-model="username" type="text" label="ชื่อผู้ใช้" :error="errors.username" required />
          <BaseInput v-model="password" type="password" label="รหัสผ่าน" :error="errors.password" required />

          <BaseButton type="submit" variant="primary" block :loading="submitting || auth.loading" class="!h-[46px] mt-2">
            เข้าสู่ระบบ
          </BaseButton>

          <p class="text-center text-[11px] text-ink-400 pt-4 border-t border-ink-100/60">
            demo: admin / admin
          </p>
        </form>
      </div>
      <p class="text-center text-[11px] text-ink-400 mt-6">© DebtTrack — แอปเปิ้ลพบฟินเทคไทย</p>
    </div>
  </div>
</template>
