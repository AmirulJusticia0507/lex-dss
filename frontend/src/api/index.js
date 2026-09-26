import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
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
  analyzeConflict: (data) => api.post('/legal/analyze-conflict', data),
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
  refreshToken: () => api.post('/auth/refresh'),
}

export default api