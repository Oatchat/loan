<script setup>
defineProps({
  title: String,
  message: String,
})
</script>

<template>
  <div class="text-center py-16 px-6">
    <div class="w-24 h-24 rounded-full bg-brand-light mx-auto mb-5 flex items-center justify-center">
      <svg width="44" height="44" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="8" r="3.5" stroke="#0071E3" stroke-width="1.6"/>
        <path d="M4 20c0-3.5 3.5-6 8-6s8 2.5 8 6" stroke="#0071E3" stroke-width="1.6" stroke-linecap="round"/>
        <circle cx="18.5" cy="17" r="3.2" fill="#0071E3"/>
        <text x="18.5" y="18.6" text-anchor="middle" font-size="4.4" font-weight="700" fill="white" font-family="-apple-system">฿</text>
      </svg>
    </div>
    <h3 class="t-h3 text-ink-900 mb-1">{{ title }}</h3>
    <p class="t-small text-ink-400 mb-5">{{ message }}</p>
    <slot />
  </div>
</template>
