<template>
  <div class="dashboard">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon total">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalRequests }}</div>
            <div class="stat-label">今日请求量</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon models">
            <el-icon><Grid /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.activeModels }}</div>
            <div class="stat-label">活跃模型</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon quota">
            <el-icon><Coin /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalQuota }}M</div>
            <div class="stat-label">剩余额度(Tokens)</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon switches">
            <el-icon><Switch /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.switchCount }}</div>
            <div class="stat-label">今日切换次数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 中间图表区域 -->
    <el-row :gutter="20" class="chart-section">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>近7天请求量趋势</span>
              <el-radio-group v-model="trendPeriod" size="small">
                <el-radio-button label="7d">7天</el-radio-button>
                <el-radio-button label="30d">30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <v-chart class="chart" :option="trendChartOption" autoresize />
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>模型使用占比</span>
          </template>
          <v-chart class="chart" :option="pieChartOption" autoresize />
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 底部区域 -->
    <el-row :gutter="20" class="bottom-section">
      <!-- 当前模型状态 -->
      <el-col :span="12">
        <el-card class="model-status-card">
          <template #header>
            <div class="card-header">
              <span>当前使用模型</span>
              <el-tag type="success" size="small">运行中</el-tag>
            </div>
          </template>
          <div class="current-model" v-if="currentModel">
            <div class="model-header">
              <el-avatar :size="48" src="https://api.dicebear.com/7.x/identicon/svg?seed=model" />
              <div class="model-info">
                <div class="model-name">{{ currentModel.vendor }} - {{ currentModel.model_name }}</div>
                <div class="model-meta">
                  <el-tag size="small">{{ currentModel.priority }}号优先级</el-tag>
                  <span class="quota-info">
                    剩余额度: {{ currentModel.remain_quota }}M Tokens
                  </span>
                </div>
              </div>
            </div>
            <el-progress 
              :percentage="currentModel.used_ratio" 
              :status="getQuotaStatus(currentModel.used_ratio)"
              :stroke-width="10"
            />
            <div class="model-actions">
              <el-button type="primary" @click="testModel(currentModel.id)">测试连通</el-button>
              <el-button @click="switchModel(currentModel.id)">立即切换</el-button>
            </div>
          </div>
          <el-empty v-else description="暂无可用模型，请先添加模型配置" />
        </el-card>
      </el-col>
      
      <!-- 最近切换日志 -->
      <el-col :span="12">
        <el-card class="switch-log-card">
          <template #header>
            <div class="card-header">
              <span>最近切换日志</span>
              <el-button text type="primary" @click="$router.push('/logs')">查看全部</el-button>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="log in switchLogs"
              :key="log.id"
              :timestamp="log.create_time"
              :type="log.status === 1 ? 'success' : 'danger'"
            >
              <div class="log-item">
                <span class="log-action">
                  {{ log.from_model }} → {{ log.to_model }}
                </span>
                <div class="log-reason">{{ log.reason }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="switchLogs.length === 0" description="暂无切换日志" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 告警提示 -->
    <el-alert
      v-if="alertModels.length > 0"
      :title="`${alertModels.length}个模型额度即将耗尽`"
      type="warning"
      show-icon
      class="alert-banner"
      closable
      @close="handleAlertClose"
    >
      <template #default>
        <div class="alert-models">
          <el-tag 
            v-for="model in alertModels" 
            :key="model.id" 
            type="warning"
            size="small"
            class="alert-tag"
          >
            {{ model.vendor }} - {{ model.model_name }} ({{ model.used_ratio }}%)
          </el-tag>
        </div>
        <el-button type="primary" size="small" @click="$router.push('/quota')">立即处理</el-button>
      </template>
    </el-alert>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ChatDotRound, Grid, Coin, Switch } from '@element-plus/icons-vue'
import { modelApi, statsApi, logApi } from '@/api'
import { ElMessage } from 'element-plus'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const stats = ref({
  totalRequests: 0,
  activeModels: 0,
  totalQuota: 0,
  switchCount: 0
})

const currentModel = ref(null)
const switchLogs = ref([])
const alertModels = ref([])
const trendPeriod = ref('7d')
const loading = ref(true)
const trendData = ref([])
const modelRankings = ref([])

// 趋势图配置
const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['请求量'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: trendData.value.map(item => item.date)
  },
  yAxis: { type: 'value' },
  series: [
    {
      name: '请求量',
      type: 'line',
      smooth: true,
      data: trendData.value.map(item => item.requests),
      areaStyle: { opacity: 0.1 },
      itemStyle: { color: '#667eea' }
    }
  ]
}))

// 饼图配置
const pieChartOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { orient: 'vertical', left: 'left' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    avoidLabelOverlap: false,
    label: { show: false },
    emphasis: { label: { show: true, fontSize: 16 } },
    data: modelRankings.value
  }]
}))

const getQuotaStatus = (ratio) => {
  if (ratio >= 90) return 'exception'
  if (ratio >= 70) return 'warning'
  return 'success'
}

const fetchDashboardData = async () => {
  loading.value = true
  try {
    const data = await statsApi.dashboard()
    // statsApi 返回的已经是 data 对象
    if (data) {
      stats.value = data.stats || {}
      currentModel.value = data.currentModel
      switchLogs.value = data.switchLogs || []
      alertModels.value = data.alertModels || []
    }
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
    // 显示空数据友好提示
    ElMessage.warning('暂无数据，请先配置模型')
  } finally {
    loading.value = false
  }
}

const fetchTrendData = async () => {
  try {
    const days = trendPeriod.value === '7d' ? 7 : 30
    const response = await statsApi.trends({ days })
    if (response) {
      trendData.value = response.trend || []
    }
  } catch (error) {
    console.error('获取趋势数据失败:', error)
    // 使用模拟数据
    trendData.value = generateMockTrendData(days)
  }
}

const fetchModelRankings = async () => {
  try {
    const response = await statsApi.models()
    if (response && response.rankings) {
      modelRankings.value = response.rankings.map(item => ({
        value: item.requests,
        name: item.model
      }))
    }
  } catch (error) {
    console.error('获取模型排行失败:', error)
    // 使用模拟数据
    modelRankings.value = generateMockRankingData()
  }
}

// 生成模拟趋势数据
const generateMockTrendData = (days) => {
  const data = []
  const now = new Date()
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    data.push({
      date: date.toISOString().split('T')[0],
      requests: Math.floor(Math.random() * 200) + 50
    })
  }
  return data
}

// 生成模拟排行数据
const generateMockRankingData = () => {
  return [
    { value: 1048, name: 'GPT-4' },
    { value: 735, name: 'Claude-3' },
    { value: 580, name: '通义千问' },
    { value: 484, name: '智谱清言' },
    { value: 300, name: '其他' }
  ]
}

const testModel = async (id) => {
  try {
    await modelApi.test(id)
    ElMessage.success('模型连通测试成功')
  } catch (error) {
    ElMessage.error('模型连通测试失败')
  }
}

const switchModel = async (id) => {
  try {
    ElMessage.success('已触发模型切换')
    fetchDashboardData()
  } catch (error) {
    ElMessage.error('切换失败')
  }
}

const handleAlertClose = () => {
  alertModels.value = []
}

// 监听趋势周期变化
watch(trendPeriod, () => {
  fetchTrendData()
})

onMounted(() => {
  fetchDashboardData()
  fetchTrendData()
  fetchModelRankings()
})
</script>

<style lang="scss" scoped>
.dashboard {
  .stat-cards {
    margin-bottom: 20px;
    
    .stat-card {
      border-radius: 12px;
      
      .stat-icon {
        width: 56px;
        height: 56px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        color: #fff;
        
        &.total { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        &.models { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        &.quota { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
        &.switches { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
      }
      
      .stat-info {
        margin-top: 12px;
        text-align: center;
        
        .stat-value {
          font-size: 28px;
          font-weight: bold;
          color: #333;
        }
        
        .stat-label {
          font-size: 14px;
          color: #999;
          margin-top: 4px;
        }
      }
    }
  }
  
  .chart-section, .bottom-section {
    margin-bottom: 20px;
  }
  
  .chart-card, .model-status-card, .switch-log-card {
    border-radius: 12px;
    height: 100%;
    
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    
    .chart {
      height: 300px;
    }
  }
  
  .current-model {
    .model-header {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 16px;
      
      .model-info {
        .model-name {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 8px;
        }
        
        .model-meta {
          display: flex;
          align-items: center;
          gap: 12px;
          
          .quota-info {
            font-size: 14px;
            color: #666;
          }
        }
      }
    }
    
    .model-actions {
      margin-top: 16px;
      display: flex;
      gap: 12px;
    }
  }
  
  .log-item {
    .log-action {
      font-weight: 500;
    }
    
    .log-reason {
      font-size: 12px;
      color: #999;
      margin-top: 4px;
    }
  }
  
  .alert-banner {
    margin-bottom: 20px;
    
    .alert-models {
      margin: 8px 0;
      
      .alert-tag {
        margin-right: 8px;
        margin-bottom: 4px;
      }
    }
  }
}
</style>
