<template>
  <div class="welcome-container">
    <el-card class="welcome-card">
      <div class="welcome-header">
        <h1>🎉 欢迎使用灵模网关</h1>
        <p class="subtitle">让我们快速完成初始配置</p>
      </div>

      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="修改密码" />
        <el-step title="添加模型" />
        <el-step title="完成" />
      </el-steps>

      <div class="step-content">
        <!-- 步骤 1: 修改密码 -->
        <div v-if="currentStep === 0" class="step-form">
          <h2>🔐 修改默认密码</h2>
          <p class="tip">为了账户安全，建议修改默认密码</p>
          
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="120px"
          >
            <el-form-item label="当前密码">
              <el-input v-model="passwordForm.oldPassword" type="password" show-password />
              <div class="field-hint">默认密码: admin123</div>
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤 2: 添加模型 -->
        <div v-if="currentStep === 1" class="step-form">
          <h2>🤖 添加第一个模型</h2>
          <p class="tip">配置您的第一个 LLM 模型</p>

          <el-form :model="modelForm" label-width="100px">
            <el-form-item label="厂商">
              <el-select v-model="modelForm.vendor" placeholder="选择模型厂商" style="width: 100%">
                <el-option label="OpenAI (GPT-4)" value="openai" />
                <el-option label="Claude (Anthropic)" value="claude" />
                <el-option label="通义千问 (Qwen)" value="qwen" />
                <el-option label="智谱清言 (Zhipu)" value="zhipu" />
                <el-option label="文心一言 (Ernie)" value="ernie" />
                <el-option label="讯飞星火 (Spark)" value="spark" />
                <el-option label="Kimi (Moonshot)" value="moonshot" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="模型名称">
              <el-input v-model="modelForm.model_name" placeholder="如: gpt-4o" />
            </el-form-item>
            
            <el-form-item label="API Key">
              <el-input v-model="modelForm.api_key" type="password" show-password placeholder="请输入 API Key" />
              <div class="field-hint">
                <el-link type="primary" @click="openVendorLink">
                  如何获取 API Key？
                </el-link>
              </div>
            </el-form-item>
            
            <el-form-item label="优先级">
              <el-input-number v-model="modelForm.priority" :min="1" :max="999" />
              <span class="hint-text">数字越小优先级越高</span>
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤 3: 完成 -->
        <div v-if="currentStep === 2" class="step-complete">
          <div class="success-icon">✅</div>
          <h2>配置完成！</h2>
          <p>现在可以开始使用灵模网关了</p>
          
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/models')">
              进入模型配置
            </el-button>
            <el-button @click="$router.push('/quota')">
              查看额度监控
            </el-button>
          </div>
        </div>
      </div>

      <div class="step-actions">
        <el-button v-if="currentStep < 2" type="primary" @click="nextStep" :loading="loading">
          {{ currentStep === 0 ? '跳过，稍后修改' : '下一步' }}
        </el-button>
        <el-button v-if="currentStep === 0" @click="skipPassword">
          暂不修改
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { authApi, modelApi } from '@/api'

const router = useRouter()
const currentStep = ref(0)
const loading = ref(false)
const passwordFormRef = ref(null)

// 密码表单
const passwordForm = reactive({
  oldPassword: 'admin123',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 模型表单
const modelForm = reactive({
  vendor: '',
  model_name: '',
  api_key: '',
  priority: 100
})

// 厂商链接
const vendorLinks = {
  openai: 'https://platform.openai.com/api-keys',
  claude: 'https://console.anthropic.com/',
  qwen: 'https://dashscope.console.aliyun.com/',
  zhipu: 'https://open.bigmodel.cn/',
  ernie: 'https://yiyan.baidu.com/',
  spark: 'https://spark-api.xf-yun.com/',
  moonshot: 'https://platform.moonshot.cn/'
}

const openVendorLink = () => {
  if (vendorLinks[modelForm.vendor]) {
    window.open(vendorLinks[modelForm.vendor], '_blank')
  }
}

// 下一步
const nextStep = async () => {
  if (currentStep.value === 0) {
    // 修改密码步骤
    if (passwordForm.newPassword) {
      try {
        await passwordFormRef.value.validate()
        loading.value = true
        await authApi.changePassword(
          passwordForm.oldPassword,
          passwordForm.newPassword
        )
        ElMessage.success('密码修改成功')
      } catch (error) {
        loading.value = false
        return
      }
    }
    currentStep.value = 1
  } else if (currentStep.value === 1) {
    // 添加模型步骤
    if (!modelForm.vendor || !modelForm.model_name || !modelForm.api_key) {
      ElMessage.warning('请填写完整的模型信息')
      return
    }
    
    try {
      loading.value = true
      await modelApi.add(modelForm)
      ElMessage.success('模型添加成功')
      currentStep.value = 2
    } catch (error) {
      console.error('添加模型失败:', error)
      ElMessage.error(error.response?.data?.detail || '添加模型失败')
    } finally {
      loading.value = false
    }
  }
}

// 跳过密码修改
const skipPassword = () => {
  ElMessageBox.confirm(
    '跳过密码修改可能存在安全风险，是否继续？',
    '确认',
    { type: 'warning' }
  ).then(() => {
    currentStep.value = 1
  }).catch(() => {})
}
</script>

<style lang="scss" scoped>
.welcome-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.welcome-card {
  width: 600px;
  max-width: 90%;
  padding: 20px;
}

.welcome-header {
  text-align: center;
  margin-bottom: 30px;
  
  h1 {
    font-size: 28px;
    margin-bottom: 10px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  
  .subtitle {
    color: #909399;
    font-size: 14px;
  }
}

.step-content {
  margin: 40px 0;
  min-height: 300px;
  
  .step-form {
    h2 {
      font-size: 20px;
      margin-bottom: 10px;
    }
    
    .tip {
      color: #909399;
      margin-bottom: 20px;
    }
    
    .field-hint {
      font-size: 12px;
      color: #909399;
      margin-top: 5px;
    }
    
    .hint-text {
      margin-left: 10px;
      font-size: 12px;
      color: #909399;
    }
  }
  
  .step-complete {
    text-align: center;
    padding: 40px 0;
    
    .success-icon {
      font-size: 64px;
      margin-bottom: 20px;
    }
    
    h2 {
      font-size: 24px;
      margin-bottom: 10px;
    }
    
    .quick-actions {
      margin-top: 30px;
      display: flex;
      gap: 20px;
      justify-content: center;
    }
  }
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
}
</style>
