<template>
  <div class="password-container">
    <el-card class="password-card">
      <template #header>
        <div class="card-header">
          <span>修改密码</span>
        </div>
      </template>
      
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="120px"
        class="password-form"
      >
        <el-form-item label="当前密码">
          <el-input
            v-model="formData.oldPassword"
            type="password"
            placeholder="请输入当前密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="新密码">
          <el-input
            v-model="formData.newPassword"
            type="password"
            placeholder="请输入新密码（至少6位）"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认新密码">
          <el-input
            v-model="formData.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            修改密码
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'

const formRef = ref(null)
const submitting = ref(false)

const formData = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 表单验证规则
const validateConfirmPassword = (rule, value, callback) => {
  if (value !== formData.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  oldPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 提交修改密码
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    await authApi.changePassword(formData.oldPassword, formData.newPassword)
    
    ElMessage.success('密码修改成功')
    handleReset()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('修改密码失败:', error)
      ElMessage.error(error.response?.data?.detail || '密码修改失败')
    }
  } finally {
    submitting.value = false
  }
}

// 重置表单
const handleReset = () => {
  formData.oldPassword = ''
  formData.newPassword = ''
  formData.confirmPassword = ''
  formRef.value?.clearValidate()
}
</script>

<style lang="scss" scoped>
.password-container {
  padding: 20px;
}

.password-card {
  max-width: 500px;
  margin: 0 auto;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}
</style>
