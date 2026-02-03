<template>
  <div class="agent-guide">
    <!-- 网关信息 -->
    <el-card class="gateway-info">
      <template #header>
        <div class="card-header">
          <span><el-icon><Connection /></el-icon> 网关连接信息</span>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="网关地址">
          <el-input 
            :value="gatewayInfo.base_url" 
            readonly
            class="copy-field"
          >
            <template #append>
              <el-button @click="copyToClipboard(gatewayInfo.base_url)">
                <el-icon><CopyDocument /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-descriptions-item>
        <el-descriptions-item label="API Key">
          <el-input 
            :value="gatewayInfo.api_key" 
            type="password"
            show-password
            readonly
            class="copy-field"
          >
            <template #append>
              <el-button @click="copyToClipboard(gatewayInfo.api_key)">
                <el-icon><CopyDocument /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 工具列表 -->
    <el-card class="tools-card">
      <template #header>
        <div class="card-header">
          <span>Agent工具适配指南</span>
          <el-tag type="success">已支持 {{ supportedTools.length }} 个工具</el-tag>
        </div>
      </template>
      
      <el-collapse v-model="activeCollapse">
        <!-- OpenClaw -->
        <el-collapse-item title="OpenClaw" name="openclaw">
          <template #title>
            <div class="tool-title">
              <img src="https://openclaw.ai/favicon.ico" class="tool-icon" />
              <span>OpenClaw - AI助手</span>
              <el-tag type="success" size="small" class="tool-tag">推荐</el-tag>
            </div>
          </template>
          
          <div class="tool-content">
            <el-alert
              title="OpenClaw配置方法"
              type="info"
              :closable="false"
              style="margin-bottom: 16px;"
            />
            
            <el-steps :active="3" simple>
              <el-step title="打开配置文件" description="config.yaml" />
              <el-step title="修改模型配置" description="替换为网关配置" />
              <el-step title="重启服务" description="启动OpenClaw" />
            </el-steps>
            
            <div class="config-example">
              <div class="code-header">
                <span>config.yaml 模型配置</span>
                <el-button type="primary" size="small" @click="copyOpenclawConfig">
                  <el-icon><CopyDocument /></el-icon>
                  复制配置
                </el-button>
              </div>
              <pre><code>{{ openclawConfig }}</code></pre>
            </div>
            
            <div class="tool-actions">
              <el-button type="primary" @click="downloadOpenclawScript">
                <el-icon><Download /></el-icon>
                下载一键适配脚本
              </el-button>
            </div>
          </div>
        </el-collapse-item>

        <!-- Claude Code -->
        <el-collapse-item title="Claude Code" name="claude">
          <template #title>
            <div class="tool-title">
              <img src="https://www.anthropic.com/favicon.ico" class="tool-icon" />
              <span>Claude Code - 终端AI编程助手</span>
            </div>
          </template>
          
          <div class="tool-content">
            <el-tabs>
              <el-tab-pane label="Mac/Linux">
                <div class="config-example">
                  <div class="code-header">
                    <span>终端配置命令</span>
                    <el-button type="primary" size="small" @click="copyClaudeLinuxCmd">
                      <el-icon><CopyDocument /></el-icon>
                      复制
                    </el-button>
                  </div>
                  <pre><code>{{ claudeLinuxCmd }}</code></pre>
                </div>
                
                <el-button type="primary" @click="downloadClaudeScript('sh')">
                  <el-icon><Download /></el-icon>
                  下载适配脚本 (Mac/Linux)
                </el-button>
              </el-tab-pane>
              
              <el-tab-pane label="Windows">
                <div class="config-example">
                  <div class="code-header">
                    <span>PowerShell命令</span>
                    <el-button type="primary" size="small" @click="copyClaudeWinCmd">
                      <el-icon><CopyDocument /></el-icon>
                      复制
                    </el-button>
                  </div>
                  <pre><code>{{ claudeWinCmd }}</code></pre>
                </div>
                
                <el-button type="primary" @click="downloadClaudeScript('bat')">
                  <el-icon><Download /></el-icon>
                  下载适配脚本 (Windows)
                </el-button>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-collapse-item>

        <!-- Cursor -->
        <el-collapse-item title="Cursor" name="cursor">
          <template #title>
            <div class="tool-title">
              <img src="https://cursor.sh/favicon.ico" class="tool-icon" />
              <span>Cursor - AI代码编辑器</span>
            </div>
          </template>
          
          <div class="tool-content">
            <el-steps :active="3" simple>
              <el-step title="打开设置" description="Settings" />
              <el-step title="选择Model" description="Cursor Settings" />
              <el-step title="配置网关" description="Custom API" />
            </el-steps>
            
            <el-alert
              title="配置步骤"
              type="success"
              :closable="false"
              style="margin: 16px 0;"
            >
              <ol style="margin: 8px 0; padding-left: 20px;">
                <li>打开 Cursor，点击顶部菜单 <b>Settings → Preferences → Cursor → Model</b></li>
                <li>关闭 <b>Use Default Model API</b></li>
                <li>在 <b>Custom API Base</b> 中填入网关地址</li>
                <li>在 <b>Custom API Key</b> 中填入网关API Key</li>
                <li>点击 <b>Save</b> 保存</li>
              </ol>
            </el-alert>
            
            <div class="config-example">
              <div class="code-header">
                <span>配置参数</span>
              </div>
              <pre><code>Custom API Base: {{ gatewayInfo.base_url }}
Custom API Key: {{ gatewayInfo.api_key }}</code></pre>
            </div>
          </div>
        </el-collapse-item>

        <!-- ChatGPT Next Web -->
        <el-collapse-item title="ChatGPT Next Web" name="chatgpt-next">
          <template #title>
            <div class="tool-title">
              <img src="https://github.com/ChatGPTNextWeb/ChatGPT-Next-Web/raw/main/public/appicon.png" class="tool-icon" />
              <span>ChatGPT Next Web</span>
            </div>
          </template>
          
          <div class="tool-content">
            <div class="config-example">
              <div class="code-header">
                <span>配置参数</span>
              </div>
              <pre><code>API Key: {{ gatewayInfo.api_key }}
Base URL: {{ gatewayInfo.base_url }}</code></pre>
            </div>
          </div>
        </el-collapse-item>

        <!-- 通用配置 -->
        <el-collapse-item title="其他工具 (通用配置)" name="generic">
          <template #title>
            <div class="tool-title">
              <el-icon><Box /></el-icon>
              <span>其他支持OpenAI协议的工具</span>
            </div>
          </template>
          
          <div class="tool-content">
            <el-alert
              title="通用配置方法"
              type="info"
              :closable="false"
              style="margin-bottom: 16px;"
            >
              大多数支持OpenAI API的工具都可以通过以下配置对接灵模网关：
            </el-alert>
            
            <div class="config-example">
              <div class="code-header">
                <span>通用配置参数</span>
              </div>
              <pre><code>{
  "base_url": "{{ gatewayInfo.base_url }}",
  "api_key": "{{ gatewayInfo.api_key }}",
  "model": "gpt-3.5-turbo"  // 可选，部分工具需要
}</code></pre>
            </div>
            
            <el-table :data="genericTools" style="margin-top: 16px;">
              <el-table-column prop="name" label="工具名称" />
              <el-table-column prop="config" label="配置方式" />
              <el-table-column prop="note" label="备注" />
            </el-table>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- 测试区域 -->
    <el-card class="test-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><Connection /></el-icon> 连通性测试</span>
        </div>
      </template>
      
      <div class="test-content">
        <el-form :inline="true" :model="testForm">
          <el-form-item label="测试模型">
            <el-select v-model="testForm.model_id" placeholder="选择模型">
              <el-option 
                v-for="m in modelList" 
                :key="m.id" 
                :label="`${m.vendor} - ${m.model_name}`" 
                :value="m.id" 
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleTest" :loading="testing">
              <el-icon><Connection /></el-icon>
              开始测试
            </el-button>
          </el-form-item>
        </el-form>
        
        <div v-if="testResult" class="test-result" :class="testResult.success ? 'success' : 'error'">
          <div class="result-header">
            <el-icon v-if="testResult.success"><CircleCheck /></el-icon>
            <el-icon v-else><CircleClose /></el-icon>
            <span>{{ testResult.success ? '测试成功' : '测试失败' }}</span>
          </div>
          <div class="result-content" v-if="testResult.message">
            {{ testResult.message }}
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection, CopyDocument, Box, CircleCheck, CircleClose, Download } from '@element-plus/icons-vue'
import { modelApi, configApi } from '@/api'

const activeCollapse = ref(['openclaw', 'claude', 'cursor'])

const gatewayInfo = reactive({
  base_url: 'http://localhost:8080/v1',
  api_key: 'gateway_123456'
})

const testForm = reactive({
  model_id: null
})

const testResult = ref(null)
const testing = ref(false)
const modelList = ref([])

const supportedTools = ['OpenClaw', 'Claude Code', 'Cursor', 'ChatGPT Next Web', 'LangChain', 'AutoGPT']

const genericTools = [
  { name: 'LangChain', config: 'openai_api_base', note: '环境变量或代码配置' },
  { name: 'AutoGPT', config: 'API Base', note: '配置文件' },
  { name: 'Anything LLM', config: 'Base URL', note: '设置页面' },
  { name: 'LibreChat', config: 'Endpoint Name', note: '自定义端点' },
  { name: 'OpenWebUI', config: 'OpenAI URL', note: '管理面板' }
]

const openclawConfig = `model:
  provider: openai
  name: gpt-3.5-turbo
  base_url: ${gatewayInfo.base_url}
  api_key: ${gatewayInfo.api_key}
  temperature: 0.7
  max_tokens: 2048`

const claudeLinuxCmd = `# 设置环境变量
export ANTHROPIC_API_KEY="${gatewayInfo.api_key}"
export ANTHROPIC_API_BASE="${gatewayInfo.base_url}"

# 启动Claude Code
claude`

const claudeWinCmd = `# PowerShell中执行
$env:ANTHROPIC_API_KEY="${gatewayInfo.api_key}"
$env:ANTHROPIC_API_BASE="${gatewayInfo.base_url}"

# 启动Claude Code
claude`

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const copyOpenclawConfig = () => copyToClipboard(openclawConfig)
const copyClaudeLinuxCmd = () => copyToClipboard(claudeLinuxCmd)
const copyClaudeWinCmd = () => copyToClipboard(claudeWinCmd)

const downloadOpenclawScript = () => {
  ElMessage.success('脚本下载功能开发中')
}

const downloadClaudeScript = (ext) => {
  ElMessage.success(`脚本下载功能开发中 (.${ext})`)
}

const handleTest = async () => {
  if (!testForm.model_id) {
    ElMessage.warning('请选择测试模型')
    return
  }
  
  testing.value = true
  testResult.value = null
  
  try {
    await modelApi.test(testForm.model_id)
    testResult.value = { success: true, message: '模型连通正常，可以正常使用' }
  } catch (error) {
    testResult.value = { success: false, message: error.msg || '连通测试失败，请检查配置' }
  } finally {
    testing.value = false
  }
}

const fetchModels = async () => {
  try {
    const res = await modelApi.list({ status: 1 })
    modelList.value = res.data || []
    if (modelList.value.length > 0) {
      testForm.model_id = modelList.value[0].id
    }
  } catch (error) {
    console.error('获取模型列表失败')
  }
}

const fetchGatewayConfig = async () => {
  try {
    const res = await configApi.get('gateway_api_key')
    if (res.data) {
      gatewayInfo.api_key = res.data.config_value
    }
  } catch (error) {
    console.error('获取网关配置失败')
  }
}

onMounted(() => {
  fetchModels()
  fetchGatewayConfig()
})
</script>

<style lang="scss" scoped>
.agent-guide {
  .gateway-info {
    margin-bottom: 20px;
    
    .copy-field {
      width: 100%;
    }
  }
  
  .tools-card {
    margin-bottom: 20px;
    
    .tool-title {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .tool-icon {
        width: 24px;
        height: 24px;
      }
      
      .tool-tag {
        margin-left: 8px;
      }
    }
    
    .tool-content {
      padding: 16px 0;
      
      .config-example {
        background: #f5f7fa;
        border-radius: 4px;
        margin: 16px 0;
        overflow: hidden;
        
        .code-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 16px;
          background: #e4e7ed;
          font-size: 12px;
          font-weight: 500;
        }
        
        pre {
          margin: 0;
          padding: 16px;
          overflow-x: auto;
          
          code {
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px;
            color: #606266;
          }
        }
      }
      
      .tool-actions {
        margin-top: 16px;
      }
    }
  }
  
  .test-card {
    .test-content {
      .test-result {
        margin-top: 16px;
        padding: 16px;
        border-radius: 4px;
        
        &.success {
          background: #f0f9eb;
          border: 1px solid #e1f3d8;
          
          .result-header {
            color: #67c23a;
          }
        }
        
        &.error {
          background: #fef0f0;
          border: 1px solid #fde2e2;
          
          .result-header {
            color: #f56c6c;
          }
        }
        
        .result-header {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 500;
          margin-bottom: 8px;
        }
        
        .result-content {
          font-size: 14px;
          color: #606266;
        }
      }
    }
  }
}
</style>
