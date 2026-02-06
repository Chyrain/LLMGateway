# 灵模网关 React 前端

🎯 使用 React + Ant Design 重写的灵模网关管理后台，提供更现代的 UI 体验。

## ✨ 特性

- 🎨 **现代 UI** - Ant Design 5.x 设计语言
- 📱 **响应式** - 适配各种屏幕尺寸
- 🚀 **高性能** - React 18 + Vite 构建
- 📊 **数据可视化** - ECharts 图表支持
- 🔐 **安全认证** - JWT Token 认证
- 🌙 **暗色主题** - 优雅的暗色侧边栏

## 🛠️ 技术栈

| 分类 | 技术 | 版本 |
|-----|------|------|
| 框架 | React | 18.2+ |
| UI 组件 | Ant Design | 5.x |
| 路由 | React Router | 6.x |
| HTTP | Axios | 1.x |
| 图表 | ECharts | 5.x |
| 样式 | Sass | - |
| 构建 | Vite | 5.x |

## 📁 项目结构

```
frontend-react/
├── src/
│   ├── main.jsx              # 入口文件
│   ├── App.jsx               # 主应用组件（含路由和布局）
│   ├── services/
│   │   └── api.js           # API 服务层（Axios 封装）
│   ├── pages/
│   │   ├── Login.jsx        # 🔐 登录页
│   │   ├── Welcome.jsx      # 👋 欢迎页
│   │   ├── Dashboard.jsx    # 📊 仪表盘
│   │   ├── ModelConfig.jsx  # ⚙️ 模型配置
│   │   ├── QuotaMonitor.jsx # 💰 额度监控
│   │   ├── SystemConfig.jsx # 🔧 系统配置
│   │   ├── Logs.jsx         # 📝 日志管理
│   │   ├── AgentGuide.jsx   # 🤖 Agent 适配
│   │   ├── Profile.jsx      # 👤 个人中心
│   │   └── ChangePassword.jsx # 🔑 修改密码
│   ├── hooks/               # 自定义 Hooks
│   ├── components/           # 公共组件
│   └── styles/
│       └── index.scss       # 全局样式
├── index.html
├── vite.config.js           # Vite 配置
├── nginx.conf               # Nginx 配置（Docker）
├── Dockerfile              # Docker 构建文件
└── package.json
```

## 🚀 快速开始

### 本地开发

```bash
# 进入目录
cd frontend-react

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### Docker 部署

```bash
# 构建并启动
docker compose up -d frontend-react

# 查看日志
docker logs -f llmgateway-frontend-react

# 访问管理后台
# http://localhost:88
```

### 配置

在 `.env` 文件中配置：

```env
# API 基础地址
VITE_API_BASE=/api

# 开发环境可以直连后端
# VITE_API_BASE=http://localhost:8000
```

## 📖 功能列表

### ✅ 已完成

- [x] 用户登录/退出
- [x] 仪表盘（统计卡片、使用趋势、模型分布）
- [x] 模型配置管理（增删改查、测试连通、启用禁用）
- [x] 额度监控（实时同步、使用趋势、预警提醒）
- [x] 系统配置
- [x] 日志管理（列表查看、筛选、导出、清空）
- [x] Agent 适配指南
- [x] 个人中心（查看信息、修改密码）
- [x] 通知系统（未读计数、消息列表）

### 🔄 对比 Vue 版本

| 特性 | Vue 3 版本 | React 版本 |
|------|-----------|-----------|
| UI 框架 | Element Plus | Ant Design 5.x |
| 状态管理 | ref/reactive | useState/useEffect |
| 路由 | Vue Router 4 | React Router 6 |
| 图表 | vue-echarts | echarts-for-react |
| HTTP 客户端 | axios | axios |
| 样式方案 | Scoped CSS | SCSS Modules |
| 打包工具 | Vite | Vite |
| 暗色主题 | Element Plus 内置 | Ant Design 内置 |

## 🔧 核心组件

### API 服务 (`services/api.js`)

统一封装 Axios，提供：
- 请求/响应拦截器
- Token 自动注入
- 错误处理
- 消息提示

```javascript
import { authApi, modelApi, quotaApi } from './services/api';

// 登录示例
await authApi.login(username, password);

// 获取模型列表
const models = await modelApi.list();
```

### 主布局 (`App.jsx`)

- 响应式侧边栏（可折叠）
- 顶部导航栏（通知、用户菜单）
- 页面标题动态更新
- 路由守卫（ProtectedRoute）

## 🎨 页面预览

### 登录页
- 简洁的登录表单
- 默认管理员: `admin` / `admin123`
- 记住用户名

### 仪表盘
- 统计卡片（模型数、额度、使用率）
- 7天使用趋势图
- 模型分布饼图
- 快速操作入口

### 模型配置
- 表格展示模型列表
- 状态筛选、优先级排序
- 添加/编辑/删除/测试

## 🐛 常见问题

### 1. 登录提示 500 错误

检查 nginx 代理配置：
```nginx
location /api/ {
    proxy_pass http://backend:8000/api/;  # 确保末尾有 /api/
}
```

### 2. API 请求 404

确保 `.env` 中 `VITE_API_BASE=/api` 与 nginx 代理路径一致。

### 3. 样式不生效

检查是否正确安装 Sass：
```bash
npm install sass
```

## 📝 更新日志

### v1.1.0 (2024-02-05)

- ✨ 优化暗色主题
- 🔧 修复 nginx 代理配置问题
- 📊 改进仪表盘图表
- 🐛 修复若干 bug

### v1.0.0 (2024-02-04)

- 🎉 初始版本发布
- 🔐 用户认证系统
- 🤖 模型配置管理
- 📊 额度监控
- 📝 日志管理
- 🔔 通知系统

## 📄 许可证

MIT License
