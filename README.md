# 灵模网关 (LLMGateway)

🎯 一个免费 LLM 模型聚合网关，支持多模型自动切换、额度监控、请求日志等功能。

## ✨ 特性

- 🔄 **多模型支持** - 支持 24+ 厂商（国际/国内/本地）
- 📊 **额度监控** - 实时监控各模型使用额度，避免超支
- 🚀 **自动切换** - 额度耗尽自动切换到下一个可用模型
- 📝 **请求日志** - 完整记录所有 API 请求，便于排查问题
- 🔔 **通知预警** - 额度即将耗尽时及时提醒
- 👤 **用户管理** - 个人中心、密码修改
- 🎨 **双前端** - Vue 3 + React 双版本管理后台
- 🆕 **统一配置** - `vendors.json` 统一管理厂商模型配置
- 🎯 **能力检测** - 自动识别 Vision/Text/Audio 能力
- 📦 **Coding Plan** - 支持编程套餐管理和配额同步

```
┌─────────────────────────────────────────────────────────┐
│                      用户访问                           │
└─────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
      ┌─────────┐    ┌─────────┐    ┌─────────┐
      │ Vue 前端 │    │ React 前端 │   │ 网关 API │
      │ :80     │    │ :88     │    │ :8000   │
      └─────────┘    └─────────┘    └─────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                ┌─────────────────────┐
                │   Nginx 反向代理     │
                │   (统一入口)         │
                └─────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
      ┌─────────┐    ┌─────────┐    ┌─────────┐
      │ 后端API │    │ 网关服务 │    │ SQLite  │
      │ :8000   │    │ :8080   │    │ 数据库   │
      └─────────┘    └─────────┘    └─────────┘
```

## 🚀 快速开始

### 方式一：本地 Docker 部署

#### 1. 环境准备

```bash
# Docker 和 Docker Compose
docker --version
docker compose version
```

#### 2. 克隆项目

```bash
git clone https://github.com/Chyrain/LLMGateway.git
cd LLMGateway
```

#### 3. 初始化配置

```bash
# 运行初始化脚本生成配置文件和加密密钥
chmod +x scripts/init.sh
./scripts/init.sh
```

#### 4. 启动服务

```bash
# 标准模式（多容器）
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# 或全合一模式（节省资源，推荐 NAS 使用）
docker compose -f docker-compose.all-in-one.yml --env-file .env.prod up -d --build
```

### 方式二：NAS 一键部署

```bash
# 执行一键部署脚本
chmod +x deploy-to-nas.sh
./deploy-to-nas.sh -h 192.168.1.2 -u chyrain
```

> 📄 详细部署文档请查看 [DEPLOY.md](DEPLOY.md)

### 访问管理后台

| 前端版本 | 地址 | 说明 |
|---------|------|------|
| Vue 版 | http://localhost:80 | 默认版本 |
| React 版 | http://localhost:88 | 全新 UI |

**默认账号**: `admin` / `admin123`

> ⚠️ **首次登录后请立即修改默认密码！**

## 📖 使用指南

### 添加模型配置

1. 登录管理后台
2. 进入 **模型配置** 页面
3. 点击 **添加模型**
4. 填写模型信息：
   - **厂商**: 选择模型提供商（OpenAI、Claude、Qwen 等）
   - **模型名称**: 如 `gpt-4o`、`claude-3-5-sonnet`
   - **API Key**: 在各平台申请的 API Key
   - **API Base**: API 接口地址（大部分厂商已预设）
   - **优先级**: 数字越小优先级越高（1 最高）
5. 点击 **测试连通** 验证配置
6. 点击 **启用** 激活模型

### 配置参数说明

| 参数 | 必填 | 说明 |
|-----|------|------|
| 厂商 | ✅ | 模型提供商 |
| 模型名称 | ✅ | 具体模型标识 |
| API Key | ✅ | 平台申请的密钥 |
| API Base | ❌ | 大部分厂商已预设默认值 |
| 优先级 | ❌ | 默认 100，数字越小优先级越高 |

### 使用网关 API

```bash
# 示例：调用 Chat Completions API
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

## 🎨 前端版本对比

| 特性 | Vue 3 版本 | React 版本 |
|------|-----------|-----------|
| UI 框架 | Element Plus 2.x | Ant Design 5.x |
| 端口 | 80 | 88 |
| 状态管理 | ref/reactive | useState/useEffect |
| 路由 | Vue Router 4 | React Router 6 |
| 图表 | ECharts | ECharts |
| 暗色主题 | ✅ | ✅ |
| 响应式 | ✅ | ✅ |

**推荐**: 新用户推荐使用 Vue 版本，功能更完善；React 版本适合前端技术栈为 React 的团队。

## 🏗️ 项目结构

```
LLMGateway/
├── backend/               # 后端服务 (FastAPI + Python)
│   ├── main.py            # 应用入口
│   ├── config/            # 配置模块（数据库、加密）
│   ├── models/            # 数据模型
│   ├── routers/           # API 路由
│   │   ├── auth.py        # 认证接口
│   │   ├── config.py      # 配置接口
│   │   ├── logs.py        # 日志接口
│   │   ├── notifications.py # 通知接口
│   │   └── stats.py       # 统计接口
│   └── services/         # 业务逻辑
│       ├── gateway_core.py # 网关核心
│       └── quota_monitor.py # 额度监控
│
├── frontend/              # Vue3 前端 (默认)
│   ├── src/
│   │   ├── api/          # API 接口封装
│   │   ├── views/        # 页面组件
│   │   ├── router/       # 路由配置
│   │   └── store/        # Pinia 状态管理
│   └── Dockerfile
│
├── frontend-react/       # React 前端 (端口 88)
│   ├── src/
│   │   ├── services/     # API 服务层
│   │   ├── pages/        # 页面组件
│   │   ├── hooks/        # 自定义 Hooks
│   │   └── styles/       # 样式文件
│   ├── nginx.conf        # Nginx 配置
│   └── Dockerfile
│
├── gateway/              # 网关服务
├── docs/                 # 项目文档
├── scripts/              # 脚本工具
└── docker-compose.yml    # Docker 编排配置
```

## 💻 本地开发

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --reload

# API 文档: http://localhost:8000/docs
```

### Vue 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### React 前端开发

```bash
cd frontend-react

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 🐳 Docker 部署

### 使用 Docker Compose

```bash
# 构建并启动所有服务
docker compose up -d

# 只启动 Vue 前端（默认）
docker compose up -d frontend

# 只启动 React 前端
docker compose up -d frontend-react

# 只启动后端
docker compose up -d backend

# 查看日志
docker compose logs -f

# 停止所有服务
docker compose down

# 重新构建（修改配置后）
docker compose build --no-cache
```

### 单独部署 React 前端

```bash
# 构建镜像
docker build -t llmgateway-frontend-react:latest frontend-react/

# 运行容器
docker run -d -p 88:80 --name llmgateway-react \
  --network llmgateway-network \
  llmgateway-frontend-react:latest
```

### 环境变量配置

通过 `.env` 文件：

```env
# 后端配置
BACKEND_PORT=8000
DB_TYPE=sqlite
DB_PATH=./data/llmgateway.db
ENCRYPT_KEY=your-256-bit-encryption-key-here

# React 前端
VITE_API_BASE=/api

# 网关
GATEWAY_PORT=8080
```

### 端口说明

| 服务 | 端口 | 说明 | 默认开启 |
|------|------|------|---------|
| Vue 前端 | 80 | 管理后台（默认） | ✅ |
| React 前端 | 88 | 管理后台（React版） | ✅ |
| 后端 API | 8000 | REST API | ✅ |
| 网关服务 | 8080 | LLM 网关 | ✅ |

## 📡 API 接口文档

### 认证接口

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/logout` | POST | 退出登录 |
| `/api/auth/profile` | GET | 获取用户信息 |
| `/api/auth/change-password` | POST | 修改密码 |

### 模型配置

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/api/model/list` | GET | 模型列表 |
| `/api/model/add` | POST | 添加模型 |
| `/api/model/{id}` | PUT | 更新模型 |
| `/api/model/{id}` | DELETE | 删除模型 |
| `/api/model/{id}/test` | POST | 测试连通 |
| `/api/model/{id}/enable` | POST | 启用模型 |
| `/api/model/{id}/disable` | POST | 禁用模型 |

### 额度监控

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/api/quota/stat` | GET | 额度统计 |
| `/api/quota/sync/{modelId}` | POST | 同步额度 |
| `/api/quota/history` | GET | 使用历史 |

### 日志管理

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/api/log/list` | GET | 日志列表 |
| `/api/log/export` | GET | 导出日志 |
| `/api/log/clear` | POST | 清空日志 |

### 网关 API

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/v1/chat/completions` | POST | Chat Completions |
| `/v1/models` | GET | 模型列表 |

## 🔔 通知系统

系统会在以下情况发送通知：

- ✅ 模型启用成功
- ⚠️ 模型额度低于 20%
- ❌ 模型额度耗尽
- 🔄 自动切换模型

## 🛠️ 技术栈

### 后端

- **FastAPI** - 高性能 Python Web 框架
- **SQLAlchemy** - ORM 数据库访问
- **SQLite** - 轻量级数据库
- **Uvicorn** - ASGI 服务器

### 前端（Vue）

- **Vue 3** - 前端框架
- **Element Plus** - UI 组件库
- **Pinia** - 状态管理
- **Axios** - HTTP 客户端
- **ECharts** - 数据可视化

### 前端（React）

- **React 18** - 前端框架
- **Ant Design 5.x** - UI 组件库
- **React Router 6** - 路由管理
- **Axios** - HTTP 客户端
- **ECharts** - 数据可视化

## 📝 更新日志

### v1.5.0 (2026-03-29)

#### ✨ 核心功能增强
- 🔄 **双格式厂商动态端点路由** - 根据请求端点类型自动选择正确的模型配置
  - 支持双格式的厂商 (qwen/bailian) 根据请求端点自动路由到对应的 API
  - OpenAI 格式请求 → 使用 `api_spec=openai` 的模型配置 (api_base + api_path)
  - Anthropic 格式请求 → 使用 `api_spec=anthropic` 的模型配置 (api_base + api_path)
  - 直接使用模型配置的 API Base 和 API Path，不做动态修改

#### 🐛 Bug 修复
- ✅ 修复双格式厂商模型选择逻辑，修复指定模型时未正确选择对应 api_spec 记录的问题
- ✅ 修复 `/v1/messages` 端点路由，Anthropic 端点的模型配置选择逻辑
- ✅ 修复 `/v1/chat/completions` 端点路由，OpenAI 端点的模型配置选择逻辑
- ✅ 恢复 thinking 字段到允许列表（由 router 层按需过滤）

#### 📚 文档更新
- ✅ 更新 CHANGELOG 记录 1.5.0 版本
- ✅ 更新国内厂商 API 配置文档

---

### v1.4.9 (2026-03-29)

#### 🔧 百炼 Anthropic 原生支持
- ✅ 修正阿里百炼平台的 Anthropic 格式支持方式
- ✅ 百炼平台原生支持 Anthropic 格式，不需要转换
- ✅ 更新 `anthropic_compat_base` 为 `https://coding.dashscope.aliyuncs.com/apps/anthropic`
- ✅ `api_spec_support` 改为 `["openai", "anthropic"]`（原生支持两种格式）

---

### v1.4.8 (2026-03-28)

#### 🚀 核心功能增强
- 🔄 **Auto 模型模式** - 新增 `auto` 模型选项，支持自动切换至最高优先级可用模型
- 🎯 **智能负载均衡** - 网关支持不传 model 参数时自动使用最高优先级模型
- 🔧 **自动重试机制** - 模型失败时自动切换下一个可用模型，提升请求成功率
- ✅ **响应验证** - 空响应时自动切换，确保请求可靠性

#### 🏭 新增厂商支持
- **腾讯混元** - 完整支持腾讯混元大模型
- **字节豆包** - 支持字节跳动豆包大模型
- **零一万物** - 支持零一万物 AI 模型
- **阶跃星辰** - 支持阶跃星辰大模型

#### 🐛 Bug 修复
- ✅ 修复 MiniMax 模型网关连接问题
- ✅ 修复 auto 模式只选择已连通模型的逻辑
- ✅ 修复无模型时返回空列表的处理

#### 🎨 前端优化
- ✅ 更新 React 前端厂商配置模板
- ✅ 清理冗余配置文件

#### 📝 文档更新
- ✅ 更新 Docker 部署与更新指南
- ✅ 完善厂商配置说明文档

---

### v1.2.0 (2026-03-01)
---

### v1.1.0 (2026-02-05)
## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
