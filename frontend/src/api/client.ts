import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redirect to login on 401
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ─────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; password: string; full_name: string; unit_number?: string }) =>
    api.post('/auth/register', data),
  login: (email: string, password: string) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    return api.post('/auth/login', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  me: () => api.get('/auth/me'),
}

// ── Plugs ──────────────────────────────────────────────
export const plugsApi = {
  list: () => api.get('/plugs/'),
  get: (id: number) => api.get(`/plugs/${id}`),
  create: (data: any) => api.post('/plugs/', data),
  update: (id: number, data: any) => api.patch(`/plugs/${id}`, data),
  delete: (id: number) => api.delete(`/plugs/${id}`),
  test: (id: number) => api.post(`/plugs/${id}/test`),
}

// ── Sessions ───────────────────────────────────────────
export const sessionsApi = {
  start: (plug_id: number) => api.post('/sessions/start', { plug_id }),
  stop: (id: number) => api.post(`/sessions/${id}/stop`),
  active: () => api.get('/sessions/active'),
  history: (limit = 20, offset = 0) => api.get(`/sessions/history?limit=${limit}&offset=${offset}`),
  allAdmin: (limit = 50) => api.get(`/sessions/all?limit=${limit}`),
}

// ── Analytics ──────────────────────────────────────────
export const analyticsApi = {
  mySummary: () => api.get('/analytics/me/summary'),
  myDaily: (days = 30) => api.get(`/analytics/me/daily?days=${days}`),
  adminOverview: () => api.get('/analytics/admin/overview'),
  plugUsage: () => api.get('/analytics/admin/plug-usage'),
}

// ── Coins ───────────────────────────────────────────────
export const coinsApi = {
  balance: () => api.get('/coins/balance'),
  transactions: (limit = 30) => api.get(`/coins/transactions?limit=${limit}`),
  topup: (coins: number) => api.post('/coins/topup', { coins }),
  adminCredit: (user_id: number, coins: number, reason: string) =>
    api.post('/coins/admin/credit', { user_id, coins, reason }),
}

export default api
