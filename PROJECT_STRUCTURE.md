# 灵模网关 - LLM Free Quota Gateway

## 📦 项目结构

```
LLMGateway/
├── README.md                    # 项目说明文档
├── CHANGELOG.md                 # 更新日志
├── docker-compose.yml           # Docker部署配置
├── backend/                     # 后端服务
│   ├── main.py                  # FastAPI主入口
│   ├── requirements.txt         # Python依赖
│   ├── config/                  # 配置模块
│   │   ├── database.py          # 数据库配置
│   │   ├── encryption.py        # 加密工具
│   │   ├── vendors.json         # 统一厂商模型配置 ★新增
│   │   └── vendor_config.py     # 厂商配置加载器 ★新增
│   ├── models/                  # 数据模型
│   │   ├── model_config.py      # 模型配置表
│   │   ├── coding_plan.py       # Coding Plan配置表 ★新增
│   │   ├── quota_stat.py        # 额度统计表
│   │   ├── system_config.py     # 系统配置表
│   │   └── operation_log.py     # 操作日志表
│   ├── routers/                 # API路由
│   │   ├── gateway.py           # 网关路由
│   │   ├── quota.py             # 配额路由
│   │   ├── cron.py              # 定时任务路由 ★新增
│   │   └── coding_plan.py       # Coding Plan路由 ★新增
│   ├── services/                # 业务服务
│   │   ├── gateway_core.py      # 网关核心服务
│   │   ├── coding_plan_service.py # Coding Plan服务 ★新增
│   │   ├── quota_monitor.py     # 额度监控服务
│   │   └── model_switcher.py    # 模型切换服务
│   └── templates/               # 厂商模板
├── frontend-react/              # React前端项目 (端口88)
│   ├── package.json             # npm配置
│   ├── vite.config.js           # Vite配置
│   └── src/                     # React源码
│       ├── main.jsx             # 入口文件
│       ├── App.jsx              # 根组件
│       ├── router/              # 路由配置
│       ├── services/            # API接口
│       ├── pages/               # 页面组件
│       │   ├── ModelConfig.jsx  # 模型配置
│       │   ├── Logs.jsx         # 日志管理
│       │   └── ...
│       └── styles/              # 样式文件
├── frontend/                    # Vue前端项目 (端口80)
│   ├── package.json             # npm配置
│   ├── vite.config.js           # Vite配置
│   └── src/                     # Vue源码
├── docs/                        # 文档
│   ├── API.md                   # API文档
│   └── DEPLOY.md                # 部署文档
└── data/                        # 数据目录
```

## 🚀 快速开始

### Docker部署（推荐）

```bash
# 克隆项目
git clone https://github.com/chyrain/LLMGateway.git
cd LLMGateway

# 启动服务
docker-compose up -d

# 访问管理平台
# React 前端: http://localhost:88
# Vue 前端: http://localhost:80
# API 文档: http://localhost:8000/docs
```

### 本地开发

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端（新终端）
cd frontend-react
npm install
npm run dev
```

## 📖 使用流程

1. **登录管理平台** (`http://localhost:88`)
2. **添加模型配置**
   - 进入「模型配置」页面
   - 选择厂商模板（支持24+厂商）
   - 填入API Key
   - 测试连通性后保存
3. **配置 Coding Plan**（可选）
   - 进入「Coding Plan」页面
   - 添加套餐配置
   - 同步配额使用情况
4. **配置自动切换**
   - 进入「额度监控」页面
   - 设置切换阈值
   - 调整模型优先级

## 🔧 核心功能

| 功能 | 说明 |
|-----|------|
| 多模型管理 | 支持24+厂商，内置预配置模板 |
| 统一配置 | `vendors.json` 统一管理厂商模型配置 |
| 模型能力检测 | 自动识别 Vision/Text/Audio 能力 |
| Coding Plan | 支持编程套餐管理和配额同步 |
| 自动切换 | 额度耗尽自动切换，无感知续跑 |
| 实时监控 | 额度消耗实时统计，多渠道告警 |
| 安全加密 | Fernet 加密存储 API Key |

## 📚 支持的厂商

### 国际厂商
OpenAI, Anthropic Claude, Google Gemini, Mistral AI, Groq, Perplexity, xAI Grok

### 国内厂商
通义千问(含灵码Coding Plan), 智谱AI, 深度求索, 月之暗面Kimi, MiniMax, 讯飞星火, 腾讯混元, 字节豆包, 零一万物, 阶跃星辰

### 本地模型
Ollama, vLLM, LM Studio

## 🐳 Docker命令

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 更新镜像
docker-compose pull
docker-compose up -d
```

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request