import React from 'react';
import { Button, Card, Row, Col, Space } from 'antd';
import {
  CheckCircleOutlined,
  ApiOutlined,
  BarChartOutlined,
  BellOutlined,
  SafetyOutlined,
  RocketOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const Welcome = () => {
  const navigate = useNavigate();

  const features = [
    { icon: <ApiOutlined />, title: '多模型支持', desc: 'OpenAI、Claude、Qwen等主流模型' },
    { icon: <BarChartOutlined />, title: '额度监控', desc: '实时监控各模型使用额度' },
    { icon: <RocketOutlined />, title: '自动切换', desc: '额度耗尽自动切换' },
    { icon: <BellOutlined />, title: '通知预警', desc: '及时提醒额度状态' },
    { icon: <SafetyOutlined />, title: '安全可靠', desc: 'API Key 加密存储' }
  ];

  return (
    <div className="welcome-container">
      <div className="logo">🤖</div>
      <h1>欢迎使用灵模网关</h1>
      <p>免费 LLM 模型聚合网关，多模型自动切换、额度监控、请求日志</p>
      
      <Row gutter={[24, 24]} style={{ maxWidth: 900, width: '100%', marginBottom: 40 }}>
        {features.map((feature, index) => (
          <Col xs={24} sm={12} md={8} key={index}>
            <Card
              bordered={false}
              style={{
                background: 'rgba(255,255,255,0.1)',
                backdropFilter: 'blur(10px)'
              }}
            >
              <Space direction="vertical" align="center" style={{ width: '100%' }}>
                <div style={{ fontSize: 40, color: '#4facfe' }}>
                  {feature.icon}
                </div>
                <div style={{ fontWeight: 600 }}>{feature.title}</div>
                <div style={{ fontSize: 13, opacity: 0.8 }}>
                  {feature.desc}
                </div>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
      
      <Button
        type="primary"
        size="large"
        onClick={() => navigate('/')}
        icon={<CheckCircleOutlined />}
      >
        开始使用
      </Button>
    </div>
  );
};

export default Welcome;
