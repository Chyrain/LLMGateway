# 四层日志追踪系统 - 实现总结

## 实现完成情况

### 已创建文件

| 文件 | 说明 |
|-----|------|
| `backend/services/debug_logger.py` | 四层日志核心模块（新建） |
| `test_four_layer_log.py` | 测试脚本（新建） |
| `FOUR_LAYER_LOG.md` | 使用说明文档（新建） |

### 已修改文件

| 文件 | 修改内容 |
|-----|---------|
| `backend/routers/gateway.py` | 添加 L1 日志记录（入口原始请求） |
| `backend/services/gateway_core.py` | 添加 L2/L3/L4 日志记录（HTTP 请求转发） |
| `backend/services/sdk_gateway.py` | 添加 L2/L3 日志记录（SDK 请求转发） |
| `.env.example` | 添加调试日志配置项 |
| `CHANGELOG.md` | 记录本次更新 |

## 四层日志定义

| 层级 | 名称 | 记录位置 | 数据内容 |
|-----|------|---------|---------|
| L1 | 原始输入 ← Client | `gateway.py:chat_completions` | 客户端原始请求 |
| L2 | 网关输出 → Vendor | `gateway_core.py` / `sdk_gateway.py` | 转发给厂商的请求 |
| L3 | 厂商响应 ← Vendor | `gateway_core.py` / `sdk_gateway.py` | 厂商原始响应 |
| L4 | 最终输出 → Client | `gateway_core.py:_standardize_response` 后 | 标准化后的响应 |

## 核心功能

### 1. 调试日志模块 (`debug_logger.py`)

- `log_four_layers()` - 记录完整四层日志
- `log_layer()` - 记录单层日志
- `log_request_start()` - L1 便捷函数
- `log_gateway_forward()` - L2 便捷函数
- `log_vendor_response()` - L3 便捷函数
- `log_final_output()` - L4 便捷函数
- `debug_logger` - 装饰器自动记录输入输出

### 2. 配置选项

```bash
# 是否启用调试日志 (true/false)
DEBUG_LOG_ENABLED=false

# 日志层级过滤 (all / input / output / none)
DEBUG_LOG_LAYERS=all

# 单个字段最大日志长度
DEBUG_LOG_MAX_LENGTH=5000

# 日志输出方式 (console / file / both)
DEBUG_LOG_OUTPUT=console

# 日志文件路径
DEBUG_LOG_FILE=./data/debug_requests.log
```

### 3. 字段透传验证

自动检测以下字段是否正确透传：
- `thinking` 字段 L1→L2
- `reasoning_content` 字段 L3→L4
- `tool_calls` 字段 L3→L4

## 使用流程

### 1. 启用调试日志

```bash
# 方法一：修改 .env 文件
echo "DEBUG_LOG_ENABLED=true" >> .env
echo "DEBUG_LOG_OUTPUT=console" >> .env

# 方法二：环境变量
export DEBUG_LOG_ENABLED=true
```

### 2. 启动网关

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### 3. 发送测试请求

```bash
python test_four_layer_log.py
```

### 4. 查看日志

- 控制台：查看格式化日志
- 文件：`./data/debug_requests.log`

## 日志输出示例

```
═══════════════════════════════════════════════════════════
[4-LAYER LOG] Request ID: a1b2c3d4  Model: MiniMax-M2.5
═══════════════════════════════════════════════════════════

【L1 原始输入】← Client
{
  "model": "auto",
  "messages": [...],
  "thinking": {"type": "enabled", "budget_tokens": 1000}
}

【L2 网关输出】→ Vendor API
{
  "model": "MiniMax-M2.5",
  "messages": [...],
  "thinking": {"type": "enabled", "budget_tokens": 1000}
}

【L3 厂商响应】← Vendor API
{
  "choices": [...],
  "usage": {...}
}

【L4 最终输出】→ Client
{
  "id": "chatcmpl-xxx",
  "choices": [...],
  "usage": {...}
}

═══════════════════════════════════════════════════════════
[字段对比] L1→L2: thinking 字段 ✓ 已透传
           L3→L4: reasoning_content 字段 ✓ 已保留
═══════════════════════════════════════════════════════════
```

## 测试验证

运行测试脚本验证功能：

```bash
# 确保网关运行
uvicorn main:app --reload --port 8080

# 运行测试
python test_four_layer_log.py
```

## 性能说明

- 默认关闭 (`DEBUG_LOG_ENABLED=false`) 无性能影响
- 启用时会有轻微开销（JSON 序列化和格式化）
- 建议生产环境关闭，开发/调试时启用

## 后续优化建议

1. **异步日志** - 使用异步队列避免阻塞主流程
2. **采样率** - 支持日志采样（如只记录 10% 请求）
3. **敏感信息过滤** - 自动过滤 API Key 等敏感字段
4. **日志级别** - 支持更细粒度的日志级别控制
5. **分布式追踪** - 支持跨服务追踪（集成 OpenTelemetry）

## 相关文档

- `FOUR_LAYER_LOG.md` - 详细使用说明
- `backend/services/debug_logger.py` - 源代码及注释
- `.env.example` - 配置示例

## 实现日期

2026-03-15
