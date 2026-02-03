<template>
  <div class="quota-monitor">
    <!-- 统计概览 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ totalQuota }}</div>
            <div class="stat-label">总剩余额度 (Tokens)</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ totalUsed }}</div>
            <div class="stat-label">已用额度 (Tokens)</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ avgUsage }}%</div>
            <div class="stat-label">平均使用率</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ alertCount }}</div>
            <div class="stat-label">告警模型数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 切换规则配置 -->
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>自动切换规则</span>
          <el-button type="primary" @click="handleSaveConfig" :loading="saving">
            保存配置
          </el-button>
        </div>
      </template>
      
      <el-form :model="switchConfig" label-width="160px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="全局切换阈值">
              <el-slider 
                v-model="switchConfig.threshold" 
                :min="50" 
                :max="100"
                :step="1"
                :format-tooltip="(val) => val + '%'"
              />
              <span class="form-tip">当模型额度消耗超过此阈值时自动切换</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="切换策略">
              <el-radio-group v-model="switchConfig.strategy">
                <el-radio label="priority">按优先级切换</el-radio>
                <el-radio label="quota">按剩余额度切换</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="兜底策略">
          <el-checkbox v-model="switchConfig.disableOnEmpty">
            所有模型额度耗尽时禁用网关服务
          </el-checkbox>
        </el-form-item>
        
        <el-form-item label="监控间隔">
          <el-input-number 
            v-model="switchConfig.interval" 
            :min="5" 
            :max="300"
          />
          <span class="form-unit">秒</span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 模型额度列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>模型额度详情</span>
          <div class="header-actions">
            <el-button @click="handleSyncAll">
              <el-icon><Refresh /></el-icon>
              同步全部额度
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="quotaList" v-loading="loading" stripe>
        <el-table-column prop="vendor" label="厂商" width="120">
          <template #default="{ row }">
            <el-tag>{{ getVendorName(row.vendor) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="model_name" label="模型" min-width="150" />
        
        <el-table-column label="总额度" width="150">
          <template #default="{ row }">
            {{ formatQuota(row.total_quota) }}
          </template>
        </el-table-column>
        
        <el-table-column label="已用额度" width="150">
          <template #default="{ row }">
            {{ formatQuota(row.used_quota) }}
          </template>
        </el-table-column>
        
        <el-table-column label="剩余额度" width="150">
          <template #default="{ row }">
            {{ formatQuota(row.remain_quota) }}
          </template>
        </el-table-column>
        
        <el-table-column label="使用率" width="200">
          <template #default="{ row }">
            <el-progress 
              :percentage="Math.round(row.used_ratio)" 
              :stroke-width="8"
              :status="getProgressStatus(row.used_ratio)"
              :show-text="false"
            />
            <span class="usage-text">{{ row.used_ratio.toFixed(1) }}%</span>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getQuotaTagType(row.quota_status)" size="small">
              {{ getQuotaStatus(row.quota_status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button-group>
              <el-tooltip content="同步额度">
                <el-button size="small" @click="handleSync(row)">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="手动录入">
                <el-button size="small" @click="handleManualUpdate(row)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 额度使用图表 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>额度使用占比</span>
          </template>
          <v-chart class="chart" :option="pieOption" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>近7天使用趋势</span>
          </template>
          <v-chart class="chart" :option="lineOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- 手动录入对话框 -->
    <el-dialog
      v-model="manualDialogVisible"
      title="手动录入额度"
      width="400px"
    >
      <el-form :model="manualForm" label-width="100px">
        <el-form-item label="模型">
          <el-input :value="manualForm.model_name" disabled />
        </el-form-item>
        <el-form-item label="总额度">
          <el-input-number 
            v-model="manualForm.total_quota" 
            :min="0"
            :precision="0"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="已用额度">
          <el-input-number 
            v-model="manualForm.used_quota" 
            :min="0"
            :precision="0"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="manualDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleManualSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import { Refresh, Edit } from '@element-plus/icons-vue'
import { quotaApi, configApi } from '@/api'

use([CanvasRenderer, PieChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const loading = ref(false)
const saving = ref(false)
const quotaList = ref([])
const manualDialogVisible = ref(false)

const switchConfig = reactive({
  threshold: 99,
  strategy: 'priority',
  disableOnEmpty: false,
  interval: 10
})

const manualForm = reactive({
  model_id: null,
  model_name: '',
  total_quota: 0,
  used_quota: 0
})

// 计算属性
const totalQuota = computed(() => {
  return quotaList.value.reduce((sum, item) => sum + (item.total_quota || 0), 0)
})

const totalUsed = computed(() => {
  return quotaList.value.reduce((sum, item) => sum + (item.used_quota || 0), 0)
})

const avgUsage = computed(() => {
  if (quotaList.value.length === 0) return 0
  const total = quotaList.value.reduce((sum, item) => sum + (item.used_ratio || 0), 0)
  return (total / quotaList.value.length).toFixed(1)
})

const alertCount = computed(() => {
  return quotaList.value.filter(item => item.quota_status === 1).length
})

// 图表配置
const pieOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { orient: 'vertical', left: 'left' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: quotaList.value.map(item => ({
      name: item.model_name,
      value: item.used_quota
    }))
  }]
}))

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['使用量'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  },
  yAxis: { type: 'value' },
  series: [{
    name: '使用量',
    type: 'line',
    smooth: true,
    data: [120, 132, 101, 134, 90, 230, 210],
    areaStyle: { opacity: 0.1 }
  }]
}))

// 厂商名称映射
const vendorNameMap = {
  openai: 'OpenAI',
  qwen: '通义千问',
  zhipu: '智谱清言',
  spark: '讯飞星火',
  doubao: '字节豆包',
  claude: 'Claude',
  gemini: 'Google Gemini',
  mistral: 'Mistral',
  groq: 'Groq'
}

const getVendorName = (vendor) => vendorNameMap[vendor] || vendor

const formatQuota = (quota) => {
  if (!quota) return '0'
  if (quota >= 1000000) return `${(quota / 1000000).toFixed(1)}M`
  if (quota >= 1000) return `${(quota / 1000).toFixed(1)}K`
  return quota.toString()
}

const getQuotaStatus = (status) => {
  const map = { 0: '已耗尽', 1: '即将耗尽', 2: '充足' }
  return map[status] || '未知'
}

const getQuotaTagType = (status) => {
  const map = { 0: 'danger', 1: 'warning', 2: 'success' }
  return map[status] || 'info'
}

const getProgressStatus = (ratio) => {
  if (ratio >= 90) return 'exception'
  if (ratio >= 70) return 'warning'
  return 'success'
}

const fetchQuotaData = async () => {
  loading.value = true
  try {
    const res = await quotaApi.stat()
    quotaList.value = res.data || []
  } catch (error) {
    ElMessage.error('获取额度数据失败')
  } finally {
    loading.value = false
  }
}

const fetchSwitchConfig = async () => {
  try {
    const res = await configApi.get('switch_threshold')
    if (res.data) {
      switchConfig.threshold = parseInt(res.data.config_value) || 99
    }
  } catch (error) {
    console.error('获取切换配置失败')
  }
}

const handleSync = async (row) => {
  try {
    await quotaApi.sync(row.model_id)
    ElMessage.success('额度同步成功')
    fetchQuotaData()
  } catch (error) {
    ElMessage.error('额度同步失败')
  }
}

const handleSyncAll = async () => {
  for (const item of quotaList.value) {
    try {
      await quotaApi.sync(item.model_id)
    } catch (error) {
      console.error(`模型 ${item.model_name} 同步失败`)
    }
  }
  ElMessage.success('全部同步完成')
  fetchQuotaData()
}

const handleManualUpdate = (row) => {
  manualForm.model_id = row.model_id
  manualForm.model_name = row.model_name
  manualForm.total_quota = row.total_quota
  manualForm.used_quota = row.used_quota
  manualDialogVisible.value = true
}

const handleManualSave = async () => {
  try {
    await quotaApi.update(manualForm.model_id, {
      total_quota: manualForm.total_quota,
      used_quota: manualForm.used_quota
    })
    ElMessage.success('保存成功')
    manualDialogVisible.value = false
    fetchQuotaData()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const handleSaveConfig = async () => {
  saving.value = true
  try {
    await configApi.set({
      key: 'switch_threshold',
      value: switchConfig.threshold.toString()
    })
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('配置保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchQuotaData()
  fetchSwitchConfig()
})
</script>

<style lang="scss" scoped>
.quota-monitor {
  .stat-row {
    margin-bottom: 20px;
    
    .stat-card {
      .stat-content {
        text-align: center;
        
        .stat-value {
          font-size: 28px;
          font-weight: bold;
          color: #303133;
        }
        
        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-top: 8px;
        }
      }
    }
  }
  
  .config-card {
    margin-bottom: 20px;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
  
  .table-card {
    margin-bottom: 20px;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .usage-text {
      margin-left: 8px;
      font-size: 12px;
      color: #606266;
    }
  }
  
  .chart-row {
    .chart-card {
      .chart {
        height: 300px;
      }
    }
  }
  
  .form-tip, .form-unit {
    margin-left: 8px;
    font-size: 12px;
    color: #909399;
  }
}
</style>
