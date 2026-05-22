<script setup>
import { computed } from 'vue'
const props = defineProps({
  variant: { type: String, default: 'neutral' }, // success | warning | danger | info | neutral
  pulse: Boolean,
})
const cls = computed(() => {
  const v = {
    success: 'bg-green-50 text-green-700',
    warning: 'bg-amber-50 text-amber-700',
    danger: 'bg-red-50 text-red-700',
    info: 'bg-brand-light text-brand',
    neutral: 'bg-ink-100 text-ink-600',
  }[props.variant]
  return `inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[12px] font-medium ${v} ${props.pulse ? 'animate-pulse-soft' : ''}`
})
</script>

<template>
  <span :class="cls">
    <slot name="icon" />
    <slot />
  </span>
</template>
