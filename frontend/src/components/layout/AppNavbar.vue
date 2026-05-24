<script setup>
import { useRouter, useRoute, RouterLink } from 'vue-router'
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue'
import { BellIcon, ArrowRightOnRectangleIcon, Cog6ToothIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '../../stores/auth'
import { initials, avatarColor } from '../../utils/formatters'
import { computed } from 'vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const links = [
  { to: '/', label: 'แดชบอร์ด', match: ['dashboard'] },
  { to: '/debtors', label: 'ลูกหนี้', match: ['debtors', 'debtor-detail', 'debtor-edit', 'debtor-new'] },
  { to: '/reports', label: 'รายงาน', match: ['reports'] },
  { to: '/settings', label: 'ตั้งค่า', match: ['settings'] },
]

const isActive = (l) => l.match.includes(route.name)

const userInitials = computed(() => initials(auth.user?.name))
const userColor = computed(() => avatarColor(auth.user?.name))

function doLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="sticky top-0 z-40 h-[52px] border-b border-black/[0.06]"
    style="background: rgba(255,255,255,0.85); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);">
    <div class="h-full max-w-[1400px] mx-auto px-6 lg:px-12 flex items-center justify-between gap-6">
      <RouterLink to="/" class="flex items-center gap-2 group">
        <div class="w-7 h-7 rounded-md bg-brand grid place-items-center text-white font-bold text-[14px]">฿</div>
        <span class="font-semibold text-[16px] tracking-tight text-ink-900">DebtTrack</span>
      </RouterLink>

      <nav class="hidden md:flex items-center gap-1">
        <RouterLink v-for="l in links" :key="l.to" :to="l.to"
          class="relative px-3 py-1.5 text-[14px] font-medium transition-colors duration-200"
          :class="isActive(l) ? 'text-brand' : 'text-ink-600 hover:text-ink-900'">
          {{ l.label }}
          <span v-if="isActive(l)"
            class="absolute left-3 right-3 -bottom-[15px] h-[2px] bg-brand rounded-full"
            style="transition: all 220ms cubic-bezier(.16,1,.3,1);" />
        </RouterLink>
      </nav>

      <div class="flex items-center gap-3">
        <button class="relative p-2 rounded-full hover:bg-ink-100 transition-colors" aria-label="การแจ้งเตือน">
          <BellIcon class="w-5 h-5 text-ink-600" />
        </button>

        <Menu as="div" class="relative">
          <MenuButton class="flex items-center gap-2 p-1 pr-2 rounded-full hover:bg-ink-100 transition-colors">
            <span class="w-8 h-8 rounded-full text-white font-semibold text-[13px] grid place-items-center"
              :style="{ background: userColor }">{{ userInitials }}</span>
            <span class="hidden sm:inline text-[13px] text-ink-900 font-medium">{{ auth.user?.name }}</span>
          </MenuButton>
          <transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 scale-95"
            enter-to-class="opacity-100 scale-100" leave-active-class="transition duration-150 ease-in"
            leave-from-class="opacity-100" leave-to-class="opacity-0">
            <MenuItems class="absolute right-0 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg-soft border border-ink-100 focus:outline-none overflow-hidden">
              <div class="px-4 py-3 border-b border-ink-100">
                <p class="text-[13px] font-medium text-ink-900 truncate">{{ auth.user?.name }}</p>
                <p class="text-[11px] text-ink-400 truncate">@{{ auth.user?.username }}</p>
              </div>
              <MenuItem v-slot="{ active }">
                <RouterLink to="/settings"
                  :class="['flex items-center gap-2 px-4 py-2.5 text-[13px]', active ? 'bg-ink-50 text-ink-900' : 'text-ink-600']">
                  <Cog6ToothIcon class="w-4 h-4" /> ตั้งค่า
                </RouterLink>
              </MenuItem>
              <MenuItem v-slot="{ active }">
                <button @click="doLogout"
                  :class="['w-full flex items-center gap-2 px-4 py-2.5 text-[13px]', active ? 'bg-red-50 text-danger' : 'text-ink-600']">
                  <ArrowRightOnRectangleIcon class="w-4 h-4" /> ออกจากระบบ
                </button>
              </MenuItem>
            </MenuItems>
          </transition>
        </Menu>
      </div>
    </div>
  </header>
</template>
