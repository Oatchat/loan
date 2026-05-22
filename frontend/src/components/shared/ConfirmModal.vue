<script setup>
import BaseModal from '../ui/BaseModal.vue'
import BaseButton from '../ui/BaseButton.vue'

defineProps({
  open: Boolean,
  title: { type: String, default: 'ยืนยันการดำเนินการ' },
  message: String,
  confirmText: { type: String, default: 'ยืนยัน' },
  cancelText: { type: String, default: 'ยกเลิก' },
  variant: { type: String, default: 'primary' }, // primary | danger
  loading: Boolean,
})
defineEmits(['confirm', 'close'])
</script>

<template>
  <BaseModal :open="open" :title="title" size="sm" @close="$emit('close')">
    <p class="text-ink-600 t-body">{{ message }}</p>
    <template #actions>
      <BaseButton variant="ghost" @click="$emit('close')">{{ cancelText }}</BaseButton>
      <BaseButton :variant="variant" :loading="loading" @click="$emit('confirm')">{{ confirmText }}</BaseButton>
    </template>
  </BaseModal>
</template>
