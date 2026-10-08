import axios from 'axios'

// Vite dev server proxies /api -> http://localhost:8000 (see vite.config.js).
const baseURL = import.meta.env.VITE_API_BASE || '/api'

export const api = axios.create({ baseURL })

export const analyzePrompt = (prompt, userId, department, provider) =>
  api.post('/analyze', { prompt, user_id: userId, department, provider }).then(r => r.data)

export const analyzeFile = (file, userId, department, provider) => {
  const form = new FormData()
  form.append('file', file)
  form.append('user_id', userId)
  form.append('department', department)
  if (provider) form.append('provider', provider)
  return api.post('/analyze-file', form).then(r => r.data)
}

export const getProviders = () => api.get('/providers').then(r => r.data)

export const getAuditLogs = (limit = 50) =>
  api.get('/audit-logs', { params: { limit } }).then(r => r.data)

export const getStats = () => api.get('/stats').then(r => r.data)

export const getTimeseries = (hours = 24) =>
  api.get('/analytics/timeseries', { params: { hours } }).then(r => r.data)

export const getDepartments = () =>
  api.get('/analytics/departments').then(r => r.data)

export const getRules = () => api.get('/rules').then(r => r.data)

export const createRule = (name, pattern, severity) =>
  api.post('/rules', { name, pattern, severity }).then(r => r.data)

export const deleteRule = (id) => api.delete(`/rules/${id}`).then(r => r.data)

export const toggleRule = (id, active) =>
  api.patch(`/rules/${id}/toggle`, null, { params: { active } }).then(r => r.data)

export const exportCsvUrl = () => `${baseURL}/export/csv`

export const runAgent = (name) => api.post(`/agents/${name}`).then(r => r.data)

export const getApprovals = (status = 'pending') =>
  api.get('/approvals', { params: { status } }).then(r => r.data)

export const approveRequest = (id, decidedBy, provider) =>
  api.post(`/approvals/${id}/approve`, { decided_by: decidedBy, provider }).then(r => r.data)

export const rejectRequest = (id, decidedBy) =>
  api.post(`/approvals/${id}/reject`, { decided_by: decidedBy }).then(r => r.data)
