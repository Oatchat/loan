<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  label: String,
  value: { type: [Number, String], default: 0 },
  prefix: { type: String, default: '' },
  trend: { type: Number, default: null }, // +12, -3
  accent: { type: String, default: 'info' }, // info | success | warning | danger | neutral
  icon: { type: Object, default: null },
})

const displayed = ref(0)
const target = ref(0)

function countUp(to) {
  const start = displayed.value
  const duration = 700
  const t0 = performance.now()
  function step(t) {
    const p = Math.min(1, (t - t0) / duration)
    const eased = 1 - Math.pow(1 - p, 3)
    displayed.value = start + (to - start) * eased
    if (p < 1) requestAnimationFrame(step)
    else displayed.value = to
  }
  requestAnimationFrame(step)
}

onMounted(() => {
  const v = Number(props.value) || 0
  target.value = v
  countUp(v)
})
watch(() => props.value, (n) => {
  const v = Number(n) || 0
  target.value = v
  countUp(v)
})

const accentMap = {
  info: { bg: 'bg-brand-light', text: 'text-brand' },
  success: { bg: 'bg-green-50', text: 'text-green-600' },
  warning: { bg: 'bg-amber-50', text: 'text-amber-600' },
  danger: { bg: 'bg-red-50', text: 'text-red-600' },
  neutral: { bg: 'bg-ink-100', text: 'text-ink-600' },
}
</script>

<template>
  <div class="bg-white rounded-lg shadow-md-soft p-6 lift">
    <div class="flex items-start justify-between mb-4">
      <div :class="['w-10 h-10 rounded-full flex items-center justify-center', accentMap[accent].bg]">
        <component v-if="icon" :is="icon" :class="['w-5 h-5', accentMap[accent].text]" />
      </div>
      <span v-if="trend !== null"
        :class="['text-[12px] font-medium px-2 py-0.5 rounded-full',
          trend >= 0 ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700']">
        {{ trend >= 0 ? '▲' : '▼' }} {{ Math.abs(trend) }}%
      </span>
    </div>
    <p class="t-caption mb-1">{{ label }}</p>
    <p class="text-[28px] font-semibold text-ink-900 tabular-nums leading-none">
      {{ prefix }}{{ Math.round(displayed).toLocaleString('th-TH') }}
    </p>
  </div>
</template>
