<script setup>
import { onMounted, ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { MagnifyingGlassIcon, PlusIcon, EyeIcon, PencilSquareIcon, BanknotesIcon, TrashIcon } from '@heroicons/vue/24/outline'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseBadge from '../components/ui/BaseBadge.vue'
import BaseTable from '../components/ui/BaseTable.vue'
import BaseSelect from '../components/ui/BaseSelect.vue'
import EmptyState from '../components/shared/EmptyState.vue'
import ConfirmModal from '../components/shared/ConfirmModal.vue'
import BulkDebtorActions from '../components/shared/BulkDebtorActions.vue'
import { useDebtorsStore } from '../stores/debtors'
import { formatBaht, formatRelative, initials, avatarColor, statusLabel } from '../utils/formatters'
import { useToast } from 'vue-toastification'

const router = useRouter()
const route = useRoute()
const debtors = useDebtorsStore()
const toast = useToast()

const filters = [
  { value: 'all', label: 'ทั้งหมด' },
  { value: 'active', label: 'ปกติ' },
  { value: 'near_due', label: 'ใกล้ครบ' },
  { value: 'overdue', label: 'เกินกำหนด' },
  { value: 'closed', label: 'ปิดแล้ว' },
]

const sortOptions = [
  { value: 'recent', label: 'ล่าสุด' },
  { value: 'name', label: 'ตามชื่อ' },
  { value: 'balance', label: 'ยอดคงเหลือ' },
  { value: 'due', label: 'ครบกำหนด' },
]

const search = ref('')
const status = ref(route.query.status || 'all')
const sort = ref('recent')
const selectedIds = ref([])

async function refresh() {
  debtors.query = { q: search.value, status: status.value, sort: sort.value }
  await debtors.fetchAll()
}

let t
watch(search, () => {
  clearTimeout(t)
  t = setTimeout(refresh, 250)
})
watch(status, refresh)
watch(sort, refresh)

onMounted(refresh)

const rows = computed(() =>
  debtors.list
    .filter(d => status.value === 'closed' || d.status !== 'closed')
    .map(d => ({ ...d, _highlight: d.status === 'overdue' ? 'overdue' : undefined }))
)

const columns = [
  { key: 'name', label: 'ลูกหนี้' },
  { key: 'principal', label: 'ยืม / คงเหลือ', align: 'right' },
  { key: 'interest_rate', label: 'ดอกเบี้ย', align: 'center' },
  { key: 'next_due_date', label: 'ครบกำหนด' },
  { key: 'status', label: 'สถานะ' },
]

function statusVariant(s) {
  return { active: 'info', near_due: 'warning', overdue: 'danger', closed: 'neutral' }[s] || 'neutral'
}

// confirm-delete state
const deleting = ref(null)
const deletingLoading = ref(false)
async function confirmDelete() {
  if (!deleting.value) return
  deletingLoading.value = true
  try {
    await debtors.remove(deleting.value.id)
    toast.success(`ลบ ${deleting.value.name} เรียบร้อย`)
    deleting.value = null
  } finally { deletingLoading.value = false }
}
</script>

<template>
  <div class="page-enter space-y-6">
    <!-- header -->
    <div class="flex items-end justify-between gap-4 flex-wrap">
      <div>
        <p class="t-caption mb-1">ฐานข้อมูล</p>
        <h1 class="t-h1 text-ink-900">ลูกหนี้</h1>
      </div>
      <BaseButton variant="primary" @click="router.push('/debtors/new')">
        <template #icon-left><PlusIcon class="w-4 h-4" /></template>
        เพิ่มลูกหนี้
      </BaseButton>
    </div>

    <!-- search + sort -->
    <div class="flex items-center gap-3 flex-wrap">
      <div class="relative flex-1 min-w-[260px]">
        <MagnifyingGlassIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-400" />
        <input v-model="search" type="search" placeholder="ค้นหาชื่อหรือเบอร์โทร..."
          class="w-full h-11 pl-11 pr-4 rounded-full bg-white border border-ink-200 outline-none text-[14px] focus:border-brand focus:ring-4 focus:ring-brand/15 transition-all duration-220" />
      </div>
      <div class="w-full sm:w-52">
        <BaseSelect v-model="sort" :options="sortOptions" label="เรียงตาม" />
      </div>
    </div>

    <!-- filter pills -->
    <div class="flex items-center gap-2 flex-wrap">
      <button v-for="f in filters" :key="f.value" @click="status = f.value"
        :class="['h-9 px-4 rounded-full text-[13px] font-medium transition-all duration-200 border',
          status === f.value
            ? 'bg-brand text-white border-brand shadow-sm-soft'
            : 'bg-white text-ink-600 border-ink-200 hover:border-ink-400']">
        {{ f.label }}
      </button>
    </div>

    <BaseTable :columns="columns" :rows="rows" :loading="debtors.loading"
      selectable v-model:selected="selectedIds"
      row-clickable @row-click="(row) => router.push(`/debtors/${row.id}`)">
      <template #cell-name="{ row }">
        <div class="flex items-center gap-3">
          <span class="w-10 h-10 rounded-full text-white font-semibold text-[13px] grid place-items-center flex-shrink-0"
            :style="{ background: avatarColor(row.name) }">{{ initials(row.name) }}</span>
          <div class="min-w-0">
            <p class="font-medium text-ink-900 leading-tight truncate">{{ row.name }}</p>
            <p class="t-small text-ink-400">{{ row.phone }}</p>
          </div>
        </div>
      </template>
      <template #cell-principal="{ row }">
        <p class="tabular-nums text-[14px]">{{ formatBaht(row.principal) }}</p>
        <p class="tabular-nums text-[12px] text-ink-400">คงเหลือ {{ formatBaht(row.balance) }}</p>
      </template>
      <template #cell-interest_rate="{ row }">
        <BaseBadge variant="info">{{ row.interest_rate }}%/ด</BaseBadge>
      </template>
      <template #cell-next_due_date="{ row }">
        <span v-if="row.next_due_date" :class="row.days_until_due < 0 ? 'text-danger font-medium' : 'text-ink-600'">
          {{ formatRelative(row.next_due_date) }}
        </span>
        <span v-else class="text-ink-400">—</span>
      </template>
      <template #cell-status="{ row }">
        <BaseBadge :variant="statusVariant(row.status)" :pulse="row.status === 'overdue'">{{ statusLabel(row.status) }}</BaseBadge>
      </template>
      <template #actions="{ row }">
        <div class="inline-flex items-center gap-0 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity duration-200" @click.stop>
          <button @click.stop="router.push(`/debtors/${row.id}/edit`)" title="แก้ไข" class="p-2 rounded hover:bg-ink-100 text-ink-600">
            <PencilSquareIcon class="w-4 h-4" />
          </button>
          <button @click.stop="router.push(`/debtors/${row.id}#pay`)" title="บันทึกชำระ" class="p-2 rounded hover:bg-brand-light text-brand">
            <BanknotesIcon class="w-4 h-4" />
          </button>
          <button @click.stop="deleting = row" title="ลบ" class="p-2 rounded hover:bg-red-50 text-danger">
            <TrashIcon class="w-4 h-4" />
          </button>
        </div>
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

    <BulkDebtorActions
      :debtors="debtors.list"
      v-model:selectedIds="selectedIds"
      @changed="refresh()"
    />

    <ConfirmModal :open="!!deleting"
      :title="`ลบ ${deleting?.name}?`"
      :message="`คุณแน่ใจหรือไม่? ข้อมูลของ ${deleting?.name} และรายการชำระทั้งหมดจะถูกลบถาวร`"
      confirm-text="ลบถาวร" variant="danger" :loading="deletingLoading"
      @confirm="confirmDelete" @close="deleting = null" />
  </div>
</template>
