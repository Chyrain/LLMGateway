import React, { useState, useEffect } from 'react';
import { Card, Form, Input, InputNumber, Button, message, Row, Col } from 'antd';
import { SaveOutlined, SafetyOutlined } from '@ant-design/icons';
import { configApi } from '../services/api';

const SystemConfig = () => {
  const [gatewayForm] = Form.useForm();
  const [alertForm] = Form.useForm();
  const [commonForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [thresholdValue, setThresholdValue] = useState(80);

  // 默认配置值
  const defaultConfig = {
    gateway_port: 8080,
    gateway_api_key: '',
    alert_threshold: 80,
    log_retention: 30,
    refresh_interval: 60
  };

  // 组件挂载时加载配置
  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    setLoading(true);
    try {
      const response = await configApi.list();
      console.log('加载配置:', response);
      
      if (response.code === 200 && response.data) {
        const data = response.data;
        
        // 设置网关配置
        gatewayForm.setFieldsValue({
          port: parseInt(data.gateway_port) || defaultConfig.gateway_port,
          api_key: data.gateway_api_key || defaultConfig.gateway_api_key
        });
        
        // 设置告警配置
        const alertThreshold = parseInt(data.alert_threshold) || defaultConfig.alert_threshold;
        alertForm.setFieldsValue({
          threshold: alertThreshold
        });
        setThresholdValue(alertThreshold);
        
        // 设置通用配置
        commonForm.setFieldsValue({
          log_retention: parseInt(data.log_retention) || defaultConfig.log_retention,
          refresh_interval: parseInt(data.refresh_interval) || defaultConfig.refresh_interval
        });
        
        console.log('配置加载完成');
      }
    } catch (error) {
      console.error('加载配置失败:', error);
      message.error('加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveGateway = async () => {
    try {
      const values = gatewayForm.getFieldsValue();
      console.log('保存网关配置:', values);
      
      await configApi.set({ key: 'gateway_port', value: values.port.toString() });
      if (values.api_key) {
        await configApi.set({ key: 'gateway_api_key', value: values.api_key });
      }
      message.success('网关配置已保存');
      loadConfigs(); // 重新加载配置
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存失败');
    }
  };

  const handleSaveAlert = async () => {
    try {
      console.log('保存告警配置，当前值:', thresholdValue);
      
      await configApi.set({ key: 'alert_threshold', value: String(thresholdValue) });
      message.success('告警配置已保存');
      loadConfigs();
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存失败');
    }
  };

  const handleSaveCommon = async () => {
    try {
      const values = commonForm.getFieldsValue();
      console.log('保存通用配置:', values);
      
      await configApi.set({ key: 'log_retention', value: values.log_retention.toString() });
      await configApi.set({ key: 'refresh_interval', value: values.refresh_interval.toString() });
      message.success('通用配置已保存');
      loadConfigs(); // 重新加载配置
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存失败');
    }
  };

  const handleResetEncryptKey = async () => {
    try {
      await configApi.resetEncryptKey();
      message.success('加密密钥已重置');
    } catch (error) {
      console.error('重置失败:', error);
      message.error('重置失败');
    }
  };

  return (
    <div>
      <Row gutter={[20, 20]}>
        <Col span={12}>
          <Card title="网关配置" extra={
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveGateway} loading={loading}>
              保存
            </Button>
          }>
            <Form form={gatewayForm} layout="vertical">
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
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveAlert} loading={loading}>
              保存
            </Button>
          }>
            <Form form={alertForm} layout="vertical">
              <Form.Item label="额度告警阈值 (%)">
                <InputNumber 
                  min={0} 
                  max={100} 
                  style={{ width: '100%' }}
                  value={thresholdValue}
                  onChange={(value) => {
                    console.log('阈值变化:', value);
                    setThresholdValue(value || 0);
                  }}
                />
                <div className="form-tip">当模型使用额度达到此百分比时触发告警</div>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>

      <Row gutter={[20, 20]} style={{ marginTop: 20 }}>
        <Col span={12}>
          <Card title="通用配置" extra={
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveCommon} loading={loading}>
              保存
            </Button>
          }>
            <Form form={commonForm} layout="vertical">
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
            <div style={{ marginBottom: 16 }}>
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
            <div className="form-tip" style={{ marginTop: 8 }}>警告：重置后需要重新配置所有敏感信息</div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default SystemConfig;
