<script setup>
import { useAuthStore } from '../stores/auth'
import BaseCard from '../components/ui/BaseCard.vue'
import { initials, avatarColor } from '../utils/formatters'
import { computed } from 'vue'

const auth = useAuthStore()
const userInitials = computed(() => initials(auth.user?.name))
const userColor = computed(() => avatarColor(auth.user?.name))
</script>

<template>
  <div class="page-enter space-y-6">
    <div>
      <p class="t-caption mb-1">บัญชี</p>
      <h1 class="t-h1 text-ink-900">ตั้งค่า</h1>
    </div>

    <BaseCard>
      <h2 class="t-h3 mb-4">ข้อมูลผู้ใช้</h2>
      <div class="flex items-center gap-4">
        <span class="w-16 h-16 rounded-full text-white font-semibold text-[20px] grid place-items-center"
          :style="{ background: userColor }">{{ userInitials }}</span>
        <div>
          <p class="text-[16px] font-medium text-ink-900">{{ auth.user?.name }}</p>
          <p class="text-[13px] text-ink-400">@{{ auth.user?.username }}</p>
        </div>
      </div>
    </BaseCard>

    <BaseCard>
      <h2 class="t-h3 mb-4">เกี่ยวกับ DebtTrack</h2>
      <dl class="space-y-2 text-[13px]">
        <div class="flex justify-between"><dt class="text-ink-400">เวอร์ชัน</dt><dd>1.0.0</dd></div>
        <div class="flex justify-between"><dt class="text-ink-400">Frontend</dt><dd>Vue 3 + Vite + Tailwind</dd></div>
        <div class="flex justify-between"><dt class="text-ink-400">Backend</dt><dd>FastAPI + SQLite</dd></div>
      </dl>
    </BaseCard>
  </div>
</template>
