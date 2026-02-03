# 灵模网关 (LLM Free Quota Gateway)

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Vue](https://img.shields.io/badge/vue-3.4+-yellow)
![License](https://img.shields.io/badge/license-MIT-orange)

**标准化OpenAI兼容协议的大模型免费额度自动切换网关**

[English](README_EN.md) | 简体中文

</div>

## 📋 目录

- [产品简介](#产品简介)
- [核心特性](#核心特性)
- [快速开始](#快速开始)
- [架构设计](#架构设计)
- [使用指南](#使用指南)
- [Agent工具适配](#agent工具适配)
- [部署文档](#部署文档)
- [API文档](#api文档)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 🎯 产品简介

**灵模网关**是一款标准化OpenAI兼容协议的大模型统一接入网关，核心解决个人/开发者利用各家大模型免费额度的痛点。

通过**一站式大模型API配置管理、实时额度监控、阈值触发自动切换**能力，让用户无需手动关注各厂商额度消耗，实现大模型服务"无感续跑"。

## ✨ 核心特性

- 🔄 **自动切换** - 额度耗尽自动切换，无需人工干预
- 🔐 **安全加密** - AES-256加密存储API Key
- 📊 **实时监控** - 额度消耗实时统计，多渠道告警
- 🛠️ **开箱即用** - 内置15+厂商预配置模板
- 🐳 **Docker部署** - 一键部署，5分钟上线
- 🔧 **工具适配** - OpenClaw、Claude Code、Cursor一键对接

## 🚀 快速开始

### 方式一：Docker Compose一键部署（推荐）

```bash
# 克隆项目
git clone https://github.com/your-repo/LLMGateway.git
cd LLMGateway

# 启动服务
docker-compose up -d

# 访问管理平台
# http://localhost:80
# 默认管理员: admin
# 默认密码: admin123
```

### 方式二：本地开发部署

#### 前端

```bash
cd frontend
npm install
npm run dev
```

#### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户浏览器                               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    前端管理平台 (Vue3 + Element Plus)            │
│  仪表盘 | 模型配置 | 额度监控 | 系统配置 | 日志管理 | Agent适配   │
└─────────────────────────────┬───────────────────────────────────┘
                              │ RESTful API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    后端服务 (FastAPI + Python)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐  │
│  │ 配置管理服务 │ │ 额度监控服务 │ │ 日志服务    │ │ 统计告警   │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    网关核心服务 (OpenAI兼容接口)                  │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    厂商API转发层                         │   │
│   │  OpenAI │ Claude │ Gemini │ 文心一言 │ 通义千问 │ ...   │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    数据存储 (SQLite/MySQL)                       │
│  model_config | quota_stat | system_config | operation_log      │
└─────────────────────────────────────────────────────────────────┘
```

## 📖 使用指南

### 1. 添加模型配置

1. 进入「模型配置」页面
2. 点击「添加模型」
3. 选择厂商模板（如OpenAI、智谱清言）
4. 填入API Key
5. 点击「测试连通性」
6. 保存启用

### 2. 配置自动切换

1. 进入「额度监控」页面
2. 设置全局切换阈值（默认99%）
3. 调整模型优先级（拖拽排序）
4. 启用自动切换

### 3. 对接Agent工具

参考 [Agent工具适配指南](docs/AGENT_GUIDE.md)

## 🔧 Agent工具适配

### OpenClaw

```yaml
# config.yaml
model:
  provider: openai
  name: gpt-3.5-turbo
  base_url: http://你的网关IP:8080/v1
  api_key: gateway_123456
```

### Claude Code

```bash
export ANTHROPIC_API_KEY=gateway_123456
export ANTHROPIC_API_BASE=http://你的网关IP:8080/v1
```

### Cursor

在Settings中配置：
- Custom API Base: `http://你的网关IP:8080/v1`
- Custom API Key: `gateway_123456`

详细教程见 [Agent工具适配文档](docs/AGENT_GUIDE.md)

## 🐳 部署文档

### 环境要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 内存: 最低512MB，推荐1GB+
- 磁盘: 最低1GB

### 配置说明

修改 `docker-compose.yml` 中的环境变量：

```yaml
environment:
  - GATEWAY_PORT=8080
  - API_PORT=8000
  - ENCRYPT_KEY=your-256bit-key
  - DB_TYPE=sqlite  # 或 mysql
```

### Nginx反向代理（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:80;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }

    location /v1 {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }
}
```

## 📚 API文档

### 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/model/list` | GET | 获取模型配置列表 |
| `/api/model/add` | POST | 新增模型配置 |
| `/api/model/test` | POST | 测试模型连通性 |
| `/api/quota/stat` | GET | 获取额度统计 |
| `/api/switch/rule` | POST | 配置自动切换规则 |
| `/api/log/list` | GET | 获取日志列表 |
| `/v1/chat/completions` | POST | OpenAI标准网关接口 |

完整API文档: [API Reference](docs/API.md)

## ❓ 常见问题

### Q1: 额度为什么不自动同步？
部分厂商（如OpenAI、Anthropic）支持自动同步，其他厂商需要手动录入额度。

### Q2: 迁移数据会丢失吗？
支持断点续传，迁移失败可重新执行，不会丢失已成功迁移的数据。

### Q3: 如何升级版本？
```bash
git pull
docker-compose down
docker-compose up -d
```

更多问题: [FAQ](docs/FAQ.md)

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [OpenAI](https://openai.com) - Chat Completions API标准
- [Vue.js](https://vuejs.org) - 前端框架
- [FastAPI](https://fastapi.tiangolo.com) - 后端框架
- [Element Plus](https://element-plus.org) - UI组件库

---

<div align="center">

**让大模型服务更普惠**

Made with ❤️ by LLMGateway Team

</div>
