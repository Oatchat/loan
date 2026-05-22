<script setup>
import { useRouter } from 'vue-router'
import { ChevronLeftIcon } from '@heroicons/vue/24/outline'
import DebtorForm from '../components/debtor/DebtorForm.vue'

const router = useRouter()
</script>

<template>
  <div class="page-enter">
    <button @click="router.back()" class="inline-flex items-center gap-1 text-[13px] text-ink-600 hover:text-ink-900 mb-3 transition-colors">
      <ChevronLeftIcon class="w-4 h-4" /> ย้อนกลับ
    </button>
    <p class="t-caption mb-1">เพิ่มข้อมูล</p>
    <h1 class="t-h1 text-ink-900 mb-6">เพิ่มลูกหนี้ใหม่</h1>
    <DebtorForm mode="create" />
  </div>
</template>
