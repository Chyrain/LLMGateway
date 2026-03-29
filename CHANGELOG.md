# 更新日志

所有值得注意的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/)，
并遵循 [Semantic Versioning](https://semver.org/)。

## [1.5.0] - 2026-03-29

### 新增
- ✨ **双格式厂商动态端点路由** - 根据请求端点类型自动选择正确的模型配置
  - 支持双格式的厂商 (qwen/bailian) 根据请求端点自动路由到对应的 API
  - OpenAI 格式请求 → 使用 `api_spec=openai` 的模型配置 (api_base + api_path)
  - Anthropic 格式请求 → 使用 `api_spec=anthropic` 的模型配置 (api_base + api_path)
  - 直接使用模型配置的 API Base 和 API Path，不做动态修改

### 修复
- 🐛 **双格式厂商模型选择逻辑** - 修复指定模型时未正确选择对应 api_spec 记录的问题
  - 当用户指定模型名称时，根据请求端点类型查找匹配 api_spec 的模型记录
  - 从数据库模型配置中正确获取 api_base 和 api_path
- 🐛 **/v1/messages 端点路由** - 修复 Anthropic 端点的模型配置选择逻辑
- 🐛 **/v1/chat/completions 端点路由** - 修复 OpenAI 端点的模型配置选择逻辑

### 修改
- 🔧 `backend/routers/gateway.py` - 为 `/v1/chat/completions` 和 `/v1/messages` 端点添加模型配置选择逻辑
  - 检查厂商是否支持双格式 (`vendor_supports_both`)
  - 根据请求端点类型查找匹配 api_spec 的模型记录
  - 使用模型记录的 api_base 和 api_path 组合成完整请求地址

## [1.4.9] - 2026-03-29

### 修复
- 🔧 **百炼 Anthropic 原生支持** - 修正阿里百炼平台的 Anthropic 格式支持方式
  - 百炼平台原生支持 Anthropic 格式，不需要转换
  - 更新 `anthropic_compat_base` 为 `https://coding.dashscope.aliyuncs.com/apps/anthropic`
  - `api_spec_support` 改为 `["openai", "anthropic"]`（原生支持两种格式）
  - `anthropic_via_conversion` 改为 `false`（不使用转换模式）
  - Anthropic 格式请求直接透传到百炼 API，保持 tools 等参数原样

### 修改
- 📝 **vendors_api_base_rules.json** - 更新 qwen 和 bailian 厂商配置
  - Anthropic 请求使用正确的 Base URL: `/apps/anthropic`
  - tools/tool_choice 等参数原样透传，不做转换

## [1.4.8] - 2026-03-28

### 新增
- ✨ **连通性测试自动识别 API 格式** - 根据 API Path 自动判断使用 OpenAI 或 Anthropic 格式
  - 包含 `/messages` 或 `anthropic` 的路径使用 Anthropic 格式请求
  - 其他路径使用 OpenAI 格式请求
  - 返回数据中包含实际请求的 URL 便于调试

### 修复
- 🐛 **Anthropic tools 格式转换** - 修复 Anthropic 转 OpenAI 模式时 tools 参数格式错误
  - 新增 `_convert_anthropic_tools_to_openai()` 函数
  - 将 Anthropic 格式的 `input_schema` 转换为 OpenAI 格式的 `parameters`
  - 将 Anthropic 格式的 `tool_choice` 转换为 OpenAI 格式
- 🐛 **thinking 参数兼容性问题** - 修复百炼等厂商不支持 thinking 参数导致的 API 错误
  - 从 `_clean_openai_request` 允许列表中移除 `thinking` 字段
  - 在网关路由中自动移除发送给 qwen/bailian/zhipu/minimax 的 `thinking` 参数
  - 仅 DeepSeek R1 等部分厂商支持 `thinking` 参数
- 🐛 **转换模式 tool_calls None 错误** - 修复 OpenAI 响应中 tool_calls 为 None 时的转换错误
  - 使用 `message.get("tool_calls") or []` 确保始终为可迭代对象

### 修改
- 🔧 **百炼 API Base 地址** - 更新为 `https://coding.dashscope.aliyuncs.com/v1`
  - 支持 `sk-sp-` 前缀的通义灵码 Coding Plan API Key
  - 同时支持 OpenAI 和 Anthropic 两种格式请求

### 验证
- ✅ **基础对话测试** - 单轮和多轮对话正常
- ✅ **流式输出测试** - SSE 格式事件完整 (message_start/content_block_delta/message_delta/message_stop)
- ✅ **API Key 自动匹配** - `sk-sp-` 前缀自动使用 Coding Plan API
- ✅ **Kimi K2.5 连通性测试** - 百炼 Kimi K2.5 模型 Anthropic 格式请求完整可用
  - 连通性测试自动识别 `/messages` 路径使用 Anthropic 格式
  - 响应正确转换为 Anthropic 格式返回（含 stop_reason、type、content 数组）

## [1.4.7] - 2026-03-28

### 修复
- 🐛 **Anthropic 格式兼容模式实现** - 实现国内厂商 Anthropic 格式请求的转换模式
  -  `/v1/messages` 端点接收 Anthropic 格式请求后，自动转换为 OpenAI 格式
  - 使用 OpenAI SDK 将请求转发至厂商 API（阿里通义千问、阿里百炼、智谱 AI、MiniMax）
  - 将 OpenAI 格式响应转换回 Anthropic 格式返回给客户端
  - 支持完整的 Anthropic Messages API 兼容体验（包括 tool_use）

### 新增
- ✨ **Anthropic 转换模式配置** - 新增 `anthropic_via_conversion` 配置项
  - 用于标识厂商是否支持通过转换模式处理 Anthropic 格式请求
  - 与 `api_spec_support: ["openai"]` 配合使用，区分原生支持和转换支持
- ✨ **Anthropic 格式转换函数** - 新增 `_convert_openai_to_anthropic_response` 和 `_convert_openai_chunk_to_anthropic_event`
  - 支持 OpenAI 响应转 Anthropic 格式（非流式和流式）
  - 支持 tool_calls 到 tool_use 的转换
  - 支持 finish_reason 到 stop_reason 的映射

### 修改
- 🔧 `backend/config/vendors_api_base_rules.json` - 更新厂商配置
  - 所有国内厂商 `api_spec_support` 改为 `["openai"]`（仅支持 OpenAI 格式）
  - 添加 `anthropic_via_conversion: true` 标识支持转换模式
  - 保留 `anthropic_compat_base` 用于指定 API Base 地址
- 🔧 `backend/config/vendor_config.py` - 新增 `supports_anthropic_via_conversion()` 函数
- 🔧 `backend/routers/gateway.py` - 更新 `/v1/messages` 端点处理逻辑
  - 根据 `anthropic_via_conversion` 配置决定使用转换模式或原生模式
  - 转换模式：Anthropic → OpenAI → 厂商 API → OpenAI → Anthropic
  - 原生模式：直接使用 Anthropic SDK 转发（适用于未来支持原生 Anthropic 的厂商）

### 技术实现
- 转换模式流程：
  1. L1: 接收 Anthropic 格式请求（`/v1/messages`）
  2. 转换：Anthropic messages → OpenAI messages（system 作为 system role）
  3. L2: 使用 OpenAI SDK 发送至厂商 API
  4. L3: 接收厂商 OpenAI 格式响应
  5. 转换：OpenAI response → Anthropic message
  6. L4: 返回 Anthropic 格式响应给客户端
- 流式转换：
  - OpenAI chunk → Anthropic event 实时转换
  - 支持 message_start, content_block_start, content_block_delta, message_delta, message_stop 事件
  - 支持 tool_use 事件的流式传输

## [1.4.5] - 2026-03-28

### 修复
- 🐛 **Anthropic 格式兼容模式** - 修正国内厂商 Anthropic 兼容配置，改为使用转换模式而非原生透传
  - 国内厂商（阿里通义千问、阿里百炼、智谱 AI、MiniMax）实际仅支持 OpenAI 兼容接口
  - `/v1/messages` 端点接收 Anthropic 格式请求后，自动转换为 OpenAI 格式转发
  - 响应时将 OpenAI 格式的 `tool_calls` 转换为 Anthropic 格式的 `tool_use`
  - 支持完整的 Anthropic Messages API 兼容体验

### 技术实现
- 更新 `vendors_api_base_rules.json` 配置：
  - 所有国内厂商 `api_spec_support` 改为 `["openai"]`
  - 移除无效的 `anthropic_compat_base` 配置
- `/v1/messages` 端点逻辑：
  - 检查厂商 `api_spec_support` 配置
  - 不支持 `anthropic` 时自动使用 OpenAI 格式转换兼容
  - 保持完整的 tool_use 转换和响应构建

## [1.4.4] - 2026-03-28

### 新增
- ✨ **国内厂商 API Base 自动匹配** - 支持根据 API Key 前缀和 plan_type 自动选择正确的 API 地址
  - 阿里通义千问：sk-sp- → Coding Plan, sk- → 标准 API
  - 智谱 AI：支持 coding plan_type → Coding Plan API
  - 新增 vendors_api_base_rules.json 统一管理配置
- 📄 **国内厂商 API 配置文档** - docs/domestic_vendors_api_config.md

### 支持厂商列表
| 厂商 | API Key 前缀 | plan_type | 自动匹配 |
|------|-------------|-----------|---------|
| 阿里通义千问 | sk-sp-/sk- | - | ✅ |
| 阿里百炼 | sk-sp-/sk- | - | ✅ |
| 智谱 AI | - | coding | ✅ |
| 深度求索 | sk- | - | ✅ |
| 月之暗面 | sk- | - | ✅ |
| 字节豆包 | - | - | ✅ |
| MiniMax | - | coding | ✅ |
| 讯飞星火 | - | - | ✅ |
| 腾讯混元 | - | - | ✅ |
| 百度千帆 | - | - | ✅ |
| 阶跃星辰 | - | - | ✅ |
| 零一万物 | - | - | ✅ |

## [1.4.3] - 2026-03-28

### 修复
- 🐛 **Anthropic 接口 tool_use 转换** - 修复 OpenAI 响应转换为 Anthropic 格式时 tool_calls 丢失
  - 添加 OpenAI tool_calls 到 Anthropic tool_use 的完整转换逻辑
  - 支持 tool_use 字段正确透传给 Claude Code 等客户端
- 🐛 **qwen thinking 模式 tool_choice 兼容** - 修复 qwen thinking 模式不支持 tool_choice 的问题
  - 自动检测并移除 thinking 模式下的 tool_choice 参数
  - 添加 tools、tool_choice、enable_thinking 参数透传
- 🐛 **MiniMax tool_call 解析增强** - 完善 struct Tool 和 XML 格式解析
  - 修复 struct Tool 格式的 skill_input 参数解析，支持 JSON 参数透传
  - 修复 XML 格式的 parameter 标签正则匹配，添加结束标签

## [1.4.2] - 2026-03-28

### 新增
- 📦 **阿里百炼厂商支持** - 新增 bailian 厂商模型配置
  - qwen3.5-plus, glm-5, kimi-k2.5, MiniMax-M2.5 等 8 个模型
  - 支持 Coding Plan API 配额同步

### 修复
- 🐛 **glm-5 模型配置冲突** - 禁用 ollama 厂商的 glm-5 配置，使用 bailian 厂商
- 🐛 **MiniMax tool_call 解析增强** - 完善 struct Tool 和 XML 格式解析
  - 修复 struct Tool 格式的 skill_input 参数解析，支持 JSON 参数透传
  - 修复 XML 格式的 parameter 标签正则匹配，添加结束标签
  - 添加完整的测试用例覆盖 (test_all_minimax.py)

## [1.4.1] - 2026-03-23

### 修复
- 🐛 **MiniMax tool_call 解析增强** - 完善 struct Tool 和 XML 格式解析
  - 修复 struct Tool 格式的 skill_input 参数解析，支持 JSON 参数透传
  - 修复 XML 格式的 parameter 标签正则匹配，添加结束标签
  - 添加完整的测试用例覆盖 (test_all_minimax.py)

## [1.4.0] - 2026-03-15

### 新增
- 📊 **四层日志追踪系统** - 完整的请求/响应数据流转追踪
  - L1 原始输入：客户端发出的原始 HTTP 请求
  - L2 网关输出：网关转发给厂商 API 的请求
  - L3 厂商响应：厂商 API 返回的原始响应
  - L4 最终输出：网关返回给客户端的响应
- 🔍 **字段透传验证** - 自动检测关键字段是否正确透传
  - `thinking` 字段 L1→L2 透传检测
  - `reasoning_content` 字段 L3→L4 保留检测
  - `tool_calls` 字段 L3→L4 保留检测
- 📝 **调试日志模块** - `backend/services/debug_logger.py`
  - 支持 JSON 格式化输出带缩进
  - 支持长度限制避免日志过大
  - 支持文件输出和控制台输出
- 📋 **测试脚本** - `test_four_layer_log.py` 验证日志功能
- 🔧 **MiniMax tool_call 格式转换** - 将 MiniMax 的 XML 格式 tool_call 转换为标准 OpenAI 格式
  - 支持解析 `<minimax:tool_call>` XML 格式
  - 自动转换为标准 `tool_calls` 数组
  - Claude Code 可正常识别并执行命令

### 修改
- 🔧 `backend/routers/gateway.py` - 添加 L1/L4 日志记录
- 🔧 `backend/services/gateway_core.py` - 添加 L2/L3/L4 日志记录和 MiniMax tool_call 解析
- 🔧 `backend/services/sdk_gateway.py` - 添加 L2/L3 日志记录 (OpenAI/Anthropic SDK)
- 📝 `.env.example` - 添加调试日志配置项

### 配置
- `DEBUG_LOG_ENABLED` - 是否启用调试日志
- `DEBUG_LOG_LAYERS` - 日志层级过滤 (all/input/output/none)
- `DEBUG_LOG_MAX_LENGTH` - 单个字段最大日志长度
- `DEBUG_LOG_OUTPUT` - 日志输出方式 (console/file/both)
- `DEBUG_LOG_FILE` - 日志文件路径

### 文档
- 📄 `FOUR_LAYER_LOG.md` - 四层日志使用说明文档

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
