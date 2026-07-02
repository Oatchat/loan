<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import {
  ChevronLeftIcon, PencilSquareIcon, BanknotesIcon, TrashIcon,
  ArrowPathRoundedSquareIcon, DocumentArrowDownIcon, CheckCircleIcon,
  ExclamationCircleIcon, ClockIcon,
} from '@heroicons/vue/24/outline'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseBadge from '../components/ui/BaseBadge.vue'
import BaseModal from '../components/ui/BaseModal.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseTextarea from '../components/ui/BaseTextarea.vue'
import ConfirmModal from '../components/shared/ConfirmModal.vue'
import { useDebtorsStore } from '../stores/debtors'
import { formatBaht, formatDate, formatRelative, initials, avatarColor, statusLabel } from '../utils/formatters'
import { useInterestCalc } from '../composables/useInterestCalc'
import { paymentSchema, rolloverSchema } from '../utils/validators'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const debtors = useDebtorsStore()
const toast = useToast()
const apiBase = import.meta.env.VITE_API_BASE_URL || '/api'

const d = computed(() => debtors.current)
const loaded = ref(false)

onMounted(async () => {
  await debtors.fetchOne(route.params.id)
  loaded.value = true
  if (window.location.hash === '#pay') showPay.value = true
})

const principalRef = computed(() => d.value?.principal || 0)
const rateRef = computed(() => d.value?.interest_rate || 0)
const monthsRef = computed(() => d.value?.installments || 1)
const typeRef = computed(() => d.value?.interest_type || 'flat')
const startRef = computed(() => d.value?.start_date || dayjs().format('YYYY-MM-DD'))
const firstDueRef = computed(() => d.value?.first_due_date || null)
const { schedule } = useInterestCalc({
  principal: principalRef, ratePerMonth: rateRef, months: monthsRef,
  interestType: typeRef, startDate: startRef, firstDueDate: firstDueRef,
})

const sortedPayments = computed(() =>
  [...(d.value?.payments || [])].sort((a, b) => dayjs(a.paid_date).valueOf() - dayjs(b.paid_date).valueOf())
)

const paymentsByInstallment = computed(() => {
  const map = new Map()
  for (const p of sortedPayments.value) {
    if (p.installment_no != null && !map.has(p.installment_no)) map.set(p.installment_no, p)
  }
  // fallback: payments without installment_no — fill remaining slots in order
  const orphans = sortedPayments.value.filter(p => p.installment_no == null)
  return { map, orphans }
})

const enrichedSchedule = computed(() => {
  const { map, orphans } = paymentsByInstallment.value
  let orphanIdx = 0
  return schedule.value.map((row) => {
    let matched = map.get(row.month)
    if (!matched && orphanIdx < orphans.length) matched = orphans[orphanIdx++]
    return {
      ...row,
      payment_id: matched?.id ?? null,
      paid: matched?.amount ?? null,
      paid_date: matched?.paid_date ?? null,
      status: matched ? (dayjs(matched.paid_date).isAfter(dayjs(row.dueDate)) ? 'late' : 'paid')
                       : (dayjs(row.dueDate).isBefore(dayjs()) ? 'overdue' : 'pending'),
    }
  })
})

function statusVariant(s) {
  return { active: 'info', near_due: 'warning', overdue: 'danger', closed: 'neutral' }[s] || 'neutral'
}

// delete payment state
const deletingPay = ref(null)
const deletingPayLoading = ref(false)
async function confirmDeletePayment() {
  if (!deletingPay.value) return
  deletingPayLoading.value = true
  try {
    await debtors.deletePayment(d.value.id, deletingPay.value.id)
    toast.success('ลบรายการชำระเรียบร้อย')
    deletingPay.value = null
  } finally { deletingPayLoading.value = false }
}

// payment modal
const showPay = ref(false)
const pay = ref({ amount: '', paid_date: dayjs().format('YYYY-MM-DD'), note: '', installment_no: null })
const payErrors = ref({})
const payLoading = ref(false)
const payInstallmentMeta = ref(null)  // { month, dueDate, payment } when opened from tick

function openPayBlank() {
  pay.value = { amount: '', paid_date: dayjs().format('YYYY-MM-DD'), note: '', installment_no: null }
  payInstallmentMeta.value = null
  payErrors.value = {}
  showPay.value = true
}

// ── Multi-tick selection in schedule table ───────────────────────────────────
const selectedMonths = ref(new Set())

function toggleScheduleRow(row) {
  if (row.status === 'paid' || row.status === 'late') {
    askUntick(row)  // already-paid rows → confirm-delete (single)
    return
  }
  const s = new Set(selectedMonths.value)
  if (s.has(row.month)) s.delete(row.month)
  else s.add(row.month)
  selectedMonths.value = s
}

const selectedRows = computed(() =>
  enrichedSchedule.value.filter(r => selectedMonths.value.has(r.month))
)

const selectedTotal = computed(() =>
  selectedRows.value.reduce((sum, r) => sum + (r.payment || 0), 0)
)

function clearSelection() {
  selectedMonths.value = new Set()
}

// ── Bulk pay modal ───────────────────────────────────────────────────────────
const showBulkPay = ref(false)
const bulkPay = ref({ paid_date: dayjs().format('YYYY-MM-DD'), note: '' })
const bulkPayErrors = ref({})
const bulkPayLoading = ref(false)

function openBulkPay() {
  if (!selectedRows.value.length) return
  bulkPay.value = { paid_date: dayjs().format('YYYY-MM-DD'), note: '' }
  bulkPayErrors.value = {}
  showBulkPay.value = true
}

async function submitBulkPay() {
  bulkPayErrors.value = {}
  if (!bulkPay.value.paid_date) {
    bulkPayErrors.value = { paid_date: 'กรุณาเลือกวันที่ชำระ' }
    return
  }
  const rows = selectedRows.value
  if (!rows.length) return
  bulkPayLoading.value = true
  try {
    // Sequential to keep installment_no order deterministic and avoid SQLite contention.
    for (const r of rows) {
      await debtors.addPayment(d.value.id, {
        amount: Math.round(r.payment * 100) / 100,
        paid_date: bulkPay.value.paid_date,
        note: bulkPay.value.note || null,
        installment_no: r.month,
      })
    }
    toast.success(`บันทึกชำระ ${rows.length} งวด • รวม ${formatBaht(selectedTotal.value)}`)
    showBulkPay.value = false
    clearSelection()
  } catch (e) {
    toast.error('บันทึกบางงวดไม่สำเร็จ')
  } finally {
    bulkPayLoading.value = false
  }
}

async function submitPayment() {
  payErrors.value = {}
  try {
    await paymentSchema.validate(pay.value, { abortEarly: false })
  } catch (e) {
    payErrors.value = Object.fromEntries((e.inner || []).map(x => [x.path, x.message]))
    return
  }
  payLoading.value = true
  try {
    const payload = {
      amount: Number(pay.value.amount),
      paid_date: pay.value.paid_date,
      note: pay.value.note || null,
    }
    if (pay.value.installment_no != null) payload.installment_no = pay.value.installment_no
    await debtors.addPayment(d.value.id, payload)
    toast.success(`บันทึกชำระ ${formatBaht(payload.amount)} เรียบร้อย`)
    showPay.value = false
    pay.value = { amount: '', paid_date: dayjs().format('YYYY-MM-DD'), note: '', installment_no: null }
    payInstallmentMeta.value = null
  } finally { payLoading.value = false }
}

// uncheck a paid row → confirm delete payment
const untickTarget = ref(null)
const untickLoading = ref(false)
function askUntick(row) {
  untickTarget.value = row
}
async function confirmUntick() {
  if (!untickTarget.value?.payment_id) return
  untickLoading.value = true
  try {
    await debtors.deletePayment(d.value.id, untickTarget.value.payment_id)
    toast.success(`ลบรายการชำระงวด #${untickTarget.value.month} แล้ว`)
    untickTarget.value = null
  } finally { untickLoading.value = false }
}

// rollover modal
const showRoll = ref(false)
const roll = ref({ new_principal: '', interest_rate: 2, installments: 6, start_date: dayjs().format('YYYY-MM-DD'), note: '' })
const rollErrors = ref({})
const rollLoading = ref(false)
function openRoll() {
  roll.value = {
    new_principal: Math.round(d.value?.balance || 0),
    interest_rate: d.value?.interest_rate || 2,
    installments: d.value?.installments || 6,
    start_date: dayjs().format('YYYY-MM-DD'),
    note: '',
  }
  showRoll.value = true
}
async function submitRoll() {
  rollErrors.value = {}
  try {
    await rolloverSchema.validate(roll.value, { abortEarly: false })
  } catch (e) {
    rollErrors.value = Object.fromEntries((e.inner || []).map(x => [x.path, x.message]))
    return
  }
  rollLoading.value = true
  try {
    const newD = await debtors.rollover(d.value.id, {
      ...roll.value,
      new_principal: Number(roll.value.new_principal),
      interest_rate: Number(roll.value.interest_rate),
      installments: parseInt(roll.value.installments),
    })
    toast.success(`ทบยอดสำเร็จ — สร้างสัญญาใหม่ #${newD.id}`)
    showRoll.value = false
    router.push(`/debtors/${newD.id}`)
  } finally { rollLoading.value = false }
}

// delete
const showDel = ref(false)
const delLoading = ref(false)
async function doDelete() {
  delLoading.value = true
  try {
    await debtors.remove(d.value.id)
    toast.success(`ลบ ${d.value.name} เรียบร้อย`)
    router.push('/debtors')
  } finally { delLoading.value = false }
}

const bannerColor = computed(() => {
  if (!d.value) return ''
  return {
    active: 'from-blue-50 to-blue-100/50 border-l-brand',
    near_due: 'from-amber-50 to-amber-100/40 border-l-amber-500',
    overdue: 'from-red-50 to-red-100/40 border-l-danger',
    closed: 'from-ink-100 to-ink-50 border-l-ink-400',
  }[d.value.status] || ''
})
</script>

<template>
  <div v-if="!loaded || !d" class="page-enter">
    <div class="animate-pulse-soft h-8 w-48 bg-ink-100 rounded mb-3" />
    <div class="animate-pulse-soft h-12 w-72 bg-ink-100 rounded mb-8" />
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <div class="lg:col-span-3 space-y-4">
        <div v-for="i in 4" :key="i" class="h-24 bg-white rounded-lg shadow-sm-soft animate-pulse-soft" />
      </div>
      <div class="lg:col-span-2 space-y-4">
        <div v-for="i in 3" :key="i" class="h-32 bg-white rounded-lg shadow-sm-soft animate-pulse-soft" />
      </div>
    </div>
  </div>

  <div v-else class="page-enter pb-12">
    <button @click="router.push('/debtors')" class="inline-flex items-center gap-1 text-[13px] text-ink-600 hover:text-ink-900 mb-3 transition-colors">
      <ChevronLeftIcon class="w-4 h-4" /> รายการลูกหนี้
    </button>

    <!-- header -->
    <div class="flex items-start justify-between gap-4 flex-wrap mb-6">
      <div class="flex items-center gap-4">
        <span class="w-14 h-14 rounded-full text-white font-semibold text-[18px] grid place-items-center"
          :style="{ background: avatarColor(d.name) }">{{ initials(d.name) }}</span>
        <div>
          <h1 class="t-h1 text-ink-900 leading-tight">{{ d.name }}</h1>
          <p class="t-small text-ink-400">{{ d.phone }} <span v-if="d.line_id">• LINE {{ d.line_id }}</span></p>
        </div>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <BaseButton variant="ghost" @click="router.push(`/debtors/${d.id}/edit`)">
          <template #icon-left><PencilSquareIcon class="w-4 h-4" /></template>แก้ไข
        </BaseButton>
        <BaseButton variant="secondary" @click="openRoll" :disabled="d.status === 'closed'">
          <template #icon-left><ArrowPathRoundedSquareIcon class="w-4 h-4" /></template>ทบยอด
        </BaseButton>
        <BaseButton variant="danger" @click="showDel = true">
          <template #icon-left><TrashIcon class="w-4 h-4" /></template>ลบ
        </BaseButton>
      </div>
    </div>

    <!-- status banner -->
    <div :class="['rounded-lg border-l-[3px] bg-gradient-to-r px-5 py-4 mb-6 flex items-center justify-between gap-4', bannerColor]">
      <div class="flex items-center gap-3">
        <BaseBadge :variant="statusVariant(d.status)" :pulse="d.status === 'overdue'">
          <CheckCircleIcon v-if="d.status === 'closed'" class="w-3.5 h-3.5" />
          <ExclamationCircleIcon v-else-if="d.status === 'overdue'" class="w-3.5 h-3.5" />
          <ClockIcon v-else class="w-3.5 h-3.5" />
          {{ statusLabel(d.status) }}
        </BaseBadge>
        <p class="text-[14px] text-ink-900">
          คงเหลือ <strong class="tabular-nums">{{ formatBaht(d.balance) }}</strong>
          <span v-if="d.is_open_ended" class="text-ink-600"> • ยืมแบบไม่กำหนดงวด</span>
          <span v-else-if="d.next_due_date" class="text-ink-600"> • งวดถัดไป {{ formatRelative(d.next_due_date) }}</span>
        </p>
      </div>
    </div>

    <!-- rollover indicator -->
    <div v-if="d.rollover_from_id" class="rounded-md border-l-[3px] border-l-amber-500 bg-amber-50 px-4 py-3 mb-6 flex items-center gap-3">
      <ArrowPathRoundedSquareIcon class="w-5 h-5 text-amber-600 flex-shrink-0" />
      <p class="text-[13px] text-amber-900">
        ยอดนี้เป็นยอดทบจากสัญญา <button @click="router.push(`/debtors/${d.rollover_from_id}`)" class="font-semibold underline">#{{ d.rollover_from_id }}</button>
        <span v-if="d.rolled_amount"> — เดิม {{ formatBaht(d.rolled_amount) }} → ใหม่ {{ formatBaht(d.principal) }}</span>
      </p>
    </div>

    <!-- two-column 60/40 -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <!-- Left 60% -->
      <div class="lg:col-span-3 space-y-6">
        <!-- payment timeline -->
        <section class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6">
          <div class="flex items-center justify-between mb-5">
            <h2 class="t-h3">ประวัติชำระ</h2>
            <BaseButton variant="primary" size="sm" @click="openPayBlank" :disabled="d.status === 'closed'">
              <template #icon-left><BanknotesIcon class="w-4 h-4" /></template>บันทึกชำระ
            </BaseButton>
          </div>

          <div v-if="!sortedPayments.length" class="text-center py-10 text-ink-400 text-[14px]">
            ยังไม่มีรายการชำระ
          </div>
          <div v-else class="relative">
            <div class="absolute left-[14px] top-2 bottom-2 w-px bg-ink-200" />
            <div v-for="(p, idx) in sortedPayments" :key="p.id"
              class="relative flex gap-4 pb-5 last:pb-0"
              :style="{ animation: `fade-up 320ms cubic-bezier(.16,1,.3,1) ${idx * 50}ms both` }">
              <div :class="['relative z-10 w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0',
                p.status === 'late' ? 'bg-amber-100' : 'bg-green-100']">
                <CheckCircleIcon :class="['w-4 h-4', p.status === 'late' ? 'text-amber-600' : 'text-green-600']" />
              </div>
              <div class="flex-1 flex items-start justify-between gap-3">
                <div>
                  <p class="text-[14px] font-medium text-ink-900">{{ formatBaht(p.amount) }}</p>
                  <p class="text-[12px] text-ink-400">{{ formatDate(p.paid_date) }}<span v-if="p.installment_no"> • งวด {{ p.installment_no }}</span></p>
                  <p v-if="p.note" class="text-[12px] text-ink-600 mt-1">"{{ p.note }}"</p>
                </div>
                <div class="flex items-center gap-1">
                  <BaseBadge :variant="p.status === 'late' ? 'warning' : 'success'">
                    {{ p.status === 'late' ? 'ล่าช้า' : 'ชำระแล้ว' }}
                  </BaseBadge>
                  <button @click="deletingPay = p" title="ลบรายการนี้"
                    class="p-1.5 rounded hover:bg-red-50 text-ink-400 hover:text-danger transition-colors">
                    <TrashIcon class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- schedule table — hidden for open-ended loans -->
        <section v-if="!d.is_open_ended" class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6">
          <h2 class="t-h3 mb-4">ตารางผ่อนชำระ</h2>
          <div class="overflow-x-auto">
            <table class="w-full text-[13px]">
              <thead>
                <tr class="text-left text-ink-400 border-b border-ink-100">
                  <th class="py-2 pr-3 font-medium w-[42px]" aria-label="ติ๊กชำระ"></th>
                  <th class="py-2 pr-3 font-medium">งวด</th>
                  <th class="py-2 pr-3 font-medium">วันครบ</th>
                  <th class="py-2 pr-3 font-medium text-right">ยอดต้อง</th>
                  <th class="py-2 pr-3 font-medium text-right">จ่ายแล้ว</th>
                  <th class="py-2 pr-3 font-medium text-right">คงเหลือ</th>
                  <th class="py-2 pr-3 font-medium">สถานะ</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in enrichedSchedule" :key="row.month"
                  class="border-b border-ink-100 last:border-0 group transition-colors"
                  :class="[
                    row.status === 'paid' || row.status === 'late' ? 'bg-green-50/30' : '',
                    selectedMonths.has(row.month) ? 'bg-brand-light/40' : ''
                  ]">
                  <td class="py-2.5 pr-3">
                    <label class="inline-flex items-center cursor-pointer select-none"
                      :title="(row.status === 'paid' || row.status === 'late') ? 'คลิกเพื่อยกเลิกการชำระ' : 'คลิกเพื่อเลือก/ยกเลิก'">
                      <input
                        type="checkbox"
                        :checked="row.status === 'paid' || row.status === 'late' || selectedMonths.has(row.month)"
                        :disabled="d.status === 'closed'"
                        @change="toggleScheduleRow(row)"
                        class="w-[18px] h-[18px] rounded border-ink-300 text-brand focus:ring-brand/40 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                      />
                    </label>
                  </td>
                  <td class="py-2.5 pr-3 text-ink-600">#{{ row.month }}</td>
                  <td class="py-2.5 pr-3">{{ formatDate(row.dueDate) }}</td>
                  <td class="py-2.5 pr-3 text-right tabular-nums">{{ formatBaht(row.payment) }}</td>
                  <td class="py-2.5 pr-3 text-right tabular-nums">{{ row.paid ? formatBaht(row.paid) : '—' }}</td>
                  <td class="py-2.5 pr-3 text-right tabular-nums">{{ formatBaht(Math.max(0, row.payment - (row.paid || 0))) }}</td>
                  <td class="py-2.5 pr-3">
                    <BaseBadge :variant="{paid:'success', late:'warning', overdue:'danger', pending:'neutral'}[row.status]">
                      {{ {paid:'ชำระแล้ว', late:'ล่าช้า', overdue:'เกินกำหนด', pending:'รอ'}[row.status] }}
                    </BaseBadge>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <!-- Right 40% -->
      <div class="lg:col-span-2 space-y-6">
        <section class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6">
          <h2 class="t-h3 mb-4">ข้อมูลลูกหนี้</h2>
          <dl class="space-y-2.5 text-[13px]">
            <div class="flex justify-between"><dt class="text-ink-400">ชื่อ</dt><dd class="text-ink-900 font-medium">{{ d.name }}</dd></div>
            <div class="flex justify-between"><dt class="text-ink-400">เบอร์โทร</dt><dd class="text-ink-900">{{ d.phone }}</dd></div>
            <div v-if="d.national_id" class="flex justify-between"><dt class="text-ink-400">เลขบัตร</dt><dd class="text-ink-900 tabular-nums">{{ d.national_id }}</dd></div>
            <div v-if="d.line_id" class="flex justify-between"><dt class="text-ink-400">LINE</dt><dd class="text-ink-900">{{ d.line_id }}</dd></div>
            <div v-if="d.address" class="flex justify-between gap-3"><dt class="text-ink-400 flex-shrink-0">ที่อยู่</dt><dd class="text-ink-900 text-right">{{ d.address }}</dd></div>
          </dl>
        </section>

        <section class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6">
          <h2 class="t-h3 mb-4">สรุปสัญญา</h2>
          <dl class="space-y-2.5 text-[13px]">
            <div class="flex justify-between"><dt class="text-ink-400">เงินต้น</dt><dd class="tabular-nums font-medium">{{ formatBaht(d.principal) }}</dd></div>
            <div v-if="d.is_open_ended" class="flex justify-between"><dt class="text-ink-400">รูปแบบ</dt><dd>ไม่กำหนดงวด</dd></div>
            <template v-else>
              <div class="flex justify-between"><dt class="text-ink-400">รูปแบบดอก</dt><dd>{{ ({flat:'Flat',compound:'ทบต้น',custom:'กำหนดเอง'})[d.interest_type] }}</dd></div>
            </template>
            <div class="flex justify-between"><dt class="text-ink-400">อัตราดอก</dt><dd class="tabular-nums">{{ d.interest_rate }}%/ด</dd></div>
            <div v-if="!d.is_open_ended" class="flex justify-between"><dt class="text-ink-400">จำนวนงวด</dt><dd class="tabular-nums">{{ d.installments }} เดือน</dd></div>
            <div class="flex justify-between"><dt class="text-ink-400">วันที่ยืม</dt><dd>{{ formatDate(d.start_date) }}</dd></div>
            <div v-if="!d.is_open_ended && d.first_due_date" class="flex justify-between"><dt class="text-ink-400">วันครบงวดแรก</dt><dd>{{ formatDate(d.first_due_date) }}</dd></div>
            <div class="h-px bg-ink-100 my-2"></div>
            <div class="flex justify-between"><dt class="text-ink-400">จ่ายแล้ว</dt><dd class="tabular-nums text-green-600">{{ formatBaht(d.total_paid) }}</dd></div>
            <div class="flex justify-between"><dt class="text-ink-400">คงเหลือ</dt><dd class="tabular-nums text-brand font-semibold">{{ formatBaht(d.balance) }}</dd></div>
          </dl>
        </section>

        <section v-if="d.bank || d.account_no || d.funding_source" class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6">
          <h2 class="t-h3 mb-4">ช่องทางการเงิน</h2>
          <div v-if="d.bank || d.account_no" class="mb-4">
            <p class="text-[11px] text-ink-400 uppercase tracking-wide mb-1">รับเงินคืน</p>
            <p class="text-[12px] text-ink-400">{{ d.bank }}</p>
            <p class="text-[16px] font-semibold tabular-nums">{{ d.account_no }}</p>
          </div>
          <div v-if="d.funding_source" :class="d.bank || d.account_no ? 'pt-4 border-t border-ink-100' : ''">
            <p class="text-[11px] text-ink-400 uppercase tracking-wide mb-1">แหล่งเงินที่ปล่อยกู้</p>
            <p class="text-[14px] text-ink-900">{{ d.funding_source }}</p>
          </div>
        </section>

        <section v-if="d.attachments?.length" class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6">
          <h2 class="t-h3 mb-4">เอกสารแนบ ({{ d.attachments.length }})</h2>
          <div class="grid grid-cols-2 gap-2.5">
            <a v-for="a in d.attachments" :key="a.id"
              :href="`${apiBase}/debtors/${d.id}/attachments/${a.id}/download`" target="_blank"
              class="aspect-square bg-ink-50 rounded-md flex flex-col items-center justify-center p-3 hover:bg-ink-100 transition-colors group">
              <DocumentArrowDownIcon class="w-7 h-7 text-ink-400 group-hover:text-brand mb-2" />
              <p class="text-[11px] text-ink-600 text-center line-clamp-2 break-all">{{ a.original_name }}</p>
              <p class="text-[10px] text-ink-400 mt-1">{{ ({contract:'สัญญา',id_card:'บัตร',slip:'สลิป',collateral:'หลักทรัพย์'})[a.category] }}</p>
            </a>
          </div>
        </section>

        <section v-if="d.notes" class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6">
          <h2 class="t-h3 mb-2">หมายเหตุ</h2>
          <p class="text-[13px] text-ink-600 whitespace-pre-wrap">{{ d.notes }}</p>
        </section>
      </div>
    </div>

    <!-- Sticky bulk-action toolbar for selected schedule rows -->
    <transition
      enter-active-class="transition duration-220 ease-apple"
      enter-from-class="opacity-0 translate-y-3"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-apple"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-3">
      <div v-if="selectedRows.length"
        class="fixed bottom-4 left-1/2 -translate-x-1/2 z-30 bg-white shadow-lg-soft rounded-full border border-ink-100 px-4 py-2 flex items-center gap-3">
        <p class="text-[13px] text-ink-900">
          เลือก <strong class="text-brand">{{ selectedRows.length }}</strong> งวด
          <span class="text-ink-400">• รวม</span>
          <strong class="tabular-nums ml-1">{{ formatBaht(selectedTotal) }}</strong>
        </p>
        <BaseButton variant="ghost" size="sm" @click="clearSelection">ยกเลิก</BaseButton>
        <BaseButton variant="primary" size="sm" @click="openBulkPay">
          <template #icon-left><BanknotesIcon class="w-4 h-4" /></template>
          บันทึกชำระ
        </BaseButton>
      </div>
    </transition>

    <!-- Bulk pay modal -->
    <BaseModal :open="showBulkPay" :title="`บันทึกชำระ ${selectedRows.length} งวด`" size="md" @close="showBulkPay = false">
      <div class="space-y-4">
        <div class="max-h-[200px] overflow-y-auto rounded-md border border-ink-100">
          <table class="w-full text-[12px]">
            <thead class="bg-ink-50 sticky top-0">
              <tr class="text-left text-ink-400">
                <th class="px-3 py-2 font-medium">งวด</th>
                <th class="px-3 py-2 font-medium">วันครบ</th>
                <th class="px-3 py-2 font-medium text-right">ยอด</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in selectedRows" :key="r.month" class="border-t border-ink-100">
                <td class="px-3 py-1.5 text-ink-600">#{{ r.month }}</td>
                <td class="px-3 py-1.5">{{ formatDate(r.dueDate) }}</td>
                <td class="px-3 py-1.5 text-right tabular-nums">{{ formatBaht(r.payment) }}</td>
              </tr>
            </tbody>
            <tfoot class="bg-ink-50/50 border-t border-ink-100">
              <tr>
                <td colspan="2" class="px-3 py-2 text-ink-400">รวม</td>
                <td class="px-3 py-2 text-right tabular-nums font-semibold">{{ formatBaht(selectedTotal) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
        <BaseInput v-model="bulkPay.paid_date" type="date" label="วันที่ชำระ (ใช้กับทุกงวด)" :error="bulkPayErrors.paid_date" required />
        <BaseTextarea v-model="bulkPay.note" label="หมายเหตุ" rows="2" placeholder="ใช้กับทุกงวด (optional)" />
      </div>
      <template #actions>
        <BaseButton variant="ghost" @click="showBulkPay = false">ยกเลิก</BaseButton>
        <BaseButton variant="primary" :loading="bulkPayLoading" @click="submitBulkPay">
          ยืนยันบันทึกชำระ
        </BaseButton>
      </template>
    </BaseModal>

    <!-- Untick confirm (single paid row) -->
    <ConfirmModal :open="!!untickTarget"
      title="ยกเลิกการชำระงวดนี้?"
      :message="untickTarget ? `ลบรายการชำระงวด #${untickTarget.month} (${formatBaht(untickTarget.paid)}) — ยอดคงเหลือจะถูกคำนวณใหม่` : ''"
      confirm-text="ยืนยันยกเลิก" variant="danger" :loading="untickLoading"
      @confirm="confirmUntick" @close="untickTarget = null" />

    <!-- Payment modal -->
    <BaseModal :open="showPay" title="บันทึกชำระเงิน" @close="showPay = false">
      <div class="space-y-4">
        <BaseInput v-model="pay.amount" type="number" label="จำนวนเงิน (฿)" prefix="฿" :error="payErrors.amount" required />
        <BaseInput v-model="pay.paid_date" type="date" label="วันที่ชำระ" :error="payErrors.paid_date" required />
        <BaseTextarea v-model="pay.note" label="หมายเหตุ" rows="2" placeholder="optional..." />
      </div>
      <template #actions>
        <BaseButton variant="ghost" @click="showPay = false">ยกเลิก</BaseButton>
        <BaseButton variant="primary" :loading="payLoading" @click="submitPayment">บันทึกชำระ</BaseButton>
      </template>
    </BaseModal>

    <!-- Rollover modal -->
    <BaseModal :open="showRoll" title="ทบยอด (Rollover)" size="md" @close="showRoll = false">
      <p class="text-[13px] text-ink-600 mb-4">
        สร้างสัญญาใหม่จากยอดคงเหลือ ({{ formatBaht(d?.balance) }}) สัญญาเดิมจะถูกปิด
      </p>
      <div class="space-y-4">
        <BaseInput v-model="roll.new_principal" type="number" label="ยอดเงินต้นใหม่ (฿)" prefix="฿" :error="rollErrors.new_principal" required />
        <div class="grid grid-cols-2 gap-3">
          <BaseInput v-model="roll.interest_rate" type="number" label="ดอกเบี้ย (%/ด)" suffix="%" :error="rollErrors.interest_rate" required />
          <BaseInput v-model="roll.installments" type="number" label="จำนวนงวด" :error="rollErrors.installments" required />
        </div>
        <BaseInput v-model="roll.start_date" type="date" label="วันที่เริ่ม" :error="rollErrors.start_date" required />
        <BaseTextarea v-model="roll.note" label="หมายเหตุ" rows="2" />
      </div>
      <template #actions>
        <BaseButton variant="ghost" @click="showRoll = false">ยกเลิก</BaseButton>
        <BaseButton variant="primary" :loading="rollLoading" @click="submitRoll">ยืนยันทบยอด</BaseButton>
      </template>
    </BaseModal>

    <ConfirmModal :open="showDel"
      :title="`ลบ ${d?.name}?`"
      :message="`ข้อมูลและรายการชำระทั้งหมดจะถูกลบถาวร — การกระทำนี้ไม่สามารถยกเลิกได้`"
      confirm-text="ลบถาวร" variant="danger" :loading="delLoading"
      @confirm="doDelete" @close="showDel = false" />

    <ConfirmModal :open="!!deletingPay"
      title="ลบรายการชำระ?"
      :message="deletingPay ? `ลบรายการชำระ ${formatBaht(deletingPay.amount)} วันที่ ${formatDate(deletingPay.paid_date)} — ยอดคงเหลือจะถูกคำนวณใหม่` : ''"
      confirm-text="ลบรายการนี้" variant="danger" :loading="deletingPayLoading"
      @confirm="confirmDeletePayment" @close="deletingPay = null" />
  </div>
</template>
