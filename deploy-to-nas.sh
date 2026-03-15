#!/bin/bash

# LLMGateway NAS 一键部署脚本
# 用法：./deploy-to-nas.sh [options]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
DEFAULT_NAS_HOST="192.168.1.2"
DEFAULT_NAS_USER="chyrain"
DEFAULT_DEPLOY_PATH="/volume1/docker/llmgateway"

# 打印信息
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 显示用法
usage() {
    cat << EOF
LLMGateway NAS 一键部署脚本

用法：$0 [options]

选项:
    -h, --host        NAS 服务器 IP 地址 (默认：$DEFAULT_NAS_HOST)
    -u, --user        NAS 用户名 (默认：$DEFAULT_NAS_USER)
    -p, --path        NAS 部署路径 (默认：$DEFAULT_DEPLOY_PATH)
    -n, --no-build    跳过构建，只部署已有镜像
    -c, --clean       部署前清理 NAS 上的旧容器和数据
    --help            显示此帮助信息

示例:
    $0                              # 使用默认配置部署
    $0 -h 192.168.1.100 -u admin   # 指定 NAS 地址和用户名
    $0 -c                          # 清理后重新部署
    $0 -n                          # 跳过构建（快速部署）

EOF
    exit 0
}

# 解析参数
SKIP_BUILD=false
CLEAN_FIRST=false
NAS_HOST="$DEFAULT_NAS_HOST"
NAS_USER="$DEFAULT_NAS_USER"
DEPLOY_PATH="$DEFAULT_DEPLOY_PATH"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            NAS_HOST="$2"
            shift 2
            ;;
        -u|--user)
            NAS_USER="$2"
            shift 2
            ;;
        -p|--path)
            DEPLOY_PATH="$2"
            shift 2
            ;;
        -n|--no-build)
            SKIP_BUILD=true
            shift
            ;;
        -c|--clean)
            CLEAN_FIRST=true
            shift
            ;;
        --help)
            usage
            ;;
        *)
            error "未知选项：$1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 检查 SSH 连接
check_ssh_connection() {
    info "检查 SSH 连接到 $NAS_HOST ..."
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$NAS_USER@$NAS_HOST" "echo 'Connection OK'" 2>/dev/null; then
        error "无法 SSH 连接到 $NAS_HOST"
        info "请确保:"
        echo "  1. NAS 服务器已开机并联网"
        echo "  2. SSH 服务已启用"
        echo "  3. 已配置 SSH 密钥认证或使用密码"
        exit 1
    fi
    success "SSH 连接成功"
}

# 检查 Docker 环境
check_docker() {
    info "检查 NAS 上的 Docker 环境..."
    if ! ssh "$NAS_USER@$NAS_HOST" "docker --version 2>/dev/null"; then
        error "NAS 上未安装 Docker"
        exit 1
    fi
    if ! ssh "$NAS_USER@$NAS_HOST" "docker compose version 2>/dev/null || docker-compose --version 2>/dev/null"; then
        warn "未检测到 docker compose，尝试使用 docker-compose"
    fi
    success "Docker 环境检查通过"
}

# 生成加密密钥
generate_encrypt_key() {
    info "生成 API 加密密钥..."
    if command -v openssl &> /dev/null; then
        ENCRYPT_KEY=$(openssl rand -base64 32)
    else
        # 使用 Python 生成
        ENCRYPT_KEY=$(python3 -c "import base64,os; print(base64.b64encode(os.urandom(32)).decode())")
    fi
    success "加密密钥生成完成"
}

# 准备部署文件
prepare_files() {
    info "准备部署文件..."

    # 创建部署目录
    DEPLOY_DIR=$(mktemp -d)
    info "临时部署目录：$DEPLOY_DIR"

    # 复制必要的文件
    cp docker-compose.prod.yml "$DEPLOY_DIR/docker-compose.yml"
    cp .env.prod.example "$DEPLOY_DIR/.env.prod"
    cp -r backend "$DEPLOY_DIR/"
    cp -r frontend "$DEPLOY_DIR/"
    cp -r frontend-react "$DEPLOY_DIR/"

    # 生成 .env 文件
    if [ ! -f .env.prod ]; then
        info "从示例文件生成 .env.prod..."
        generate_encrypt_key
        cp .env.prod.example .env.prod
        # 替换加密密钥
        sed -i.bak "s/ENCRYPT_KEY=.*/ENCRYPT_KEY=$ENCRYPT_KEY/" .env.prod
        rm -f .env.prod.bak
        success "已生成 .env.prod 文件（请妥善保管加密密钥）"
    fi

    # 复制.env.prod 到部署目录
    cp .env.prod "$DEPLOY_DIR/"

    # 创建数据目录
    mkdir -p "$DEPLOY_DIR/data"
    mkdir -p "$DEPLOY_DIR/logs/backend"
    mkdir -p "$DEPLOY_DIR/logs/gateway"

    success "部署文件准备完成"
}

# 清理旧部署
clean_old_deployment() {
    if [ "$CLEAN_FIRST" = true ]; then
        warn "清理 NAS 上的旧部署..."
        ssh "$NAS_USER@$NAS_HOST" << 'CLEAN_EOF'
cd "$DEPLOY_PATH" 2>/dev/null || exit 0
docker compose down --remove-orphans 2>/dev/null || true
docker-compose down --remove-orphans 2>/dev/null || true
CLEAN_EOF
        success "清理完成"
    fi
}

# 上传文件到 NAS
upload_files() {
    info "上传文件到 NAS: $DEPLOY_PATH ..."

    # 在 NAS 上创建目录
    ssh "$NAS_USER@$NAS_HOST" "mkdir -p '$DEPLOY_PATH'"

    # 使用 rsync 或 scp 上传
    if command -v rsync &> /dev/null; then
        info "使用 rsync 上传文件..."
        rsync -avz --delete "$DEPLOY_DIR/" "$NAS_USER@$NAS_HOST:$DEPLOY_PATH/"
    else
        info "使用 scp 上传文件..."
        scp -r "$DEPLOY_DIR"/* "$NAS_USER@$NAS_HOST:$DEPLOY_PATH/"
    fi

    success "文件上传完成"
}

# 构建和启动
build_and_start() {
    info "在 NAS 上构建并启动服务..."

    ssh "$NAS_USER@$NAS_HOST" << 'EOF'
cd "$DEPLOY_PATH"

# 尝试使用 docker compose (Docker Compose v2)
if command -v docker compose &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    # 回退到 docker-compose (v1)
    COMPOSE_CMD="docker-compose"
fi

# 停止并移除旧容器
$COMPOSE_CMD down --remove-orphans 2>/dev/null || true

# 构建镜像
if [ "$SKIP_BUILD" = "false" ]; then
    info "开始构建 Docker 镜像..."
    $COMPOSE_CMD build --no-cache
else
    info "跳过构建，拉取或复用现有镜像..."
    $COMPOSE_CMD pull || true
fi

# 启动服务
info "启动 LLMGateway 服务..."
$COMPOSE_CMD up -d

# 等待服务启动
sleep 5

# 显示状态
info "服务状态:"
$COMPOSE_CMD ps
EOF

    success "服务启动完成"
}

# 显示部署信息
show_deploy_info() {
    echo ""
    success "========== LLMGateway 部署完成 =========="
    echo ""
    echo "服务地址:"
    echo "  - Vue 前端 (默认):    http://$NAS_HOST:80"
    echo "  - React 前端：http://$NAS_HOST:88"
    echo "  - 后端 API:    http://$NAS_HOST:8000"
    echo "  - 网关接口：http://$NAS_HOST:8080"
    echo ""
    echo "默认管理员账号:"
    echo "  - 用户名：admin"
    echo "  - 密码：admin123"
    echo ""
    echo "重要提示:"
    echo "  1. 首次启动可能需要几分钟初始化数据库"
    echo "  2. 请尽快修改默认管理员密码"
    echo "  3. 加密密钥已保存在 .env.prod 文件中，请妥善保管"
    echo ""
    echo "管理命令 (SSH 到 NAS 后执行):"
    echo "  cd $DEPLOY_PATH"
    echo "  docker compose logs -f     # 查看日志"
    echo "  docker compose restart     # 重启服务"
    echo "  docker compose down        # 停止服务"
    echo "============================================="
}

# 清理临时文件
cleanup() {
    if [ -n "$DEPLOY_DIR" ] && [ -d "$DEPLOY_DIR" ]; then
        rm -rf "$DEPLOY_DIR"
    fi
}

# 主流程
main() {
    echo ""
    echo "========================================="
    echo "   LLMGateway NAS 一键部署工具"
    echo "========================================="
    echo ""

    info "部署配置:"
    echo "  NAS 地址：$NAS_HOST"
    echo "  用户名：$NAS_USER"
    echo "  部署路径：$DEPLOY_PATH"
    echo "  跳过构建：$SKIP_BUILD"
    echo "  清理旧部署：$CLEAN_FIRST"
    echo ""

    # 交互确认
    read -p "是否继续部署？[y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "部署已取消"
        exit 0
    fi

    # 执行部署步骤
    check_ssh_connection
    check_docker
    prepare_files
    clean_old_deployment
    upload_files
    build_and_start
    show_deploy_info

    # 清理
    trap cleanup EXIT
}

# 运行主流程
main
