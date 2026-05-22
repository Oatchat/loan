<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronLeftIcon } from '@heroicons/vue/24/outline'
import DebtorForm from '../components/debtor/DebtorForm.vue'
import { useDebtorsStore } from '../stores/debtors'

const route = useRoute()
const router = useRouter()
const debtors = useDebtorsStore()
const initial = ref(null)

onMounted(async () => {
  initial.value = await debtors.fetchOne(route.params.id)
})
</script>

<template>
  <div class="page-enter">
    <button @click="router.back()" class="inline-flex items-center gap-1 text-[13px] text-ink-600 hover:text-ink-900 mb-3 transition-colors">
      <ChevronLeftIcon class="w-4 h-4" /> ย้อนกลับ
    </button>
    <p class="t-caption mb-1">แก้ไขข้อมูล</p>
    <h1 class="t-h1 text-ink-900 mb-6">แก้ไข {{ initial?.name || '...' }}</h1>
    <DebtorForm v-if="initial" mode="edit" :initial="initial" />
  </div>
</template>
