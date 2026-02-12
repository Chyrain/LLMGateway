import React, { useState, useEffect } from 'react';
import { Card, Descriptions, Tag, Button, Input, Space, message, Switch, Divider, Alert, Steps, List, Tabs, Modal, Spin } from 'antd';
import { CopyOutlined, CheckCircleOutlined, PlayCircleOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons';
import { modelApi, configApi } from '../services/api';

const AgentGuide = () => {
  const [modelList, setModelList] = useState([]);
  const [gatewayApiKey, setGatewayApiKey] = useState('');
  const [copied, setCopied] = useState(false);
  const [testModalVisible, setTestModalVisible] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);
  const [testMessage, setTestMessage] = useState('');
  const [testResponse, setTestResponse] = useState('');
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    fetchModels();
    fetchGatewayKey();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await modelApi.list({ status: 1 });
      if (response.code === 200) {
        setModelList(response.data || []);
      }
    } catch (error) {
      console.error('获取模型列表失败:', error);
    }
  };

  const fetchGatewayKey = async () => {
    try {
      const response = await configApi.get('gateway_api_key');
      if (response.code === 200) {
        setGatewayApiKey(response.data?.config_value || '');
      }
    } catch (error) {
      console.error('获取网关配置失败:', error);
    }
  };

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleTestModel = (model) => {
    setSelectedModel(model);
    setTestModalVisible(true);
    setTestMessage('');
    setTestResponse('');
  };

  const handleSendTestMessage = async () => {
    if (!testMessage.trim()) {
      message.warning('请输入测试消息');
      return;
    }

    setTesting(true);
    setTestResponse('');

    try {
      const response = await fetch('http://localhost:8080/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${gatewayApiKey || 'gtw_admin123'}`
        },
        body: JSON.stringify({
          model: selectedModel.model_name,
          messages: [{ role: 'user', content: testMessage }]
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `请求失败: ${response.status}`);
      }

      const data = await response.json();
      const content = data.choices?.[0]?.message?.content || '无响应内容';
      setTestResponse(content);
    } catch (error) {
      console.error('测试失败:', error);
      setTestResponse(`请求失败: ${error.message}`);
    } finally {
      setTesting(false);
    }
  };

  const curlExample = `curl -X POST "http://localhost:8080/v1/chat/completions" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer ${gatewayApiKey || 'YOUR_API_KEY'}" \\
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "你好"}]
  }'`;

  const pythonExample = `import requests

url = "http://localhost:8080/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer ${gatewayApiKey || 'YOUR_API_KEY'}"
}
data = {
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "你好"}]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())`;

  const openaiCompatibleExample = `from openai import OpenAI

client = OpenAI(
    api_key="${gatewayApiKey || 'YOUR_API_KEY'}",
    base_url="http://localhost:8080/v1"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "你好"}]
)

print(response.choices[0].message.content)`;

  const langchainExample = `from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key="${gatewayApiKey || 'YOUR_API_KEY'}",
    openai_api_base="http://localhost:8080/v1"
)

messages = [HumanMessage(content="你好")]
response = llm.invoke(messages)
print(response.content)`;

  const CodeBlock = ({ title, code }) => (
    <Card size="small" title={title} style={{ marginBottom: 16 }}>
      <div style={{ position: 'relative' }}>
        <pre style={{
          background: '#f5f5f5',
          padding: 16,
          borderRadius: 8,
          overflow: 'auto',
          fontSize: 12,
          maxHeight: 300
        }}>
          {code}
        </pre>
        <Button
          type="primary"
          size="small"
          icon={<CopyOutlined />}
          onClick={() => handleCopy(code)}
          style={{ position: 'absolute', top: 8, right: 8 }}
        >
          {copied ? '已复制!' : '复制'}
        </Button>
      </div>
    </Card>
  );

  return (
    <div>
      <Alert
        message="Agent 工具适配"
        description="灵模网关提供 OpenAI 兼容的 API 接口，可以直接对接各种 Agent 框架和工具。"
        type="info"
        showIcon
        style={{ marginBottom: 20 }}
      />

      <Steps
        current={0}
        items={[
          { title: '获取 API Key', description: '从系统配置获取' },
          { title: '配置 Endpoint', description: '使用网关地址' },
          { title: '集成 Agent', description: '对接各种框架' }
        ]}
        style={{ marginBottom: 20 }}
      />

      <Card title="1. 获取网关 API Key" style={{ marginBottom: 20 }}>
        <Descriptions>
          <Descriptions.Item label="API Key">
            {gatewayApiKey ? (
              <Space>
                <Input.Password
                  value={gatewayApiKey}
                  style={{ width: 400 }}
                  readOnly
                />
                <Button 
                  type="primary" 
                  icon={<CopyOutlined />}
                  onClick={() => handleCopy(gatewayApiKey)}
                >
                  复制
                </Button>
              </Space>
            ) : (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Alert
                  message="API Key 未设置"
                  description="请前往「系统配置」-「网关配置」中设置 API Key"
                  type="warning"
                  showIcon
                  action={
                    <Button 
                      type="primary" 
                      size="small"
                      onClick={() => window.location.href = '/#/system-config'}
                    >
                      去设置
                    </Button>
                  }
                />
                <div style={{ color: '#999', fontSize: 12 }}>
                  默认网关 API Key: gtw_admin123
                </div>
              </Space>
            )}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="2. API 调用示例" style={{ marginBottom: 20 }}>
        <Tabs
          items={[
            {
              key: 'curl',
              label: 'cURL',
              children: <CodeBlock title="cURL 调用示例" code={curlExample} />
            },
            {
              key: 'python',
              label: 'Python Requests',
              children: <CodeBlock title="Python Requests 示例" code={pythonExample} />
            },
            {
              key: 'openai',
              label: 'OpenAI Python',
              children: <CodeBlock title="OpenAI Python SDK 示例" code={openaiCompatibleExample} />
            },
            {
              key: 'langchain',
              label: 'LangChain',
              children: <CodeBlock title="LangChain 示例" code={langchainExample} />
            }
          ]}
        />
      </Card>

      <Card title="3. 已配置模型" style={{ marginBottom: 20 }}>
        <List
          grid={{ gutter: 16, column: 3 }}
          dataSource={modelList}
          renderItem={(item) => (
            <List.Item>
              <Card 
                size="small" 
                hoverable 
                onClick={() => handleTestModel(item)}
                style={{ cursor: 'pointer', width: '100%' }}
                bodyStyle={{ padding: '12px' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Space>
                    <Tag color="blue">{item.vendor}</Tag>
                    <span style={{ fontWeight: 500 }}>{item.model_name}</span>
                  </Space>
                  <Button 
                    type="primary" 
                    size="small" 
                    icon={<PlayCircleOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTestModel(item);
                    }}
                  >
                    测试
                  </Button>
                </div>
              </Card>
            </List.Item>
          )}
          locale={{ emptyText: '暂无可用模型，请先添加模型配置' }}
        />
      </Card>

      {/* 测试对话弹窗 */}
      <Modal
        title={
          <Space>
            <RobotOutlined />
            <span>测试模型: {selectedModel?.model_name}</span>
          </Space>
        }
        open={testModalVisible}
        onCancel={() => setTestModalVisible(false)}
        width={700}
        footer={[
          <Button key="close" onClick={() => setTestModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 8, color: '#666' }}>
            <UserOutlined /> 发送消息:
          </div>
          <Input.TextArea
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            placeholder="输入测试消息，例如：你好"
            rows={3}
            disabled={testing}
          />
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleSendTestMessage}
            loading={testing}
            disabled={!testMessage.trim()}
            style={{ marginTop: 8 }}
          >
            发送测试
          </Button>
        </div>

        {testResponse && (
          <div>
            <div style={{ marginBottom: 8, color: '#666' }}>
              <RobotOutlined /> 模型回复:
            </div>
            <Card 
              size="small" 
              style={{ background: '#f6ffed', border: '1px solid #b7eb8f' }}
            >
              <pre style={{ 
                margin: 0, 
                whiteSpace: 'pre-wrap', 
                wordWrap: 'break-word',
                fontFamily: 'inherit'
              }}>
                {testResponse}
              </pre>
            </Card>
          </div>
        )}

        {testing && !testResponse && (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16, color: '#999' }}>正在等待模型响应...</div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AgentGuide;
