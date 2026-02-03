# Agent工具适配指南

本文档介绍如何将主流AI Agent工具对接灵模网关，实现免费额度的自动切换。

## 目录

- [OpenClaw](#1-openclaw)
- [Claude Code](#2-claude-code)
- [Cursor](#3-cursor)
- [ChatGPT Next Web](#4-chatgpt-next-web)
- [通用配置](#5-通用配置)

---

## 1. OpenClaw

### 方式一：脚本自动适配（推荐）

```bash
# 进入OpenClaw目录
cd /path/to/openclaw

# 下载并运行适配脚本
curl -O https://your-gateway-url/scripts/openclaw-adapter.sh
chmod +x openclaw-adapter.sh
./openclaw-adapter.sh
```

### 方式二：手动配置

修改 `config.yaml` 文件：

```yaml
model:
  provider: openai                    # 固定为openai
  name: gpt-3.5-turbo                 # 网关统一接收
  base_url: http://你的网关IP:8080/v1 # 替换为你的网关地址
  api_key: gateway_123456             # 网关的通用密钥
  temperature: 0.7
  max_tokens: 2048
```

### 验证对接

启动OpenClaw后，在Web界面输入：
```
你好，告诉我你当前的模型名称
```

网关会返回当前使用的大模型名称，表示对接成功。

---

## 2. Claude Code

### 方式一：Windows脚本

```batch
# 下载并运行适配脚本
claude-code-adapter.bat
```

### 方式二：手动配置

#### 临时配置（当前终端有效）

```bash
# Mac/Linux
export ANTHROPIC_API_KEY=gateway_123456
export ANTHROPIC_API_BASE=http://你的网关IP:8080/v1
claude

# Windows PowerShell
$env:ANTHROPIC_API_KEY="gateway_123456"
$env:ANTHROPIC_API_BASE="http://你的网关IP:8080/v1"
claude
```

#### 永久配置（所有终端有效）

```bash
# Mac/Linux (zsh)
echo 'export ANTHROPIC_API_KEY=gateway_123456' >> ~/.zshrc
echo 'export ANTHROPIC_API_BASE=http://你的网关IP:8080/v1' >> ~/.zshrc
source ~/.zshrc

# Windows
setx ANTHROPIC_API_KEY "gateway_123456"
setx ANTHROPIC_API_BASE "http://你的网关IP:8080/v1"
```

### 验证对接

启动Claude Code后，输入：
```
用Python写一个hello world，告诉我你当前使用的大模型
```

验证是否能正常生成代码并返回模型名称。

---

## 3. Cursor

### 配置步骤

1. 打开Cursor，点击顶部菜单 `Settings` → `Preferences` → `Cursor` → `Model`

2. 关闭 `Use Default Model API`

3. 配置以下参数：
   - **Custom API Base**: `http://你的网关IP:8080/v1`
   - **Custom API Key**: `gateway_123456`

4. 点击 `Save` 保存

### 验证对接

在Cursor中选中任意代码，右键选择 `Ask Cursor`，输入：
```
解释这段代码
```

验证是否能正常返回结果，且网关日志中能看到请求记录。

---

## 4. ChatGPT Next Web

### 配置步骤

1. 打开ChatGPT Next Web设置页面
2. 找到 `API Key` 设置项
3. 输入灵模网关的通用密钥：`gateway_123456`
4. 找到 `API Base URL` 设置项
5. 输入：`http://你的网关IP:8080/v1`
6. 保存设置

---

## 5. 通用配置

### 环境变量配置

| 工具 | 环境变量 | 说明 |
|-----|---------|------|
| Claude Code | `ANTHROPIC_API_BASE` | 网关地址 |
| Claude Code | `ANTHROPIC_API_KEY` | 网关密钥 |
| OpenAI兼容工具 | `OPENAI_API_BASE` | 网关地址 |
| OpenAI兼容工具 | `OPENAI_API_KEY` | 网关密钥 |

### 配置文件配置

```yaml
# OpenAI兼容格式
{
  "base_url": "http://你的网关IP:8080/v1",
  "api_key": "gateway_123456"
}
```

### 网关配置参数

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| 网关地址 | `http://localhost:8080` | 网关服务地址 |
| API路径 | `/v1/chat/completions` | OpenAI兼容接口路径 |
| API Key | `gateway_123456` | 网关通用密钥 |

---

## 常见问题

### Q1: 对接后提示认证失败

**原因**: API Key配置错误

**解决**:
1. 检查网关是否启动
2. 确认API Key是否正确（区分大小写）
3. 检查网关地址是否可访问

### Q2: 请求返回501错误

**原因**: 网关无可用模型

**解决**:
1. 登录管理平台
2. 进入「模型配置」页面
3. 至少添加并启用一个模型

### Q3: 切换模型后工具报错

**原因**: 工具缓存了旧的模型配置

**解决**:
1. 重启工具
2. 清除工具缓存
3. 重新发起请求

---

## 联系支持

如遇到问题，请：
1. 查看网关日志：`docker-compose logs -f backend`
2. 在GitHub提交Issue
3. 发送邮件到 support@llmgateway.dev
