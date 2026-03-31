#!/bin/bash
################################################################################
# 🚀 Crypto Projects Dashboard - 公网访问一键启动脚本
################################################################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🚀 Crypto Projects Dashboard - 公网访问启动${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# 切换到项目目录
cd "$(dirname "$0")"

# 检查本地服务器是否运行
echo -e "${YELLOW}[1/2]${NC} 检查本地 HTTP 服务器..."

if netstat -tuln 2>/dev/null | grep -q ":8000"; then
    echo -e "${GREEN}✅${NC} 本地服务器已在运行 (端口 8000)"
else
    echo -e "${YELLOW}⏳${NC} 启动本地 HTTP 服务器..."
    nohup python3 -m http.server 8000 > /tmp/http_server.log 2>&1 &

    # 等待服务器启动
    for i in {1..10}; do
        sleep 1
        if netstat -tuln 2>/dev/null | grep -q ":8000"; then
            echo -e "${GREEN}✅${NC} 本地服务器已启动 (端口 8000)"
            break
        fi
    done

    # 再次检查
    if ! netstat -tuln 2>/dev/null | grep -q ":8000"; then
        echo -e "${RED}❌ 本地服务器启动失败${NC}"
        echo "   查看日志: tail -f /tmp/http_server.log"
        exit 1
    fi
fi

# 测试本地访问
echo -e "${YELLOW}[2/2]${NC} 测试本地服务..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/dashboard.html 2>/dev/null)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅${NC} 本地服务正常 (HTTP 200)"
else
    echo -e "${RED}❌${NC} 本地服务异常 (HTTP $HTTP_CODE)"
    exit 1
fi

echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🌐 本地服务已就绪，启动公网隧道...${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo -e "${YELLOW}提示：${NC}"
echo "  - 隧道启动后，会显示一个公网 URL"
echo "  - 复制该 URL 在浏览器中访问"
echo "  - 在 URL 后加上 /dashboard.html 访问仪表板"
echo "  - 按 Ctrl+C 可关闭隧道"
echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# 启动 Serveo 隧道
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:8000 serveo.net