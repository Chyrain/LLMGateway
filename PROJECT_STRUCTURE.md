# 灵模网关 - LLM Free Quota Gateway

## 📦 项目结构

```
LLMGateway/
├── README.md                    # 项目说明文档
├── docker-compose.yml           # Docker部署配置
├── backend/                     # 后端服务
│   ├── main.py                  # FastAPI主入口
│   ├── requirements.txt         # Python依赖
│   ├── config/                  # 配置模块
│   │   ├── database.py          # 数据库配置
│   │   └── encryption.py        # 加密工具
│   ├── models/                  # 数据模型
│   │   ├── model_config.py      # 模型配置表
│   │   ├── quota_stat.py        # 额度统计表
│   │   ├── system_config.py     # 系统配置表
│   │   └── operation_log.py     # 操作日志表
│   ├── routers/                 # API路由
│   ├── services/                # 业务服务
│   │   ├── gateway_core.py      # 网关核心服务
│   │   ├── quota_monitor.py     # 额度监控服务
│   │   └── model_switcher.py    # 模型切换服务
│   └── templates/               # 厂商模板
├── frontend/                    # 前端项目
│   ├── package.json             # npm配置
│   ├── vite.config.js           # Vite配置
│   └── src/                     # Vue源码
│       ├── main.js              # 入口文件
│       ├── App.vue              # 根组件
│       ├── router/              # 路由配置
│       ├── api/                 # API接口
│       ├── views/               # 页面组件
│       └── styles/              # 样式文件
├── docs/                        # 文档
│   ├── AGENT_GUIDE.md           # Agent适配指南
│   ├── API.md                   # API文档
│   └── DEPLOY.md                # 部署文档
├── scripts/                     # 工具脚本
│   ├── openclaw-adapter.sh      # OpenClaw适配脚本
│   └── claude-code-adapter.bat  # Claude Code适配脚本
└── data/                        # 数据目录
```

## 🚀 快速开始

### Docker部署（推荐）

```bash
# 克隆项目
git clone https://github.com/your-repo/LLMGateway.git
cd LLMGateway

# 启动服务
docker-compose up -d

# 访问管理平台
# http://localhost:80
# 默认账号: admin/admin123
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
cd frontend
npm install
npm run dev
```

## 📖 使用流程

1. **登录管理平台** (`http://localhost:80`)
2. **添加模型配置**
   - 进入「模型配置」页面
   - 选择厂商模板（如OpenAI、智谱清言）
   - 填入API Key
   - 测试连通性后保存
3. **配置自动切换**
   - 进入「额度监控」页面
   - 设置切换阈值（默认99%）
   - 调整模型优先级
4. **对接Agent工具**
   - 参考 `docs/AGENT_GUIDE.md`
   - 一键对接OpenClaw/Claude Code/Cursor

## 🔧 核心功能

| 功能 | 说明 |
|-----|------|
| 多模型管理 | 支持15+厂商，内置预配置模板 |
| 自动切换 | 额度耗尽自动切换，无感知续跑 |
| 实时监控 | 额度消耗实时统计，多渠道告警 |
| 安全加密 | AES-256加密存储API Key |
| 工具适配 | OpenClaw/Claude Code/Cursor一键对接 |

## 📚 文档链接

- [快速开始](README.md)
- [Agent适配指南](docs/AGENT_GUIDE.md)
- [API文档](docs/API.md)
- [部署文档](docs/DEPLOY.md)

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

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request
