#!/bin/bash
################################################################################
# 🌐 Serveo 公网隧道备用启动脚本（使用子域名）
################################################################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd /root/.copaw/crypto_projects

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🌐 启动 Serveo 公网隧道（备用）${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# 生成随机子域名
SUBDOMAIN="crypto$(date +%s | tail -c 5)"
echo -e "${YELLOW}🎲${NC} 使用子域名: ${GREEN}$SUBDOMAIN${NC}"
echo ""

# 停止现有隧道
echo -e "${YELLOW}[1/2]${NC} 停止现有隧道..."
pkill -f "ssh.*serveo" 2>/dev/null
screen -wipe serveo 2>/dev/null
sleep 2
echo -e "${GREEN}✅${NC} 现有隧道已停止"

# 启动新隧道（指定端口 80 和子域名）
echo -e "${YELLOW}[2/2]${NC} 启动新隧道..."
echo ""

# 使用 screen 启动，指定子域名
screen -dmS serveo bash -c "ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:8000 $SUBDOMAIN.serveo.net 2>&1 | tee /tmp/serveo.log"

SSH_PID=$(ps aux | grep "ssh.*serveo" | grep -v grep | awk '{print $2}' | head -1)
echo -e "${GREEN}✅${NC} 隧道已启动 (PID: $SSH_PID)"
echo ""

# 等待隧道启动
echo -e "${YELLOW}⏳${NC} 等待隧道启动..."
sleep 5

# 显示结果
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${GREEN}🎉 隧道启动成功！${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# 尝试从日志中提取 URL
if [ -s /tmp/serveo.log ]; then
    echo -e "${BLUE}📋 隧道日志：${NC}"
    cat /tmp/serveo.log
    echo ""
fi

# 提供 URL
echo -e "${BLUE}🌐 公网 URL：${NC}"
echo "  📱 主地址: ${GREEN}https://$SUBDOMAIN.serveo.net${NC}"
echo "  📄 Dashboard: ${GREEN}https://$SUBDOMAIN.serveo.net/dashboard.html${NC}"
echo ""

echo -e "${BLUE}🛠️ 管理命令：${NC}"
echo "  查看日志: ${GREEN}tail -f /tmp/serveo.log${NC}"
echo "  查看隧道: ${GREEN}screen -r serveo${NC}"
echo "  停止隧道: ${GREEN}pkill -f 'ssh.*serveo'${NC}"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
