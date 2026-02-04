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
              <el-badge :value="alertCount" :hidden="alertCount === 0" class="alert-badge">
                <el-icon @click="toggleNotifications"><Bell /></el-icon>
              </el-badge>
              <el-dropdown @command="handleCommand">
                <span class="user-info">
                  <el-avatar :size="32" src="https://api.dicebear.com/7.x/avataaars/svg?seed=admin" />
                  <span class="username">管理员</span>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="profile" icon="User">个人中心</el-dropdown-item>
                    <el-dropdown-item command="password" icon="Lock">修改密码</el-dropdown-item>
                    <el-dropdown-item divided command="logout" icon="SwitchButton">退出登录</el-dropdown-item>
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
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Monitor, DataBoard, Setting, PieChart, Tools, Document, Connection, Bell, Fold, Expand, User, Lock, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const locale = zhCn
const route = useRoute()
const router = useRouter()
const isCollapsed = ref(false)
const alertCount = ref(2)
const showNotifications = ref(false)

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

// 打开通知面板
const toggleNotifications = () => {
  showNotifications.value = !showNotifications.value
}

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
    ElMessage.success('已退出登录')
    router.push('/')
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
</style>
