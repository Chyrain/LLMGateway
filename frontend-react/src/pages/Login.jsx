import React, { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';

const Login = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const response = await authApi.login(values.username, values.password);
      
      if (response.code === 200 && response.data) {
        const token = response.data.access_token;
        localStorage.setItem('token', token);
        localStorage.setItem('username', response.data.username || values.username);
        
        // 检查是否是首次登录
        if (!localStorage.getItem('llmgateway_visited')) {
          localStorage.setItem('llmgateway_visited', 'true');
          message.success('登录成功');
          navigate('/welcome');
        } else {
          message.success('登录成功');
          navigate('/');
        }
      } else {
        message.error(response.msg || '登录失败');
      }
    } catch (error) {
      console.error('登录失败:', error);
      message.error(error.response?.data?.detail || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <div className="logo">🤖</div>
          <h1>灵模网关</h1>
          <p>LLM Free Quota Gateway</p>
        </div>
        <Form
          name="login"
          onFinish={onFinish}
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, max: 20, message: '用户名长度在 3-20 个字符' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
            />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 4, max: 20, message: '密码长度在 4-20 个字符' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              className="login-btn"
            >
              登 录
            </Button>
          </Form.Item>
        </Form>
        <div className="login-footer">
          <p>默认管理员: admin / admin123</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
