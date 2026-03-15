# LLMGateway NAS 容器化部署指南

本文档介绍如何将 LLMGateway 部署到 NAS 服务器的 Docker 环境中。

## 目录

- [快速开始](#快速开始)
- [手动部署](#手动部署)
- [一键部署脚本](#一键部署脚本)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 快速开始

### 前提条件

1. NAS 服务器已安装 Docker 和 Docker Compose
2. 已配置 SSH 免密登录或知道 SSH 密码
3. 本地已安装 Git、Docker

### 一键部署（推荐）

```bash
# 1. 克隆项目（如果还没有）
git clone <your-repo-url>
cd LLMGateway

# 2. 执行一键部署脚本
chmod +x deploy-to-nas.sh
./deploy-to-nas.sh -h 192.168.1.2 -u chyrain
```

### 访问服务

部署完成后，通过以下地址访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| Vue 前端 | http://192.168.1.2:80 | 默认管理界面（推荐） |
| React 前端 | http://192.168.1.2:88 | 备选管理界面 |
| 后端 API | http://192.168.1.2:8000 | 管理 API + 网关接口 |
| 网关接口 | http://192.168.1.2:8080 | LLM 转发接口（OpenAI 兼容） |

**默认管理员账号：**
- 用户名：`admin`
- 密码：`admin123`

> ⚠️ 首次登录后请立即修改默认密码

---

## 手动部署

### 步骤 1: 准备部署目录

SSH 登录到 NAS 服务器：

```bash
ssh chyrain@192.168.1.2

# 创建部署目录
mkdir -p /volume1/docker/llmgateway
cd /volume1/docker/llmgateway
```

### 步骤 2: 上传项目文件

```bash
# 方式 1: 使用 git clone
git clone <your-repo-url> .

# 方式 2: 从本地上传
# 在本地执行：
scp -r backend frontend frontend-react docker-compose.prod.yml .env.prod.example chyrain@192.168.1.2:/volume1/docker/llmgateway/
```

### 步骤 3: 配置环境变量

```bash
# 复制环境变量文件
cp .env.prod.example .env.prod

# 生成加密密钥（重要！）
openssl rand -base64 32

# 编辑.env.prod 文件，替换 ENCRYPT_KEY 为上面生成的密钥
vi .env.prod
```

### 步骤 4: 创建数据目录

```bash
mkdir -p data logs/backend logs/gateway
```

### 步骤 5: 构建并启动

```bash
# 使用 docker compose v2
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# 或使用 docker-compose v1
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

### 步骤 6: 查看服务状态

```bash
# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f backend

# 测试服务
curl http://localhost:8000/health
```

---

## 一键部署脚本

### 脚本用法

```bash
./deploy-to-nas.sh [options]
```

### 可用选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-h, --host` | NAS 服务器 IP 地址 | 192.168.1.2 |
| `-u, --user` | NAS 用户名 | chyrain |
| `-p, --path` | NAS 部署路径 | /volume1/docker/llmgateway |
| `-n, --no-build` | 跳过构建，只部署已有镜像 | false |
| `-c, --clean` | 部署前清理旧容器和数据 | false |

### 使用示例

```bash
# 使用默认配置部署
./deploy-to-nas.sh

# 指定 NAS 地址
./deploy-to-nas.sh -h 192.168.1.100 -u admin

# 指定部署路径
./deploy-to-nas.sh -p /mnt/data/docker/llmgateway

# 清理旧部署后重新部署
./deploy-to-nas.sh -c

# 跳过构建（快速重启）
./deploy-to-nas.sh -n
```

---

## 配置说明

### 环境变量 (.env.prod)

```bash
# API Key 加密密钥（必须修改！）
ENCRYPT_KEY=your-256-bit-encryption-key-here

# 服务端口
API_PORT=8000              # 后端 API 端口
GATEWAY_PORT=8080          # 网关端口
FRONTEND_PORT=80           # Vue 前端端口
REACT_FRONTEND_PORT=88     # React 前端端口

# 网关配置
SWITCH_THRESHOLD=99        # 自动切换阈值 (%)
SYNC_INTERVAL=10           # 额度同步间隔 (秒)
LOG_LEVEL=INFO             # 日志级别
```

### 端口映射

| 容器端口 | 主机端口 | 说明 |
|---------|---------|------|
| 8000 | 8000 | 后端 API（管理接口 + 网关） |
| 8080 | 8080 | 网关服务（LLM 转发） |
| 80 | 80 | Vue 前端 |
| 80 | 88 | React 前端 |

> ⚠️ 如果端口冲突，可在 .env.prod 中修改主机端口映射

### 数据持久化

| 目录 | 说明 |
|------|------|
| `./data` | SQLite 数据库文件 |
| `./logs/backend` | 后端日志 |
| `./logs/gateway` | 网关日志 |

---

## 常用管理命令

### SSH 登录 NAS 后执行

```bash
cd /volume1/docker/llmgateway

# 查看服务状态
docker compose ps

# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend

# 重启服务
docker compose restart

# 重启特定服务
docker compose restart backend

# 停止服务
docker compose down

# 停止并删除容器（保留数据）
docker compose down --remove-orphans

# 完全清理（删除容器和数据卷）
docker compose down -v

# 更新部署
git pull
docker compose build
docker compose up -d
```

---

## 常见问题

### 1. 容器无法启动

**检查日志：**
```bash
docker compose logs backend
```

**常见原因：**
- 端口被占用：修改 .env.prod 中的端口配置
- 数据库路径权限问题：`chmod 755 ./data`
- 加密密钥格式错误：确保是 base64 格式

### 2. 前端无法访问

**检查容器状态：**
```bash
docker compose ps frontend
```

**检查端口占用：**
```bash
netstat -tlnp | grep :80
```

**解决方案：**
- 修改 FRONTEND_PORT 为其他端口
- 或停止占用 80 端口的服务

### 3. 数据库初始化失败

```bash
# 删除数据库文件重新初始化
rm -f ./data/llmgateway.db
docker compose restart backend
```

### 4. 加密密钥丢失

如果丢失了加密密钥，所有保存的 API Key 将无法解密。解决方法：

1. 生成新密钥：`openssl rand -base64 32`
2. 更新 .env.prod 文件
3. 重启服务
4. 在管理后台重新配置 API Key

### 5. NAS 是群晖 (Synology)

群晖 Docker 默认可能未启用 Compose 功能：

**启用方法：**
1. 打开「Container Manager」或「Docker」
2. 进入「设置」或「偏好设置」
3. 启用 Docker Compose 功能

**或使用命令行：**
```bash
# SSH 登录群晖
sudo -i
docker compose version
```

### 6. NAS 是威联通 (QNAP)

威联通可能需要先安装 Container Station：

1. 在 App Center 安装 Container Station
2. 启用 SSH 访问
3. 按照上述步骤部署

---

## 性能优化建议

### 1. 内存分配

建议为 NAS 上的 Docker 分配至少 2GB 内存：

- 后端服务：512MB
- 前端服务：128MB x 2
- 预留：1GB+

### 2. 存储位置

将数据目录放在 SSD 或高速存储卷上：

```bash
# 推荐路径（SSD 卷）
/volume1/docker/llmgateway

# 不推荐（机械硬盘）
/volume2/data/llmgateway
```

### 3. 网络模式

如果 NAS 支持，可使用 host 网络模式提升性能（需修改 docker-compose.yml）：

```yaml
services:
  backend:
    network_mode: host
```

---

## 升级指南

### 自动升级

```bash
cd /volume1/docker/llmgateway

# 拉取最新代码
git pull

# 重新构建并启动
docker compose build
docker compose up -d
```

### 保留配置升级

```bash
# 备份配置文件
cp .env.prod .env.prod.bak

# 拉取代码后对比配置差异
diff .env.prod.example .env.prod

# 根据需要更新配置
```

---

## 技术支持

- 项目文档：查看项目根目录的 README.md
- 问题反馈：提交 Issue
- 更新日志：查看 CHANGELOG.md
