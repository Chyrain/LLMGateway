import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/welcome',
    name: 'Welcome',
    component: () => import('@/views/Welcome.vue'),
    meta: { title: '欢迎使用', requiresAuth: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '仪表盘', requiresAuth: true }
  },
  {
    path: '/models',
    name: 'Models',
    component: () => import('@/views/ModelConfig.vue'),
    meta: { title: '模型配置', requiresAuth: true }
  },
  {
    path: '/quota',
    name: 'Quota',
    component: () => import('@/views/QuotaMonitor.vue'),
    meta: { title: '额度监控', requiresAuth: true }
  },
  {
    path: '/config',
    name: 'Config',
    component: () => import('@/views/SystemConfig.vue'),
    meta: { title: '系统配置', requiresAuth: true }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('@/views/Logs.vue'),
    meta: { title: '日志管理', requiresAuth: true }
  },
  {
    path: '/agent',
    name: 'Agent',
    component: () => import('@/views/AgentGuide.vue'),
    meta: { title: 'Agent工具适配', requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { title: '个人中心', requiresAuth: true }
  },
  {
    path: '/change-password',
    name: 'ChangePassword',
    component: () => import('@/views/ChangePassword.vue'),
    meta: { title: '修改密码', requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 检查是否是首次登录
const isFirstLogin = () => {
  const hasVisited = localStorage.getItem('llmgateway_visited')
  return !hasVisited
}

// 认证守卫
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '首页'} - 灵模网关`
  
  const requiresAuth = to.meta.requiresAuth !== false
  const token = localStorage.getItem('token')
  
  if (requiresAuth && !token) {
    // 需要登录但没有 token，跳转到登录页
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && token) {
    // 已登录访问登录页，跳转到仪表盘
    next({ name: 'Dashboard' })
  } else if (to.name === 'Dashboard' && isFirstLogin()) {
    // 首次登录访问仪表盘，跳转到欢迎页
    next({ name: 'Welcome' })
  } else {
    next()
  }
})

export default router
