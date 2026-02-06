import React, { useState, useEffect } from 'react';
import { Card, Descriptions, Tag, Button, Input, Space, message, Switch, Divider, Alert, Steps, List, Tabs } from 'antd';
import { CopyOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { modelApi, configApi } from '../services/api';

const AgentGuide = () => {
  const [modelList, setModelList] = useState([]);
  const [gatewayApiKey, setGatewayApiKey] = useState('');
  const [copied, setCopied] = useState(false);

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
            <Input.Password
              value={gatewayApiKey}
              placeholder="请在系统配置中设置"
              style={{ width: 400 }}
              readOnly
            />
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

      <Card title="3. 已配置模型">
        <List
          grid={{ gutter: 16, column: 3 }}
          dataSource={modelList}
          renderItem={(item) => (
            <List.Item>
              <Tag color="blue">{item.vendor}</Tag>
              <Tag>{item.model_name}</Tag>
            </List.Item>
          )}
          locale={{ emptyText: '暂无可用模型，请先添加模型配置' }}
        />
      </Card>
    </div>
  );
};

export default AgentGuide;
