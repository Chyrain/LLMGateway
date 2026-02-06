<template>
  <div class="logs-page">
    <!-- 日志筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="日志类型">
          <el-select v-model="filters.log_type" placeholder="全部" clearable>
            <el-option label="访问日志" :value="1" />
            <el-option label="切换日志" :value="2" />
            <el-option label="错误日志" :value="3" />
            <el-option label="测试日志" :value="4" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型">
          <el-select v-model="filters.model_id" placeholder="全部" clearable>
            <el-option 
              v-for="m in modelList" 
              :key="m.id" 
              :label="m.model_name" 
              :value="m.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable>
            <el-option label="成功" :value="1" />
            <el-option label="失败" :value="0" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filters.date_range"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            :shortcuts="dateShortcuts"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-radio-group v-model="activeTab" size="small">
              <el-radio-button :label="null">全部</el-radio-button>
              <el-radio-button :label="1">访问日志</el-radio-button>
              <el-radio-button :label="2">切换日志</el-radio-button>
              <el-radio-button :label="3">错误日志</el-radio-button>
            </el-radio-group>
          </div>
          <div class="header-actions">
            <el-button @click="handleExport">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
            <el-button type="danger" @click="handleClear" :loading="clearing">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe @row-click="handleRowClick">
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.create_time) }}
          </template>
        </el-table-column>
        
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getLogTypeTag(row.log_type)" size="small">
              {{ getLogTypeName(row.log_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="模型" width="150">
          <template #default="{ row }">
            {{ getModelName(row.model_id) }}
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-icon :color="row.status ? '#67C23A' : '#F56C6C'">
              <CircleCheck v-if="row.status" />
              <CircleClose v-else />
            </el-icon>
          </template>
        </el-table-column>
        
        <el-table-column label="内容" min-width="300">
          <template #default="{ row }">
            <el-button 
              v-if="row.log_content && row.log_content.length > 100"
              type="primary" 
              link
              @click.stop="handleViewContent(row)"
            >
              查看详情
            </el-button>
            <span v-else>{{ row.log_content }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[20, 50, 100, 200]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="日志详情"
      width="700px"
    >
      <el-descriptions :column="2" border v-if="currentLog">
        <el-descriptions-item label="日志ID" :span="2">
          {{ currentLog.id }}
        </el-descriptions-item>
        <el-descriptions-item label="日志类型">
          <el-tag :type="getLogTypeTag(currentLog.log_type)">
            {{ getLogTypeName(currentLog.log_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-icon :color="currentLog.status ? '#67C23A' : '#F56C6C'">
            <CircleCheck v-if="currentLog.status" />
            <CircleClose v-else />
          </el-icon>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatTime(currentLog.create_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="关联模型">
          {{ getModelName(currentLog.model_id) }}
        </el-descriptions-item>
        <el-descriptions-item label="日志内容" :span="2">
          <el-input
            type="textarea"
            :rows="10"
            :value="currentLog.log_content"
            readonly
            class="log-content"
          />
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Download, Delete, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { logApi, modelApi } from '@/api'
import dayjs from 'dayjs'

const loading = ref(false)
const clearing = ref(false)
const tableData = ref([])
const modelList = ref([])
const detailVisible = ref(false)
const currentLog = ref(null)
const activeTab = ref(null)

const filters = reactive({
  log_type: null,
  model_id: null,
  status: null,
  date_range: null
})

const pagination = reactive({
  page: 1,
  size: 50,
  total: 0
})

const dateShortcuts = [
  { text: '今天', value: () => [dayjs().startOf('day'), dayjs().endOf('day')] },
  { text: '最近3天', value: () => [dayjs().subtract(3, 'day'), dayjs().endOf('day')] },
  { text: '最近7天', value: () => [dayjs().subtract(7, 'day'), dayjs().endOf('day')] },
  { text: '最近30天', value: () => [dayjs().subtract(30, 'day'), dayjs().endOf('day')] }
]

watch(activeTab, (val) => {
  filters.log_type = val
  pagination.page = 1
  fetchData()
})

const formatTime = (time) => {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'
}

const getLogTypeName = (type) => {
  const map = { 1: '访问日志', 2: '切换日志', 3: '错误日志', 4: '测试日志' }
  return map[type] || '未知'
}

const getLogTypeTag = (type) => {
  const map = { 1: '', 2: 'success', 3: 'danger', 4: 'info' }
  return map[type] || 'info'
}

const getModelName = (modelId) => {
  if (!modelId) return '-'
  const model = modelList.value.find(m => m.id === modelId)
  return model ? `${model.vendor}/${model.model_name}` : `ID: ${modelId}`
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      log_type: filters.log_type,
      model_id: filters.model_id,
      status: filters.status
    }
    
    if (filters.date_range) {
      params.start_time = filters.date_range[0].toISOString()
      params.end_time = filters.date_range[1].toISOString()
    }
    
    const res = await logApi.list(params)
    
    // 后端返回: { code, msg, data: [...] }
    tableData.value = res.data || []
    pagination.total = tableData.value.length
  } catch (error) {
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

const fetchModels = async () => {
  try {
    const res = await modelApi.list()
    modelList.value = res.data || []
  } catch (error) {
    console.error('获取模型列表失败')
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  filters.log_type = null
  filters.model_id = null
  filters.status = null
  filters.date_range = null
  activeTab.value = null
  handleSearch()
}

const handleSizeChange = () => {
  pagination.page = 1
  fetchData()
}

const handlePageChange = () => {
  fetchData()
}

const handleRowClick = (row) => {
  // 可选：点击行显示详情
}

const handleViewContent = (row) => {
  currentLog.value = row
  detailVisible.value = true
}

const handleExport = async () => {
  try {
    await logApi.export(filters)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const handleClear = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有日志吗？此操作不可恢复。',
      '清空确认',
      { type: 'warning' }
    )
    clearing.value = true
    await logApi.clear(filters.log_type)
    ElMessage.success('日志已清空')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清空失败')
    }
  } finally {
    clearing.value = false
  }
}

onMounted(() => {
  fetchData()
  fetchModels()
})
</script>

<style lang="scss" scoped>
.logs-page {
  .filter-card {
    margin-bottom: 20px;
  }
  
  .table-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-actions {
        display: flex;
        gap: 12px;
      }
    }
    
    .pagination-container {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
  
  .log-content {
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 12px;
  }
}
</style>
