import React, { useState, useEffect } from 'react';
import { Card, Form, Input, InputNumber, Button, Switch, message, Divider, Space, Row, Col } from 'antd';
import { SaveOutlined, SyncOutlined, SafetyOutlined } from '@ant-design/icons';
import { configApi } from '../services/api';

const SystemConfig = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [gatewayForm] = Form.useForm();

  const gatewayConfig = {
    port: 8080,
    api_key: ''
  };

  const alertConfig = {
    threshold: 80
  };

  const commonConfig = {
    log_retention: 30,
    refresh_interval: 60
  };

  const handleSaveGateway = async () => {
    try {
      const values = gatewayForm.getFieldsValue();
      await configApi.set({ key: 'gateway_port', value: values.port.toString() });
      await configApi.set({ key: 'gateway_api_key', value: values.api_key });
      message.success('网关配置已保存');
    } catch (error) {
      message.error('保存失败');
    }
  };

  const handleSaveAlert = async () => {
    try {
      const values = form.getFieldsValue();
      await configApi.set({ key: 'alert_threshold', value: values.threshold.toString() });
      message.success('告警配置已保存');
    } catch (error) {
      message.error('保存失败');
    }
  };

  const handleSaveCommon = async () => {
    try {
      const values = form.getFieldsValue();
      await configApi.set({ key: 'log_retention', value: values.log_retention.toString() });
      await configApi.set({ key: 'refresh_interval', value: values.refresh_interval.toString() });
      message.success('通用配置已保存');
    } catch (error) {
      message.error('保存失败');
    }
  };

  const handleResetEncryptKey = async () => {
    try {
      await configApi.resetEncryptKey();
      message.success('加密密钥已重置');
    } catch (error) {
      message.error('重置失败');
    }
  };

  return (
    <div>
      <Row gutter={[20, 20]}>
        <Col span={12}>
          <Card title="网关配置" extra={
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveGateway}>
              保存
            </Button>
          }>
            <Form form={gatewayForm} layout="vertical" initialValues={gatewayConfig}>
              <Form.Item name="port" label="网关端口">
                <InputNumber min={1} max={65535} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="api_key" label="API Key">
                <Input.Password placeholder="留空保持原值" />
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="告警配置" extra={
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveAlert}>
              保存
            </Button>
          }>
            <Form form={form} layout="vertical" initialValues={alertConfig}>
              <Form.Item name="threshold" label="额度告警阈值 (%)">
                <InputNumber min={0} max={100} style={{ width: '100%' }} />
                <div className="form-tip">当模型使用额度达到此百分比时触发告警</div>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>

      <Row gutter={[20, 20]} style={{ marginTop: 20 }}>
        <Col span={12}>
          <Card title="通用配置" extra={
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveCommon}>
              保存
            </Button>
          }>
            <Form layout="vertical" initialValues={commonConfig}>
              <Form.Item name="log_retention" label="日志保留天数">
                <InputNumber min={1} max={365} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="refresh_interval" label="刷新间隔 (秒)">
                <InputNumber min={10} max={3600} style={{ width: '100%' }} />
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="安全设置">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <strong>加密密钥</strong>
                <div className="form-tip">用于加密敏感配置数据</div>
              </div>
              <Button
                type="primary"
                danger
                icon={<SafetyOutlined />}
                onClick={handleResetEncryptKey}
              >
                重置加密密钥
              </Button>
              <div className="form-tip">警告：重置后需要重新配置所有敏感信息</div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default SystemConfig;
