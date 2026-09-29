import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: 'Masuk', public: true },
  },
  {
    path: '/tentang',
    name: 'About',
    component: () => import('@/views/Information.vue'),
    meta: { title: 'Tentang', public: true, infoPage: 'about' },
  },
  {
    path: '/privasi-cookies',
    name: 'Privacy',
    component: () => import('@/views/Information.vue'),
    meta: { title: 'Privasi & Cookies', public: true, infoPage: 'privacy' },
  },
  {
    path: '/bantuan',
    name: 'Help',
    component: () => import('@/views/Information.vue'),
    meta: { title: 'Bantuan', public: true, infoPage: 'help' },
  },
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: 'Dashboard', icon: 'Monitor' },
  },
  {
    path: '/conflict-checker',
    name: 'ConflictChecker',
    component: () => import('@/views/ConflictChecker.vue'),
    meta: { title: 'Conflict Checker', icon: 'Warning' },
  },
  {
    path: '/dss-panel',
    name: 'DSSPanel',
    component: () => import('@/views/DSSPanel.vue'),
    meta: { title: 'DSS Panel', icon: 'DataAnalysis' },
  },
  {
    path: '/legal-library',
    name: 'LegalLibrary',
    component: () => import('@/views/LegalLibrary.vue'),
    meta: { title: 'Legal Library', icon: 'Collection' },
  },
  {
    path: '/case-law',
    name: 'CaseLaw',
    component: () => import('@/views/CaseLaw.vue'),
    meta: { title: 'Case Law Search', icon: 'Collection' },
  },
  {
    path: '/contract-analyzer',
    name: 'ContractAnalyzer',
    component: () => import('@/views/ContractAnalyzer.vue'),
    meta: { title: 'Contract Analyzer', icon: 'Document' },
  },
  {
    path: '/deviation-analysis',
    name: 'DeviationAnalysis',
    component: () => import('@/views/DeviationAnalysis.vue'),
    meta: { title: 'Deviation Analysis', icon: 'TrendCharts' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: 'Pengaturan', icon: 'Setting' },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { title: 'Profil & Akun', icon: 'User' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || 'Dashboard'} | Lex-DSS`
  const hasToken = Boolean(localStorage.getItem('access_token'))
  if (!to.meta.public && !hasToken) return { name: 'Login' }
  if (to.name === 'Login' && hasToken) return { name: 'Dashboard' }
  return true
})

export default router
