# AGENTS.md - LLMGateway 项目开发指南

> 适用于 LLMGateway 多模态网关项目的 AI 代理开发指南

## 项目概述

LLMGateway 是一个统一的多模态大模型 API 网关，支持：
- **多厂商接入**: OpenAI、Anthropic、阿里通义、智谱、讯飞、Google Gemini 等
- **多模态支持**: 文本、图片（Vision）、流式输出
- **双前端**: Vue 3 (端口 80) + React (端口 88)
- **核心功能**: 负载均衡、配额管理、日志审计、额度监控

---

## 一、构建/测试/运行命令

### 1.1 后端 (FastAPI + Python 3.10)

```bash
cd backend

# 安装依赖
pip install -r requirements.txt
pip install -r tests/requirements.txt  # 测试依赖

# 运行所有测试
pytest tests/test_all.py -v

# 运行单个测试类
pytest tests/test_all.py::TestEncryption -v

# 运行单个测试方法
pytest tests/test_all.py::TestEncryption::test_encrypt_decrypt_roundtrip -v

# 运行测试并生成覆盖率报告
pytest tests/test_all.py -v --cov=backend

# 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 代码检查
ruff check .
ruff format .
```

### 1.2 前端 - React (端口 88)

```bash
cd frontend-react

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build

# 预览生产构建
npm run preview

# 运行 E2E 测试
npm run test:e2e

# 运行 E2E 测试（带 UI）
npm run test:e2e:ui
```

### 1.3 前端 - Vue (端口 80)

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build

# 代码检查
npm run lint
```

### 1.4 Docker (全部服务)

```bash
# 启动所有服务
docker compose up -d

# 启动特定服务
docker compose up -d backend
docker compose up -d frontend
docker compose up -d frontend-react

# 查看日志
docker compose logs -f backend

# 停止并清理
docker compose down

# 重新构建（不使用缓存）
docker compose build --no-cache
```

---

## 二、代码风格指南

### 2.1 Python (后端)

| 类别 | 规范 |
|------|------|
| **基础风格** | 遵循 PEP 8，最大行宽 100 字符 |
| **导入顺序** | 标准库 → 第三方 → 本地模块，按字母排序 |
| **类型注解** | 函数参数和返回值必须使用类型注解 |
| **命名约定** | `snake_case` (函数/变量), `PascalCase` (类), `UPPER_CASE` (常量) |
| **字符串引号** | 统一使用双引号 `"` |
| **文档字符串** | 使用三双引号 `"""` |
| **错误处理** | 使用 FastAPI `HTTPException`，返回合适的状态码 |
| **异步编程** | 使用 `async/await`，避免阻塞操作 |

**示例:**
```python
from fastapi import HTTPException
from typing import Dict, Optional

async def get_model_config(model_id: int, db: SessionLocal) -> Dict:
    """获取模型配置"""
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model.to_dict()
```

### 2.2 React (frontend-react/)

| 类别 | 规范 |
|------|------|
| **组件风格** | 使用 Ant Design 5.x 组件库 |
| **组件命名** | `PascalCase` (如 `ModelConfig.jsx`) |
| **Hooks** | 自定义 Hook 使用 `useHookName` 格式 |
| **导入顺序** | React → 第三方 → 本地组件 → 服务 |
| **状态管理** | 优先使用 React Hooks，复杂状态用 Context |
| **样式** | 使用 SCSS 模块，BEM 命名约定 |

**示例:**
```jsx
import React, { useState, useEffect } from 'react';
import { Card, Button, Table } from 'antd';
import { modelApi } from '@/services/api';
import styles from './ModelConfig.module.scss';

const ModelConfig = () => {
  const [models, setModels] = useState([]);
  
  useEffect(() => {
    loadModels();
  }, []);
  
  return <Card className={styles.container}>...</Card>;
};
```

### 2.3 Vue 3 (frontend/)

| 类别 | 规范 |
|------|------|
| **组件风格** | Element Plus 组件约定 |
| **组件命名** | `PascalCase` |
| **组合式 API** | 使用 `<script setup>` 语法 |
| **导入顺序** | Vue → 第三方 → 本地组件 → API 服务 |

### 2.4 数据库 (SQLAlchemy)

```python
# ✅ 正确使用会话
try:
    db.add(model)
    db.commit()
except Exception as e:
    db.rollback()
    raise
finally:
    db.close()

# ✅ 使用类型注解
from sqlalchemy.orm import Session
def get_model(db: Session, model_id: int) -> ModelConfig:
    ...
```

### 2.5 测试规范

| 要求 | 说明 |
|------|------|
| **测试框架** | pytest + `@pytest.mark.asyncio` |
| **测试类命名** | `Test*` 前缀 (如 `TestEncryption`) |
| **测试方法命名** | 使用下划线分隔，描述性命名 |
| **Mock 外部依赖** | HTTP 请求、数据库等必须 Mock |
| **测试夹具** | 使用 `@pytest.fixture` 共享测试数据 |

### 2.6 安全规范

- ✅ API Key 使用 Fernet 加密存储 (`config/encryption.py`)
- ✅ 禁止在日志中输出敏感信息
- ✅ 生产环境使用正确的 CORS 配置
- ✅ 所有用户输入使用 Pydantic 模型验证

### 2.7 Git 规范

- ✅ 提交信息清晰描述变更内容
- ✅ 不提交 `__pycache__`, `.pyc`, `node_modules`, `venv/`
- ✅ 敏感文件 (`.env`, API Key) 禁止提交

---

## 三、项目结构

```
LLMGateway/
├── backend/                 # FastAPI 后端
│   ├── config/             # 配置文件
│   ├── models/             # SQLAlchemy 模型
│   ├── routers/            # API 路由
│   ├── services/           # 业务逻辑
│   └── tests/              # 单元测试
├── frontend/               # Vue 3 前端 (端口 80)
├── frontend-react/         # React 前端 (端口 88)
└── docker-compose.yml      # Docker 编排
```

---

## 四、开发注意事项

### 4.1 添加新模型厂商

1. 在 `backend/services/gateway_core.py` 的 `VENDOR_CONFIGS` 添加配置
2. 实现请求构建器 `_build_xxx_request`
3. 实现响应解析器 `_parse_xxx_response`
4. 在前端 `ModelConfig.jsx` 添加厂商模板

### 4.2 连通性测试失败排查

- 检查 `api_base` URL 格式（必须以 `http://` 或 `https://` 开头）
- 确认 `api_spec` 与 API 格式匹配（OpenAI 兼容 vs 官方格式）
- 验证请求体格式（某些厂商使用 `input.messages` 而非 `messages`）

### 4.3 多模态支持

- 消息内容支持 `str | List[ContentPart]`
- 图片格式：URL 或 base64 (`data:image/jpeg;base64,...`)
- 流式输出：设置 `stream: true`，返回 `text/event-stream`

---

## 五、常见问题

**Q: 测试失败 "UnboundLocalError"?**  
A: 这是现有问题，不影响核心功能。专注于业务逻辑测试。

**Q: 如何调试网关请求？**  
A: 在 `gateway_core.py` 中添加 `print(f"[DEBUG] ...")` 查看请求/响应。

**Q: Docker 启动失败？**  
A: 检查端口占用，确认 `.env` 配置正确，查看 `docker compose logs`。

---

## 七、厂商模型配置

### 7.1 配置文件位置

| 文件 | 说明 |
|------|------|
| `backend/config/vendors.json` | 统一厂商模型配置（JSON格式） |
| `backend/config/vendor_config.py` | Python配置加载器 |
| `frontend-react/src/pages/ModelConfig.jsx` | 前端厂商模板 |

### 7.2 支持的厂商

**国际厂商**: OpenAI, Anthropic Claude, Google Gemini, Mistral AI, Groq, Perplexity, xAI Grok

**国内厂商**: 通义千问(含灵码Coding Plan), 智谱AI, 深度求索, 月之暗面Kimi, MiniMax, 讯飞星火, 腾讯混元, 字节豆包, 零一万物, 阶跃星辰

**本地模型**: Ollama, vLLM, LM Studio

### 7.3 添加新厂商

1. 编辑 `backend/config/vendors.json` 添加厂商配置
2. 同步更新 `frontend-react/src/pages/ModelConfig.jsx` 的 VENDOR_CONFIGS
3. 重启后端服务

---

## 八、Docker 部署与更新
---

## 七、厂商模型配置

### 7.1 配置文件位置

| 文件 | 说明 |
|------|------|
| `backend/config/vendors.json` | 统一厂商模型配置（JSON格式） |
| `backend/config/vendor_config.py` | Python配置加载器 |
| `frontend-react/src/pages/ModelConfig.jsx` | 前端厂商模板 |

### 7.2 支持的厂商

**国际厂商**: OpenAI, Anthropic Claude, Google Gemini, Mistral AI, Groq, Perplexity, xAI Grok

**国内厂商**: 通义千问(含灵码Coding Plan), 智谱AI, 深度求索, 月之暗面Kimi, MiniMax, 讯飞星火, 腾讯混元, 字节豆包, 零一万物, 阶跃星辰

**本地模型**: Ollama, vLLM, LM Studio

### 7.3 添加新厂商

1. 编辑 `backend/config/vendors.json` 添加厂商配置
2. 同步更新 `frontend-react/src/pages/ModelConfig.jsx` 的 VENDOR_CONFIGS
3. 重启后端服务

---

## 八、Docker 部署与更新

### 8.1 部署流程

**完成代码修改后，必须重新构建并重启 Docker 服务：**

```bash
# 1. 进入项目根目录
cd /Users/chyrain/Desktop/workspace/AI/LLMGateway

# 2. 重新构建镜像（不使用缓存）
docker compose build --no-cache

# 3. 重启所有服务
docker compose down
docker compose up -d

# 4. 查看启动日志确认成功
docker compose logs -f backend
docker compose logs -f frontend-react
```

### 8.2 只重启特定服务

```bash
# 只重启后端
docker compose restart backend

# 只重启 React 前端
docker compose restart frontend-react

# 只重启 Vue 前端
docker compose restart frontend
```

### 8.3 验证部署

```bash
# 检查所有服务状态
docker compose ps

# 访问测试
curl http://localhost:88/api/models  # React 前端 API
curl http://localhost/api/models     # Vue 前端 API (Nginx 代理)
```

---

**最后更新**: 2026-03-01  
**适用版本**: LLMGateway v1.0+


## 七、Docker 部署与更新

### 7.1 部署流程

**完成代码修改后，必须重新构建并重启 Docker 服务：**

```bash
# 1. 进入项目根目录
cd /Users/chyrain/Desktop/workspace/AI/LLMGateway

# 2. 重新构建镜像（不使用缓存）
docker compose build --no-cache

# 3. 重启所有服务
docker compose down
docker compose up -d

# 4. 查看启动日志确认成功
docker compose logs -f backend
docker compose logs -f frontend-react
```

### 7.2 只重启特定服务

```bash
# 只重启后端
docker compose restart backend

# 只重启 React 前端
docker compose restart frontend-react

# 只重启 Vue 前端
docker compose restart frontend
```

### 7.3 验证部署

```bash
# 检查所有服务状态
docker compose ps

# 查看特定服务状态
docker compose ps backend
docker compose ps frontend-react

# 访问测试
curl http://localhost:88/api/models  # React 前端 API
curl http://localhost/api/models     # Vue 前端 API (Nginx 代理)
```

### 7.4 常见问题

**Q: 修改后服务未更新？**  
A: 确保使用了 `--no-cache` 重新构建：`docker compose build --no-cache`

**Q: 容器启动失败？**  
A: 查看日志：`docker compose logs -f backend`

**Q: 端口冲突？**  
A: 停止其他占用端口的进程，或修改 `docker-compose.yml` 中的端口映射

---

**最后更新**: 2026-02-28  
**适用版本**: LLMGateway v1.0+
