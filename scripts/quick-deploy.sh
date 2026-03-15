#!/bin/bash

# LLMGateway 快速部署脚本（服务器端）
# 此脚本应放在 NAS 服务器上执行

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

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    error "未安装 Docker"
    exit 1
fi

# 检查 docker compose
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif docker-compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    error "未安装 Docker Compose"
    exit 1
fi

info "使用 Docker Compose 命令：$COMPOSE_CMD"

# 检查配置文件
if [ ! -f ".env.prod" ]; then
    warn ".env.prod 不存在，从示例文件创建..."
    cp .env.prod.example .env.prod

    # 生成加密密钥
    if command -v openssl &> /dev/null; then
        ENCRYPT_KEY=$(openssl rand -base64 32)
        sed -i "s/ENCRYPT_KEY=.*/ENCRYPT_KEY=$ENCRYPT_KEY/" .env.prod
        success "已生成加密密钥：$ENCRYPT_KEY"
        warn "请妥善保管此密钥，建议备份到安全位置"
    fi
fi

# 创建数据目录
info "创建数据目录..."
mkdir -p data logs/backend logs/gateway

# 停止旧服务
info "停止旧服务..."
$COMPOSE_CMD down --remove-orphans 2>/dev/null || true

# 构建镜像
info "构建 Docker 镜像..."
$COMPOSE_CMD build

# 启动服务
info "启动 LLMGateway 服务..."
$COMPOSE_CMD up -d

# 等待启动
sleep 3

# 显示状态
echo ""
success "========== 部署完成 =========="
echo ""
echo "服务状态:"
$COMPOSE_CMD ps

echo ""
echo "访问地址:"
echo "  Vue 前端：http://$(hostname -I 2>/dev/null | awk '{print $1}'):80"
echo "  React 前端：http://$(hostname -I 2>/dev/null | awk '{print $1}'):88"
echo "  后端 API: http://$(hostname -I 2>/dev/null | awk '{print $1}'):8000"
echo "  网关接口：http://$(hostname -I 2>/dev/null | awk '{print $1}'):8080"
echo ""
echo "默认账号：admin / admin123"
echo ""
echo "管理命令:"
echo "  $COMPOSE_CMD logs -f     # 查看日志"
echo "  $COMPOSE_CMD restart     # 重启服务"
echo "  $COMPOSE_CMD down        # 停止服务"
echo "================================="
