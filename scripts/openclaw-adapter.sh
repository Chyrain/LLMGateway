#!/bin/bash

# =============================================
# 灵模网关 - OpenClaw 一键适配脚本
# =============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   灵模网关 - OpenClaw 一键适配脚本${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 检查是否在OpenClaw目录
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}错误: 未找到 config.yaml 文件${NC}"
    echo "请确保在 OpenClaw 项目根目录下运行此脚本"
    exit 1
fi

# 读取当前配置
echo -e "${YELLOW}读取当前配置...${NC}"
CURRENT_PROVIDER=$(grep "provider:" config.yaml | head -1 | awk '{print $2}')
CURRENT_MODEL=$(grep "name:" config.yaml | head -1 | awk '{print $2}')
CURRENT_BASE_URL=$(grep "base_url:" config.yaml | head -1 | awk '{print $2}')
CURRENT_API_KEY=$(grep "api_key:" config.yaml | head -1 | awk '{print $2}')

echo "  当前模型: $CURRENT_MODEL"
echo "  当前地址: $CURRENT_BASE_URL"
echo ""

# 获取网关配置
read -p "请输入灵模网关地址 (默认: http://localhost:8080): " GATEWAY_URL
GATEWAY_URL=${GATEWAY_URL:-http://localhost:8080}

read -p "请输入灵模网关API Key (默认: gateway_123456): " GATEWAY_KEY
GATEWAY_KEY=${GATEWAY_KEY:-gateway_123456}

echo ""
echo -e "${YELLOW}正在更新配置...${NC}"

# 备份原配置
cp config.yaml config.yaml.backup.$(date +%Y%m%d%H%M%S)
echo -e "${GREEN}✓ 已备份原配置${NC}"

# 更新配置
if [ "$(uname)" == "Darwin" ]; then
    # macOS
    sed -i '' "s|provider: .*|provider: openai|g" config.yaml
    sed -i '' "s|name: .*|name: gpt-3.5-turbo|g" config.yaml
    sed -i '' "s|base_url: .*|base_url: $GATEWAY_URL/v1|g" config.yaml
    sed -i '' "s|api_key: .*|api_key: $GATEWAY_KEY|g" config.yaml
else
    # Linux/Windows
    sed -i "s|provider: .*|provider: openai|g" config.yaml
    sed -i "s|name: .*|name: gpt-3.5-turbo|g" config.yaml
    sed -i "s|base_url: .*|base_url: $GATEWAY_URL/v1|g" config.yaml
    sed -i "s|api_key: .*|api_key: $GATEWAY_KEY|g" config.yaml
fi

echo -e "${GREEN}✓ 配置已更新${NC}"

# 验证配置
echo ""
echo -e "${YELLOW}验证新配置...${NC}"
NEW_BASE_URL=$(grep "base_url:" config.yaml | head -1 | awk '{print $2}')
NEW_API_KEY=$(grep "api_key:" config.yaml | head -1 | awk '{print $2}')

if [ "$NEW_BASE_URL" == "$GATEWAY_URL/v1" ]; then
    echo -e "${GREEN}✓ 网关地址配置正确${NC}"
else
    echo -e "${RED}✗ 网关地址配置失败${NC}"
fi

if [ "$NEW_API_KEY" == "$GATEWAY_KEY" ]; then
    echo -e "${GREEN}✓ API Key配置正确${NC}"
else
    echo -e "${RED}✗ API Key配置失败${NC}"
fi

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}   配置完成！${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "下一步:"
echo "  1. 启动 OpenClaw: ./openclaw start"
echo "  2. 在管理平台确认模型已启用"
echo "  3. 开始使用！"
echo ""
echo -e "${YELLOW}提示: 如需回滚，运行: mv config.yaml.backup.* config.yaml${NC}"
