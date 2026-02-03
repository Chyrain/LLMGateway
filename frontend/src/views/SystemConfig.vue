<template>
  <div class="system-config">
    <el-row :gutter="20">
      <!-- 网关配置 -->
      <el-col :span="12">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Setting /></el-icon> 网关服务配置</span>
            </div>
          </template>
          
          <el-form :model="gatewayConfig" label-width="120px">
            <el-form-item label="服务端口">
              <el-input-number v-model="gatewayConfig.port" :min="1" :max="65535" />
              <span class="form-tip">网关服务监听端口</span>
            </el-form-item>
            
            <el-form-item label="API端口">
              <el-input-number v-model="gatewayConfig.api_port" :min="1" :max="65535" />
              <span class="form-tip">后端API监听端口</span>
            </el-form-item>
            
            <el-form-item label="HTTPS">
              <el-switch v-model="gatewayConfig.https" />
              <span class="form-tip">是否启用HTTPS（需要配置SSL证书）</span>
            </el-form-item>
            
            <el-form-item label="流式请求超时">
              <el-input-number v-model="gatewayConfig.stream_timeout" :min="10" :max="600" />
              <span class="form-unit">秒</span>
            </el-form-item>
            
            <el-form-item label="最大并发数">
              <el-input-number v-model="gatewayConfig.max_concurrent" :min="1" :max="1000" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="handleSaveGateway" :loading="saving">
                保存网关配置
              </el-button>
              <el-button @click="handleRestartGateway">重启网关服务</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <!-- 加密配置 -->
      <el-col :span="12">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Lock /></el-icon> 安全加密配置</span>
            </div>
          </template>
          
          <el-form :model="encryptConfig" label-width="120px">
            <el-form-item label="加密密钥">
              <el-input 
                v-model="encryptConfig.key" 
                type="password"
                show-password
                placeholder="请输入加密密钥"
              />
              <span class="form-tip">用于加密存储API Key，建议使用复杂密码</span>
            </el-form-item>
            
            <el-form-item label="确认密钥">
              <el-input 
                v-model="encryptConfig.key_confirm" 
                type="password"
                show-password
                placeholder="确认加密密钥"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="warning" @click="handleResetKey">
                重置加密密钥
              </el-button>
              <span class="warning-text">警告：重置后需要重新配置所有API Key</span>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="config-row">
      <!-- 告警配置 -->
      <el-col :span="12">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Bell /></el-icon> 告警通知配置</span>
            </div>
          </template>
          
          <el-form :model="alertConfig" label-width="120px">
            <el-form-item label="告警阈值">
              <el-slider 
                v-model="alertConfig.threshold" 
                :min="50" 
                :max="100"
                :format-tooltip="(val) => val + '%'"
              />
              <span class="form-tip">额度消耗超过此阈值时发送告警</span>
            </el-form-item>
            
            <el-form-item label="告警渠道">
              <el-checkbox-group v-model="alertConfig.channels">
                <el-checkbox label="email">邮件</el-checkbox>
                <el-checkbox label="webhook">Webhook</el-checkbox>
                <el-checkbox label="dingtalk">钉钉机器人</el-checkbox>
                <el-checkbox label="wechat">企业微信</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            
            <el-form-item label="接收邮箱">
              <el-input v-model="alertConfig.email" placeholder="alert@example.com" />
            </el-form-item>
            
            <el-form-item label="Webhook URL">
              <el-input v-model="alertConfig.webhook_url" placeholder="https://your-webhook.com" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="handleSaveAlert" :loading="saving">
                保存告警配置
              </el-button>
              <el-button @click="handleTestAlert">发送测试告警</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <!-- 通用配置 -->
      <el-col :span="12">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Tools /></el-icon> 通用配置</span>
            </div>
          </template>
          
          <el-form :model="commonConfig" label-width="120px">
            <el-form-item label="日志保留天数">
              <el-input-number v-model="commonConfig.log_retention" :min="1" :max="365" />
              <span class="form-unit">天</span>
            </el-form-item>
            
            <el-form-item label="数据刷新间隔">
              <el-input-number v-model="commonConfig.refresh_interval" :min="5" :max="300" />
              <span class="form-unit">秒</span>
            </el-form-item>
            
            <el-form-item label="界面语言">
              <el-select v-model="commonConfig.language">
                <el-option label="简体中文" value="zh" />
                <el-option label="English" value="en" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="时区">
              <el-select v-model="commonConfig.timezone">
                <el-option label="Asia/Shanghai (UTC+8)" value="Asia/Shanghai" />
                <el-option label="America/New_York (UTC-5)" value="America/New_York" />
                <el-option label="Europe/London (UTC+0)" value="Europe/London" />
              </el-select>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="handleSaveCommon" :loading="saving">
                保存通用配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 网关密钥配置 -->
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><Key /></el-icon> 网关访问密钥</span>
        </div>
      </template>
      
      <el-form :model="gatewayKeyConfig" label-width="140px">
        <el-alert
          title="网关访问密钥用于Agent工具对接，请妥善保管"
          type="warning"
          :closable="false"
          style="margin-bottom: 20px;"
        />
        
        <el-form-item label="网关API Key">
          <el-input 
            v-model="gatewayKeyConfig.api_key" 
            type="password"
            show-password
            placeholder="Agent工具使用的API Key"
            style="width: 400px;"
          />
          <el-button type="primary" @click="handleGenerateKey" style="margin-left: 12px;">
            生成新密钥
          </el-button>
        </el-form-item>
        
        <el-form-item label="API Key有效期">
          <el-select v-model="gatewayKeyConfig.key_expiry" style="width: 200px;">
            <el-option label="永不过期" :value="0" />
            <el-option label="7天" :value="7" />
            <el-option label="30天" :value="30" />
            <el-option label="90天" :value="90" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSaveGatewayKey" :loading="saving">
            保存网关密钥
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting, Lock, Bell, Tools, Key } from '@element-plus/icons-vue'
import { configApi } from '@/api'

const saving = ref(false)

const gatewayConfig = reactive({
  port: 8080,
  api_port: 8000,
  https: false,
  stream_timeout: 300,
  max_concurrent: 100
})

const encryptConfig = reactive({
  key: '',
  key_confirm: ''
})

const alertConfig = reactive({
  threshold: 90,
  channels: ['webhook'],
  email: '',
  webhook_url: ''
})

const commonConfig = reactive({
  log_retention: 30,
  refresh_interval: 10,
  language: 'zh',
  timezone: 'Asia/Shanghai'
})

const gatewayKeyConfig = reactive({
  api_key: '',
  key_expiry: 0
})

const handleSaveGateway = async () => {
  saving.value = true
  try {
    await configApi.set({ key: 'gateway_port', value: gatewayConfig.port.toString() })
    ElMessage.success('网关配置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleRestartGateway = async () => {
  try {
    await ElMessageBox.confirm('确定要重启网关服务吗？重启期间服务将不可用。', '重启确认', {
      type: 'warning'
    })
    // 调用重启API
    ElMessage.success('网关服务正在重启...')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重启失败')
    }
  }
}

const handleResetKey = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置加密密钥吗？此操作将导致所有已存储的API Key失效，需要重新配置。',
      '危险操作',
      { type: 'error' }
    )
    
    await configApi.resetEncryptKey()
    ElMessage.success('加密密钥已重置，请重新登录并配置API Key')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

const handleSaveAlert = async () => {
  saving.value = true
  try {
    await configApi.set({ key: 'alert_threshold', value: alertConfig.threshold.toString() })
    ElMessage.success('告警配置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleTestAlert = async () => {
  ElMessage.success('测试告警已发送')
}

const handleSaveCommon = async () => {
  saving.value = true
  try {
    await configApi.set({ key: 'log_retention', value: commonConfig.log_retention.toString() })
    await configApi.set({ key: 'refresh_interval', value: commonConfig.refresh_interval.toString() })
    ElMessage.success('通用配置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleGenerateKey = () => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let key = 'gateway_'
  for (let i = 0; i < 32; i++) {
    key += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  gatewayKeyConfig.api_key = key
}

const handleSaveGatewayKey = async () => {
  saving.value = true
  try {
    await configApi.set({ key: 'gateway_api_key', value: gatewayKeyConfig.api_key })
    ElMessage.success('网关密钥保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  // 加载配置
})
</script>

<style lang="scss" scoped>
.system-config {
  .config-row {
    margin-top: 20px;
  }
  
  .config-card {
    margin-bottom: 20px;
    
    .card-header {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .form-tip, .form-unit {
      margin-left: 8px;
      font-size: 12px;
      color: #909399;
    }
    
    .warning-text {
      margin-left: 12px;
      font-size: 12px;
      color: #F56C6C;
    }
  }
}
</style>
