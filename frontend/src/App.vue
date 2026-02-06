<template>
  <el-config-provider :locale="locale">
    <div class="app-container">
      <el-container>
        <!-- 侧边栏 -->
        <el-aside :width="isCollapsed ? '64px' : '220px'" class="sidebar">
          <div class="logo">
            <el-icon v-if="isCollapsed"><Monitor /></el-icon>
            <span v-else>🤖 灵模网关</span>
          </div>
          
          <el-menu
            :default-active="activeMenu"
            :collapse="isCollapsed"
            router
            class="sidebar-menu"
          >
            <el-menu-item index="/">
              <el-icon><DataBoard /></el-icon>
              <span>仪表盘</span>
            </el-menu-item>
            
            <el-menu-item index="/models">
              <el-icon><Setting /></el-icon>
              <span>模型配置</span>
            </el-menu-item>
            
            <el-menu-item index="/quota">
              <el-icon><PieChart /></el-icon>
              <span>额度监控</span>
            </el-menu-item>
            
            <el-menu-item index="/config">
              <el-icon><Tools /></el-icon>
              <span>系统配置</span>
            </el-menu-item>
            
            <el-menu-item index="/logs">
              <el-icon><Document /></el-icon>
              <span>日志管理</span>
            </el-menu-item>
            
            <el-menu-item index="/agent">
              <el-icon><Connection /></el-icon>
              <span>Agent适配</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <el-container>
          <!-- 顶部栏 -->
          <el-header class="header">
            <div class="header-left">
              <el-icon class="collapse-btn" @click="isCollapsed = !isCollapsed">
                <Fold v-if="!isCollapsed" />
                <Expand v-else />
              </el-icon>
              <el-breadcrumb separator="/">
                <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
                <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
              </el-breadcrumb>
            </div>
            
            <div class="header-right">
              <el-popover
                placement="bottom-end"
                :width="360"
                trigger="click"
                @show="fetchNotifications"
              >
                <template #reference>
                  <el-badge :value="alertCount" :hidden="alertCount === 0" class="alert-badge">
                    <el-icon><Bell /></el-icon>
                  </el-badge>
                </template>
                <div class="notification-panel">
                  <div class="notification-header">
                    <span>消息通知</span>
                    <el-button text type="primary" size="small" @click="markAllRead" v-if="notifications.length > 0">
                      全部已读
                    </el-button>
                  </div>
                  <el-scrollbar class="notification-list" v-if="notifications.length > 0">
                    <div
                      v-for="notif in notifications"
                      :key="notif.id"
                      class="notification-item"
                      :class="{ unread: !notif.is_read }"
                      @click="handleNotificationClick(notif)"
                    >
                      <div class="notif-icon">
                        <el-icon v-if="notif.type === 'warning'"><Warning /></el-icon>
                        <el-icon v-else-if="notif.type === 'success'"><SuccessFilled /></el-icon>
                        <el-icon v-else-if="notif.type === 'error'"><CircleCloseFilled /></el-icon>
                        <el-icon v-else><InfoFilled /></el-icon>
                      </div>
                      <div class="notif-content">
                        <div class="notif-title">{{ notif.title }}</div>
                        <div class="notif-message">{{ notif.message }}</div>
                        <div class="notif-time">{{ formatTime(notif.create_time) }}</div>
                      </div>
                    </div>
                  </el-scrollbar>
                  <div class="notification-empty" v-else>
                    <el-icon size="48"><Bell /></el-icon>
                    <p>暂无通知</p>
                  </div>
                </div>
              </el-popover>
              <el-dropdown @command="handleCommand" trigger="click">
                <span class="user-info">
                  <el-avatar :size="32" src="https://api.dicebear.com/7.x/avataaars/svg?seed=admin" />
                  <span class="username">{{ username }}</span>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="profile">
                      <el-icon><User /></el-icon>个人中心
                    </el-dropdown-item>
                    <el-dropdown-item command="password">
                      <el-icon><Lock /></el-icon>修改密码
                    </el-dropdown-item>
                    <el-dropdown-item divided command="logout">
                      <el-icon><SwitchButton /></el-icon>退出登录
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </el-header>
          
          <!-- 主内容区 -->
          <el-main class="main-content">
            <router-view />
          </el-main>
        </el-container>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Monitor, DataBoard, Setting, PieChart, Tools, Document, Connection, Bell, Fold, Expand, User, Lock, SwitchButton, Warning, SuccessFilled, CircleCloseFilled, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { authApi, notificationApi } from '@/api'

const locale = zhCn
const route = useRoute()
const router = useRouter()
const isCollapsed = ref(false)
const alertCount = ref(0)
const showNotifications = ref(false)
const username = ref('管理员')
const notifications = ref([])

// 获取未读通知数量
const fetchUnreadCount = async () => {
  try {
    const data = await notificationApi.unreadCount()
    alertCount.value = data?.count || 0
  } catch (error) {
    console.error('获取未读通知数量失败:', error)
  }
}

// 获取通知列表
const fetchNotifications = async () => {
  try {
    const data = await notificationApi.list({ limit: 10 })
    notifications.value = data || []
  } catch (error) {
    console.error('获取通知列表失败:', error)
  }
}

// 标记全部已读
const markAllRead = async () => {
  try {
    await notificationApi.markAllRead()
    notifications.value = notifications.value.map(n => ({ ...n, is_read: true }))
    alertCount.value = 0
    ElMessage.success('已全部标记为已读')
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

// 处理通知点击
const handleNotificationClick = async (notif) => {
  if (!notif.is_read) {
    try {
      await notificationApi.markRead(notif.id)
      notif.is_read = true
      alertCount.value = Math.max(0, alertCount.value - 1)
    } catch (error) {
      console.error('标记已读失败:', error)
    }
  }
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString()
}

// 页面加载时获取通知数量
onMounted(() => {
  const token = localStorage.getItem('token')
  if (token) {
    username.value = localStorage.getItem('username') || '管理员'
    fetchUnreadCount()
  }
})

const activeMenu = computed(() => route.path)
const currentPageTitle = computed(() => {
  const titles = {
    '/': '仪表盘',
    '/models': '模型配置',
    '/quota': '额度监控',
    '/config': '系统配置',
    '/logs': '日志管理',
    '/agent': 'Agent工具适配',
    '/profile': '个人中心',
    '/change-password': '修改密码'
  }
  return titles[route.path] || '仪表盘'
})

// 打开个人中心
const goToProfile = () => {
  router.push('/profile')
}

// 打开修改密码
const goToChangePassword = () => {
  router.push('/change-password')
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // 调用退出登录 API
    try {
      await authApi.logout()
    } catch (error) {
      // API 调用失败也继续清除本地状态
      console.log('退出登录 API 调用失败，继续清除本地状态')
    }
    
    // 清除本地存储
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}

// 处理下拉菜单命令
const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      goToProfile()
      break
    case 'password':
      goToChangePassword()
      break
    case 'logout':
      handleLogout()
      break
  }
}
</script>

<style lang="scss" scoped>
.app-container {
  height: 100vh;
  display: flex;
}

.sidebar {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  transition: width 0.3s;
  overflow: hidden;
  
  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 18px;
    font-weight: bold;
    background: rgba(255, 255, 255, 0.05);
  }
  
  .sidebar-menu {
    border-right: none;
    background: transparent;
    
    :deep(.el-menu-item) {
      color: rgba(255, 255, 255, 0.7);
      
      &:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
      }
      
      &.is-active {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: #fff;
      }
    }
  }
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  padding: 0 20px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .collapse-btn {
      font-size: 20px;
      cursor: pointer;
      padding: 4px;
      border-radius: 4px;
      
      &:hover {
        background: #f5f5f5;
      }
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;
    
    .alert-badge {
      cursor: pointer;
      font-size: 20px;
      padding: 8px;
    }
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      
      .username {
        font-size: 14px;
      }
    }
  }
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.notification-panel {
  .notification-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 12px;
    border-bottom: 1px solid #ebeef5;
    margin-bottom: 12px;
    font-weight: bold;
  }
  
  .notification-list {
    max-height: 320px;
    
    .notification-item {
      display: flex;
      gap: 12px;
      padding: 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: background 0.2s;
      
      &:hover {
        background: #f5f7fa;
      }
      
      &.unread {
        background: #ecf5ff;
        
        &:hover {
          background: #d9ecff;
        }
      }
      
      .notif-icon {
        font-size: 20px;
        color: #909399;
      }
      
      .notif-content {
        flex: 1;
        min-width: 0;
        
        .notif-title {
          font-weight: 500;
          margin-bottom: 4px;
        }
        
        .notif-message {
          font-size: 12px;
          color: #909399;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .notif-time {
          font-size: 12px;
          color: #c0c4cc;
          margin-top: 4px;
        }
      }
    }
  }
  
  .notification-empty {
    text-align: center;
    padding: 40px 0;
    color: #909399;
    
    p {
      margin-top: 12px;
    }
  }
}
</style>
