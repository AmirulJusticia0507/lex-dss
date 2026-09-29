import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const legalApi = {
  analyzeConflict: (data) => api.post('/legal/analyze-conflict', data, { timeout: 180000 }),
  getConflicts: (params) => api.get('/legal/conflicts', { params }),
  getConflictDetail: (id) => api.get(`/legal/conflicts/${id}`),
  getLegalArticles: (params) => api.get('/legal/articles', { params }),
  getArticleDetail: (id) => api.get(`/legal/articles/${id}`),
  searchArticles: (query, filters) => api.post('/legal/articles/search', { query, ...filters }),
  getHierarchy: () => api.get('/legal/hierarchy'),
  getStats: () => api.get('/legal/stats'),
}

export const dssApi = {
  getLegalOpinion: (data) => api.post('/dss/legal-opinion', data),
  getRiskAssessment: (data) => api.post('/dss/risk-assessment', data),
  getRecommendations: (data) => api.post('/dss/recommendations', data),
  getHistory: (params) => api.get('/dss/history', { params }),
}

export const authApi = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (data) => api.post('/auth/register', data),
  logout: () => api.post('/auth/logout'),
  getProfile: () => api.get('/auth/profile'),
  getProfileWithToken: (token) => api.get('/auth/profile', { headers: { Authorization: `Bearer ${token}` } }),
  updateProfile: (data) => api.patch('/auth/profile', data),
  changePassword: (data) => api.put('/auth/password', data),
  getPreferences: () => api.get('/auth/preferences'),
  updatePreferences: (preferences) => api.put('/auth/preferences', { preferences }),
  resetPreferences: () => api.delete('/auth/preferences'),
  deletePreference: (key) => api.delete(`/auth/preferences/${encodeURIComponent(key)}`),
  refreshToken: () => api.post('/auth/refresh'),
  getCaptchaChallenge: () => api.get('/auth/captcha/challenge'),
}

export const usersApi = {
  getRoles: () => api.get('/users/roles'),
  list: () => api.get('/users/'),
  create: (data) => api.post('/users/', data),
  update: (id, data) => api.patch(`/users/${id}`, data),
  deactivate: (id) => api.delete(`/users/${id}`),
  activate: (id) => api.post(`/users/${id}/activate`),
}

export const deviationApi = {
  scoreDeviation: (data) => api.post('/deviation/score', data),
  scoreDocument: (data) => api.post('/deviation/score/document', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  getDocumentJob: (id) => api.get(`/deviation/score/document/${id}`),
  listReports: (params) => api.get('/deviation/reports', { params }),
  getReport: (id) => api.get(`/deviation/reports/${id}`),
  updateKYFlag: (id, data) => api.post(`/deviation/reports/${id}/ky-flag`, data),
  exportReport: (id, format = 'json') => api.get(`/deviation/reports/${id}/export`, { params: { format }, responseType: 'blob' }),
  getStats: (params) => api.get('/deviation/statistics', { params }),
}

export const civicPollApi = {
  queueTranscript: (data) => api.post('/civic-poll/transcripts/queue', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  listQueue: (status = 'PENDING') => api.get('/civic-poll/transcripts/queue', { params: { status } }),
  reviewCandidate: (id, data) => api.post(`/civic-poll/transcripts/queue/${id}/review`, data),
  promoteCandidate: (id, data) => api.post(`/civic-poll/transcripts/queue/${id}/promote`, data, { timeout: 60000 }),
}

export default api
