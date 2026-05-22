<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import BaseInput from '../ui/BaseInput.vue'
import BaseSelect from '../ui/BaseSelect.vue'
import BaseTextarea from '../ui/BaseTextarea.vue'
import BaseButton from '../ui/BaseButton.vue'
import BaseUpload from '../ui/BaseUpload.vue'
import { useInterestCalc } from '../../composables/useInterestCalc'
import { useDebtorsStore } from '../../stores/debtors'
import { debtorSchema } from '../../utils/validators'
import { formatBaht, formatDate } from '../../utils/formatters'
import dayjs from 'dayjs'

const props = defineProps({
  mode: { type: String, default: 'create' }, // create | edit
  initial: { type: Object, default: null },
})

const router = useRouter()
const debtors = useDebtorsStore()
const toast = useToast()

function fresh() {
  const today = dayjs().format('YYYY-MM-DD')
  return {
    name: '', phone: '', national_id: '', line_id: '', address: '',
    principal: '', interest_rate: 2, interest_type: 'flat', installments: 6,
    start_date: today,
    bank: 'SCB', account_no: '',
    notes: '',
  }
}
const form = ref(props.initial ? { ...fresh(), ...props.initial } : fresh())
const contractFiles = ref([])
const idFiles = ref([])
const slipFiles = ref([])
const collFiles = ref([])

const errors = ref({})
const submitting = ref(false)

watch(() => props.initial, (v) => { if (v) form.value = { ...fresh(), ...v } })

const interestTypes = [
  { value: 'flat', label: 'Flat Rate' },
  { value: 'compound', label: 'ทบต้น (Compound)' },
  { value: 'custom', label: 'กำหนดเอง' },
]
const banks = [
  { value: 'SCB', label: 'SCB - ไทยพาณิชย์' },
  { value: 'KBANK', label: 'KBANK - กสิกรไทย' },
  { value: 'BBL', label: 'BBL - กรุงเทพ' },
  { value: 'KTB', label: 'KTB - กรุงไทย' },
  { value: 'TTB', label: 'TTB - ทหารไทยธนชาต' },
  { value: 'BAY', label: 'BAY - กรุงศรี' },
  { value: 'PROMPT_PAY', label: 'พร้อมเพย์' },
]

const principalRef = computed(() => Number(form.value.principal) || 0)
const rateRef = computed(() => Number(form.value.interest_rate) || 0)
const monthsRef = computed(() => parseInt(form.value.installments) || 1)
const typeRef = computed(() => form.value.interest_type)
const startRef = computed(() => form.value.start_date)

const { totalInterest, monthlyPayment, totalPayment, schedule } = useInterestCalc({
  principal: principalRef, ratePerMonth: rateRef, months: monthsRef,
  interestType: typeRef, startDate: startRef,
})

async function copyAccount() {
  if (!form.value.account_no) return
  try {
    await navigator.clipboard.writeText(form.value.account_no)
    toast.success('คัดลอกเลขบัญชีแล้ว', { timeout: 1500 })
  } catch {}
}

async function uploadAttachments(debtorId) {
  const jobs = []
  for (const f of contractFiles.value) jobs.push(debtors.uploadAttachment(debtorId, 'contract', f))
  for (const f of idFiles.value) jobs.push(debtors.uploadAttachment(debtorId, 'id_card', f))
  for (const f of slipFiles.value) jobs.push(debtors.uploadAttachment(debtorId, 'slip', f))
  for (const f of collFiles.value) jobs.push(debtors.uploadAttachment(debtorId, 'collateral', f))
  await Promise.allSettled(jobs)
}

async function submit() {
  errors.value = {}
  try {
    await debtorSchema.validate(form.value, { abortEarly: false })
  } catch (e) {
    errors.value = Object.fromEntries((e.inner || []).map(x => [x.path, x.message]))
    const first = document.querySelector('[data-error="true"]')
    first?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    toast.error('กรุณากรอกข้อมูลให้ครบถ้วน')
    return
  }
  submitting.value = true
  try {
    const payload = {
      ...form.value,
      principal: Number(form.value.principal),
      interest_rate: Number(form.value.interest_rate),
      installments: parseInt(form.value.installments),
    }
    let d
    if (props.mode === 'edit' && props.initial?.id) {
      d = await debtors.update(props.initial.id, payload)
      await uploadAttachments(d.id)
      toast.success(`บันทึก ${d.name} เรียบร้อย`)
      router.push(`/debtors/${d.id}`)
    } else {
      d = await debtors.create(payload)
      await uploadAttachments(d.id)
      toast.success(`เพิ่ม ${d.name} เรียบร้อย`)
      router.push(`/debtors/${d.id}`)
    }
  } catch (e) {
    // toast already shown by global handler
  } finally {
    submitting.value = false
  }
}

function onUploadError(msg) { toast.error(msg) }
</script>

<template>
  <form @submit.prevent="submit" class="space-y-6 pb-32">
    <!-- Section 1: personal -->
    <section class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6 sm:p-7">
      <h2 class="t-h3 mb-4 flex items-center gap-2"><span class="w-1.5 h-1.5 rounded-full bg-brand"></span> ข้อมูลส่วนตัว</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div :data-error="!!errors.name"><BaseInput v-model="form.name" label="ชื่อ-นามสกุล" :error="errors.name" required /></div>
        <div :data-error="!!errors.phone"><BaseInput v-model="form.phone" label="เบอร์โทร" :error="errors.phone" required placeholder="08XXXXXXXX" /></div>
        <BaseInput v-model="form.national_id" label="เลขบัตรประชาชน" :error="errors.national_id" />
        <BaseInput v-model="form.line_id" label="LINE ID / ช่องทางติดต่อ" />
        <div class="sm:col-span-2"><BaseTextarea v-model="form.address" label="ที่อยู่" rows="3" /></div>
      </div>
    </section>

    <!-- Section 2: loan + auto-calc preview -->
    <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6 sm:p-7 lg:col-span-2">
        <h2 class="t-h3 mb-4 flex items-center gap-2"><span class="w-1.5 h-1.5 rounded-full bg-brand"></span> ข้อมูลการยืม</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div :data-error="!!errors.principal">
            <BaseInput v-model="form.principal" type="number" label="จำนวนเงิน (฿)" prefix="฿" :error="errors.principal" required />
          </div>
          <div :data-error="!!errors.interest_rate">
            <BaseInput v-model="form.interest_rate" type="number" label="ดอกเบี้ย (%/เดือน)" suffix="%" :error="errors.interest_rate" required />
          </div>
          <div :data-error="!!errors.installments">
            <BaseInput v-model="form.installments" type="number" label="จำนวนงวด (เดือน)" :error="errors.installments" required />
          </div>
          <BaseInput v-model="form.start_date" type="date" label="วันที่ยืม" :error="errors.start_date" required />
          <div class="sm:col-span-2">
            <p class="t-caption mb-2 ml-1">รูปแบบการคิดดอก</p>
            <div class="flex flex-wrap gap-2">
              <button v-for="t in interestTypes" :key="t.value" type="button" @click="form.interest_type = t.value"
                :class="['h-9 px-4 rounded-full text-[13px] font-medium transition-all duration-200 border',
                  form.interest_type === t.value
                    ? 'bg-brand text-white border-brand shadow-sm-soft'
                    : 'bg-white text-ink-600 border-ink-200 hover:border-ink-400']">
                {{ t.label }}
              </button>
            </div>
          </div>
        </div>
      </div>
      <!-- live preview -->
      <div class="glass rounded-lg p-6 self-start sticky top-[68px]">
        <p class="t-caption mb-3">สรุปการคำนวณ</p>
        <dl class="space-y-2.5">
          <div class="flex justify-between"><dt class="text-[13px] text-ink-600">เงินต้น</dt>
            <dd class="text-[15px] font-medium tabular-nums">{{ formatBaht(principalRef) }}</dd></div>
          <div class="flex justify-between"><dt class="text-[13px] text-ink-600">ดอกเบี้ยรวม</dt>
            <dd class="text-[15px] font-medium tabular-nums text-green-600">{{ formatBaht(totalInterest) }}</dd></div>
          <div class="flex justify-between"><dt class="text-[13px] text-ink-600">ผ่อน/เดือน</dt>
            <dd class="text-[15px] font-medium tabular-nums">{{ formatBaht(monthlyPayment) }}</dd></div>
          <div class="h-px bg-ink-200/60 my-2"></div>
          <div class="flex justify-between items-baseline">
            <dt class="text-[13px] text-ink-600">รวมทั้งสิ้น</dt>
            <dd class="text-[20px] font-semibold tabular-nums text-brand">{{ formatBaht(totalPayment) }}</dd>
          </div>
        </dl>
        <p v-if="schedule.length" class="mt-4 text-[11px] text-ink-400">
          งวดแรกครบกำหนด {{ formatDate(schedule[0].dueDate, 'D MMM YYYY') }}
        </p>
      </div>
    </section>

    <!-- Section 3: payment channel -->
    <section class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6 sm:p-7">
      <h2 class="t-h3 mb-4 flex items-center gap-2"><span class="w-1.5 h-1.5 rounded-full bg-brand"></span> ช่องทางรับชำระ</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseSelect v-model="form.bank" label="ธนาคาร" :options="banks" />
        <div class="relative">
          <BaseInput v-model="form.account_no" label="เลขบัญชี / พร้อมเพย์" />
          <button type="button" @click="copyAccount" v-if="form.account_no"
            class="absolute right-2 top-9 px-2.5 py-1 rounded-md text-[11px] text-brand bg-brand-light hover:bg-brand-light/80 font-medium">
            คัดลอก
          </button>
        </div>
      </div>
    </section>

    <!-- Section 4: attachments -->
    <section class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6 sm:p-7">
      <h2 class="t-h3 mb-4 flex items-center gap-2"><span class="w-1.5 h-1.5 rounded-full bg-brand"></span> แนบเอกสาร</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <BaseUpload v-model="contractFiles" label="สัญญา" hint="jpg/png/pdf • ≤10MB" @error="onUploadError" />
        <BaseUpload v-model="idFiles" label="บัตรประชาชน" hint="jpg/png/pdf • ≤10MB" @error="onUploadError" />
        <BaseUpload v-model="slipFiles" label="สลิปโอนเงิน" hint="jpg/png/pdf • ≤10MB" @error="onUploadError" />
        <BaseUpload v-model="collFiles" label="หลักทรัพย์ค้ำประกัน" hint="jpg/png/pdf • ≤10MB" @error="onUploadError" />
      </div>
    </section>

    <!-- Section 5: notes -->
    <section class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6 sm:p-7">
      <h2 class="t-h3 mb-4 flex items-center gap-2"><span class="w-1.5 h-1.5 rounded-full bg-brand"></span> หมายเหตุ</h2>
      <BaseTextarea v-model="form.notes" :maxlength="500" rows="4" placeholder="บันทึกเพิ่มเติม..." :error="errors.notes" />
    </section>

    <!-- Sticky footer -->
    <div class="fixed bottom-0 left-0 right-0 z-30 border-t border-ink-100"
      style="background: rgba(255,255,255,0.85); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);">
      <div class="max-w-[1400px] mx-auto px-6 lg:px-12 py-3 flex items-center justify-between gap-3">
        <BaseButton variant="ghost" @click="router.back()">ยกเลิก</BaseButton>
        <BaseButton type="submit" variant="primary" :loading="submitting">
          {{ mode === 'edit' ? 'บันทึกการแก้ไข' : 'บันทึกลูกหนี้' }}
        </BaseButton>
      </div>
    </div>
  </form>
</template>
