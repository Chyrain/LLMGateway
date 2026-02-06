import React, { useState } from 'react';
import { Card, Form, Input, Button, message } from 'antd';
import { LockOutlined, SaveOutlined } from '@ant-design/icons';
import { authApi } from '../services/api';
import { useNavigate } from 'react-router-dom';

const ChangePassword = () => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const onFinish = async (values) => {
    if (values.new_password !== values.confirm_password) {
      message.error('两次输入的密码不一致');
      return;
    }

    setLoading(true);
    try {
      await authApi.changePassword(values.old_password, values.new_password);
      message.success('密码修改成功');
      form.resetFields();
      // 跳转到登录页
      setTimeout(() => {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        navigate('/login');
      }, 1500);
    } catch (error) {
      console.error('修改密码失败:', error);
      message.error(error.response?.data?.detail || '修改密码失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="修改密码" style={{ maxWidth: 500, margin: '0 auto' }}>
      <Form
        form={form}
        name="changePassword"
        onFinish={onFinish}
        layout="vertical"
      >
        <Form.Item
          name="old_password"
          label="当前密码"
          rules={[{ required: true, message: '请输入当前密码' }]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="请输入当前密码"
          />
        </Form.Item>
        <Form.Item
          name="new_password"
          label="新密码"
          rules={[
            { required: true, message: '请输入新密码' },
            { min: 4, message: '密码长度至少4位' },
            { max: 20, message: '密码长度最多20位' }
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="请输入新密码"
          />
        </Form.Item>
        <Form.Item
          name="confirm_password"
          label="确认新密码"
          dependencies={['new_password']}
          rules={[
            { required: true, message: '请确认新密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('new_password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('两次输入的密码不一致'));
              }
            })
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="请再次输入新密码"
          />
        </Form.Item>
        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            icon={<SaveOutlined />}
            block
          >
            保存修改
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default ChangePassword;
