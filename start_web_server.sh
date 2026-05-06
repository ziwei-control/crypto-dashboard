#!/bin/bash
################################################################################
# 🌐 Crypto Dashboard Web Server - 启动 8899 端口 Web 服务
################################################################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

PORT=8899
PROJECT_DIR="/home/admin/projects/crypto-dashboard"

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🌐 Crypto Dashboard Web Server${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

cd "$PROJECT_DIR"

# 检查是否已有进程
EXISTING_PID=$(lsof -t -i:$PORT 2>/dev/null)

if [ -n "$EXISTING_PID" ]; then
    echo -e "${YELLOW}⚠️${NC} 端口 $PORT 已被占用 (PID: $EXISTING_PID)"
    echo -e "${YELLOW}   正在重启服务...${NC}"
    kill $EXISTING_PID 2>/dev/null
    sleep 1
fi

# 启动 Web 服务器
nohup python3 -m http.server $PORT > /tmp/web_${PORT}.log 2>&1 &
NEW_PID=$!

sleep 2

# 验证服务是否启动
if curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT | grep -q "200"; then
    echo -e "${GREEN}✅${NC} Web Server 已启动!"
    echo ""
    echo -e "${BLUE}访问地址:${NC}"
    echo -e "  ${GREEN}本地访问:${NC} http://localhost:$PORT"
    echo -e "  ${GREEN}局域网访问:${NC} http://$(hostname -I | awk '{print $1}'):$PORT"
    echo ""
    echo -e "${BLUE}Dashboard:${NC} http://$(hostname -I | awk '{print $1}'):$PORT/dashboard_pwa.html"
    echo ""
    echo -e "${YELLOW}PID:${NC} $NEW_PID"
    echo -e "${YELLOW}日志:${NC} /tmp/web_${PORT}.log"
else
    echo -e "${RED}❌${NC} 启动失败，请检查日志：/tmp/web_${PORT}.log"
    exit 1
fi
