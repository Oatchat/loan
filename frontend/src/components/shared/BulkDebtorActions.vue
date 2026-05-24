<script setup>
import { ref, computed } from 'vue'
import { useToast } from 'vue-toastification'
import { TrashIcon, BanknotesIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import BaseButton from '../ui/BaseButton.vue'
import BaseModal from '../ui/BaseModal.vue'
import BaseInput from '../ui/BaseInput.vue'
import BaseTextarea from '../ui/BaseTextarea.vue'
import ConfirmModal from './ConfirmModal.vue'
import { useDebtorsStore } from '../../stores/debtors'
import { nextUnpaidInstallment } from '../../composables/useInterestCalc'
import { formatBaht, formatDate } from '../../utils/formatters'
import dayjs from 'dayjs'

const props = defineProps({
  debtors: { type: Array, required: true },         // full debtor objects available in caller's store
  selectedIds: { type: Array, required: true },     // array of debtor.id
})
const emit = defineEmits(['update:selectedIds', 'changed'])

const store = useDebtorsStore()
const toast = useToast()

const selectedDebtors = computed(() => {
  const ids = new Set(props.selectedIds)
  return props.debtors.filter(d => ids.has(d.id))
})

function clearSelection() {
  emit('update:selectedIds', [])
}

// ── Bulk delete ──────────────────────────────────────────────────────────────
const showDelete = ref(false)
const deleteLoading = ref(false)
async function doDelete() {
  if (!selectedDebtors.value.length) return
  deleteLoading.value = true
  try {
    let ok = 0, fail = 0
    for (const d of selectedDebtors.value) {
      try { await store.remove(d.id); ok++ } catch { fail++ }
    }
    if (fail === 0) toast.success(`ลบ ${ok} รายการเรียบร้อย`)
    else toast.warning(`ลบสำเร็จ ${ok} • ผิดพลาด ${fail}`)
    showDelete.value = false
    clearSelection()
    emit('changed')
  } finally { deleteLoading.value = false }
}

// ── Bulk pay next installment ────────────────────────────────────────────────
const showPayNext = ref(false)
const payNext = ref({ paid_date: dayjs().format('YYYY-MM-DD'), note: '' })
const payNextErrors = ref({})
const payNextLoading = ref(false)

const payNextPreview = computed(() =>
  selectedDebtors.value.map(d => {
    const inst = nextUnpaidInstallment(d)
    return {
      id: d.id,
      name: d.name,
      eligible: !!inst && d.status !== 'closed',
      reason: !inst ? 'ปิดบัญชีแล้ว' : (d.status === 'closed' ? 'ปิดบัญชีแล้ว' : null),
      month: inst?.month ?? null,
      amount: inst?.payment ?? 0,
      dueDate: inst?.dueDate ?? null,
    }
  })
)
const payNextEligible = computed(() => payNextPreview.value.filter(r => r.eligible))
const payNextSkipped = computed(() => payNextPreview.value.filter(r => !r.eligible))
const payNextTotal = computed(() => payNextEligible.value.reduce((s, r) => s + r.amount, 0))

function openPayNext() {
  payNext.value = { paid_date: dayjs().format('YYYY-MM-DD'), note: '' }
  payNextErrors.value = {}
  showPayNext.value = true
}

async function submitPayNext() {
  payNextErrors.value = {}
  if (!payNext.value.paid_date) {
    payNextErrors.value = { paid_date: 'กรุณาเลือกวันที่ชำระ' }
    return
  }
  if (!payNextEligible.value.length) return
  payNextLoading.value = true
  let ok = 0, fail = 0
  try {
    for (const r of payNextEligible.value) {
      try {
        await store.addPayment(r.id, {
          amount: Math.round(r.amount * 100) / 100,
          paid_date: payNext.value.paid_date,
          note: payNext.value.note || null,
          installment_no: r.month,
        })
        ok++
      } catch { fail++ }
    }
    if (fail === 0) toast.success(`บันทึกชำระ ${ok} ราย • รวม ${formatBaht(payNextTotal.value)}`)
    else toast.warning(`สำเร็จ ${ok} • ผิดพลาด ${fail}`)
    showPayNext.value = false
    clearSelection()
    emit('changed')
  } finally { payNextLoading.value = false }
}
</script>

<template>
  <teleport to="body">
    <transition
      enter-active-class="transition duration-220 ease-apple"
      enter-from-class="opacity-0 translate-y-3"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-apple"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-3">
      <div v-if="selectedDebtors.length"
        class="fixed bottom-4 left-1/2 -translate-x-1/2 z-30 bg-white shadow-lg-soft rounded-full border border-ink-100 pl-4 pr-2 py-2 flex items-center gap-3 max-w-[calc(100vw-2rem)]">
        <p class="text-[13px] text-ink-900 whitespace-nowrap">
          เลือก <strong class="text-brand">{{ selectedDebtors.length }}</strong> ราย
        </p>
        <div class="h-5 w-px bg-ink-200"></div>
        <BaseButton variant="ghost" size="sm" @click="openPayNext">
          <template #icon-left><BanknotesIcon class="w-4 h-4" /></template>
          ชำระงวดถัดไป
        </BaseButton>
        <BaseButton variant="ghost" size="sm" @click="showDelete = true" class="!text-danger hover:!bg-red-50">
          <template #icon-left><TrashIcon class="w-4 h-4" /></template>
          ลบ
        </BaseButton>
        <button @click="clearSelection" class="p-2 rounded-full hover:bg-ink-100 text-ink-400" aria-label="ยกเลิกการเลือก">
          <XMarkIcon class="w-4 h-4" />
        </button>
      </div>
    </transition>
  </teleport>

  <!-- Bulk delete confirm -->
  <ConfirmModal :open="showDelete"
    :title="`ลบลูกหนี้ ${selectedDebtors.length} ราย?`"
    :message="`ข้อมูลและรายการชำระทั้งหมดของลูกหนี้ที่เลือกจะถูกลบถาวร — การกระทำนี้ไม่สามารถยกเลิกได้`"
    confirm-text="ลบถาวร" variant="danger" :loading="deleteLoading"
    @confirm="doDelete" @close="showDelete = false" />

  <!-- Bulk pay-next modal -->
  <BaseModal :open="showPayNext"
    :title="`ชำระงวดถัดไป ${payNextEligible.length} ราย`"
    size="md" @close="showPayNext = false">
    <div class="space-y-4">
      <div v-if="payNextEligible.length" class="max-h-[220px] overflow-y-auto rounded-md border border-ink-100">
        <table class="w-full text-[12px]">
          <thead class="bg-ink-50 sticky top-0">
            <tr class="text-left text-ink-400">
              <th class="px-3 py-2 font-medium">ลูกหนี้</th>
              <th class="px-3 py-2 font-medium">งวด</th>
              <th class="px-3 py-2 font-medium">วันครบ</th>
              <th class="px-3 py-2 font-medium text-right">ยอด</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in payNextEligible" :key="r.id" class="border-t border-ink-100">
              <td class="px-3 py-1.5 text-ink-900 truncate max-w-[160px]">{{ r.name }}</td>
              <td class="px-3 py-1.5 text-ink-600">#{{ r.month }}</td>
              <td class="px-3 py-1.5 text-ink-600">{{ formatDate(r.dueDate) }}</td>
              <td class="px-3 py-1.5 text-right tabular-nums">{{ formatBaht(r.amount) }}</td>
            </tr>
          </tbody>
          <tfoot class="bg-ink-50/50 border-t border-ink-100">
            <tr>
              <td colspan="3" class="px-3 py-2 text-ink-400">รวม</td>
              <td class="px-3 py-2 text-right tabular-nums font-semibold">{{ formatBaht(payNextTotal) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div v-if="payNextSkipped.length" class="text-[12px] text-ink-400 rounded-md bg-ink-50 px-3 py-2">
        ข้าม {{ payNextSkipped.length }} ราย:
        <span v-for="(r, i) in payNextSkipped" :key="r.id">
          {{ r.name }} ({{ r.reason || 'ไม่มีงวดถัดไป' }}){{ i < payNextSkipped.length - 1 ? ', ' : '' }}
        </span>
      </div>

      <BaseInput v-model="payNext.paid_date" type="date" label="วันที่ชำระ (ใช้กับทุกราย)" :error="payNextErrors.paid_date" required />
      <BaseTextarea v-model="payNext.note" label="หมายเหตุ" rows="2" placeholder="optional..." />
    </div>
    <template #actions>
      <BaseButton variant="ghost" @click="showPayNext = false">ยกเลิก</BaseButton>
      <BaseButton variant="primary" :loading="payNextLoading" :disabled="!payNextEligible.length" @click="submitPayNext">
        ยืนยันบันทึก
      </BaseButton>
    </template>
  </BaseModal>
</template>
