#!/bin/bash
set -e

echo "=========================================="
echo "  XiaoTao Travel - 构建并打包镜像"
echo "=========================================="

cd "$(dirname "$0")"

PLATFORM="${PLATFORM:-linux/amd64}"

echo ""
echo "构建后端镜像 (${PLATFORM})..."
docker build --platform "$PLATFORM" -t cs599-backend:latest -f Dockerfile.backend .

echo ""
echo "构建前端镜像 (${PLATFORM})..."
docker build --platform "$PLATFORM" -t cs599-frontend:latest -f Dockerfile.frontend .

echo ""
echo "打包镜像为 tar 文件..."
docker save -o cs599-backend.tar cs599-backend:latest
docker save -o cs599-frontend.tar cs599-frontend:latest

echo ""
echo "=========================================="
echo "  打包完成！"
echo "  生成文件："
ls -lh cs599-*.tar
echo ""
echo "  下一步：将以下文件传到服务器 /opt/cs599/ 目录"
echo "    cs599-backend.tar"
echo "    cs599-frontend.tar"
echo "    docker-compose.prod.yml"
echo "    deploy.sh"
echo "    src/aggentic_RAG/travel_agent/config/servers_config.json"
echo ""
echo "  传输命令（替换你的服务器IP）："
echo "    SERVER_IP=你的服务器IP"
echo "    ssh root@\$SERVER_IP 'mkdir -p /opt/cs599'"
echo "    scp cs599-backend.tar cs599-frontend.tar docker-compose.prod.yml deploy.sh root@\$SERVER_IP:/opt/cs599/"
echo "    scp src/aggentic_RAG/travel_agent/config/servers_config.json root@\$SERVER_IP:/opt/cs599/"
echo "=========================================="
