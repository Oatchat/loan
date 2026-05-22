<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: String,
  type: { type: String, default: 'text' },
  placeholder: String,
  error: String,
  hint: String,
  disabled: Boolean,
  required: Boolean,
  prefix: String,
  suffix: String,
})
defineEmits(['update:modelValue', 'blur', 'focus'])

const id = `i-${Math.random().toString(36).slice(2, 9)}`
const focused = ref(false)
const hasValue = computed(() => props.modelValue !== '' && props.modelValue !== null && props.modelValue !== undefined)
const floating = computed(() => focused.value || hasValue.value)

const wrapCls = computed(() => [
  'relative w-full rounded-md bg-white transition-all duration-220 ease-apple',
  'border',
  props.error
    ? 'border-danger animate-shake'
    : focused.value
      ? 'border-brand ring-4 ring-brand/15'
      : 'border-ink-200 hover:border-ink-400',
  props.disabled ? 'opacity-60 pointer-events-none' : '',
].join(' '))
</script>

<template>
  <div class="w-full">
    <div :class="wrapCls">
      <label v-if="label" :for="id"
        class="absolute pointer-events-none transition-all duration-220 ease-apple"
        :class="floating
          ? 'top-1.5 left-3 text-[11px] font-medium tracking-wide uppercase text-ink-400'
          : 'top-1/2 -translate-y-1/2 left-4 text-[15px] text-ink-400'">
        {{ label }}<span v-if="required" class="text-danger ml-0.5">*</span>
      </label>
      <div class="flex items-center">
        <span v-if="prefix" class="pl-4 text-ink-400">{{ prefix }}</span>
        <input
          :id="id"
          :type="type"
          :value="modelValue"
          :placeholder="floating ? placeholder : ''"
          :disabled="disabled"
          @input="$emit('update:modelValue', $event.target.value)"
          @focus="focused = true; $emit('focus', $event)"
          @blur="focused = false; $emit('blur', $event)"
          class="w-full bg-transparent outline-none px-4 text-[15px] text-ink-900 placeholder-ink-200"
          :class="label ? 'pt-5 pb-1.5' : 'py-2.5'"
        />
        <span v-if="suffix" class="pr-4 text-ink-400">{{ suffix }}</span>
        <slot name="icon-right" />
      </div>
    </div>
    <p v-if="error" role="alert" class="mt-1.5 text-[12px] text-danger flex items-center gap-1.5 animate-fade-up">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 110 20 10 10 0 010-20zm0 6v6m0 2v2" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" fill="none"/></svg>
      {{ error }}
    </p>
    <p v-else-if="hint" class="mt-1.5 text-[12px] text-ink-400">{{ hint }}</p>
  </div>
</template>
