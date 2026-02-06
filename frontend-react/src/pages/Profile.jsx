import React, { useState } from 'react';
import { Card, Descriptions, Avatar, Space, Tag, message } from 'antd';
import { UserOutlined, MailOutlined, PhoneOutlined, CalendarOutlined } from '@ant-design/icons';

const Profile = () => {
  const [profile] = useState({
    username: localStorage.getItem('username') || 'admin',
    role: '管理员',
    email: 'admin@example.com',
    phone: '13800138000',
    createdAt: '2024-01-01 00:00:00'
  });

  return (
    <Card title="个人中心">
      <div style={{ display: 'flex', gap: 40, alignItems: 'flex-start' }}>
        <div style={{ textAlign: 'center' }}>
          <Avatar
            size={120}
            src="https://api.dicebear.com/7.x/avataaars/svg?seed=admin"
            icon={<UserOutlined />}
          />
          <div style={{ marginTop: 16 }}>
            <Tag color="blue">{profile.role}</Tag>
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <Descriptions column={2}>
            <Descriptions.Item label="用户名">
              <Space>
                <UserOutlined />
                {profile.username}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="邮箱">
              <Space>
                <MailOutlined />
                {profile.email}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="手机号">
              <Space>
                <PhoneOutlined />
                {profile.phone}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              <Space>
                <CalendarOutlined />
                {profile.createdAt}
              </Space>
            </Descriptions.Item>
          </Descriptions>
        </div>
      </div>
    </Card>
  );
};

export default Profile;
