<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <span>个人中心</span>
        </div>
      </template>
      
      <el-form :model="userInfo" label-width="100px" class="profile-form">
        <el-form-item label="用户名">
          <el-input v-model="userInfo.username" disabled />
        </el-form-item>
        
        <el-form-item label="角色">
          <el-tag type="primary">{{ userInfo.role }}</el-tag>
        </el-form-item>
        
        <el-form-item label="邮箱">
          <el-input v-model="userInfo.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item label="手机号">
          <el-input v-model="userInfo.phone" placeholder="请输入手机号" />
        </el-form-item>
        
        <el-form-item label="创建时间">
          <el-input :value="formatTime(userInfo.createdAt)" disabled />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveProfile" :loading="saving">
            保存信息
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'

const userInfo = ref({
  username: 'admin',
  role: '管理员',
  email: '',
  phone: '',
  createdAt: new Date().toISOString()
})

const saving = ref(false)

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const data = await authApi.profile()
    if (data) {
      userInfo.value = {
        username: data.username || 'admin',
        role: data.role || '管理员',
        email: data.email || '',
        phone: data.phone || '',
        createdAt: data.createdAt || new Date().toISOString()
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    // 使用默认信息
    userInfo.value = {
      username: 'admin',
      role: '管理员',
      email: '',
      phone: '',
      createdAt: new Date().toISOString()
    }
  }
}

// 保存个人信息
const saveProfile = async () => {
  saving.value = true
  try {
    // TODO: 调用保存 API
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success('个人信息保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style lang="scss" scoped>
.profile-container {
  padding: 20px;
}

.profile-card {
  max-width: 600px;
  margin: 0 auto;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}
</style>
