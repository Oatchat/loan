<script setup>
const props = defineProps({
  variant: { type: String, default: 'solid' }, // solid | glass
  hover: Boolean,
  padding: { type: String, default: 'md' }, // sm | md | lg
})
</script>

<template>
  <div :class="[
    'rounded-lg border border-ink-100 transition-all',
    variant === 'glass' ? 'glass' : 'bg-white shadow-sm-soft',
    hover ? 'lift cursor-pointer' : '',
    padding === 'sm' ? 'p-4' : padding === 'lg' ? 'p-8' : 'px-7 py-6',
  ]">
    <slot />
  </div>
</template>
