import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '仪表盘' }
  },
  {
    path: '/models',
    name: 'Models',
    component: () => import('@/views/ModelConfig.vue'),
    meta: { title: '模型配置' }
  },
  {
    path: '/quota',
    name: 'Quota',
    component: () => import('@/views/QuotaMonitor.vue'),
    meta: { title: '额度监控' }
  },
  {
    path: '/config',
    name: 'Config',
    component: () => import('@/views/SystemConfig.vue'),
    meta: { title: '系统配置' }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('@/views/Logs.vue'),
    meta: { title: '日志管理' }
  },
  {
    path: '/agent',
    name: 'Agent',
    component: () => import('@/views/AgentGuide.vue'),
    meta: { title: 'Agent工具适配' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { title: '个人中心' }
  },
  {
    path: '/change-password',
    name: 'ChangePassword',
    component: () => import('@/views/ChangePassword.vue'),
    meta: { title: '修改密码' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '首页'} - 灵模网关`
  next()
})

export default router
