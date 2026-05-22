import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { title: 'เข้าสู่ระบบ', public: true },
  },
  {
    path: '/',
    component: () => import('../layouts/AppLayout.vue'),
    children: [
      { path: '', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { title: 'แดชบอร์ด' } },
      { path: 'debtors', name: 'debtors', component: () => import('../views/DebtorListView.vue'), meta: { title: 'ลูกหนี้' } },
      { path: 'debtors/new', name: 'debtor-new', component: () => import('../views/AddDebtorView.vue'), meta: { title: 'เพิ่มลูกหนี้' } },
      { path: 'debtors/:id', name: 'debtor-detail', component: () => import('../views/DebtorDetailView.vue'), meta: { title: 'รายละเอียดลูกหนี้' } },
      { path: 'debtors/:id/edit', name: 'debtor-edit', component: () => import('../views/EditDebtorView.vue'), meta: { title: 'แก้ไขลูกหนี้' } },
      { path: 'reports', name: 'reports', component: () => import('../views/ReportView.vue'), meta: { title: 'รายงาน' } },
      { path: 'settings', name: 'settings', component: () => import('../views/SettingsView.vue'), meta: { title: 'ตั้งค่า' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (to.meta?.title) document.title = `${to.meta.title} • DebtTrack`
  if (!to.meta?.public && !auth.isAuthenticated) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return next({ name: 'dashboard' })
  }
  next()
})
