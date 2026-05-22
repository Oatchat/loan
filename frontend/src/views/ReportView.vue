<script setup>
import { onMounted, ref, computed, watch } from 'vue'
import { Bar, Doughnut, Line } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement,
  ArcElement, Tooltip, Legend, Title, Filler,
} from 'chart.js'
import { api } from '../plugins/axios'
import { formatBaht, statusLabel } from '../utils/formatters'
import { ArrowDownTrayIcon, DocumentTextIcon, TableCellsIcon } from '@heroicons/vue/24/outline'
import BaseButton from '../components/ui/BaseButton.vue'
import StatCard from '../components/ui/StatCard.vue'

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Tooltip, Legend, Title, Filler)

const presets = [
  { value: '30', label: '30 วันล่าสุด' },
  { value: '90', label: 'ไตรมาสล่าสุด' },
  { value: '365', label: 'ปีล่าสุด' },
  { value: 'all', label: 'ทั้งหมด' },
]
const range = ref('365')
const data = ref(null)
const loading = ref(false)

async function fetchData() {
  loading.value = true
  try {
    const params = {}
    if (range.value !== 'all') {
      const d = new Date()
      d.setDate(d.getDate() - Number(range.value))
      params.start = d.toISOString().slice(0, 10)
    }
    const res = await api.get('/reports/summary', { params })
    data.value = res.data
  } finally { loading.value = false }
}

watch(range, fetchData)
onMounted(fetchData)

const summary = computed(() => data.value?.summary)
const monthly = computed(() => data.value?.monthly || [])
const statusBreakdown = computed(() => data.value?.status_breakdown || {})

const npl = computed(() => {
  if (!summary.value || summary.value.total_debtors === 0) return 0
  return ((summary.value.overdue_count / summary.value.total_debtors) * 100).toFixed(1)
})

const barData = computed(() => ({
  labels: monthly.value.map(m => m.month),
  datasets: [{
    label: 'ปล่อยกู้', backgroundColor: '#0071E3',
    data: monthly.value.map(m => m.issued), borderRadius: 6, barThickness: 18,
  }, {
    label: 'เก็บได้', backgroundColor: '#30D158',
    data: monthly.value.map(m => m.collected), borderRadius: 6, barThickness: 18,
  }],
}))

const doughnutData = computed(() => {
  const keys = ['active', 'near_due', 'overdue', 'closed']
  return {
    labels: keys.map(statusLabel),
    datasets: [{
      data: keys.map(k => statusBreakdown.value[k] || 0),
      backgroundColor: ['#0071E3', '#FF9F0A', '#FF3B30', '#86868B'],
      borderColor: '#fff', borderWidth: 3,
    }],
  }
})

const lineData = computed(() => {
  let acc = 0
  return {
    labels: monthly.value.map(m => m.month),
    datasets: [{
      label: 'ดอกเบี้ยสะสม', data: monthly.value.map(m => (acc += m.interest)),
      borderColor: '#30D158', backgroundColor: 'rgba(48,209,88,0.12)',
      fill: true, tension: 0.35, pointRadius: 3, pointHoverRadius: 5,
    }],
  }
})

const chartOpts = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 12 } } } },
  scales: { y: { ticks: { font: { size: 11 } } }, x: { ticks: { font: { size: 11 } } } },
}
const doughnutOpts = {
  responsive: true, maintainAspectRatio: false, cutout: '65%',
  plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 12 } } } },
}

function exportCSV() {
  const headers = ['Month', 'Issued', 'Collected', 'Interest']
  const lines = [headers.join(',')]
  monthly.value.forEach(m => lines.push([m.month, m.issued, m.collected, m.interest].join(',')))
  const blob = new Blob(['﻿' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `debttrack-report-${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="page-enter space-y-6">
    <div class="flex items-end justify-between gap-4 flex-wrap">
      <div>
        <p class="t-caption mb-1">ภาพรวมธุรกิจ</p>
        <h1 class="t-h1 text-ink-900">รายงาน</h1>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <div class="flex items-center gap-1 bg-white rounded-full p-1 border border-ink-200">
          <button v-for="p in presets" :key="p.value" @click="range = p.value"
            :class="['h-8 px-3 rounded-full text-[12px] font-medium transition-all duration-200',
              range === p.value ? 'bg-brand text-white' : 'text-ink-600 hover:text-ink-900']">
            {{ p.label }}
          </button>
        </div>
        <BaseButton variant="secondary" size="sm" @click="exportCSV">
          <template #icon-left><ArrowDownTrayIcon class="w-4 h-4" /></template>Export CSV
        </BaseButton>
      </div>
    </div>

    <!-- KPI row -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4" v-if="summary">
      <StatCard label="ปล่อยกู้รวม" :value="summary.total_principal" prefix="฿" accent="info" :icon="DocumentTextIcon" />
      <StatCard label="เก็บได้" :value="summary.total_paid" prefix="฿" accent="success" :icon="TableCellsIcon" />
      <StatCard label="ดอกเบี้ย" :value="summary.total_interest_earned" prefix="฿" accent="warning" />
      <StatCard label="NPL %" :value="npl" accent="danger" />
    </div>

    <!-- charts -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6 lg:col-span-2">
        <h2 class="t-h3 mb-4">ยอดปล่อยกู้ / เก็บได้ รายเดือน</h2>
        <div class="h-72"><Bar v-if="monthly.length" :data="barData" :options="chartOpts" /></div>
      </div>
      <div class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6">
        <h2 class="t-h3 mb-4">สัดส่วนสถานะ</h2>
        <div class="h-72"><Doughnut v-if="summary?.total_debtors" :data="doughnutData" :options="doughnutOpts" /></div>
      </div>
    </div>

    <div class="bg-white rounded-lg shadow-sm-soft border border-ink-100 p-6">
      <h2 class="t-h3 mb-4">ดอกเบี้ยสะสม</h2>
      <div class="h-72"><Line v-if="monthly.length" :data="lineData" :options="chartOpts" /></div>
    </div>

    <!-- detailed table -->
    <div class="bg-white rounded-lg shadow-sm-soft border border-ink-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-ink-100">
        <h2 class="t-h3">ตารางรายละเอียดรายเดือน</h2>
      </div>
      <table class="w-full text-[13px]">
        <thead class="bg-ink-50">
          <tr>
            <th class="t-caption text-left px-5 py-3 text-ink-400">เดือน</th>
            <th class="t-caption text-right px-5 py-3 text-ink-400">ปล่อยกู้</th>
            <th class="t-caption text-right px-5 py-3 text-ink-400">เก็บได้</th>
            <th class="t-caption text-right px-5 py-3 text-ink-400">ดอกเบี้ย</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in monthly" :key="m.month" class="border-b border-ink-100 last:border-0 hover:bg-ink-50">
            <td class="px-5 py-3 tabular-nums">{{ m.month }}</td>
            <td class="px-5 py-3 text-right tabular-nums">{{ formatBaht(m.issued) }}</td>
            <td class="px-5 py-3 text-right tabular-nums text-green-600">{{ formatBaht(m.collected) }}</td>
            <td class="px-5 py-3 text-right tabular-nums text-amber-600">{{ formatBaht(m.interest) }}</td>
          </tr>
          <tr v-if="!monthly.length">
            <td colspan="4" class="px-5 py-10 text-center text-ink-400">ยังไม่มีข้อมูล</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
