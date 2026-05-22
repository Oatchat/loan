<script setup>
import { TransitionRoot, TransitionChild, Dialog, DialogPanel, DialogTitle } from '@headlessui/vue'

defineProps({
  open: Boolean,
  title: String,
  size: { type: String, default: 'md' }, // sm | md | lg
})
defineEmits(['close'])
</script>

<template>
  <TransitionRoot appear :show="open" as="template">
    <Dialog as="div" class="relative z-50" @close="$emit('close')">
      <TransitionChild as="template" enter="duration-200 ease-out" enter-from="opacity-0" enter-to="opacity-100"
        leave="duration-150 ease-in" leave-from="opacity-100" leave-to="opacity-0">
        <div class="fixed inset-0 bg-black/40 backdrop-blur-sm" />
      </TransitionChild>
      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
          <TransitionChild as="template"
            enter="duration-220 ease-apple" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
            leave="duration-150 ease-in" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95">
            <DialogPanel :class="[
              'w-full transform overflow-hidden rounded-xl bg-white shadow-lg-soft transition-all',
              size === 'sm' ? 'max-w-sm' : size === 'lg' ? 'max-w-3xl' : 'max-w-md',
            ]">
              <DialogTitle v-if="title" as="h3" class="t-h2 px-6 pt-6">{{ title }}</DialogTitle>
              <div class="px-6 py-5">
                <slot />
              </div>
              <div v-if="$slots.actions" class="px-6 py-4 bg-ink-50 border-t border-ink-100 flex justify-end gap-2">
                <slot name="actions" />
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
