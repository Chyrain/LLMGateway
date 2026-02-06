<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo">🤖</div>
        <h1>灵模网关</h1>
        <p>LLM Free Quota Gateway</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        class="login-form"
        size="large"
      >
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username"
            placeholder="用户名"
            prefix-icon="User"
            clearable
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>默认管理员: admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { authApi } from '@/api'

const router = useRouter()
const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  username: 'admin',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3-20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 4, max: 20, message: '密码长度在 4-20 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      const response = await authApi.login(loginForm.username, loginForm.password)
      
      // 响应格式: { code, msg, data: { access_token, username } }
      if (response.code === 200 && response.data) {
        // 保存 token
        const token = response.data.access_token
        localStorage.setItem('token', token)
        localStorage.setItem('username', response.data.username || loginForm.username)
        
        // 检查是否是首次登录（没有设置过标记）
        if (!localStorage.getItem('llmgateway_visited')) {
          localStorage.setItem('llmgateway_visited', 'true')
          // 首次登录，跳转到欢迎页
          ElMessage.success('登录成功')
          router.push('/welcome')
        } else {
          ElMessage.success('登录成功')
          router.push('/')
        }
      } else {
        ElMessage.error(response.msg || response.detail || '登录失败')
      }
    } catch (error) {
      console.error('登录失败:', error)
      ElMessage.error(error.detail || '登录失败，请检查用户名和密码')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style lang="scss" scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
  
  .logo {
    font-size: 60px;
    margin-bottom: 16px;
  }
  
  h1 {
    font-size: 28px;
    font-weight: 600;
    color: #333;
    margin-bottom: 8px;
  }
  
  p {
    font-size: 14px;
    color: #999;
  }
}

.login-form {
  .login-btn {
    width: 100%;
    height: 44px;
    font-size: 16px;
    letter-spacing: 4px;
  }
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  
  p {
    font-size: 13px;
    color: #999;
  }
}
</style>
