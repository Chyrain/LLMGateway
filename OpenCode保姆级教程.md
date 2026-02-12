# OpenCode 保姆级教程

> 📌 **什么是 OpenCode？**
> OpenCode 是一个开源的 AI 编程助手，可以在终端、桌面应用或 IDE 扩展中使用。它支持 75+ 种 LLM 提供商，包括 Claude、GPT、Gemini 等。

---

## 📋 目录

1. [安装 OpenCode](#1-安装-opencode)
2. [配置 AI 模型](#2-配置-ai-模型)
3. [初始化项目](#3-初始化项目)
4. [基本使用](#4-基本使用)
5. [高级功能](#5-高级功能)
6. [常见问题](#6-常见问题)

---

## 1. 安装 OpenCode

### 🖥️ 方式一：终端/命令行版本（CLI）

#### macOS / Linux

**推荐方式 - 使用安装脚本：**
```bash
curl -fsSL https://opencode.ai/install | bash
```

**使用 Homebrew：**
```bash
# 使用 OpenCode 官方源（推荐，更新更及时）
brew install anomalyco/tap/opencode

# 或使用 Homebrew 官方源
brew install opencode
```

**使用 Node.js：**
```bash
npm install -g opencode-ai
# 或
bun install -g opencode-ai
# 或
pnpm install -g opencode-ai
# 或
yarn global add opencode-ai
```

**Arch Linux：**
```bash
paru -S opencode-bin
```

#### Windows

**推荐：使用 WSL（Windows Subsystem for Linux）**

在 WSL 中运行：
```bash
curl -fsSL https://opencode.ai/install | bash
```

**使用 Chocolatey：**
```bash
choco install opencode
```

**使用 Scoop：**
```bash
scoop install opencode
```

**使用 NPM：**
```bash
npm install -g opencode-ai
```

**使用 Docker：**
```bash
docker run -it --rm ghcr.io/anomalyco/opencode
```

#### 验证安装

```bash
opencode --version
```

---

### 🖥️ 方式二：桌面端版本（Desktop）

#### macOS

**Apple Silicon (M1/M2/M3)：**
```bash
brew install --cask opencode-desktop
```
或直接下载：[下载链接](https://opencode.ai/download/darwin-aarch64-dmg)

**Intel Mac：**
```bash
brew install --cask opencode-desktop
```
或直接下载：[下载链接](https://opencode.ai/download/darwin-x64-dmg)

#### Windows

直接下载安装程序：[下载链接](https://opencode.ai/download/windows-x64-nsis)

#### Linux

**Debian/Ubuntu (.deb)：**
```bash
# 下载后安装
sudo dpkg -i opencode-desktop_*.deb
```
或直接下载：[下载链接](https://opencode.ai/download/linux-x64-deb)

**Fedora/RHEL (.rpm)：**
```bash
# 下载后安装
sudo rpm -i opencode-desktop_*.rpm
```
或直接下载：[下载链接](https://opencode.ai/download/linux-x64-rpm)

---

### 🔌 方式三：IDE 扩展

- **VS Code:** [安装链接](https://opencode.ai/docs/ide/)
- **Cursor:** [安装链接](https://opencode.ai/docs/ide/)
- **Zed:** [安装链接](https://opencode.ai/docs/ide/)
- **Windsurf:** [安装链接](https://opencode.ai/docs/ide/)
- **VSCodium:** [安装链接](https://opencode.ai/docs/ide/)

---

## 2. 配置 AI 模型

### 🎯 推荐方式：OpenCode Zen（新手友好）

OpenCode Zen 是 OpenCode 团队精选和测试过的模型集合，最适合编码任务。

**步骤：**

1. **启动 OpenCode：**
   ```bash
   opencode
   ```

2. **运行连接命令：**
   ```
   /connect
   ```

3. **选择 opencode，然后访问：** [opencode.ai/auth](https://opencode.ai/auth)

4. **注册/登录，添加付款信息，复制 API Key**

5. **粘贴 API Key：**
   ```
   ┌ API key
   │
   │
   └ enter
   ```

### 🔧 其他模型提供商

如果你想使用其他提供商（如 OpenAI、Claude、Gemini 等）：

```
/connect
```

然后选择对应的提供商并输入 API Key。

**支持的提供商包括：**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- GitHub Copilot
- 以及 75+ 其他提供商

---

## 3. 初始化项目

### 📁 进入你的项目目录

```bash
cd /path/to/your/project
```

### 🚀 启动 OpenCode

```bash
opencode
```

### 📝 初始化项目

在 OpenCode 终端中运行：

```
/init
```

**这会自动：**
- 分析你的项目结构
- 创建 `AGENTS.md` 文件（项目配置文件）
- 理解代码模式和项目约定

⚠️ **重要提示：** 建议将 `AGENTS.md` 提交到 Git，这样团队成员可以共享相同的配置。

---

## 4. 基本使用

### 💬 提问和解释代码

你可以向 OpenCode 询问关于代码库的任何问题：

```
How is authentication handled in @packages/functions/src/api/index.ts
```

💡 **提示：** 使用 `@` 键可以模糊搜索项目中的文件。

---

### ➕ 添加新功能

#### 方式一：计划模式（推荐）

1. **切换到计划模式（按 Tab 键）**
   
   右下角会显示模式指示器

2. **描述你想要的功能：**
   ```
   When a user deletes a note, we'd like to flag it as deleted in the database.
   Then create a screen that shows all the recently deleted notes.
   From this screen, the user can undelete a note or permanently delete it.
   ```

3. **迭代计划**
   
   OpenCode 会给出实现计划，你可以提供反馈或添加更多细节：
   ```
   We'd like to design this new screen using a design I've used before.
   [Image #1] Take a look at this image and use it as a reference.
   ```

   💡 **提示：** 可以直接拖拽图片到终端，OpenCode 可以分析图片内容。

4. **执行构建（再按 Tab 键切换回构建模式）**
   ```
   Sounds good! Go ahead and make the changes.
   ```

#### 方式二：直接构建

对于简单的更改，可以直接要求 OpenCode 构建：

```
We need to add authentication to the /settings route. Take a look at how this is
handled in the /notes route in @packages/functions/src/notes.ts and implement
the same logic in @packages/functions/src/settings.ts
```

---

### ↩️ 撤销更改

如果不满意更改，可以撤销：

```
/undo
```

💡 **提示：** 可以多次运行 `/undo` 撤销多步更改。

如果想重做：
```
/redo
```

---

### 🔗 分享对话

你可以分享与 OpenCode 的对话给团队成员：

```
/share
```

这会创建一个链接并复制到剪贴板。

⚠️ **注意：** 对话默认不公开分享。

---

## 5. 高级功能

### 🎨 自定义主题

```
/theme
```

查看可用主题并切换。

---

### ⌨️ 自定义快捷键

查看文档：[Keybinds](https://opencode.ai/docs/keybinds)

常用快捷键：
- `Tab` - 切换计划/构建模式
- `@` - 文件搜索
- `Ctrl+K` - 搜索命令
- `/` - 输入命令

---

### 🛠️ 自定义命令

创建自定义命令来提高效率：

查看文档：[Commands](https://opencode.ai/docs/commands)

---

### 🔧 配置代码格式化

配置你的代码格式化工具：

查看文档：[Formatters](https://opencode.ai/docs/formatters)

---

### 🤖 使用 Agents

创建自定义 agents 来处理特定任务：

查看文档：[Agents](https://opencode.ai/docs/agents)

---

### 🔌 MCP 服务器

集成 Model Context Protocol 服务器：

查看文档：[MCP Servers](https://opencode.ai/docs/mcp-servers)

---

## 6. 常见问题

### ❓ OpenCode 是免费的吗？

OpenCode 本身是开源免费的。但你可能需要为使用的 AI 模型 API 付费。OpenCode Zen 提供按量付费的模型访问。

### ❓ 我的代码安全吗？

OpenCode 不存储你的代码或上下文数据，适合在隐私敏感的环境中使用。

### ❓ 可以离线使用吗？

可以，如果你使用本地模型（如通过 Ollama）。

### ❓ 支持哪些编程语言？

OpenCode 支持几乎所有编程语言，会自动加载相应的 LSP（语言服务器协议）。

### ❓ 如何更新 OpenCode？

根据安装方式：
- **curl 安装：** 重新运行安装脚本
- **Homebrew：** `brew upgrade opencode`
- **npm：** `npm update -g opencode-ai`

### ❓ 遇到问题怎么办？

1. 查看官方文档：[opencode.ai/docs](https://opencode.ai/docs)
2. 查看故障排除指南：[Troubleshooting](https://opencode.ai/docs/troubleshooting/)
3. 加入 Discord 社区：[Discord](https://opencode.ai/discord)
4. 在 GitHub 上提交 issue：[GitHub Issues](https://github.com/anomalyco/opencode/issues)

---

## 📚 更多资源

- **官方文档：** [opencode.ai/docs](https://opencode.ai/docs)
- **GitHub：** [github.com/anomalyco/opencode](https://github.com/anomalyco/opencode)
- **Discord：** [opencode.ai/discord](https://opencode.ai/discord)
- **Twitter/X：** [@opencode](https://x.com/opencode)

---

## ✅ 快速开始清单

- [ ] 安装 OpenCode（CLI 或 Desktop）
- [ ] 运行 `opencode` 启动
- [ ] 运行 `/connect` 配置 AI 模型
- [ ] 进入项目目录
- [ ] 运行 `/init` 初始化项目
- [ ] 开始提问或构建功能！

---

*最后更新：2026-02-10*
*文档版本：v1.0*
