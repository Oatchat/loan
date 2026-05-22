<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { default: '' },
  label: String,
  options: { type: Array, default: () => [] }, // [{value,label}]
  error: String,
  required: Boolean,
  disabled: Boolean,
})
defineEmits(['update:modelValue'])

const id = `s-${Math.random().toString(36).slice(2, 9)}`
const wrapCls = computed(() => [
  'relative w-full rounded-md bg-white border transition-all duration-220 ease-apple',
  props.error ? 'border-danger' : 'border-ink-200 hover:border-ink-400 focus-within:border-brand focus-within:ring-4 focus-within:ring-brand/15',
].join(' '))
</script>

<template>
  <div class="w-full">
    <label v-if="label" :for="id" class="block text-[11px] font-medium uppercase tracking-wide text-ink-400 mb-1.5 ml-1">
      {{ label }}<span v-if="required" class="text-danger ml-0.5">*</span>
    </label>
    <div :class="wrapCls">
      <select :id="id" :value="modelValue" :disabled="disabled"
        @change="$emit('update:modelValue', $event.target.value)"
        class="w-full appearance-none bg-transparent outline-none px-4 py-2.5 pr-10 text-[15px] text-ink-900 cursor-pointer">
        <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <svg class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-ink-400" width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <p v-if="error" role="alert" class="mt-1.5 text-[12px] text-danger">{{ error }}</p>
  </div>
</template>
