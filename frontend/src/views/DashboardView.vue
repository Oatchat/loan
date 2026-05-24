<script setup>
import { onMounted, computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  UsersIcon, BanknotesIcon, ArrowTrendingUpIcon, ExclamationTriangleIcon, CheckCircleIcon,
  PlusIcon, XMarkIcon, ChevronRightIcon,
} from '@heroicons/vue/24/outline'
import StatCard from '../components/ui/StatCard.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseBadge from '../components/ui/BaseBadge.vue'
import BaseTable from '../components/ui/BaseTable.vue'
import EmptyState from '../components/shared/EmptyState.vue'
import BulkDebtorActions from '../components/shared/BulkDebtorActions.vue'
import { useDebtorsStore } from '../stores/debtors'
import { formatBaht, formatDate, formatRelative, initials, avatarColor, statusLabel } from '../utils/formatters'
import dayjs from 'dayjs'

const router = useRouter()
const debtors = useDebtorsStore()
const showAlert = ref(true)
const selectedIds = ref([])

onMounted(() => debtors.fetchAll())

const upcoming = computed(() => {
  const now = dayjs()
  return debtors.list
    .filter(d => d.next_due_date && d.status !== 'closed')
    .filter(d => {
      const diff = dayjs(d.next_due_date).diff(now, 'day')
      return diff >= -1 && diff <= 7
    })
    .sort((a, b) => dayjs(a.next_due_date).valueOf() - dayjs(b.next_due_date).valueOf())
    .slice(0, 12)
})

const recentRows = computed(() =>
  [...debtors.list]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 6)
    .map(d => ({ ...d, _highlight: d.status === 'overdue' ? 'overdue' : undefined }))
)

const columns = [
  { key: 'name', label: 'ลูกหนี้' },
  { key: 'principal', label: 'ยอดยืม', align: 'right' },
  { key: 'balance', label: 'คงเหลือ', align: 'right' },
  { key: 'next_due_date', label: 'ครบกำหนด' },
  { key: 'status', label: 'สถานะ' },
]

function statusVariant(s) {
  return { active: 'info', near_due: 'warning', overdue: 'danger', closed: 'neutral' }[s] || 'neutral'
}
</script>

<template>
  <div class="page-enter space-y-8">
    <!-- header -->
    <div class="flex items-end justify-between gap-4 flex-wrap">
      <div>
        <p class="t-caption mb-1">ภาพรวม</p>
        <h1 class="t-h1 text-ink-900">แดชบอร์ด</h1>
      </div>
      <BaseButton variant="primary" @click="router.push('/debtors/new')">
        <template #icon-left><PlusIcon class="w-4 h-4" /></template>
        เพิ่มลูกหนี้
      </BaseButton>
    </div>

    <!-- stat cards (clickable → filter list) -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <router-link to="/debtors" class="focus-visible:outline-none rounded-lg">
        <StatCard label="ลูกหนี้ทั้งหมด" :value="debtors.list.length" accent="info" :icon="UsersIcon" />
      </router-link>
      <router-link to="/reports" class="focus-visible:outline-none rounded-lg">
        <StatCard label="ยอดปล่อยกู้รวม" :value="debtors.totalPrincipal" prefix="฿" accent="neutral" :icon="BanknotesIcon" />
      </router-link>
      <router-link to="/reports" class="focus-visible:outline-none rounded-lg">
        <StatCard label="ดอกเบี้ยสะสม" :value="debtors.totalInterestEarned" prefix="฿" accent="success" :icon="ArrowTrendingUpIcon" />
      </router-link>
      <router-link :to="{ path: '/debtors', query: { status: 'overdue' } }" class="focus-visible:outline-none rounded-lg">
        <StatCard label="เกินกำหนด" :value="debtors.overdueCount" accent="danger" :icon="ExclamationTriangleIcon" />
      </router-link>
      <router-link :to="{ path: '/debtors', query: { status: 'closed' } }" class="focus-visible:outline-none rounded-lg">
        <StatCard label="ปิดบัญชีแล้ว" :value="debtors.closedCount" accent="neutral" :icon="CheckCircleIcon" />
      </router-link>
    </div>

    <!-- overdue alert -->
    <div v-if="debtors.overdueCount > 0 && showAlert"
      class="relative rounded-md border-l-[3px] border-l-danger pl-5 pr-4 py-4 flex items-center gap-3 animate-fade-up"
      style="background: linear-gradient(135deg, #FFF1F0, #FFE4E1);">
      <ExclamationTriangleIcon class="w-5 h-5 text-danger flex-shrink-0" />
      <p class="text-[14px] text-ink-900 flex-1">
        มีลูกหนี้ <strong class="text-danger">{{ debtors.overdueCount }} ราย</strong> เกินกำหนดชำระ — ต้องติดตาม
      </p>
      <button @click="router.push({ path: '/debtors', query: { status: 'overdue' } })"
        class="text-[13px] font-medium text-danger hover:underline">ดูรายการ →</button>
      <button @click="showAlert = false" class="p-1 rounded hover:bg-white/50 text-ink-400">
        <XMarkIcon class="w-4 h-4" />
      </button>
    </div>

    <!-- upcoming payments -->
    <section v-if="upcoming.length">
      <div class="flex items-baseline justify-between mb-3">
        <h2 class="t-h2 text-ink-900">งวดที่จะถึงกำหนด (7 วัน)</h2>
        <span class="t-small text-ink-400">{{ upcoming.length }} รายการ</span>
      </div>
      <div class="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 snap-x">
        <button v-for="(d, idx) in upcoming" :key="d.id"
          @click="router.push(`/debtors/${d.id}`)"
          class="snap-start flex-shrink-0 w-[240px] text-left bg-white rounded-md shadow-sm-soft border border-ink-100 p-4 lift transition-all"
          :style="{ animation: `fade-up 320ms cubic-bezier(.16,1,.3,1) ${idx * 50}ms both` }">
          <div class="flex items-center gap-2.5 mb-3">
            <span class="w-9 h-9 rounded-full text-white font-semibold text-[12px] grid place-items-center flex-shrink-0"
              :style="{ background: avatarColor(d.name) }">{{ initials(d.name) }}</span>
            <div class="min-w-0">
              <p class="text-[14px] font-medium text-ink-900 truncate">{{ d.name }}</p>
              <p class="text-[11px] text-ink-400">{{ formatRelative(d.next_due_date) }}</p>
            </div>
          </div>
          <p class="text-[12px] text-ink-400 mb-0.5">คงเหลือ</p>
          <p class="text-[18px] font-semibold text-ink-900">{{ formatBaht(d.balance) }}</p>
          <BaseBadge :variant="statusVariant(d.status)" :pulse="d.status === 'overdue'" class="mt-2">
            {{ statusLabel(d.status) }}
          </BaseBadge>
        </button>
      </div>
    </section>

    <!-- recent debtors table -->
    <section>
      <div class="flex items-baseline justify-between mb-3">
        <h2 class="t-h2 text-ink-900">ลูกหนี้ล่าสุด</h2>
        <button @click="router.push('/debtors')" class="text-[13px] font-medium text-brand hover:underline flex items-center gap-1">
          ดูทั้งหมด <ChevronRightIcon class="w-4 h-4" />
        </button>
      </div>
      <BaseTable :columns="columns" :rows="recentRows" :loading="debtors.loading"
        selectable v-model:selected="selectedIds">
        <template #cell-name="{ row }">
          <button @click="router.push(`/debtors/${row.id}`)" class="flex items-center gap-3 hover:opacity-80 text-left">
            <span class="w-9 h-9 rounded-full text-white font-semibold text-[12px] grid place-items-center"
              :style="{ background: avatarColor(row.name) }">{{ initials(row.name) }}</span>
            <div>
              <p class="font-medium text-ink-900 leading-tight">{{ row.name }}</p>
              <p class="t-small text-ink-400">{{ row.phone }}</p>
            </div>
          </button>
        </template>
        <template #cell-principal="{ row }"><span class="tabular-nums">{{ formatBaht(row.principal) }}</span></template>
        <template #cell-balance="{ row }"><span class="tabular-nums font-medium">{{ formatBaht(row.balance) }}</span></template>
        <template #cell-next_due_date="{ row }">
          <span v-if="row.next_due_date" :class="row.days_until_due < 0 ? 'text-danger font-medium' : 'text-ink-600'">
            {{ formatRelative(row.next_due_date) }}
          </span>
          <span v-else class="text-ink-400">—</span>
        </template>
        <template #cell-status="{ row }">
          <BaseBadge :variant="statusVariant(row.status)" :pulse="row.status === 'overdue'">
            {{ statusLabel(row.status) }}
          </BaseBadge>
        </template>
        <template #empty>
          <EmptyState title="ยังไม่มีลูกหนี้" message="กดปุ่ม + เพิ่มลูกหนี้ เพื่อเริ่มต้น">
            <BaseButton variant="primary" @click="router.push('/debtors/new')">
              <template #icon-left><PlusIcon class="w-4 h-4" /></template>
              เพิ่มลูกหนี้คนแรก
            </BaseButton>
          </EmptyState>
        </template>
      </BaseTable>
    </section>

    <BulkDebtorActions
      :debtors="debtors.list"
      v-model:selectedIds="selectedIds"
      @changed="debtors.fetchAll()"
    />
  </div>
</template>
