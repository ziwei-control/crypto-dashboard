#!/bin/bash
# 使用 screen 启动 serveo 隧道

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🌐 启动 Serveo 隧道（使用 screen）...${NC}"

# 停止现有隧道
pkill -f "ssh.*serveo" 2>/dev/null
screen -wipe serveo 2>/dev/null
sleep 2

# 使用 screen 启动隧道
screen -dmS serveo bash -c "cd /root/.copaw/crypto_projects && ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 0:localhost:8000 serveo.net 2>&1 | tee /tmp/serveo.log"

echo -e "${GREEN}✅ 隧道已启动 (screen: serveo)${NC}"
echo ""
echo -e "${BLUE}查看隧道状态：${NC}"
echo "  screen -r serveo"
echo ""
echo -e "${BLUE}查看日志：${NC}"
echo "  tail -f /tmp/serveo.log"
