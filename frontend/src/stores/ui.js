import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', {
  state: () => ({
    loading: false,
    sidebarOpen: false,
  }),
  actions: {
    setLoading(v) { this.loading = v },
    toggleSidebar() { this.sidebarOpen = !this.sidebarOpen },
  },
})
