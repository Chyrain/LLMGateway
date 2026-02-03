# 更新日志

所有值得注意的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/)，
并遵循 [Semantic Versioning](https://semver.org/)。

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
