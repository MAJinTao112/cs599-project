#!/bin/bash
set -e

DEPLOY_DIR="/opt/cs599"

echo "=========================================="
echo "  XiaoTao Travel - 服务器部署脚本"
echo "=========================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误: 未安装 Docker"
    echo "  安装命令: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

cd "$DEPLOY_DIR"

# 加载镜像
echo ""
if ls *.tar &> /dev/null; then
    echo "加载镜像文件..."
    for f in *.tar; do
        echo "  加载 $f ..."
        docker load -i "$f"
    done
    echo "镜像加载完成"
else
    echo "未找到 .tar 镜像文件，请先将镜像文件传到 $DEPLOY_DIR 目录"
    exit 1
fi

# 创建 .env 文件
if [ ! -f .env ]; then
    echo ""
    echo "首次部署，请配置 API Key："
    echo ""
    read -rsp "请输入 DEEPSEEK_API_KEY: " DEEPSEEK_KEY
    echo ""
    read -rsp "请输入 DASHSCOPE_API_KEY: " DASHSCOPE_KEY
    echo ""

    cat > .env << EOF
DEEPSEEK_API_KEY=${DEEPSEEK_KEY}
DASHSCOPE_API_KEY=${DASHSCOPE_KEY}
MCP_CONFIG_PATH=travel_agent/config/servers_config.json
EOF
    echo ".env 文件已创建"
else
    echo ".env 文件已存在，跳过创建"
fi

# 启动服务
echo ""
echo "启动服务..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "=========================================="
echo "  部署完成！"
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "你的服务器IP")
echo "  前端: http://${SERVER_IP}:80"
echo "  后端健康检查: curl http://127.0.0.1:8000/api/health"
echo "=========================================="
echo ""
echo "常用命令："
echo "  查看日志: docker compose -f docker-compose.prod.yml logs -f"
echo "  停止服务: docker compose -f docker-compose.prod.yml down"
echo "  重启服务: docker compose -f docker-compose.prod.yml restart"
