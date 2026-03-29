# 国内大模型厂商 API 接口配置清单

本文档列出了所有国内大模型厂商的标准 API 和 Coding Plan API 地址配置，用于灵模网关自动匹配。

## 配置说明

网关支持根据 API Key 前缀自动选择正确的 API 地址。当添加模型时，如果未手动指定 `api_base`，系统会根据 API Key 自动匹配。

## 厂商配置清单

### 1. 阿里通义千问 / 阿里百炼

| 模式 | API Base | API Key 前缀 | 说明 |
|------|----------|-------------|------|
| 标准 API | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `sk-` | 按 Token 计费 |
| Coding Plan | `https://coding.dashscope.aliyuncs.com/v1` | `sk-sp-` | 通义灵码套餐 |

```json
{
  "vendor": "qwen",
  "api_base_rules": [
    {"api_key_prefix": "sk-sp-", "api_base": "https://coding.dashscope.aliyuncs.com/v1"},
    {"api_key_prefix": "sk-", "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1"}
  ]
}
```

### 2. 智谱 AI (GLM)

| 模式 | API Base | API Key 前缀 | 说明 |
|------|----------|-------------|------|
| 标准 API | `https://open.bigmodel.cn/api/paas/v4` | - | 按 Token 计费 |
| Coding Plan | `https://open.bigmodel.cn/api/coding/paas/v4` | - | GLM Coding 套餐 |

```json
{
  "vendor": "zhipu",
  "api_base_rules": [
    {"match_pattern": "coding", "api_base": "https://open.bigmodel.cn/api/coding/paas/v4"},
    {"api_base": "https://open.bigmodel.cn/api/paas/v4"}
  ]
}
```

### 3. 深度求索 (DeepSeek)

| 模式 | API Base | API Key 前缀 | 说明 |
|------|----------|-------------|------|
| 标准 API | `https://api.deepseek.com` | `sk-` | 按 Token 计费 |

```json
{
  "vendor": "deepseek",
  "api_base": "https://api.deepseek.com"
}
```

### 4. 月之暗面 (Kimi)

| 模式 | API Base | API Key 前缀 | 说明 |
|------|----------|-------------|------|
| 标准 API | `https://api.moonshot.cn/v1` | `sk-` | 按 Token 计费 |

```json
{
  "vendor": "moonshot",
  "api_base": "https://api.moonshot.cn/v1"
}
```

### 5. 百度智能云 (千帆)

| 模式 | API Base | 认证方式 | 说明 |
|------|----------|---------|------|
| 标准 API | `https://qianfan.baidubce.com/v2` | OAuth 2.0 | 按 Token 计费 + 资源包 |

```json
{
  "vendor": "baidu_qianfan",
  "api_base": "https://qianfan.baidubce.com/v2",
  "auth_method": "oauth2"
}
```

### 6. 腾讯混元

| 模式 | API Base | 认证方式 | 说明 |
|------|----------|---------|------|
| 标准 API | `https://api.hunyuan.cloud.tencent.com/v1` | TC3-HMAC-SHA256 | 按 Token 计费 |

```json
{
  "vendor": "hunyuan",
  "api_base": "https://api.hunyuan.cloud.tencent.com/v1",
  "auth_method": "tc3-hmac-sha256"
}
```

### 7. 字节豆包 (火山方舟)

| 模式 | API Base | API Key 前缀 | 说明 |
|------|----------|-------------|------|
| 标准 API | `https://ark.cn-beijing.volces.com/api/v3` | - | 按 Token 计费 |

```json
{
  "vendor": "doubao",
  "api_base": "https://ark.cn-beijing.volces.com/api/v3"
}
```

### 8. MiniMax

| 模式 | API Base | API Key 前缀 | 说明 |
|------|----------|-------------|------|
| 标准 API | `https://api.minimaxi.com/v1` | - | 按 Token 计费 + 套餐 |

```json
{
  "vendor": "minimax",
  "api_base": "https://api.minimaxi.com/v1"
}
```

### 9. 讯飞星火

| 模式 | API Base | 认证方式 | 说明 |
|------|----------|---------|------|
| 标准 API | `https://spark-api-open.xf-yun.com/v1` | APIKey/APISecret | 按 Token 计费 |

```json
{
  "vendor": "spark",
  "api_base": "https://spark-api-open.xf-yun.com/v1",
  "auth_method": "jwt-signature"
}
```

### 10. 阶跃星辰

| 模式 | API Base | API Key 前缀 | 说明 |
|------|----------|-------------|------|
| 标准 API | `https://api.stepfun.com/v1` | - | 按 Token 计费 |

```json
{
  "vendor": "stepfun",
  "api_base": "https://api.stepfun.com/v1"
}
```

### 11. 零一万物

| 模式 | API Base | API Key 前缀 | 说明 |
|------|----------|-------------|------|
| 标准 API | `https://api.lingyiwanwu.com/v1` | - | 按 Token 计费 |

```json
{
  "vendor": "yi",
  "api_base": "https://api.lingyiwanwu.com/v1"
}
```

## 汇总表格

| 厂商 | 标准 API Key 前缀 | Coding Plan Key 前缀 | API 地址数量 | 自动匹配支持 |
|------|------------------|---------------------|-------------|-------------|
| 阿里通义千问 | `sk-` | `sk-sp-` | 2 | ✅ |
| 智谱 AI | - | - | 2 | ✅ |
| 深度求索 | `sk-` | N/A | 1 | ✅ |
| 月之暗面 | `sk-` | N/A | 1 | ✅ |
| 百度千帆 | OAuth | N/A | 1 | ⚠️ 需 OAuth |
| 腾讯混元 | SecretId | N/A | 1 | ⚠️ 需签名 |
| 字节豆包 | - | N/A | 1 | ✅ |
| MiniMax | - | N/A | 1 | ✅ |
| 讯飞星火 | APIKey | N/A | 1 | ⚠️ 需签名 |
| 阶跃星辰 | - | N/A | 1 | ✅ |
| 零一万物 | - | N/A | 1 | ✅ |

## 使用说明

### 添加模型时自动匹配 API 地址

当你通过 API 添加模型时，如果不指定 `api_base`，系统会自动根据 API Key 前缀匹配：

```bash
curl -X POST "http://localhost:8000/api/models" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor": "qwen",
    "model_name": "qwen3.5-plus",
    "api_key": "sk-sp-xxxxxxxxxx"  # 自动使用 Coding Plan API 地址
  }'
```

### 手动指定 API 地址

如果需要覆盖自动匹配，可以手动指定 `api_base`：

```bash
curl -X POST "http://localhost:8000/api/models" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor": "qwen",
    "model_name": "qwen3.5-plus",
    "api_key": "sk-sp-xxxxxxxxxx",
    "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1"
  }'
```

## 更新记录

- **2026-03-29 (v1.5.0)**: 双格式厂商动态端点路由
  - 支持双格式的厂商 (qwen/bailian) 根据请求端点自动路由到对应的 API
  - OpenAI 格式请求 → 使用 `api_spec=openai` 的模型配置
  - Anthropic 格式请求 → 使用 `api_spec=anthropic` 的模型配置
  - 新增阿里百炼原生 Anthropic 格式支持：`https://coding.dashscope.aliyuncs.com/apps/anthropic`

- **2026-03-28**: 初始版本，添加 11 个国内厂商配置
  - 支持根据 API Key 前缀自动匹配 API 地址
  - 支持 Coding Plan 和标准 API 两种模式
