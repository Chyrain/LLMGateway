import React, { useState, useEffect } from 'react';
import {
  Table, Card, Button, Tag, Space, Input, Select, Modal, Form,
  InputNumber, Switch, message, Popconfirm, Tooltip, Spin, Alert
} from 'antd';
import {
  PlusOutlined, ApiOutlined, EditOutlined,
  DeleteOutlined, SearchOutlined, CheckCircleFilled,
  CloseCircleFilled, CloudDownloadOutlined
} from '@ant-design/icons';
import { modelApi } from '../services/api';

// 厂商默认配置（API Base 和模型列表）
const VENDOR_CONFIGS = {
  openai: {
    name: 'OpenAI',
    apiBase: 'https://api.openai.com/v1',
    apiPath: '/chat/completions',
    apiSpec: 'openai',
    models: ['gpt-3.5-turbo', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4'],
    needApiKey: true
  },
  qwen: {
    name: '通义千问',
    apiBase: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    apiPath: '/chat/completions',
    apiSpec: 'openai',
    models: ['qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen2-72b-instruct'],
    needApiKey: true
  },
  zhipu: {
    name: '智谱 AI',
    apiBase: 'https://open.bigmodel.cn/api/paas/v4',
    apiPath: '/chat/completions',
    apiSpec: 'openai',
    models: ['glm-3-turbo', 'glm-4', 'glm-4v', 'glm-4-plus', 'glm-4.7'],
    needApiKey: true
  },
  spark: {
    name: '讯飞星火',
    apiBase: 'https://spark-api.xf-yun.com',
    apiPath: '/v3.5/chat',
    apiSpec: 'openai',
    models: ['spark-v3.1', 'spark-v3.5'],
    needApiKey: true
  },
  doubao: {
    name: '字节豆包',
    apiBase: 'https://ark.cn-beijing.volces.com/api/v3',
    apiPath: '/chat/completions',
    apiSpec: 'openai',
    models: ['Doubao-pro-32k', 'Doubao-pro-128k'],
    needApiKey: true
  },
  claude: {
    name: 'Claude',
    apiBase: 'https://api.anthropic.com/v1',
    apiPath: '/messages',
    apiSpec: 'anthropic',
    models: ['claude-sonnet-4-20250514', 'claude-haiku-3-20250514', 'claude-opus-4-20250514'],
    needApiKey: true
  },
  gemini: {
    name: 'Google Gemini',
    apiBase: 'https://generativelanguage.googleapis.com/v1beta',
    apiPath: '/models/gemini-pro:generateContent',
    apiSpec: 'gemini',
    models: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
    needApiKey: true
  },
  mistral: {
    name: 'Mistral AI',
    apiBase: 'https://api.mistral.ai/v1',
    apiPath: '/chat/completions',
    apiSpec: 'openai',
    models: ['mistral-tiny', 'mistral-small', 'mistral-medium', 'mistral-large', 'open-mistral-7b'],
    needApiKey: true
  },
  perplexity: {
    name: 'Perplexity',
    apiBase: 'https://api.perplexity.ai',
    apiPath: '/chat/completions',
    apiSpec: 'openai',
    models: ['sonar-small-online', 'sonar-medium-online', 'sonar-large-online'],
    needApiKey: true
  },
  groq: {
    name: 'Groq',
    apiBase: 'https://api.groq.com/openai/v1',
    apiPath: '/chat/completions',
    apiSpec: 'openai',
    models: ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768'],
    needApiKey: true
  },
  minimax: {
    name: 'MiniMax',
    apiBase: 'https://api.minimax.io/v1/text',
    apiPath: '/chatcompletion_v2',
    apiSpec: 'openai',
    models: ['MiniMax-M1', 'MiniMax-Text-01', 'abab6.5s-chat', 'abab6.5-chat'],
    needApiKey: true
  },
  deepseek: {
    name: 'DeepSeek',
    apiBase: 'https://api.deepseek.com/v1',
    apiPath: '/chat/completions',
    apiSpec: 'openai',
    models: ['deepseek-chat', 'deepseek-reasoner'],
    needApiKey: true
  },
  moonshot: {
    name: '月之暗面 (Moonshot)',
    apiBase: 'https://api.moonshot.cn/v1',
    apiPath: '/chat/completions',
    apiSpec: 'openai',
    models: ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'],
    needApiKey: true
  },
  stepfun: {
    name: '阶跃星辰 (StepFun)',
    apiBase: 'https://api.stepfun.com/v1',
    apiPath: '/chat/completions',
    apiSpec: 'openai',
    models: ['step-1v-8k', 'step-1v-32k', 'step-1v-128k'],
    needApiKey: true
  },
  // 本地模型
  ollama: {
    name: 'Ollama (本地)',
    apiBase: 'http://localhost:11434',
    apiPath: '/v1/chat/completions',
    apiSpec: 'openai',
    models: ['llama3', 'llama3.1', 'qwen2', 'mistral', 'codellama', 'phi3'],
    needApiKey: false
  },
  localai: {
    name: 'LocalAI (本地)',
    apiBase: 'http://localhost:8080',
    apiPath: '/v1/chat/completions',
    apiSpec: 'openai',
    models: ['llama-2-7b', 'mistral-7b', 'codellama-7b', 'gpt-4all'],
    needApiKey: false
  },
  lmstudio: {
    name: 'LM Studio (本地)',
    apiBase: 'http://localhost:1234',
    apiPath: '/v1/chat/completions',
    apiSpec: 'openai',
    models: ['llama-3-8b', 'mistral-7b', 'neural-chat', 'starcoder'],
    needApiKey: false
  },
  vllm: {
    name: 'vLLM (本地)',
    apiBase: 'http://localhost:8000',
    apiPath: '/v1/chat/completions',
    apiSpec: 'openai',
    models: ['llama-2-7b', 'llama-2-13b', 'llama-2-70b', 'qwen-14b'],
    needApiKey: false
  },
  // 自定义厂商
  custom: {
    name: '自定义',
    apiBase: '',
    apiPath: '',
    apiSpec: 'openai',
    models: [],
    needApiKey: true,
    isCustom: true
  }
};

// API 规范选项
const API_SPEC_OPTIONS = [
  { value: 'openai', label: 'OpenAI 兼容 (推荐)', description: '标准 OpenAI API 格式' },
  { value: 'anthropic', label: 'Anthropic Claude 兼容', description: 'Claude API 格式' },
  { value: 'gemini', label: 'Google Gemini 兼容', description: 'Gemini API 格式' },
  { value: 'custom', label: '完全自定义', description: '需要手动配置请求/响应格式' },
];

// 厂商选项
const vendorOptions = Object.entries(VENDOR_CONFIGS).map(([value, config]) => ({
  value,
  label: config.name,
  needApiKey: config.needApiKey,
  isCustom: config.isCustom || false
}));

const ModelConfig = () => {
  const [tableData, setTableData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('add');
  const [form] = Form.useForm();
  const [filters, setFilters] = useState({ vendor: null, status: null });
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [availableModels, setAvailableModels] = useState([]);
  const [fetchingModels, setFetchingModels] = useState(false);
  const [fetchError, setFetchError] = useState(null);
  const [editingRecord, setEditingRecord] = useState(null);

  useEffect(() => {
    fetchData();
  }, [filters]);

  // 监听编辑记录变化，设置表单值
  useEffect(() => {
    if (editingRecord && modalVisible) {
      console.log('useEffect 设置表单值:', editingRecord);
      form.setFieldsValue(editingRecord);
      // 验证设置后的值
      setTimeout(() => {
        const currentValues = form.getFieldsValue();
        console.log('useEffect 设置后当前值:', currentValues);
      }, 50);
    }
  }, [editingRecord, modalVisible]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await modelApi.list({
        vendor: filters.vendor,
        status: filters.status
      });
      if (response.code === 200) {
        setTableData(response.data || []);
      }
    } catch (error) {
      message.error('获取模型列表失败');
    } finally {
      setLoading(false);
    }
  };

  const getVendorName = (vendor) => {
    return vendorOptions.find(v => v.value === vendor)?.label || vendor;
  };

  // 厂商选择变化时自动填充默认 API Base
  const handleVendorChange = (vendor) => {
    setSelectedVendor(vendor);
    setAvailableModels([]);
    setFetchError(null);
    const config = VENDOR_CONFIGS[vendor];
    
    if (config && modalType === 'add') {
      // 自动填充 API Base、Path、Spec 和默认模型
      form.setFieldsValue({
        api_base: config.apiBase,
        api_path: config.apiPath,
        api_spec: config.apiSpec,
        model_name: config.models[0] || ''
      });
    }
  };

  const handleAdd = () => {
    setModalType('add');
    setSelectedVendor(null);
    setAvailableModels([]);
    setFetchError(null);
    setEditingRecord(null);
    form.resetFields();
    setModalVisible(true);
    // 设置默认值
    setEditingRecord({ priority: 100 });
  };

  const handleFetchModels = async () => {
    const values = form.getFieldsValue(['vendor', 'api_key', 'api_base']);
    
    if (!values.vendor) {
      message.error('请先选择厂商');
      return;
    }
    
    const needApiKey = VENDOR_CONFIGS[values.vendor]?.needApiKey !== false;
    if (needApiKey && !values.api_key) {
      message.error('请先填写 API Key');
      return;
    }

    setFetchingModels(true);
    setFetchError(null);
    
    try {
      const response = await modelApi.fetchAvailable({
        vendor: values.vendor,
        api_key: values.api_key,
        api_base: values.api_base
      });
      
      if (response.code === 200) {
        setAvailableModels(response.data || []);
        if (response.data && response.data.length > 0) {
          message.success(`成功获取 ${response.data.length} 个模型`);
        } else {
          message.warning('未获取到模型列表');
        }
      } else {
        setFetchError(response.msg || '获取模型列表失败');
        message.error(response.msg || '获取模型列表失败');
      }
    } catch (error) {
      console.error('获取模型失败:', error);
      setFetchError('请求失败，请检查网络或API配置');
      message.error('获取模型列表失败');
    } finally {
      setFetchingModels(false);
    }
  };

  const handleModelSelect = (modelId) => {
    form.setFieldsValue({ model_name: modelId });
  };

  const handleEdit = async (record) => {
    setModalType('edit');
    setSelectedVendor(record.vendor);
    setAvailableModels([]);
    setFetchError(null);
    setEditingRecord(null);
    
    // 先获取数据
    let formData = record;
    try {
      const response = await modelApi.get(record.id);
      if (response.code === 200 && response.data) {
        formData = response.data;
      }
    } catch (error) {
      console.error('获取模型详情失败:', error);
    }
    
    console.log('准备编辑的数据:', formData);
    
    // 先重置表单，然后打开模态框
    form.resetFields();
    setModalVisible(true);
    
    // 设置编辑记录，触发 useEffect
    setEditingRecord(formData);
  };

  const handleDelete = async (id) => {
    try {
      await modelApi.delete(id);
      message.success('删除成功');
      fetchData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleTest = async (id) => {
    try {
      const response = await modelApi.test(id);
      message.success(response.msg || '连通测试成功');
    } catch (error) {
      message.error('连通测试失败');
    }
  };

  const handleStatusChange = async (record) => {
    try {
      if (record.status === 1) {
        await modelApi.disable(record.id);
      } else {
        await modelApi.enable(record.id);
      }
      message.success('状态更新成功');
      fetchData();
    } catch (error) {
      message.error('状态更新失败');
    }
  };

  const handleSave = async () => {
    try {
      await form.validateFields();
      
      // 手动获取所有字段值
      const values = form.getFieldsValue(true);
      console.log('表单原始值:', values);
      
      // 特别处理 priority 字段
      const priorityValue = form.getFieldValue('priority');
      console.log('Priority 字段值:', priorityValue, '类型:', typeof priorityValue);
      
      // 确保 priority 是数字
      const finalValues = {
        ...values,
        priority: Number(priorityValue) || 100
      };
      
      console.log('最终提交的值:', finalValues);
      console.log('最终 priority:', finalValues.priority);
      
      if (modalType === 'add') {
        await modelApi.add(finalValues);
        message.success('添加成功');
      } else {
        await modelApi.update(finalValues.id, finalValues);
        message.success('更新成功');
      }
      setModalVisible(false);
      setEditingRecord(null);
      fetchData();
    } catch (error) {
      console.error('保存失败:', error);
    }
  };

  const columns = [
    {
      title: '厂商',
      dataIndex: 'vendor',
      render: (vendor) => <Tag>{getVendorName(vendor)}</Tag>
    },
    {
      title: '模型名称',
      dataIndex: 'model_name'
    },
    {
      title: 'API Base',
      dataIndex: 'api_base',
      ellipsis: true,
      render: (text) => <span style={{ fontSize: 12 }}>{text || '-'}</span>
    },
    {
      title: 'API Path',
      dataIndex: 'api_path',
      ellipsis: true,
      render: (text) => <span style={{ fontSize: 12, color: '#666' }}>{text || '-'}</span>
    },
    {
      title: '状态',
      dataIndex: 'status',
      render: (status, record) => (
        <Switch
          checked={status === 1}
          onChange={() => handleStatusChange(record)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      )
    },
    {
      title: '连通性',
      dataIndex: 'connect_status',
      render: (status) => (
        status === 1 ?
          <CheckCircleFilled style={{ color: '#67C23A', fontSize: 18 }} /> :
          <CloseCircleFilled style={{ color: '#F56C6C', fontSize: 18 }} />
      )
    },
    {
      title: '优先级',
      dataIndex: 'priority'
    },
    {
      title: '操作',
      render: (_, record) => (
        <Space>
          <Tooltip title="测试连通">
            <Button
              type="text"
              icon={<ApiOutlined />}
              onClick={() => handleTest(record.id)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定删除此模型?"
            onConfirm={() => handleDelete(record.id)}
          >
            <Tooltip title="删除">
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 检查是否为本地模型（不需要 API Key）
  const isLocalModel = selectedVendor && VENDOR_CONFIGS[selectedVendor]?.needApiKey === false;

  return (
    <div>
      <Card className="filter-card">
        <Space>
          <Select
            placeholder="全部厂商"
            allowClear
            style={{ width: 150 }}
            options={vendorOptions}
            value={filters.vendor}
            onChange={(value) => setFilters({ ...filters, vendor: value })}
          />
          <Select
            placeholder="全部状态"
            allowClear
            style={{ width: 120 }}
            options={[
              { label: '启用', value: 1 },
              { label: '禁用', value: 0 }
            ]}
            value={filters.status}
            onChange={(value) => setFilters({ ...filters, status: value })}
          />
          <Button type="primary" icon={<SearchOutlined />} onClick={fetchData}>
            刷新
          </Button>
        </Space>
      </Card>

      <Card
        title="模型配置列表"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            添加模型
          </Button>
        }
        className="table-card"
      >
        <Table
          dataSource={tableData}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={modalType === 'add' ? '添加模型' : '编辑模型'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => {
          setModalVisible(false);
          setEditingRecord(null);
        }}
        width={650}
        destroyOnClose={true}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="id" hidden>
            <Input />
          </Form.Item>
          
          <Form.Item
            name="vendor"
            label="厂商"
            rules={[{ required: true, message: '请选择厂商' }]}
          >
            <Select 
              options={vendorOptions} 
              placeholder="请选择厂商"
              onChange={handleVendorChange}
            />
          </Form.Item>
          
          <Form.Item label="获取可用模型" style={{ marginBottom: 8 }}>
            <Button 
              type="default" 
              icon={<CloudDownloadOutlined />}
              onClick={handleFetchModels}
              loading={fetchingModels}
              disabled={!selectedVendor}
              style={{ width: '100%' }}
            >
              {fetchingModels ? '获取中...' : '获取可用模型列表'}
            </Button>
          </Form.Item>

          {fetchError && (
            <Alert
              message={fetchError}
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {availableModels.length > 0 && (
            <Form.Item label="选择模型" style={{ marginBottom: 16 }}>
              <Select
                placeholder="点击选择模型"
                style={{ width: '100%' }}
                onChange={handleModelSelect}
                optionLabelProp="label"
              >
                {availableModels.map(model => (
                  <Select.Option 
                    key={model.id} 
                    value={model.id}
                    label={model.name || model.id}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontWeight: 500 }}>{model.name || model.id}</span>
                      {model.description && (
                        <span style={{ fontSize: 12, color: '#999' }}>{model.description}</span>
                      )}
                    </div>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          )}
          
          <Form.Item
            name="model_name"
            label="模型名称"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="请输入或选择模型名称" />
          </Form.Item>
          
          <Form.Item
            name="api_base"
            label="API Base"
            tooltip={selectedVendor ? `默认值: ${VENDOR_CONFIGS[selectedVendor]?.apiBase || ''}` : ''}
            rules={[{ required: true, message: '请输入 API Base 地址' }]}
          >
            <Input placeholder={selectedVendor ? VENDOR_CONFIGS[selectedVendor]?.apiBase : 'https://api.example.com'} />
          </Form.Item>
          
          <Form.Item
            name="api_path"
            label="API Path"
            tooltip={selectedVendor ? `默认值: ${VENDOR_CONFIGS[selectedVendor]?.apiPath || ''}` : '请求路径，如 /chat/completions'}
            rules={[{ required: true, message: '请输入 API Path' }]}
          >
            <Input placeholder={selectedVendor ? VENDOR_CONFIGS[selectedVendor]?.apiPath : '/chat/completions'} />
          </Form.Item>
          
          <Form.Item
            name="api_spec"
            label="API 规范"
            tooltip="选择 API 规范类型，不同规范会影响请求/响应的参数映射"
            rules={[{ required: true, message: '请选择 API 规范' }]}
          >
            <Select
              placeholder="选择 API 规范"
              options={API_SPEC_OPTIONS}
            />
          </Form.Item>
          
          <Form.Item
            name="api_key"
            label="API Key"
            tooltip={isLocalModel ? '本地模型通常不需要 API Key' : '请输入对应的 API Key'}
            rules={[
              { 
                required: !isLocalModel, 
                message: isLocalModel ? '本地模型可留空' : '请输入 API Key' 
              }
            ]}
          >
            <Input.Password 
              placeholder={isLocalModel ? '本地模型可留空' : '请输入 API Key'} 
            />
          </Form.Item>
          
          <Form.Item 
            name="priority" 
            label="优先级"
          >
            <Input 
              type="number" 
              min={1} 
              max={999} 
              style={{ width: '100%' }} 
              placeholder="请输入优先级"
            />
          </Form.Item>
          <div className="form-tip" style={{ marginTop: -20, marginBottom: 16, color: '#999', fontSize: 12 }}>
            数字越小优先级越高
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default ModelConfig;
