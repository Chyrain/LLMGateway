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
          <el-tag type="primary">管理员</el-tag>
        </el-form-item>
        
        <el-form-item label="邮箱">
          <el-input v-model="userInfo.email" />
        </el-form-item>
        
        <el-form-item label="手机号">
          <el-input v-model="userInfo.phone" />
        </el-form-item>
        
        <el-form-item label="创建时间">
          <el-input v-model="userInfo.createdAt" disabled />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveProfile">保存信息</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const userInfo = ref({
  username: 'admin',
  email: 'admin@example.com',
  phone: '13800138000',
  createdAt: '2024-01-01 00:00:00'
})

const saveProfile = () => {
  ElMessage.success('个人信息保存成功')
}
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
