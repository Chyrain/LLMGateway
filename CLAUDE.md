# CLAUDE.md

本文档为 Claude Code (claude.ai/code) 在本项目中工作提供指导。

## 语言规范
- 所有对话和文档都请使用中文

## 项目概述

LLMGateway（灵模网关）是一个免费的大语言模型聚合网关，提供以下功能：

- 多模型支持（OpenAI、Claude、Qwen、智谱清言、通义千问、MiniMax、DeepSeek、月之暗面等）
- 配额耗尽时自动切换模型
- 实时配额监控
- 请求日志和操作日志记录
- 管理后台，支持双前端（Vue 3 和 React）

## 架构设计

### 组件构成

- **后端**（FastAPI + SQLAlchemy + SQLite）：API 服务、网关逻辑、数据库
- **Vue 前端**（Element Plus）：默认管理界面，运行在端口 80
- **React 前端**（Ant Design）：备选管理界面，运行在端口 88

### 关键后端文件

- `backend/main.py`：FastAPI 应用入口、路由注册、运行模式判断
- `backend/routers/gateway.py`：网关路由（OpenAI + Anthropic 兼容接口）
- `backend/services/gateway_core.py`：核心网关逻辑 - 请求路由、模型选择、自动切换
- `backend/services/quota_monitor.py`：配额跟踪和监控
- `backend/services/model_switcher.py`：模型回退/切换逻辑
- `backend/routers/`：API 端点（认证、配置、日志、通知、统计）
- `backend/models/`：SQLAlchemy 模型（model_config、quota_stat、operation_log、system_config）
- `backend/config/encryption.py`：API 密钥的 Fernet 加密

### 运行模式

网关服务支持两种运行模式（通过环境变量控制）：

| 环境变量 | 端口 | 暴露接口 |
|---------|------|---------|
| `API_MODE=true` | 8000 | 管理接口（/api/*）+ 网关接口（/v1/*） |
| `GATEWAY_MODE=true` | 8080 | 仅网关接口（/v1/*） |

### 网关接口（8080 端口）

- `GET /v1/models` - 模型列表（OpenAI 兼容）
- `POST /v1/chat/completions` - 聊天完成（OpenAI 兼容）
- `POST /v1/messages` - 聊天完成（Anthropic 兼容）

### 数据流转

1. 客户端请求到达网关端点
2. `gateway_core.py` 选择模型（手动模式或自动切换模式）
3. 使用加密后的 API 密钥将请求转发给 LLM 提供商
4. 响应记录到 `operation_log` 表
5. 配额更新到 `quota_stat` 表

## 常用命令

### 开发环境

```bash
# 后端
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Vue 前端（端口 80）
cd frontend && npm run dev

# React 前端（端口 88）
cd frontend-react && npm run dev
```

### Docker

```bash
docker compose up -d              # 启动所有服务
docker compose logs -f            # 查看日志
docker compose down               # 停止所有服务
```

### 测试

```bash
cd backend
pytest tests/test_all.py -v                    # 运行所有测试
pytest tests/test_all.py::TestEncryption -v   # 运行特定测试类
pytest tests/test_all.py -v --cov=backend     # 带覆盖率
```

## 服务地址

- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 网关：http://localhost:8080
- Vue 前端：http://localhost:80（默认管理员：admin/admin123）
- React 前端：http://localhost:88

## 环境变量

`.env` 文件中的关键变量：

- `DB_TYPE`：数据库类型（sqlite）
- `DB_PATH`：数据库文件路径
- `ENCRYPT_KEY`：用于 API 密钥加密的 Fernet 密钥
- `API_PORT`：后端端口（8000）
- `GATEWAY_PORT`：网关端口（8080）
- `SWITCH_THRESHOLD`：自动切换阈值百分比
- `SYNC_INTERVAL`：配额同步间隔（秒）
