<template>
  <div class="model-config">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="厂商">
          <el-select v-model="filters.vendor" placeholder="全部" clearable>
            <el-option 
              v-for="v in vendorOptions" 
              :key="v.value" 
              :label="v.label" 
              :value="v.value" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable>
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>模型配置列表</span>
          <div class="header-actions">
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>
              添加模型
            </el-button>
            <el-button @click="handleBatchTest">
              <el-icon><Connection /></el-icon>
              批量测试
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="vendor" label="厂商" width="120">
          <template #default="{ row }">
            <el-tag>{{ getVendorName(row.vendor) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="model_name" label="模型名称" min-width="150" />
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.status"
              :active-value="1"
              :inactive-value="0"
              @change="handleStatusChange(row)"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="连通性" width="100">
          <template #default="{ row }">
            <el-icon :color="row.connect_status ? '#67C23A' : '#F56C6C'">
              <CircleCheck v-if="row.connect_status" />
              <CircleClose v-else />
            </el-icon>
          </template>
        </el-table-column>
        
        <el-table-column label="额度" width="120">
          <template #default="{ row }">
            <el-tag :type="getQuotaTagType(row.quota_status)" size="small">
              {{ getQuotaStatus(row.quota_status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="priority" label="优先级" width="80" />
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-tooltip content="测试连通">
                <el-button size="small" @click="handleTest(row)">
                  <el-icon><Connection /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="编辑">
                <el-button size="small" @click="handleEdit(row)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="删除">
                <el-button size="small" type="danger" @click="handleDelete(row)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '添加模型' : '编辑模型'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="厂商" prop="vendor">
          <el-select v-model="formData.vendor" placeholder="选择厂商" @change="handleVendorChange">
            <el-option 
              v-for="v in vendorOptions" 
              :key="v.value" 
              :label="v.label" 
              :value="v.value" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型名称" prop="model_name">
          <el-select 
            v-model="formData.model_name" 
            placeholder="选择模型"
            :disabled="dialogType === 'edit'"
          >
            <el-option 
              v-for="m in getModelOptions(formData.vendor)" 
              :key="m" 
              :label="m" 
              :value="m" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="API Key" prop="api_key">
          <el-input 
            v-model="formData.api_key" 
            type="password"
            show-password
            placeholder="请输入API Key"
          />
        </el-form-item>
        
        <el-form-item label="API地址" prop="api_base">
          <el-input v-model="formData.api_base" placeholder="API基础地址" />
        </el-form-item>
        
        <el-form-item label="温度" prop="temperature">
          <el-slider 
            v-model="formData.temperature" 
            :min="0" 
            :max="2" 
            :step="0.1"
            :marks="{0: '0', 1: '1', 2: '2'}"
          />
        </el-form-item>
        
        <el-form-item label="最大Token" prop="max_tokens">
          <el-input-number v-model="formData.max_tokens" :min="1" :max="32768" />
        </el-form-item>
        
        <el-form-item label="优先级" prop="priority">
          <el-input-number v-model="formData.priority" :min="1" :max="999" />
          <span class="form-tip">数字越小优先级越高</span>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          测试并保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Connection, Edit, Delete, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { modelApi } from '@/api'

const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const dialogType = ref('add')
const formRef = ref(null)

const filters = reactive({
  vendor: null,
  status: null
})

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const formData = reactive({
  id: null,
  vendor: '',
  model_name: '',
  api_key: '',
  api_base: '',
  temperature: 0.7,
  max_tokens: 2048,
  priority: 100
})

const formRules = {
  vendor: [{ required: true, message: '请选择厂商', trigger: 'change' }],
  model_name: [{ required: true, message: '请选择模型', trigger: 'change' }],
  api_key: [{ required: true, message: '请输入API Key', trigger: 'blur' }]
}

// 厂商选项
const vendorOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'qwen', label: '通义千问' },
  { value: 'zhipu', label: '智谱清言' },
  { value: 'spark', label: '讯飞星火' },
  { value: 'doubao', label: '字节豆包' },
  { value: 'claude', label: 'Claude' },
  { value: 'gemini', label: 'Google Gemini' },
  { value: 'mistral', label: 'Mistral' },
  { value: 'groq', label: 'Groq (Llama3)' }
]

// 模型配置模板
const modelTemplates = {
  openai: ['gpt-3.5-turbo', 'gpt-4o', 'gpt-4o-mini'],
  qwen: ['qwen-turbo', 'qwen-plus', 'qwen-max'],
  zhipu: ['glm-3-turbo', 'glm-4', 'glm-4v'],
  spark: ['spark-v3.1', 'spark-v3.5'],
  doubao: ['Doubao-pro-32k'],
  claude: ['claude-sonnet-4-20250514', 'claude-haiku-3-20250514'],
  gemini: ['gemini-pro', 'gemini-pro-vision'],
  mistral: ['mistral-tiny', 'mistral-small', 'mistral-medium'],
  groq: ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768']
}

const getVendorName = (vendor) => {
  return vendorOptions.find(v => v.value === vendor)?.label || vendor
}

const getModelOptions = (vendor) => {
  return modelTemplates[vendor] || []
}

const getQuotaStatus = (status) => {
  const map = { 0: '已耗尽', 1: '即将耗尽', 2: '充足' }
  return map[status] || '未知'
}

const getQuotaTagType = (status) => {
  const map = { 0: 'danger', 1: 'warning', 2: 'success' }
  return map[status] || 'info'
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await modelApi.list({
      vendor: filters.vendor,
      status: filters.status
    })
    // 后端返回: { code, msg, data: [...] }
    tableData.value = res.data || []
    pagination.total = tableData.value.length
  } catch (error) {
    ElMessage.error('获取模型列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  filters.vendor = null
  filters.status = null
  handleSearch()
}

const handleSizeChange = () => {
  pagination.page = 1
  fetchData()
}

const handlePageChange = () => {
  fetchData()
}

const handleAdd = () => {
  dialogType.value = 'add'
  Object.assign(formData, {
    id: null,
    vendor: '',
    model_name: '',
    api_key: '',
    api_base: '',
    temperature: 0.7,
    max_tokens: 2048,
    priority: 100
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogType.value = 'edit'
  Object.assign(formData, {
    id: row.id,
    vendor: row.vendor,
    model_name: row.model_name,
    api_key: '',
    api_base: row.api_base || '',
    temperature: row.params?.temperature || 0.7,
    max_tokens: row.params?.max_tokens || 2048,
    priority: row.priority
  })
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${row.model_name}" 吗？`,
      '删除确认',
      { type: 'warning' }
    )
    await modelApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleTest = async (row) => {
  try {
    await modelApi.test(row.id)
    ElMessage.success('连通测试成功')
    fetchData()
  } catch (error) {
    ElMessage.error('连通测试失败')
  }
}

const handleBatchTest = async () => {
  const enabledModels = tableData.value.filter(m => m.status === 1)
  if (enabledModels.length === 0) {
    ElMessage.warning('没有启用的模型')
    return
  }
  
  for (const model of enabledModels) {
    try {
      await modelApi.test(model.id)
    } catch (error) {
      console.error(`模型 ${model.model_name} 测试失败`)
    }
  }
  ElMessage.success('批量测试完成')
  fetchData()
}

const handleStatusChange = async (row) => {
  try {
    if (row.status === 1) {
      await modelApi.enable(row.id)
    } else {
      await modelApi.disable(row.id)
    }
    ElMessage.success(row.status ? '已启用' : '已禁用')
  } catch (error) {
    row.status = row.status ? 0 : 1
    ElMessage.error('状态更新失败')
  }
}

const handleVendorChange = () => {
  formData.model_name = ''
  // 设置默认API地址
  const baseUrls = {
    openai: 'https://api.openai.com',
    qwen: 'https://dashscope.aliyuncs.com',
    zhipu: 'https://open.bigmodel.cn',
    claude: 'https://api.anthropic.com',
    gemini: 'https://generativelanguage.googleapis.com'
  }
  formData.api_base = baseUrls[formData.vendor] || ''
}

const handleSave = async () => {
  try {
    await formRef.value.validate()
    saving.value = true
    
    // 先测试连通性
    const testRes = await modelApi.test({ 
      vendor: formData.vendor,
      model_name: formData.model_name,
      api_key: formData.api_key,
      api_base: formData.api_base
    })
    
    // 保存配置
    const saveData = {
      vendor: formData.vendor,
      model_name: formData.model_name,
      api_key: formData.api_key,
      api_base: formData.api_base,
      params: {
        temperature: formData.temperature,
        max_tokens: formData.max_tokens
      },
      priority: formData.priority
    }
    
    if (dialogType.value === 'add') {
      await modelApi.add(saveData)
    } else {
      await modelApi.update(formData.id, saveData)
    }
    
    ElMessage.success(dialogType.value === 'add' ? '添加成功' : '更新成功')
    dialogVisible.value = false
    fetchData()
  } catch (error) {
    if (error !== false) {
      ElMessage.error(error.msg || '操作失败')
    }
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.model-config {
  .filter-card {
    margin-bottom: 20px;
  }
  
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
  
  .form-tip {
    margin-left: 8px;
    font-size: 12px;
    color: #909399;
  }
}
</style>
