#!/bin/bash

# LLMGateway 初始化脚本
# 用于首次部署时生成配置文件和加密密钥

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo "========================================="
echo "   LLMGateway 初始化配置工具"
echo "========================================="
echo ""

# 检查并生成 .env.prod 文件
if [ -f ".env.prod" ]; then
    warn ".env.prod 文件已存在"
    read -p "是否覆盖现有配置？[y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "跳过配置生成"
        exit 0
    fi
fi

# 生成加密密钥
info "生成 API 加密密钥..."
if command -v openssl &> /dev/null; then
    ENCRYPT_KEY=$(openssl rand -base64 32)
    success "加密密钥生成成功"
else
    error "未找到 openssl，请手动生成加密密钥"
    echo "运行以下命令生成密钥："
    echo "  python3 -c 'import base64,os; print(base64.b64encode(os.urandom(32)).decode())'"
    exit 1
fi

# 读取示例文件并创建新配置
info "创建 .env.prod 配置文件..."

# 获取当前时间戳
BUILD_TIMESTAMP=$(date +%s)

# 创建配置文件
cat > .env.prod << EOF
# LLMGateway 生产环境变量配置
# 此文件由初始化脚本自动生成于 $(date '+%Y-%m-%d %H:%M:%S')

# ==================== 加密配置 ====================
# API Key 加密密钥 (32 字节 base64 编码)
# ⚠️ 重要：请妥善保管此密钥，丢失后无法解密已保存的 API Key
ENCRYPT_KEY=$ENCRYPT_KEY

# ==================== 服务端口配置 ====================
# 后端 API 服务端口（管理后台）
API_PORT=8000

# 网关服务端口（LLM 转发接口）
GATEWAY_PORT=8080

# Vue 前端端口（默认管理界面）
FRONTEND_PORT=80

# React 前端端口（备选管理界面）
REACT_FRONTEND_PORT=88

# ==================== 网关运行配置 ====================
# 自动切换阈值 (%) - 当模型额度使用率达到此值时自动切换
SWITCH_THRESHOLD=99

# 额度同步间隔 (秒)
SYNC_INTERVAL=10

# 日志级别 (DEBUG/INFO/WARNING/ERROR)
LOG_LEVEL=INFO

# ==================== Docker 构建配置 ====================
# 构建时间戳（用于版本标识）
BUILD_TIMESTAMP=$BUILD_TIMESTAMP
EOF

success ".env.prod 配置文件创建成功"

# 创建数据目录
info "创建数据目录..."
mkdir -p data logs/backend logs/gateway
success "数据目录创建完成"

# 显示配置信息
echo ""
echo "========================================="
echo "   初始化完成"
echo "========================================="
echo ""
echo "生成的文件:"
echo "  - .env.prod (环境配置)"
echo "  - data/ (数据目录)"
echo "  - logs/ (日志目录)"
echo ""
echo "重要信息:"
echo "  加密密钥：$ENCRYPT_KEY"
echo ""
warn "请务必备份上述加密密钥！"
echo ""
echo "下一步操作:"
echo ""
echo "  方式 1: 使用 docker-compose 启动"
echo "  -------"
echo "  docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build"
echo ""
echo "  方式 2: 使用一键部署脚本部署到 NAS"
echo "  -------"
echo "  ./deploy-to-nas.sh -h 192.168.1.2 -u chyrain"
echo ""
echo "  方式 3: 使用全合一模式（节省资源）"
echo "  -------"
echo "  docker compose -f docker-compose.all-in-one.yml --env-file .env.prod up -d --build"
echo ""
echo "========================================="
