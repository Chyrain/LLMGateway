import axios from 'axios';
import { message } from 'antd';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const msg = error.response?.data?.msg || error.response?.data?.detail || '请求失败';
    message.error(msg);
    return Promise.reject(error);
  }
);

// 认证相关
export const authApi = {
  login: (username, password) => api.post('/auth/login', null, {
    headers: { username, password }
  }),
  logout: () => api.post('/auth/logout'),
  profile: () => api.get('/auth/profile'),
  changePassword: (oldPassword, newPassword) => api.post('/auth/change-password', null, {
    headers: { old_password: oldPassword, new_password: newPassword }
  })
};

// 消息通知相关
export const notificationApi = {
  list: (params) => api.get('/notifications', { params }),
  create: (data) => api.post('/notifications', data),
  markRead: (id) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put('/notifications/read-all'),
  delete: (id) => api.delete(`/notifications/${id}`),
  clearRead: () => api.delete('/notifications/clear-read'),
  unreadCount: () => api.get('/notifications/unread-count')
};

// 模型配置相关
export const modelApi = {
  list: () => api.get('/model/list'),
  add: (data) => api.post('/model/add', data),
  update: (id, data) => api.put(`/model/${id}`, data),
  delete: (id) => api.delete(`/model/${id}`),
  test: (id) => api.post(`/model/${id}/test`),
  enable: (id) => api.post(`/model/${id}/enable`),
  disable: (id) => api.post(`/model/${id}/disable`)
};

// 额度统计相关
export const quotaApi = {
  stat: (params) => api.get('/quota/stat', { params }),
  sync: (modelId) => api.post(`/quota/sync/${modelId}`),
  update: (modelId, data) => api.put(`/quota/${modelId}`, data),
  history: (params) => api.get('/quota/history', { params })
};

// 系统配置相关
export const configApi = {
  get: (key) => api.get(`/config/${key}`),
  set: (data) => api.post('/config/set', data),
  list: () => api.get('/config/list'),
  resetEncryptKey: () => api.post('/config/reset-encrypt-key')
};

// 日志相关
export const logApi = {
  list: (params) => api.get('/log/list', { params }),
  export: (params) => api.get('/log/export', { params }),
  clear: (type) => api.post('/log/clear', { type })
};

// 统计相关
export const statsApi = {
  dashboard: () => api.get('/stats/dashboard'),
  trends: (params) => api.get('/stats/usage', { params }),
  models: () => api.get('/stats/models'),
  quota: () => api.get('/stats/quota')
};

export default api;
