<script setup>
import { computed } from 'vue'

const props = defineProps({
  columns: { type: Array, default: () => [] }, // [{key, label, align?}]
  rows: { type: Array, default: () => [] },
  loading: Boolean,
  empty: { type: String, default: 'ไม่มีข้อมูล' },
  selectable: { type: Boolean, default: false },
  selected: { type: Array, default: () => [] },     // v-model:selected — array of row.id
  rowKey: { type: String, default: 'id' },
  rowClickable: { type: Boolean, default: false },
  minWidth: { type: String, default: '720px' },
})
const emit = defineEmits(['update:selected', 'row-click'])

const selectedSet = computed(() => new Set(props.selected))

const selectableIds = computed(() =>
  props.rows.map(r => r[props.rowKey]).filter(v => v != null)
)

const allSelected = computed(() =>
  selectableIds.value.length > 0 && selectableIds.value.every(id => selectedSet.value.has(id))
)
const someSelected = computed(() =>
  !allSelected.value && selectableIds.value.some(id => selectedSet.value.has(id))
)

function toggleRow(id) {
  if (id == null) return
  const next = new Set(selectedSet.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  emit('update:selected', [...next])
}

function toggleAll() {
  if (allSelected.value) {
    emit('update:selected', props.selected.filter(id => !selectableIds.value.includes(id)))
  } else {
    const merged = new Set([...props.selected, ...selectableIds.value])
    emit('update:selected', [...merged])
  }
}
</script>

<template>
  <div class="bg-white rounded-lg shadow-sm-soft border border-ink-100 overflow-x-auto -webkit-overflow-scrolling-touch">
    <table class="w-full text-[14px]" :style="{ minWidth }">
      <thead class="bg-ink-50 border-b border-ink-100">
        <tr>
          <th v-if="selectable" class="px-5 py-3 w-[42px]">
            <input
              type="checkbox"
              :checked="allSelected"
              :indeterminate.prop="someSelected"
              :disabled="!selectableIds.length"
              @change="toggleAll"
              class="w-[16px] h-[16px] rounded border-ink-300 text-brand focus:ring-brand/40 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="เลือกทั้งหมด"
            />
          </th>
          <th v-for="c in columns" :key="c.key"
            :class="['t-caption text-ink-400 px-5 py-3 font-medium',
              c.align === 'right' ? 'text-right' : c.align === 'center' ? 'text-center' : 'text-left']">
            {{ c.label }}
          </th>
          <th v-if="$slots.actions" class="t-caption text-ink-400 px-5 py-3 text-right">การจัดการ</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading" v-for="i in 4" :key="`sk-${i}`" class="border-b border-ink-100">
          <td v-if="selectable" class="px-5 py-4"><div class="h-3 w-[16px] bg-ink-100 rounded animate-pulse-soft" /></td>
          <td v-for="c in columns" :key="c.key" class="px-5 py-4">
            <div class="h-3 bg-ink-100 rounded animate-pulse-soft" />
          </td>
          <td v-if="$slots.actions" class="px-5 py-4"><div class="h-3 bg-ink-100 rounded animate-pulse-soft w-24 ml-auto" /></td>
        </tr>
        <tr v-else-if="!rows.length">
          <td :colspan="columns.length + (selectable ? 1 : 0) + ($slots.actions ? 1 : 0)" class="px-5 py-14 text-center text-ink-400">
            <slot name="empty">{{ empty }}</slot>
          </td>
        </tr>
        <tr v-else v-for="(row, idx) in rows" :key="row[rowKey] ?? idx"
          class="border-b border-ink-100 last:border-0 group transition-colors duration-220"
          :style="{ animation: `fade-up 320ms cubic-bezier(.16,1,.3,1) ${idx * 30}ms both` }"
          :class="[
            row._highlight === 'overdue' ? 'border-l-[3px] border-l-danger bg-red-50/30' : 'hover:bg-brand-light/40',
            selectable && selectedSet.has(row[rowKey]) ? 'bg-brand-light/40' : '',
            rowClickable ? 'cursor-pointer' : '',
          ]"
          @click="rowClickable && emit('row-click', row)">
          <td v-if="selectable" class="px-5 py-3.5 align-middle">
            <input
              type="checkbox"
              :checked="selectedSet.has(row[rowKey])"
              @change="toggleRow(row[rowKey])"
              @click.stop
              class="w-[16px] h-[16px] rounded border-ink-300 text-brand focus:ring-brand/40 cursor-pointer"
              :aria-label="`เลือกแถว ${row.name || idx + 1}`"
            />
          </td>
          <td v-for="c in columns" :key="c.key"
            :class="['px-5 py-3.5 align-middle',
              c.align === 'right' ? 'text-right' : c.align === 'center' ? 'text-center' : '']">
            <slot :name="`cell-${c.key}`" :row="row" :value="row[c.key]">{{ row[c.key] }}</slot>
          </td>
          <td v-if="$slots.actions" class="px-5 py-3.5 text-right">
            <slot name="actions" :row="row" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
