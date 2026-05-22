import { defineStore } from 'pinia'
import { api } from '../plugins/axios'

export const useDebtorsStore = defineStore('debtors', {
  state: () => ({
    list: [],
    current: null,
    loading: false,
    query: { q: '', status: 'all', sort: 'recent' },
  }),
  getters: {
    overdueCount: (s) => s.list.filter(d => d.status === 'overdue').length,
    nearDueCount: (s) => s.list.filter(d => d.status === 'near_due').length,
    activeCount: (s) => s.list.filter(d => d.status === 'active').length,
    closedCount: (s) => s.list.filter(d => d.status === 'closed').length,
    totalPrincipal: (s) => s.list.reduce((acc, d) => acc + (d.principal || 0), 0),
    totalBalance: (s) => s.list.reduce((acc, d) => acc + (d.balance || 0), 0),
    totalInterestEarned: (s) => s.list.reduce((acc, d) => acc + Math.max(0, (d.total_paid || 0) - (d.principal || 0)), 0),
  },
  actions: {
    async fetchAll() {
      this.loading = true
      try {
        const params = {
          q: this.query.q || undefined,
          status: this.query.status === 'all' ? undefined : this.query.status,
          sort: this.query.sort,
        }
        const { data } = await api.get('/debtors', { params })
        this.list = data
      } finally {
        this.loading = false
      }
    },
    async fetchOne(id) {
      const { data } = await api.get(`/debtors/${id}`)
      this.current = data
      return data
    },
    async create(payload) {
      const { data } = await api.post('/debtors', payload)
      this.list.unshift(data)
      return data
    },
    async update(id, payload) {
      const { data } = await api.put(`/debtors/${id}`, payload)
      const idx = this.list.findIndex(d => d.id === id)
      if (idx >= 0) this.list[idx] = data
      if (this.current?.id === id) this.current = data
      return data
    },
    async remove(id) {
      await api.delete(`/debtors/${id}`)
      this.list = this.list.filter(d => d.id !== id)
    },
    async addPayment(id, payload) {
      const { data } = await api.post(`/debtors/${id}/payments`, payload)
      // refresh enriched
      await this.fetchOne(id)
      return data
    },
    async rollover(id, payload) {
      const { data } = await api.post(`/debtors/${id}/rollover`, payload)
      return data
    },
    async calcInterest(payload) {
      const { data } = await api.post('/calc/interest', payload)
      return data
    },
    async uploadAttachment(id, category, file) {
      const fd = new FormData()
      fd.append('category', category)
      fd.append('file', file)
      const { data } = await api.post(`/debtors/${id}/attachments`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    async deleteAttachment(debtorId, attachmentId) {
      await api.delete(`/debtors/${debtorId}/attachments/${attachmentId}`)
    },
  },
})
