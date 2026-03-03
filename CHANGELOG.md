# 更新日志

所有值得注意的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/)，
并遵循 [Semantic Versioning](https://semver.org/)。

## [1.3.0] - 2026-03-03

### 新增
- 🔄 **Auto 模型模式** - 新增 `auto` 模型选项，支持自动切换至最高优先级可用模型
- 🎯 **智能负载均衡** - 网关支持不传 model 参数时自动使用最高优先级模型
- 📦 **新增厂商支持**:
  - 腾讯混元
  - 字节豆包
  - 零一万物
  - 阶跃星辰

### 改进
- 🔧 **自动重试机制** - 模型失败时自动切换下一个可用模型，提升请求成功率
- ✅ **响应验证** - 空响应时自动切换，确保请求可靠性
- 🔄 **完善自动切换逻辑** - 无模型时返回空列表，模型失败时自动重试下一个

### 修复
- 🐛 修复 MiniMax 模型网关连接问题
- 🐛 修复 auto 模式只选择已连通模型的逻辑

### 优化
- 🎨 更新 React 前端厂商配置模板
- 🧹 清理冗余配置文件 (docker-compose.fixed.yml)

### 文档
- 📝 更新 Docker 部署与更新指南
- 📚 完善厂商配置说明文档

## [1.2.0] - 2026-03-01
## [1.2.0] - 2026-03-01

### 新增
- 🔄 **统一厂商配置** - 新增 `config/vendors.json` 统一管理 24+ 厂商模型配置
- 🎯 **模型能力自动检测** - 自动识别 Vision/Text/Audio 能力和上下文长度
- 📦 **Coding Plan 支持** - 支持阿里云百炼、MiniMax、智谱、火山方舟等厂商的编程套餐
- 🤖 **新增厂商**：
  - 国际: Mistral AI, Groq, Perplexity, xAI Grok, Together AI, Cohere
  - 国内: 深度求索(DeepSeek), 月之暗面(Kimi), 阶跃星辰, 腾讯混元, 字节豆包, 零一万物
  - 本地: Ollama, vLLM, LM Studio

### API 增强
- ✅ `GET /api/models` 返回模型能力（vision/text/context_length）
- ✅ `GET /api/coding-plans` 获取 Coding Plan 套餐信息
- ✅ `GET /api/coding-plans/packages` 获取套餐价格信息
- ✅ `POST /api/cron/sync-quota` 定时同步配额
- ✅ `GET/POST/PUT/DELETE /api/coding-plans/configs` Coding Plan 配置 CRUD

### 前端优化
- 🎨 日志详情页美化（JSON 语法高亮、默认展开）
- 📋 新增复制功能
- 🔄 模型配置模板同步更新

### 文档更新
- 📝 AGENTS.md 中文版开发指南
- 📚 厂商配置文档完善

## [1.0.0] - 2026-02-03

### 新增
- 🚀 初始版本发布
- 🔄 标准化 OpenAI 兼容网关核心
- 📦 支持 10+ 主流大模型厂商：
  - OpenAI (GPT-3.5/4o)
  - Claude (Anthropic)
  - Google Gemini
  - 智谱清言 (GLM)
  - 通义千问 (Qwen)
  - 讯飞星火 (Spark)
  - 字节豆包 (Doubao)
  - Mistral
  - Groq (Llama 3)
  - Perplexity
- 📊 额度监控与统计面板
- 🔐 AES-256 API Key 加密存储
- 🔄 自动切换策略
- 🐳 Docker Compose 一键部署
- 🛠️ Agent 工具一键适配：
  - OpenClaw
  - Claude Code
  - Cursor
  - ChatGPT Next Web
- 📈 前端管理平台 (Vue3 + Element Plus)：
  - 仪表盘
  - 模型配置
  - 额度监控
  - 系统配置
  - 日志管理
  - Agent 适配指南
- ✅ 39 个单元测试 (100% 通过)

### 已知问题
- 部分厂商不支持自动额度同步
- 前端 E2E 测试待完善

## 计划功能
- [ ] 用户认证系统
- [ ] 团队/多用户支持
- [ ] 插件市场
- [ ] 本地模型集成 (Ollama)
- [ ] 负载均衡
- [ ] 邮件告警通知
