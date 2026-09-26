import { createRouter, createWebHistory } from 'vue-router'

const routes = [
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
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: 'Pengaturan', icon: 'Setting' },
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

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'Dashboard'} | Lex-DSS`
  next()
})

export default router
