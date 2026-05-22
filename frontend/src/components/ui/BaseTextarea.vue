<script setup>
import { computed } from 'vue'
const props = defineProps({
  modelValue: { type: String, default: '' },
  label: String,
  placeholder: String,
  error: String,
  maxlength: Number,
  rows: { type: Number, default: 4 },
})
defineEmits(['update:modelValue'])
const id = `t-${Math.random().toString(36).slice(2, 9)}`
const count = computed(() => (props.modelValue || '').length)
</script>

<template>
  <div class="w-full">
    <label v-if="label" :for="id" class="block text-[11px] font-medium uppercase tracking-wide text-ink-400 mb-1.5 ml-1">{{ label }}</label>
    <div class="relative">
      <textarea :id="id" :rows="rows" :value="modelValue" :placeholder="placeholder" :maxlength="maxlength"
        @input="$emit('update:modelValue', $event.target.value)"
        class="w-full rounded-md border bg-white px-4 py-3 text-[15px] outline-none transition-all duration-220 ease-apple resize-y"
        :class="error ? 'border-danger' : 'border-ink-200 hover:border-ink-400 focus:border-brand focus:ring-4 focus:ring-brand/15'"
      ></textarea>
      <span v-if="maxlength" class="absolute bottom-2 right-3 text-[11px] text-ink-400">{{ count }}/{{ maxlength }}</span>
    </div>
    <p v-if="error" role="alert" class="mt-1.5 text-[12px] text-danger">{{ error }}</p>
  </div>
</template>
