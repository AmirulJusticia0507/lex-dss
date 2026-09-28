import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { legalApi, dssApi } from '@/api'

function extractArticleList(payload) {
  let current = payload

  // Support both the API's `{ data: [...] }` response and common nested
  // envelopes such as `{ data: { items: [...] } }`.
  for (let depth = 0; depth < 4 && current; depth += 1) {
    if (Array.isArray(current)) {
      return current.map((article) => ({
        ...article,
        hierarchy_rank: article.hierarchy_rank ?? article.hierarchy?.rank ?? null,
      }))
    }

    const list = current.items ?? current.results ?? current.articles
    if (Array.isArray(list)) {
      return list.map((article) => ({
        ...article,
        hierarchy_rank: article.hierarchy_rank ?? article.hierarchy?.rank ?? null,
      }))
    }

    current = current.data
  }

  return []
}

export const useLegalStore = defineStore('legal', () => {
  const conflicts = ref([])
  const articles = ref([])
  const hierarchy = ref([])
  const stats = ref(null)
  const currentConflict = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const conflictCount = computed(() => conflicts.value.length)
  const highSeverityConflicts = computed(() =>
    conflicts.value.filter((c) => c.severity === 'HIGH').length
  )
  const mediumSeverityConflicts = computed(() =>
    conflicts.value.filter((c) => c.severity === 'MEDIUM').length
  )
  const lowSeverityConflicts = computed(() =>
    conflicts.value.filter((c) => c.severity === 'LOW').length
  )

  async function fetchConflicts(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await legalApi.getConflicts(params)
      conflicts.value = response.data.data || response.data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchConflictDetail(id) {
    loading.value = true
    error.value = null
    try {
      const response = await legalApi.getConflictDetail(id)
      currentConflict.value = response.data.data || response.data
      return currentConflict.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function analyzeConflict(data) {
    loading.value = true
    error.value = null
    try {
      const response = await legalApi.analyzeConflict(data)
      return response.data.data || response.data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchArticles(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await legalApi.getLegalArticles(params)
      articles.value = extractArticleList(response.data)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchHierarchy() {
    try {
      const response = await legalApi.getHierarchy()
      hierarchy.value = response.data.data || response.data
    } catch (err) {
      error.value = err.message
    }
  }

  async function fetchStats() {
    try {
      const response = await legalApi.getStats()
      stats.value = response.data.data || response.data
    } catch (err) {
      error.value = err.message
    }
  }

  function clearCurrentConflict() {
    currentConflict.value = null
  }

  function clearError() {
    error.value = null
  }

  return {
    conflicts,
    articles,
    hierarchy,
    stats,
    currentConflict,
    loading,
    error,
    conflictCount,
    highSeverityConflicts,
    mediumSeverityConflicts,
    lowSeverityConflicts,
    fetchConflicts,
    fetchConflictDetail,
    analyzeConflict,
    fetchArticles,
    fetchHierarchy,
    fetchStats,
    clearCurrentConflict,
    clearError,
  }
})

export const useDSSStore = defineStore('dss', () => {
  const legalOpinion = ref(null)
  const riskAssessment = ref(null)
  const recommendations = ref([])
  const history = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function getLegalOpinion(data) {
    loading.value = true
    error.value = null
    try {
      const response = await dssApi.getLegalOpinion(data)
      legalOpinion.value = response.data.data || response.data
      return legalOpinion.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getRiskAssessment(data) {
    loading.value = true
    error.value = null
    try {
      const response = await dssApi.getRiskAssessment(data)
      riskAssessment.value = response.data.data || response.data
      return riskAssessment.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getRecommendations(data) {
    loading.value = true
    error.value = null
    try {
      const response = await dssApi.getRecommendations(data)
      recommendations.value = response.data.data || response.data
      return recommendations.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchHistory(params = {}) {
    try {
      const response = await dssApi.getHistory(params)
      history.value = response.data.data || response.data
    } catch (err) {
      error.value = err.message
    }
  }

  function clearResults() {
    legalOpinion.value = null
    riskAssessment.value = null
    recommendations.value = []
  }

  return {
    legalOpinion,
    riskAssessment,
    recommendations,
    history,
    loading,
    error,
    getLegalOpinion,
    getRiskAssessment,
    getRecommendations,
    fetchHistory,
    clearResults,
  }
})

export const useUIStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(false)
  const theme = ref('light')
  const notifications = ref([])
  const activeTab = ref('dark')

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setSidebarCollapsed(collapsed) {
    sidebarCollapsed.value = collapsed
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    applyTheme(theme.value)
  }

  function setTheme(newTheme) {
    theme.value = newTheme
    applyTheme(newTheme)
  }

  function applyTheme(newTheme) {
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('lex-dss-theme', newTheme)
  }

  function initTheme() {
    const saved = localStorage.getItem('lex-dss-theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const initialTheme = saved || (prefersDark ? 'dark' : 'light')
    theme.value = initialTheme
    applyTheme(initialTheme)

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('lex-dss-theme')) {
        const newTheme = e.matches ? 'dark' : 'light'
        theme.value = newTheme
        applyTheme(newTheme)
      }
    })
  }

  function addNotification(notification) {
    notifications.value.unshift({
      id: Date.now(),
      ...notification,
      read: false,
    })
  }

  function markAsRead(id) {
    const notif = notifications.value.find((n) => n.id === id)
    if (notif) notif.read = true
  }

  function removeNotification(id) {
    notifications.value = notifications.value.filter((n) => n.id !== id)
  }

  function setActiveTab(tab) {
    activeTab.value = tab
  }

  return {
    sidebarCollapsed,
    theme,
    notifications,
    activeTab,
    toggleSidebar,
    setSidebarCollapsed,
    toggleTheme,
    setTheme,
    initTheme,
    addNotification,
    markAsRead,
    removeNotification,
    setActiveTab,
  }
})

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token') || null)
  const isAuthenticated = computed(() => !!token.value)

  function setAuth(authData) {
    user.value = authData.user
    token.value = authData.token
    localStorage.setItem('access_token', authData.token)
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('access_token')
  }

  return {
    user,
    token,
    isAuthenticated,
    setAuth,
    logout,
  }
})
