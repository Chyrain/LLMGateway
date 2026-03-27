# 四层日志追踪系统使用说明

## 功能概述

四层日志追踪系统用于追踪请求/响应在网关处理过程中的完整数据流转，帮助调试和验证字段透传是否正确。

## 四层数据定义

| 层级 | 名称 | 描述 | 数据流向 |
|-----|------|------|---------|
| L1 | 原始输入 (Raw Input) | 客户端发出的原始 HTTP 请求 | ← Client |
| L2 | 网关输出 (Gateway Output) | 网关转发给厂商 API 的请求 | → Vendor |
| L3 | 厂商响应 (Vendor Response) | 厂商 API 返回的原始响应 | ← Vendor |
| L4 | 最终输出 (Final Output) | 网关返回给客户端的响应 | → Client |

## 启用调试日志

### 方法一：环境变量

在 `.env` 文件中添加：

```bash
# 启用调试日志
DEBUG_LOG_ENABLED=true

# 记录所有四层日志
DEBUG_LOG_LAYERS=all

# 输出到控制台
DEBUG_LOG_OUTPUT=console

# 单个字段最大长度
DEBUG_LOG_MAX_LENGTH=5000
```

### 方法二：运行时设置

```python
from services.debug_logger import set_config

set_config("enabled", True)
set_config("layers", "all")
set_config("output", "console")
set_config("max_length", 5000)
```

## 配置选项

| 配置项 | 可选值 | 默认值 | 说明 |
|-------|--------|--------|------|
| DEBUG_LOG_ENABLED | true/false | false | 是否启用调试日志 |
| DEBUG_LOG_LAYERS | all/input/output/none | all | 日志层级过滤 |
| DEBUG_LOG_MAX_LENGTH | 整数 | 5000 | 单个字段最大日志长度 |
| DEBUG_LOG_OUTPUT | console/file/both | console | 日志输出方式 |
| DEBUG_LOG_FILE | 文件路径 | ./data/debug_requests.log | 日志文件路径 |

## 日志输出示例

```
═══════════════════════════════════════════════════════════
[4-LAYER LOG] Request ID: a1b2c3d4  Model: MiniMax-M2.5  Vendor: minimax
═══════════════════════════════════════════════════════════

【L1 原始输入】← Client
{
  "model": "auto",
  "messages": [{"role": "user", "content": "你好"}],
  "thinking": {"type": "enabled", "budget_tokens": 1000},
  "max_tokens": 100
}

【L2 网关输出】→ Vendor API
{
  "model": "MiniMax-M2.5",
  "messages": [{"role": "user", "content": "你好"}],
  "thinking": {"type": "enabled", "budget_tokens": 1000},
  "max_tokens": 100
}

【L3 厂商响应】← Vendor API
{
  "choices": [{"message": {"content": "你好！有什么可以帮助你的？", "role": "assistant"}}],
  "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
}

【L4 最终输出】→ Client
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "choices": [{"message": {"content": "你好！有什么可以帮助你的？", "role": "assistant"}}],
  "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
}

═══════════════════════════════════════════════════════════
[字段对比] L1→L2: thinking 字段 ✓ 已透传
           L3→L4: reasoning_content 字段 ✓ 已保留
           L3→L4: tool_calls 字段 ✓ 已保留
═══════════════════════════════════════════════════════════
```

## 使用 API

### 记录完整四层日志

```python
from services.debug_logger import log_four_layers

log_four_layers(
    l1_raw_input=request_data,
    l2_gateway_output=mapped_request,
    l3_vendor_response=vendor_response,
    l4_final_output=standardized_response,
    request_id="a1b2c3d4",
    model="MiniMax-M2.5",
    vendor="minimax"
)
```

### 记录单层日志

```python
from services.debug_logger import log_layer

# L1 日志
log_layer("L1", request_data, context={"request_id": "a1b2c3d4", "model": "auto"})

# L2 日志
log_layer("L2", mapped_request, context={"request_id": "a1b2c3d4", "vendor": "minimax"})

# L3 日志
log_layer("L3", vendor_response, context={"request_id": "a1b2c3d4", "vendor": "minimax"})

# L4 日志
log_layer("L4", standardized_response, context={"request_id": "a1b2c3d4", "model": "MiniMax-M2.5"})
```

### 便捷函数

```python
from services.debug_logger import (
    log_request_start,      # L1
    log_gateway_forward,    # L2
    log_vendor_response,    # L3
    log_final_output        # L4
)

log_request_start(request_data, request_id="a1b2c3d4", model="auto")
log_gateway_forward(mapped_request, request_id="a1b2c3d4", vendor="minimax")
log_vendor_response(vendor_response, request_id="a1b2c3d4", vendor="minimax")
log_final_output(standardized_response, request_id="a1b2c3d4", model="MiniMax-M2.5")
```

### 装饰器

```python
from services.debug_logger import debug_logger

@debug_logger
async def my_function(request_data):
    # 自动记录输入输出日志
    return process(request_data)
```

## 验证方法

### 1. 启动网关

```bash
# 设置环境变量
export DEBUG_LOG_ENABLED=true
export DEBUG_LOG_OUTPUT=console

# 启动网关服务
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### 2. 发送测试请求

使用提供的测试脚本：

```bash
# 确保网关服务运行中
python test_four_layer_log.py
```

或使用 curl：

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer gtw_admin123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "你好"}],
    "thinking": {"type": "enabled", "budget_tokens": 1000}
  }'
```

### 3. 检查日志输出

- **控制台输出**：查看格式化的四层日志
- **文件输出**：查看 `./data/debug_requests.log` 文件

### 4. 验证字段透传

- 确认 L1→L2：`thinking` 字段是否保留
- 确认 L3→L4：`reasoning_content` 字段是否保留
- 确认 L3→L4：`tool_calls` 字段是否保留

## 已集成文件

| 文件 | 日志层级 | 说明 |
|-----|---------|------|
| `backend/routers/gateway.py` | L1, L4 | 网关入口和出口 |
| `backend/services/gateway_core.py` | L2, L3, L4 | HTTP 请求转发核心 |
| `backend/services/sdk_gateway.py` | L2, L3 | OpenAI/Anthropic SDK 转发 |

## 关闭调试日志

设置环境变量：

```bash
DEBUG_LOG_ENABLED=false
```

或在代码中：

```python
from services.debug_logger import set_config
set_config("enabled", False)
```

## 性能影响

- 调试日志启用时会增加一定的性能开销
- 主要体现在 JSON 序列化和格式化输出
- 建议在生产环境中关闭 (`DEBUG_LOG_ENABLED=false`)

## 故障排查

### 问题：日志没有输出

1. 检查 `DEBUG_LOG_ENABLED` 是否为 `true`
2. 检查 `DEBUG_LOG_LAYERS` 配置是否正确
3. 检查 `DEBUG_LOG_OUTPUT` 配置（console/file/both）

### 问题：日志文件没有创建

1. 确保目录存在：`mkdir -p ./data`
2. 检查文件写入权限
3. 确认 `DEBUG_LOG_FILE` 路径正确

### 问题：日志内容被截断

增加 `DEBUG_LOG_MAX_LENGTH` 值：

```bash
DEBUG_LOG_MAX_LENGTH=10000
```

## 相关文件

- `backend/services/debug_logger.py` - 四层日志核心模块
- `.env.example` - 环境变量配置示例
- `test_four_layer_log.py` - 测试脚本

## 更新日志

2026-03-15
- 初始版本发布
- 支持 L1-L4 四层日志记录
- 集成到 gateway.py、gateway_core.py、sdk_gateway.py
- 支持字段透传验证功能
