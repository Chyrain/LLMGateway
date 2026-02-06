import React, { useState, useEffect } from 'react';
import {
  Table, Card, Button, Tag, Space, Input, Select, Modal, Form,
  InputNumber, Switch, message, Popconfirm, Tooltip
} from 'antd';
import {
  PlusOutlined, ApiOutlined, EditOutlined,
  DeleteOutlined, SearchOutlined, CheckCircleFilled,
  CloseCircleFilled
} from '@ant-design/icons';
import { modelApi } from '../services/api';

// 厂商默认配置（API Base 和模型列表）
const VENDOR_CONFIGS = {
  openai: {
    name: 'OpenAI',
    apiBase: 'https://api.openai.com/v1',
    models: ['gpt-3.5-turbo', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4'],
    needApiKey: true
  },
  qwen: {
    name: '通义千问',
    apiBase: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    models: ['qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen2-72b-instruct'],
    needApiKey: true
  },
  zhipu: {
    name: '智谱清言',
    apiBase: 'https://api.bigmodel.cn/api/llm/v3.5',
    models: ['glm-3-turbo', 'glm-4', 'glm-4v', 'glm-4-plus'],
    needApiKey: true
  },
  spark: {
    name: '讯飞星火',
    apiBase: 'https://spark-api.xf-yun.com/v3.1/chat',
    models: ['spark-v3.1', 'spark-v3.5'],
    needApiKey: true
  },
  doubao: {
    name: '字节豆包',
    apiBase: 'https://ark.cn-beijing.volces.com/api/v3',
    models: ['Doubao-pro-32k', 'Doubao-pro-128k'],
    needApiKey: true
  },
  claude: {
    name: 'Claude',
    apiBase: 'https://api.anthropic.com/v1',
    models: ['claude-sonnet-4-20250514', 'claude-haiku-3-20250514', 'claude-opus-4-20250514'],
    needApiKey: true
  },
  gemini: {
    name: 'Google Gemini',
    apiBase: 'https://generativelanguage.googleapis.com/v1beta',
    models: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
    needApiKey: true
  },
  mistral: {
    name: 'Mistral AI',
    apiBase: 'https://api.mistral.ai/v1',
    models: ['mistral-tiny', 'mistral-small', 'mistral-medium', 'mistral-large', 'open-mistral-7b'],
    needApiKey: true
  },
  groq: {
    name: 'Groq (Llama3)',
    apiBase: 'https://api.groq.com/openai/v1',
    models: ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768'],
    needApiKey: true
  },
  // 本地模型
  ollama: {
    name: 'Ollama (本地)',
    apiBase: 'http://localhost:11434/v1',
    models: ['llama3', 'llama3.1', 'qwen2', 'mistral', 'codellama', 'phi3'],
    needApiKey: false
  },
  localai: {
    name: 'LocalAI (本地)',
    apiBase: 'http://localhost:8080/v1',
    models: ['llama-2-7b', 'mistral-7b', 'codellama-7b', 'gpt-4all'],
    needApiKey: false
  },
  lmstudio: {
    name: 'LM Studio (本地)',
    apiBase: 'http://localhost:1234/v1',
    models: ['llama-3-8b', 'mistral-7b', 'neural-chat', 'starcoder'],
    needApiKey: false
  },
  vllm: {
    name: 'vLLM (本地)',
    apiBase: 'http://localhost:8000/v1',
    models: ['llama-2-7b', 'llama-2-13b', 'llama-2-70b', 'qwen-14b'],
    needApiKey: false
  }
};

// 厂商选项
const vendorOptions = Object.entries(VENDOR_CONFIGS).map(([value, config]) => ({
  value,
  label: config.name,
  needApiKey: config.needApiKey
}));

const ModelConfig = () => {
  const [tableData, setTableData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('add');
  const [form] = Form.useForm();
  const [filters, setFilters] = useState({ vendor: null, status: null });
  const [selectedVendor, setSelectedVendor] = useState(null);

  useEffect(() => {
    fetchData();
  }, [filters]);

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
    const config = VENDOR_CONFIGS[vendor];
    
    if (config && modalType === 'add') {
      // 自动填充 API Base 和默认模型
      form.setFieldsValue({
        api_base: config.apiBase,
        model_name: config.models[0]
      });
    }
  };

  const handleAdd = () => {
    setModalType('add');
    setSelectedVendor(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setModalType('edit');
    setSelectedVendor(record.vendor);
    form.setFieldsValue(record);
    setModalVisible(true);
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
      const values = await form.validateFields();
      if (modalType === 'add') {
        await modelApi.add(values);
        message.success('添加成功');
      } else {
        await modelApi.update(values.id, values);
        message.success('更新成功');
      }
      setModalVisible(false);
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
      ellipsis: true
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
        onCancel={() => setModalVisible(false)}
        width={650}
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
          
          <Form.Item
            name="model_name"
            label="模型名称"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="请输入模型名称" />
          </Form.Item>
          
          <Form.Item
            name="api_base"
            label="API Base"
            tooltip={selectedVendor ? `默认值: ${VENDOR_CONFIGS[selectedVendor]?.apiBase || ''}` : ''}
            rules={[{ required: true, message: '请输入 API Base 地址' }]}
          >
            <Input placeholder={selectedVendor ? VENDOR_CONFIGS[selectedVendor]?.apiBase : 'https://api.example.com/v1'} />
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
          
          <Form.Item name="priority" label="优先级" initialValue={100}>
            <InputNumber min={1} max={999} style={{ width: '100%' }} />
            <span className="form-tip" style={{ marginLeft: 8, color: '#999' }}>
              数字越小优先级越高
            </span>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ModelConfig;
