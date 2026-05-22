<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: { type: String, default: 'primary' }, // primary | ghost | danger | secondary
  size: { type: String, default: 'md' },         // sm | md | lg
  loading: Boolean,
  disabled: Boolean,
  block: Boolean,
  type: { type: String, default: 'button' },
})

const cls = computed(() => {
  const base = 'inline-flex items-center justify-center gap-2 font-medium rounded-md transition-all duration-220 ease-apple active:scale-[0.97] focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-brand/50 select-none'
  const sizes = {
    sm: 'h-9 px-3 text-[13px]',
    md: 'h-[42px] px-5 text-[15px]',
    lg: 'h-[48px] px-6 text-[16px]',
  }[props.size]
  const variants = {
    primary: 'bg-brand text-white hover:bg-brand-hover shadow-sm-soft',
    ghost: 'bg-transparent text-ink-900 hover:bg-ink-100',
    secondary: 'bg-ink-100 text-ink-900 hover:bg-ink-200',
    danger: 'bg-danger text-white hover:opacity-90 shadow-sm-soft',
  }[props.variant]
  return [base, sizes, variants, props.block ? 'w-full' : '', (props.disabled || props.loading) ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''].join(' ')
})
</script>

<template>
  <button :type="type" :class="cls" :disabled="disabled || loading">
    <svg v-if="loading" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" opacity=".25" />
      <path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="3" stroke-linecap="round" />
    </svg>
    <slot v-else name="icon-left" />
    <slot />
    <slot name="icon-right" />
  </button>
</template>
