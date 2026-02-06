import React, { useState, useEffect, createContext, useContext } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import {
  Layout,
  Menu,
  Avatar,
  Dropdown,
  Badge,
  Space,
  Button,
  message
} from 'antd';
import {
  DashboardOutlined,
  SettingOutlined,
  PieChartOutlined,
  ToolOutlined,
  FileTextOutlined,
  RobotOutlined,
  BellOutlined,
  UserOutlined,
  LockOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons';
import { authApi, notificationApi } from './services/api';
import Login from './pages/Login';
import Welcome from './pages/Welcome';
import Dashboard from './pages/Dashboard';
import ModelConfig from './pages/ModelConfig';
import QuotaMonitor from './pages/QuotaMonitor';
import SystemConfig from './pages/SystemConfig';
import Logs from './pages/Logs';
import AgentGuide from './pages/AgentGuide';
import Profile from './pages/Profile';
import ChangePassword from './pages/ChangePassword';

const { Header, Sider, Content } = Layout;

// 用户上下文
export const UserContext = createContext(null);

// 主布局组件
const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [username, setUsername] = useState('管理员');
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      const savedUsername = localStorage.getItem('username') || '管理员';
      setUsername(savedUsername);
      fetchUnreadCount();
    }
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const res = await notificationApi.unreadCount();
      if (res.code === 200) {
        setUnreadCount(res.data?.count || 0);
      }
    } catch (error) {
      console.error('获取未读通知失败:', error);
    }
  };

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表盘'
    },
    {
      key: '/models',
      icon: <SettingOutlined />,
      label: '模型配置'
    },
    {
      key: '/quota',
      icon: <PieChartOutlined />,
      label: '额度监控'
    },
    {
      key: '/config',
      icon: <ToolOutlined />,
      label: '系统配置'
    },
    {
      key: '/logs',
      icon: <FileTextOutlined />,
      label: '日志管理'
    },
    {
      key: '/agent',
      icon: <RobotOutlined />,
      label: 'Agent适配'
    }
  ];

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心'
    },
    {
      key: 'password',
      icon: <LockOutlined />,
      label: '修改密码'
    },
    {
      type: 'divider'
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录'
    }
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  const handleUserMenuClick = ({ key }) => {
    if (key === 'profile') {
      navigate('/profile');
    } else if (key === 'password') {
      navigate('/change-password');
    } else if (key === 'logout') {
      handleLogout();
    }
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      // 忽略退出错误
    }
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    message.success('已退出登录');
    navigate('/login');
  };

  const getPageTitle = () => {
    const titles = {
      '/': '仪表盘',
      '/models': '模型配置',
      '/quota': '额度监控',
      '/config': '系统配置',
      '/logs': '日志管理',
      '/agent': 'Agent工具适配',
      '/profile': '个人中心',
      '/change-password': '修改密码'
    };
    return titles[location.pathname] || '仪表盘';
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          background: 'linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)'
        }}
      >
        <div style={{
          height: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: collapsed ? 14 : 18,
          fontWeight: 'bold',
          background: 'rgba(255,255,255,0.05)'
        }}>
          {collapsed ? '🤖' : '🤖 灵模网关'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ background: 'transparent', borderRight: 0 }}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 220, transition: 'margin 0.2s' }}>
        <Header style={{
          padding: '0 20px',
          background: '#fff',
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <Space>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
            />
            <span style={{ fontSize: 16, fontWeight: 500 }}>
              {getPageTitle()}
            </span>
          </Space>
          <Space size={20}>
            <Badge count={unreadCount} size="small">
              <Button type="text" icon={<BellOutlined style={{ fontSize: 18 }} />} />
            </Badge>
            <Dropdown
              menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
              trigger={['click']}
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar
                  src="https://api.dicebear.com/7.x/avataaars/svg?seed=admin"
                  size={32}
                />
                <span>{username}</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{
          margin: 20,
          padding: 20,
          background: '#f5f7fa',
          minHeight: 'calc(100vh - 100px)',
          borderRadius: 8
        }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

// 受保护的路由组件
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const location = window.location.pathname;

  // 检查是否是首次访问
  const hasVisited = localStorage.getItem('llmgateway_visited');

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (location === '/' && !hasVisited) {
    return <Navigate to="/welcome" replace />;
  }

  return children;
};

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/welcome" element={
        <ProtectedRoute>
          <Welcome />
        </ProtectedRoute>
      } />
      <Route path="/" element={
        <ProtectedRoute>
          <MainLayout>
            <Dashboard />
          </MainLayout>
        </ProtectedRoute>
      } />
      <Route path="/models" element={
        <ProtectedRoute>
          <MainLayout>
            <ModelConfig />
          </MainLayout>
        </ProtectedRoute>
      } />
      <Route path="/quota" element={
        <ProtectedRoute>
          <MainLayout>
            <QuotaMonitor />
          </MainLayout>
        </ProtectedRoute>
      } />
      <Route path="/config" element={
        <ProtectedRoute>
          <MainLayout>
            <SystemConfig />
          </MainLayout>
        </ProtectedRoute>
      } />
      <Route path="/logs" element={
        <ProtectedRoute>
          <MainLayout>
            <Logs />
          </MainLayout>
        </ProtectedRoute>
      } />
      <Route path="/agent" element={
        <ProtectedRoute>
          <MainLayout>
            <AgentGuide />
          </MainLayout>
        </ProtectedRoute>
      } />
      <Route path="/profile" element={
        <ProtectedRoute>
          <MainLayout>
            <Profile />
          </MainLayout>
        </ProtectedRoute>
      } />
      <Route path="/change-password" element={
        <ProtectedRoute>
          <MainLayout>
            <ChangePassword />
          </MainLayout>
        </ProtectedRoute>
      } />
    </Routes>
  );
}

export default App;
