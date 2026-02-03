import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.msg || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// 统一响应处理
export const handleResponse = (res) => {
  if (res.code === 200) {
    return res.data
  }
  throw new Error(res.msg || '请求失败')
}

// 模型配置相关
export const modelApi = {
  list: () => api.get('/model/list'),
  add: (data) => api.post('/model/add', data),
  update: (id, data) => api.put(`/model/${id}`, data),
  delete: (id) => api.delete(`/model/${id}`),
  test: (id) => api.post(`/model/${id}/test`),
  enable: (id) => api.post(`/model/${id}/enable`),
  disable: (id) => api.post(`/model/${id}/disable`),
  reorder: (data) => api.post('/model/reorder', data)
}

// 额度统计相关
export const quotaApi = {
  stat: (params) => api.get('/quota/stat', { params }),
  sync: (modelId) => api.post(`/quota/sync/${modelId}`),
  update: (modelId, data) => api.put(`/quota/${modelId}`, data),
  history: (params) => api.get('/quota/history', { params })
}

// 系统配置相关
export const configApi = {
  get: (key) => api.get(`/config/${key}`),
  set: (data) => api.post('/config/set', data),
  list: () => api.get('/config/list'),
  resetEncryptKey: () => api.post('/config/reset-encrypt-key')
}

// 日志相关
export const logApi = {
  list: (params) => api.get('/log/list', { params }),
  export: (params) => api.get('/log/export', { params }),
  clear: (type) => api.post('/log/clear', { type })
}

// 统计相关
export const statsApi = {
  dashboard: () => api.get('/stats/dashboard'),
  trends: (params) => api.get('/stats/trends', { params }),
  usage: (params) => api.get('/stats/usage', { params })
}

// 网关健康检查
export const healthApi = {
  check: () => api.get('/health')
}

export default api
