<script setup>
import { ref } from 'vue'
import { XMarkIcon, ArrowUpTrayIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: { type: Array, default: () => [] }, // File[]
  label: { type: String, default: 'แนบไฟล์' },
  accept: { type: String, default: 'image/jpeg,image/png,image/webp,application/pdf' },
  maxSize: { type: Number, default: 10 * 1024 * 1024 }, // 10MB
  maxCount: { type: Number, default: 5 },
  hint: String,
})
const emit = defineEmits(['update:modelValue', 'error'])

const dragOver = ref(false)
const fileInput = ref(null)

function onDrop(e) {
  e.preventDefault()
  dragOver.value = false
  addFiles(Array.from(e.dataTransfer.files || []))
}
function pick() { fileInput.value?.click() }
function onChange(e) {
  addFiles(Array.from(e.target.files || []))
  e.target.value = ''
}
function addFiles(files) {
  const accepted = props.accept.split(',').map(s => s.trim())
  const next = [...props.modelValue]
  for (const f of files) {
    if (next.length >= props.maxCount) { emit('error', `แนบไฟล์ได้สูงสุด ${props.maxCount} ไฟล์`); break }
    if (!accepted.includes(f.type)) { emit('error', `ไฟล์ ${f.name} ประเภทไม่รองรับ`); continue }
    if (f.size > props.maxSize) { emit('error', `ไฟล์ ${f.name} ใหญ่เกิน ${Math.round(props.maxSize/1024/1024)}MB`); continue }
    next.push(f)
  }
  emit('update:modelValue', next)
}
function remove(i) {
  const next = [...props.modelValue]
  next.splice(i, 1)
  emit('update:modelValue', next)
}
function previewUrl(f) {
  if (f.url) return f.url
  if (f.type?.startsWith('image/')) return URL.createObjectURL(f)
  return null
}
</script>

<template>
  <div>
    <div
      @dragover.prevent="dragOver = true"
      @dragleave.prevent="dragOver = false"
      @drop="onDrop"
      @click="pick"
      :class="['border-2 border-dashed rounded-md p-5 text-center cursor-pointer transition-all duration-220 ease-apple',
        dragOver ? 'border-brand bg-brand-light' : 'border-ink-200 hover:border-ink-400 bg-ink-50/40']">
      <ArrowUpTrayIcon class="w-6 h-6 mx-auto mb-2 text-ink-400" />
      <p class="text-[13px] font-medium text-ink-900">{{ label }}</p>
      <p v-if="hint" class="text-[11px] text-ink-400 mt-1">{{ hint }}</p>
      <input ref="fileInput" type="file" :accept="accept" multiple class="hidden" @change="onChange" />
    </div>
    <div v-if="modelValue.length" class="mt-3 space-y-1.5">
      <div v-for="(f, i) in modelValue" :key="i"
        class="flex items-center gap-2 bg-white rounded-sm border border-ink-100 px-2.5 py-1.5">
        <img v-if="previewUrl(f)" :src="previewUrl(f)" class="w-9 h-9 rounded object-cover" />
        <div v-else class="w-9 h-9 rounded bg-ink-100 flex items-center justify-center text-[10px] text-ink-400">PDF</div>
        <div class="flex-1 min-w-0">
          <p class="text-[12px] truncate text-ink-900">{{ f.name || f.original_name }}</p>
          <p class="text-[10px] text-ink-400">{{ ((f.size || 0)/1024).toFixed(1) }} KB</p>
        </div>
        <button @click.stop="remove(i)" class="p-1 rounded hover:bg-ink-100 text-ink-400 hover:text-danger">
          <XMarkIcon class="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
</template>
