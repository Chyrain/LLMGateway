# 贡献指南

感谢您对灵模网关项目的兴趣！我们欢迎各种形式的贡献，包括但不限于：

- 🐛 报告Bug
- 💡 提出新功能建议
- 📝 完善文档
- 🔧 提交代码修复
- 🌟 添加新功能

## 📋 如何贡献

### 1. Fork 项目

点击右上角的 Fork 按钮，将项目复制到您的 GitHub 账户。

### 2. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/LLMGateway.git
cd LLMGateway
```

### 3. 创建分支

```bash
git checkout -b feature/AmazingFeature
```

### 4. 进行开发

请遵循以下开发规范：

#### 代码规范
- **Python**: 遵循 PEP 8 规范，使用 Black 格式化
- **Vue**: 遵循 Vue 3 官方风格指南
- **提交信息**: 使用 Conventional Commits 格式

#### 提交信息格式

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 添加测试
- `chore`: 构建工具或辅助功能

**示例**:
```
feat(gateway): 添加 Claude 模型支持

- 新增 Claude API 参数映射
- 更新厂商模板配置
- 添加 Claude 响应格式转换

Closes #123
```

### 5. 编写测试

确保您的代码包含适当的测试用例：

```bash
# 运行单元测试
cd backend
pytest tests/

# 运行前端测试
cd frontend
npm test
```

### 6. 提交更改

```bash
git add .
git commit -m "feat: 添加新功能"
```

### 7. 推送到您的 Fork

```bash
git push origin feature/AmazingFeature
```

### 8. 创建 Pull Request

在 GitHub 上创建 Pull Request，详细描述您的更改。

## 📐 项目结构

```
LLMGateway/
├── backend/           # 后端服务 (Python FastAPI)
├── frontend/          # 前端管理平台 (Vue3)
├── docs/              # 文档
├── scripts/           # 工具脚本
├── docker-compose.yml # Docker 配置
└── LICENSE            # MIT 许可证
```

## 🔧 开发环境设置

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 🧪 测试要求

- 所有新功能必须包含测试
- 确保所有测试通过后再提交 PR
- 代码覆盖率应保持在 80% 以上

## 📝 文档要求

- 更新 README.md（如果涉及用户可见的更改）
- 更新 API 文档（如果更改了接口）
- 添加注释解释复杂的代码逻辑

## 💬 交流讨论

- 📧 邮箱: chyrain@example.com
- 💬 GitHub Issues: 用于报告 Bug 和提出建议
- 🐱 GitHub Discussions: 用于一般讨论

## 📜 行为准则

请阅读我们的 [行为准则](CODE_OF_CONDUCT.md)，了解社区标准。

---

再次感谢您的贡献！ 🎉
